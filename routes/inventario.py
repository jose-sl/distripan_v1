from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from database import get_connection

inventario_bp = Blueprint(
    "inventario",
    __name__
)

# ==========================================
# INVENTARIO
# ==========================================

@inventario_bp.route("/inventario")
def inventario():

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    conexion = get_connection()
    cursor = conexion.cursor(dictionary=True)

    # ======================================
    # PRODUCTOS TERMINADOS
    # ======================================

    cursor.execute("""
        SELECT
            p.id_producto,
            p.nombre,
            p.stock_actual,

            COALESCE(
                (
                    SELECT SUM(dp.cantidad)
                    FROM detalle_pedido dp
                    INNER JOIN pedidos pe
                        ON pe.id_pedido = dp.id_pedido
                    WHERE pe.estado IN
                    (
                        'PENDIENTE',
                        'EN_PRODUCCION',
                        'LISTO_PARA_DESPACHO',
                        'EN_RUTA'
                    )
                    AND dp.id_producto = p.id_producto
                ),
                0
            ) AS solicitado

        FROM productos p
        WHERE p.estado = 1
        ORDER BY p.nombre
    """)

    productos = cursor.fetchall()

    # ======================================
    # MATERIAS PRIMAS
    # ======================================

    cursor.execute("""
        SELECT
            mp.id_materia,
            mp.nombre,
            mp.unidad_medida,
            mp.stock_actual,

            COALESCE(
                (
                    SELECT SUM(
                        rp.cantidad_requerida *
                        dp.cantidad
                    )
                    FROM recetas_producto rp

                    INNER JOIN detalle_pedido dp
                        ON dp.id_producto = rp.id_producto

                    INNER JOIN pedidos pe
                        ON pe.id_pedido = dp.id_pedido

                    WHERE pe.estado='PENDIENTE'
                    AND rp.id_materia = mp.id_materia
                ),
                0
            ) AS requerido

        FROM materias_primas mp
        WHERE mp.estado = 1
        ORDER BY mp.nombre
    """)

    materias = cursor.fetchall()

    # ======================================
    # PEDIDOS PENDIENTES
    # ======================================

    cursor.execute("""
        SELECT COUNT(*) total
        FROM pedidos
        WHERE estado='PENDIENTE'
    """)

    hay_pendientes = (
        cursor.fetchone()["total"] > 0
    )

    # ======================================
    # PRODUCCIÓN ACTIVA
    # ======================================

    cursor.execute("""
        SELECT COUNT(*) total
        FROM pedidos
        WHERE estado='EN_PRODUCCION'
    """)

    produccion_activa = (
        cursor.fetchone()["total"] > 0
    )

    # ======================================
    # REINICIO DISPONIBLE
    # ======================================

    cursor.execute("""
        SELECT COUNT(*) total
        FROM pedidos
        WHERE estado='EN_PRODUCCION'
    """)

    puede_reiniciar = (
        cursor.fetchone()["total"] > 0
    )

    # ======================================
    # PENDIENTE DE DESPACHO O EN RUTA
    # ======================================

    cursor.execute("""
            SELECT COUNT(*) total
            FROM pedidos
            WHERE estado in ('LISTO_PARA_DESPACHO','EN_RUTA')
        """)

    pendiente_entregar = (
            cursor.fetchone()["total"] > 0
    )

    cursor.close()
    conexion.close()

    if pendiente_entregar:
        flash(
            "Hay pedidos pendientes de entregar.",
            "danger"
        )

    return render_template(
        "inventario.html",
        productos=productos,
        materias=materias,
        hay_pendientes=hay_pendientes,
        produccion_activa=produccion_activa,
        puede_reiniciar=puede_reiniciar
    )

# ==========================================
# ACTUALIZAR PRODUCTO TERMINADO
# ==========================================

@inventario_bp.route(
    "/inventario/producto/<int:id>",
    methods=["POST"]
)
def actualizar_producto(id):

    cantidad = int(
        request.form["cantidad"]
    )

    conexion = get_connection()
    cursor = conexion.cursor()

    cursor.execute("""
        UPDATE productos
        SET stock_actual =
            stock_actual + %s
        WHERE id_producto=%s
    """,
    (
        cantidad,
        id
    ))

    conexion.commit()

    cursor.close()
    conexion.close()

    flash(
        "Inventario actualizado correctamente.",
        "success"
    )

    return redirect(
        url_for("inventario.inventario")
    )

# ==========================================
# ACTUALIZAR MATERIA PRIMA
# ==========================================

@inventario_bp.route(
    "/inventario/materia/<int:id>",
    methods=["POST"]
)
def actualizar_materia(id):

    cantidad = float(
        request.form["cantidad"]
    )

    conexion = get_connection()
    cursor = conexion.cursor()

    cursor.execute("""
        UPDATE materias_primas
        SET stock_actual =
            stock_actual + %s
        WHERE id_materia=%s
    """,
    (
        cantidad,
        id
    ))

    conexion.commit()

    cursor.close()
    conexion.close()

    flash(
        "Materia prima actualizada.",
        "success"
    )

    return redirect(
        url_for("inventario.inventario")
    )

