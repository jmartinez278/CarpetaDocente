"""Guardar las competencias del periodo (specs competencias-periodo y registro-actividad; D5)."""

import datetime

import pytest
from django.core.exceptions import ValidationError

from actividad.models import Operacion, RegistroActividad
from catalogo.models import Competencia
from institucion.models import AnioEscolar, Periodo
from notas import servicios
from notas.models import CompetenciaPeriodo
from notas.tests.conftest import (
    CASTELLANO,
    COMUNICACION,
    INGLES,
    MATEMATICA,
    NOV_20,
    OCT_30,
    ids_de,
)

pytestmark = pytest.mark.django_db


def guardar(usuario, seccion, numero, ids, hoy=OCT_30, visto=None):
    """``visto`` es el universo que mostró la pantalla; por defecto, el de ahora."""
    if visto is None:
        visto = servicios.universo(usuario, seccion)
    return servicios.guardar_marcas(usuario, seccion, numero, ids, hoy=hoy, visto=visto)


def marcas(seccion, numero):
    return set(
        CompetenciaPeriodo.objects.filter(seccion=seccion, periodo__numero=numero).values_list(
            "competencia_id", flat=True
        )
    )


def entradas():
    return list(
        RegistroActividad.objects.filter(operacion=Operacion.COMPETENCIAS_MARCADAS).order_by("id")
    )


@pytest.fixture
def siete():
    """Las 4 de Matemática y las 3 de Comunicación (escenario «Camino ideal»)."""
    ids = ids_de(MATEMATICA, COMUNICACION)
    assert len(ids) == 7
    return ids


# --- Camino ideal, corrección e idempotencia ---


def test_primer_guardado_crea_las_marcas_y_deja_competencias_marcadas(
    docente, seccion_tutora, bimestres, universo_ie, siete
):
    cambios = guardar(docente, seccion_tutora, 3, siete)

    assert marcas(seccion_tutora, 3) == siete
    assert cambios.agregadas == sorted(siete)
    assert cambios.quitadas == []
    (entrada,) = entradas()
    assert entrada.usuario == docente
    assert (entrada.entidad, entrada.entidad_id) == ("seccion", str(seccion_tutora.pk))
    assert entrada.detalle == {"periodo": 3, "agregadas": sorted(siete), "quitadas": []}


def test_corregir_borra_la_quitada_y_deja_su_entrada(
    docente, seccion_tutora, bimestres, universo_ie, siete
):
    guardar(docente, seccion_tutora, 3, siete)
    quitada = min(siete)

    cambios = guardar(docente, seccion_tutora, 3, siete - {quitada})

    assert marcas(seccion_tutora, 3) == siete - {quitada}
    assert (cambios.agregadas, cambios.quitadas) == ([], [quitada])
    assert entradas()[-1].detalle == {"periodo": 3, "agregadas": [], "quitadas": [quitada]}


def test_corregir_un_periodo_anterior_no_toca_el_vigente(
    docente, seccion_tutora, bimestres, universo_ie, siete
):
    guardar(docente, seccion_tutora, 1, universo_ie)
    guardar(docente, seccion_tutora, 3, siete)

    guardar(docente, seccion_tutora, 1, universo_ie - {min(siete)})

    assert marcas(seccion_tutora, 1) == universo_ie - {min(siete)}
    assert marcas(seccion_tutora, 3) == siete


def test_el_mismo_envio_dos_veces_no_cambia_nada_ni_deja_entrada(
    docente, seccion_tutora, bimestres, universo_ie, siete
):
    guardar(docente, seccion_tutora, 3, siete)

    cambios = guardar(docente, seccion_tutora, 3, siete)

    assert (cambios.agregadas, cambios.quitadas) == ([], [])
    assert marcas(seccion_tutora, 3) == siete
    assert CompetenciaPeriodo.objects.count() == 7
    assert len(entradas()) == 1


# --- Periodos que no se marcan ---


