"""Rutas de las competencias de una sección (design de US-029, D8).

Se incluyen en ``config/urls.py`` bajo ``docente/secciones/<int:seccion_id>/competencias/``. El
número del periodo va en la ruta del guardado.
"""

from django.urls import path

from notas import views

app_name = "competencias"

urlpatterns = [
    path("", views.CompetenciasView.as_view(), name="pantalla"),
    path("<int:numero>/", views.GuardarView.as_view(), name="guardar"),
]
