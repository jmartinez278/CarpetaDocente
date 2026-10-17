"""Vistas del módulo cuentas."""

from django.views.generic import TemplateView


class InicioView(TemplateView):
    """Página inicial: identifica el sistema y sus tres dimensiones (EN-01).

    Será la página de entrada tras el inicio de sesión (RF-001, US-001).
    """

    template_name = "inicio.html"
