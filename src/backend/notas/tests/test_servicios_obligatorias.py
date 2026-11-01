"""Competencias obligatorias del último periodo y notas (spec competencias-periodo; D6, D7)."""

import datetime

import pytest

from catalogo.models import Competencia
from institucion.models import AnioEscolar, Institucion, Periodo, Seccion
from notas import servicios
from notas.tests.conftest import (
    EDUCACION_FISICA,
    INGLES,
    MATEMATICA,
    competencia,
    con_notas,
    marcar,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def cinco_sin_notas(seccion_tutora, bimestres, universo_ie):
    """Bimestres 1 a 3 marcados y con notas en todo el universo menos 5 competencias."""
    faltan = set(sorted(universo_ie)[:5])
    for periodo in bimestres[:3]:
        marcar(seccion_tutora, periodo, universo_ie - faltan)
        con_notas(seccion_tutora, periodo, universo_ie - faltan)
    return faltan


def test_flujo_alternativo_valido_en_el_bimestre_4_las_no_marcadas_antes(
    docente, seccion_tutora, bimestres, cinco_sin_notas
):
    obligatorias = servicios.competencias_obligatorias(docente, seccion_tutora, bimestres[3])

    assert obligatorias == cinco_sin_notas


def test_una_con_notas_en_un_solo_periodo_anterior_ya_no_es_obligatoria(
    docente, seccion_tutora, bimestres, cinco_sin_notas
):
    una = min(cinco_sin_notas)
    marcar(seccion_tutora, bimestres[1], [una])
    con_notas(seccion_tutora, bimestres[1], [una])

    obligatorias = servicios.competencias_obligatorias(docente, seccion_tutora, bimestres[3])

    assert obligatorias == cinco_sin_notas - {una}


def test_marcada_antes_sin_notas_sigue_siendo_obligatoria(
    docente, seccion_tutora, bimestres, cinco_sin_notas
):
    """Escenario «Marcada antes, sin notas»."""
    una = min(cinco_sin_notas)
    marcar(seccion_tutora, bimestres[1], [una])

    obligatorias = servicios.competencias_obligatorias(docente, seccion_tutora, bimestres[3])

    assert obligatorias == cinco_sin_notas


def test_las_notas_de_otra_seccion_no_cuentan(
    docente, seccion_tutora, bimestres, universo_ie, anio_abierto
):
    otra = Seccion.objects.create(anio_escolar=anio_abierto, grado=3, nombre="B")
    con_notas(otra, bimestres[0], universo_ie)

    obligatorias = servicios.competencias_obligatorias(docente, seccion_tutora, bimestres[3])

    assert obligatorias == universo_ie


def test_las_obligatorias_se_leen_en_dos_consultas(
    docente, seccion_tutora, bimestres, cinco_sin_notas, universo_ie, django_assert_num_queries
):
    """El último periodo (una) y las competencias con notas del año (una)."""
    with django_assert_num_queries(2):
        servicios.competencias_obligatorias(docente, seccion_tutora, bimestres[3], universo_ie)


def test_en_el_bimestre_3_ninguna_es_obligatoria(
    docente, seccion_tutora, bimestres, cinco_sin_notas
):
    assert servicios.competencias_obligatorias(docente, seccion_tutora, bimestres[2]) == set()


def test_en_un_anio_cerrado_ninguna_es_obligatoria(
    docente, seccion_tutora, bimestres, cinco_sin_notas, anio_abierto
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


# --- Notas de una competencia en el periodo ---


def test_una_sola_nota_basta(seccion_tutora, bimestres, ie):
    """Escenario «Una sola nota basta»: una «A» de C1 de Matemática en el bimestre 3."""
    c1 = competencia(MATEMATICA, 1).pk
    con_notas(seccion_tutora, bimestres[2], [c1])

    assert servicios.tiene_notas(seccion_tutora, bimestres[2], c1) is True
    assert servicios.competencias_con_notas(seccion_tutora, bimestres[2]) == {c1}


def test_las_notas_de_otro_periodo_no_cuentan(seccion_tutora, bimestres, ie):
    """Escenario «Notas de otro periodo»: C1 con notas en el bimestre 2 y ninguna en el 3."""
    c1 = competencia(MATEMATICA, 1).pk
    con_notas(seccion_tutora, bimestres[1], [c1])

    assert servicios.tiene_notas(seccion_tutora, bimestres[2], c1) is False
    assert servicios.competencias_con_notas(seccion_tutora, bimestres[2]) == set()


def test_las_notas_de_otra_seccion_no_cuentan_en_el_periodo(
    seccion_tutora, bimestres, ie, anio_abierto
):
    otra = Seccion.objects.create(anio_escolar=anio_abierto, grado=3, nombre="B")
    c1 = competencia(MATEMATICA, 1).pk
    con_notas(otra, bimestres[2], [c1])

    assert servicios.competencias_con_notas(seccion_tutora, bimestres[2]) == set()


def test_las_competencias_con_notas_se_leen_en_una_consulta(
    seccion_tutora, bimestres, ie, django_assert_num_queries
):
    con_notas(seccion_tutora, bimestres[2], sorted(ie)[:4])

    with django_assert_num_queries(1):
        con = servicios.competencias_con_notas(seccion_tutora, bimestres[2])

    assert con == set(sorted(ie)[:4])
