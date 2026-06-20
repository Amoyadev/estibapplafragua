"""URLs de la app de operaciones de Estibapp."""
from django.urls import path

from . import views

app_name = "operaciones"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),

    # --- Catálogos (Sprint 1) ---
    path("clientes/", views.ClienteList.as_view(), name="cliente_list"),
    path("clientes/nuevo/", views.ClienteCreate.as_view(), name="cliente_crear"),
    path("clientes/<int:pk>/editar/", views.ClienteUpdate.as_view(), name="cliente_editar"),
    path("clientes/<int:pk>/eliminar/", views.ClienteDelete.as_view(), name="cliente_eliminar"),

    path("conductores/", views.ConductorList.as_view(), name="conductor_list"),
    path("conductores/nuevo/", views.ConductorCreate.as_view(), name="conductor_crear"),
    path("conductores/<int:pk>/editar/", views.ConductorUpdate.as_view(), name="conductor_editar"),
    path("conductores/<int:pk>/eliminar/", views.ConductorDelete.as_view(), name="conductor_eliminar"),

    path("empresas/", views.EmpresaList.as_view(), name="empresa_list"),
    path("empresas/nueva/", views.EmpresaCreate.as_view(), name="empresa_crear"),
    path("empresas/<int:pk>/editar/", views.EmpresaUpdate.as_view(), name="empresa_editar"),
    path("empresas/<int:pk>/eliminar/", views.EmpresaDelete.as_view(), name="empresa_eliminar"),

    path("camiones/", views.CamionList.as_view(), name="camion_list"),
    path("camiones/nuevo/", views.CamionCreate.as_view(), name="camion_crear"),
    path("camiones/<int:pk>/editar/", views.CamionUpdate.as_view(), name="camion_editar"),
    path("camiones/<int:pk>/eliminar/", views.CamionDelete.as_view(), name="camion_eliminar"),

    path("agentes/", views.AgenteList.as_view(), name="agente_list"),
    path("agentes/nuevo/", views.AgenteCreate.as_view(), name="agente_crear"),
    path("agentes/<int:pk>/editar/", views.AgenteUpdate.as_view(), name="agente_editar"),
    path("agentes/<int:pk>/eliminar/", views.AgenteDelete.as_view(), name="agente_eliminar"),

    path("contenedores/", views.ContenedorList.as_view(), name="contenedor_list"),
    path("contenedores/nuevo/", views.ContenedorCreate.as_view(), name="contenedor_crear"),
    path("contenedores/<int:pk>/editar/", views.ContenedorUpdate.as_view(), name="contenedor_editar"),
    path("contenedores/<int:pk>/eliminar/", views.ContenedorDelete.as_view(), name="contenedor_eliminar"),

    # --- ETA y flujo (Sprint 2) ---
    path("etas/", views.ETAList.as_view(), name="eta_list"),
    path("etas/nueva/", views.ETACreate.as_view(), name="eta_crear"),
    path("etas/<int:pk>/", views.ETADetail.as_view(), name="eta_detalle"),
    path("etas/<int:pk>/editar/", views.ETAUpdate.as_view(), name="eta_editar"),
    path("etas/<int:pk>/avanzar/", views.eta_avanzar, name="eta_avanzar"),
    path("etas/<int:pk>/estado/", views.eta_cambiar_estado, name="eta_cambiar_estado"),
    path("etas/<int:pk>/ubicacion/", views.patio_ubicacion, name="eta_ubicacion"),
    path("etas/<int:pk>/movimiento/", views.eta_movimiento_manual, name="eta_movimiento"),

    # --- Pantallas por perfil (Sprint 3) ---
    path("bandeja/", views.BandejaCoordinador.as_view(), name="bandeja"),
    path("patio/", views.TableroPatio.as_view(), name="patio"),
    path("tablero/", views.TableroOperativo.as_view(), name="tablero"),
    path("buscar/", views.ContenedorBuscar.as_view(), name="contenedor_buscar"),

    # --- Trazabilidad y reportes (Sprint 4) ---
    path("recuentos/", views.Recuentos.as_view(), name="recuentos"),
    path("reportes/", views.Reportes.as_view(), name="reportes"),
    path("reportes/cliente/<int:pk>/", views.ReporteCliente.as_view(), name="reporte_cliente"),
    path("reportes/<str:tipo>.csv", views.exportar_csv, name="exportar_csv"),
]
