"""Modelo de trazabilidad: un registro por cada acción relevante de usuario."""
from django.conf import settings
from django.db import models


class RegistroAuditoria(models.Model):
    """
    Bitácora persistente de acciones. Se llena automáticamente vía signals.

    Guarda una "foto" del usuario (nombre) además del FK, para que el registro
    siga siendo legible aunque el usuario se elimine más adelante.
    """

    class Accion(models.TextChoices):
        CREAR = "CREAR", "Creación"
        ACTUALIZAR = "ACTUALIZAR", "Actualización"
        ELIMINAR = "ELIMINAR", "Eliminación"
        LOGIN = "LOGIN", "Inicio de sesión"
        LOGOUT = "LOGOUT", "Cierre de sesión"
        LOGIN_FALLIDO = "LOGIN_FALLIDO", "Intento de acceso fallido"

    fecha = models.DateTimeField("Fecha", auto_now_add=True, db_index=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="auditorias",
    )
    usuario_nombre = models.CharField(max_length=150, blank=True)
    accion = models.CharField(max_length=20, choices=Accion.choices, db_index=True)
    modelo = models.CharField(max_length=100, blank=True, db_index=True)
    objeto_id = models.CharField(max_length=50, blank=True)
    objeto_repr = models.CharField(max_length=255, blank=True)
    cambios = models.JSONField(default=dict, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    ruta = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "Registro de auditoría"
        verbose_name_plural = "Registros de auditoría"
        ordering = ["-fecha"]
        indexes = [
            models.Index(fields=["modelo", "objeto_id"]),
            models.Index(fields=["accion", "fecha"]),
        ]

    def __str__(self):
        actor = self.usuario_nombre or "sistema"
        return f"{self.fecha:%Y-%m-%d %H:%M} · {actor} · {self.get_accion_display()}"
