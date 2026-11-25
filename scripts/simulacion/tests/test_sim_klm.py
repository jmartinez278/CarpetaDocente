"""Rutas de los agentes y conversión a operadores KLM (G2). Datos simulados.

Los tiempos salen de operadores KLM (SUPUESTO sin ancla), nunca del reloj del agente. El KLM
cubre solo la ruta ideal que el agente ejecutó: desvíos y confusiones se registran aparte.
"""

import copy
from pathlib import Path

import pytest

pytest.importorskip("numpy")
pytest.importorskip("yaml")

import yaml  # noqa: E402

from simulacion import klm, medicion, parametros  # noqa: E402

PERSONAS = ("P1", "P2", "P3")
OPERADORES = {"K": 0.2, "P": 1.1, "B": 0.1, "H": 0.4, "M": 1.35, "R_domestica": 1.0}
OPERADORES |= {"R_slow_4g": 3.0}
AGENTES = Path(__file__).resolve().parents[1] / "agentes"


def _paso(accion, objetivo="un objetivo", **marcas):
    return {"accion": accion, "objetivo": objetivo, **marcas}


def _ruta(persona="P1", tarea="notas", pasos=None, **extra):
    base = {
        "persona": persona,
        "tarea": tarea,
        "exito": True,
        "errores": [],
        "confusiones": [],
        "pasos": pasos if pasos is not None else _pasos_notas(),
    }
    return base | extra


def _pasos_notas():
    return [
        _paso("clic", inicia_subtarea=True),  # M + B
        _paso("apuntar", decision=True),  # M + P
        _paso("espera"),  # R
        _paso("tap", por_estudiante=True),  # P + B
        _paso("tecla", por_estudiante=True),  # K
        _paso("espera", verifica=True),  # R + M
    ]


@pytest.fixture
def valores():
    v = parametros.valores(parametros.cargar())
    v["o2"]["operadores_klm"] = dict(OPERADORES)
    v["poblacion"]["tasa_excepciones_asistencia"] = 0.1
    v["poblacion"]["proporcion_conclusion_notas"] = 0.25
    v["poblacion"]["caracteres_conclusion"] = 40
    return v


def _tabla_completa(valores, **cambios):
    rutas = [
        _ruta(p, t, **cambios) for p in PERSONAS for t in medicion.TAREAS_KLM
    ]  # fmt: skip
    return klm.construir_tabla(rutas, valores)


# ── validación de la ruta ────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("campo", ["segundos", "duracion", "tiempo", "ms", "reloj"])
def test_una_ruta_con_tiempo_del_reloj_se_rechaza(campo):
    with pytest.raises(klm.RutaInvalida, match=campo):
        klm.validar_ruta(_ruta(**{campo: 12.5}))
    paso = _paso("clic", **{campo: 3})
    with pytest.raises(klm.RutaInvalida, match=campo):
        klm.validar_ruta(_ruta(pasos=[paso]))


def test_una_accion_desconocida_se_rechaza():
    with pytest.raises(klm.RutaInvalida, match="accion"):
        klm.validar_ruta(_ruta(pasos=[_paso("telepatia")]))


def test_un_paso_sin_objetivo_se_rechaza():
    with pytest.raises(klm.RutaInvalida, match="objetivo"):
        klm.validar_ruta(_ruta(pasos=[{"accion": "clic"}]))


def test_una_ruta_sin_pasos_se_rechaza():
    with pytest.raises(klm.RutaInvalida, match="pasos"):
        klm.validar_ruta(_ruta(pasos=[]))


def test_persona_o_tarea_desconocida_se_rechaza():
    with pytest.raises(klm.RutaInvalida, match="persona"):
        klm.validar_ruta(_ruta(persona="P9"))
    with pytest.raises(klm.RutaInvalida, match="tarea"):
        klm.validar_ruta(_ruta(tarea="inventada"))


@pytest.mark.parametrize("campo", ["exito", "errores", "confusiones"])
def test_la_ruta_registra_exito_errores_y_confusiones(campo):
    ruta = _ruta()
    del ruta[campo]
    with pytest.raises(klm.RutaInvalida, match=campo):
        klm.validar_ruta(ruta)


def test_una_ruta_valida_pasa():
    klm.validar_ruta(_ruta())


