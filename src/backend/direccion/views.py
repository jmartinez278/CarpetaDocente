"""Vistas del módulo direccion (US-040)."""

from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from asistencia.servicios import saludo
from cuentas.acceso import RolRequeridoMixin
from cuentas.models import Usuario
from direccion import servicios
from institucion.servicios import texto_seccion
from repositorio import servicios as repositorio
from repositorio.views import EntregaBase, no_disponible


class DireccionMixin(RolRequeridoMixin):
    """Reserva la vista al rol Dirección (D2): otro rol va a su inicio y una visita, al ingreso."""

    rol_requerido = Usuario.Rol.DIRECCION


class ConsolidadosView(DireccionMixin, TemplateView):
    """Consolidados de la dirección. Por ahora solo el marco con el ☰ (US-040, D2 y D8): el mapa
    y el resumen llegan en el grupo 6."""

    http_method_names = ["get", "head", "options"]
    template_name = "direccion/consolidados.html"


class SeccionView(DireccionMixin, TemplateView):
    """Una pestaña del detalle de una sección (D2). Solo lectura: ``seccion_de_la_direccion``
    da 404 para otra institución, un año CERRADO o una sección que no existe.

    Por ahora solo el título de la sección; las pestañas llegan en los grupos 6 y 7.
    """

    http_method_names = ["get", "head", "options"]
    template_name = "direccion/seccion.html"
    pestana = ""

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        seccion = servicios.seccion_de_la_direccion(self.request.user, self.kwargs["id_seccion"])
        contexto.update(
            seccion=seccion, titulo_seccion=texto_seccion(seccion), pestana=self.pestana
        )
        return contexto


def _volver_a_consolidados():
    return ("Consolidados", "Volver a Consolidados", reverse("direccion:consolidados"))


class SesionView(DireccionMixin, View):
    """La página de una sesión para la dirección (D2 y D7): la de la docente sin migas, acciones
    de la autora ni total de vistas, y sin contar una vista (la dirección no es colega)."""

    http_method_names = ["get", "head", "options"]

    def get(self, request, id_sesion):
        sesion = repositorio.sesion_visible_direccion(request.user, id_sesion)
        if sesion is None:
            return no_disponible(request, _volver_a_consolidados())
        contexto = {
            "sesion": sesion,
            "grado": sesion.grados_texto,
            "referencia": False,
            "url_descargar": reverse("direccion:descargar", args=[sesion.pk]),
            "url_ver": reverse("direccion:ver", args=[sesion.pk]),
        }
        return render(request, "direccion/sesion.html", contexto)


class EntregarView(DireccionMixin, EntregaBase):
    """«Descargar» y «Ver» para la dirección: la misma entrega, con su puerta de visibilidad."""

    http_method_names = ["get", "head", "options"]
    visible = staticmethod(repositorio.sesion_visible_direccion)

    def no_disponible(self, request):
        return no_disponible(request, _volver_a_consolidados())


class InicioDireccionView(RolRequeridoMixin, TemplateView):
    """Portada de la dirección (spec pantallas-de-inicio, «Inicio de la dirección»; D9).

    Saluda según la hora de Lima como la del docente y lleva la banda de Consolidados con las
    secciones atrasadas del bimestre vigente, Entregas (próximamente) y el cierre del bimestre,
    con el botón que abre la plantilla del SIAGIE.
    """

    rol_requerido = Usuario.Rol.DIRECCION
    template_name = "direccion/inicio.html"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        institucion = self.request.user.institucion
        contexto["saludo"] = saludo(timezone.localtime().hour)
        contexto["institucion"] = institucion
        contexto["inicio"] = servicios.inicio_de_la_direccion(institucion, timezone.localdate())
        return contexto
