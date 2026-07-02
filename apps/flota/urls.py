"""URLs de la app Flota."""
from django.urls import path

from . import views

app_name = "flota"

urlpatterns = [
    # Tractos
    path("tractos/",                       views.TractoList.as_view(),   name="tracto_list"),
    path("tractos/nuevo/",                 views.TractoCreate.as_view(), name="tracto_crear"),
    path("tractos/<int:pk>/editar/",       views.TractoUpdate.as_view(), name="tracto_editar"),
    path("tractos/<int:pk>/eliminar/",     views.TractoDelete.as_view(), name="tracto_eliminar"),

    # Semirremolques
    path("semiremolques/",                 views.SemiRemolqueList.as_view(),   name="semiremolque_list"),
    path("semiremolques/nuevo/",           views.SemiRemolqueCreate.as_view(), name="semiremolque_crear"),
    path("semiremolques/<int:pk>/editar/", views.SemiRemolqueUpdate.as_view(), name="semiremolque_editar"),
    path("semiremolques/<int:pk>/eliminar/", views.SemiRemolqueDelete.as_view(), name="semiremolque_eliminar"),
]