# ── conversión a operadores ──────────────────────────────────────────────────────────────────


def test_cada_accion_equivale_a_sus_operadores():
    assert klm.operadores_de(_ruta(pasos=[_paso("tecla")])) == [("K", "fijo")]
    assert klm.operadores_de(_ruta(pasos=[_paso("apuntar")])) == [("P", "fijo")]
    assert klm.operadores_de(_ruta(pasos=[_paso("clic")])) == [("B", "fijo")]
    assert klm.operadores_de(_ruta(pasos=[_paso("tap")])) == [("P", "fijo"), ("B", "fijo")]
    assert klm.operadores_de(_ruta(pasos=[_paso("manos")])) == [("H", "fijo")]
    assert klm.operadores_de(_ruta(pasos=[_paso("espera")])) == [("R", "fijo")]


def test_m_al_iniciar_una_subtarea():
    ops = klm.operadores_de(_ruta(pasos=[_paso("clic", inicia_subtarea=True)]))
    assert ops == [("M", "fijo"), ("B", "fijo")]


def test_m_antes_de_una_decision():
    ops = klm.operadores_de(_ruta(pasos=[_paso("apuntar", decision=True)]))
    assert ops == [("M", "fijo"), ("P", "fijo")]


def test_m_al_verificar_un_aviso_del_sistema():
    ops = klm.operadores_de(_ruta(pasos=[_paso("espera", verifica=True)]))
    assert ("M", "fijo") in ops and ("R", "fijo") in ops


def test_un_paso_con_varias_marcas_lleva_una_sola_m():
    paso = _paso("clic", inicia_subtarea=True, decision=True, verifica=True)
    ops = klm.operadores_de(_ruta(pasos=[paso]))
    assert [o for o, _ in ops].count("M") == 1


def test_sin_m_en_la_secuencia_repetida_por_estudiante():
    paso = _paso("tap", por_estudiante=True, inicia_subtarea=True, decision=True, verifica=True)
    ops = klm.operadores_de(_ruta(pasos=[paso]))
    assert ops == [("P", "por_estudiante"), ("B", "por_estudiante")]


def test_los_desvios_no_entran_a_los_operadores():
    pasos = [_paso("clic"), _paso("clic", "botón equivocado", desvio=True), _paso("tecla")]
    assert klm.operadores_de(_ruta(pasos=pasos)) == [("B", "fijo"), ("K", "fijo")]


# ── tiempo ───────────────────────────────────────────────────────────────────────────────────


def test_tiempo_de_una_ruta_calculado_a_mano(valores):
    # fijo (s): M+B 1,45 · M+P 2,45 · R 1,0 · R+M 2,35 = 7,25 · por estudiante: P+B+K = 1,4
    celda = klm.tiempo_ruta(_ruta(), valores)
    assert celda["fijo"] == pytest.approx(7.25 / 60)
    assert celda["por_estudiante"] == pytest.approx(1.4 / 60)


def test_el_resultado_es_en_minutos_con_fijo_y_por_estudiante(valores):
    assert set(klm.tiempo_ruta(_ruta(), valores)) == {"fijo", "por_estudiante"}


def test_la_respuesta_del_sistema_sigue_el_contexto_de_la_tarea(valores):
    # asistencia: celular con Slow 4G; notas y sesión: conexión doméstica (contexto_tarea)
    pasos = [_paso("espera")]
    notas = klm.tiempo_ruta(_ruta(tarea="notas", pasos=pasos), valores)
    asistencia = klm.tiempo_ruta(_ruta(tarea="asistencia_momento", pasos=pasos), valores)
    sesion = klm.tiempo_ruta(_ruta(tarea="sesion_entrega", pasos=pasos), valores)
    diferido = klm.tiempo_ruta(_ruta(tarea="asistencia_diferido", pasos=pasos), valores)
    assert notas["fijo"] == pytest.approx(1.0 / 60)
    assert sesion["fijo"] == pytest.approx(1.0 / 60)
    assert asistencia["fijo"] == pytest.approx(3.0 / 60)
    assert diferido["fijo"] == pytest.approx(3.0 / 60)


def test_cambiar_un_operador_cambia_la_tabla(valores):
    antes = klm.tiempo_ruta(_ruta(), valores)
    valores["o2"]["operadores_klm"]["M"] = 2.0
    assert klm.tiempo_ruta(_ruta(), valores)["fijo"] > antes["fijo"]


