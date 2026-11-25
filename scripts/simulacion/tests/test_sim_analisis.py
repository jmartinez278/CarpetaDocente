"""Análisis de la corrida principal, réplicas, punto de quiebre y figuras (G4). Datos simulados."""

import csv
import hashlib

import pytest

pytest.importorskip("numpy")
pytest.importorskip("scipy")
pytest.importorskip("yaml")
pytest.importorskip("matplotlib")

import numpy as np  # noqa: E402

from simulacion import analisis, klm, medicion, parametros  # noqa: E402


@pytest.fixture(scope="module")
def arbol():
    return parametros.cargar()


@pytest.fixture(scope="module")
def valores(arbol):
    return parametros.valores(arbol)


@pytest.fixture(scope="module")
def tabla(valores):
    return klm.construir_tabla(klm.cargar_rutas(), valores)


@pytest.fixture(scope="module")
def principal(valores, tabla):
    return analisis.analizar(medicion.simular(valores, 2026, tabla))


# --- Contraste de un indicador (3.5.2) ---------------------------------------------------------


def test_con_diferencias_normales_usa_t_y_d_de_cohen():
    rng = np.random.default_rng(1)
    pre = rng.normal(20, 3, 24)
    post = pre - 5 + rng.normal(0, 1, 24)
    c = analisis.contrastar(pre, post, "menor")
    assert c["shapiro_p"] >= 0.05
    assert c["prueba"] == "t de Student (relacionadas)"
    d = post - pre
    assert c["efecto_nombre"] == "d de Cohen"
    assert c["efecto"] == pytest.approx(d.mean() / d.std(ddof=1))
    assert c["p"] < 0.05 and c["rechaza"]


def test_con_diferencias_no_normales_usa_wilcoxon_y_biserial_de_rangos():
    pre = np.full(24, 10.0)
    post = pre + np.array([-8.0] * 3 + [-1.0, -0.5, -0.4, -0.3, -0.2] * 4 + [0.1])
    c = analisis.contrastar(pre, post, "menor")
    assert c["shapiro_p"] < 0.05
    assert c["prueba"] == "Wilcoxon (rangos con signo)"
    assert c["efecto_nombre"] == "biserial de rangos"
    d = post - pre
    rangos = analisis.rankdata(np.abs(d))
    positivos, negativos = rangos[d > 0].sum(), rangos[d < 0].sum()
    assert c["efecto"] == pytest.approx((positivos - negativos) / (positivos + negativos))
    assert c["rechaza"]


def test_la_prueba_es_unilateral_en_el_sentido_de_h1():
    rng = np.random.default_rng(2)
    pre = rng.normal(20, 3, 24)
    sube = pre + 5 + rng.normal(0, 1, 24)
    # El tiempo sube: con H1 «post < pre» no se rechaza H0, aunque la diferencia sea enorme.
    assert not analisis.contrastar(pre, sube, "menor")["rechaza"]
    assert analisis.contrastar(pre, sube, "mayor")["rechaza"]


def test_wilcoxon_descarta_las_diferencias_en_cero():
    pre = np.full(24, 90.0)
    post = pre.copy()
    post[:6] = 100.0  # 18 docentes sin cambio (exactitud en 100 % en ambos momentos)
    c = analisis.contrastar(pre, post, "mayor")
    assert c["prueba"] == "Wilcoxon (rangos con signo)"
    assert c["n_sin_cero"] == 6
    assert c["efecto"] == pytest.approx(1.0)


def test_sin_variacion_en_las_diferencias_no_aplica_prueba():
    pre = np.full(24, 5.0)
    c = analisis.contrastar(pre, pre - 1, "menor")
    assert c["prueba"] == "no aplica (diferencias constantes)"
    assert np.isnan(c["p"]) and not c["rechaza"]