# ==========================================
# LIMPIAR PRODUCTOS TERMINADOS
# ==========================================

@inventario_bp.route("/inventario/limpiar")
def limpiar_inventario():

    conexion = get_connection()
    cursor = conexion.cursor()

    cursor.execute("""
        UPDATE productos
        SET stock_actual = 0
    """)

    conexion.commit()

    cursor.close()
    conexion.close()

    flash(
        "Inventario reiniciado.",
        "success"
    )

    return redirect(
        url_for("inventario.inventario")
    )

# ==========================================
# INICIAR PRODUCCIÓN
# ==========================================

@inventario_bp.route("/inventario/iniciar")
def iniciar_produccion():

    conexion = get_connection()
    cursor = conexion.cursor(dictionary=True)

    # ======================================
    # CALCULAR CONSUMO DE MATERIAS PRIMAS
    # ======================================

    cursor.execute("""
        SELECT
            mp.id_materia,
            mp.nombre,
            mp.stock_actual,
            mp.stock_minimo,
            mp.unidad_medida,

            COALESCE(
                SUM(
                    rp.cantidad_requerida *
                    dp.cantidad
                ),
                0
            ) AS requerido

        FROM materias_primas mp

        LEFT JOIN recetas_producto rp
            ON mp.id_materia = rp.id_materia

        LEFT JOIN detalle_pedido dp
            ON rp.id_producto = dp.id_producto

        LEFT JOIN pedidos p
            ON dp.id_pedido = p.id_pedido
            AND p.estado='PENDIENTE'

        GROUP BY
            mp.id_materia,
            mp.nombre,
            mp.stock_actual,
            mp.stock_minimo,
            mp.unidad_medida
    """)

    materias = cursor.fetchall()

    # ======================================
    # VERIFICAR MATERIA PRIMA SUFICIENTE
    # ======================================

    for materia in materias:

        requerido = float(
            materia["requerido"] or 0
        )

        nuevo_stock = (
            float(materia["stock_actual"])
            - requerido
        )

        if nuevo_stock < 0:

            descripcion = (
                f"No existe suficiente "
                f"{materia['nombre']} "
                f"para iniciar la producción."
            )

            cursor.execute("""
                INSERT INTO alertas
                (
                    descripcion,
                    estado,
                    fecha_registro
                )
                VALUES
                (
                    %s,
                    'PENDIENTE',
                    NOW()
                )
            """,
            (descripcion,))

            flash(
                descripcion,
                "danger"
            )

            conexion.commit()

            cursor.close()
            conexion.close()

            return redirect(
                url_for("dashboard")
            )

    # ======================================
    # DESCONTAR INVENTARIO
    # ======================================

    for materia in materias:

        requerido = float(
            materia["requerido"] or 0
        )

        nuevo_stock = (
            float(materia["stock_actual"])
            - requerido
        )

        cursor.execute("""
            UPDATE materias_primas
            SET stock_actual=%s
            WHERE id_materia=%s
        """,
        (
            nuevo_stock,
            materia["id_materia"]
        ))

        # ==================================
        # ALERTA STOCK BAJO
        # ==================================

        if nuevo_stock <= materia["stock_minimo"]:

            descripcion = (
                f"La materia prima "
                f"'{materia['nombre']}' "
                f"se encuentra por debajo "
                f"del stock mínimo. "
                f"Existencia actual: "
                f"{nuevo_stock:.4f} "
                f"{materia['unidad_medida']}"
            )

            cursor.execute("""
                INSERT INTO alertas
                (
                    descripcion,
                    estado,
                    fecha_registro
                )
                VALUES
                (
                    %s,
                    'PENDIENTE',
                    NOW()
                )
            """,
            (descripcion,))

    # ======================================
    # CAMBIAR PEDIDOS
    # ======================================

    cursor.execute("""
        UPDATE pedidos
        SET estado='EN_PRODUCCION'
        WHERE estado='PENDIENTE'
    """)

    conexion.commit()

    cursor.close()
    conexion.close()

    flash(
        "Producción iniciada correctamente.",
        "success"
    )

    return redirect(
        url_for("dashboard")
    )

# ==========================================
# FINALIZAR PRODUCCIÓN
# ==========================================

@inventario_bp.route(
    "/inventario/finalizar"
)
def finalizar_produccion():

    conexion = get_connection()
    cursor = conexion.cursor()

    cursor.execute("""
        UPDATE pedidos
        SET estado='LISTO_PARA_DESPACHO'
        WHERE estado='EN_PRODUCCION'
    """)

    afectados = cursor.rowcount

    conexion.commit()

    cursor.close()
    conexion.close()

    if afectados > 0:

        flash(
            "Producción finalizada correctamente.",
            "success"
        )

    return redirect(
        url_for(
            "inventario.inventario"
        )
    )