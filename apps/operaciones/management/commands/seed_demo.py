"""
Comando de carga de datos de demostración (seed) para Estibapp.

Genera datos históricos desde 2025-01-01 hasta hoy:
  - 3 usuarios QA (uno por rol).
  - Datos maestros aleatorios (clientes, conductores, camiones, agentes, contenedores).
  - ETAs distribuidas en el período, 70% como cliente Tattersall.
  - Movimientos escalonados en el tiempo para llenar los gráficos.

Es IDEMPOTENTE: se puede ejecutar varias veces sin duplicar usuarios ni
catálogos base. Usa --reset para borrar las ETAs/movimientos y volver a
generarlas.

Uso:
    python manage.py seed_demo
    python manage.py seed_demo --reset
    python manage.py seed_demo --password "OtraClave123*"
"""
import os
import random
import unicodedata
from datetime import date, datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.operaciones.models import (
    ESTADOS_EN_DEPOSITO,
    FLUJO_PASOS,
    AgentePortuario,
    Camion,
    Cliente,
    Conductor,
    Contenedor,
    Empresa,
    ETA,
    Movimiento,
)
from apps.operaciones.permissions import (
    ROL_ADMIN,
    ROL_COORDINADOR,
    ROL_PATIO,
)

User = get_user_model()

PASSWORD_QA = "Estibapp2025*"

# Datos históricos: desde esta fecha hasta hoy
FECHA_INICIO = date(2025, 1, 1)

# ================================================================
# USUARIOS CORPORATIVOS REALES
# ================================================================
DOMINIO_CORPORATIVO = os.environ.get("DOMINIO_CORPORATIVO", "estibapp.cl")

USUARIOS_CORPORATIVOS = [
    ("Javier Ovalle Calderón", ROL_ADMIN),
]


def _sin_acentos(texto):
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def nomenclatura_usuario(nombre_completo, dominio=None):
    dominio = dominio or DOMINIO_CORPORATIVO
    partes = _sin_acentos(nombre_completo.strip()).split()
    nombre = partes[0] if partes else "usuario"
    apellido = partes[1] if len(partes) > 1 else ""
    username = (nombre[:1] + apellido).lower()
    email = f"{username}@{dominio}"
    return username, email


# ---- Catálogos de ejemplo ----
NOMBRES = [
    "Comercial Andes", "Frutícola del Maipo", "Importadora Pacífico",
    "Exportadora Aconcagua", "Logística Casablanca", "Naviera del Sur",
    "Agroexport Curicó", "Distribuidora Valparaíso",
]
CONDUCTORES = [
    "Juan Pérez", "Marco Rojas", "Luis Fuentes", "Pedro Salinas",
    "Andrés Vega", "Cristián Soto", "Patricio Núñez", "Diego Lagos",
]
AGENTES = [
    ("Terminal Pacífico Sur", "TPS"),
    ("Puerto Central", "PCE"),
    ("San Antonio Terminal Internacional", "STI"),
    ("Terminal Cerros de Valparaíso", "TCVAL"),
]
EMPRESAS = [
    "Transportes Andinos", "Logística del Pacífico", "Fletes Centrales",
    "Transbordo Sur", "Carga Express",
]
MARCAS = ["Volvo", "Scania", "Mercedes-Benz", "Freightliner", "MAN"]
DEPOSITOS = ["Casablanca", "Placilla", "Quilpué", "San Antonio"]
UBICACIONES = ["Calle A", "Calle B", "Calle C", "Patio Norte", "Patio Sur"]


def rut_aleatorio():
    cuerpo = random.randint(5_000_000, 24_000_000)
    dv = random.choice("0123456789K")
    return f"{cuerpo:,}".replace(",", ".") + f"-{dv}"


def patente_aleatoria():
    letras = "".join(random.choices("BCDFGHJKLPRSTVWXYZ", k=4))
    return f"{letras}{random.randint(10, 99)}"


def codigo_contenedor():
    letras = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=4))
    return f"{letras}{random.randint(1000000, 9999999)}"