def test_una_ruta_con_confusiones_da_la_misma_tabla_que_sin_ellas(valores):
    limpia = _ruta()
    sucia = copy.deepcopy(limpia)
    sucia["confusiones"] = [
        {"paso": 2, "esperaba": "un botón Guardar", "paso_real": "tuvo que buscarlo"}
    ]
    sucia["errores"] = ["E3"]
    sucia["exito"] = False
    sucia["pasos"].insert(2, _paso("clic", "botón equivocado", desvio=True))
    sucia["pasos"].insert(3, _paso("tecla", "texto sobrante", desvio=True))
    assert klm.tiempo_ruta(sucia, valores) == klm.tiempo_ruta(limpia, valores)
    assert klm.construir_tabla([sucia], valores) == klm.construir_tabla([limpia], valores)


def test_las_confusiones_se_cuentan_como_hallazgos():
    ruta = _ruta(confusiones=[{"paso": 1, "esperaba": "a", "paso_real": "b"}, {"paso": 3}])
    assert klm.hallazgos([ruta, _ruta()]) == [
        {"persona": "P1", "tarea": "notas", "confusiones": 2, "errores": 0, "exito": True}
    ]


def test_la_misma_ruta_da_siempre_la_misma_celda(valores):
    assert klm.tiempo_ruta(_ruta(), valores) == klm.tiempo_ruta(_ruta(), valores)


# ── pasos por excepción (marcado masivo + quienes no asistieron) ────────────────────────────


def test_un_paso_por_excepcion_se_convierte_en_su_propio_ambito():
    ops = klm.operadores_de(_ruta(pasos=[_paso("tap", por_excepcion=True)]))
    assert ops == [("P", "por_excepcion"), ("B", "por_excepcion")]


def test_sin_m_en_los_pasos_por_excepcion():
    paso = _paso("tap", por_excepcion=True, inicia_subtarea=True, decision=True, verifica=True)
    assert ("M", "fijo") not in klm.operadores_de(_ruta(pasos=[paso]))
    assert all(a == "por_excepcion" for _, a in klm.operadores_de(_ruta(pasos=[paso])))


def test_un_paso_no_puede_ser_por_estudiante_y_por_excepcion():
    paso = _paso("tap", por_estudiante=True, por_excepcion=True)
    with pytest.raises(klm.RutaInvalida, match="por_excepcion"):
        klm.validar_ruta(_ruta(pasos=[paso]))


def test_los_pasos_por_excepcion_suman_a_por_estudiante_por_la_tasa(valores):
    # marcado masivo (fijo) + un toque por quien no asistió: (P + B) = 1,2 s × 0,1 por estudiante
    pasos = [_paso("tap", "marcar todos"), _paso("tap", "quien faltó", por_excepcion=True)]
    celda = klm.tiempo_ruta(_ruta(tarea="asistencia_momento", pasos=pasos), valores)
    assert celda["fijo"] == pytest.approx(1.2 / 60)
    assert celda["por_estudiante"] == pytest.approx(1.2 * 0.1 / 60)


def test_la_excepcion_se_suma_a_los_pasos_por_estudiante(valores):
    pasos = [_paso("tecla", por_estudiante=True), _paso("tecla", por_excepcion=True)]
    celda = klm.tiempo_ruta(_ruta(tarea="asistencia_momento", pasos=pasos), valores)
    assert celda["por_estudiante"] == pytest.approx((0.2 + 0.2 * 0.1) / 60)


def test_cambiar_la_tasa_cambia_la_celda_y_con_tasa_cero_no_suma(valores):
    ruta = _ruta(tarea="asistencia_momento", pasos=[_paso("tap", por_excepcion=True)])
    base = klm.tiempo_ruta(ruta, valores)["por_estudiante"]
    valores["poblacion"]["tasa_excepciones_asistencia"] = 0.2
    assert klm.tiempo_ruta(ruta, valores)["por_estudiante"] == pytest.approx(2 * base)
    valores["poblacion"]["tasa_excepciones_asistencia"] = 0.0
    assert klm.tiempo_ruta(ruta, valores)["por_estudiante"] == 0.0


