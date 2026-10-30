"""Pruebas de los modelos del catálogo (spec catalogo-curricular; design de EN-06, D1).

Las áreas de prueba usan códigos que el SIAGIE no tiene (99xx), para no chocar con el
catálogo que carga la migración ``0002``.
"""

import pytest
from django.db import IntegrityError, transaction
from django.db.models import RestrictedError

from catalogo.models import Area, Competencia, InstitucionArea
from institucion.models import Institucion

pytestmark = pytest.mark.django_db


@pytest.fixture
def area():
    return Area.objects.create(codigo_siagie="9901", nombre="Área ficticia uno", orden=91)


@pytest.fixture
def otra_area():
    return Area.objects.create(codigo_siagie="9902", nombre="Área ficticia dos", orden=92)


@pytest.fixture
def institucion():
    return Institucion.objects.create(nombre="I.E. Ficticia N.° 1")


def test_area_con_codigo_repetido_se_rechaza(area):
    with pytest.raises(IntegrityError), transaction.atomic():
        Area.objects.create(codigo_siagie="9901", nombre="Área ficticia tres", orden=93)


def test_area_con_nombre_repetido_se_rechaza(area):
    with pytest.raises(IntegrityError), transaction.atomic():
        Area.objects.create(codigo_siagie="9903", nombre="Área ficticia uno", orden=93)


def test_competencia_repetida_en_la_misma_area_se_rechaza(area):
    Competencia.objects.create(area=area, nombre="Competencia ficticia", orden=1)

    with pytest.raises(IntegrityError), transaction.atomic():
        Competencia.objects.create(area=area, nombre="Competencia ficticia", orden=2)


def test_mismo_nombre_de_competencia_en_otra_area_se_acepta(area, otra_area):
    Competencia.objects.create(area=area, nombre="Competencia ficticia", orden=1)
    Competencia.objects.create(area=otra_area, nombre="Competencia ficticia", orden=1)

    assert Competencia.objects.filter(nombre="Competencia ficticia").count() == 2


def test_dos_filas_de_la_misma_area_para_una_institucion_se_rechazan(institucion, area):
    InstitucionArea.objects.create(institucion=institucion, area=area)

    with pytest.raises(IntegrityError), transaction.atomic():
        InstitucionArea.objects.create(institucion=institucion, area=area, se_trabaja=False)


def test_borrar_un_area_con_competencias_falla(area):
    Competencia.objects.create(area=area, nombre="Competencia ficticia", orden=1)

    with pytest.raises(RestrictedError), transaction.atomic():
        area.delete()

    assert Area.objects.filter(pk=area.pk).exists()


def test_borrar_una_institucion_borra_sus_areas(institucion, area):
    InstitucionArea.objects.create(institucion=institucion, area=area)

    institucion.delete()

    assert not InstitucionArea.objects.filter(area=area).exists()
    assert Area.objects.filter(pk=area.pk).exists()


def test_competencia_nueva_nace_activa(area):
    competencia = Competencia.objects.create(area=area, nombre="Competencia ficticia", orden=1)

    competencia.refresh_from_db()
    assert competencia.activa is True


def test_area_de_institucion_nueva_se_trabaja(institucion, area):
    fila = InstitucionArea.objects.create(institucion=institucion, area=area)

    fila.refresh_from_db()
    assert fila.se_trabaja is True
