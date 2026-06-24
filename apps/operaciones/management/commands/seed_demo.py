"""
Comando de carga de datos de demostración (seed) para Estibapp.

Crea:
  - 3 usuarios QA (uno por rol) para revisar la app según el manual.
  - Datos maestros aleatorios (clientes, conductores, camiones, agentes,
    contenedores).
  - Algunas ETAs en distintos estados, con sus movimientos.

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
from datetime import datetime, time, timedelta

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

# Clave genérica por defecto para los usuarios QA (documentada en operativa.md).
PASSWORD_QA = "Estibapp2025*"

# ================================================================
# USUARIOS CORPORATIVOS REALES  (EDITABLE — modular)
# ----------------------------------------------------------------
# A diferencia de los QA (que son de prueba), aquí van las personas
# reales que usarán la app en producción. La nomenclatura del usuario
# y del correo se genera SOLA con `nomenclatura_usuario()`:
#   "Javier Ovalle Calderón"  ->  usuario "Jovalle"  ·  correo "jovalle@<dominio>"
#   (primera letra del nombre + primer apellido)
#
# ➕ PARA AGREGAR UNA PERSONA: añade una tupla (nombre_completo, rol).
#    Los roles válidos son ROL_ADMIN, ROL_COORDINADOR, ROL_PATIO.
# ================================================================
# Dominio del correo corporativo. Se puede sobrescribir con la variable
# de entorno DOMINIO_CORPORATIVO o el argumento --dominio.
DOMINIO_CORPORATIVO = os.environ.get("DOMINIO_CORPORATIVO", "estibapp.cl")

USUARIOS_CORPORATIVOS = [
    # (nombre_completo, rol)
    ("Javier Ovalle Calderón", ROL_ADMIN),  # Administrador portuario
]


def _sin_acentos(texto):
    """Quita tildes/acentos para construir usuarios y correos válidos."""
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def nomenclatura_usuario(nombre_completo, dominio=None):
    """Devuelve (username, email) según la convención de la empresa.

    Convención: primera letra del primer nombre + primer apellido.
        "Javier Ovalle Calderón" -> ("Jovalle", "jovalle@<dominio>")

    Si en el futuro cambia la regla (ej. nombre.apellido), basta con
    editar esta única función: todo el sistema la reutiliza.
    """
    dominio = dominio or DOMINIO_CORPORATIVO
    partes = _sin_acentos(nombre_completo.strip()).split()
    nombre = partes[0] if partes else "usuario"
    apellido = partes[1] if len(partes) > 1 else ""
    username = (nombre[:1] + apellido).lower()
    email = f"{username}@{dominio}"
    return username, email

# ---- Catálogos de ejemplo (datos genéricos, no reales) ----
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
    """Genera un RUT con formato chileno (sin validar dígito verificador real)."""
    cuerpo = random.randint(5_000_000, 24_000_000)
    dv = random.choice("0123456789K")
    return f"{cuerpo:,}".replace(",", ".") + f"-{dv}"


def patente_aleatoria():
    letras = "".join(random.choices("BCDFGHJKLPRSTVWXYZ", k=4))
    return f"{letras}{random.randint(10, 99)}"


def codigo_contenedor():
    letras = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=4))
    return f"{letras}{random.randint(1000000, 9999999)}"


def fecha_demo():
    """Fecha aleatoria dentro de los últimos ~5 meses.

    Distribuir las ETAs en el tiempo hace que los gráficos temporales
    (actividad por mes, retiros vs despachos) muestren una serie real en
    lugar de un único punto en el día de hoy.
    """
    return timezone.now().date() - timedelta(days=random.randint(0, 360))


class Command(BaseCommand):
    help = "Crea usuarios QA por rol y datos de demostración aleatorios."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Borra ETAs y movimientos antes de generar nuevos.",
        )
        parser.add_argument(
            "--password",
            default=PASSWORD_QA,
            help="Contraseña para los usuarios QA (por defecto Estibapp2025*).",
        )
        parser.add_argument(
            "--etas",
            type=int,
            default=40,
            help="Cantidad de ETAs a generar (por defecto 40).",
        )
        parser.add_argument(
            "--admin-password",
            default=os.environ.get("ADMIN_PASSWORD", PASSWORD_QA),
            help="Contraseña inicial de los usuarios corporativos reales "
            "(ej. Jovalle). Cámbiala antes de publicar.",
        )
        parser.add_argument(
            "--dominio",
            default=DOMINIO_CORPORATIVO,
            help="Dominio del correo corporativo (por defecto estibapp.cl).",
        )

    def handle(self, *args, **options):
        random.seed(42)  # reproducible
        password = options["password"]

        if options["reset"]:
            Movimiento.objects.all().delete()
            ETA.objects.all().delete()
            self.stdout.write(self.style.WARNING("ETAs y movimientos eliminados."))

        self._crear_usuarios_qa(password)
        self._crear_usuarios_corporativos(
            options["admin_password"], options["dominio"]
        )
        empresas, agentes, clientes, conductores, camiones, contenedores = (
            self._crear_catalogos()
        )
        self._crear_etas(
            options["etas"], empresas, agentes, clientes, conductores, camiones, contenedores
        )
        self._crear_tattersall(agentes, conductores, camiones, contenedores, empresas)

        self.stdout.write(self.style.SUCCESS("\n✅ Datos de demostración cargados."))
        self.stdout.write(
            "Usuarios QA (clave: "
            + self.style.NOTICE(password)
            + "):\n"
            "  - QA_Administrador  (rol Administrador, sin admin Django)\n"
            "  - QA_Coordinador    (rol Coordinador)\n"
            "  - QA_Patio          (rol Encargado de Patio)\n"
            "Usuarios corporativos reales (clave inicial: "
            + self.style.NOTICE(options["admin_password"])
            + " — cámbiala antes de publicar):\n"
            "  - jovalle           (Javier Ovalle Calderón, rol Administrador)\n"
            "El admin Django (/admin/) es solo para el dev: crea un superusuario\n"
            "con `python manage.py createsuperuser`.\n"
            "Detalle y flujo de prueba en docs/operativa.md"
        )

    # ------------------------------------------------------------------
    def _crear_usuarios_qa(self, password):
        definiciones = [
            # (usuario, rol, is_staff, is_superuser)
            # El rol Administrador es de NEGOCIO: NO accede al admin Django.
            # El master de Django queda solo para el dev (createsuperuser).
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
            # Siempre re-aplica clave y flags (idempotente y predecible para QA).
            user.is_staff = is_staff
            user.is_superuser = is_superuser
            user.set_password(password)
            user.save()
            grupo = Group.objects.filter(name=rol).first()
            if grupo:
                user.groups.set([grupo])
            estado = "creado" if creado else "actualizado"
            self.stdout.write(f"  · Usuario {username} ({rol}) {estado}.")

    # ------------------------------------------------------------------
    def _crear_usuarios_corporativos(self, password, dominio):
        """Crea las personas reales (ej. el administrador portuario Jovalle).

        El usuario y el correo se derivan del nombre con la convención de la
        empresa (ver `nomenclatura_usuario`). Es idempotente: re-ejecutar
        actualiza la clave y el rol sin duplicar.
        """
        if not USUARIOS_CORPORATIVOS:
            return
        for nombre_completo, rol in USUARIOS_CORPORATIVOS:
            username, email = nomenclatura_usuario(nombre_completo, dominio)
            partes = nombre_completo.split()
            first_name = partes[0] if partes else ""
            last_name = " ".join(partes[1:]) if len(partes) > 1 else ""
            user, creado = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "first_name": first_name,
                    "last_name": last_name,
                    "is_staff": False,
                    "is_superuser": False,
                },
            )
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.set_password(password)
            user.save()
            grupo = Group.objects.filter(name=rol).first()
            if grupo:
                user.groups.set([grupo])
            estado = "creado" if creado else "actualizado"
            self.stdout.write(
                f"  · Usuario corporativo {username} <{email}> ({rol}) {estado}."
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
        for _ in range(6):
            patente = patente_aleatoria()
            camion, _c = Camion.objects.get_or_create(
                patente=patente, defaults={"marca": random.choice(MARCAS)}
            )
            camiones.append(camion)
        contenedores = []
        tipos = [t for t, _ in Contenedor.Tipo.choices]
        estados = [e for e, _ in Contenedor.Estado.choices]
        for _ in range(15):
            codigo = codigo_contenedor()
            cont, _c = Contenedor.objects.get_or_create(
                codigo=codigo,
                defaults={
                    "tipo": random.choice(tipos),
                    "estado": random.choice(estados),
                },
            )
            contenedores.append(cont)

        self.stdout.write(
            f"  · Catálogos: {len(empresas)} empresas, {len(agentes)} agentes, "
            f"{len(clientes)} clientes, {len(conductores)} conductores, "
            f"{len(camiones)} camiones, {len(contenedores)} contenedores."
        )
        return empresas, agentes, clientes, conductores, camiones, contenedores

    # ------------------------------------------------------------------
    def _crear_etas(self, cantidad, empresas, agentes, clientes, conductores, camiones, contenedores):
        creadas = 0
        base = ETA.objects.count()
        en_deposito = {ETA.EstadoCiclo.EN_PATIO, ETA.EstadoCiclo.ALMACENADO}
        for i in range(cantidad):
            numero = f"ETA-2026-{base + i + 1:04d}"
            if ETA.objects.filter(numero=numero).exists():
                continue
            # Estado objetivo: avanza la ETA hasta un paso aleatorio del ciclo.
            destino_idx = random.randint(0, len(FLUJO_PASOS) - 1)
            estado_destino = FLUJO_PASOS[destino_idx]["estado"]
            ubicacion = (
                f"{random.choice(UBICACIONES)} · Nivel {random.randint(1, 4)}"
                if estado_destino in en_deposito
                else ""
            )
            fecha_eta = fecha_demo()
            eta = ETA.objects.create(
                numero=numero,
                cliente=random.choice(clientes),
                agente=random.choice(agentes),
                contenedor=random.choice(contenedores),
                conductor=random.choice(conductores) if destino_idx >= 1 else None,
                camion=random.choice(camiones) if destino_idx >= 1 else None,
                deposito=random.choice(DEPOSITOS),
                ubicacion=ubicacion,
                fecha=fecha_eta,
                fecha_retiro=fecha_eta if destino_idx >= 1 else None,
                hora_retiro=time(random.randint(8, 18), random.choice([0, 30])),
                tipo_proceso=random.choice(
                    [ETA.TipoProceso.DIRECTO, ETA.TipoProceso.INDIRECTO]
                ),
                estado=estado_destino,
                observaciones="Registro de demostración (datos genéricos).",
            )
            # Genera los movimientos correspondientes a los estados recorridos.
            self._movimientos_eta(eta, destino_idx, empresas)
            creadas += 1
        self.stdout.write(f"  · ETAs generadas: {creadas}.")

    # ------------------------------------------------------------------
    def _movimientos_eta(self, eta, hasta_idx, empresas):
        """Crea los movimientos del ciclo con fechas escalonadas.

        Las fechas se reparten en el tiempo (no todas "ahora") para que los
        gráficos de tiempo por etapa y de retiros/despachos tengan datos reales.
        """
        cursor = timezone.make_aware(
            datetime.combine(eta.fecha, time(random.randint(7, 10), 0))
        )
        for idx in range(1, hasta_idx + 1):
            tipo_mov = FLUJO_PASOS[idx]["mov"]
            if not tipo_mov:
                continue
            cursor += timedelta(hours=random.randint(6, 60))
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
    def _crear_tattersall(self, agentes, conductores, camiones, contenedores, empresas):
        """
        Cliente principal de la demo: **Tattersall** concentra ~47% del depósito.
        Además tiene contenedores ya **despachados a puerto** (cierre final: de
        vuelta en puerto), según la convención de negocio.
        """
        cliente, _c = Cliente.objects.get_or_create(
            nombre="Tattersall",
            defaults={
                "rut": "90.412.000-6",
                "email": "operaciones@tattersall.cl",
                "telefono": "+56 2 2630 0000",
                "activo": True,
            },
        )
        # Cuántos hay en depósito de OTROS clientes, para resolver T/(T+otros)=0.47.
        otros = (
            ETA.objects.filter(estado__in=ESTADOS_EN_DEPOSITO)
            .exclude(cliente=cliente)
            .count()
        )
        en_deposito = max(4, round(0.887 * otros)) if otros else 6
        devueltos = max(3, round(en_deposito * 0.6))  # despachados a puerto (cierre final)

        base = ETA.objects.count()
        idx_almacenado = 3  # ALMACENADO inicial en FLUJO_PASOS
        idx_puerto = len(FLUJO_PASOS) - 1  # DESPACHADO_PUERTO (cierre final)
        self._correlativo_tat = 0

        def _nueva(estado_destino, destino_idx, en_dep):
            self._correlativo_tat += 1
            numero = f"ETA-TAT-{base + self._correlativo_tat:04d}"
            if ETA.objects.filter(numero=numero).exists():
                return
            fecha_tat = fecha_demo()
            eta = ETA.objects.create(
                numero=numero,
                cliente=cliente,
                agente=random.choice(agentes),
                contenedor=random.choice(contenedores),
                conductor=random.choice(conductores),
                camion=random.choice(camiones),
                deposito=random.choice(DEPOSITOS),
                ubicacion=(
                    f"{random.choice(UBICACIONES)} · Nivel {random.randint(1, 4)}"
                    if en_dep else ""
                ),
                fecha=fecha_tat,
                fecha_retiro=fecha_tat,
                hora_retiro=time(random.randint(8, 18), random.choice([0, 30])),
                tipo_proceso=ETA.TipoProceso.DIRECTO,
                estado=estado_destino,
                observaciones="Cliente principal demo (Tattersall).",
            )
            self._movimientos_eta(eta, destino_idx, empresas)

        for _ in range(en_deposito):
            _nueva(ETA.EstadoCiclo.ALMACENADO, idx_almacenado, True)
        for _ in range(devueltos):
            _nueva(ETA.EstadoCiclo.DESPACHADO_PUERTO, idx_puerto, False)

        self.stdout.write(
            f"  · Tattersall: {en_deposito} en depósito (~47%) + "
            f"{devueltos} devueltos a puerto (DESPACHADO_PUERTO)."
        )
