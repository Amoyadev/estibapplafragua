"""Formularios de Estibapp con estilos Bootstrap automáticos."""
import re

from django import forms
from django.utils import timezone

from .models import (
    AgentePortuario,
    Camion,
    Cliente,
    Conductor,
    Contenedor,
    Empresa,
    ETA,
    Movimiento,
)
from .validators import formatear_rut


class BootstrapFormMixin:
    """Agrega clases Bootstrap a todos los campos automáticamente."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, (forms.CheckboxInput,)):
                widget.attrs.setdefault("class", "form-check-input")
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                widget.attrs.setdefault("class", "form-select")
            else:
                widget.attrs.setdefault("class", "form-control")


class ClienteForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ["nombre", "rut", "email", "telefono", "activo"]

    def clean_rut(self):
        # RUT opcional: si viene, se valida por módulo 11 y se normaliza.
        return formatear_rut(self.cleaned_data.get("rut"))


class EmpresaForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Empresa
        fields = ["nombre", "rut", "activo"]

    def clean_rut(self):
        return formatear_rut(self.cleaned_data.get("rut"))


class ConductorForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Conductor
        fields = ["nombre", "empresa", "rut", "telefono"]

    def clean_rut(self):
        return formatear_rut(self.cleaned_data.get("rut"))


class CamionForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Camion
        fields = ["patente", "marca"]


class AgentePortuarioForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = AgentePortuario
        fields = ["nombre", "sigla", "activo"]


class ContenedorForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Contenedor
        fields = ["codigo", "tipo", "estado"]


class ETAForm(BootstrapFormMixin, forms.ModelForm):
    """
    Alta/edición de ETA con los datos reales de la operación
    (mismas columnas que las planillas Retiro/Entregas).

    Los campos internos `fecha`, `hora_retiro`, `deposito` y `puerto` se
    derivan automáticamente en `save()` a partir de los datos operativos,
    para no pedir información duplicada al usuario.
    """

    class Meta:
        model = ETA
        fields = [
            # --- Identificación ---
            "numero",
            "cliente",
            "contenedor",
            "agente",
            # --- Datos de la operación ---
            "operacion",
            "despacho",
            "nave",
            "dimension",
            "peso",
            # --- Asignación de transporte ---
            "conductor",
            "camion",
            # --- Retiro (puerto) ---
            "fecha_retiro",
            "horario",
            "estado_retiro",
            # --- Entrega / devolución ---
            "fecha_entrega",
            "direccion_entrega",
            "deposito_devolucion",
            "estado_entrega",
            "otd",
            # --- Trazabilidad ---
            "tipo_proceso",
            "observaciones",
        ]
        widgets = {
            "fecha_retiro": forms.DateInput(attrs={"type": "date"}),
            "fecha_entrega": forms.DateInput(attrs={"type": "date"}),
            "horario": forms.TimeInput(attrs={"type": "time"}),
            "direccion_entrega": forms.TextInput(),
            "observaciones": forms.Textarea(attrs={"rows": 2}),
        }
        labels = {
            "agente": "Puerto / terminal de origen",
            "deposito_devolucion": "Depósito de devolución (vacío)",
        }

    # --- Validaciones de entrada (consideración MVP 1) ---
    # Estas reglas evitan datos sucios que después ensucian los informes.
    def clean_numero(self):
        """N° ETA: solo letras mayúsculas, números y guiones (ej. ETA-2026-0001)."""
        numero = (self.cleaned_data.get("numero") or "").strip().upper()
        if not re.fullmatch(r"[A-Z0-9\-]{3,30}", numero):
            raise forms.ValidationError(
                "El N° ETA solo admite letras, números y guiones (3 a 30 caracteres)."
            )
        return numero

    def save(self, commit=True):
        """Deriva los campos internos a partir de los datos operativos reales."""
        eta = super().save(commit=False)
        cd = self.cleaned_data
        # `fecha` es obligatoria en el modelo: se toma del retiro o la entrega.
        eta.fecha = cd.get("fecha_retiro") or cd.get("fecha_entrega") or timezone.now().date()
        eta.hora_retiro = cd.get("horario")
        # Espejo para mantener vivos los reportes que usan `deposito`/`puerto`.
        if cd.get("deposito_devolucion"):
            eta.deposito = cd["deposito_devolucion"][:120]
        if eta.agente_id:
            eta.puerto = eta.agente.nombre[:40]
        if commit:
            eta.save()
        return eta



class MovimientoManualForm(BootstrapFormMixin, forms.ModelForm):
    """Permite registrar un movimiento manual sobre una ETA."""

    class Meta:
        model = Movimiento
        fields = ["tipo", "fecha", "empresa_responsable", "observacion"]
        widgets = {
            "fecha": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "observacion": forms.Textarea(attrs={"rows": 2}),
        }


class PatioUbicacionForm(BootstrapFormMixin, forms.ModelForm):
    """Formulario breve para que el jefe de patio registre la ubicación física."""

    class Meta:
        model = ETA
        fields = ["ubicacion"]
        widgets = {
            "ubicacion": forms.TextInput(
                attrs={"placeholder": "Ej. Calle B · Piso 2 · Nivel 1"}
            ),
        }
