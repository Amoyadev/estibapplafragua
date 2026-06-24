"""Modelos de la app de comunicaciones — bandeja IMAP."""
from django.db import models


class CorreoETA(models.Model):
    """Correo extraído del buzón IMAP y candidato a crear una ETA."""

    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        PROCESADO = "PROCESADO", "Procesado"
        IGNORADO  = "IGNORADO",  "Ignorado"

    msg_id           = models.CharField(max_length=300, unique=True, db_index=True)
    asunto           = models.CharField(max_length=500)
    remitente        = models.CharField(max_length=300)
    fecha_correo     = models.DateTimeField()
    # Campos extraídos del cuerpo (pueden quedar vacíos si el parser no los encuentra)
    numero_eta       = models.CharField(max_length=50, blank=True)
    cliente_nombre   = models.CharField(max_length=200, blank=True)
    puerto           = models.CharField(max_length=100, blank=True)
    contenedor_codigo = models.CharField(max_length=30, blank=True)
    cuerpo           = models.TextField(blank=True)
    estado           = models.CharField(
        max_length=20, choices=Estado.choices, default=Estado.PENDIENTE
    )
    creado           = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha_correo"]
        verbose_name = "Correo ETA"
        verbose_name_plural = "Correos ETA"

    def __str__(self):
        return f"{self.asunto} — {self.remitente} ({self.fecha_correo:%d/%m/%Y})"
