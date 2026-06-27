"""
Validación de RUT chileno (algoritmo módulo 11).

El RUT/RUN chileno usa el algoritmo de "módulo 11" para calcular su dígito
verificador (DV). Este algoritmo es estable y sigue vigente al 2026: NO ha
cambiado, lo único que evoluciona es el rango de números asignados por el
Registro Civil. Por eso la validación correcta es **algorítmica** (verificar
que el DV calculado coincida con el ingresado), no por listas.

Uso en formularios:
    from .validators import validar_rut, formatear_rut

    def clean_rut(self):
        return formatear_rut(self.cleaned_data.get("rut"))
"""
import re

from django.core.exceptions import ValidationError


def _limpiar(rut):
    """Deja solo dígitos y el DV (K mayúscula), sin puntos ni guion."""
    return re.sub(r"[^0-9kK]", "", str(rut or "")).upper()


def calcular_dv(cuerpo):
    """Calcula el dígito verificador (módulo 11) para el cuerpo numérico."""
    suma = 0
    multiplicador = 2
    for digito in reversed(str(cuerpo)):
        suma += int(digito) * multiplicador
        multiplicador = 2 if multiplicador == 7 else multiplicador + 1
    resto = 11 - (suma % 11)
    if resto == 11:
        return "0"
    if resto == 10:
        return "K"
    return str(resto)


def validar_rut(rut):
    """
    Valida un RUT chileno por módulo 11.

    Lanza ValidationError si el formato o el dígito verificador es inválido.
    Devuelve la tupla (cuerpo:int, dv:str) si es válido.
    """
    limpio = _limpiar(rut)
    if len(limpio) < 2:
        raise ValidationError("El RUT está incompleto.")

    cuerpo, dv = limpio[:-1], limpio[-1]
    if not cuerpo.isdigit():
        raise ValidationError("El RUT solo puede contener números y el dígito verificador.")

    numero = int(cuerpo)
    # Rango razonable para personas/empresas chilenas (evita ceros o gigantes).
    if not (1_000_000 <= numero <= 99_999_999):
        raise ValidationError("El RUT está fuera de un rango válido.")

    if dv != calcular_dv(numero):
        raise ValidationError("El dígito verificador del RUT no es correcto.")

    return numero, dv


def formatear_rut(rut):
    """
    Valida y devuelve el RUT con formato canónico chileno: 12.345.678-9.

    Si el valor viene vacío, devuelve cadena vacía (los RUT son opcionales en
    varios modelos). Si es inválido, propaga ValidationError.
    """
    if not str(rut or "").strip():
        return ""
    numero, dv = validar_rut(rut)
    cuerpo = f"{numero:,}".replace(",", ".")
    return f"{cuerpo}-{dv}"
