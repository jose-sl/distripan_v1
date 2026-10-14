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
from routes.rutas import rutas_bp

# Blueprints
from routes.usuarios import usuarios_bp
from routes.revendedores import revendedores_bp
from routes.pedidos import pedidos_bp
from routes.inventario import inventario_bp
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.wrappers import Response
from werkzeug.serving import run_simple
from werkzeug.security import check_password_hash

app = Flask(__name__)

app.secret_key = "distribuidora_secret_key"

# =====================================================
# REGISTRO DE BLUEPRINTS
# =====================================================

app.register_blueprint(usuarios_bp)
app.register_blueprint(revendedores_bp)
app.register_blueprint(pedidos_bp)
app.register_blueprint(inventario_bp)
app.register_blueprint(rutas_bp)

# =====================================================
# LOGIN
# =====================================================

@app.route('/', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        usuario = request.form['usuario']
        password = request.form['password']

        conexion = get_connection()
        cursor = conexion.cursor(dictionary=True)

        cursor.execute("""
            SELECT *
            FROM usuarios
            WHERE usuario=%s
            AND estado=%s
        """,
        (
            usuario,
            1
        ))

        usuario_db = cursor.fetchone()

        cursor.close()
        conexion.close()

        if usuario_db:

            if check_password_hash(usuario_db['contrasena'], password):

                session['usuario_id'] = usuario_db['id_usuario']
                session['nombre'] = usuario_db['nombre']
                session['usuario'] = usuario_db['usuario']
                session['rol'] = usuario_db['rol']

                if session['rol'] == 'REVENDEDOR':
                    return redirect(
                        url_for('pedidos.listar_pedidos')
                    )
                elif session['rol'] == 'DESPACHO':
                    return redirect(
                        url_for('rutas.listar_rutas')
                    )
                elif session['rol'] == 'PRODUCCION':
                    return redirect(
                        url_for('inventario.inventario')
                    )
                else:
                    return redirect(
                        url_for('dashboard')
                    )

        flash(
            'Usuario o contraseña incorrectos',
            'danger'
        )

    return render_template(
        'login.html'
    )

# =====================================================
# DASHBOARD
# =====================================================

@app.route('/dashboard')
def dashboard():

    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    conexion = get_connection()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        SELECT COUNT(*) total
        FROM pedidos
        WHERE estado='PENDIENTE'
    """)
    pedidos_pendientes = cursor.fetchone()['total']

    cursor.execute("""
        SELECT COUNT(*) total
        FROM pedidos
        WHERE estado='EN_PRODUCCION'
    """)
    pedidos_produccion = cursor.fetchone()['total']

    cursor.execute("""
        SELECT COUNT(*) total
        FROM rutas_distribucion
        WHERE estado='EN_EJECUCION'
    """)
    rutas_activas = cursor.fetchone()['total']

    cursor.execute("""
        SELECT COUNT(*) total
        FROM alertas
        WHERE estado='PENDIENTE'
    """)
    alertas_pendientes = cursor.fetchone()['total']

    cursor.execute("""
        SELECT *
        FROM alertas
        ORDER BY FIELD(estado, 'PENDIENTE', 'ATENDIDA')
        LIMIT 50
    """)

    alertas = cursor.fetchall()

    cursor.close()
    conexion.close()

    return render_template(
        'dashboard.html',
        nombre=session['nombre'],
        rol=session['rol'],
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

    conexion = get_connection()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        UPDATE alertas
        SET estado='ATENDIDA'
        WHERE id_alerta=%s
    """, (id_alerta,))

    conexion.commit()

    cursor.close()
    conexion.close()

    return redirect(
        url_for("dashboard")
    )

# ==========================
# LOGOUT
# =====================================================

@app.route('/logout')
def logout():

    session.clear()

    return redirect(
        url_for('login')
    )

# =====================================================
# PREFIJO UNIVERSAL
# =====================================================

app_prefijada = DispatcherMiddleware(
    Response("Página no encontrada", status=404),
    {
        "/distri_pan_v1": app
    }
)

# =====================================================
# MAIN
# =====================================================

if __name__ == '__main__':
    run_simple(
        hostname="0.0.0.0",
        port=5000,
        application=app_prefijada,
        use_debugger=True,
        use_reloader=True
    )