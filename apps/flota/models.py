"""
Modelos de Flota — gestión de equipos de transporte.

Tracto   : Cabeza tractora (reemplaza el modelo Camion de operaciones).
           Usa db_table = 'operaciones_camion' para reutilizar la tabla existente
           sin perder datos. Los campos nuevos se agregan con nullable via migración.

SemiRemolque : Semirremolque acoplable al tracto (tabla nueva).
"""
from django.db import models


class TimeStampedModel(models.Model):
    creado      = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Tracto(TimeStampedModel):
    """Cabeza tractora (tracto) identificada por patente."""

    class Estado(models.TextChoices):
        DISPONIBLE     = "DISPONIBLE",     "Disponible"
        EN_SERVICIO    = "EN_SERVICIO",    "En servicio"
        MANTENIMIENTO  = "MANTENIMIENTO",  "En mantención"
        FUERA_SERVICIO = "FUERA_SERVICIO", "Fuera de servicio"

    # ── Identificación ────────────────────────────────────────────────
    patente = models.CharField(max_length=10, unique=True)
    marca   = models.CharField(max_length=60, blank=True)
    modelo  = models.CharField(max_length=60, blank=True)
    anio    = models.PositiveSmallIntegerField("Año", null=True, blank=True)
    vin     = models.CharField("VIN", max_length=17, blank=True)
    motor   = models.CharField("N° motor", max_length=40, blank=True)

    # ── Medidores ─────────────────────────────────────────────────────
    kilometraje = models.PositiveIntegerField(
        null=True, blank=True, help_text="Kilometraje actual."
    )
    horometro = models.DecimalField(
        "Horómetro", max_digits=8, decimal_places=1, null=True, blank=True,
        help_text="Horas de motor."
    )
    odometro = models.PositiveIntegerField("Odómetro", null=True, blank=True)

    # ── Vencimientos ──────────────────────────────────────────────────
    vencimiento_seguro   = models.DateField("Vto. seguro", null=True, blank=True)
    vencimiento_permiso  = models.DateField("Vto. permiso circulación", null=True, blank=True)
    vencimiento_revision = models.DateField("Vto. revisión técnica", null=True, blank=True)

    # ── Estado ────────────────────────────────────────────────────────
    estado = models.CharField(
        max_length=15, choices=Estado.choices, default=Estado.DISPONIBLE
    )

    class Meta:
        # Reutiliza la tabla que antes pertenecía al modelo Camion de operaciones.
        db_table         = "operaciones_camion"
        verbose_name     = "Tracto"
        verbose_name_plural = "Tractos"
        ordering         = ["patente"]

    def __str__(self):
        return self.patente


class SemiRemolque(TimeStampedModel):
    """Semirremolque (plataforma/carrocería) acoplable a un tracto."""

    class Tipo(models.TextChoices):
        MULTY = "MULTY", "Multy"
        PLANA = "PLANA", "Plana"
        DE_20 = "DE_20", "De 20'"
        DE_40 = "DE_40", "De 40'"
        OTRO  = "OTRO",  "Otro"

    class Estado(models.TextChoices):
        DISPONIBLE     = "DISPONIBLE",     "Disponible"
        EN_SERVICIO    = "EN_SERVICIO",    "En servicio"
        MANTENIMIENTO  = "MANTENIMIENTO",  "En mantención"
        FUERA_SERVICIO = "FUERA_SERVICIO", "Fuera de servicio"

    patente = models.CharField(max_length=10, unique=True)
    tipo    = models.CharField(max_length=10, choices=Tipo.choices, default=Tipo.OTRO)
    estado  = models.CharField(max_length=15, choices=Estado.choices,
                               default=Estado.DISPONIBLE)

    class Meta:
        verbose_name        = "Semirremolque"
        verbose_name_plural = "Semirremolques"
        ordering            = ["patente"]

    def __str__(self):
        return f"{self.patente} ({self.get_tipo_display()})"
