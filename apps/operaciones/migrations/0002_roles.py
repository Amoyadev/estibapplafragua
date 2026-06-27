"""
Crea los grupos/roles base de Estibapp y les asigna permisos.
Roles: Administrador, Coordinador, Encargado de Patio.

Esta migración es de DATOS: se puede re-ejecutar de forma segura
(usa get_or_create). Si quieres cambiar permisos por rol, edita
`PERMISOS_POR_ROL` y crea una nueva migración de datos.
"""
from django.db import migrations

# Modelos (app_label, model) sobre los que damos permisos CRUD por rol.
CATALOGOS = [
    ("operaciones", "cliente"),
    ("operaciones", "conductor"),
    ("operaciones", "camion"),
    ("operaciones", "agenteportuario"),
    ("operaciones", "contenedor"),
]
ETA_MODELS = [
    ("operaciones", "eta"),
    ("operaciones", "movimiento"),
]

ACCIONES = ["add", "change", "delete", "view"]


def _perms(apps, modelos, acciones):
    Permission = apps.get_model("auth", "Permission")
    perms = []
    for app_label, model in modelos:
        for accion in acciones:
            codename = f"{accion}_{model}"
            try:
                perms.append(
                    Permission.objects.get(
                        codename=codename,
                        content_type__app_label=app_label,
                    )
                )
            except Permission.DoesNotExist:
                pass
    return perms


def crear_roles(apps, schema_editor):
    Group = apps.get_model("auth", "Group")

    administrador, _ = Group.objects.get_or_create(name="Administrador")
    coordinador, _ = Group.objects.get_or_create(name="Coordinador")
    patio, _ = Group.objects.get_or_create(name="Encargado de Patio")

    # Administrador: todo sobre catálogos + ETAs
    administrador.permissions.set(
        _perms(apps, CATALOGOS + ETA_MODELS, ACCIONES)
    )

    # Coordinador: gestiona catálogos y crea/edita ETAs
    coordinador.permissions.set(
        _perms(apps, CATALOGOS, ACCIONES)
        + _perms(apps, ETA_MODELS, ["add", "change", "view"])
    )

    # Encargado de Patio: ve catálogos, opera ETAs/movimientos
    patio.permissions.set(
        _perms(apps, CATALOGOS, ["view"])
        + _perms(apps, ETA_MODELS, ["change", "view", "add"])
    )


def eliminar_roles(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(
        name__in=["Administrador", "Coordinador", "Encargado de Patio"]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("operaciones", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(crear_roles, eliminar_roles),
    ]
