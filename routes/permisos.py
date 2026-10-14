from functools import wraps

from flask import (
    session,
    redirect,
    url_for,
    flash
)


def roles_requeridos(*roles_permitidos):

    def decorador(funcion):

        @wraps(funcion)
        def funcion_protegida(*args, **kwargs):

            # Verificar sesión
            if "usuario_id" not in session:

                flash(
                    "Debe iniciar sesión para acceder.",
                    "danger"
                )

                return redirect(
                    url_for("login")
                )

            # Verificar rol
            rol = session.get("rol")

            if rol not in roles_permitidos:

                flash(
                    "No tiene permisos para acceder "
                    "a esta sección.",
                    "danger"
                )

                return redirect(
                    url_for("dashboard")
                )

            return funcion(*args, **kwargs)

        return funcion_protegida

    return decorador