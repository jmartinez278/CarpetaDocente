"""Mediciones O1 y O2 por docente (G1): tiempos, E1–E4, Likert, SUS y Anexo 2."""

import pytest

pytest.importorskip("numpy")
pytest.importorskip("yaml")

import numpy as np  # noqa: E402

from simulacion import medicion, parametros  # noqa: E402

PERSONAS = ("P1", "P2", "P3")


def _klm_de_prueba():
    """Tabla KLM falsa, solo para probar la mecánica; la real la entrega G2."""
    tareas = {
        "sesion_entrega": {"fijo": 1.0, "por_estudiante": 0.0},
        "notas": {"fijo": 0.5, "por_estudiante": 0.05},
        "asistencia_momento": {"fijo": 0.3, "por_estudiante": 0.03},
        "asistencia_diferido": {"fijo": 0.6, "por_estudiante": 0.03},
        "corregir_nota": {"fijo": 0.2, "por_estudiante": 0.0},
    }
    return {p: dict(tareas) for p in PERSONAS}


@pytest.fixture
def valores():
    return parametros.valores(parametros.cargar())


def _simular(valores, semilla=11, klm=None):
    return medicion.simular(valores, semilla, klm or _klm_de_prueba())


def test_misma_semilla_misma_salida(valores):
    assert _simular(valores, 5) == _simular(valores, 5)
    assert _simular(valores, 5) != _simular(valores, 6)


def test_una_fila_por_docente_y_momento(valores):
    resultado = _simular(valores)
    assert len(resultado.filas) == 48
    assert {f["momento"] for f in resultado.filas} == {"pretest", "postest"}
    assert len(resultado.docentes) == 24


def test_o2_no_corre_sin_la_tabla_klm(valores):
    with pytest.raises(medicion.KLMFaltante):
        medicion.simular(valores, 1, None)


def test_o2_no_corre_si_falta_una_tarea_en_la_tabla(valores):
    klm = _klm_de_prueba()
    del klm["P1"]["notas"]
    with pytest.raises(medicion.KLMFaltante, match="P1.*notas"):
        medicion.simular(valores, 1, klm)


def test_sesion_es_elaboracion_mas_entrega(valores):
    for fila in _simular(valores).filas:
        total = fila["sesion_elaboracion_min"] + fila["sesion_entrega_min"]
        assert fila["sesion_min"] == pytest.approx(total)


def test_la_elaboracion_tiene_la_misma_distribucion_en_o1_y_o2(valores):
    valores["poblacion"]["n_docentes"] = 4000
    valores["poblacion"]["grados"] = 1000
    filas = _simular(valores).filas
    pre = np.log([f["sesion_elaboracion_min"] for f in filas if f["momento"] == "pretest"])
    post = np.log([f["sesion_elaboracion_min"] for f in filas if f["momento"] == "postest"])
    assert abs(pre.mean() - post.mean()) < 0.02


def test_asistencia_promedia_cinco_jornadas(valores):
    for fila in _simular(valores).filas:
        assert len(fila["asistencia_jornadas_min"]) == 5
        assert fila["asistencia_min"] == pytest.approx(np.mean(fila["asistencia_jornadas_min"]))


def test_o2_toma_sus_tiempos_de_la_tabla_klm(valores):
    lenta = _klm_de_prueba()
    for persona in PERSONAS:
        lenta[persona]["sesion_entrega"] = {"fijo": 100.0, "por_estudiante": 0.0}
    rapida = _simular(valores, 3).filas
    con_lenta = _simular(valores, 3, lenta).filas
    post = [f for f in con_lenta if f["momento"] == "postest"]
    post_rapida = [f for f in rapida if f["momento"] == "postest"]
    for lento, rapido in zip(post, post_rapida, strict=True):
        assert lento["sesion_entrega_min"] == pytest.approx(rapido["sesion_entrega_min"] * 100)


def test_exactitud_es_c_entre_a(valores):
    for fila in _simular(valores).filas:
        for dim in ("notas", "asistencia"):
            a = fila[f"{dim}_revisados"]
            b = fila[f"{dim}_con_error"]
            errores = sum(fila[f"{dim}_E{i}"] for i in range(1, 5))
            assert b == errores  # un registro con varios errores cuenta una vez
            assert 0 <= b <= a
            assert fila[f"{dim}_exactitud"] == pytest.approx((a - b) / a * 100)
            assert 0 <= fila[f"{dim}_exactitud"] <= 100


