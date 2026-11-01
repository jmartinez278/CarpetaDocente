"""Lectura de la hoja, su periodo y las notas faltantes (spec registro-notas; D2, D3 y D4)."""

import pytest

from catalogo.models import InstitucionArea
from institucion.models import Estudiante
from notas import servicios
from notas.tests.conftest import (
    AGO_1,
    COMUNICACION,
    CONCLUSION,
    INGLES,
    MAR_2,
    MATEMATICA,
    NOV_20,
    OCT_30,
    competencia,
    crear_estudiantes,
    ids_de,
    marcar,
    poner_nota,
)

pytestmark = pytest.mark.django_db

ARTE = "0001"


@pytest.fixture
def lista(seccion_tutora):
    """Tres activos (en desorden), un trasladado y una retirada."""
    activos = crear_estudiantes(seccion_tutora, "ROJAS, MATEO", "ÁLVAREZ, LUCÍA", "CCAHUANA, PEDRO")
    trasladado = crear_estudiantes(
        seccion_tutora, "TORRES, IVÁN", estado=Estudiante.Estado.TRASLADADO
    )[0]
    retirada = crear_estudiantes(
        seccion_tutora, "VARGAS, ELENA", estado=Estudiante.Estado.RETIRADO
    )[0]
    return activos, trasladado, retirada


def hoja(docente, seccion, periodo, codigo):
    hojas = servicios.hoja_de_notas(docente, seccion, periodo)
    return next(h for h in hojas if h.area.codigo_siagie == codigo)


def area_institucion(seccion, codigo):
    return InstitucionArea.objects.select_related("area").get(
        institucion_id=seccion.anio_escolar.institucion_id, area__codigo_siagie=codigo
    )


# --- hoja_de_notas: columnas ---


def test_las_columnas_son_las_marcadas_con_su_numero_del_catalogo(
    docente, seccion_tutora, ie, bimestres
):
    """Escenario «Competencia sin marcar»: C1, C3 y C4 si C2 no se marcó."""
    c2 = competencia(MATEMATICA, 2).pk
    marcar(seccion_tutora, bimestres[2], ids_de(MATEMATICA) - {c2})

    matematica = hoja(docente, seccion_tutora, bimestres[2], MATEMATICA)

    assert [(c.etiqueta, c.competencia.orden) for c in matematica.columnas] == [
        ("C1", 1),
        ("C3", 3),
        ("C4", 4),
    ]
    assert matematica.total == 4
    assert matematica.columnas[0].competencia.nombre == "Resuelve problemas de cantidad"


def test_el_numero_es_la_posicion_entre_las_activas(docente, seccion_tutora, ie, bimestres):
    desactivada = competencia(MATEMATICA, 1)
    desactivada.activa = False
    desactivada.save()
    marcar(seccion_tutora, bimestres[2], ids_de(MATEMATICA))

    matematica = hoja(docente, seccion_tutora, bimestres[2], MATEMATICA)

    assert [(c.etiqueta, c.competencia.orden) for c in matematica.columnas] == [
        ("C1", 2),
        ("C2", 3),
        ("C3", 4),
    ]


def test_las_hojas_van_en_orden_siagie(docente, seccion_tutora, ie, bimestres):
    marcar(seccion_tutora, bimestres[2], ie)

    hojas = servicios.hoja_de_notas(docente, seccion_tutora, bimestres[2])

    ordenes = [h.area.orden for h in hojas]
    assert ordenes == sorted(ordenes)
    assert len(hojas) == 10


def test_el_area_a_cargo_va_sin_celdas(docente, seccion_tutora, ie, bimestres, lista):
    """Escenario «Área del docente de curso»."""
    marcar(seccion_tutora, bimestres[2], ie)

    ingles = hoja(docente, seccion_tutora, bimestres[2], INGLES)

    assert ingles.a_cargo and not ingles.marcable
    assert (ingles.columnas, ingles.filas, ingles.solo_lectura, ingles.notas) == ([], [], [], {})


def test_la_marcable_sin_marcas_va_sin_celdas(docente, seccion_tutora, ie, bimestres, lista):
    """Escenario «Área sin competencias marcadas»: otras áreas sí tienen marcas."""
    marcar(seccion_tutora, bimestres[2], ids_de(MATEMATICA))

    arte = hoja(docente, seccion_tutora, bimestres[2], ARTE)

    assert arte.marcable and not arte.a_cargo
    assert (arte.columnas, arte.filas, arte.solo_lectura) == ([], [], [])


