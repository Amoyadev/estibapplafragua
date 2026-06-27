from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="CorreoETA",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("msg_id", models.CharField(db_index=True, max_length=300, unique=True)),
                ("asunto", models.CharField(max_length=500)),
                ("remitente", models.CharField(max_length=300)),
                ("fecha_correo", models.DateTimeField()),
                ("numero_eta", models.CharField(blank=True, max_length=50)),
                ("cliente_nombre", models.CharField(blank=True, max_length=200)),
                ("puerto", models.CharField(blank=True, max_length=100)),
                ("contenedor_codigo", models.CharField(blank=True, max_length=30)),
                ("cuerpo", models.TextField(blank=True)),
                (
                    "estado",
                    models.CharField(
                        choices=[
                            ("PENDIENTE", "Pendiente"),
                            ("PROCESADO", "Procesado"),
                            ("IGNORADO", "Ignorado"),
                        ],
                        default="PENDIENTE",
                        max_length=20,
                    ),
                ),
                ("creado", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Correo ETA",
                "verbose_name_plural": "Correos ETA",
                "ordering": ["-fecha_correo"],
            },
        ),
    ]
