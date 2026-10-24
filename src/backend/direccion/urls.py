"""Rutas de la dirección. Los consolidados llegarán con US-040."""

from django.urls import path

from direccion.views import InicioDireccionView

app_name = "direccion"

urlpatterns = [
    path("", InicioDireccionView.as_view(), name="inicio"),
]
