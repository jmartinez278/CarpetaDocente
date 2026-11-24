"""Rutas de la dirección (US-040, D2)."""

from django.urls import path

from direccion.views import ConsolidadosView, InicioDireccionView

app_name = "direccion"

urlpatterns = [
    path("", InicioDireccionView.as_view(), name="inicio"),
    path("consolidados/", ConsolidadosView.as_view(), name="consolidados"),
]
