"""Pruebas del registro de Institución en el panel de administración (documento 10)."""

import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_panel_lista_instituciones(admin_client):
    respuesta = admin_client.get(reverse("admin:institucion_institucion_changelist"))

    assert respuesta.status_code == 200
