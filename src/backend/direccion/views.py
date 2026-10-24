"""Vistas del módulo direccion."""

from django.views.generic import TemplateView

from cuentas.acceso import RolRequeridoMixin
from cuentas.models import Usuario


class InicioDireccionView(RolRequeridoMixin, TemplateView):
    """Inicio de la dirección: estado vacío hasta los consolidados de US-040."""

    rol_requerido = Usuario.Rol.DIRECCION
    template_name = "direccion/inicio.html"
