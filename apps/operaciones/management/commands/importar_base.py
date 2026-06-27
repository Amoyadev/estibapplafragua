"""
Importa la "info base de alimentación" generada por la app de escritorio
Estibapp_portable (archivo JSON) hacia la base de datos de Django.

El JSON tiene esta forma (la produce  Estibapp_portable > Exportar):
    {
      "empresas":    [{"nombre":..., "rut":..., "activo": true}, ...],
      "agentes":     [{"nombre":..., "sigla":..., "activo": true}, ...],
      "ubicaciones": [{"nombre":..., "deposito":...}, ...],
      "operadores":  [{"nombre_completo":..., "rol":..., "username":..., "email":...}, ...],
      "etas":        [{"numero":..., "cliente":..., "agente":..., "deposito":...,
                       "ubicacion":..., "fecha":"AAAA-MM-DD", "estado":..., "observaciones":...}]
    }

Es IDEMPOTENTE: usa get_or_create por clave natural (nombre/numero/username),
así que re-importar el mismo archivo no duplica registros.

Uso:
    python manage.py importar_base base_estibapp.json
    python manage.py importar_base /ruta/al/base_estibapp.json --password "ClaveInicial*"
"""
import json
import os
import random

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.utils.dateparse import parse_date

from apps.operaciones.models import (
    AgentePortuario,
    Cliente,
    Contenedor,
    Empresa,
    ETA,
)

# Reutiliza la MISMA convención de usuario/correo que el seed (modular).
from apps.operaciones.management.commands.seed_demo import (
    PASSWORD_QA,
    nomenclatura_usuario,
)

User = get_user_model()

ESTADOS_VALIDOS = {e for e, _ in ETA.EstadoCiclo.choices}


def _codigo_contenedor():
    letras = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=4))
    return f"{letras}{random.randint(1000000, 9999999)}"


class Command(BaseCommand):
    help = "Carga datos base desde un JSON exportado por Estibapp_portable."

    def add_arguments(self, parser):
        parser.add_argument("archivo", help="Ruta al archivo base_estibapp.json")
        parser.add_argument(
            "--password",
            default=os.environ.get("ADMIN_PASSWORD", PASSWORD_QA),
            help="Clave inicial para los operadores creados (cámbiala luego).",
        )

    def handle(self, *args, **options):
        ruta = options["archivo"]
        if not os.path.exists(ruta):
            raise CommandError(f"No existe el archivo: {ruta}")
        try:
            # utf-8-sig tolera un eventual BOM al inicio del archivo.
            with open(ruta, encoding="utf-8-sig") as fh:
                datos = json.load(fh)
        except json.JSONDecodeError as exc:
            raise CommandError(f"JSON inválido: {exc}")

        self._importar_empresas(datos.get("empresas", []))
        self._importar_agentes(datos.get("agentes", []))
        self._importar_operadores(datos.get("operadores", []), options["password"])
        self._importar_etas(datos.get("etas", []))

        ubic = datos.get("ubicaciones", [])
        if ubic:
            self.stdout.write(
                f"  · Ubicaciones en el archivo: {len(ubic)} "
                "(se usan como referencia; el modelo ETA guarda la ubicación "
                "como texto)."
            )
        self.stdout.write(self.style.SUCCESS("\n✅ Importación completada."))

    # ------------------------------------------------------------------
    def _bool(self, valor, por_defecto=True):
        if isinstance(valor, bool):
            return valor
        if valor is None:
            return por_defecto
        return str(valor).strip().lower() in ("sí", "si", "true", "1", "x")

    # ------------------------------------------------------------------
    def _importar_empresas(self, registros):
        n = 0
        for r in registros:
            nombre = (r.get("nombre") or "").strip()
            if not nombre:
                continue
            Empresa.objects.get_or_create(
                nombre=nombre,
                defaults={
                    "rut": r.get("rut", ""),
                    "activo": self._bool(r.get("activo")),
                },
            )
            n += 1
        self.stdout.write(f"  · Empresas procesadas: {n}.")

    # ------------------------------------------------------------------
    def _importar_agentes(self, registros):
        n = 0
        for r in registros:
            nombre = (r.get("nombre") or "").strip()
            if not nombre:
                continue
            AgentePortuario.objects.get_or_create(
                nombre=nombre,
                defaults={
                    "sigla": r.get("sigla", ""),
                    "activo": self._bool(r.get("activo")),
                },
            )
            n += 1
        self.stdout.write(f"  · Agentes procesados: {n}.")

    # ------------------------------------------------------------------
    def _importar_operadores(self, registros, password):
        n = 0
        for r in registros:
            nombre = (r.get("nombre_completo") or "").strip()
            if not nombre:
                continue
            rol = (r.get("rol") or "").strip()
            username = (r.get("username") or "").strip()
            email = (r.get("email") or "").strip()
            if not username or not email:
                username, email = nomenclatura_usuario(nombre)
            partes = nombre.split()
            user, _creado = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "first_name": partes[0] if partes else "",
                    "last_name": " ".join(partes[1:]) if len(partes) > 1 else "",
                },
            )
            user.email = email
            user.set_password(password)
            user.save()
            grupo = Group.objects.filter(name=rol).first()
            if grupo:
                user.groups.set([grupo])
            n += 1
        self.stdout.write(f"  · Operadores procesados: {n}.")

    # ------------------------------------------------------------------
    def _importar_etas(self, registros):
        n = 0
        for r in registros:
            numero = (r.get("numero") or "").strip()
            if not numero or ETA.objects.filter(numero=numero).exists():
                continue
            cliente, _ = Cliente.objects.get_or_create(
                nombre=(r.get("cliente") or "Cliente sin nombre").strip()
            )
            agente, _ = AgentePortuario.objects.get_or_create(
                nombre=(r.get("agente") or "Agente sin nombre").strip()
            )
            contenedor = Contenedor.objects.create(codigo=_codigo_contenedor())
            estado = (r.get("estado") or "").strip()
            if estado not in ESTADOS_VALIDOS:
                estado = ETA.EstadoCiclo.SOLICITADO
            fecha = parse_date(r.get("fecha") or "") or timezone.now().date()
            ETA.objects.create(
                numero=numero,
                cliente=cliente,
                agente=agente,
                contenedor=contenedor,
                deposito=r.get("deposito", ""),
                ubicacion=r.get("ubicacion", ""),
                fecha=fecha,
                estado=estado,
                observaciones=r.get("observaciones", ""),
            )
            n += 1
        self.stdout.write(f"  · ETAs creadas: {n}.")
