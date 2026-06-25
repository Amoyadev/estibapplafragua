"""Vistas de Estibapp (Sprints 1-4)."""
import csv
from collections import defaultdict

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.db.models import Count, Q
from django.db.models.functions import TruncDate, TruncMonth
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from .forms import (
    AgentePortuarioForm,
    CamionForm,
    ClienteForm,
    ConductorForm,
    ContenedorForm,
    EmpresaForm,
    ETAForm,
    MovimientoManualForm,
    PatioUbicacionForm,
)
from .models import (
    AgentePortuario,
    Camion,
    Cliente,
    Conductor,
    Contenedor,
    Empresa,
    ESTADOS_CIERRE,
    ESTADOS_EN_DEPOSITO,
    ESTADOS_EN_PUERTO,
    ETA,
    FLUJO_ETA,
    FLUJO_PASOS,
    Movimiento,
)
from .permissions import (
    AdminOCoordinador,
    AdminOPatio,
    CualquierRol,
    SoloAdmin,
    ROL_ADMIN,
    ROL_COORDINADOR,
    ROL_PATIO,
    en_grupos,
)


# ============================================================
# Dashboard (router por rol)
# ============================================================
class DashboardView(CualquierRol, ListView):
    model = ETA
    template_name = "operaciones/dashboard.html"
    context_object_name = "etas_recientes"

    def get_queryset(self):
        return ETA.objects.select_related("cliente", "contenedor")[:8]

    def get_context_data(self, **kwargs):
        from datetime import timedelta
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        ctx["es_admin"] = en_grupos(user, [ROL_ADMIN])
        ctx["es_coordinador"] = en_grupos(user, [ROL_COORDINADOR])
        ctx["es_patio"] = en_grupos(user, [ROL_PATIO])
        ctx["total_etas"] = ETA.objects.count()
        ctx["abiertas"] = ETA.objects.exclude(
            estado=ETA.EstadoCiclo.DESPACHADO_PUERTO
        ).count()
        ctx["en_deposito"] = ETA.objects.filter(
            estado__in=ESTADOS_EN_DEPOSITO
        ).count()

        # ── Period filter ─────────────────────────────────────
        hoy = timezone.now().date()
        periodo = self.request.GET.get("periodo", "mes")
        deltas = {"semana": 7, "mes": 30, "trimestre": 90, "anual": 365}
        dias = deltas.get(periodo, 30)
        desde = hoy - timedelta(days=dias)

        etas_periodo = ETA.objects.filter(fecha__gte=desde)

        actividad = (
            ETA.objects.filter(fecha__gte=desde)
            .annotate(dia=TruncDate("fecha"))
            .values("dia")
            .annotate(total=Count("pk"))
            .order_by("dia")
        )
        por_estado = (
            etas_periodo
            .values("estado")
            .annotate(total=Count("pk"))
            .order_by("-total")
        )
        labels_estado = [
            dict(ETA.EstadoCiclo.choices).get(r["estado"], r["estado"])
            for r in por_estado
        ]
        ctx["periodo"] = periodo
        ctx["periodos"] = [
            ("semana", "Esta semana"),
            ("mes", "Este mes"),
            ("trimestre", "Trimestre"),
            ("anual", "Año"),
        ]
        ctx["graf_actividad"] = {
            "labels": [str(r["dia"]) for r in actividad],
            "data": [r["total"] for r in actividad],
        }
        ctx["graf_estados"] = {
            "labels": labels_estado,
            "data": [r["total"] for r in por_estado],
        }
        ctx["etas_periodo_count"] = etas_periodo.count()
        return ctx


# ============================================================
# CRUD genérico de catálogos (Sprint 1)
# ============================================================
class BaseCatalogoList(AdminOCoordinador, ListView):
    template_name = "operaciones/catalogo_lista.html"
    columnas: list = []
    titulo = ""
    crear_url = ""
    editar_url = ""
    eliminar_url = ""

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            titulo=self.titulo,
            columnas=self.columnas,
            crear_url=self.crear_url,
            editar_url=self.editar_url,
            eliminar_url=self.eliminar_url,
        )
        return ctx


class BaseCatalogoCreate(AdminOCoordinador, CreateView):
    template_name = "operaciones/catalogo_form.html"
    titulo = ""

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titulo"] = self.titulo
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Registro creado correctamente.")
        return super().form_valid(form)


class BaseCatalogoUpdate(AdminOCoordinador, UpdateView):
    template_name = "operaciones/catalogo_form.html"
    titulo = ""

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titulo"] = self.titulo
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Registro actualizado correctamente.")
        return super().form_valid(form)


class BaseCatalogoDelete(AdminOCoordinador, DeleteView):
    template_name = "operaciones/catalogo_confirmar_eliminar.html"

    def form_valid(self, form):
        messages.success(self.request, "Registro eliminado.")
        return super().form_valid(form)


# ---- Cliente ----
class ClienteList(BaseCatalogoList):
    model = Cliente
    titulo = "Clientes"
    crear_url = "operaciones:cliente_crear"
    editar_url = "operaciones:cliente_editar"
    eliminar_url = "operaciones:cliente_eliminar"
    columnas = [("Nombre", "nombre"), ("RUT", "rut"), ("Email", "email"), ("Activo", "activo")]


class ClienteCreate(BaseCatalogoCreate):
    model = Cliente
    form_class = ClienteForm
    titulo = "Nuevo cliente"
    success_url = reverse_lazy("operaciones:cliente_list")


class ClienteUpdate(BaseCatalogoUpdate):
    model = Cliente
    form_class = ClienteForm
    titulo = "Editar cliente"
    success_url = reverse_lazy("operaciones:cliente_list")


class ClienteDelete(BaseCatalogoDelete):
    model = Cliente
    success_url = reverse_lazy("operaciones:cliente_list")


# ---- Conductor ----
class ConductorList(BaseCatalogoList):
    model = Conductor
    titulo = "Conductores"
    crear_url = "operaciones:conductor_crear"
    editar_url = "operaciones:conductor_editar"
    eliminar_url = "operaciones:conductor_eliminar"
    columnas = [("Nombre", "nombre"), ("Empresa", "empresa"), ("RUT", "rut"), ("Teléfono", "telefono")]

    def get_queryset(self):
        return Conductor.objects.select_related("empresa")