def test_un_periodo_futuro_no_se_guarda(docente, seccion_tutora, bimestres, universo_ie, siete):
    with pytest.raises(servicios.PeriodoNoMarcable):
        guardar(docente, seccion_tutora, 4, siete)

    assert not CompetenciaPeriodo.objects.exists()
    assert entradas() == []


def test_en_un_anio_cerrado_no_se_guarda(
    docente, seccion_tutora, bimestres, universo_ie, siete, anio_abierto
):
    AnioEscolar.objects.filter(pk=anio_abierto.pk).update(estado=AnioEscolar.Estado.CERRADO)

    with pytest.raises(servicios.PeriodoNoMarcable):
        guardar(docente, seccion_tutora, 3, siete)

    assert not CompetenciaPeriodo.objects.exists()


def test_un_periodo_que_no_existe_no_se_guarda(docente, seccion_tutora, bimestres, siete):
    with pytest.raises(Periodo.DoesNotExist):
        guardar(docente, seccion_tutora, 5, siete)


def test_el_periodo_de_otro_anio_no_se_alcanza(docente, seccion_tutora, siete, institucion):
    """El periodo se busca en el año de la sección: el de otro año no sirve (D1)."""
    otro = AnioEscolar.objects.create(
        institucion=institucion, anio=2026, estado=AnioEscolar.Estado.CERRADO
    )
    Periodo.objects.create(
        anio_escolar=otro,
        numero=1,
        fecha_inicio=datetime.date(2026, 3, 9),
        fecha_fin=datetime.date(2026, 5, 15),
    )

    with pytest.raises(Periodo.DoesNotExist):
        guardar(docente, seccion_tutora, 1, siete)

    assert not CompetenciaPeriodo.objects.exists()


# --- Conjuntos que no se guardan ---


@pytest.mark.parametrize(
    "fuera", [lambda: min(ids_de(INGLES)), lambda: min(ids_de(CASTELLANO)), lambda: 999_999]
)
def test_una_competencia_fuera_del_universo_no_guarda_nada(
    docente, seccion_tutora, bimestres, universo_ie, siete, fuera
):
    with pytest.raises(ValidationError) as error:
        guardar(docente, seccion_tutora, 3, siete | {fuera()})

    assert error.value.messages == [servicios.CONJUNTO_NO_VALIDO]
    assert not CompetenciaPeriodo.objects.exists()
    assert entradas() == []


def test_otra_docente_no_guarda_nada(otra_docente, seccion_tutora, bimestres, siete):
    with pytest.raises(ValidationError):
        guardar(otra_docente, seccion_tutora, 3, siete)

    assert not CompetenciaPeriodo.objects.exists()


def test_un_conjunto_vacio_no_se_guarda(docente, seccion_tutora, bimestres, universo_ie, siete):
    guardar(docente, seccion_tutora, 3, siete)

    with pytest.raises(ValidationError) as error:
        guardar(docente, seccion_tutora, 3, [])

    assert error.value.messages == [servicios.SIN_MARCAS]
    assert error.value.messages == ["Marca al menos una competencia para guardar."]
    assert marcas(seccion_tutora, 3) == siete


# --- Obligatorias del último periodo ---


def test_en_el_bimestre_4_las_obligatorias_se_agregan_aunque_falten_en_el_envio(
    docente, seccion_tutora, bimestres, universo_ie
):
    faltan = set(sorted(universo_ie)[:5])
    for numero in (1, 2, 3):
        guardar(docente, seccion_tutora, numero, universo_ie - faltan, hoy=NOV_20)
    envio = {max(universo_ie)}

    cambios = guardar(docente, seccion_tutora, 4, envio, hoy=NOV_20)

    assert marcas(seccion_tutora, 4) == envio | faltan
    assert cambios.agregadas == sorted(envio | faltan)


def test_en_el_bimestre_4_un_envio_vacio_con_obligatorias_se_guarda(
    docente, seccion_tutora, bimestres, universo_ie
):
    faltan = set(sorted(universo_ie)[:5])
    for numero in (1, 2, 3):
        guardar(docente, seccion_tutora, numero, universo_ie - faltan, hoy=NOV_20)

    guardar(docente, seccion_tutora, 4, [], hoy=NOV_20)

    assert marcas(seccion_tutora, 4) == faltan