def test_descriptivos_y_variacion_porcentual():
    pre = np.array([10.0, 20, 30, 40])
    post = np.array([5.0, 10, 15, 30])
    c = analisis.contrastar(pre, post, "menor")
    assert c["pre_media"] == 25 and c["post_media"] == 15
    assert c["pre_mediana"] == 25 and c["post_minimo"] == 5 and c["post_maximo"] == 30
    assert c["pre_de"] == pytest.approx(np.std(pre, ddof=1))
    assert c["variacion_pct"] == pytest.approx((15 - 25) / 25 * 100)
    assert c["dif_media"] == -10


def test_ic_95_de_la_diferencia_de_medias():
    rng = np.random.default_rng(3)
    pre = rng.normal(20, 3, 24)
    post = pre - 4 + rng.normal(0, 1, 24)
    c = analisis.contrastar(pre, post, "menor")
    assert c["ic95_inf"] < c["dif_media"] < c["ic95_sup"]


# --- Decisiones (regla propuesta, ajustes-cap3 punto 10) -----------------------------------------


def _con(rechazos):
    return {ind: {"rechaza": r} for ind, r in rechazos.items()}


def test_una_he_con_dos_indicadores_pide_los_dos():
    todos = dict.fromkeys(analisis.HIPOTESIS_DE, True)
    d = analisis.decidir(_con({**todos, "notas_exactitud": False}))
    assert d["HE1"] and not d["HE2"] and d["HE3"] and not d["HG"]
    assert analisis.decidir(_con(todos))["HG"]


def test_likert_global_se_contrasta_pero_no_decide():
    todos = dict.fromkeys(analisis.HIPOTESIS_DE, True)
    d = analisis.decidir(_con({**todos, "likert_global": False}))
    assert d["HG"]
    assert "likert_global" in analisis.INDICADORES
    assert analisis.HIPOTESIS_DE.get("likert_global") is None


def test_la_decision_nunca_dice_se_acepta_la_hg_suelto(principal):
    for fila in principal["decisiones_tabla"]:
        texto = fila[analisis.COLUMNA_DECISION].lower()
        assert "se acepta" not in texto
        assert "datos simulados" in texto or "regla propuesta" in texto


def test_el_analisis_principal_contrasta_los_seis_indicadores(principal):
    assert set(principal["contrastes"]) == set(analisis.INDICADORES)
    assert {f["hipotesis"] for f in principal["decisiones_tabla"]} == {"HE1", "HE2", "HE3", "HG"}


# --- Réplicas ---------------------------------------------------------------------------------


def test_las_replicas_se_repiten_con_las_mismas_semillas(valores, tabla):
    a = analisis.replicas(valores, tabla, range(1, 6), procesos=1)
    b = analisis.replicas(valores, tabla, range(1, 6), procesos=1)
    assert a == b
    assert {f["semilla"] for f in a} == {1, 2, 3, 4, 5}


def test_las_replicas_en_paralelo_dan_lo_mismo(valores, tabla):
    serie = analisis.replicas(valores, tabla, range(1, 5), procesos=1)
    paralelo = analisis.replicas(valores, tabla, range(1, 5), procesos=2)
    assert serie == paralelo


def test_las_replicas_no_tocan_django(valores, tabla):
    import sys

    antes = {m for m in sys.modules if m.startswith("django.db")}
    analisis.replicas(valores, tabla, range(1, 3), procesos=1)
    assert {m for m in sys.modules if m.startswith("django.db")} == antes


def test_resumen_de_replicas():
    filas = [
        {"semilla": s, "indicador": "notas_min", "p": p, "dif_media": d, "rechaza": p < 0.05,
         "prueba": "t de Student (relacionadas)"}
        for s, p, d in [(1, 0.01, -3.0), (2, 0.20, -1.0), (3, 0.001, -5.0), (4, 0.04, -2.0)]
    ]  # fmt: skip
    r = analisis.resumir_replicas(filas)["notas_min"]
    assert r["pct_rechazo"] == 75
    assert r["p_mediana"] == pytest.approx(np.median([0.01, 0.20, 0.001, 0.04]))
    assert r["dif_p2_5"] == pytest.approx(np.percentile([-3, -1, -5, -2], 2.5))
    assert r["replicas"] == 4


