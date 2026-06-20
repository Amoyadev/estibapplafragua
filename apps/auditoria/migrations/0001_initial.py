from django.conf import settings
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="RegistroAuditoria",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("fecha", models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="Fecha")),
                ("usuario_nombre", models.CharField(blank=True, max_length=150)),
                ("accion", models.CharField(choices=[("CREAR", "Creación"), ("ACTUALIZAR", "Actualización"), ("ELIMINAR", "Eliminación"), ("LOGIN", "Inicio de sesión"), ("LOGOUT", "Cierre de sesión"), ("LOGIN_FALLIDO", "Intento de acceso fallido")], db_index=True, max_length=20)),
                ("modelo", models.CharField(blank=True, db_index=True, max_length=100)),
                ("objeto_id", models.CharField(blank=True, max_length=50)),
                ("objeto_repr", models.CharField(blank=True, max_length=255)),
                ("cambios", models.JSONField(blank=True, default=dict)),
                ("ip", models.GenericIPAddressField(blank=True, null=True)),
                ("ruta", models.CharField(blank=True, max_length=255)),
                ("usuario", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="auditorias", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Registro de auditoría",
                "verbose_name_plural": "Registros de auditoría",
                "ordering": ["-fecha"],
            },
        ),
        migrations.AddIndex(
            model_name="registroauditoria",
            index=models.Index(fields=["modelo", "objeto_id"], name="auditoria_r_modelo_3b1c8e_idx"),
        ),
        migrations.AddIndex(
            model_name="registroauditoria",
            index=models.Index(fields=["accion", "fecha"], name="auditoria_r_accion_6d2f4a_idx"),
        ),
    ]
