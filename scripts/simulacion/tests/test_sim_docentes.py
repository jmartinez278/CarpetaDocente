"""Docentes simuladas sim01…sim24 (G1)."""

import pytest

pytest.importorskip("numpy")
pytest.importorskip("yaml")

import numpy as np  # noqa: E402

from simulacion import docentes, parametros  # noqa: E402


@pytest.fixture
def valores():
    return parametros.valores(parametros.cargar())


def _generar(valores, semilla=7):
    return docentes.generar(valores, np.random.default_rng(semilla))


def test_genera_24_docentes_con_usuario_codigo_y_seccion_unicos(valores):
    lista = _generar(valores)
    assert len(lista) == 24
    assert [d.usuario for d in lista][:2] == ["sim01", "sim02"]
    assert lista[-1].usuario == "sim24"
    assert lista[0].codigo == "D01"
    assert len({(d.grado, d.seccion) for d in lista}) == 24
    assert (lista[0].grado, lista[0].seccion) == (1, "A")
    assert (lista[-1].grado, lista[-1].seccion) == (6, "D")


def test_misma_semilla_mismas_docentes(valores):
    assert _generar(valores, 3) == _generar(valores, 3)
    assert _generar(valores, 3) != _generar(valores, 4)


def test_rasgos_en_sus_dominios(valores):
    centro = valores["poblacion"]["estudiantes_centro"]
    amplitud = valores["poblacion"]["estudiantes_amplitud"]
    for d in _generar(valores):
        assert d.persona in ("P1", "P2", "P3")
        assert d.modalidad in ("momento", "diferido")
        assert d.medio_notas_o1 in ("cuaderno", "excel")
        assert d.ritmo > 0 and d.cuidado > 0
        assert centro - amplitud <= d.n_estudiantes <= centro + amplitud


def test_la_persona_sigue_a_la_destreza(valores):
    lista = _generar(valores)
    orden = {"P1": 0, "P2": 1, "P3": 2}
    por_destreza = sorted(lista, key=lambda d: d.destreza)
    rangos = [orden[d.persona] for d in por_destreza]
    assert rangos == sorted(rangos)


def test_proporciones_extremas_dan_una_sola_persona(valores):
    valores["rasgos"]["proporcion_p1"] = 0.0
    valores["rasgos"]["proporcion_p3"] = 0.0
    assert {d.persona for d in _generar(valores)} == {"P2"}


def test_proporciones_que_suman_mas_de_uno_se_rechazan(valores):
    valores["rasgos"]["proporcion_p1"] = 0.6
    valores["rasgos"]["proporcion_p3"] = 0.5
    with pytest.raises(ValueError, match="proporcion"):
        _generar(valores)


def test_correlacion_destreza_actitud_se_respeta_en_muestras_grandes(valores):
    valores["poblacion"]["n_docentes"] = 4000
    valores["poblacion"]["grados"] = 1000
    lista = _generar(valores)
    r = np.corrcoef([d.destreza for d in lista], [d.actitud for d in lista])[0, 1]
    assert r == pytest.approx(valores["rasgos"]["correlacion_destreza_actitud"], abs=0.05)
