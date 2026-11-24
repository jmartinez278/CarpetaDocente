"""Rutas de la dirección (US-040, D2). Todas de solo lectura y del rol Dirección."""

from django.urls import path

from direccion import views

app_name = "direccion"

urlpatterns = [
    path("", views.InicioDireccionView.as_view(), name="inicio"),
    path("consolidados/", views.ConsolidadosView.as_view(), name="consolidados"),
    path(
        "consolidados/secciones/<int:id_seccion>/notas/",
        views.NotasView.as_view(),
        name="notas",
    ),
    path(
        "consolidados/secciones/<int:id_seccion>/asistencia/",
        views.AsistenciaView.as_view(),
        name="asistencia",
    ),
    path(
        "consolidados/secciones/<int:id_seccion>/sesiones/",
        views.SesionesView.as_view(),
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
