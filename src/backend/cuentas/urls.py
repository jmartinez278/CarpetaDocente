"""Rutas del docente. Su portada vive en cuentas porque no es de una dimensión (D3)."""

from django.urls import path

from cuentas.views import PortadaDocenteView, SinPermisoView

app_name = "docente"

urlpatterns = [
    path("", PortadaDocenteView.as_view(), name="portada"),
    path("sin-permiso/", SinPermisoView.as_view(), name="sin_permiso"),
]
