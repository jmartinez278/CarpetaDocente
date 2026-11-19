"""Rutas de exportaciones: completar la plantilla del SIAGIE (US-024/025, design D1 y D13)."""

from django.urls import path

from exportaciones.views import BorrarEquivalenciaView, CompletarPlantillaView

app_name = "plantilla_siagie"

urlpatterns = [
    path("", CompletarPlantillaView.as_view(), name="completar"),
    path(
        "equivalencias/<int:equivalencia_id>/borrar/",
        BorrarEquivalenciaView.as_view(),
        name="borrar",
    ),
]
