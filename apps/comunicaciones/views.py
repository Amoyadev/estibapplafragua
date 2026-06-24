"""Vistas de la bandeja de correos IMAP — Estibapp."""
import email
import imaplib
import re
from email.header import decode_header

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.operaciones.permissions import ROL_ADMIN, ROL_COORDINADOR, en_grupos

from .models import CorreoETA

# ── Configuración IMAP (variables de entorno en producción) ──────────────────
import os

IMAP_HOST     = os.environ.get("IMAP_HOST",  "outlook.office365.com")
IMAP_PORT     = int(os.environ.get("IMAP_PORT", "993"))
IMAP_USER     = os.environ.get("IMAP_USER",  "nfarias@logisticayalmacenaje.cl")
IMAP_PASSWORD = os.environ.get("IMAP_PASSWORD", "")
IMAP_FOLDER   = os.environ.get("IMAP_FOLDER", "INBOX")
IMAP_DIAS     = int(os.environ.get("IMAP_DIAS", "30"))  # ventana de búsqueda


# ── Helpers ───────────────────────────────────────────────────────────────────

def _decode_header_str(raw):
    """Decodifica un header de correo (puede estar en base64/QP)."""
    parts = decode_header(raw or "")
    resultado = []
    for part, enc in parts:
        if isinstance(part, bytes):
            resultado.append(part.decode(enc or "utf-8", errors="replace"))
        else:
            resultado.append(str(part))
    return " ".join(resultado).strip()


def _get_body(msg):
    """Extrae el cuerpo en texto plano del mensaje."""
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            cd = str(part.get("Content-Disposition", ""))
            if ct == "text/plain" and "attachment" not in cd:
                charset = part.get_content_charset() or "utf-8"
                return part.get_payload(decode=True).decode(charset, errors="replace")
    payload = msg.get_payload(decode=True)
    if payload:
        charset = msg.get_content_charset() or "utf-8"
        return payload.decode(charset, errors="replace")
    return ""


def _parse_campo(cuerpo, patron):
    """Busca el primer grupo del patrón (case-insensitive) en el cuerpo."""
    m = re.search(patron, cuerpo, re.IGNORECASE)
    return m.group(1).strip() if m else ""


def _fetch_imap():
    """
    Conecta al buzón IMAP, descarga correos de los últimos IMAP_DIAS días
    y guarda los nuevos en CorreoETA.  Retorna el número de registros nuevos.
    """
    from datetime import datetime, timedelta, timezone as dt_tz

    mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
    mail.login(IMAP_USER, IMAP_PASSWORD)
    mail.select(IMAP_FOLDER)

    # Fecha límite en formato que IMAP entiende: "07-Jun-2026"
    desde = (datetime.now(dt_tz.utc) - timedelta(days=IMAP_DIAS)).strftime("%d-%b-%Y")
    _, ids = mail.search(None, f'SINCE "{desde}" NOT DELETED')

    nuevos = 0
    for num in ids[0].split():
        _, data = mail.fetch(num, "(RFC822)")
        raw = data[0][1]
        msg = email.message_from_bytes(raw)

        msg_id  = msg.get("Message-ID", "").strip() or f"_no_id_{num.decode()}"
        asunto  = _decode_header_str(msg.get("Subject", ""))
        de_raw  = _decode_header_str(msg.get("From", ""))
        date_str = msg.get("Date", "")

        # Parsear fecha
        try:
            from email.utils import parsedate_to_datetime
            fecha_correo = parsedate_to_datetime(date_str)
            if timezone.is_naive(fecha_correo):
                fecha_correo = timezone.make_aware(fecha_correo)
        except Exception:
            fecha_correo = timezone.now()

        # Saltar si ya existe
        if CorreoETA.objects.filter(msg_id=msg_id).exists():
            continue

        cuerpo = _get_body(msg)

        # Parsear campos solo si es un correo de ETA
        es_eta = any(
            k in asunto.upper()
            for k in ("ETA EN SECUENCIA", "ETA SECUENCIA", "ETA", "SECUENCIA")
        )

        numero_eta        = _parse_campo(cuerpo, r"ETA[:\s#]+([A-Z0-9\-]+)") if es_eta else ""
        cliente_nombre    = _parse_campo(cuerpo, r"Cliente[:\s]+(.+?)[\r\n]") if es_eta else ""
        puerto            = _parse_campo(cuerpo, r"Puerto[:\s]+(.+?)[\r\n]")  if es_eta else ""
        contenedor_codigo = re.search(r"[A-Z]{4}[0-9]{7}", cuerpo)
        contenedor_codigo = contenedor_codigo.group(0) if contenedor_codigo else ""

        CorreoETA.objects.create(
            msg_id=msg_id,
            asunto=asunto,
            remitente=de_raw,
            fecha_correo=fecha_correo,
            numero_eta=numero_eta,
            cliente_nombre=cliente_nombre,
            puerto=puerto,
            contenedor_codigo=contenedor_codigo,
            cuerpo=cuerpo[:8000],  # limitar tamaño
        )
        nuevos += 1

    mail.logout()
    return nuevos