def test_resumen_por_hipotesis():
    filas = []
    for s, rechazos in [(1, (True, True)), (2, (True, False)), (3, (True, True))]:
        filas += [
            {"semilla": s, "indicador": "notas_min", "rechaza": rechazos[0]},
            {"semilla": s, "indicador": "notas_exactitud", "rechaza": rechazos[1]},
        ]
    pct = analisis.resumir_hipotesis(filas)
    assert pct["HE2"] == pytest.approx(200 / 3)


# --- Punto de quiebre (DEC-2) ------------------------------------------------------------------


def test_escalar_solo_toca_los_tiempos_de_o1_de_la_tarea(valores):
    otro = analisis.escalar_o1(valores, "notas", 0.5)
    assert otro["o1"]["notas"]["apertura"] == valores["o1"]["notas"]["apertura"] * 0.5
    assert otro["o1"]["corregir_nota"]["costo"] == valores["o1"]["corregir_nota"]["costo"] * 0.5
    assert (
        otro["o1"]["corregir_nota"]["probabilidad"]
        == valores["o1"]["corregir_nota"]["probabilidad"]
    )
    assert otro["o1"]["asistencia"] == valores["o1"]["asistencia"]
    assert otro["o1"]["sesion"] == valores["o1"]["sesion"]
    assert valores["o1"]["notas"]["apertura"] == 2  # el original no cambia


def test_en_sesion_la_elaboracion_no_se_escala(valores):
    otro = analisis.escalar_o1(valores, "sesion", 2)
    assert otro["o1"]["sesion"]["entrega_mediana"] == 30
    assert otro["o1"]["sesion"]["elaboracion_mediana"] == 90


def test_umbral_de_barrido_es_el_primero_desde_el_que_todo_rechaza():
    factores = [0.1, 0.2, 0.3, 0.4, 0.5]
    assert analisis.umbral_de_barrido(factores, [False, True, False, True, True]) == 0.4
    assert analisis.umbral_de_barrido(factores, [False] * 5) is None
    assert analisis.umbral_de_barrido(factores, [True] * 5) == 0.1


def test_biseccion_encuentra_el_cruce_de_una_funcion_creciente():
    f = analisis.biseccion(lambda x: 100 * x, inferior=0.0, superior=2.0, meta=80, tolerancia=0.001)
    assert f == pytest.approx(0.8, abs=0.002)
    assert analisis.biseccion(lambda x: 10, 0.0, 2.0, 80, 0.01) is None


def test_quiebre_principal_bien_ubicado(valores, tabla):
    paso = 0.05
    q = analisis.quiebre_principal(valores, tabla, "notas", 2026, paso=paso, maximo=1.5)
    assert q["factor"] is not None
    p_en = analisis.p_de_tarea(valores, tabla, "notas", 2026, q["factor"])
    p_antes = analisis.p_de_tarea(valores, tabla, "notas", 2026, round(q["factor"] - paso, 4))
    assert p_en < 0.05 <= p_antes


def test_el_quiebre_informa_el_valor_y_si_cae_en_el_rango(arbol, valores):
    filas = analisis.parametros_en_quiebre(arbol, valores, "asistencia", 0.5)
    por = {f["parametro"]: f for f in filas}
    assert set(por) == set(analisis.PARAMETROS_QUIEBRE["asistencia"])
    f = por["o1.asistencia.por_estudiante"]
    assert f["valor_en_quiebre"] == pytest.approx(0.075)
    assert f["dentro_del_rango"] is True
    # Un rango que empieza en 0 contiene cualquier valor reducido: no cuenta como «dentro».
    cero = por["o1.asistencia.transcripcion_apertura"]
    assert cero["rango_desde_cero"] is True
    assert cero["dentro_del_rango"] is None


def _p(dentro):
    return {"dentro_del_rango": dentro}


