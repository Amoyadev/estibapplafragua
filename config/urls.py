"""URLs raíz de Estiba."""
from django.contrib import admin
from django.urls import include, path

from apps.core import views as core_views

urlpatterns = [
    path("admin/", admin.site.urls),
    # El acceso (login) vive dentro de la home: ambas rutas renderizan la
    # misma landing con el formulario. No hay pantalla de login separada.
    path("login/", core_views.HomeLoginView.as_view(), name="login"),
    path("logout/", core_views.cerrar_sesion, name="logout"),
    path("", include("apps.core.urls")),
    path("app/", include("apps.operaciones.urls")),
]

admin.site.site_header = "Estibapp — Administración"
admin.site.site_title = "Estibapp"
admin.site.index_title = "Panel de gestión portuaria"
