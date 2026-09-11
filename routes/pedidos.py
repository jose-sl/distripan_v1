from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database import get_connection

pedidos_bp = Blueprint("pedidos", __name__, url_prefix="/pedidos")


# ==========================================================
# LISTAR PEDIDOS
# ==========================================================

@pedidos_bp.route("/")
def listar_pedidos():

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    usuario_id = session["usuario_id"]
    rol = session["rol"]

    conexion = get_connection()
    cursor = conexion.cursor(dictionary=True)

    if rol == "REVENDEDOR":

        cursor.execute("""
            SELECT
                p.id_pedido,
                r.nombre AS revendedor,
                p.fecha_pedido,
                p.estado,
                p.total
            FROM pedidos p
            INNER JOIN revendedores r
                ON p.id_revendedor = r.id_revendedor
            WHERE p.id_usuario = %s
            AND P.fecha_pedido >= DATE_SUB(CURDATE(), INTERVAL 5 DAY)
            ORDER BY FIELD(p.estado, 'PENDIENTE', 'EN_PRODUCCION', 'LISTO_PARA_DESPACHO', 'EN_RUTA', 'ENTREGADO', 'CANCELADO')
        """, (usuario_id,))

    else:

        cursor.execute("""
            SELECT
                p.id_pedido,
                r.nombre AS revendedor,
                p.fecha_pedido,
                p.estado,
                p.total
            FROM pedidos p
            INNER JOIN revendedores r
                ON p.id_revendedor = r.id_revendedor
            ORDER BY FIELD(p.estado, 'PENDIENTE', 'EN_PRODUCCION', 'LISTO_PARA_DESPACHO', 'EN_RUTA', 'ENTREGADO', 'CANCELADO')
        """)

    pedidos = cursor.fetchall()

    cursor.close()
    conexion.close()

    return render_template(
        "pedidos.html",
        pedidos=pedidos
    )


# ==========================================================
# VER PEDIDO
# ==========================================================

@pedidos_bp.route("/ver/<int:id>", methods=["GET", "POST"])
def ver_pedido(id):

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    usuario_id = session["usuario_id"]

    conexion = get_connection()
    cursor = conexion.cursor(dictionary=True)

    # ------------------------------------------------------
    # Verificar que el pedido pertenezca al usuario.
    # ------------------------------------------------------

    cursor.execute("""
        SELECT
            p.*,
            r.nombre AS revendedor
        FROM pedidos p
        INNER JOIN revendedores r
            ON p.id_revendedor = r.id_revendedor
        WHERE p.id_pedido = %s
    """, (id,))

    pedido = cursor.fetchone()

    if not pedido:

        cursor.close()
        conexion.close()

        flash(
            "El pedido no existe.",
            "danger"
        )

        return redirect(
            url_for("pedidos.listar_pedidos")
        )

    # ======================================================
    # GET
    # ======================================================

    # ------------------------------------------------------
    # Obtener cantidades existentes.
    # ------------------------------------------------------

    cursor.execute("""
        SELECT
            id_producto,
            cantidad
        FROM detalle_pedido
        WHERE id_pedido = %s
    """, (id,))

    detalles = cursor.fetchall()

    cantidades_guardadas = {}

    for detalle in detalles:
        cantidades_guardadas[
            detalle["id_producto"]
        ] = detalle["cantidad"]

    # ------------------------------------------------------
    # Obtener todos los productos activos.
    # ------------------------------------------------------

    cursor.execute("""
        SELECT
            id_producto,
            nombre,
            precio
        FROM productos
        WHERE estado = 1
        ORDER BY nombre
    """)

    productos_db = cursor.fetchall()

    # ------------------------------------------------------
    # Agregar la cantidad guardada a cada producto.
    # ------------------------------------------------------

    productos = []

    for producto in productos_db:

        producto["cantidad"] = cantidades_guardadas.get(
            producto["id_producto"],
            0
        )

        productos.append(producto)

    cursor.close()
    conexion.close()

    return render_template(
        "pedidos_ver.html",
        pedido=pedido,
        productos=productos
    )


# ==========================================================
# AGREGAR PEDIDO
# ==========================================================

