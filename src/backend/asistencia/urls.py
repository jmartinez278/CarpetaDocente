"""Rutas de la asistencia de una sección (design de US-030, D10).

Se incluyen en ``config/urls.py`` bajo ``docente/secciones/<int:seccion_id>/asistencia/``. La fecha
va en la ruta de los guardados para que US-031 abra otros días sin cambiarlas.
"""

import datetime

from django.urls import path, register_converter

from asistencia import views


class FechaConverter:
    """Una fecha AAAA-MM-DD que existe; "2026-02-30" no es una ruta (404)."""

    regex = r"\d{4}-\d{2}-\d{2}"

    def to_python(self, value):
        return datetime.date.fromisoformat(value)

    def to_url(self, value):
        return value.isoformat() if isinstance(value, datetime.date) else value


register_converter(FechaConverter, "fecha")

app_name = "asistencia"

urlpatterns = [
    path("", views.HoyView.as_view(), name="hoy"),
    path(
        "<fecha:fecha>/estudiantes/<int:estudiante_id>/",
        views.MarcarView.as_view(),
        name="marcar",
    ),
    path("<fecha:fecha>/restantes/", views.RestantesView.as_view(), name="restantes"),
]