def test_la_tasa_de_excepciones_es_un_solo_supuesto_compartido():
    arbol = parametros.cargar()
    nodo = arbol["poblacion"]["tasa_excepciones_asistencia"]
    assert nodo["supuesto"] is True and nodo["ancla"] == "sin ancla"
    assert nodo["rango"][0] <= nodo["valor"] <= nodo["rango"][1]
    rutas = [ruta for ruta, _ in parametros.supuestos(arbol)]
    assert rutas.count("poblacion.tasa_excepciones_asistencia") == 1
    assert not any("excepcion" in r for r in rutas if r.startswith("o2."))


def test_una_lectura_solo_suma_la_m_de_verificar():
    ops = klm.operadores_de(_ruta(pasos=[_paso("lectura", verifica=True)]))
    assert ops == [("M", "fijo")]


def test_una_lectura_sin_marca_no_suma_nada():
    assert klm.operadores_de(_ruta(pasos=[_paso("lectura")])) == []


def test_un_texto_fijo_de_la_consigna_son_n_teclas():
    ops = klm.operadores_de(_ruta(pasos=[_paso("texto", caracteres=3)]))
    assert ops == [("K", "fijo")] * 3


def test_un_texto_fijo_suma_al_tiempo_fijo(valores):
    celda = klm.tiempo_ruta(_ruta(pasos=[_paso("texto", caracteres=32)]), valores)
    assert celda["fijo"] == pytest.approx(32 * 0.2 / 60)
    assert celda["por_estudiante"] == 0.0


@pytest.mark.parametrize("caracteres", [0, -4, 2.5, "40", True])
def test_los_caracteres_de_un_texto_fijo_son_un_entero_positivo(caracteres):
    with pytest.raises(klm.RutaInvalida, match="caracteres"):
        klm.validar_ruta(_ruta(pasos=[_paso("texto", caracteres=caracteres)]))


def test_la_conclusion_toma_sus_caracteres_del_parametro_no_de_la_ruta():
    paso = _paso("texto", por_conclusion=True, caracteres=10)
    with pytest.raises(klm.RutaInvalida, match="caracteres"):
        klm.validar_ruta(_ruta(pasos=[paso]))


def test_caracteres_solo_vale_en_un_texto():
    with pytest.raises(klm.RutaInvalida, match="caracteres"):
        klm.validar_ruta(_ruta(pasos=[_paso("tecla", caracteres=3)]))


# ── conclusión de B y C (RN-003): solo una parte de los estudiantes, y 40 caracteres ─────────


def test_un_paso_por_conclusion_es_su_propio_ambito():
    ops = klm.operadores_de(_ruta(pasos=[_paso("tap", por_conclusion=True)]))
    assert ops == [("P", "por_conclusion"), ("B", "por_conclusion")]


def test_el_texto_de_la_conclusion_se_escribe_con_teclas_por_caracter():
    ops = klm.operadores_de(_ruta(pasos=[_paso("texto", por_conclusion=True)]))
    assert ops == [("T", "por_conclusion")]


def test_el_texto_solo_vale_en_una_conclusion():
    with pytest.raises(klm.RutaInvalida, match="texto"):
        klm.validar_ruta(_ruta(pasos=[_paso("texto")]))
    with pytest.raises(klm.RutaInvalida, match="texto"):
        klm.validar_ruta(_ruta(pasos=[_paso("texto", por_estudiante=True)]))


def test_los_ambitos_son_excluyentes():
    for otra in ("por_estudiante", "por_excepcion"):
        paso = _paso("tap", por_conclusion=True, **{otra: True})
        with pytest.raises(klm.RutaInvalida, match="por_conclusion"):
            klm.validar_ruta(_ruta(pasos=[paso]))


def test_sin_m_en_los_pasos_por_conclusion():
    paso = _paso("tap", por_conclusion=True, inicia_subtarea=True, decision=True, verifica=True)
    assert all(a == "por_conclusion" for _, a in klm.operadores_de(_ruta(pasos=[paso])))


def test_la_conclusion_suma_por_la_proporcion_y_por_los_caracteres(valores):
    # un toque (P + B = 1,2 s) y 40 teclas (0,2 s) solo con el 25 % de los estudiantes
    pasos = [
        _paso("tap", "abrir la conclusión", por_conclusion=True),
        _paso("texto", "escribir la conclusión", por_conclusion=True),
    ]
    celda = klm.tiempo_ruta(_ruta(pasos=pasos), valores)
    assert celda["fijo"] == 0.0
    assert celda["por_estudiante"] == pytest.approx(0.25 * (1.2 + 40 * 0.2) / 60)


