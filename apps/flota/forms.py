"""Formularios de la app Flota (Tracto + SemiRemolque)."""
from django import forms

from .models import SemiRemolque, Tracto


class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "form-check-input")
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                widget.attrs.setdefault("class", "form-select")
            else:
                widget.attrs.setdefault("class", "form-control")


class TractoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Tracto
        fields = [
            "patente", "marca", "modelo", "anio", "vin", "motor",
            "kilometraje", "horometro", "odometro",
            "vencimiento_seguro", "vencimiento_permiso", "vencimiento_revision",
            "estado",
        ]
        widgets = {
            "vencimiento_seguro":   forms.DateInput(attrs={"type": "date"}),
            "vencimiento_permiso":  forms.DateInput(attrs={"type": "date"}),
            "vencimiento_revision": forms.DateInput(attrs={"type": "date"}),
        }


class SemiRemolqueForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = SemiRemolque
        fields = ["patente", "tipo", "estado"]
