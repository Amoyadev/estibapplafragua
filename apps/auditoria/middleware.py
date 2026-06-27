"""
Middleware de auditoría: expone el "actor" (usuario + IP + ruta) de la
petición actual a los signals, que no tienen acceso directo al request.

Usa almacenamiento thread-local. Debe ir DESPUÉS de AuthenticationMiddleware
en la lista MIDDLEWARE para que `request.user` ya esté disponible.
"""
import threading

_locals = threading.local()


def _client_ip(request):
    """IP del cliente respetando el proxy (Nginx) si envía X-Forwarded-For."""
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def get_actor():
    """Devuelve el dict del actor actual o None (p. ej. en tareas de sistema)."""
    return getattr(_locals, "actor", None)


class AuditoriaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        _locals.actor = {
            "user": user if (user and user.is_authenticated) else None,
            "ip": _client_ip(request),
            "ruta": request.path,
        }
        try:
            return self.get_response(request)
        finally:
            # Evita filtrar el actor entre peticiones del mismo worker/hilo.
            _locals.actor = None