def fecha_en_rango(desde=None, hasta=None):
    """Fecha aleatoria entre desde (default FECHA_INICIO) y hasta (default hoy)."""
    desde = desde or FECHA_INICIO
    hasta = hasta or timezone.now().date()
    delta = (hasta - desde).days
    if delta <= 0:
        return desde
    return desde + timedelta(days=random.randint(0, delta))


class Command(BaseCommand):
    help = "Crea usuarios QA por rol y datos de demostración históricos (2025-hoy)."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true",
                            help="Borra ETAs y movimientos antes de generar nuevos.")
        parser.add_argument("--password", default=PASSWORD_QA,
                            help="Contraseña para los usuarios QA.")
        parser.add_argument("--etas", type=int, default=60,
                            help="ETAs generales (no Tattersall). Default 60.")
        parser.add_argument("--etas-tat", type=int, default=140,
                            help="ETAs Tattersall (70%% del total). Default 140.")
        parser.add_argument("--admin-password",
                            default=os.environ.get("ADMIN_PASSWORD", PASSWORD_QA))
        parser.add_argument("--dominio", default=DOMINIO_CORPORATIVO)

    def handle(self, *args, **options):
        random.seed(42)
        password = options["password"]

        if options["reset"]:
            Movimiento.objects.all().delete()
            ETA.objects.all().delete()
            self.stdout.write(self.style.WARNING("ETAs y movimientos eliminados."))

        self._crear_usuarios_qa(password)
        self._crear_usuarios_corporativos(options["admin_password"], options["dominio"])
        empresas, agentes, clientes, conductores, camiones, contenedores = (
            self._crear_catalogos()
        )
        self._crear_etas(
            options["etas"], empresas, agentes, clientes,
            conductores, camiones, contenedores,
        )
        self._crear_tattersall(
            options["etas_tat"], agentes, conductores, camiones, contenedores, empresas,
        )

        self.stdout.write(self.style.SUCCESS("\n✅ Datos de demostración cargados."))
        self.stdout.write(
            "Usuarios QA (clave: " + self.style.NOTICE(password) + "):\n"
            "  - QA_Administrador  (rol Administrador)\n"
            "  - QA_Coordinador    (rol Coordinador)\n"
            "  - QA_Patio          (rol Encargado de Patio)\n"
        )

    # ------------------------------------------------------------------
    def _crear_usuarios_qa(self, password):
        definiciones = [
            ("QA_Administrador", ROL_ADMIN, False, False),
            ("QA_Coordinador", ROL_COORDINADOR, False, False),
            ("QA_Patio", ROL_PATIO, False, False),
        ]
        for username, rol, is_staff, is_superuser in definiciones:
            user, creado = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": f"{username.lower()}@estibapp.demo",
                    "first_name": "QA",
                    "last_name": rol,
                    "is_staff": is_staff,
                    "is_superuser": is_superuser,
                },
            )
            user.is_staff = is_staff
            user.is_superuser = is_superuser
            user.set_password(password)
            user.save()
            grupo = Group.objects.filter(name=rol).first()
            if grupo:
                user.groups.set([grupo])
            self.stdout.write(f"  · Usuario {username} ({rol}) {'creado' if creado else 'actualizado'}.")

    # ------------------------------------------------------------------
    def _crear_usuarios_corporativos(self, password, dominio):
        for nombre_completo, rol in USUARIOS_CORPORATIVOS:
            username, email = nomenclatura_usuario(nombre_completo, dominio)
            partes = nombre_completo.split()
            first_name = partes[0] if partes else ""
            last_name = " ".join(partes[1:]) if len(partes) > 1 else ""
            user, creado = User.objects.get_or_create(
                username=username,
                defaults={"email": email, "first_name": first_name,
                          "last_name": last_name, "is_staff": False, "is_superuser": False},
            )
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.set_password(password)
            user.save()
            grupo = Group.objects.filter(name=rol).first()
            if grupo:
                user.groups.set([grupo])
            self.stdout.write(
                f"  · Usuario corporativo {username} <{email}> ({rol}) "
                f"{'creado' if creado else 'actualizado'}."
            )

    # ------------------------------------------------------------------
    def _crear_catalogos(self):
        empresas = [
            Empresa.objects.get_or_create(
                nombre=nombre, defaults={"rut": rut_aleatorio(), "activo": True}
            )[0]
            for nombre in EMPRESAS
        ]
        agentes = [
            AgentePortuario.objects.get_or_create(
                nombre=nombre, defaults={"sigla": sigla, "activo": True}
            )[0]
            for nombre, sigla in AGENTES
        ]
        clientes = [
            Cliente.objects.get_or_create(
                nombre=nombre,
                defaults={
                    "rut": rut_aleatorio(),
                    "email": f"contacto@{nombre.split()[0].lower()}.cl",
                    "telefono": f"+569{random.randint(10000000, 99999999)}",
                    "activo": True,
                },
            )[0]
            for nombre in NOMBRES
        ]
        conductores = [
            Conductor.objects.get_or_create(
                nombre=nombre,
                defaults={
                    "empresa": random.choice(empresas),
                    "rut": rut_aleatorio(),
                    "telefono": f"+569{random.randint(10000000, 99999999)}",
                },
            )[0]
            for nombre in CONDUCTORES
        ]
        camiones = []
        for _ in range(8):
            patente = patente_aleatoria()
            camion, _ = Camion.objects.get_or_create(
                patente=patente, defaults={"marca": random.choice(MARCAS)}
            )
            camiones.append(camion)
        contenedores = []
        tipos = [t for t, _ in Contenedor.Tipo.choices]
        estados = [e for e, _ in Contenedor.Estado.choices]
        for _ in range(30):
            codigo = codigo_contenedor()
            cont, _ = Contenedor.objects.get_or_create(
                codigo=codigo,
                defaults={"tipo": random.choice(tipos), "estado": random.choice(estados)},
            )
            contenedores.append(cont)

        self.stdout.write(
            f"  · Catálogos: {len(empresas)} empresas, {len(agentes)} agentes, "
            f"{len(clientes)} clientes, {len(conductores)} conductores, "
            f"{len(camiones)} camiones, {len(contenedores)} contenedores."
        )
        return empresas, agentes, clientes, conductores, camiones, contenedores

    # ------------------------------------------------------------------
    def _eta_create(self, numero, cliente, agentes, contenedores, conductores,
                    camiones, empresas, fecha_eta, destino_idx, ubicacion,
                    tipo_proceso, observaciones):
        """Crea una ETA + sus movimientos. Devuelve la ETA o None si ya existe."""
        if ETA.objects.filter(numero=numero).exists():
            return None
        en_deposito = {ETA.EstadoCiclo.EN_PATIO, ETA.EstadoCiclo.ALMACENADO}
        estado_destino = FLUJO_PASOS[destino_idx]["estado"]
        tiene_conductor = destino_idx >= 1
        eta = ETA.objects.create(
            numero=numero,
            cliente=cliente,
            agente=random.choice(agentes),
            contenedor=random.choice(contenedores),
            conductor=random.choice(conductores) if tiene_conductor else None,
            camion=random.choice(camiones) if tiene_conductor else None,
            deposito=random.choice(DEPOSITOS),
            ubicacion=ubicacion,
            fecha=fecha_eta,
            fecha_retiro=fecha_eta if tiene_conductor else None,
            hora_retiro=time(random.randint(7, 18), random.choice([0, 15, 30, 45])),
            tipo_proceso=tipo_proceso,
            estado=estado_destino,
            observaciones=observaciones,
        )
        self._movimientos_eta(eta, destino_idx, empresas)
        return eta

    def _movimientos_eta(self, eta, hasta_idx, empresas):
        cursor = timezone.make_aware(
            datetime.combine(eta.fecha, time(random.randint(7, 10), 0))
        )
        for idx in range(1, hasta_idx + 1):
            tipo_mov = FLUJO_PASOS[idx]["mov"]
            if not tipo_mov:
                continue
            cursor += timedelta(hours=random.randint(4, 72))
            empresa_resp = (
                eta.conductor.empresa
                if eta.conductor and eta.conductor.empresa
                else random.choice(empresas)
            )
            Movimiento.objects.create(
                eta=eta,
                tipo=tipo_mov,
                fecha=cursor,
                empresa_responsable=empresa_resp,
                observacion="Movimiento generado por seed_demo.",
            )

    # ------------------------------------------------------------------
    def _crear_etas(self, cantidad, empresas, agentes, clientes,
                    conductores, camiones, contenedores):
        """ETAs de clientes variados distribuidas en el período histórico."""
        en_deposito = {ETA.EstadoCiclo.EN_PATIO, ETA.EstadoCiclo.ALMACENADO}
        base = ETA.objects.count()
        creadas = 0
        for i in range(cantidad):
            numero = f"ETA-2025-{base + i + 1:04d}"
            destino_idx = random.randint(0, len(FLUJO_PASOS) - 1)
            estado_destino = FLUJO_PASOS[destino_idx]["estado"]
            ubicacion = (
                f"{random.choice(UBICACIONES)} · Nivel {random.randint(1, 4)}"
                if estado_destino in en_deposito else ""
            )
            fecha_eta = fecha_en_rango()
            eta = self._eta_create(
                numero=numero,
                cliente=random.choice(clientes),
                agentes=agentes,
                contenedores=contenedores,
                conductores=conductores,
                camiones=camiones,
                empresas=empresas,
                fecha_eta=fecha_eta,
                destino_idx=destino_idx,
                ubicacion=ubicacion,
                tipo_proceso=random.choice(
                    [ETA.TipoProceso.DIRECTO, ETA.TipoProceso.INDIRECTO]
                ),
                observaciones="Registro de demostración (datos genéricos).",
            )
            if eta:
                creadas += 1
        self.stdout.write(f"  · ETAs generales generadas: {creadas}.")

    # ------------------------------------------------------------------
    def _crear_tattersall(self, cantidad, agentes, conductores, camiones,
                          contenedores, empresas):
        """
        ETAs de Tattersall (~70% del total).
        Distribuidas en el período histórico completo con distintos estados.
        """
        cliente, _ = Cliente.objects.get_or_create(
            nombre="Tattersall",
            defaults={
                "rut": "90.412.000-6",
                "email": "operaciones@tattersall.cl",
                "telefono": "+56 2 2630 0000",
                "activo": True,
            },
        )
        en_deposito_set = {ETA.EstadoCiclo.EN_PATIO, ETA.EstadoCiclo.ALMACENADO}
        base = ETA.objects.count()
        creadas = 0

        # Distribuir: 40% ciclo completo, 35% en algún estado intermedio, 25% aún activos
        pesos = []
        for idx in range(len(FLUJO_PASOS)):
            # Mayor peso a estados intermedios y finales para simular operación madura
            if idx == 0:
                peso = 5
            elif idx == len(FLUJO_PASOS) - 1:
                peso = 20
            else:
                paso = FLUJO_PASOS[idx]
                peso = 18 if paso["estado"] in (
                    ETA.EstadoCiclo.ALMACENADO, ETA.EstadoCiclo.DESPACHADO_CLIENTE
                ) else 12
            pesos.append(peso)

        indices = random.choices(range(len(FLUJO_PASOS)), weights=pesos, k=cantidad)

        for i, destino_idx in enumerate(indices):
            numero = f"ETA-TAT-{base + i + 1:04d}"
            estado_destino = FLUJO_PASOS[destino_idx]["estado"]
            ubicacion = (
                f"{random.choice(UBICACIONES)} · Nivel {random.randint(1, 4)}"
                if estado_destino in en_deposito_set else ""
            )
            fecha_eta = fecha_en_rango()
            eta = self._eta_create(
                numero=numero,
                cliente=cliente,
                agentes=agentes,
                contenedores=contenedores,
                conductores=conductores,
                camiones=camiones,
                empresas=empresas,
                fecha_eta=fecha_eta,
                destino_idx=destino_idx,
                ubicacion=ubicacion,
                tipo_proceso=ETA.TipoProceso.DIRECTO,
                observaciones="Cliente principal demo (Tattersall).",
            )
            if eta:
                creadas += 1

        self.stdout.write(
            f"  · ETAs Tattersall generadas: {creadas} "
            f"(período 2025-01-01 → hoy)."
        )