class ConductorCreate(BaseCatalogoCreate):
    model = Conductor
    form_class = ConductorForm
    titulo = "Nuevo conductor"
    success_url = reverse_lazy("operaciones:conductor_list")


class ConductorUpdate(BaseCatalogoUpdate):
    model = Conductor
    form_class = ConductorForm
    titulo = "Editar conductor"
    success_url = reverse_lazy("operaciones:conductor_list")


class ConductorDelete(BaseCatalogoDelete):
    model = Conductor
    success_url = reverse_lazy("operaciones:conductor_list")


# ---- Empresa (transporte / responsable) ----
class EmpresaList(BaseCatalogoList):
    model = Empresa
    titulo = "Empresas"
    crear_url = "operaciones:empresa_crear"
    editar_url = "operaciones:empresa_editar"
    eliminar_url = "operaciones:empresa_eliminar"
    columnas = [("Nombre", "nombre"), ("RUT", "rut"), ("Activo", "activo")]


class EmpresaCreate(BaseCatalogoCreate):
    model = Empresa
    form_class = EmpresaForm
    titulo = "Nueva empresa"
    success_url = reverse_lazy("operaciones:empresa_list")


class EmpresaUpdate(BaseCatalogoUpdate):
    model = Empresa
    form_class = EmpresaForm
    titulo = "Editar empresa"
    success_url = reverse_lazy("operaciones:empresa_list")


class EmpresaDelete(BaseCatalogoDelete):
    model = Empresa
    success_url = reverse_lazy("operaciones:empresa_list")


# ---- Camión ----
class CamionList(BaseCatalogoList):
    model = Camion
    titulo = "Camiones"
    crear_url = "operaciones:camion_crear"
    editar_url = "operaciones:camion_editar"
    eliminar_url = "operaciones:camion_eliminar"
    columnas = [("Patente", "patente"), ("Marca", "marca")]


class CamionCreate(BaseCatalogoCreate):
    model = Camion
    form_class = CamionForm
    titulo = "Nuevo camión"
    success_url = reverse_lazy("operaciones:camion_list")


class CamionUpdate(BaseCatalogoUpdate):
    model = Camion
    form_class = CamionForm
    titulo = "Editar camión"
    success_url = reverse_lazy("operaciones:camion_list")


class CamionDelete(BaseCatalogoDelete):
    model = Camion
    success_url = reverse_lazy("operaciones:camion_list")


# ---- Agente portuario ----
class AgenteList(BaseCatalogoList):
    model = AgentePortuario
    titulo = "Agentes portuarios"
    crear_url = "operaciones:agente_crear"
    editar_url = "operaciones:agente_editar"
    eliminar_url = "operaciones:agente_eliminar"
    columnas = [("Nombre", "nombre"), ("Sigla", "sigla"), ("Activo", "activo")]


class AgenteCreate(BaseCatalogoCreate):
    model = AgentePortuario
    form_class = AgentePortuarioForm
    titulo = "Nuevo agente portuario"
    success_url = reverse_lazy("operaciones:agente_list")


class AgenteUpdate(BaseCatalogoUpdate):
    model = AgentePortuario
    form_class = AgentePortuarioForm
    titulo = "Editar agente portuario"
    success_url = reverse_lazy("operaciones:agente_list")


class AgenteDelete(BaseCatalogoDelete):
    model = AgentePortuario
    success_url = reverse_lazy("operaciones:agente_list")


# ---- Contenedor ----
class ContenedorList(BaseCatalogoList):
    model = Contenedor
    titulo = "Contenedores"
    crear_url = "operaciones:contenedor_crear"
    editar_url = "operaciones:contenedor_editar"
    eliminar_url = "operaciones:contenedor_eliminar"
    columnas = [("Código", "codigo"), ("Tipo", "get_tipo_display"), ("Estado", "get_estado_display")]


class ContenedorCreate(BaseCatalogoCreate):
    model = Contenedor
    form_class = ContenedorForm
    titulo = "Nuevo contenedor"
    success_url = reverse_lazy("operaciones:contenedor_list")


class ContenedorUpdate(BaseCatalogoUpdate):
    model = Contenedor
    form_class = ContenedorForm
    titulo = "Editar contenedor"
    success_url = reverse_lazy("operaciones:contenedor_list")


class ContenedorDelete(BaseCatalogoDelete):
    model = Contenedor
    success_url = reverse_lazy("operaciones:contenedor_list")


# ============================================================
# ETA: registro y flujo (Sprint 2)
# ============================================================
def _notificar_cliente(eta, estado):
    """Envía un aviso al cliente (email a consola en MVP). No bloquea si falla."""
    if not eta.cliente.email:
        return
    try:
        send_mail(
            subject=f"[Estibapp] ETA {eta.numero} → {eta.get_estado_display()}",
            message=(
                f"Estimado/a {eta.cliente.nombre},\n\n"
                f"Su solicitud (ETA {eta.numero}) cambió al estado: "
                f"{eta.get_estado_display()}.\n\n"
                f"Contenedor: {eta.contenedor.codigo}\n"
                f"Saludos,\nEstibapp"
            ),
            from_email=None,
            recipient_list=[eta.cliente.email],
            fail_silently=True,
        )
    except Exception:  # noqa: BLE001 - el aviso nunca debe romper la operación
        pass


def _avanzar_eta(eta, usuario):
    """Avanza la ETA al siguiente paso del ciclo y registra su movimiento.

    El avance se calcula sobre FLUJO_PASOS (no sobre estados únicos) para
    soportar el retorno del cliente al depósito antes del cierre final.
    """
    idx = eta.paso_actual_idx()
    if idx == -1 or idx + 1 >= len(FLUJO_PASOS):
        return None
    paso = FLUJO_PASOS[idx + 1]
    eta.estado = paso["estado"]
    eta.save(update_fields=["estado", "actualizado"])

    tipo_mov = paso["mov"]
    if tipo_mov:
        empresa = (
            eta.conductor.empresa
            if eta.conductor and eta.conductor.empresa
            else None
        )
        Movimiento.objects.create(
            eta=eta,
            tipo=tipo_mov,
            fecha=timezone.now(),
            empresa_responsable=empresa,
            observacion="Avance automático del ciclo.",
        )
    _notificar_cliente(eta, eta.estado)
    return eta.estado