@pedidos_bp.route("/agregar", methods=["GET", "POST"])
def agregar_pedido():

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    usuario_id = session["usuario_id"]
    rol = session["rol"]

    # ------------------------------------------------------
    # Solo los usuarios con rol REVENDEDOR pueden crear
    # pedidos.
    # ------------------------------------------------------

    if rol != "REVENDEDOR":
        flash(
            "No tiene permisos para registrar pedidos.",
            "danger"
        )
        return redirect(url_for("pedidos.listar_pedidos"))

    conexion = get_connection()
    cursor = conexion.cursor(dictionary=True)

    # ======================================================
    # POST
    # ======================================================

    if request.method == "POST":

        id_revendedor = request.form.get("id_revendedor")

        # --------------------------------------------------
        # Obtener los arreglos enviados por el formulario.
        # --------------------------------------------------

        id_productos = request.form.getlist("id_producto[]")
        cantidades = request.form.getlist("cantidad[]")

        # --------------------------------------------------
        # Validar revendedor
        # --------------------------------------------------

        if not id_revendedor:
            cursor.close()
            conexion.close()

            flash(
                "Debe seleccionar un revendedor.",
                "danger"
            )

            return redirect(
                url_for("pedidos.agregar_pedido")
            )

        # --------------------------------------------------
        # Verificar que el revendedor pertenezca al usuario
        # que está registrando el pedido.
        # --------------------------------------------------

        cursor.execute("""
            SELECT id_revendedor
            FROM revendedores
            WHERE id_revendedor = %s
            AND id_usuario = %s
            AND estado = 1
        """, (id_revendedor, usuario_id))

        revendedor = cursor.fetchone()

        if not revendedor:

            cursor.close()
            conexion.close()

            flash(
                "El revendedor seleccionado no es válido.",
                "danger"
            )

            return redirect(
                url_for("pedidos.agregar_pedido")
            )

        # --------------------------------------------------
        # Validar que existan productos.
        # --------------------------------------------------

        if not id_productos or not cantidades:

            cursor.close()
            conexion.close()

            flash(
                "No se recibieron productos para el pedido.",
                "danger"
            )

            return redirect(
                url_for("pedidos.agregar_pedido")
            )

        if len(id_productos) != len(cantidades):

            cursor.close()
            conexion.close()

            flash(
                "Los datos de los productos no son válidos.",
                "danger"
            )

            return redirect(
                url_for("pedidos.agregar_pedido")
            )

        try:

            # ------------------------------------------------
            # Crear el pedido inicialmente con total 0.
            # ------------------------------------------------

            cursor.execute("""
                INSERT INTO pedidos (
                    id_distribuidora,
                    id_revendedor,
                    id_usuario,
                    id_ruta,
                    estado,
                    total
                )
                VALUES (
                    1,
                    %s,
                    %s,
                    NULL,
                    'PENDIENTE',
                    0
                )
            """, (
                id_revendedor,
                usuario_id
            ))

            id_pedido = cursor.lastrowid

            total = 0
            productos_insertados = 0

            # ----------------------------------------------
            # Recorrer todos los productos enviados.
            # ----------------------------------------------

            for i in range(len(id_productos)):

                try:
                    id_producto = int(id_productos[i])
                    cantidad = int(cantidades[i])
                except (ValueError, TypeError):
                    continue

                # ------------------------------------------
                # Ignorar cantidades cero o negativas.
                # ------------------------------------------

                if cantidad <= 0:
                    continue

                # ------------------------------------------
                # Obtener el precio REAL desde la base de
                # datos. No se utiliza el precio enviado por
                # HTML para evitar manipulaciones.
                # ------------------------------------------

                cursor.execute("""
                    SELECT
                        id_producto,
                        precio
                    FROM productos
                    WHERE id_producto = %s
                    AND estado = 1
                """, (id_producto,))

                producto = cursor.fetchone()

                if not producto:
                    continue

                precio_unitario = float(producto["precio"])

                subtotal = precio_unitario * cantidad

                # ------------------------------------------
                # Insertar detalle del pedido.
                # ------------------------------------------

                cursor.execute("""
                    INSERT INTO detalle_pedido (
                        id_pedido,
                        id_producto,
                        cantidad,
                        precio_unitario,
                        subtotal
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    )
                """, (
                    id_pedido,
                    id_producto,
                    cantidad,
                    precio_unitario,
                    subtotal
                ))

                total += subtotal
                productos_insertados += 1

            # ------------------------------------------------
            # Verificar que por lo menos un producto haya sido
            # agregado.
            # ------------------------------------------------

            if productos_insertados == 0:

                conexion.rollback()

                cursor.close()
                conexion.close()

                flash(
                    "Debe ingresar una cantidad mayor que 0 "
                    "para al menos un producto.",
                    "danger"
                )

                return redirect(
                    url_for("pedidos.agregar_pedido")
                )

            # ------------------------------------------------
            # Actualizar el total del pedido.
            # ------------------------------------------------

            cursor.execute("""
                UPDATE pedidos
                SET total = %s
                WHERE id_pedido = %s
            """, (
                total,
                id_pedido
            ))

            conexion.commit()

            cursor.close()
            conexion.close()

            flash(
                "Pedido registrado correctamente.",
                "success"
            )

            return redirect(
                url_for("pedidos.listar_pedidos")
            )

        except Exception as error:

            conexion.rollback()

            cursor.close()
            conexion.close()

            print("ERROR AL REGISTRAR PEDIDO:", error)

            flash(
                "Ocurrió un error al registrar el pedido.",
                "danger"
            )

            return redirect(
                url_for("pedidos.agregar_pedido")
            )

    # ======================================================
    # GET
    # ======================================================

    cursor.execute("""
        SELECT
            id_revendedor,
            nombre
        FROM revendedores
        WHERE id_usuario = %s
        AND estado = 1
        ORDER BY nombre
    """, (usuario_id,))

    revendedores = cursor.fetchall()

    cursor.execute("""
        SELECT
            id_producto,
            nombre,
            precio
        FROM productos
        WHERE estado = 1
        ORDER BY nombre
    """)

    productos = cursor.fetchall()

    cursor.close()
    conexion.close()

    return render_template(
        "pedidos_agregar.html",
        revendedores=revendedores,
        productos=productos
    )


