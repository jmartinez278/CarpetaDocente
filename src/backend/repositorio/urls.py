"""Rutas de Sesiones (design de US-010, US-014 y EN-03, D7).

Se incluyen en ``config/urls.py`` bajo ``docente/sesiones/``.
"""

from django.urls import path

from repositorio import views

app_name = "sesiones"

urlpatterns = [
    path("", views.SesionesView.as_view(), name="inicio"),
    path("enviar/", views.EnviarSesionView.as_view(), name="enviar"),
]
