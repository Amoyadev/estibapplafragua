"""Configuración de la app de auditoría."""
from django.apps import AppConfig


class AuditoriaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.auditoria"
    verbose_name = "Auditoría y trazabilidad"

    def ready(self):
        # Conecta los signals (post_save/post_delete y eventos de sesión)
        # solo cuando la app está lista, evitando imports circulares.
        from . import signals  # noqa: F401