# ==========================================================
# EDITAR PEDIDO
# ==========================================================

@pedidos_bp.route("/editar/<int:id>", methods=["GET", "POST"])
def editar_pedido(id):

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    usuario_id = session["usuario_id"]
    rol = session["rol"]

    if rol != "REVENDEDOR":
        flash(
            "No tiene permisos para modificar pedidos.",
            "danger"
        )
        return redirect(url_for("pedidos.listar_pedidos"))

    conexion = get_connection()
    cursor = conexion.cursor(dictionary=True)

    # ------------------------------------------------------
    # Verificar que el pedido pertenezca al usuario.
    # ------------------------------------------------------

    cursor.execute("""
        SELECT
            p.*,
            r.nombre AS revendedor
        FROM pedidos p
        INNER JOIN revendedores r
            ON p.id_revendedor = r.id_revendedor
        WHERE p.id_pedido = %s
        AND p.id_usuario = %s
    """, (id, usuario_id))

    pedido = cursor.fetchone()

    if not pedido:

        cursor.close()
        conexion.close()

        flash(
            "El pedido no existe o no tiene permisos para modificarlo.",
            "danger"
        )

        return redirect(
            url_for("pedidos.listar_pedidos")
        )

    # ======================================================
    # POST
    # ======================================================

    if request.method == "POST":

        id_productos = request.form.getlist("id_producto[]")
        cantidades = request.form.getlist("cantidad[]")

        if not id_productos or not cantidades:

            cursor.close()
            conexion.close()

            flash(
                "No se recibieron productos.",
                "danger"
            )

            return redirect(
                url_for("pedidos.editar_pedido", id=id)
            )

        try:

            # ----------------------------------------------
            # Eliminar detalles anteriores.
            # ----------------------------------------------

            cursor.execute("""
                DELETE FROM detalle_pedido
                WHERE id_pedido = %s
            """, (id,))

            total = 0
            productos_insertados = 0

            # ----------------------------------------------
            # Insertar nuevamente los detalles.
            # ----------------------------------------------

            for i in range(len(id_productos)):

                try:
                    id_producto = int(id_productos[i])
                    cantidad = int(cantidades[i])
                except (ValueError, TypeError):
                    continue

                if cantidad <= 0:
                    continue

                cursor.execute("""
                    SELECT
                        id_producto,
                        precio
                    FROM productos
                    WHERE id_producto = %s
                    AND estado = 1
                """, (id_producto,))

                producto = cursor.fetchone()

                if not producto:
                    continue

                precio_unitario = float(producto["precio"])
                subtotal = precio_unitario * cantidad

                cursor.execute("""
                    INSERT INTO detalle_pedido (
                        id_pedido,
                        id_producto,
                        cantidad,
                        precio_unitario,
                        subtotal
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    )
                """, (
                    id,
                    id_producto,
                    cantidad,
                    precio_unitario,
                    subtotal
                ))

                total += subtotal
                productos_insertados += 1

            if productos_insertados == 0:

                conexion.rollback()

                cursor.close()
                conexion.close()

                flash(
                    "Debe ingresar una cantidad mayor que 0 "
                    "para al menos un producto.",
                    "danger"
                )

                return redirect(
                    url_for("pedidos.editar_pedido", id=id)
                )

            # ----------------------------------------------
            # Actualizar total.
            # ----------------------------------------------

            cursor.execute("""
                UPDATE pedidos
                SET total = %s
                WHERE id_pedido = %s
            """, (
                total,
                id
            ))

            conexion.commit()

            cursor.close()
            conexion.close()

            flash(
                "Pedido modificado correctamente.",
                "success"
            )

            return redirect(
                url_for("pedidos.listar_pedidos")
            )

        except Exception as error:

            conexion.rollback()

            cursor.close()
            conexion.close()

            print("ERROR AL MODIFICAR PEDIDO:", error)

            flash(
                "Ocurrió un error al modificar el pedido.",
                "danger"
            )

            return redirect(
                url_for("pedidos.editar_pedido", id=id)
            )

    # ======================================================
    # GET
    # ======================================================

    # ------------------------------------------------------
    # Obtener cantidades existentes.
    # ------------------------------------------------------

    cursor.execute("""
        SELECT
            id_producto,
            cantidad
        FROM detalle_pedido
        WHERE id_pedido = %s
    """, (id,))

    detalles = cursor.fetchall()

    cantidades_guardadas = {}

    for detalle in detalles:
        cantidades_guardadas[
            detalle["id_producto"]
        ] = detalle["cantidad"]

    # ------------------------------------------------------
    # Obtener todos los productos activos.
    # ------------------------------------------------------

    cursor.execute("""
        SELECT
            id_producto,
            nombre,
            precio
        FROM productos
        WHERE estado = 1
        ORDER BY nombre
    """)

    productos_db = cursor.fetchall()

    # ------------------------------------------------------
    # Agregar la cantidad guardada a cada producto.
    # ------------------------------------------------------

    productos = []

    for producto in productos_db:

        producto["cantidad"] = cantidades_guardadas.get(
            producto["id_producto"],
            0
        )

        productos.append(producto)

    cursor.close()
    conexion.close()

    return render_template(
        "pedidos_editar.html",
        pedido=pedido,
        productos=productos
    )


