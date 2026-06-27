"""Filtros de plantilla auxiliares para Estibapp."""
from django import template

register = template.Library()


@register.filter
def get_attr(obj, nombre):
    """
    Obtiene un atributo dinámico de un objeto en la plantilla.
    Si el atributo es un método (ej. get_tipo_display), lo invoca.
    Uso: {{ objeto|get_attr:"nombre_campo" }}
    """
    valor = getattr(obj, nombre, "")
    if callable(valor):
        valor = valor()
    return valor


@register.filter
def en_grupo(user, nombres):
    """True si el usuario es superuser o pertenece a algún grupo (coma-separado)."""
    if user.is_superuser:
        return True
    grupos = [n.strip() for n in nombres.split(",")]
    return user.groups.filter(name__in=grupos).exists()


# ============================================================
# Colores por estado de ETA (estilo paneles de Confluence)
# ------------------------------------------------------------
# Cada estado del ciclo se asocia a un color "genérico" semántico:
#   warning   → amarillo (pendiente / requiere acción)
#   info      → celeste  (en proceso inicial)
#   secondary → plomo    (en depósito / almacenado)
#   success   → verde    (despacho a cliente · cierre parcial)
#   dark      → negro    (despacho a puerto · cierre final)
# El foco es trazar al contenedor: los estados de "cierre" son los que
# tienen al contenedor FUERA del depósito.
# EDITABLE: ajusta el color de un estado cambiando su valor aquí.
# ============================================================
ESTADO_VARIANTE = {
    "SOLICITADO": "warning",
    "ASIGNADO": "info",
    "EN_PATIO": "primary",
    "ALMACENADO": "secondary",
    "DESPACHADO_CLIENTE": "success",
    "DESPACHADO_PUERTO": "dark",
}

# Color del chip de ubicación física del contenedor (trazabilidad).
UBICACION_VARIANTE = {
    "Puerto (origen)": "info",
    "Depósito": "success",
    "En cliente": "warning",
    "Puerto (final)": "dark",
}

# Variantes claras que necesitan texto oscuro para buen contraste.
_TEXTO_OSCURO = {"warning", "info", "light"}


@register.filter
def estado_variante(estado):
    """Devuelve la variante Bootstrap (warning/info/...) para un estado."""
    return ESTADO_VARIANTE.get(str(estado), "secondary")


@register.filter
def ubicacion_badge(ubicacion):
    """Clase de badge coloreada según la ubicación física del contenedor."""
    variante = UBICACION_VARIANTE.get(str(ubicacion), "secondary")
    extra = " text-dark" if variante in _TEXTO_OSCURO else ""
    return f"bg-{variante}{extra}"


@register.filter
def estado_badge(estado):
    """Clase completa para una etiqueta (badge) coloreada por estado."""
    variante = ESTADO_VARIANTE.get(str(estado), "secondary")
    extra = " text-dark" if variante in _TEXTO_OSCURO else ""
    return f"bg-{variante}{extra}"


@register.filter
def estado_btn(estado):
    """Clase de botón Bootstrap coloreada por estado."""
    return f"btn-{ESTADO_VARIANTE.get(str(estado), 'secondary')}"