# ── Vistas ─────────────────────────────────────────────────────────────────────

def bandeja_correos(request):
    """Muestra la bandeja de correos IMAP extraídos."""
    if not en_grupos(request.user, [ROL_ADMIN, ROL_COORDINADOR]):
        return redirect("login")

    estado_filtro = request.GET.get("estado", "")
    qs = CorreoETA.objects.all()
    if estado_filtro:
        qs = qs.filter(estado=estado_filtro)

    correos = qs[:100]
    total   = CorreoETA.objects.count()
    pendientes = CorreoETA.objects.filter(estado=CorreoETA.Estado.PENDIENTE).count()

    return render(request, "comunicaciones/bandeja_correos.html", {
        "correos":       correos,
        "total":         total,
        "pendientes":    pendientes,
        "estado_filtro": estado_filtro,
        "estados":       CorreoETA.Estado.choices,
        "imap_user":     IMAP_USER,
    })


def sincronizar_correos(request):
    """Dispara la sincronización IMAP y redirige a la bandeja."""
    if not en_grupos(request.user, [ROL_ADMIN]):
        messages.error(request, "Solo el administrador puede sincronizar correos.")
        return redirect("comunicaciones:bandeja")
    if request.method == "POST":
        if not IMAP_PASSWORD:
            messages.warning(
                request,
                "Contraseña IMAP no configurada. "
                "Define la variable de entorno IMAP_PASSWORD en el servidor."
            )
        else:
            try:
                n = _fetch_imap()
                messages.success(
                    request,
                    f"Sincronización completada: {n} correo(s) nuevo(s) descargado(s)."
                )
            except imaplib.IMAP4.error as exc:
                messages.error(request, f"Error IMAP: {exc}")
            except Exception as exc:
                messages.error(request, f"Error inesperado: {exc}")
    return redirect("comunicaciones:bandeja")


def marcar_correo(request, pk):
    """Cambia el estado de un correo (PROCESADO / IGNORADO)."""
    if not en_grupos(request.user, [ROL_ADMIN, ROL_COORDINADOR]):
        return redirect("login")
    correo = get_object_or_404(CorreoETA, pk=pk)
    if request.method == "POST":
        nuevo_estado = request.POST.get("estado", "")
        if nuevo_estado in dict(CorreoETA.Estado.choices):
            correo.estado = nuevo_estado
            correo.save(update_fields=["estado"])
            messages.success(request, f"Correo marcado como {correo.get_estado_display()}.")
    return redirect("comunicaciones:bandeja")


def ver_correo(request, pk):
    """Muestra el cuerpo completo de un correo."""
    if not en_grupos(request.user, [ROL_ADMIN, ROL_COORDINADOR]):
        return redirect("login")
    correo = get_object_or_404(CorreoETA, pk=pk)
    return render(request, "comunicaciones/ver_correo.html", {"correo": correo})
