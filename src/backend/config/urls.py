"""Rutas de la aplicación. El catálogo de rutas está en docs/03 Implementación."""

from django.contrib import admin
from django.urls import include, path

from cuentas.views import IngresarView, IngresoPanelView, RaizView

urlpatterns = [
    path("", RaizView.as_view(), name="raiz"),
    path("ingresar/", IngresarView.as_view(), name="ingresar"),
    path("docente/", include("cuentas.urls")),
    path("direccion/", include("direccion.urls")),
    # Antes de admin.site.urls: el panel no tiene un login propio (RN-024).
    path("admin/login/", IngresoPanelView.as_view(), name="ingreso_panel"),
    path("admin/", admin.site.urls),
]
