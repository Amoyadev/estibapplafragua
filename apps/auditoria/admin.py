"""Admin de solo lectura para la bitácora de auditoría."""
from django.contrib import admin

from .models import RegistroAuditoria


@admin.register(RegistroAuditoria)
class RegistroAuditoriaAdmin(admin.ModelAdmin):
    list_display = ("fecha", "usuario_nombre", "accion", "modelo", "objeto_repr", "ip")
    list_filter = ("accion", "modelo", "fecha")
    search_fields = ("usuario_nombre", "objeto_repr", "objeto_id", "ip", "ruta")
    date_hierarchy = "fecha"
    readonly_fields = (
        "fecha",
        "usuario",
        "usuario_nombre",
        "accion",
        "modelo",
        "objeto_id",
        "objeto_repr",
        "cambios",
        "ip",
        "ruta",
    )

    # La bitácora es inmutable: no se crea, edita ni borra desde el admin.
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