# --- hoja_de_notas: filas y notas ---


def test_las_filas_son_los_activos_por_apellidos(docente, seccion_tutora, ie, bimestres, lista):
    marcar(seccion_tutora, bimestres[2], ids_de(MATEMATICA))

    matematica = hoja(docente, seccion_tutora, bimestres[2], MATEMATICA)

    assert [e.apellidos for e in matematica.filas] == ["ÁLVAREZ", "CCAHUANA", "ROJAS"]


def test_el_trasladado_con_notas_va_al_final_y_la_retirada_sin_notas_no(
    docente, seccion_tutora, ie, bimestres, lista
):
    """Escenarios «Trasladado con notas» y «Retirado sin notas»."""
    _, trasladado, retirada = lista
    marcar(seccion_tutora, bimestres[2], ids_de(MATEMATICA, COMUNICACION))
    c4 = competencia(MATEMATICA, 4).pk
    poner_nota(trasladado, c4, bimestres[2], "C")
    poner_nota(retirada, competencia(COMUNICACION, 1), bimestres[2], "A")

    matematica = hoja(docente, seccion_tutora, bimestres[2], MATEMATICA)
    comunicacion = hoja(docente, seccion_tutora, bimestres[2], COMUNICACION)

    assert matematica.solo_lectura == [trasladado]
    assert retirada not in matematica.solo_lectura + matematica.filas
    assert matematica.notas[(trasladado.pk, c4)] == ("C", CONCLUSION)
    assert comunicacion.solo_lectura == [retirada]


def test_las_notas_de_otro_periodo_no_entran(docente, seccion_tutora, ie, bimestres, lista):
    activo = lista[0][0]
    c1 = competencia(MATEMATICA, 1).pk
    marcar(seccion_tutora, bimestres[1], ids_de(MATEMATICA))
    marcar(seccion_tutora, bimestres[2], ids_de(MATEMATICA))
    poner_nota(activo, c1, bimestres[1], "AD")
    poner_nota(activo, c1, bimestres[2], "A")

    matematica = hoja(docente, seccion_tutora, bimestres[2], MATEMATICA)

    assert matematica.notas == {(activo.pk, c1): ("A", "")}


def test_la_hoja_se_lee_en_un_numero_fijo_de_consultas(
    docente, seccion_tutora, ie, bimestres, lista, django_assert_num_queries
):
    """Con las 10 áreas, sin consultas por área ni por celda (D2)."""
    marcar(seccion_tutora, bimestres[2], ie)
    activos, trasladado, _ = lista
    for estudiante in [*activos, trasladado]:
        for id_ in sorted(ie)[:6]:
            poner_nota(estudiante, id_, bimestres[2], "A")

    with django_assert_num_queries(5):
        hojas = servicios.hoja_de_notas(docente, seccion_tutora, bimestres[2])
        celdas = sum(len(h.notas) for h in hojas)

    assert celdas == 24


# --- periodo_de_la_hoja (D3) ---


def periodo(seccion, pedido, hoy):
    periodos = servicios.periodos_de_la_seccion(seccion, hoy)
    elegido = servicios.periodo_de_la_hoja(periodos, pedido)
    return elegido.numero if elegido else None


def test_sin_pedido_abre_el_vigente(seccion_tutora, bimestres):
    """Escenario «Abre en el vigente»."""
    assert periodo(seccion_tutora, None, OCT_30) == 3


def test_un_periodo_anterior_pedido(seccion_tutora, bimestres):
    """Escenario «Periodo anterior pedido»."""
    assert periodo(seccion_tutora, "1", OCT_30) == 1


def test_un_periodo_futuro_pedido_abre_el_vigente(seccion_tutora, bimestres):
    """Escenario «Periodo futuro pedido»."""
    assert periodo(seccion_tutora, "4", OCT_30) == 3


def test_un_pedido_que_no_es_un_numero_abre_el_vigente(seccion_tutora, bimestres):
    assert periodo(seccion_tutora, "tres", OCT_30) == 3


def test_en_vacaciones_abre_el_ultimo_anterior(seccion_tutora, bimestres):
    """Escenario «Vacaciones»: el 1 de agosto, entre el B2 y el B3."""
    assert periodo(seccion_tutora, None, AGO_1) == 2


def test_tras_el_ultimo_vigente_abre_el_ultimo_anterior(seccion_tutora, bimestres):
    assert periodo(seccion_tutora, None, NOV_20) == 4