# --- Caso de error: competencia con notas ---


def test_quitar_una_competencia_con_notas_no_guarda_nada(
    docente, seccion_tutora, bimestres, universo_ie, siete, monkeypatch
):
    guardar(docente, seccion_tutora, 3, siete)
    con_notas = min(siete)
    monkeypatch.setattr(
        servicios,
        "tiene_notas",
        lambda seccion, periodo, competencia: competencia == con_notas,
    )
    otra_nueva = min(universo_ie - siete)

    with pytest.raises(servicios.CompetenciaConNotas) as error:
        guardar(docente, seccion_tutora, 3, (siete - {con_notas}) | {otra_nueva})

    assert error.value.competencias == [con_notas]
    assert str(error.value) == servicios.MENSAJE_CON_NOTAS
    assert servicios.MENSAJE_CON_NOTAS == "La competencia tiene notas registradas en este periodo"
    assert marcas(seccion_tutora, 3) == siete
    assert len(entradas()) == 1


# --- Marcas que la tutora no ve ---


def test_la_marca_de_una_competencia_desactivada_sigue_tras_guardar(
    docente, seccion_tutora, bimestres, universo_ie
):
    guardar(docente, seccion_tutora, 2, universo_ie)
    desactivada = Competencia.objects.get(area__codigo_siagie=MATEMATICA, orden=1)
    desactivada.activa = False
    desactivada.save()

    guardar(docente, seccion_tutora, 2, universo_ie - {desactivada.pk} - {max(universo_ie)})

    assert desactivada.pk in marcas(seccion_tutora, 2)
    assert max(universo_ie) not in marcas(seccion_tutora, 2)


def test_la_marca_de_un_area_a_cargo_sigue_tras_guardar(
    docente, seccion_tutora, bimestres, universo_ie, siete
):
    de_ingles = min(ids_de(INGLES))
    CompetenciaPeriodo.objects.create(
        seccion=seccion_tutora, periodo=bimestres[2], competencia_id=de_ingles
    )

    cambios = guardar(docente, seccion_tutora, 3, siete)

    assert marcas(seccion_tutora, 3) == siete | {de_ingles}
    assert de_ingles not in cambios.quitadas


# --- Universo que cambió con la pantalla abierta (escenario «Catálogo cambiado al guardar») ---


def test_una_competencia_reactivada_con_la_pantalla_abierta_no_pierde_su_marca(
    docente, seccion_tutora, bimestres, universo_ie
):
    guardar(docente, seccion_tutora, 2, universo_ie)
    reactivada = Competencia.objects.get(area__codigo_siagie=MATEMATICA, orden=1)
    reactivada.activa = False
    reactivada.save()
    visto = servicios.universo(docente, seccion_tutora)  # La pantalla abre sin ella.
    reactivada.activa = True
    reactivada.save()

    with pytest.raises(ValidationError) as error:
        guardar(docente, seccion_tutora, 2, visto - {max(visto)}, visto=visto)

    assert error.value.messages == [servicios.CONJUNTO_NO_VALIDO]
    assert marcas(seccion_tutora, 2) == universo_ie
    assert len(entradas()) == 1


def test_una_competencia_desactivada_con_la_pantalla_abierta_no_guarda_nada(
    docente, seccion_tutora, bimestres, universo_ie, siete
):
    visto = servicios.universo(docente, seccion_tutora)
    desactivada = Competencia.objects.get(area__codigo_siagie=COMUNICACION, orden=1)
    desactivada.activa = False
    desactivada.save()

    with pytest.raises(ValidationError) as error:
        guardar(docente, seccion_tutora, 3, siete - {desactivada.pk}, visto=visto)

    assert error.value.messages == [servicios.CONJUNTO_NO_VALIDO]
    assert not CompetenciaPeriodo.objects.exists()
