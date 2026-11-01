"""Rutas de la hoja de notas de una sección (design de US-020, D8).

Se incluyen en ``config/urls.py`` bajo ``docente/secciones/<int:seccion_id>/notas/``. Es un módulo
aparte porque ``notas/urls.py`` ya es el namespace ``competencias``. El guardado lleva en la ruta
el número del periodo y el código SIAGIE del área.
"""

from django.urls import path

from notas import views

app_name = "notas"

urlpatterns = [
    path("", views.HojaView.as_view(), name="hoja"),
    path("<int:numero>/<str:area>/", views.GuardarHojaView.as_view(), name="guardar"),
]
