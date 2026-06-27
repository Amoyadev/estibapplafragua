"""Vistas de la bandeja de correos — Estibapp.

Método de sincronización: Microsoft Graph API (OAuth2 client credentials).
El flujo IMAP con Basic Auth fue deshabilitado por Microsoft en octubre 2022.

Variables de entorno requeridas (en .env del droplet):
    GRAPH_TENANT_ID      ID del tenant Azure AD (directorio)
    GRAPH_CLIENT_ID      ID de la app registrada en Azure AD
    GRAPH_CLIENT_SECRET  Secreto de la app
    GRAPH_USER_EMAIL     Buzón a leer (ej. nfarias@logisticayalmacenaje.cl)
    IMAP_DIAS            Ventana de búsqueda en días (default 30)
"""
import os
import re

import requests as http_requests

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.operaciones.permissions import ROL_ADMIN, ROL_COORDINADOR, en_grupos

from .models import CorreoETA

# ── Configuración Graph API ───────────────────────────────────────────────────
GRAPH_TENANT_ID     = os.environ.get("GRAPH_TENANT_ID", "")
GRAPH_CLIENT_ID     = os.environ.get("GRAPH_CLIENT_ID", "")
GRAPH_CLIENT_SECRET = os.environ.get("GRAPH_CLIENT_SECRET", "")
GRAPH_USER_EMAIL    = os.environ.get(
    "GRAPH_USER_EMAIL",
    os.environ.get("IMAP_USER", "nfarias@logisticayalmacenaje.cl"),
)
IMAP_DIAS = int(os.environ.get("IMAP_DIAS", "30"))

GRAPH_CONFIGURADO = all([GRAPH_TENANT_ID, GRAPH_CLIENT_ID, GRAPH_CLIENT_SECRET])


# ── Helpers de parseo ─────────────────────────────────────────────────────────

def _parse_campo(cuerpo, patron):
    m = re.search(patron, cuerpo, re.IGNORECASE)
    return m.group(1).strip() if m else ""


def _limpiar_html(html):
    """Elimina tags HTML y colapsa espacios."""
    texto = re.sub(r"<[^>]+>", " ", html or "")
    return re.sub(r"\s+", " ", texto).strip()


# ── Lógica Graph API ──────────────────────────────────────────────────────────

def _get_access_token():
    """Obtiene token OAuth2 via client_credentials para Graph API."""
    url = f"https://login.microsoftonline.com/{GRAPH_TENANT_ID}/oauth2/v2.0/token"
    resp = http_requests.post(url, data={
        "grant_type":    "client_credentials",
        "client_id":     GRAPH_CLIENT_ID,
        "client_secret": GRAPH_CLIENT_SECRET,
        "scope":         "https://graph.microsoft.com/.default",
    }, timeout=15)
    resp.raise_for_status()
    return resp.json()["access_token"]


def _fetch_graph():
    """
    Lee correos del buzón via Microsoft Graph API y guarda los nuevos en CorreoETA.
    Retorna el número de registros nuevos.
    """
    from datetime import datetime, timedelta, timezone as dt_tz

    token = _get_access_token()
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

    desde = (
        datetime.now(dt_tz.utc) - timedelta(days=IMAP_DIAS)
    ).strftime("%Y-%m-%dT%H:%M:%SZ")

    url = (
        f"https://graph.microsoft.com/v1.0/users/{GRAPH_USER_EMAIL}/messages"
        f"?$filter=receivedDateTime ge {desde}"
        f"&$select=id,subject,from,receivedDateTime,body,isRead"
        f"&$top=50&$orderby=receivedDateTime desc"
    )

    nuevos = 0
    while url:
        resp = http_requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
        data = resp.json()

        for msg in data.get("value", []):
            msg_id = msg.get("id", "")
            if not msg_id or CorreoETA.objects.filter(msg_id=msg_id).exists():
                continue

            asunto    = msg.get("subject", "") or ""
            de_raw    = (msg.get("from") or {}).get("emailAddress", {}).get("address", "")
            fecha_str = msg.get("receivedDateTime", "")
            cuerpo_raw = (msg.get("body") or {}).get("content", "")
            cuerpo    = _limpiar_html(cuerpo_raw)

            # Parsear fecha ISO
            try:
                fecha_correo = datetime.fromisoformat(fecha_str.replace("Z", "+00:00"))
            except Exception:
                fecha_correo = timezone.now()

            es_eta = any(
                k in asunto.upper()
                for k in ("ETA EN SECUENCIA", "ETA SECUENCIA", "ETA", "SECUENCIA")
            )

            numero_eta        = _parse_campo(cuerpo, r"ETA[:\s#]+([A-Z0-9\-]+)") if es_eta else ""
            cliente_nombre    = _parse_campo(cuerpo, r"Cliente[:\s]+(.+?)[\r\n]") if es_eta else ""
            puerto            = _parse_campo(cuerpo, r"Puerto[:\s]+(.+?)[\r\n]")  if es_eta else ""
            m_cont            = re.search(r"[A-Z]{4}[0-9]{7}", cuerpo)
            contenedor_codigo = m_cont.group(0) if m_cont else ""

            CorreoETA.objects.create(
                msg_id=msg_id,
                asunto=asunto,
                remitente=de_raw,
                fecha_correo=fecha_correo,
                numero_eta=numero_eta,
                cliente_nombre=cliente_nombre,
                puerto=puerto,
                contenedor_codigo=contenedor_codigo,
                cuerpo=cuerpo[:8000],
            )
            nuevos += 1

        url = data.get("@odata.nextLink")  # paginación automática

    return nuevos


