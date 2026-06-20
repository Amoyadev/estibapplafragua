"""
Control de acceso por rol (grupos Django) para Estibapp.

Los superusuarios tienen acceso total. El resto se valida por pertenencia
a los grupos: Administrador, Coordinador, Encargado de Patio.
"""
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

# Nombres de los grupos (deben coincidir con la migración 0002_roles).
ROL_ADMIN = "Administrador"
ROL_COORDINADOR = "Coordinador"
ROL_PATIO = "Encargado de Patio"


def en_grupos(user, nombres):
    """True si el usuario es superuser o pertenece a alguno de los grupos."""
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=nombres).exists()


class RolRequeridoMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin para vistas basadas en clase. Define `roles_permitidos`
    como lista de nombres de grupo. Superuser siempre pasa.
    """

    roles_permitidos: list[str] = []

    def test_func(self):
        return en_grupos(self.request.user, self.roles_permitidos)


class SoloAdmin(RolRequeridoMixin):
    roles_permitidos = [ROL_ADMIN]


class AdminOCoordinador(RolRequeridoMixin):
    roles_permitidos = [ROL_ADMIN, ROL_COORDINADOR]


class AdminOPatio(RolRequeridoMixin):
    roles_permitidos = [ROL_ADMIN, ROL_PATIO]


class CualquierRol(RolRequeridoMixin):
    roles_permitidos = [ROL_ADMIN, ROL_COORDINADOR, ROL_PATIO]
