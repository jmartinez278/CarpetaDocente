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


# Rangos de O1 aprobados por Marco (DEC-1, 25-11-2026): amplios y redondos. Los valores no
# cambian; solo los rangos de sensibilidad.
RANGOS_DEC_1 = {
    "o1.sesion.elaboracion_mediana": [30, 180],
    "o1.sesion.entrega_mediana": [5, 60],
    "o1.notas.apertura": [1, 10],
    "o1.notas.por_estudiante_cuaderno": [0.1, 1],
    "o1.notas.por_estudiante_excel": [0.1, 1],
    "o1.notas.por_caracter_conclusion": [0.01, 0.05],
    "o1.asistencia.por_estudiante": [0.05, 0.5],
    "o1.asistencia.transcripcion_apertura": [0, 10],
    "o1.asistencia.transcripcion_por_estudiante": [0.05, 0.3],
    "o1.corregir_nota.probabilidad": [0, 0.5],
    "o1.corregir_nota.costo": [0.5, 5],
    "poblacion.tasa_excepciones_asistencia": [0, 0.3],
    "poblacion.proporcion_conclusion_notas": [0, 0.5],
    "poblacion.caracteres_conclusion": [10, 200],
    "errores_o1.notas.E1": [0, 0.05],
    "errores_o1.notas.E2_cuaderno": [0, 0.01],
    "errores_o1.notas.E2_excel": [0, 0.03],
    "errores_o1.notas.E3_cuaderno": [0, 0.05],
    "errores_o1.notas.E3_excel": [0, 0.03],
    "errores_o1.notas.E4": [0, 0.05],
    "errores_o1.asistencia.E1_momento": [0, 0.03],
    "errores_o1.asistencia.E1_diferido": [0, 0.05],
    "errores_o1.asistencia.E2": [0, 0.01],
    "errores_o1.asistencia.E3_momento": [0, 0.03],
    "errores_o1.asistencia.E3_diferido": [0, 0.1],
    "errores_o1.asistencia.E4_momento": [0, 0.02],
    "errores_o1.asistencia.E4_diferido": [0, 0.15],
    "errores_o1.asistencia.olvida_dia": [0, 0.15],
}


@pytest.mark.parametrize("ruta", RANGOS_DEC_1)
def test_los_rangos_de_o1_son_los_aprobados_y_el_valor_cae_dentro(ruta):
    arbol = parametros.cargar()
    nodo = parametros._nodo(arbol, ruta)
    assert nodo["rango"] == RANGOS_DEC_1[ruta]
    minimo, maximo = nodo["rango"]
    assert minimo <= nodo["valor"] <= maximo


def test_cada_supuesto_numerico_del_yaml_cae_en_su_rango():
    for ruta, rango in parametros.supuestos(parametros.cargar()):
        valor = parametros.valor(parametros.cargar(), ruta)
        numeros = valor if isinstance(valor, list) else [valor]
        assert all(rango[0] <= x <= rango[1] for x in numeros), ruta
