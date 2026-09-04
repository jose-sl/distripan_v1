from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from database import get_connection
from routes.usuarios import usuarios_bp

app = Flask(__name__)

app.secret_key = "distribuidora_2026"

# ==========================================
# BLUEPRINTS
# ==========================================

app.register_blueprint(
    usuarios_bp
)

# ==========================================

# ==========================
# LOGIN
# ==========================

@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        usuario = request.form["usuario"]
        password = request.form["password"]

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                id_usuario,
                nombre,
                usuario,
                rol
            FROM usuarios
            WHERE usuario = %s
            AND contrasena = %s
            AND estado = TRUE
        """, (
            usuario,
            password
        ))

        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user:

            session["usuario_id"] = user["id_usuario"]
            session["nombre"] = user["nombre"]
            session["rol"] = user["rol"]

            return redirect(
                url_for("dashboard")
            )

        flash(
            "Usuario o contraseña incorrectos",
            "danger"
        )

    return render_template(
        "login.html"
    )

# ==========================
# DASHBOARD
# ==========================

@app.route("/dashboard")
def dashboard():

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT COUNT(*) total
        FROM pedidos
        WHERE estado='PENDIENTE'
    """)
    pedidos_pendientes = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT COUNT(*) total
        FROM pedidos
        WHERE estado='EN_PRODUCCION'
    """)
    pedidos_produccion = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT COUNT(*) total
        FROM rutas_distribucion
        WHERE estado='EN_EJECUCION'
    """)
    rutas_activas = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT COUNT(*) total
        FROM alertas
        WHERE estado='PENDIENTE'
    """)
    alertas_pendientes = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT
            id_alerta,
            descripcion,
            estado
        FROM alertas
        ORDER BY fecha_registro DESC
    """)

    alertas = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "dashboard.html",
        nombre=session["nombre"],
        rol=session["rol"],
        pedidos_pendientes=pedidos_pendientes,
        pedidos_produccion=pedidos_produccion,
        rutas_activas=rutas_activas,
        alertas_pendientes=alertas_pendientes,
        alertas=alertas
    )

# ==========================
# SOLUCIONAR ALERTA
# ==========================

@app.route("/alerta/solucionar/<int:id_alerta>")
def solucionar_alerta(id_alerta):

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE alertas
        SET estado='ATENDIDA'
        WHERE id_alerta=%s
    """, (id_alerta,))

    conn.commit()

    cursor.close()
    conn.close()

    return redirect(
        url_for("dashboard")
    )

# ==========================
# LOGOUT
# ==========================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )

# ==========================
# MAIN
# ==========================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )