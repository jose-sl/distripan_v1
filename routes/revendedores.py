from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from database import get_connection


revendedores_bp = Blueprint(
    'revendedores',
    __name__
)


# =====================================================
# LISTAR
# =====================================================

@revendedores_bp.route('/revendedores')
def listar_revendedores():

    if 'usuario_id' not in session:
        return redirect(
            url_for('login')
        )

    conexion = get_connection()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            r.*,
            u.nombre AS usuario_nombre,
            u.usuario
        FROM revendedores r

        INNER JOIN usuarios u
            ON r.id_usuario = u.id_usuario

        ORDER BY r.nombre
    """)

    revendedores = cursor.fetchall()

    cursor.close()
    conexion.close()

    return render_template(
        'revendedores.html',
        revendedores=revendedores
    )


# =====================================================
# AGREGAR
# =====================================================

@revendedores_bp.route(
    '/revendedores/agregar',
    methods=['GET', 'POST']
)
def agregar_revendedor():

    if 'usuario_id' not in session:
        return redirect(
            url_for('login')
        )

    conexion = get_connection()
    cursor = conexion.cursor(dictionary=True)

    if request.method == 'POST':

        nombre = request.form['nombre']

        direccion = request.form['direccion']

        telefono = request.form['telefono']

        zona = request.form['zona']

        latitud = (
            request.form['latitud']
            or None
        )

        longitud = (
            request.form['longitud']
            or None
        )

        estado = request.form['estado']

        # -------------------------------------------------
        # USUARIO RESPONSABLE
        # -------------------------------------------------
        #
        # Si el formulario contiene id_usuario,
        # se utiliza ese usuario.
        #
        # Si no lo contiene, se utiliza el usuario
        # actualmente conectado.
        #
        # Esto permite que el formulario actual
        # revendedores_agregar.html siga funcionando.
        # -------------------------------------------------

        id_usuario = request.form.get(
            'id_usuario'
        )

        if not id_usuario:

            id_usuario = session['usuario_id']

        cursor.execute("""
            INSERT INTO revendedores
            (
                nombre,
                direccion,
                telefono,
                zona,
                latitud,
                longitud,
                estado,
                id_usuario
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
        """,
        (
            nombre,
            direccion,
            telefono,
            zona,
            latitud,
            longitud,
            estado,
            id_usuario
        ))

        conexion.commit()

        cursor.close()
        conexion.close()

        flash(
            'Revendedor agregado correctamente',
            'success'
        )

        return redirect(
            url_for(
                'revendedores.listar_revendedores'
            )
        )


    # =================================================
    # USUARIOS DISPONIBLES
    # =================================================

    cursor.execute("""
        SELECT
            id_usuario,
            nombre,
            usuario
        FROM usuarios
        WHERE estado=1
        ORDER BY nombre
    """)

    usuarios = cursor.fetchall()

    cursor.close()
    conexion.close()

    return render_template(
        'revendedores_agregar.html',
        usuarios=usuarios
    )


# =====================================================
# EDITAR
# =====================================================

@revendedores_bp.route(
    '/revendedores/editar/<int:id>',
    methods=['GET', 'POST']
)
def editar_revendedor(id):

    if 'usuario_id' not in session:
        return redirect(
            url_for('login')
        )

    conexion = get_connection()
    cursor = conexion.cursor(dictionary=True)

    if request.method == 'POST':

        nombre = request.form['nombre']

        direccion = request.form['direccion']

        telefono = request.form['telefono']

        zona = request.form['zona']

        latitud = (
            request.form['latitud']
            or None
        )

        longitud = (
            request.form['longitud']
            or None
        )

        estado = request.form['estado']

        id_usuario = request.form['id_usuario']


        cursor.execute("""
            UPDATE revendedores

            SET
                nombre=%s,
                direccion=%s,
                telefono=%s,
                zona=%s,
                latitud=%s,
                longitud=%s,
                estado=%s,
                id_usuario=%s

            WHERE id_revendedor=%s
        """,
        (
            nombre,
            direccion,
            telefono,
            zona,
            latitud,
            longitud,
            estado,
            id_usuario,
            id
        ))

        conexion.commit()

        cursor.close()
        conexion.close()

        flash(
            'Revendedor actualizado correctamente',
            'success'
        )

        return redirect(
            url_for(
                'revendedores.listar_revendedores'
            )
        )


    # =================================================
    # OBTENER REVENDEDOR
    # =================================================

    cursor.execute("""
        SELECT
            *
        FROM revendedores
        WHERE id_revendedor=%s
    """,
    (id,))

    revendedor = cursor.fetchone()


    # =================================================
    # OBTENER USUARIOS
    # =================================================

    cursor.execute("""
        SELECT
            id_usuario,
            nombre,
            usuario
        FROM usuarios
        WHERE estado=1
        ORDER BY nombre
    """)

    usuarios = cursor.fetchall()

    cursor.close()
    conexion.close()


    return render_template(
        'revendedores_editar.html',
        revendedor=revendedor,
        usuarios=usuarios
    )


# =====================================================
# VER
# =====================================================

@revendedores_bp.route(
    '/revendedores/ver/<int:id>'
)
def ver_revendedor(id):

    if 'usuario_id' not in session:
        return redirect(
            url_for('login')
        )

    conexion = get_connection()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            r.*,
            u.nombre AS usuario_nombre,
            u.usuario
        FROM revendedores r

        INNER JOIN usuarios u
            ON r.id_usuario = u.id_usuario

        WHERE r.id_revendedor=%s
    """,
    (id,))

    revendedor = cursor.fetchone()

    cursor.close()
    conexion.close()

    return render_template(
        'revendedores_ver.html',
        revendedor=revendedor
    )