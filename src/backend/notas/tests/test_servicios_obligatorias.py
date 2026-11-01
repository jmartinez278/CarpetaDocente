"""Competencias obligatorias del último periodo y notas (spec competencias-periodo; D6, D7)."""

import datetime

import pytest

from catalogo.models import Competencia
from institucion.models import AnioEscolar, Institucion, Periodo
from notas import servicios
from notas.models import CompetenciaPeriodo
from notas.tests.conftest import EDUCACION_FISICA, INGLES

pytestmark = pytest.mark.django_db


def marcar(seccion, periodo, ids):
    CompetenciaPeriodo.objects.bulk_create(
        CompetenciaPeriodo(seccion=seccion, periodo=periodo, competencia_id=i) for i in ids
    )


@pytest.fixture
def cinco_sin_marcar(seccion_tutora, bimestres, universo_ie):
    """Bimestres 1 a 3 marcados con todo el universo menos 5 competencias."""
    faltan = set(sorted(universo_ie)[:5])
    for periodo in bimestres[:3]:
        marcar(seccion_tutora, periodo, universo_ie - faltan)
    return faltan


def test_flujo_alternativo_valido_en_el_bimestre_4_las_no_marcadas_antes(
    docente, seccion_tutora, bimestres, cinco_sin_marcar
):
    obligatorias = servicios.competencias_obligatorias(docente, seccion_tutora, bimestres[3])

    assert obligatorias == cinco_sin_marcar


def test_una_marcada_en_un_solo_periodo_anterior_ya_no_es_obligatoria(
    docente, seccion_tutora, bimestres, cinco_sin_marcar
):
    una = min(cinco_sin_marcar)
    marcar(seccion_tutora, bimestres[1], [una])

    obligatorias = servicios.competencias_obligatorias(docente, seccion_tutora, bimestres[3])

    assert obligatorias == cinco_sin_marcar - {una}


def test_en_el_bimestre_3_ninguna_es_obligatoria(
    docente, seccion_tutora, bimestres, cinco_sin_marcar
):
    assert servicios.competencias_obligatorias(docente, seccion_tutora, bimestres[2]) == set()


def test_en_un_anio_cerrado_ninguna_es_obligatoria(
    docente, seccion_tutora, bimestres, cinco_sin_marcar, anio_abierto
):
    AnioEscolar.objects.filter(pk=anio_abierto.pk).update(estado=AnioEscolar.Estado.CERRADO)
    seccion_tutora.anio_escolar.refresh_from_db()

    assert servicios.competencias_obligatorias(docente, seccion_tutora, bimestres[3]) == set()


def test_las_areas_del_docente_de_curso_nunca_son_obligatorias(
    docente, seccion_tutora, bimestres, universo_ie
):
    obligatorias = servicios.competencias_obligatorias(docente, seccion_tutora, bimestres[3])

    de_curso = set(
        Competencia.objects.filter(area__codigo_siagie__in=[INGLES, EDUCACION_FISICA]).values_list(
            "pk", flat=True
        )
    )
    assert obligatorias == universo_ie
    assert not obligatorias & de_curso


def test_con_trimestres_el_ultimo_es_el_3(
    docente, seccion_tutora, institucion, anio_abierto, universo_ie
):
    institucion.organizacion_periodos = Institucion.OrganizacionPeriodos.TRIMESTRE
    institucion.save()
    trimestres = [
        Periodo.objects.create(
            anio_escolar=anio_abierto,
            numero=numero,
            fecha_inicio=datetime.date(2027, mes, 1),
            fecha_fin=datetime.date(2027, mes + 2, 28),
        )
        for numero, mes in [(1, 3), (2, 6), (3, 9)]
    ]

    assert servicios.competencias_obligatorias(docente, seccion_tutora, trimestres[1]) == set()
    assert servicios.competencias_obligatorias(docente, seccion_tutora, trimestres[2]) == (
        universo_ie
    )


def test_tiene_notas_es_falso_hasta_us_020(seccion_tutora, bimestres, universo_ie):
    assert servicios.tiene_notas(seccion_tutora, bimestres[0], min(universo_ie)) is False
