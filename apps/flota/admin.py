from django.contrib import admin

from .models import SemiRemolque, Tracto


@admin.register(Tracto)
class TractoAdmin(admin.ModelAdmin):
    list_display = (
        "patente", "marca", "modelo", "anio", "estado",
        "vencimiento_seguro", "vencimiento_permiso", "vencimiento_revision",
    )
    list_filter = ("estado", "marca")
    search_fields = ("patente", "vin", "motor")
    fieldsets = (
        ("Identificación", {
            "fields": ("patente", "marca", "modelo", "anio", "vin", "motor"),
        }),
        ("Medidores", {
            "fields": ("kilometraje", "horometro", "odometro"),
        }),
        ("Vencimientos", {
            "fields": ("vencimiento_seguro", "vencimiento_permiso", "vencimiento_revision"),
        }),
        ("Estado", {
            "fields": ("estado",),
        }),
    )


@admin.register(SemiRemolque)
class SemiRemolqueAdmin(admin.ModelAdmin):
    list_display = ("patente", "tipo", "estado")
    list_filter = ("tipo", "estado")
    search_fields = ("patente",)
