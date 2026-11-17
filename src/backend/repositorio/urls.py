"""Rutas de Sesiones (design de US-010, US-014 y EN-03, D7; de US-011, D10).

Se incluyen en ``config/urls.py`` bajo ``docente/sesiones/``. Un ``id`` que no es UUID no llega a
la vista: 404 de Django.
"""

from django.urls import path

from repositorio import views

app_name = "sesiones"

urlpatterns = [
    path("", views.SesionesView.as_view(), name="inicio"),
    path("repositorio/", views.RepositorioView.as_view(), name="repositorio"),
    path("enviar/", views.EnviarSesionView.as_view(), name="enviar"),
    path("<uuid:id_sesion>/", views.SesionView.as_view(), name="detalle"),
    path(
        "<uuid:id_sesion>/descargar/",
        views.EntregarView.as_view(modo="descargar"),
        name="descargar",
    ),
    path("<uuid:id_sesion>/ver/", views.EntregarView.as_view(modo="ver"), name="ver"),
    path("<uuid:id_sesion>/eliminar/", views.EliminarView.as_view(), name="eliminar"),
    path("<uuid:id_sesion>/compartir/", views.CompartirView.as_view(), name="compartir"),
    path(
        "<uuid:id_sesion>/dejar-de-compartir/",
        views.DejarDeCompartirView.as_view(),
        name="dejar_de_compartir",
    ),
]
