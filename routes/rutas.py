from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    session,
    flash
)

from routes.permisos import roles_requeridos
from database import get_connection

import folium
from folium.plugins import PolyLineTextPath
import openrouteservice

from config import ORS_API_KEY, LAT_ORIGEN, LON_ORIGEN

rutas_bp = Blueprint(
    "rutas",
    __name__
)

# ==========================================
# MOSTRAR RUTAS
# ==========================================

@rutas_bp.route("/rutas")
@roles_requeridos("ADMINISTRADOR","DESPACHO")
def listar_rutas():

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    conexion = get_connection()
    cursor = conexion.cursor(dictionary=True)

    # ======================================
    # VALIDAR PEDIDOS EN RUTA
    # ======================================

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM pedidos
        WHERE estado = 'EN_RUTA'
    """)

    resultado = cursor.fetchone()

    total_en_ruta = resultado["total"]

    # ======================================
    # OBTENER REVENDEDORES
    # ======================================

    if total_en_ruta > 0:

        # ----------------------------------
        # RUTA ACTIVA
        # ----------------------------------

        cursor.execute("""
            SELECT DISTINCT
                r.id_revendedor,
                r.nombre,
                r.direccion,
                r.latitud,
                r.longitud
            FROM revendedores r

            INNER JOIN pedidos p
                ON p.id_revendedor = r.id_revendedor

            WHERE p.estado = 'EN_RUTA'

            ORDER BY r.nombre
        """)

        revendedores = cursor.fetchall()

        mostrar_iniciar = False
        mostrar_finalizar = True

    else:

        # ----------------------------------
        # PEDIDOS LISTOS PARA DESPACHO
        # ----------------------------------

        cursor.execute("""
            SELECT DISTINCT
                r.id_revendedor,
                r.nombre,
                r.direccion,
                r.latitud,
                r.longitud
            FROM revendedores r

            INNER JOIN pedidos p
                ON p.id_revendedor = r.id_revendedor

            WHERE p.estado = 'LISTO_PARA_DESPACHO'

            ORDER BY r.nombre
        """)

        revendedores = cursor.fetchall()

        mostrar_iniciar = len(revendedores) > 0
        mostrar_finalizar = False

    # ======================================
    # CREAR MAPA
    # ======================================

    mapa = folium.Map(
        location=[
            LAT_ORIGEN,
            LON_ORIGEN
        ],
        zoom_start=15,
        control_scale=True
    )

    # ======================================
    # MARCADOR DE ORIGEN
    # ======================================

    folium.Marker(
        [
            LAT_ORIGEN,
            LON_ORIGEN
        ],

        popup="""
            <b>Distribuidora SF</b>
        """,

        tooltip="Distribuidora SF",

        icon=folium.DivIcon(
            html="""
                <div style="
                    background:#28a745;
                    color:white;
                    border-radius:50%;
                    width:30px;
                    height:30px;
                    text-align:center;
                    line-height:30px;
                    font-weight:bold;
                    border:2px solid white;
                    box-shadow:0 1px 4px rgba(0,0,0,0.5);
                ">
                    O
                </div>
            """
        )
    ).add_to(mapa)

    # ======================================
    # COORDENADAS PARA LA RUTA
    # ======================================

    coordenadas = [
        [
            LON_ORIGEN,
            LAT_ORIGEN
        ]
    ]

    contador = 1

    # ======================================
    # MARCADORES DE REVENDEDORES
    # ======================================

    for rev in revendedores:

        if (
            rev["latitud"] is None or
            rev["longitud"] is None
        ):
            continue

        latitud = float(
            rev["latitud"]
        )

        longitud = float(
            rev["longitud"]
        )

        nombre = rev["nombre"]

        direccion = rev["direccion"]

        # ----------------------------------
        # MARCADOR
        # ----------------------------------

        folium.Marker(

            [
                latitud,
                longitud
            ],

            popup=f"""
                <div style="min-width:180px;">
                    <b>{contador}</b><br>
                    <strong>{nombre}</strong><br>
                    {direccion if direccion else ""}
                </div>
            """,

            tooltip=f"""
                {contador}: {nombre}
            """,

            icon=folium.DivIcon(

                html=f"""
                    <div style="
                        background:#dc3545;
                        color:white;
                        border-radius:50%;
                        width:30px;
                        height:30px;
                        text-align:center;
                        line-height:30px;
                        font-weight:bold;
                        border:2px solid white;
                        box-shadow:0 1px 4px rgba(0,0,0,0.5);
                    ">
                        {contador}
                    </div>
                """
            )
        ).add_to(mapa)

        # ----------------------------------
        # AGREGAR PUNTO A LA RUTA
        # ----------------------------------

        coordenadas.append(
            [
                longitud,
                latitud
            ]
        )

        contador += 1

    # ======================================
    # REGRESAR AL ORIGEN
    # ======================================

    if len(coordenadas) > 1:

        coordenadas.append(
            [
                LON_ORIGEN,
                LAT_ORIGEN
            ]
        )

    # ======================================
    # GENERAR RUTA POR CALLES
    # ======================================

    if len(coordenadas) > 2:

        try:

            cliente = openrouteservice.Client(
                key=ORS_API_KEY
            )

            ruta = cliente.directions(

                coordinates=coordenadas,

                profile="driving-car",

                format="geojson"

            )

            # ----------------------------------
            # DIBUJAR RUTA
            # ----------------------------------

            geojson = folium.GeoJson(

                ruta,

                style_function=lambda feature: {
                    "color": "#0066ff",
                    "weight": 6,
                    "opacity": 0.85
                }

            ).add_to(mapa)

            # ----------------------------------
            # AGREGAR FLECHAS
            # ----------------------------------

            PolyLineTextPath(

                geojson,

                "➜",

                repeat=True,

                offset=8,

                attributes={
                    "fill": "#0066ff",
                    "font-weight": "bold",
                    "font-size": "18"
                }

            ).add_to(mapa)

        except Exception as error:

            print(
                "Error al generar la ruta:",
                error
            )

    # ======================================
    # GENERAR HTML DEL MAPA
    # ======================================

    mapa_html = mapa._repr_html_()

    cursor.close()
    conexion.close()

    # ======================================
    # MOSTRAR PÁGINA
    # ======================================

    return render_template(
        "rutas.html",

        mapa=mapa_html,

        total_revendedores=len(
            revendedores
        ),

        mostrar_iniciar=mostrar_iniciar,

        mostrar_finalizar=mostrar_finalizar
    )


# ==========================================
# INICIAR RUTA
# ==========================================

@rutas_bp.route("/rutas/iniciar")
@roles_requeridos("ADMINISTRADOR","DESPACHO")
def iniciar_ruta():

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    conexion = get_connection()
    cursor = conexion.cursor()

    # ======================================
    # CAMBIAR PEDIDOS A EN_RUTA
    # ======================================

    cursor.execute("""
        UPDATE pedidos

        SET estado = 'EN_RUTA'

        WHERE estado = 'LISTO_PARA_DESPACHO'
    """)

    cantidad = cursor.rowcount

    conexion.commit()

    cursor.close()
    conexion.close()

    # ======================================
    # MENSAJE
    # ======================================

    if cantidad > 0:

        flash(
            "Ruta iniciada correctamente.",
            "success"
        )

    else:

        flash(
            "No existen pedidos listos para despacho.",
            "warning"
        )

    return redirect(
        url_for(
            "rutas.listar_rutas"
        )
    )


# ==========================================
# FINALIZAR RUTA
# ==========================================

@rutas_bp.route("/rutas/finalizar")
@roles_requeridos("ADMINISTRADOR","DESPACHO")
def finalizar_ruta():

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    conexion = get_connection()
    cursor = conexion.cursor()

    # ======================================
    # CAMBIAR PEDIDOS A ENTREGADO
    # ======================================

    cursor.execute("""
        UPDATE pedidos

        SET estado = 'ENTREGADO'

        WHERE estado = 'EN_RUTA'
    """)

    cantidad = cursor.rowcount

    conexion.commit()

    cursor.close()
    conexion.close()

    # ======================================
    # MENSAJE
    # ======================================

    if cantidad > 0:

        flash(
            "Ruta finalizada correctamente. "
            "Los pedidos fueron marcados como entregados.",
            "success"
        )

    else:

        flash(
            "No existen pedidos actualmente en ruta.",
            "warning"
        )

    return redirect(
        url_for(
            "rutas.listar_rutas"
        )
    )