from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods


class HomeLoginView(LoginView):
    """
    Página de inicio: presentación corporativa + acceso (login) en una sola
    vista. No existe una pantalla de login separada; el formulario vive dentro
    de la landing. Si el usuario ya tiene sesión, se redirige al panel.
    """

    template_name = "core/home.html"
    redirect_authenticated_user = True


def health(request):
    """Health check para Nginx / orquestadores."""
    return JsonResponse({"status": "ok", "service": "estiba"})


@require_http_methods(["GET", "POST"])
def cerrar_sesion(request):
    """
    Cierra la sesión y muestra una página de despedida corporativa.

    Se acepta GET y POST: el botón "Salir" envía POST (CSRF), pero también se
    tolera GET para no romper enlaces directos. Tras cerrar la sesión se
    renderiza una pantalla sobria que reconoce la labor operativa del usuario.
    """
    nombre = ""
    if request.user.is_authenticated:
        nombre = request.user.get_full_name() or request.user.get_username()
        logout(request)
    return render(request, "registration/logged_out.html", {"nombre": nombre})

