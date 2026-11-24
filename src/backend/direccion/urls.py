"""Rutas de la dirección (US-040, D2). Todas de solo lectura y del rol Dirección."""

from django.urls import path

from direccion import views

app_name = "direccion"

urlpatterns = [
    path("", views.InicioDireccionView.as_view(), name="inicio"),
    path("consolidados/", views.ConsolidadosView.as_view(), name="consolidados"),
    path(
        "consolidados/secciones/<int:id_seccion>/notas/",
        views.SeccionView.as_view(pestana="notas"),
        name="notas",
    ),
    path(
        "consolidados/secciones/<int:id_seccion>/asistencia/",
        views.SeccionView.as_view(pestana="asistencia"),
        name="asistencia",
    ),
    path(
        "consolidados/secciones/<int:id_seccion>/sesiones/",
        views.SeccionView.as_view(pestana="sesiones"),
        name="sesiones",
    ),
    path("sesiones/<uuid:id_sesion>/", views.SesionView.as_view(), name="sesion"),
    path(
        "sesiones/<uuid:id_sesion>/descargar/",
        views.EntregarView.as_view(modo="descargar"),
        name="descargar",
    ),
    path("sesiones/<uuid:id_sesion>/ver/", views.EntregarView.as_view(modo="ver"), name="ver"),
]