def test_antes_del_primero_no_abre_ninguno(seccion_tutora, bimestres):
    """Escenario «Antes del primer periodo»."""
    assert periodo(seccion_tutora, None, MAR_2) is None
    assert periodo(seccion_tutora, "1", MAR_2) is None


def test_sin_periodos_no_abre_ninguno(seccion_tutora):
    """Escenario «Sin periodos»."""
    assert periodo(seccion_tutora, None, OCT_30) is None


# --- notas_faltantes (D4) ---


def test_cuenta_notas_y_no_estudiantes(
    docente, seccion_tutora, ie, bimestres, lista, django_assert_num_queries
):
    """Escenario «Conteo por notas»: uno sin C1 ni C3, otro sin C2."""
    activos, _, _ = lista
    ids = [competencia(MATEMATICA, n).pk for n in (1, 2, 3, 4)]
    marcar(seccion_tutora, bimestres[2], ids)
    primero, segundo, tercero = activos
    for id_ in ids:
        poner_nota(tercero, id_, bimestres[2])
    poner_nota(primero, ids[1], bimestres[2])
    poner_nota(primero, ids[3], bimestres[2])
    poner_nota(segundo, ids[0], bimestres[2])
    poner_nota(segundo, ids[2], bimestres[2])
    poner_nota(segundo, ids[3], bimestres[2])
    area = area_institucion(seccion_tutora, MATEMATICA)

    with django_assert_num_queries(1):
        faltantes = servicios.notas_faltantes(docente, seccion_tutora, bimestres[2], area)

    assert sorted(faltantes) == sorted(
        [(primero.pk, ids[0]), (primero.pk, ids[2]), (segundo.pk, ids[1])]
    )


def test_el_trasladado_sin_nivel_no_cuenta(docente, seccion_tutora, ie, bimestres, lista):
    """Escenario «Trasladado sin nivel»."""
    activos, trasladado, _ = lista
    c4 = competencia(MATEMATICA, 4).pk
    marcar(seccion_tutora, bimestres[2], [c4])
    poner_nota(trasladado, competencia(MATEMATICA, 1), bimestres[1], "A")
    area = area_institucion(seccion_tutora, MATEMATICA)

    faltantes = servicios.notas_faltantes(docente, seccion_tutora, bimestres[2], area)

    assert sorted(faltantes) == sorted((e.pk, c4) for e in activos)


def test_las_competencias_sin_marcar_no_cuentan(docente, seccion_tutora, ie, bimestres, lista):
    marcar(seccion_tutora, bimestres[2], [competencia(MATEMATICA, 1).pk])
    marcar(seccion_tutora, bimestres[1], ids_de(MATEMATICA))
    area = area_institucion(seccion_tutora, MATEMATICA)

    faltantes = servicios.notas_faltantes(docente, seccion_tutora, bimestres[2], area)

    assert len(faltantes) == 3
    assert {c for _, c in faltantes} == {competencia(MATEMATICA, 1).pk}


def test_las_de_otra_area_no_cuentan(docente, seccion_tutora, ie, bimestres, lista):
    marcar(seccion_tutora, bimestres[2], ids_de(MATEMATICA, COMUNICACION))
    area = area_institucion(seccion_tutora, COMUNICACION)

    faltantes = servicios.notas_faltantes(docente, seccion_tutora, bimestres[2], area)

    assert len(faltantes) == 9
    assert {c for _, c in faltantes} == ids_de(COMUNICACION)


def test_el_area_a_cargo_no_tiene_faltantes(docente, seccion_tutora, ie, bimestres, lista):
    marcar(seccion_tutora, bimestres[2], ids_de(INGLES))
    area = area_institucion(seccion_tutora, INGLES)

    assert servicios.notas_faltantes(docente, seccion_tutora, bimestres[2], area) == []


def test_en_el_ultimo_bimestre_las_obligatorias_cuentan(docente, seccion_tutora, ie, bimestres):
    """Escenario «Último bimestre»: 25 activos sin nivel en una obligatoria marcada."""
    crear_estudiantes(seccion_tutora, *(f"APELLIDO {chr(65 + n)}, NOMBRE" for n in range(25)))
    obligatoria = competencia(MATEMATICA, 2).pk
    assert obligatoria in servicios.competencias_obligatorias(docente, seccion_tutora, bimestres[3])
    marcar(seccion_tutora, bimestres[3], [obligatoria])
    area = area_institucion(seccion_tutora, MATEMATICA)

    faltantes = servicios.notas_faltantes(docente, seccion_tutora, bimestres[3], area)

    assert len(faltantes) == 25