def test_conclusion_del_quiebre_por_tarea():
    depende, robusta = "depende del supuesto", "robusta"
    # El quiebre se alcanza sin salir de los rangos solo si todos los evaluados siguen dentro.
    assert analisis.conclusion_quiebre([_p(True)]) == depende
    assert analisis.conclusion_quiebre([_p(True), _p(None)]) == depende
    assert analisis.conclusion_quiebre([_p(True), _p(False)]) == robusta
    assert analisis.conclusion_quiebre([_p(False), _p(None)]) == robusta
    assert analisis.conclusion_quiebre([]) == "robusta (no se alcanza con f ≤ 5)"


def test_quiebre_csv_con_los_dos_criterios(tmp_path):
    analisis.ejecutar_principal(tmp_path, replicas=3, procesos=1, paso_quiebre=0.25)
    with (tmp_path / "simulados_quiebre.csv").open(encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f))
    criterios = {f["criterio"] for f in filas if f.get("parametro")}
    assert criterios == {"corrida principal (p < 0,05)", "réplicas (80 %)"}
    tablas = (tmp_path / "tablas.md").read_text(encoding="utf-8")
    s10 = tablas.split("**Tabla S10")[1]
    assert "o1.notas.apertura" not in s10  # el detalle por parámetro va solo al CSV
    assert "Conclusión" in s10 and "rango que empieza en 0" in s10


# --- Salidas ------------------------------------------------------------------------------------


def _sha(ruta):
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def test_salidas_marcadas_y_parametros_intactos(tmp_path, valores, tabla):
    antes = _sha(parametros.ARCHIVO)
    analisis.ejecutar_principal(tmp_path, replicas=3, procesos=1, paso_quiebre=0.25)
    assert _sha(parametros.ARCHIVO) == antes

    csvs = sorted(tmp_path.glob("*.csv"))
    nombres = {c.name for c in csvs}
    assert {
        "simulados_principal_filas.csv",
        "simulados_principal_contrastes.csv",
        "simulados_replicas.csv",
        "simulados_replicas_resumen.csv",
        "simulados_quiebre.csv",
    } <= nombres
    for archivo in csvs:
        with archivo.open(encoding="utf-8", newline="") as f:
            filas = list(csv.DictReader(f))
        assert filas, archivo.name
        assert all(fila["origen"] == "Datos simulados" for fila in filas), archivo.name

    tablas = (tmp_path / "tablas.md").read_text(encoding="utf-8")
    titulos = [linea for linea in tablas.splitlines() if linea.startswith("**Tabla S")]
    assert titulos and all("Datos simulados" in t for t in titulos)
    assert analisis.COLUMNA_DECISION in tablas
    assert "| Planificación de sesiones |" in tablas
    assert parametros_blob() in tablas

    figuras = sorted((tmp_path / "figuras").glob("*.png"))
    assert {f.stem for f in figuras} == set(analisis.INDICADORES)


def parametros_blob():
    contenido = parametros.ARCHIVO.read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(contenido) + contenido).hexdigest()[:7]  # noqa: S324


def test_tablas_con_coma_decimal():
    assert analisis.num(12.345, 2) == "12,35"
    assert analisis.num(-0.5, 1) == "−0,5"
    assert analisis.num(float("nan"), 2) == "—"


def test_csv_con_punto_decimal(tmp_path):
    ruta = tmp_path / "x.csv"
    analisis.escribir_csv(ruta, [{"a": 1.5}])
    texto = ruta.read_text(encoding="utf-8")
    assert texto.splitlines()[0] == "origen,a"
    assert "Datos simulados,1.5" in texto


def test_figura_dice_datos_simulados(principal, valores, tabla):
    r = medicion.simular(valores, 2026, tabla)
    fig = analisis.figura(r, "notas_min")
    assert "Datos simulados" in fig.axes[0].get_title()
    assert [t.get_text() for t in fig.axes[0].get_xticklabels()] == ["Pretest (O1)", "Postest (O2)"]
