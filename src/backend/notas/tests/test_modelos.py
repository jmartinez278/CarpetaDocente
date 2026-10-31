"""Pruebas de CompetenciaPeriodo (spec competencias-periodo; design de US-029, D1)."""

import datetime

import pytest
from django.db import IntegrityError, transaction
from django.db.models import RestrictedError

from catalogo.models import Competencia
from institucion.models import Periodo, Seccion
from notas.models import CompetenciaPeriodo

pytestmark = pytest.mark.django_db


@pytest.fixture
def competencia():
    return Competencia.objects.get(area__codigo_siagie="063", orden=1)


@pytest.fixture
def marca(seccion, bimestre_1, competencia):
    return CompetenciaPeriodo.objects.create(
        seccion=seccion, periodo=bimestre_1, competencia=competencia
    )


def test_la_tabla_es_competencia_periodo():
    assert CompetenciaPeriodo._meta.db_table == "competencia_periodo"


def test_la_misma_marca_dos_veces_la_rechaza_la_base(marca):
    with pytest.raises(IntegrityError, match="uq_competencia_periodo"), transaction.atomic():
        CompetenciaPeriodo.objects.create(
            seccion=marca.seccion, periodo=marca.periodo, competencia=marca.competencia
        )


def test_la_misma_competencia_en_otro_periodo_se_acepta(marca, anio_abierto):
    bimestre_2 = Periodo.objects.create(
        anio_escolar=anio_abierto,
        numero=2,
        fecha_inicio=datetime.date(2027, 5, 25),
        fecha_fin=datetime.date(2027, 7, 24),
    )

    CompetenciaPeriodo.objects.create(
        seccion=marca.seccion, periodo=bimestre_2, competencia=marca.competencia
    )

    assert CompetenciaPeriodo.objects.count() == 2


def test_borrar_el_anio_borra_sus_periodos_y_las_marcas(marca, anio_abierto):
    anio_abierto.delete()

    assert not CompetenciaPeriodo.objects.exists()
    assert not Periodo.objects.exists()
    assert not Seccion.objects.exists()


def test_borrar_la_seccion_borra_sus_marcas(marca, seccion, bimestre_1):
    seccion.delete()

    assert not CompetenciaPeriodo.objects.exists()
    assert Periodo.objects.filter(pk=bimestre_1.pk).exists()


def test_borrar_el_periodo_borra_sus_marcas(marca, seccion, bimestre_1):
    bimestre_1.delete()

    assert not CompetenciaPeriodo.objects.exists()
    assert Seccion.objects.filter(pk=seccion.pk).exists()


def test_borrar_una_competencia_con_marcas_falla(marca, competencia):
    with pytest.raises(RestrictedError), transaction.atomic():
        competencia.delete()

    assert Competencia.objects.filter(pk=competencia.pk).exists()
    assert CompetenciaPeriodo.objects.filter(pk=marca.pk).exists()
