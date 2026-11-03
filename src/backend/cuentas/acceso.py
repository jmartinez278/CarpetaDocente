"""Pantalla de inicio de cada rol, verificación de rol y respuesta de «sin permiso».

La verificación de rol es de US-001; la respuesta 403 de «sin permiso» es de US-004 (D3). Quién
recibe ese 403 y su registro los decide ``SeccionDocenteMixin`` (``institucion/views.py``).
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from cuentas.models import Usuario

_PANTALLA_DE_INICIO = {
    Usuario.Rol.DOCENTE: "docente:portada",
    Usuario.Rol.DIRECCION: "direccion:inicio",
    Usuario.Rol.ADMINISTRADOR: "admin:index",
}


def pantalla_de_inicio(usuario: Usuario) -> str:
    """Ruta de la pantalla a la que llega ``usuario`` al entrar, según su rol."""
    return reverse(_PANTALLA_DE_INICIO[usuario.rol])


def es_htmx(request) -> bool:
    """Si la petición la envía HTMX (cabecera ``HX-Request``)."""
    return request.headers.get("HX-Request") == "true"


def redirigir(request, destino: str):
    """Redirige a ``destino``; en una petición de HTMX, la página completa con ``HX-Redirect``.

    HTMX no procesa cabeceras en un 3xx: seguiría la redirección y pintaría la pantalla de
    destino (el ingreso, por ejemplo) dentro del diálogo (US-006, D7).
    """
    if es_htmx(request):
        respuesta = HttpResponse()
        respuesta["HX-Redirect"] = destino
        return respuesta
    return HttpResponseRedirect(destino)


PLANTILLA_SIN_PERMISO = "cuentas/sin_permiso.html"


def sin_permiso(request):
    """403 de «sin permiso»: la página en la misma dirección o, con HTMX, ``HX-Redirect`` (D3).

    Con ``HX-Request`` (HTMX y los guardados por ``fetch``) el cuerpo va vacío y la cabecera lleva
    a la página completa, para no pintar un fragmento roto en un diálogo. No registra: el registro
    lo hace quien decide negar, en la misma petición.
    """
    if es_htmx(request):
        respuesta = HttpResponse(status=403)
        respuesta["HX-Redirect"] = reverse("docente:sin_permiso")
        return respuesta
    return render(request, PLANTILLA_SIN_PERMISO, status=403)


class RolRequeridoMixin(LoginRequiredMixin):
    """Reserva una vista a un rol (spec inicio-sesion, "Pantalla de inicio reservada a su rol").

    Sin sesión, lleva a ``/ingresar/?next=…`` como ``LoginRequiredMixin``. Con otro
    rol, lleva a la pantalla de inicio de ese rol sin mostrar la vista pedida. Con HTMX,
    ambos van por ``HX-Redirect`` y el ``next`` es la portada del docente (US-006, D7).
    """

    rol_requerido: str | None = None

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.rol != self.rol_requerido:
            return redirigir(request, pantalla_de_inicio(request.user))
        return super().dispatch(request, *args, **kwargs)

    def handle_no_permission(self):
        if es_htmx(self.request) and not self.request.user.is_authenticated:
            destino = redirect_to_login(reverse("docente:portada"), self.get_login_url()).url
            return redirigir(self.request, destino)
        return super().handle_no_permission()