class ETAList(CualquierRol, ListView):
    """Vista máster: todas las ETAs con filtros (Administrador y roles)."""

    model = ETA
    template_name = "operaciones/eta_lista.html"
    context_object_name = "etas"
    paginate_by = 25

    def get_queryset(self):
        qs = ETA.objects.select_related("cliente", "agente", "contenedor")
        estado = self.request.GET.get("estado")
        buscar = self.request.GET.get("q")
        if estado:
            qs = qs.filter(estado=estado)
        if buscar:
            qs = qs.filter(
                Q(numero__icontains=buscar)
                | Q(cliente__nombre__icontains=buscar)
                | Q(contenedor__codigo__icontains=buscar)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["estados"] = ETA.EstadoCiclo.choices
        ctx["estado_sel"] = self.request.GET.get("estado", "")
        ctx["q"] = self.request.GET.get("q", "")
        return ctx


class ETADetail(CualquierRol, DetailView):
    model = ETA
    template_name = "operaciones/eta_detalle.html"
    context_object_name = "eta"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["movimientos"] = self.object.movimientos.select_related(
            "empresa_responsable"
        ).all()
        ctx["estado_siguiente"] = self.object.estado_siguiente()
        ctx["mov_form"] = MovimientoManualForm()
        ctx["ubicacion_form"] = PatioUbicacionForm(instance=self.object)
        # Pasos del ciclo en formato "tipo Jira": indica cuáles ya se
        # recorrieron, el actual y los que quedan por delante (clicables).
        actual_idx = self.object.paso_actual_idx()
        estados_flujo = []
        for idx, paso in enumerate(FLUJO_PASOS):
            estados_flujo.append(
                {
                    "idx": idx,
                    "valor": paso["estado"],
                    "label": paso["label"],
                    "pasado": idx < actual_idx,
                    "actual": idx == actual_idx,
                    "futuro": idx > actual_idx,
                }
            )
        ctx["estados_flujo"] = estados_flujo
        # Para el stepper visual y el bloque camión/conductor en movimiento manual
        ctx["flujo_pasos"] = FLUJO_PASOS
        ctx["camiones"] = Camion.objects.all().order_by("patente")
        ctx["conductores"] = Conductor.objects.filter(
            estado=Conductor.Estado.ACTIVO
        ).select_related("empresa").order_by("nombre")
        # Siguiente paso en el flujo para el formulario unificado
        sig_idx = actual_idx + 1
        if sig_idx < len(FLUJO_PASOS):
            ctx["siguiente_paso_idx"] = sig_idx
            ctx["siguiente_paso_label"] = FLUJO_PASOS[sig_idx]["label"]
            ctx["siguiente_es_retiro"] = (
                FLUJO_PASOS[sig_idx].get("mov") == Movimiento.Tipo.RETIRO
            )
        else:
            ctx["siguiente_paso_idx"] = None
            ctx["siguiente_paso_label"] = None
            ctx["siguiente_es_retiro"] = False
        # Último movimiento para mostrarlo en el card
        ctx["ultimo_movimiento"] = self.object.movimientos.first()
        # Todos los pasos futuros (para el selector de estado en el form)
        ctx["pasos_futuros"] = [
            {
                "idx": p["idx"],
                "label": p["label"],
                "es_retiro": FLUJO_PASOS[p["idx"]].get("mov") == Movimiento.Tipo.RETIRO,
            }
            for p in estados_flujo
            if p["futuro"]
        ]
        return ctx


class ETACreate(AdminOCoordinador, CreateView):
    model = ETA
    form_class = ETAForm
    template_name = "operaciones/eta_form.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titulo"] = "Nueva ETA"
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "ETA creada en estado SOLICITADO.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("operaciones:eta_detalle", args=[self.object.pk])


class ETAUpdate(AdminOCoordinador, UpdateView):
    model = ETA
    form_class = ETAForm
    template_name = "operaciones/eta_form.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titulo"] = f"Editar ETA {self.object.numero}"
        return ctx

    def get_success_url(self):
        return reverse_lazy("operaciones:eta_detalle", args=[self.object.pk])


def eta_avanzar(request, pk):
    """Avanza una ETA al siguiente estado (Admin, Coordinador o Patio)."""
    if not en_grupos(request.user, [ROL_ADMIN, ROL_COORDINADOR, ROL_PATIO]):
        return redirect("login")
    eta = get_object_or_404(ETA, pk=pk)
    if request.method == "POST":
        nuevo = _avanzar_eta(eta, request.user)
        if nuevo:
            messages.success(request, f"ETA avanzada a {eta.get_estado_display()}.")
        else:
            messages.info(request, "La ETA ya está en el último estado del ciclo.")
    return redirect("operaciones:eta_detalle", pk=pk)