def test_registros_revisados_siguen_al_anexo_3(valores):
    resultado = _simular(valores)
    competencias = parametros.competencias_tutora(valores["catalogo"]["areas_de_docente_de_curso"])
    por_codigo = {d.codigo: d for d in resultado.docentes}
    for fila in resultado.filas:
        n = por_codigo[fila["codigo"]].n_estudiantes
        assert fila["notas_revisados"] == n * competencias
        assert fila["asistencia_revisados"] == n * 5


def test_lo_que_la_app_impide_no_aparece_en_o2(valores):
    valores["poblacion"]["n_docentes"] = 400
    valores["poblacion"]["grados"] = 100
    post = [f for f in _simular(valores).filas if f["momento"] == "postest"]
    assert all(f["notas_E2"] == 0 and f["asistencia_E2"] == 0 for f in post)


def test_e4_de_asistencia_en_o2_solo_en_diferido(valores):
    valores["poblacion"]["n_docentes"] = 400
    valores["poblacion"]["grados"] = 100
    valores["errores_o2"]["asistencia"]["E4_diferido"] = 0.5
    resultado = _simular(valores)
    modalidad = {d.codigo: d.modalidad for d in resultado.docentes}
    post = [f for f in resultado.filas if f["momento"] == "postest"]
    assert all(f["asistencia_E4"] == 0 for f in post if modalidad[f["codigo"]] == "momento")
    assert any(f["asistencia_E4"] > 0 for f in post if modalidad[f["codigo"]] == "diferido")


def test_el_medio_de_o1_cambia_e2_y_e3(valores):
    valores["poblacion"]["n_docentes"] = 2000
    valores["poblacion"]["grados"] = 500
    resultado = _simular(valores)
    medio = {d.codigo: d.medio_notas_o1 for d in resultado.docentes}
    pre = [f for f in resultado.filas if f["momento"] == "pretest"]

    def tasa(medio_buscado, error):
        filas = [f for f in pre if medio[f["codigo"]] == medio_buscado]
        return sum(f[f"notas_{error}"] for f in filas) / sum(f["notas_revisados"] for f in filas)

    assert tasa("cuaderno", "E3") > tasa("excel", "E3")
    assert tasa("excel", "E2") > tasa("cuaderno", "E2")


def test_likert_en_sus_rangos_y_niveles(valores):
    for fila in _simular(valores).filas:
        items = [fila[f"likert_{i}"] for i in range(1, 16)]
        assert all(1 <= x <= 5 for x in items)
        for d, dim in enumerate(("planificacion", "notas", "asistencia")):
            puntaje = fila[f"likert_{dim}"]
            assert puntaje == sum(items[d * 5 : d * 5 + 5])
            assert 5 <= puntaje <= 25
            assert fila[f"likert_{dim}_nivel"] in ("desfavorable", "regular", "favorable")
        assert fila["likert_global"] == sum(items)
        assert 15 <= fila["likert_global"] <= 75


def test_nivel_likert_sigue_los_cortes_del_anexo_4():
    niveles = {"desfavorable": [5, 11], "regular": [12, 18], "favorable": [19, 25]}
    assert medicion.nivel(11, niveles) == "desfavorable"
    assert medicion.nivel(12, niveles) == "regular"
    assert medicion.nivel(19, niveles) == "favorable"


def test_sus_solo_en_el_postest_y_entre_0_y_100(valores):
    for fila in _simular(valores).filas:
        if fila["momento"] == "pretest":
            assert fila["sus"] is None
        else:
            assert 0 <= fila["sus"] <= 100
            assert fila["sus"] % 2.5 == 0


def test_puntaje_sus_con_la_formula_estandar():
    assert medicion.puntaje_sus([5, 1] * 5) == 100
    assert medicion.puntaje_sus([1, 5] * 5) == 0
    assert medicion.puntaje_sus([3] * 10) == 50


def test_autorregistro_del_anexo_2(valores):
    for fila in _simular(valores).filas:
        assert fila["autorregistro_sesiones"] >= 0
        if fila["autorregistro_sesiones"] == 0:
            assert fila["autorregistro_total_min"] == 0
        else:
            assert fila["autorregistro_total_min"] > 0


def test_cada_fila_dice_datos_simulados(valores):
    assert all(f["origen"] == "Datos simulados" for f in _simular(valores).filas)
