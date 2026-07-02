"""
Migration 0008 — Feature-01/2026 Bloque C: FK ETA.tracto → flota.Tracto.

Cambios en operaciones_eta:
  - AddField  tracto  (FK → flota.Tracto, nullable, SET_NULL)
  - AlterField camion (renombra related_name → etas_legacy, conserva FK)
"""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("flota", "0001_initial"),
        ("operaciones", "0007_conductor_enriquecido"),
    ]

    operations = [
        # 0. Registrar db_table explícita en Camion (ya era el default; no toca la BD)
        migrations.AlterModelTable(
            name="camion",
            table="operaciones_camion",
        ),
        # 1. Agregar columna tracto_id a operaciones_eta
        migrations.AddField(
            model_name="eta",
            name="tracto",
            field=models.ForeignKey(
                "flota.Tracto",
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="etas",
                verbose_name="Tracto",
            ),
        ),
        # 2. Actualizar related_name de camion (solo estado Django, sin cambio de BD)
        migrations.AlterField(
            model_name="eta",
            name="camion",
            field=models.ForeignKey(
                "operaciones.Camion",
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="etas_legacy",
            ),
        ),
    ]
