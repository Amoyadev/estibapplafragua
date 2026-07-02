"""Vistas de la app Flota (Tracto + SemiRemolque)."""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from apps.operaciones.permissions import AdminOCoordinador

from .forms import SemiRemolqueForm, TractoForm
from .models import SemiRemolque, Tracto


# ── Base genérica ──────────────────────────────────────────────────────────
class BaseFlotaList(AdminOCoordinador, ListView):
    template_name = "flota/catalogo_lista.html"
    paginate_by = 20
    titulo = ""
    crear_url = ""
    editar_url = ""
    eliminar_url = ""
    columnas: list = []

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


class BaseFlotaCreate(AdminOCoordinador, CreateView):
    template_name = "flota/catalogo_form.html"
    titulo = ""

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titulo"] = self.titulo
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Registro creado correctamente.")
        return super().form_valid(form)


class BaseFlotaUpdate(AdminOCoordinador, UpdateView):
    template_name = "flota/catalogo_form.html"
    titulo = ""

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titulo"] = self.titulo
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Registro actualizado correctamente.")
        return super().form_valid(form)


class BaseFlotaDelete(AdminOCoordinador, DeleteView):
    template_name = "flota/catalogo_confirmar_eliminar.html"

    def form_valid(self, form):
        messages.success(self.request, "Registro eliminado.")
        return super().form_valid(form)


# ── Tracto ─────────────────────────────────────────────────────────────────
class TractoList(BaseFlotaList):
    model = Tracto
    titulo = "Tractos"
    crear_url = "flota:tracto_crear"
    editar_url = "flota:tracto_editar"
    eliminar_url = "flota:tracto_eliminar"
    columnas = [
        ("Patente", "patente"),
        ("Marca", "marca"),
        ("Modelo", "modelo"),
        ("Estado", "get_estado_display"),
        ("Vto. revisión", "vencimiento_revision"),
    ]


class TractoCreate(BaseFlotaCreate):
    model = Tracto
    form_class = TractoForm
    titulo = "Nuevo tracto"
    success_url = reverse_lazy("flota:tracto_list")


class TractoUpdate(BaseFlotaUpdate):
    model = Tracto
    form_class = TractoForm
    titulo = "Editar tracto"
    success_url = reverse_lazy("flota:tracto_list")


class TractoDelete(BaseFlotaDelete):
    model = Tracto
    success_url = reverse_lazy("flota:tracto_list")


# ── SemiRemolque ───────────────────────────────────────────────────────────
class SemiRemolqueList(BaseFlotaList):
    model = SemiRemolque
    titulo = "Semirremolques"
    crear_url = "flota:semiremolque_crear"
    editar_url = "flota:semiremolque_editar"
    eliminar_url = "flota:semiremolque_eliminar"
    columnas = [
        ("Patente", "patente"),
        ("Tipo", "get_tipo_display"),
        ("Estado", "get_estado_display"),
    ]


class SemiRemolqueCreate(BaseFlotaCreate):
    model = SemiRemolque
    form_class = SemiRemolqueForm
    titulo = "Nuevo semirremolque"
    success_url = reverse_lazy("flota:semiremolque_list")


class SemiRemolqueUpdate(BaseFlotaUpdate):
    model = SemiRemolque
    form_class = SemiRemolqueForm
    titulo = "Editar semirremolque"
    success_url = reverse_lazy("flota:semiremolque_list")


class SemiRemolqueDelete(BaseFlotaDelete):
    model = SemiRemolque
    success_url = reverse_lazy("flota:semiremolque_list")