# ── Vistas ────────────────────────────────────────────────────────────────────

def bandeja_correos(request):
    from django.core.paginator import Paginator
    if not en_grupos(request.user, [ROL_ADMIN, ROL_COORDINADOR]):
        return redirect("login")

    estado_filtro = request.GET.get("estado", "")
    qs = CorreoETA.objects.all().order_by("-fecha_correo")
    if estado_filtro:
        qs = qs.filter(estado=estado_filtro)

    paginator  = Paginator(qs, 20)
    page_num   = request.GET.get("page", 1)
    page_obj   = paginator.get_page(page_num)
    total      = CorreoETA.objects.count()
    pendientes = CorreoETA.objects.filter(estado=CorreoETA.Estado.PENDIENTE).count()

    return render(request, "comunicaciones/bandeja_correos.html", {
        "correos":        page_obj,
        "page_obj":       page_obj,
        "is_paginated":   page_obj.has_other_pages(),
        "paginator":      paginator,
        "total":          total,
        "pendientes":     pendientes,
        "estado_filtro":  estado_filtro,
        "estados":        CorreoETA.Estado.choices,
        "graph_user":     GRAPH_USER_EMAIL,
        "graph_ok":       GRAPH_CONFIGURADO,
    })


def sincronizar_correos(request):
    if not en_grupos(request.user, [ROL_ADMIN]):
        messages.error(request, "Solo el administrador puede sincronizar correos.")
        return redirect("comunicaciones:bandeja")

    if request.method == "POST":
        if not GRAPH_CONFIGURADO:
            messages.warning(
                request,
                "Graph API no configurada. Definí GRAPH_TENANT_ID, "
                "GRAPH_CLIENT_ID y GRAPH_CLIENT_SECRET en el .env del servidor."
            )
        else:
            try:
                n = _fetch_graph()
                messages.success(
                    request,
                    f"Sincronización completada: {n} correo(s) nuevo(s) descargado(s)."
                )
            except http_requests.HTTPError as exc:
                messages.error(request, f"Error HTTP Graph API: {exc}")
            except Exception as exc:
                messages.error(request, f"Error inesperado: {exc}")

    return redirect("comunicaciones:bandeja")


def marcar_correo(request, pk):
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
    if not en_grupos(request.user, [ROL_ADMIN, ROL_COORDINADOR]):
        return redirect("login")
    correo = get_object_or_404(CorreoETA, pk=pk)
    return render(request, "comunicaciones/ver_correo.html", {"correo": correo})


def crear_eta_desde_correo(request, pk):
    """
    Vista intermedia: muestra un formulario pre-llenado con los datos
    parseados del correo para crear una ETA directamente desde la bandeja.
    """
    from datetime import date as date_cls
    from apps.operaciones.models import (
        ETA, Cliente, Contenedor, AgentePortuario
    )

    if not en_grupos(request.user, [ROL_ADMIN, ROL_COORDINADOR]):
        return redirect("login")

    correo = get_object_or_404(CorreoETA, pk=pk)

    cliente_match = None
    contenedor_match = None
    if correo.cliente_nombre:
        cliente_match = (
            Cliente.objects.filter(nombre__icontains=correo.cliente_nombre).first()
        )
    if correo.contenedor_codigo:
        contenedor_match = (
            Contenedor.objects.filter(codigo__iexact=correo.contenedor_codigo).first()
        )

    if request.method == "POST":
        numero        = request.POST.get("numero", "").strip()
        cliente_id    = request.POST.get("cliente")
        agente_id     = request.POST.get("agente")
        contenedor_id = request.POST.get("contenedor")
        fecha_str     = request.POST.get("fecha", "")

        errores = []
        if not numero:
            errores.append("El número ETA es requerido.")
        if ETA.objects.filter(numero=numero).exists():
            errores.append(f"Ya existe una ETA con número {numero}.")
        if not cliente_id:
            errores.append("El cliente es requerido.")
        if not agente_id:
            errores.append("El agente portuario es requerido.")
        if not contenedor_id:
            errores.append("El contenedor es requerido.")

        if not errores:
            try:
                fecha = date_cls.fromisoformat(fecha_str) if fecha_str else timezone.now().date()
                eta = ETA.objects.create(
                    numero=numero,
                    cliente_id=cliente_id,
                    agente_id=agente_id,
                    contenedor_id=contenedor_id,
                    fecha=fecha,
                    estado=ETA.EstadoCiclo.SOLICITADO,
                )
                correo.estado = CorreoETA.Estado.PROCESADO
                correo.save(update_fields=["estado"])
                messages.success(request, f"ETA {eta.numero} creada exitosamente desde correo.")
                return redirect("operaciones:eta_detalle", pk=eta.pk)
            except Exception as exc:
                errores.append(f"Error al crear la ETA: {exc}")

        for e in errores:
            messages.error(request, e)

    ctx = {
        "correo":           correo,
        "clientes":         Cliente.objects.all().order_by("nombre"),
        "agentes":          AgentePortuario.objects.all().order_by("nombre"),
        "contenedores":     Contenedor.objects.all().order_by("codigo"),
        "cliente_match":    cliente_match,
        "contenedor_match": contenedor_match,
        "hoy":              timezone.now().date().isoformat(),
        "numero_sugerido":  correo.numero_eta or "",
    }
    return render(request, "comunicaciones/crear_eta_desde_correo.html", ctx)
