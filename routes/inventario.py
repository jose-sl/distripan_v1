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
                    WHERE pe.estado='PENDIENTE'
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

    cursor.close()
    conexion.close()

    return render_template(
        "inventario.html",
        productos=productos,
        materias=materias
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
    cursor = conexion.cursor()

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
        url_for("inventario.inventario")
    )