def eta_movimiento_manual(request, pk):
    """Registra un movimiento y avanza la ETA al siguiente paso del ciclo.

    Campos obligatorios: siguiente_paso_idx, tipo_contenedor, fecha, observacion.
    Para RETIRO (Ida a puerto) también son obligatorios camion_mov y conductor_mov.
    """
    if not en_grupos(request.user, [ROL_ADMIN, ROL_COORDINADOR, ROL_PATIO]):
        return redirect("login")
    eta = get_object_or_404(ETA, pk=pk)
    if request.method != "POST":
        return redirect("operaciones:eta_detalle", pk=pk)

    from django.utils.dateparse import parse_datetime

    siguiente_idx_raw = request.POST.get("siguiente_paso_idx", "").strip()
    tipo_contenedor   = request.POST.get("tipo_contenedor", "").strip()
    fecha_str         = request.POST.get("fecha", "").strip()
    observacion       = request.POST.get("observacion", "").strip()

    errores = []
    if not siguiente_idx_raw:
        errores.append("Paso de destino no especificado.")
    if not tipo_contenedor:
        errores.append("Debes indicar el estado del contenedor (vacío / con carga).")
    if not fecha_str:
        errores.append("La fecha es obligatoria.")
    if not observacion:
        errores.append("La observación es obligatoria.")
    for e in errores:
        messages.error(request, e)
    if errores:
        return redirect("operaciones:eta_detalle", pk=pk)

    try:
        siguiente_idx = int(siguiente_idx_raw)
    except ValueError:
        messages.error(request, "Paso no válido.")
        return redirect("operaciones:eta_detalle", pk=pk)

    if not 0 <= siguiente_idx < len(FLUJO_PASOS):
        messages.error(request, "Paso fuera del flujo.")
        return redirect("operaciones:eta_detalle", pk=pk)

    fecha = parse_datetime(fecha_str)
    if not fecha:
        messages.error(request, "Formato de fecha no válido.")
        return redirect("operaciones:eta_detalle", pk=pk)

    paso_destino = FLUJO_PASOS[siguiente_idx]
    tipo_mov     = paso_destino.get("mov")

    if tipo_mov == Movimiento.Tipo.RETIRO:
        camion_id    = request.POST.get("camion_mov", "").strip()
        conductor_id = request.POST.get("conductor_mov", "").strip()
        if not camion_id or not conductor_id:
            messages.error(request, "Para Ida a puerto debes asignar camión y conductor.")
            return redirect("operaciones:eta_detalle", pk=pk)
        try:
            eta.camion    = Camion.objects.get(pk=camion_id)
            eta.conductor = Conductor.objects.get(pk=conductor_id)
            eta.save(update_fields=["camion", "conductor", "actualizado"])
        except (Camion.DoesNotExist, Conductor.DoesNotExist):
            messages.error(request, "Camión o conductor no encontrado.")
            return redirect("operaciones:eta_detalle", pk=pk)

    contenedor = eta.contenedor
    if tipo_contenedor in dict(Contenedor.Estado.choices):
        contenedor.estado = tipo_contenedor
        contenedor.save(update_fields=["estado", "actualizado"])

    while eta.paso_actual_idx() < siguiente_idx:
        next_paso  = FLUJO_PASOS[eta.paso_actual_idx() + 1]
        eta.estado = next_paso["estado"]
        eta.save(update_fields=["estado", "actualizado"])

    empresa = (
        eta.conductor.empresa
        if eta.conductor and eta.conductor.empresa
        else None
    )
    if tipo_mov:
        fecha_aware = timezone.make_aware(fecha) if timezone.is_naive(fecha) else fecha
        Movimiento.objects.create(
            eta=eta,
            tipo=tipo_mov,
            fecha=fecha_aware,
            empresa_responsable=empresa,
            observacion=observacion,
        )

    _notificar_cliente(eta, eta.estado)
    messages.success(request, f"Movimiento registrado. ETA en «{eta.get_estado_display()}».")
    return redirect("operaciones:eta_detalle", pk=pk)


def eta_asignar_transporte(request, pk):
    """Actualiza camión y conductor de una ETA sin salir de la vista detalle."""
    if not en_grupos(request.user, [ROL_ADMIN, ROL_COORDINADOR]):
        return redirect("login")
    eta = get_object_or_404(ETA, pk=pk)
    if request.method == "POST":
        camion_id    = request.POST.get("camion_id", "").strip()
        conductor_id = request.POST.get("conductor_id", "").strip()
        eta.camion    = Camion.objects.filter(pk=camion_id).first() if camion_id else None
        eta.conductor = Conductor.objects.filter(pk=conductor_id).first() if conductor_id else None
        eta.save(update_fields=["camion", "conductor", "actualizado"])
        messages.success(request, "Transporte actualizado.")
    return redirect("operaciones:eta_detalle", pk=pk)


def eta_cambiar_estado(request, pk):
    """Mueve la ETA a un paso posterior del ciclo (selector tipo ticket Jira).

    Avanza paso a paso hasta el paso destino, generando los movimientos
    intermedios para no perder trazabilidad. Se trabaja con el índice de PASO
    (no con el estado) porque ALMACENADO se repite (inicial y retorno).
    """
    if not en_grupos(request.user, [ROL_ADMIN, ROL_COORDINADOR, ROL_PATIO]):
        return redirect("login")
    eta = get_object_or_404(ETA, pk=pk)
    if request.method == "POST":
        try:
            destino_idx = int(request.POST.get("paso", ""))
        except (TypeError, ValueError):
            messages.error(request, "Paso no válido.")
            return redirect("operaciones:eta_detalle", pk=pk)
        if not 0 <= destino_idx < len(FLUJO_PASOS):
            messages.error(request, "Paso fuera del flujo.")
            return redirect("operaciones:eta_detalle", pk=pk)
        if destino_idx <= eta.paso_actual_idx():
            messages.info(request, "Solo se puede mover a un paso posterior.")
            return redirect("operaciones:eta_detalle", pk=pk)
        while (
            eta.paso_actual_idx() < destino_idx
            and _avanzar_eta(eta, request.user) is not None
        ):
            pass
        messages.success(request, f"ETA movida a «{eta.get_estado_display()}».")
    return redirect("operaciones:eta_detalle", pk=pk)


def patio_ubicacion(request, pk):
    """El jefe de patio registra la ubicación física del contenedor."""
    if not en_grupos(request.user, [ROL_ADMIN, ROL_PATIO]):
        return redirect("login")
    eta = get_object_or_404(ETA, pk=pk)
    if request.method == "POST":
        form = PatioUbicacionForm(request.POST, instance=eta)
        if form.is_valid():
            form.save()
            messages.success(request, f"Ubicación registrada: {eta.ubicacion}.")
        else:
            messages.error(request, "Ubicación no válida.")
    destino = request.POST.get("next")
    if destino:
        return redirect(destino)
    return redirect("operaciones:eta_detalle", pk=pk)


