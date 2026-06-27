"""
Signals de auditoría: traducen eventos de Django en registros de bitácora.

- post_save / post_delete sobre los modelos del dominio → CREAR/ACTUALIZAR/ELIMINAR.
- user_logged_in / user_logged_out / user_login_failed → eventos de seguridad.

Cada registro se escribe en BD (RegistroAuditoria) y, en paralelo, en los
archivos .log mediante los loggers `auditoria` y `seguridad`. Todo va envuelto
en try/except: la auditoría NUNCA debe romper la operación del usuario.
"""
import logging

from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out,
    user_login_failed,
)
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.operaciones.models import (
    ETA,
    AgentePortuario,
    Camion,
    Cliente,
    Conductor,
    Contenedor,
    Empresa,
    Movimiento,
)

from .middleware import _client_ip, get_actor
from .models import RegistroAuditoria

log_audit = logging.getLogger("auditoria")
log_seg = logging.getLogger("seguridad")

# Modelos del dominio que se auditan automáticamente.
MODELOS_AUDITADOS = (
    ETA,
    Movimiento,
    Contenedor,
    Cliente,
    Conductor,
    Camion,
    Empresa,
    AgentePortuario,
)

# Campos que nunca se guardan en el snapshot (ruido o sensibles).
_CAMPOS_EXCLUIDOS = {"creado", "actualizado", "password"}


def _snapshot(instance):
    """Foto str de los campos concretos del objeto (para trazabilidad)."""
    datos = {}
    for campo in instance._meta.concrete_fields:
        if campo.name in _CAMPOS_EXCLUIDOS:
            continue
        try:
            datos[campo.name] = str(getattr(instance, campo.attname))
        except Exception:  # noqa: BLE001
            continue
    return datos


def _registrar(accion, instance=None, actor=None, **extra):
    """Crea el RegistroAuditoria y escribe la línea de log. A prueba de fallos."""
    actor = actor or get_actor() or {}
    usuario = actor.get("user")
    nombre = ""
    if usuario is not None:
        nombre = usuario.get_full_name() or usuario.get_username()

    modelo = extra.get("modelo", "")
    objeto_id = extra.get("objeto_id", "")
    objeto_repr = extra.get("objeto_repr", "")
    cambios = extra.get("cambios", {})

    if instance is not None:
        modelo = instance._meta.verbose_name.title()
        objeto_id = str(getattr(instance, "pk", "") or "")
        objeto_repr = str(instance)[:255]

    try:
        RegistroAuditoria.objects.create(
            usuario=usuario,
            usuario_nombre=nombre,
            accion=accion,
            modelo=modelo,
            objeto_id=objeto_id,
            objeto_repr=objeto_repr,
            cambios=cambios,
            ip=actor.get("ip"),
            ruta=actor.get("ruta", "")[:255],
        )
    except Exception:  # noqa: BLE001 - la tabla puede no existir aún (migraciones)
        pass

    # Log en archivo (siempre, aunque la BD falle).
    log_audit.info(
        "accion=%s usuario=%s modelo=%s id=%s obj=%s ip=%s ruta=%s",
        accion,
        nombre or "sistema",
        modelo,
        objeto_id,
        objeto_repr,
        actor.get("ip", "-"),
        actor.get("ruta", "-"),
    )


# ------------------------------------------------------------------
# Cambios en los modelos del dominio
# ------------------------------------------------------------------
@receiver(post_save)
def _on_save(sender, instance, created, **kwargs):
    if sender not in MODELOS_AUDITADOS:
        return
    accion = RegistroAuditoria.Accion.CREAR if created else RegistroAuditoria.Accion.ACTUALIZAR
    _registrar(accion, instance=instance, cambios=_snapshot(instance))


@receiver(post_delete)
def _on_delete(sender, instance, **kwargs):
    if sender not in MODELOS_AUDITADOS:
        return
    _registrar(
        RegistroAuditoria.Accion.ELIMINAR,
        instance=instance,
        cambios=_snapshot(instance),
    )


# ------------------------------------------------------------------
# Eventos de sesión / seguridad
# ------------------------------------------------------------------
@receiver(user_logged_in)
def _on_login(sender, request, user, **kwargs):
    actor = {
        "user": user,
        "ip": _client_ip(request) if request else None,
        "ruta": getattr(request, "path", ""),
    }
    _registrar(RegistroAuditoria.Accion.LOGIN, actor=actor, modelo="Sesión")
    log_seg.info("LOGIN ok usuario=%s ip=%s", user.get_username(), actor["ip"])


@receiver(user_logged_out)
def _on_logout(sender, request, user, **kwargs):
    if user is None:
        return
    actor = {
        "user": user,
        "ip": _client_ip(request) if request else None,
        "ruta": getattr(request, "path", ""),
    }
    _registrar(RegistroAuditoria.Accion.LOGOUT, actor=actor, modelo="Sesión")
    log_seg.info("LOGOUT usuario=%s ip=%s", user.get_username(), actor["ip"])


@receiver(user_login_failed)
def _on_login_failed(sender, credentials, request=None, **kwargs):
    intento = credentials.get("username", "?")
    ip = _client_ip(request) if request else None
    _registrar(
        RegistroAuditoria.Accion.LOGIN_FALLIDO,
        actor={"user": None, "ip": ip, "ruta": getattr(request, "path", "")},
        modelo="Sesión",
        objeto_repr=f"usuario intentado: {intento}",
    )
    # WARNING para que destaque en el log de seguridad (posible fuerza bruta).
    log_seg.warning("LOGIN fallido usuario=%s ip=%s", intento, ip)
