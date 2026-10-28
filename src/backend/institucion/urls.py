"""Rutas de la lista de estudiantes de una sección (US-006, D4).

Se incluyen en ``config/urls.py`` bajo ``docente/secciones/<int:seccion_id>/estudiantes/``.
"""

from django.urls import path

from institucion import views

app_name = "estudiantes"

urlpatterns = [
    path("", views.ListaView.as_view(), name="lista"),
    path("agregar/", views.AgregarView.as_view(), name="agregar"),
    path("pegar/", views.PegarView.as_view(), name="pegar"),
    path("<int:estudiante_id>/editar/", views.EditarView.as_view(), name="editar"),
    path("<int:estudiante_id>/quitar/", views.QuitarView.as_view(), name="quitar"),
    path("vaciar/", views.VaciarView.as_view(), name="vaciar"),
]