def test_la_tasa_de_asistencia_no_afecta_a_la_conclusion(valores):
    ruta = _ruta(pasos=[_paso("texto", por_conclusion=True)])
    antes = klm.tiempo_ruta(ruta, valores)
    valores["poblacion"]["tasa_excepciones_asistencia"] = 0.2
    assert klm.tiempo_ruta(ruta, valores) == antes


def test_cambiar_proporcion_o_caracteres_cambia_la_celda(valores):
    ruta = _ruta(pasos=[_paso("texto", por_conclusion=True)])
    base = klm.tiempo_ruta(ruta, valores)["por_estudiante"]
    valores["poblacion"]["proporcion_conclusion_notas"] = 0.5
    assert klm.tiempo_ruta(ruta, valores)["por_estudiante"] == pytest.approx(2 * base)
    valores["poblacion"]["caracteres_conclusion"] = 80
    assert klm.tiempo_ruta(ruta, valores)["por_estudiante"] == pytest.approx(4 * base)


def test_la_conclusion_y_su_regla_vienen_de_la_spec_y_los_supuestos_son_compartidos():
    arbol = parametros.cargar()
    prop = arbol["poblacion"]["proporcion_conclusion_notas"]
    car = arbol["poblacion"]["caracteres_conclusion"]
    for nodo in (prop, car):
        assert nodo["supuesto"] is True and nodo["ancla"] == "sin ancla"
    # Rangos de DEC-1 (25-11).
    assert prop["rango"] == [0, 0.5] and prop["valor"] == 0.25
    assert car["rango"] == [10, 200] and car["valor"] == 40
    regla = arbol["reglas_app"]
    assert regla["conclusion_niveles"]["valor"] == ["B", "C"]
    assert regla["conclusion_caracteres"]["valor"] == [10, 500]
    for nodo in regla.values():
        assert "registro-notas" in nodo["fuente"] and "RN-003" in nodo["fuente"]
        assert "094-2020" in nodo["fuente"]
    minimo, maximo = regla["conclusion_caracteres"]["valor"]
    assert minimo <= car["rango"][0] and car["rango"][1] <= maximo
    rutas = [r for r, _ in parametros.supuestos(arbol)]
    assert rutas.count("poblacion.proporcion_conclusion_notas") == 1
    assert rutas.count("poblacion.caracteres_conclusion") == 1
    assert "o1.notas.por_caracter_conclusion" in rutas


# ── tabla ────────────────────────────────────────────────────────────────────────────────────


def test_la_tabla_tiene_el_formato_que_lee_medicion(valores):
    tabla = _tabla_completa(valores)
    assert set(tabla) == set(PERSONAS)
    for persona in PERSONAS:
        assert set(tabla[persona]) == set(medicion.TAREAS_KLM)
        assert set(tabla[persona]["notas"]) == {"fijo", "por_estudiante"}


def test_medicion_acepta_la_tabla_construida(valores):
    resultado = medicion.simular(valores, 3, _tabla_completa(valores))
    assert len(resultado.filas) == 48


def test_una_tabla_sin_una_ruta_sigue_levantando_klm_faltante(valores):
    rutas = [_ruta(p, t) for p in PERSONAS for t in medicion.TAREAS_KLM]
    rutas = [r for r in rutas if (r["persona"], r["tarea"]) != ("P2", "corregir_nota")]
    with pytest.raises(medicion.KLMFaltante, match="P2 · corregir_nota"):
        medicion.simular(valores, 3, klm.construir_tabla(rutas, valores))


def test_dos_rutas_de_la_misma_celda_se_rechazan(valores):
    with pytest.raises(klm.RutaInvalida, match="repetida"):
        klm.construir_tabla([_ruta(), _ruta()], valores)


def test_la_tabla_se_guarda_y_se_lee_igual(valores, tmp_path):
    tabla = _tabla_completa(valores)
    ruta = tmp_path / "tabla.yaml"
    klm.guardar_tabla(tabla, ruta)
    assert klm.cargar_tabla(ruta) == tabla


