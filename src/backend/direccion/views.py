"""Vistas del módulo direccion (US-040)."""

from django.utils import timezone
from django.views.generic import TemplateView

from asistencia.servicios import saludo
from cuentas.acceso import RolRequeridoMixin
from cuentas.models import Usuario
from direccion import servicios


class ConsolidadosView(RolRequeridoMixin, TemplateView):
    """Consolidados de la dirección. Por ahora solo el marco con el ☰ (US-040, D2 y D8): el mapa
    y el resumen llegan en el grupo 6."""

    rol_requerido = Usuario.Rol.DIRECCION
    template_name = "direccion/consolidados.html"


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
