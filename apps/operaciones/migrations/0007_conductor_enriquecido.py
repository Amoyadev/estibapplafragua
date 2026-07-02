"""
Migration 0007 — Feature-01/2026 Bloque B: Conductor enriquecido + RegistroConductor.

Cambios:
  - Conductor.Estado: ACTIVO/INOPERATIVO → DISPONIBLE/EN_RUTA/DESCANSO/LICENCIA
  - Nuevos campos: licencia, fecha_vencimiento_licencia
  - Nuevo modelo: RegistroConductor (log genérico)
  - RunPython: migra datos existentes ACTIVO→DISPONIBLE, INOPERATIVO→DESCANSO
"""
from django.db import migrations, models
import django.db.models.deletion


def migrar_estado_conductores(apps, schema_editor):
    """ACTIVO → DISPONIBLE, INOPERATIVO → DESCANSO."""
    Conductor = apps.get_model("operaciones", "Conductor")
    Conductor.objects.filter(estado="ACTIVO").update(estado="DISPONIBLE")
    Conductor.objects.filter(estado="INOPERATIVO").update(estado="DESCANSO")


def revertir_estado_conductores(apps, schema_editor):
    """Revertir: DISPONIBLE → ACTIVO, resto → INOPERATIVO."""
    Conductor = apps.get_model("operaciones", "Conductor")
    Conductor.objects.filter(estado="DISPONIBLE").update(estado="ACTIVO")
    Conductor.objects.exclude(estado="ACTIVO").update(estado="INOPERATIVO")


class Migration(migrations.Migration):

    dependencies = [
        ("operaciones", "0006_dialibres"),
    ]

    operations = [
        # 1. Agregar campos nuevos (nullable primero para no romper filas existentes)
        migrations.AddField(
            model_name="conductor",
            name="licencia",
            field=models.CharField(
                blank=True, max_length=20, verbose_name="Licencia",
                help_text="N° de licencia de conducir."
            ),
        ),
        migrations.AddField(
            model_name="conductor",
            name="fecha_vencimiento_licencia",
            field=models.DateField(
                blank=True, null=True, verbose_name="Vto. licencia",
                help_text="Fecha de vencimiento de la licencia."
            ),
        ),
        # 2. Migrar datos de estado ANTES de cambiar las choices
        migrations.RunPython(
            migrar_estado_conductores,
            reverse_code=revertir_estado_conductores,
        ),
        # 3. Cambiar las choices (solo metadatos, no toca la columna BD)
        migrations.AlterField(
            model_name="conductor",
            name="estado",
            field=models.CharField(
                choices=[
                    ("DISPONIBLE", "Disponible"),
                    ("EN_RUTA",    "En ruta"),
                    ("DESCANSO",   "Descanso"),
                    ("LICENCIA",   "Licencia"),
                ],
                default="DISPONIBLE",
                help_text="Estado operativo del conductor.",
                max_length=12,
            ),
        ),
        # 4. Crear RegistroConductor
        migrations.CreateModel(
            name="RegistroConductor",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("creado",      models.DateTimeField(auto_now_add=True)),
                ("actualizado", models.DateTimeField(auto_now=True)),
                ("tipo", models.CharField(
                    choices=[
                        ("COMBUSTIBLE", "Carga de combustible"),
                        ("INFRACCION",  "Infracción"),
                        ("KM",          "Registro de km"),
                        ("SERVICIO",    "Servicio / mantención"),
                        ("OTRO",        "Otro"),
                    ],
                    max_length=15,
                )),
                ("fecha",       models.DateField()),
                ("descripcion", models.TextField(blank=True)),
                ("valor", models.DecimalField(
                    blank=True, decimal_places=2, max_digits=10, null=True,
                    help_text="Valor numérico asociado (litros, km, monto de multa, etc.)."
                )),
                ("conductor", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="registros",
                    to="operaciones.conductor",
                )),
            ],
            options={
                "verbose_name": "Registro de conductor",
                "verbose_name_plural": "Registros de conductores",
                "ordering": ["-fecha", "-creado"],
            },
        ),
    ]