def test_las_rutas_se_leen_de_una_carpeta(valores, tmp_path):
    (tmp_path / "P1_notas.yaml").write_text(
        yaml.safe_dump(_ruta(), allow_unicode=True), encoding="utf-8"
    )
    assert klm.cargar_rutas(tmp_path) == [_ruta()]


def test_cargar_rutas_valida_cada_archivo(tmp_path):
    (tmp_path / "P1_notas.yaml").write_text(
        yaml.safe_dump(_ruta(segundos=4), allow_unicode=True), encoding="utf-8"
    )
    with pytest.raises(klm.RutaInvalida, match="P1_notas.yaml"):
        klm.cargar_rutas(tmp_path)


# ── operadores en parametros.yaml ────────────────────────────────────────────────────────────


def test_los_operadores_son_supuestos_sin_ancla_con_rango():
    arbol = parametros.cargar()
    ops = arbol["o2"]["operadores_klm"]
    assert set(ops) == set(OPERADORES)
    for nombre, nodo in ops.items():
        assert nodo["supuesto"] is True, nombre
        assert nodo["ancla"] == "sin ancla", nombre
        assert nodo["rango"][0] <= nodo["valor"] <= nodo["rango"][1], nombre
        assert "segundos" in nodo["unidad"], nombre


def test_los_operadores_entran_a_la_sensibilidad():
    rutas = [ruta for ruta, _ in parametros.supuestos(parametros.cargar())]
    assert "o2.operadores_klm.M" in rutas


# ── personas ─────────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("persona", PERSONAS)
def test_cada_persona_tiene_su_archivo_sin_dispositivo(persona):
    texto = (AGENTES / f"{persona}.md").read_text(encoding="utf-8")
    assert persona in texto
    for ajeno in ("360", "Slow 4G", "aula de cómputo"):
        assert ajeno not in texto, "el dispositivo lo fija la tarea, no la persona"
    assert "reloj" in texto.lower(), "la persona debe saber que no reporta tiempos"


# ── las 15 rutas reales y la tabla guardada ──────────────────────────────────────────────────


@pytest.fixture(scope="module")
def reales():
    return parametros.valores(parametros.cargar()), klm.cargar_rutas()


def test_las_15_rutas_reales_cubren_cada_persona_y_tarea(reales):
    _, rutas = reales
    celdas = {(r["persona"], r["tarea"]) for r in rutas}
    assert len(rutas) == 15
    assert celdas == {(p, t) for p in PERSONAS for t in medicion.TAREAS_KLM}


def test_cada_ruta_real_declara_que_un_solo_agente_interpreto_a_las_tres_personas(reales):
    _, rutas = reales
    for ruta in rutas:
        assert "un solo agente interpretó a las tres personas" in ruta["notas"].lower()


def test_en_asistencia_en_el_momento_p2_fue_primero(reales):
    _, rutas = reales
    p2 = next(r for r in rutas if (r["persona"], r["tarea"]) == ("P2", "asistencia_momento"))
    assert "P2 fue primero" in p2["notas"]


def test_la_tabla_guardada_es_la_de_las_rutas_reales(reales):
    valores, rutas = reales
    esperada = klm.construir_tabla(rutas, valores)
    guardada = klm.cargar_tabla()
    assert set(guardada) == set(esperada)
    for persona, tareas in esperada.items():
        for tarea, celda in tareas.items():
            for clave, minutos in celda.items():
                assert guardada[persona][tarea][clave] == pytest.approx(minutos), (persona, tarea)


def test_generar_tabla_guarda_la_de_las_rutas(reales, tmp_path):
    valores, rutas = reales
    destino = tmp_path / "tabla.yaml"
    tabla = klm.generar_tabla(valores, destino=destino)
    assert tabla == klm.construir_tabla(rutas, valores)
    assert klm.cargar_tabla(destino) == tabla


def test_medicion_corre_con_la_tabla_guardada(reales):
    valores, _ = reales
    resultado = medicion.simular(valores, 2026, klm.cargar_tabla())
    assert len(resultado.filas) == 48
    o2 = [f for f in resultado.filas if f["momento"] == "postest"]
    assert all(f["notas_min"] > 0 and f["asistencia_min"] > 0 and f["sesion_min"] > 0 for f in o2)