# ============================================================
# Pantallas por perfil (Sprint 3)
# ============================================================
class BandejaCoordinador(AdminOCoordinador, ListView):
    """Solicitudes por asignar/gestionar para el Coordinador."""

    model = ETA
    template_name = "operaciones/bandeja.html"
    context_object_name = "etas"

    def get_queryset(self):
        return ETA.objects.filter(
            estado__in=[ETA.EstadoCiclo.SOLICITADO, ETA.EstadoCiclo.ASIGNADO]
        ).select_related("cliente", "contenedor")


class TableroPatio(AdminOPatio, ListView):
    """Contenedores en patio para el Encargado de Patio (foco en el contenedor)."""

    model = ETA
    template_name = "operaciones/patio.html"
    context_object_name = "etas"

    def get_queryset(self):
        return ETA.objects.filter(
            estado__in=[
                ETA.EstadoCiclo.ASIGNADO,
                ETA.EstadoCiclo.EN_PATIO,
                ETA.EstadoCiclo.ALMACENADO,
            ]
        ).select_related("cliente", "contenedor", "conductor", "camion")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["ubicacion_form"] = PatioUbicacionForm()
        return ctx


# ============================================================
# Buscador de contenedores (foco: jefe de patio)
# ------------------------------------------------------------
# Con solo escribir el N° de contenedor (o parte), el jefe de patio ve
# DÓNDE está físicamente (ubicación + estado del ciclo actual) y TODAS sus
# ETAs históricas relacionadas en el largo plazo (trazabilidad completa).
# ============================================================
class ContenedorBuscar(CualquierRol, TemplateView):
    template_name = "operaciones/buscar_contenedor.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        q = (self.request.GET.get("q") or "").strip()
        ctx["q"] = q
        if not q:
            return ctx

        contenedores = (
            Contenedor.objects.filter(
                Q(codigo__icontains=q)
                | Q(etas__cliente__nombre__icontains=q)
                | Q(etas__numero__icontains=q)
            )
            .distinct()
            .order_by("codigo")[:50]
        )

        resultados = []
        for c in contenedores:
            etas = list(
                c.etas.select_related("cliente", "agente", "conductor")
                .order_by("-fecha", "-creado")
            )
            resultados.append({
                "contenedor": c,
                "actual": etas[0] if etas else None,
                "etas": etas,
                "total": len(etas),
            })
        ctx["resultados"] = resultados
        ctx["sin_resultados"] = not resultados
        return ctx


# ============================================================
# Tablero operativo del día (emula el panel Power BI del cliente)
# ------------------------------------------------------------
# Cada operación del día es un RETIRO (sacar contenedor del puerto) o una
# ENTREGA (llevarlo al cliente). El N° de contenedor enlaza ambos hitos.
# La pantalla muestra recuentos por operación, estado de retiro, OTD de
# entrega, estado de conductores y clientes distintos, más el detalle.
# ============================================================
class TableroOperativo(CualquierRol, TemplateView):
    template_name = "operaciones/tablero.html"

    def _fechas_disponibles(self):
        fechas = set()
        fechas.update(
            ETA.objects.exclude(fecha_retiro=None).values_list("fecha_retiro", flat=True)
        )
        fechas.update(
            ETA.objects.exclude(fecha_entrega=None).values_list("fecha_entrega", flat=True)
        )
        # Fallback: ETAs sin fecha_retiro explícita usan su campo fecha
        fechas.update(
            ETA.objects.filter(fecha_retiro=None).values_list("fecha", flat=True)
        )
        return sorted((f for f in fechas if f is not None), reverse=True)[:60]

    def _fecha_por_defecto(self, disponibles):
        """Fecha con mayor cantidad de operaciones (retiros + entregas + fecha principal)."""
        if not disponibles:
            return None
        conteo = defaultdict(int)
        for d in ETA.objects.exclude(fecha_retiro=None).values_list("fecha_retiro", flat=True):
            conteo[d] += 1
        for d in ETA.objects.exclude(fecha_entrega=None).values_list("fecha_entrega", flat=True):
            conteo[d] += 1
        for d in ETA.objects.filter(fecha_retiro=None).values_list("fecha", flat=True):
            conteo[d] += 1
        return max(conteo, key=conteo.get) if conteo else None

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        disponibles = self._fechas_disponibles()

        fecha = None
        param = self.request.GET.get("fecha")
        if param:
            try:
                fecha = timezone.datetime.strptime(param, "%Y-%m-%d").date()
            except ValueError:
                fecha = None
        if fecha is None:
            fecha = self._fecha_por_defecto(disponibles)

        val = self.request.GET.get("val", "")  # "", "RETIRO" o "ENTREGA"

        retiros = (
            ETA.objects.filter(
                Q(fecha_retiro=fecha) | Q(fecha_retiro=None, fecha=fecha)
            ).select_related("cliente", "contenedor", "conductor")
            if fecha else ETA.objects.none()
        )
        entregas = (
            ETA.objects.filter(fecha_entrega=fecha)
            .select_related("cliente", "contenedor", "conductor")
            if fecha else ETA.objects.none()
        )

        # --- Filas de detalle (una por operación) ---
        filas = []
        if val in ("", "RETIRO"):
            for e in retiros:
                filas.append(self._fila(e, "RETIRO"))
        if val in ("", "ENTREGA"):
            for e in entregas:
                filas.append(self._fila(e, "ENTREGA"))
        filas.sort(key=lambda f: (f["horario"] or ""))

        # --- KPIs ---
        n_ret, n_ent = retiros.count(), entregas.count()
        estado_ret = self._distribucion(retiros, "get_estado_retiro_display")
        estado_ent = self._distribucion(entregas, "get_otd_display")

        conductores = {}
        for e in list(retiros) + list(entregas):
            if e.conductor_id:
                conductores[e.conductor_id] = e.conductor.estado
        cond_activos = sum(1 for v in conductores.values() if v == Conductor.Estado.ACTIVO)
        cond_inop = len(conductores) - cond_activos

        clientes_dia = {e.cliente_id for e in list(retiros) + list(entregas)}

        ctx.update({
            "fecha": fecha,
            "fechas_disponibles": disponibles,
            "val": val,
            "filas": filas,
            "kpi_operacion": {"RETIRO": n_ret, "ENTREGA": n_ent, "total": n_ret + n_ent},
            "kpi_estado_ret": estado_ret,
            "kpi_estado_ent": estado_ent,
            "kpi_conductores": {"activos": cond_activos, "inoperativos": cond_inop,
                                 "total": len(conductores)},
            "kpi_clientes": len(clientes_dia),
            "graf": {
                "operacion": {"labels": ["Entrega", "Retiro"], "data": [n_ent, n_ret]},
                "estado_ret": {"labels": list(estado_ret.keys()),
                                "data": list(estado_ret.values())},
                "estado_ent": {"labels": list(estado_ent.keys()),
                                "data": list(estado_ent.values())},
                "conductores": {"labels": ["Activo", "Inoperativo"],
                                 "data": [cond_activos, cond_inop]},
            },
        })
        return ctx

    @staticmethod
    def _fila(eta, val):
        return {
            "contenedor": eta.contenedor.codigo,
            "conductor": eta.conductor.nombre if eta.conductor else "—",
            "cliente": eta.cliente.nombre,
            "horario": eta.horario.strftime("%H:%M") if eta.horario else "",
            "val": val,
            "estado": (eta.get_estado_retiro_display() if val == "RETIRO"
                       else eta.get_otd_display()),
            "pk": eta.pk,
        }

    @staticmethod
    def _distribucion(qs, metodo):
        conteo = defaultdict(int)
        for e in qs:
            etiqueta = getattr(e, metodo)() or "Sin dato"
            conteo[etiqueta] += 1
        return dict(sorted(conteo.items(), key=lambda x: -x[1]))


