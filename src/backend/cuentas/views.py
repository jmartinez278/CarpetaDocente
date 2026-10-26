"""Vistas del módulo cuentas: ingreso, redirecciones y portada del docente (US-001)."""

from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.views import LoginView, redirect_to_login
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic import RedirectView, TemplateView

from cuentas import dimensiones
from cuentas.acceso import RolRequeridoMixin, pantalla_de_inicio
from cuentas.forms import FormularioIngreso
from cuentas.models import Usuario
from institucion import servicios


class IngresarView(LoginView):
    """Inicio de sesión único de los tres roles en ``/ingresar/`` (RF-001).

    Al entrar, cada rol llega a su pantalla de inicio, o a ``next`` si es una
    dirección del propio sitio. Con la sesión ya iniciada, no muestra el formulario.
    """

    form_class = FormularioIngreso
    template_name = "cuentas/ingresar.html"
    redirect_authenticated_user = True

    def get_redirect_url(self):
        destino = super().get_redirect_url()
        # Un next que vuelve a /ingresar/ haría que LoginView detecte un ciclo y falle.
        return "" if destino.split("?")[0] == self.request.path else destino

    def get_default_redirect_url(self):
        return pantalla_de_inicio(self.request.user)


class RaizView(RedirectView):
    """La ruta raíz: sin sesión, a ``/ingresar/``; con sesión, a la pantalla del rol."""

    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            return pantalla_de_inicio(self.request.user)
        return reverse("ingresar")


class IngresoPanelView(View):
    """Reemplaza el login del panel: todo ingreso pasa por ``/ingresar/`` (RN-024).

    - Sin sesión, lleva a ``/ingresar/`` y conserva ``next``.
    - Con una cuenta de staff, vuelve al panel.
    - Con otra cuenta, lleva a su pantalla de inicio. Si esa pantalla es el panel (un
      ADMINISTRADOR sin ``is_staff``, creado a mano), responde 403 para cortar el
      ciclo panel → login → panel.
    """

    def get(self, request, *args, **kwargs):
        siguiente = request.GET.get(REDIRECT_FIELD_NAME, "")
        if not request.user.is_authenticated:
            if siguiente:
                return redirect_to_login(siguiente, reverse("ingresar"))
            return redirect("ingresar")
        if request.user.is_staff:
            if url_has_allowed_host_and_scheme(
                siguiente, allowed_hosts={request.get_host()}, require_https=request.is_secure()
            ):
                return redirect(siguiente)
            return redirect(reverse("admin:index"))
        destino = pantalla_de_inicio(request.user)
        if destino == reverse("admin:index"):
            raise PermissionDenied
        return redirect(destino)


class PortadaDocenteView(RolRequeridoMixin, TemplateView):
    """Portada del docente, con las tres dimensiones (spec pantallas-de-inicio).

    Cada tarjeta enlaza a su pantalla o queda en "Próximamente" según su bandera (D7), y el
    carrusel del celular abre en la tarjeta inicial.
    """

    rol_requerido = Usuario.Rol.DOCENTE
    template_name = "cuentas/portada_docente.html"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["dimensiones"] = dimensiones.DIMENSIONES
        contexto["inicial"] = dimensiones.tarjeta_inicial(dimensiones.DIMENSIONES)
        contexto["secciones"] = servicios.texto_secciones_docente(self.request.user)
        return contexto
