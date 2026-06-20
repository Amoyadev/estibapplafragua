"""Refactor del ciclo: se elimina CERRADO y se trazan dos despachos.

Cambios:
- ETA.estado: nuevas opciones (DESPACHADO_CLIENTE, DESPACHADO_PUERTO) y
  max_length 12 -> 20.
- Movimiento.tipo: renombra DESPACHO -> DESPACHO_CLIENTE, DEVOLUCION ->
  DESPACHO_PUERTO, agrega RETORNO; max_length 12 -> 20.
- Conversión de datos existentes:
    ETA:        DESPACHADO -> DESPACHADO_CLIENTE,  CERRADO -> DESPACHADO_PUERTO
    Movimiento: DESPACHO   -> DESPACHO_CLIENTE,    DEVOLUCION -> DESPACHO_PUERTO
"""
from django.db import migrations, models


# Mapeos de conversión (valor antiguo -> valor nuevo).
ETA_ESTADOS = {
    "DESPACHADO": "DESPACHADO_CLIENTE",
    "CERRADO": "DESPACHADO_PUERTO",
}
MOV_TIPOS = {
    "DESPACHO": "DESPACHO_CLIENTE",
    "DEVOLUCION": "DESPACHO_PUERTO",
}


def _aplicar(modelo, campo, mapeo):
    filtro = {f"{campo}__in": list(mapeo)}
    for obj in modelo.objects.filter(**filtro):
        setattr(obj, campo, mapeo[getattr(obj, campo)])
        obj.save(update_fields=[campo])


def migrar_adelante(apps, schema_editor):
    ETA = apps.get_model("operaciones", "ETA")
    Movimiento = apps.get_model("operaciones", "Movimiento")
    _aplicar(ETA, "estado", ETA_ESTADOS)
    _aplicar(Movimiento, "tipo", MOV_TIPOS)


def migrar_atras(apps, schema_editor):
    ETA = apps.get_model("operaciones", "ETA")
    Movimiento = apps.get_model("operaciones", "Movimiento")
    _aplicar(ETA, "estado", {v: k for k, v in ETA_ESTADOS.items()})
    # RETORNO no existía antes; se aproxima a DEVOLUCION para reversibilidad.
    inverso = {v: k for k, v in MOV_TIPOS.items()}
    inverso["RETORNO"] = "DEVOLUCION"
    _aplicar(Movimiento, "tipo", inverso)


class Migration(migrations.Migration):

    dependencies = [
        ("operaciones", "0003_empresa_remove_movimiento_responsable_eta_ubicacion_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="eta",
            name="estado",
            field=models.CharField(
                choices=[
                    ("SOLICITADO", "Solicitado por cliente"),
                    ("ASIGNADO", "Asignado"),
                    ("EN_PATIO", "En patio"),
                    ("ALMACENADO", "Almacenado"),
                    ("DESPACHADO_CLIENTE", "Despachado a cliente"),
                    ("DESPACHADO_PUERTO", "Despachado a puerto"),
                ],
                default="SOLICITADO",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="movimiento",
            name="tipo",
            field=models.CharField(
                choices=[
                    ("RETIRO", "Retiro"),
                    ("ALMACENAJE", "Almacenaje"),
                    ("DESPACHO_CLIENTE", "Despacho a cliente"),
                    ("RETORNO", "Devuelto a depósito"),
                    ("DESPACHO_PUERTO", "Despacho a puerto"),
                ],
                max_length=20,
            ),
        ),
        migrations.RunPython(migrar_adelante, migrar_atras),
    ]