# ==========================================================
# CANCELAR PEDIDO
# ==========================================================

@pedidos_bp.route("/cancelar/<int:id>")
def cancelar_pedido(id):

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    usuario_id = session["usuario_id"]
    rol = session["rol"]

    if rol != "REVENDEDOR":
        flash(
            "No tiene permisos para eliminar pedidos.",
            "danger"
        )
        return redirect(url_for("pedidos.listar_pedidos"))

    conexion = get_connection()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        SELECT id_pedido
        FROM pedidos
        WHERE id_pedido = %s
        AND id_usuario = %s
    """, (id, usuario_id))

    pedido = cursor.fetchone()

    if not pedido:

        cursor.close()
        conexion.close()

        flash(
            "El pedido no existe o no tiene permisos para eliminarlo.",
            "danger"
        )

        return redirect(
            url_for("pedidos.listar_pedidos")
        )

    try:

        cursor.execute("""
            UPDATE pedidos
            SET estado = 'CANCELADO'
            WHERE id_pedido = %s
            AND id_usuario = %s
        """, (id, usuario_id))

        conexion.commit()

        cursor.close()
        conexion.close()

        flash(
            "El pedido fue cancelado.",
            "success"
        )

    except Exception as error:

        conexion.rollback()

        cursor.close()
        conexion.close()

        print("ERROR AL CANCELAR PEDIDO:", error)

        flash(
            "Ocurrió un error al cancelar el pedido.",
            "danger"
        )

    return redirect(
        url_for("pedidos.listar_pedidos")
    )