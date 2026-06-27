"""URLs de la app de comunicaciones."""
from django.urls import path

from . import views

app_name = "comunicaciones"

urlpatterns = [
    path("", views.bandeja_correos, name="bandeja"),
    path("sincronizar/", views.sincronizar_correos, name="sincronizar"),
    path("<int:pk>/marcar/", views.marcar_correo, name="marcar"),
    path("<int:pk>/ver/", views.ver_correo, name="ver"),
    path("<int:pk>/crear-eta/", views.crear_eta_desde_correo, name="crear_eta"),
]
