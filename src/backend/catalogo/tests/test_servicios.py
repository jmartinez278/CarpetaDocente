"""Pruebas de las áreas de cada institución (spec catalogo-curricular; design de EN-06, D4)."""

import pytest

from catalogo import servicios
from catalogo.models import InstitucionArea
from institucion.models import Institucion

pytestmark = pytest.mark.django_db


@pytest.fixture
def institucion():
    return Institucion.objects.create(nombre="I.E. Ficticia N.° 1")


def test_institucion_nueva_nace_con_las_11_areas_y_solo_0002_sin_trabajar(institucion):
    filas = InstitucionArea.objects.filter(institucion=institucion)

    assert filas.count() == 11
    assert list(filas.filter(se_trabaja=False).values_list("area__codigo_siagie", flat=True)) == [
        "0002"
    ]


def test_asegurar_areas_repetido_no_duplica_ni_cambia_un_se_trabaja_editado(institucion):
    fila = InstitucionArea.objects.get(institucion=institucion, area__codigo_siagie="0002")
    fila.se_trabaja = True
    fila.save()

    servicios.asegurar_areas(institucion)
    servicios.asegurar_areas(institucion)

    assert InstitucionArea.objects.filter(institucion=institucion).count() == 11
    fila.refresh_from_db()
    assert fila.se_trabaja is True


def test_asegurar_areas_crea_solo_las_que_faltan(institucion):
    InstitucionArea.objects.filter(
        institucion=institucion, area__codigo_siagie__in=["0002", "0005"]
    ).delete()

    servicios.asegurar_areas(institucion)

    filas = InstitucionArea.objects.filter(institucion=institucion)
    assert filas.count() == 11
    assert filas.get(area__codigo_siagie="0002").se_trabaja is False
    assert filas.get(area__codigo_siagie="0005").se_trabaja is True


def test_guardar_de_nuevo_una_institucion_existente_no_crea_filas(institucion):
    InstitucionArea.objects.filter(institucion=institucion, area__codigo_siagie="0005").delete()

    institucion.nombre = "I.E. Ficticia N.° 2"
    institucion.save()

    assert InstitucionArea.objects.filter(institucion=institucion).count() == 10
