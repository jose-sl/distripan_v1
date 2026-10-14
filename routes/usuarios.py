from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from routes.permisos import roles_requeridos
from database import get_connection
from werkzeug.security import generate_password_hash

usuarios_bp = Blueprint(
    "usuarios",
    __name__
)

# ==========================
# LISTAR
# ==========================

@usuarios_bp.route("/usuarios")
@roles_requeridos("ADMINISTRADOR")
def listar_usuarios():

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT *
                FROM usuarios
                ORDER BY nombre
            """)

            usuarios = cursor.fetchall()

            cursor.close()
        except:
            conn.rollback()
            flash(
                "No fue posible consultar la base de datos.",
                "danger")

        finally:
            cursor.close()
            conn.close()

    except:
        flash(
            "No fue posible conectarse a la base de datos.",
            "danger"
        )

    return render_template(
        "usuarios.html",
        usuarios=usuarios
    )



# ==========================
# VER
# ==========================

@usuarios_bp.route("/usuarios/ver/<int:id>")
@roles_requeridos("ADMINISTRADOR")
def ver_usuario(id):

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM usuarios
        WHERE id_usuario=%s
    """, (id,))

    usuario = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template(
        "usuarios_ver.html",
        usuario=usuario
    )

# ==========================
# AGREGAR
# ==========================

@usuarios_bp.route("/usuarios/agregar", methods=["GET","POST"])
@roles_requeridos("ADMINISTRADOR")
def agregar_usuario():

    if request.method == "POST":

        if request.form["contrasena"] != request.form["confirmar"]:

            flash(
                "Las contraseñas no coinciden",
                "danger"
            )

            return redirect(
                url_for(
                    "usuarios.agregar_usuario"
                )
            )

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO usuarios
            (
                nombre,
                usuario,
                contrasena,
                rol,
                estado
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s
            )
        """, (
            request.form["nombre"],
            request.form["usuario"],
            generate_password_hash(request.form["contrasena"]),
            request.form["rol"],
            request.form["estado"]
        ))

        conn.commit()

        cursor.close()
        conn.close()

        return redirect(
            url_for(
                "usuarios.listar_usuarios"
            )
        )

    return render_template(
        "usuarios_agregar.html"
    )

# ==========================
# EDITAR
# ==========================

@usuarios_bp.route("/usuarios/editar/<int:id>", methods=["GET","POST"])
@roles_requeridos("ADMINISTRADOR")
def editar_usuario(id):

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":

        cursor.execute("""
            UPDATE usuarios
            SET
                nombre=%s,
                usuario=%s,
                rol=%s,
                estado=%s
            WHERE id_usuario=%s
        """, (
            request.form["nombre"],
            request.form["usuario"],
            request.form["rol"],
            request.form["estado"],
            id
        ))

        if request.form["contrasena"] != "":

            cursor.execute("""
                UPDATE usuarios
                SET contrasena=%s
                WHERE id_usuario=%s
            """, (
                generate_password_hash(request.form["contrasena"]),
                id
            ))

        conn.commit()

        return redirect(
            url_for(
                "usuarios.listar_usuarios"
            )
        )

    cursor.execute("""
        SELECT *
        FROM usuarios
        WHERE id_usuario=%s
    """, (id,))

    usuario = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template(
        "usuarios_editar.html",
        usuario=usuario
    )