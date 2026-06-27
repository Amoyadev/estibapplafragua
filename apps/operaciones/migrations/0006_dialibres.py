from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("operaciones", "0005_conductor_estado_eta_deposito_devolucion_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="DiaLibre",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("creado", models.DateTimeField(auto_now_add=True)),
                ("actualizado", models.DateTimeField(auto_now=True)),
                ("fecha", models.DateField()),
                ("motivo", models.CharField(blank=True, max_length=120)),
                (
                    "conductor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="dias_libres",
                        to="operaciones.conductor",
                    ),
                ),
            ],
            options={
                "verbose_name": "Día libre",
                "verbose_name_plural": "Días libres",
                "ordering": ["fecha"],
                "unique_together": {("conductor", "fecha")},
            },
        ),
    ]