# ============================================================
# Trazabilidad, recuentos y reportes (Sprint 4)
# ============================================================
class Recuentos(CualquierRol, ListView):
    model = ETA
    template_name = "operaciones/recuentos.html"
    context_object_name = "por_cliente"

    def get_queryset(self):
        return (
            Cliente.objects.annotate(
                total=Count("etas"),
                en_puerto=Count("etas", filter=Q(etas__estado__in=ESTADOS_EN_PUERTO)),
                en_deposito=Count("etas", filter=Q(etas__estado__in=ESTADOS_EN_DEPOSITO)),
            )
            .filter(total__gt=0)
            .order_by("nombre")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["total_puerto"] = ETA.objects.filter(estado__in=ESTADOS_EN_PUERTO).count()
        ctx["total_deposito"] = ETA.objects.filter(
            estado__in=ESTADOS_EN_DEPOSITO
        ).count()
        # Datos recientes para acompañar la vista por cliente.
        ctx["ultimas_etas"] = (
            ETA.objects.select_related("cliente", "contenedor")
            .order_by("-creado")[:5]
        )
        ctx["ultimos_en_puerto"] = (
            ETA.objects.filter(estado__in=ESTADOS_EN_PUERTO)
            .select_related("cliente", "contenedor")
            .order_by("-actualizado")[:5]
        )
        ctx["ultimos_en_deposito"] = (
            ETA.objects.filter(estado__in=ESTADOS_EN_DEPOSITO)
            .select_related("cliente", "contenedor")
            .order_by("-actualizado")[:5]
        )
        return ctx


# ============================================================
# Vista CEO: cronograma retiro-despacho por conductor / patente
# ============================================================
class RetiroDespacho(CualquierRol, TemplateView):
    """
    Panel ejecutivo: muestra todas las ETAs con conductor asignado,
    agrupadas por conductor/camión, con filtro por nombre o patente.
    Permite al CEO ver el cronograma de retiros y despachos.
    """

    template_name = "operaciones/retiro_despacho.html"

    def get_context_data(self, **kwargs):
        from datetime import timedelta
        from .models import Conductor as ConductorModel
        ctx = super().get_context_data(**kwargs)
        hoy = timezone.now().date()
        conductor_id = self.request.GET.get("conductor", "").strip()

        # Todos los conductores con ETAs activas (para el selector)
        ids_con_etas = (
            ETA.objects.filter(conductor__isnull=False)
            .exclude(estado=ETA.EstadoCiclo.DESPACHADO_PUERTO)
            .values_list("conductor_id", flat=True)
            .distinct()
        )
        conductores = (
            ConductorModel.objects.filter(pk__in=ids_con_etas)
            .select_related("empresa")
            .order_by("nombre")
        )

        # Enriquecer con conteo de ETAs y próxima fecha
        conductores_lista = []
        for c in conductores:
            etas_c = ETA.objects.filter(
                conductor=c
            ).exclude(estado=ETA.EstadoCiclo.DESPACHADO_PUERTO)
            patente = (
                etas_c.exclude(camion__isnull=True)
                .values_list("camion__patente", flat=True)
                .first()
            )
            conductores_lista.append({
                "conductor": c,
                "total": etas_c.count(),
                "hoy": etas_c.filter(fecha_retiro=hoy).count(),
                "patente": patente or "—",
            })

        ctx["conductores_lista"] = conductores_lista
        ctx["hoy"] = hoy
        ctx["conductor_id"] = conductor_id

        # Si hay conductor seleccionado → cargar sus ETAs
        if conductor_id:
            try:
                conductor_sel = ConductorModel.objects.select_related("empresa").get(pk=conductor_id)
                etas_sel = (
                    ETA.objects.select_related("camion", "cliente", "contenedor")
                    .filter(conductor=conductor_sel)
                    .exclude(estado=ETA.EstadoCiclo.DESPACHADO_PUERTO)
                    .order_by("fecha_retiro", "fecha")
                )
                ctx["conductor_sel"] = conductor_sel
                ctx["etas_sel"] = etas_sel
                ctx["total_sel"] = etas_sel.count()
                ctx["hoy_sel"] = etas_sel.filter(fecha_retiro=hoy).count()
                ctx["proximas_sel"] = etas_sel.filter(
                    fecha_retiro__gt=hoy, fecha_retiro__lte=hoy + timedelta(days=7)
                ).count()
            except ConductorModel.DoesNotExist:
                pass

        return ctx


class ReportesContextMixin:
    """
    Provee el listado de clientes para la sub-barra lateral de la sección
    Reportes. Se reutiliza tanto en la vista de gráficos como en el detalle
    por cliente (patrón vista/controlador: misma estructura, distinto cuerpo).
    """

    def get_clientes_sidebar(self):
        return (
            Cliente.objects.annotate(
                n_total=Count("etas"),
                n_deposito=Count(
                    "etas", filter=Q(etas__estado__in=ESTADOS_EN_DEPOSITO)
                ),
            )
            .filter(n_total__gt=0)
            .order_by("-n_deposito", "nombre")
        )


class Reportes(SoloAdmin, ReportesContextMixin, ListView):
    model = ETA
    template_name = "operaciones/reportes.html"
    context_object_name = "etas"

    def get_queryset(self):
        return ETA.objects.select_related("cliente", "contenedor").all()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["clientes_sidebar"] = self.get_clientes_sidebar()
        # Datos para los gráficos Chart.js. Lógica documentada en
        # docs/REPORTES_Y_GRAFOS.md (G1..G5).
        ctx["graficos"] = {
            "deposito_cliente": self._g_deposito_cliente(),
            "tiempo_etapa": self._g_tiempo_etapa(),
            "mov_agente": self._g_mov_agente(),
            "carga_deposito": self._g_carga_deposito(),
            "retiro_despacho": self._g_retiro_despacho(),
        }
        return ctx

    # -- G1: contenedores en depósito por cliente --
    def _g_deposito_cliente(self):
        qs = (
            Cliente.objects.annotate(
                n=Count("etas", filter=Q(etas__estado__in=ESTADOS_EN_DEPOSITO))
            )
            .filter(n__gt=0)
            .order_by("-n")
        )
        # Se incluyen los ids para permitir el "drill-down": al hacer clic en
        # una barra, el front navega al detalle del cliente correspondiente.
        return {
            "labels": [c.nombre for c in qs],
            "data": [c.n for c in qs],
            "ids": [c.id for c in qs],
        }

    # -- G2: tiempo promedio (días) entre etapas del ciclo --
    def _g_tiempo_etapa(self):
        # Primera marca temporal de cada tipo de movimiento por ETA.
        por_eta = defaultdict(dict)
        for m in Movimiento.objects.order_by("eta_id", "fecha"):
            por_eta[m.eta_id].setdefault(m.tipo, m.fecha)
        pares = [
            (Movimiento.Tipo.RETIRO, Movimiento.Tipo.ALMACENAJE, "Retiro → Almacenaje"),
            (Movimiento.Tipo.ALMACENAJE, Movimiento.Tipo.DESPACHO_CLIENTE, "Almacenaje → Despacho cliente"),
            (Movimiento.Tipo.DESPACHO_CLIENTE, Movimiento.Tipo.RETORNO, "Despacho cliente → Retorno"),
            (Movimiento.Tipo.RETORNO, Movimiento.Tipo.DESPACHO_PUERTO, "Retorno → Despacho puerto"),
        ]
        labels, data = [], []
        for ini, fin, etiqueta in pares:
            deltas = [
                (f[fin] - f[ini]).total_seconds() / 86400
                for f in por_eta.values()
                if ini in f and fin in f and f[fin] >= f[ini]
            ]
            labels.append(etiqueta)
            data.append(round(sum(deltas) / len(deltas), 1) if deltas else 0)
        return {"labels": labels, "data": data}

    # -- G3: movimientos por agente portuario --
    def _g_mov_agente(self):
        qs = (
            Movimiento.objects.values("eta__agente__nombre")
            .annotate(n=Count("id"))
            .order_by("-n")
        )
        return {
            "labels": [r["eta__agente__nombre"] or "—" for r in qs],
            "data": [r["n"] for r in qs],
        }

    # -- G4: carga en depósito por depósito y tipo de contenedor (apilado) --
    def _g_carga_deposito(self):
        filas = (
            ETA.objects.filter(estado__in=ESTADOS_EN_DEPOSITO)
            .values("deposito", "contenedor__tipo")
            .annotate(n=Count("id"))
        )
        tipos = dict(Contenedor.Tipo.choices)  # valor -> etiqueta
        depositos = sorted({(f["deposito"] or "—") for f in filas})
        matriz = {t: {d: 0 for d in depositos} for t in tipos}
        for f in filas:
            t = f["contenedor__tipo"]
            if t in matriz:
                matriz[t][f["deposito"] or "—"] += f["n"]
        datasets = [
            {"label": tipos[t], "data": [matriz[t][d] for d in depositos]}
            for t in tipos
            if any(matriz[t].values())
        ]
        return {"labels": depositos, "datasets": datasets}

    # -- G5: retiros vs despachos (cliente / puerto) en el tiempo (líneas) --
    def _g_retiro_despacho(self):
        def serie(tipo):
            qs = (
                Movimiento.objects.filter(tipo=tipo)
                .annotate(d=TruncDate("fecha"))
                .values("d")
                .annotate(n=Count("id"))
                .order_by("d")
            )
            return {r["d"]: r["n"] for r in qs}

        retiros = serie(Movimiento.Tipo.RETIRO)
        desp_cliente = serie(Movimiento.Tipo.DESPACHO_CLIENTE)
        desp_puerto = serie(Movimiento.Tipo.DESPACHO_PUERTO)
        fechas = sorted(set(retiros) | set(desp_cliente) | set(desp_puerto))
        return {
            "labels": [f.isoformat() for f in fechas],
            "retiros": [retiros.get(f, 0) for f in fechas],
            "despachos_cliente": [desp_cliente.get(f, 0) for f in fechas],
            "despachos_puerto": [desp_puerto.get(f, 0) for f in fechas],
        }


class ReporteCliente(SoloAdmin, ReportesContextMixin, ListView):
    """
    Detalle (drill-down) de un cliente: muestra en grilla todas sus ETAs,
    con filtro opcional por estado. Es el destino al hacer clic en una barra
    del gráfico "Contenedores en depósito por cliente".
    """

    model = ETA
    template_name = "operaciones/reporte_cliente.html"
    context_object_name = "etas"
    paginate_by = 30

    def get_queryset(self):
        self.cliente = get_object_or_404(Cliente, pk=self.kwargs["pk"])
        qs = (
            ETA.objects.filter(cliente=self.cliente)
            .select_related("cliente", "agente", "contenedor", "conductor", "camion")
            .order_by("-fecha")
        )
        estado = self.request.GET.get("estado")
        if estado:
            qs = qs.filter(estado=estado)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["clientes_sidebar"] = self.get_clientes_sidebar()
        ctx["cliente"] = self.cliente
        ctx["estados"] = ETA.EstadoCiclo.choices
        ctx["estado_sel"] = self.request.GET.get("estado", "")
        ctx["total_cliente"] = ETA.objects.filter(cliente=self.cliente).count()
        ctx["en_deposito_cliente"] = ETA.objects.filter(
            cliente=self.cliente, estado__in=ESTADOS_EN_DEPOSITO
        ).count()
        ctx["en_cliente_cliente"] = ETA.objects.filter(
            cliente=self.cliente, estado=ETA.EstadoCiclo.DESPACHADO_CLIENTE
        ).count()
        ctx["cerradas_cliente"] = ETA.objects.filter(
            cliente=self.cliente, estado=ETA.EstadoCiclo.DESPACHADO_PUERTO
        ).count()
        # Datos para los gráficos animados del panel de cliente (Chart.js).
        ctx["graficos"] = {
            "por_estado": self._g_por_estado(),
            "ubicacion": self._g_ubicacion(),
            "por_agente": self._g_por_agente(),
            "por_mes": self._g_por_mes(),
        }
        return ctx

    # Color hex por estado (alineado con op_extras.ESTADO_VARIANTE / badges).
    _ESTADO_HEX = {
        ETA.EstadoCiclo.SOLICITADO: "#ffc107",
        ETA.EstadoCiclo.ASIGNADO: "#0dcaf0",
        ETA.EstadoCiclo.EN_PATIO: "#0d6efd",
        ETA.EstadoCiclo.ALMACENADO: "#6c757d",
        ETA.EstadoCiclo.DESPACHADO_CLIENTE: "#198754",
        ETA.EstadoCiclo.DESPACHADO_PUERTO: "#212529",
    }

    # -- Distribución de las ETAs del cliente por estado del ciclo --
    def _g_por_estado(self):
        conteo = dict(
            ETA.objects.filter(cliente=self.cliente)
            .values_list("estado")
            .annotate(n=Count("id"))
        )
        labels, data, colores = [], [], []
        for valor, etiqueta in ETA.EstadoCiclo.choices:
            n = conteo.get(valor, 0)
            if n == 0:
                continue
            labels.append(etiqueta)
            data.append(n)
            colores.append(self._ESTADO_HEX.get(valor, "#6c757d"))
        return {"labels": labels, "data": data, "colores": colores}

    # -- Ubicación física actual de los contenedores del cliente --
    def _g_ubicacion(self):
        buckets = [
            ("Puerto (origen)", ESTADOS_EN_PUERTO, "#0dcaf0"),
            ("Depósito", ESTADOS_EN_DEPOSITO, "#198754"),
            ("En cliente", [ETA.EstadoCiclo.DESPACHADO_CLIENTE], "#ffc107"),
            ("Puerto (final)", [ETA.EstadoCiclo.DESPACHADO_PUERTO], "#212529"),
        ]
        labels, data, colores = [], [], []
        for etiqueta, estados, color in buckets:
            n = ETA.objects.filter(
                cliente=self.cliente, estado__in=estados
            ).count()
            if n == 0:
                continue
            labels.append(etiqueta)
            data.append(n)
            colores.append(color)
        return {"labels": labels, "data": data, "colores": colores}

    # -- ETAs del cliente por agente portuario --
    def _g_por_agente(self):
        qs = (
            ETA.objects.filter(cliente=self.cliente)
            .values("agente__nombre")
            .annotate(n=Count("id"))
            .order_by("-n")
        )
        return {
            "labels": [r["agente__nombre"] or "—" for r in qs],
            "data": [r["n"] for r in qs],
        }

    # -- ETAs del cliente por mes (línea de actividad) --
    def _g_por_mes(self):
        qs = (
            ETA.objects.filter(cliente=self.cliente)
            .annotate(m=TruncMonth("fecha"))
            .values("m")
            .annotate(n=Count("id"))
            .order_by("m")
        )
        return {
            "labels": [r["m"].strftime("%Y-%m") if r["m"] else "—" for r in qs],
            "data": [r["n"] for r in qs],
        }


# Mapea cada reporte a los estados que incluye.
REPORTES_CSV = {
    "retiro": [ETA.EstadoCiclo.SOLICITADO, ETA.EstadoCiclo.ASIGNADO, ETA.EstadoCiclo.EN_PATIO],
    "almacenados": ESTADOS_EN_DEPOSITO,
    "entregas": ESTADOS_CIERRE,
}


def exportar_csv(request, tipo):
    """Exporta un reporte (retiro/almacenados/entregas) a CSV."""
    if not en_grupos(request.user, [ROL_ADMIN]):
        return redirect("login")
    estados = REPORTES_CSV.get(tipo)
    if estados is None:
        return HttpResponse("Reporte no válido", status=404)

    etas = ETA.objects.filter(estado__in=estados).select_related(
        "cliente", "agente", "contenedor", "conductor", "camion"
    )

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="reporte_{tipo}.csv"'
    response.write("\ufeff")  # BOM para Excel (acentos correctos)
    writer = csv.writer(response, delimiter=";")
    writer.writerow(
        ["ETA", "Cliente", "Agente", "Contenedor", "Conductor", "Camion",
         "Deposito", "Fecha", "Estado"]
    )
    for e in etas:
        writer.writerow([
            e.numero,
            e.cliente.nombre,
            e.agente.nombre,
            e.contenedor.codigo,
            e.conductor.nombre if e.conductor else "",
            e.camion.patente if e.camion else "",
            e.deposito,
            e.fecha.isoformat(),
            e.get_estado_display(),
        ])
    r