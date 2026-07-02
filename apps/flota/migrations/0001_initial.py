"""
Migration flota/0001 — Feature-01/2026 Bloque C.

Estrategia para Tracto:
  La tabla `operaciones_camion` ya existe (creada por operaciones/0001_initial).
  Usamos SeparateDatabaseAndState para:
    - Estado: registrar el modelo Tracto con todos sus campos.
    - BD:     solo AGREGAR las columnas nuevas (las existentes ya están).

  Columnas existentes en operaciones_camion:
    id, patente, marca, creado, actualizado

  Columnas NUEVAS (se agregan aquí):
    modelo, anio, vin, motor, kilometraje, horometro, odometro,
    vencimiento_seguro, vencimiento_permiso, vencimiento_revision, estado

Para SemiRemolque: tabla nueva, migración normal.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        # La tabla operaciones_camion debe existir antes de agregar columnas.
        ("operaciones", "0007_conductor_enriquecido"),
    ]

    operations = [
        # ── Tracto: importar tabla existente + agregar columnas nuevas ──
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name="Tracto",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                        ("creado",      models.DateTimeField(auto_now_add=True)),
                        ("actualizado", models.DateTimeField(auto_now=True)),
                        # Columnas existentes
                        ("patente", models.CharField(max_length=10, unique=True)),
                        ("marca",   models.CharField(blank=True, max_length=60)),
                        # Columnas nuevas
                        ("modelo",  models.CharField(blank=True, max_length=60)),
                        ("anio",    models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="Año")),
                        ("vin",     models.CharField(blank=True, max_length=17, verbose_name="VIN")),
                        ("motor",   models.CharField(blank=True, max_length=40, verbose_name="N° motor")),
                        ("kilometraje", models.PositiveIntegerField(blank=True, null=True, help_text="Kilometraje actual.")),
                        ("horometro",   models.DecimalField(blank=True, decimal_places=1, max_digits=8, null=True, verbose_name="Horómetro")),
                        ("odometro",    models.PositiveIntegerField(blank=True, null=True, verbose_name="Odómetro")),
                        ("vencimiento_seguro",   models.DateField(blank=True, null=True, verbose_name="Vto. seguro")),
                        ("vencimiento_permiso",  models.DateField(blank=True, null=True, verbose_name="Vto. permiso circulación")),
                        ("vencimiento_revision", models.DateField(blank=True, null=True, verbose_name="Vto. revisión técnica")),
                        ("estado", models.CharField(
                            choices=[
                                ("DISPONIBLE",     "Disponible"),
                                ("EN_SERVICIO",    "En servicio"),
                                ("MANTENIMIENTO",  "En mantención"),
                                ("FUERA_SERVICIO", "Fuera de servicio"),
                            ],
                            default="DISPONIBLE", max_length=15,
                        )),
                    ],
                    options={
                        "verbose_name": "Tracto",
                        "verbose_name_plural": "Tractos",
                        "ordering": ["patente"],
                        "db_table": "operaciones_camion",
                    },
                ),
            ],
            database_operations=[
                # Solo agregar las NUEVAS columnas; las existentes ya están en la tabla.
                migrations.RunSQL(
                    sql="ALTER TABLE operaciones_camion ADD COLUMN IF NOT EXISTS modelo VARCHAR(60) NOT NULL DEFAULT ''",
                    reverse_sql="ALTER TABLE operaciones_camion DROP COLUMN IF EXISTS modelo",
                ),
                migrations.RunSQL(
                    sql="ALTER TABLE operaciones_camion ADD COLUMN IF NOT EXISTS anio SMALLINT",
                    reverse_sql="ALTER TABLE operaciones_camion DROP COLUMN IF EXISTS anio",
                ),
                migrations.RunSQL(
                    sql="ALTER TABLE operaciones_camion ADD COLUMN IF NOT EXISTS vin VARCHAR(17) NOT NULL DEFAULT ''",
                    reverse_sql="ALTER TABLE operaciones_camion DROP COLUMN IF EXISTS vin",
                ),
                migrations.RunSQL(
                    sql="ALTER TABLE operaciones_camion ADD COLUMN IF NOT EXISTS motor VARCHAR(40) NOT NULL DEFAULT ''",
                    reverse_sql="ALTER TABLE operaciones_camion DROP COLUMN IF EXISTS motor",
                ),
                migrations.RunSQL(
                    sql="ALTER TABLE operaciones_camion ADD COLUMN IF NOT EXISTS kilometraje INTEGER",
                    reverse_sql="ALTER TABLE operaciones_camion DROP COLUMN IF EXISTS kilometraje",
                ),
                migrations.RunSQL(
                    sql="ALTER TABLE operaciones_camion ADD COLUMN IF NOT EXISTS horometro NUMERIC(8,1)",
                    reverse_sql="ALTER TABLE operaciones_camion DROP COLUMN IF EXISTS horometro",
                ),
                migrations.RunSQL(
                    sql="ALTER TABLE operaciones_camion ADD COLUMN IF NOT EXISTS odometro INTEGER",
                    reverse_sql="ALTER TABLE operaciones_camion DROP COLUMN IF EXISTS odometro",
                ),
                migrations.RunSQL(
                    sql="ALTER TABLE operaciones_camion ADD COLUMN IF NOT EXISTS vencimiento_seguro DATE",
                    reverse_sql="ALTER TABLE operaciones_camion DROP COLUMN IF EXISTS vencimiento_seguro",
                ),
                migrations.RunSQL(
                    sql="ALTER TABLE operaciones_camion ADD COLUMN IF NOT EXISTS vencimiento_permiso DATE",
                    reverse_sql="ALTER TABLE operaciones_camion DROP COLUMN IF EXISTS vencimiento_permiso",
                ),
                migrations.RunSQL(
                    sql="ALTER TABLE operaciones_camion ADD COLUMN IF NOT EXISTS vencimiento_revision DATE",
                    reverse_sql="ALTER TABLE operaciones_camion DROP COLUMN IF EXISTS vencimiento_revision",
                ),
                migrations.RunSQL(
                    sql="ALTER TABLE operaciones_camion ADD COLUMN IF NOT EXISTS estado VARCHAR(15) NOT NULL DEFAULT 'DISPONIBLE'",
                    reverse_sql="ALTER TABLE operaciones_camion DROP COLUMN IF EXISTS estado",
                ),
            ],
        ),

        # ── SemiRemolque: tabla nueva (migración normal) ──
        migrations.CreateModel(
            name="SemiRemolque",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("creado",      models.DateTimeField(auto_now_add=True)),
                ("actualizado", models.DateTimeField(auto_now=True)),
                ("patente", models.CharField(max_length=10, unique=True)),
                ("tipo", models.CharField(
                    choices=[
                        ("MULTY", "Multy"),
                        ("PLANA", "Plana"),
                        ("DE_20", "De 20'"),
                        ("DE_40", "De 40'"),
                        ("OTRO",  "Otro"),
                    ],
                    default="OTRO", max_length=10,
                )),
                ("estado", models.CharField(
                    choices=[
                        ("DISPONIBLE",     "Disponible"),
                        ("EN_SERVICIO",    "En servicio"),
                        ("MANTENIMIENTO",  "En mantención"),
                        ("FUERA_SERVICIO", "Fuera de servicio"),
                    ],
                    default="DISPONIBLE", max_length=15,
                )),
            ],
            options={
                "verbose_name": "Semirremolque",
                "verbose_name_plural": "Semirremolques",
                "ordering": ["patente"],
            },
        ),
    ]
