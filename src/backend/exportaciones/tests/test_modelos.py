"""Equivalencia de una sección del SIAGIE con una de la I.E. (US-024/025, design D5)."""

import pytest
from django.contrib import admin
from django.db import IntegrityError, transaction
from django.test import RequestFactory
from django.urls import reverse

from exportaciones.models import EquivalenciaSeccion
from institucion.models import Seccion

pytestmark = pytest.mark.django_db


@pytest.fixture
def otra_seccion(anio_abierto):
    return Seccion.objects.create(anio_escolar=anio_abierto, grado=2, nombre="B")


def equivalencia(seccion, codigo="01", nombre="TRIUNFADORES", **campos):
    return EquivalenciaSeccion.objects.create(
        seccion=seccion,
        anio_escolar=seccion.anio_escolar,
        grado=seccion.grado,
        codigo_siagie=codigo,
        nombre_siagie=nombre,
        **campos,
    )


def test_una_equivalencia_valida_se_guarda(seccion, direccion):
    guardada = equivalencia(seccion, creado_por=direccion)

    guardada.refresh_from_db()
    assert guardada.seccion == seccion
    assert guardada.creado_en is not None
    assert seccion.equivalencia_siagie == guardada


def test_la_misma_seccion_no_tiene_dos_equivalencias(seccion):
    equivalencia(seccion)

    with pytest.raises(IntegrityError), transaction.atomic():
        equivalencia(seccion, codigo="02", nombre="CAMPEONES")


def test_la_misma_seccion_del_siagie_no_va_a_dos_secciones(seccion, otra_seccion):
    equivalencia(seccion)

    with pytest.raises(IntegrityError), transaction.atomic():
        equivalencia(otra_seccion)


def test_el_mismo_nombre_con_otro_codigo_es_otra_seccion_del_siagie(seccion, otra_seccion):
    equivalencia(seccion, codigo="01")
    equivalencia(otra_seccion, codigo="02")

    assert EquivalenciaSeccion.objects.count() == 2


def test_borrar_la_seccion_borra_su_equivalencia(seccion):
    equivalencia(seccion)

    seccion.delete()

    assert not EquivalenciaSeccion.objects.exists()


def test_borrar_la_cuenta_que_la_guardo_conserva_la_equivalencia(seccion, direccion):
    guardada = equivalencia(seccion, creado_por=direccion)

    direccion.delete()

    guardada.refresh_from_db()
    assert guardada.creado_por is None


# --- Panel: solo lectura (design D5) ---


def test_el_panel_la_muestra_sin_agregar_cambiar_ni_borrar(administrador):
    peticion = RequestFactory().get("/admin/")
    peticion.user = administrador
    model_admin = admin.site._registry[EquivalenciaSeccion]

    assert model_admin.has_view_permission(peticion)
    assert not model_admin.has_add_permission(peticion)
    assert not model_admin.has_change_permission(peticion)
    assert not model_admin.has_delete_permission(peticion)


def test_la_lista_del_panel_abre(client, administrador, seccion):
    equivalencia(seccion)
    client.force_login(administrador)

    respuesta = client.get(reverse("admin:exportaciones_equivalenciaseccion_changelist"))

    assert respuesta.status_code == 200
    assert "TRIUNFADORES" in respuesta.content.decode()
