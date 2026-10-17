"""Rutas de la aplicación. El catálogo de rutas está en docs/03 Implementación."""

from django.contrib import admin
from django.urls import path

from cuentas.views import InicioView

urlpatterns = [
    path("", InicioView.as_view(), name="inicio"),
    path("admin/", admin.site.urls),
]
