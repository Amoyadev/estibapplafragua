"""URLs raiz de Estiba."""
from django.contrib import admin
from django.urls import include, path

from apps.core import views as core_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", core_views.HomeLoginView.as_view(), name="login"),
    path("logout/", core_views.cerrar_sesion, name="logout"),
    path("", include("apps.core.urls")),
    path("app/", include("apps.operaciones.urls")),
    path("app/flota/", include("apps.flota.urls")),
    path("correos/", include("apps.comunicaciones.urls")),
]

admin.site.site_header = "Estibapp -- Administracion"
admin.site.site_title = "Estibapp"
admin.site.index_title = "Panel de gestion portuaria"
