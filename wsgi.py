from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.wrappers import Response

from app import app

application = DispatcherMiddleware(
    Response("Página no encontrada", status=404),
    {
        "/distri_pan_v1": app
    }
)