"""Carga y validación de ``parametros.yaml`` (G1)."""

import pytest

pytest.importorskip("yaml")

from simulacion import parametros  # noqa: E402


def test_el_yaml_del_repo_es_valido():
    arbol = parametros.cargar()
    assert parametros.valor(arbol, "poblacion.n_docentes") == 24


def test_rechaza_un_parametro_sin_fuente_ni_supuesto():
    arbol = {"grupo": {"x": {"valor": 3}}}
    with pytest.raises(parametros.ParametroInvalido, match=r"grupo\.x"):
        parametros.validar(arbol)


def test_rechaza_un_supuesto_sin_ancla():
    arbol = {"x": {"valor": 3, "supuesto": True, "rango": [1, 5]}}
    with pytest.raises(parametros.ParametroInvalido, match="ancla"):
        parametros.validar(arbol)


def test_rechaza_un_supuesto_numerico_sin_rango():
    arbol = {"x": {"valor": 3, "supuesto": True, "ancla": "sin ancla"}}
    with pytest.raises(parametros.ParametroInvalido, match="rango"):
        parametros.validar(arbol)


def test_rechaza_un_valor_fuera_de_su_rango():
    arbol = {"x": {"valor": 9, "supuesto": True, "ancla": "sin ancla", "rango": [1, 5]}}
    with pytest.raises(parametros.ParametroInvalido, match="fuera"):
        parametros.validar(arbol)


def test_una_lista_numerica_se_valida_contra_el_rango():
    arbol = {"x": {"valor": [0, 7], "supuesto": True, "ancla": "sin ancla", "rango": [0, 5]}}
    with pytest.raises(parametros.ParametroInvalido, match="fuera"):
        parametros.validar(arbol)


def test_rechaza_fuente_y_supuesto_a_la_vez():
    arbol = {
        "x": {"valor": 1, "fuente": "Anexo 1", "supuesto": True, "ancla": "a", "rango": [0, 2]}
    }
    with pytest.raises(parametros.ParametroInvalido, match="ambos"):
        parametros.validar(arbol)


def test_acepta_un_parametro_con_fuente():
    parametros.validar({"g": {"x": {"valor": [1, 2], "fuente": "Anexo 4"}}})


def test_valores_quita_los_metadatos():
    arbol = {"g": {"x": {"valor": 2, "fuente": "f"}, "y": {"valor": "a", "fuente": "f"}}}
    assert parametros.valores(arbol) == {"g": {"x": 2, "y": "a"}}


def test_con_valor_cambia_uno_sin_tocar_el_original():
    arbol = {"g": {"x": {"valor": 2, "supuesto": True, "ancla": "a", "rango": [1, 3]}}}
    otro = parametros.con_valor(arbol, "g.x", 3)
    assert parametros.valor(otro, "g.x") == 3
    assert parametros.valor(arbol, "g.x") == 2


def test_supuestos_lista_cada_supuesto_con_su_rango():
    arbol = parametros.cargar()
    supuestos = dict(parametros.supuestos(arbol))
    assert supuestos["poblacion.estudiantes_centro"] == [25, 35]
    assert "poblacion.n_docentes" not in supuestos


def test_competencias_de_la_tutora_salen_del_catalogo():
    # Sin las áreas que no se trabajan (0002) ni las de docente de curso (0003, 031).
    assert parametros.competencias_tutora(["0003", "031"]) == 21
    assert parametros.competencias_tutora([]) == 27
