from django.contrib import admin

from .models import (
    AgentePortuario,
    Camion,
    Cliente,
    Conductor,
    Contenedor,
    Empresa,
    ETA,
    Movimiento,
    RegistroConductor,
)


class MovimientoInline(admin.TabularInline):
    model = Movimiento
    extra = 0


@admin.register(AgentePortuario)
class AgentePortuarioAdmin(admin.ModelAdmin):
    list_display = ("nombre", "sigla", "activo")
    search_fields = ("nombre", "sigla")
    list_filter = ("activo",)


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nombre", "rut", "email", "activo")
    search_fields = ("nombre", "rut", "email")
    list_filter = ("activo",)


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "rut", "activo")
    search_fields = ("nombre", "rut")
    list_filter = ("activo",)


class RegistroConductorInline(admin.TabularInline):
    model = RegistroConductor
    extra = 0
    fields = ("tipo", "fecha", "descripcion", "valor")


@admin.register(Conductor)
class ConductorAdmin(admin.ModelAdmin):
    list_display = ("nombre", "empresa", "rut", "licencia",
                    "fecha_vencimiento_licencia", "telefono", "estado")
    search_fields = ("nombre", "rut", "empresa__nombre")
    list_filter = ("estado", "empresa")
    autocomplete_fields = ("empresa",)
    inlines = [RegistroConductorInline]


@admin.register(RegistroConductor)
class RegistroConductorAdmin(admin.ModelAdmin):
    list_display = ("conductor", "tipo", "fecha", "valor")
    list_filter = ("tipo", "fecha")
    search_fields = ("conductor__nombre",)


@admin.register(Camion)
class CamionAdmin(admin.ModelAdmin):
    list_display = ("patente", "marca")
    search_fields = ("patente",)


@admin.register(Contenedor)
class ContenedorAdmin(admin.ModelAdmin):
    list_display = ("codigo", "tipo", "estado")
    search_fields = ("codigo",)
    list_filter = ("tipo", "estado")


@admin.register(ETA)
class ETAAdmin(admin.ModelAdmin):
    list_display = (
        "numero",
        "cliente",
        "agente",
        "contenedor",
        "tipo_proceso",
        "estado",
        "fecha",
    )
    list_filter = ("estado", "tipo_proceso", "agente", "fecha")
    search_fields = ("numero", "cliente__nombre", "contenedor__codigo")
    autocomplete_fields = ("cliente", "agente", "contenedor", "conductor", "camion")
    inlines = [MovimientoInline]
    date_hierarchy = "fecha"


@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):
    list_display = ("eta", "tipo", "fecha", "empresa_responsable")
    list_filter = ("tipo", "fecha", "empresa_responsable")
    search_fields = ("eta__numero", "empresa_responsable__nombre")
