"""Análisis de la simulación (G4): corrida principal, réplicas, punto de quiebre y figuras.

Datos simulados: nada de lo que sale de aquí es una medición real. Sigue 3.5 de la tesis:
descriptivos y variación %, Shapiro-Wilk sobre las diferencias (post − pre), luego t de Student
o Wilcoxon para muestras relacionadas, unilaterales en el sentido de H₁ (ajustes-cap3, punto 9),
α = 0,05, más el tamaño del efecto que reporta Jamovi (d de Cohen o biserial de rangos).

La regla que junta los indicadores en HE y HG es una propuesta (ajustes-cap3, punto 10): una HE
rechaza H₀ si la rechazan todos sus indicadores; la HG, si la rechazan las tres HE. El puntaje
global del cuestionario se contrasta como apoyo y no entra en esa regla.

``parametros.yaml`` no se modifica: las variantes son copias en memoria.

    uv run --group simulacion python -m simulacion.analisis principal
"""

import argparse
import copy
import csv
import hashlib
import math
import os
import subprocess
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from scipy import stats
from scipy.stats import rankdata

from simulacion import klm, medicion, parametros

ORIGEN = medicion.ORIGEN
ALFA = 0.05
META_REPLICAS = 80  # % de réplicas que rechaza H₀ (DEC-2)
COLUMNA_DECISION = "Decisión estadística (datos simulados)"
SALIDA = Path(__file__).with_name("salidas")
PRUEBA_T = "t de Student (relacionadas)"
PRUEBA_W = "Wilcoxon (rangos con signo)"
NO_APLICA = "no aplica (diferencias constantes)"

# Tabla 5 de la tesis: indicador, unidad y sentido de H₁ (3.5.2 c).
INDICADORES = {
    "sesion_min": {
        "nombre": "Tiempo empleado en elaborar una sesión",
        "unidad": "min",
        "sentido": "menor",
    },
    "notas_min": {
        "nombre": "Tiempo de registro de notas",
        "unidad": "min por sección",
        "sentido": "menor",
    },
    "notas_exactitud": {
        "nombre": "Exactitud del registro de notas",
        "unidad": "% de registros sin error",
        "sentido": "mayor",
    },
    "asistencia_min": {
        "nombre": "Tiempo del control de asistencia",
        "unidad": "min por jornada",
        "sentido": "menor",
    },
    "asistencia_exactitud": {
        "nombre": "Exactitud del control de asistencia",
        "unidad": "% de registros sin error",
        "sentido": "mayor",
    },
    "likert_global": {
        "nombre": "Percepción del docente (puntaje global, Anexo 4)",
        "unidad": "puntaje (15 a 75)",
        "sentido": "mayor",
    },
}
HIPOTESIS_DE = {
    "sesion_min": "HE1",
    "notas_min": "HE2",
    "notas_exactitud": "HE2",
    "asistencia_min": "HE3",
    "asistencia_exactitud": "HE3",
}
HIPOTESIS = ("HE1", "HE2", "HE3")
NOMBRE_DIMENSION = {
    "planificacion": "Planificación de sesiones",
    "notas": "Registro y control de notas",
    "asistencia": "Control de asistencia",
    "global": "Global (15 ítems)",
}

# Punto de quiebre (DEC-2): los tiempos de O1 propios de cada tarea. La elaboración de la sesión
# es la misma en O1 y O2, así que no se escala; la probabilidad de corregir una nota tampoco.
PARAMETROS_QUIEBRE = {
    "sesion": ("o1.sesion.entrega_mediana",),
    "notas": (
        "o1.notas.apertura",
        "o1.notas.por_estudiante_cuaderno",
        "o1.notas.por_estudiante_excel",
        "o1.notas.por_caracter_conclusion",
        "o1.corregir_nota.costo",
    ),
    "asistencia": (
        "o1.asistencia.por_estudiante",
        "o1.asistencia.transcripcion_apertura",
        "o1.asistencia.transcripcion_por_estudiante",
    ),
}
INDICADOR_DE_TAREA = {"sesion": "sesion_min", "notas": "notas_min", "asistencia": "asistencia_min"}


# --- Contraste de un indicador ------------------------------------------------------------------


def _describir(prefijo: str, x: np.ndarray) -> dict:
    return {
        f"{prefijo}_n": len(x),
        f"{prefijo}_media": float(x.mean()),
        f"{prefijo}_mediana": float(np.median(x)),
        f"{prefijo}_de": float(x.std(ddof=1)),
        f"{prefijo}_minimo": float(x.min()),
        f"{prefijo}_maximo": float(x.max()),
    }


def _biserial_de_rangos(d: np.ndarray) -> float:
    """(R⁺ − R⁻) ÷ (R⁺ + R⁻) sobre las diferencias distintas de cero; positivo si post > pre."""
    d = d[d != 0]
    rangos = rankdata(np.abs(d))
    positivos, negativos = rangos[d > 0].sum(), rangos[d < 0].sum()
    return float((positivos - negativos) / (positivos + negativos))


def contrastar(pre, post, sentido: str) -> dict:
    """Descriptivos, normalidad, prueba unilateral y tamaño del efecto de un indicador."""
    pre, post = np.asarray(pre, dtype=float), np.asarray(post, dtype=float)
    d = post - pre
    n = len(d)
    alternativa = "less" if sentido == "menor" else "greater"
    fila = {**_describir("pre", pre), **_describir("post", post)}
    media_pre = fila["pre_media"]
    fila["dif_media"] = float(d.mean())
    fila["variacion_pct"] = (
        (fila["post_media"] - media_pre) / media_pre * 100 if media_pre else math.nan
    )
    error = d.std(ddof=1) / math.sqrt(n)
    margen = stats.t.ppf(0.975, n - 1) * error
    fila["ic95_inf"], fila["ic95_sup"] = fila["dif_media"] - margen, fila["dif_media"] + margen
    fila["n_sin_cero"] = int((d != 0).sum())
    fila["h1"] = "post < pre" if sentido == "menor" else "post > pre"

    if np.ptp(d) == 0:
        fila.update(
            shapiro_w=math.nan, shapiro_p=math.nan, prueba=NO_APLICA, estadistico=math.nan,
            p=math.nan, efecto_nombre="", efecto=math.nan, rechaza=False,
        )  # fmt: skip
        return fila

    shapiro = stats.shapiro(d)
    fila["shapiro_w"], fila["shapiro_p"] = float(shapiro.statistic), float(shapiro.pvalue)
    if fila["shapiro_p"] >= ALFA:
        r = stats.ttest_rel(post, pre, alternative=alternativa)
        fila.update(
            prueba=PRUEBA_T, efecto_nombre="d de Cohen", efecto=float(d.mean() / d.std(ddof=1))
        )
    else:
        # Como wilcox.test de R (Jamovi): descarta los ceros y corrige por continuidad.
        r = stats.wilcoxon(
            d, zero_method="wilcox", correction=True, alternative=alternativa, method="auto"
        )
        fila.update(
            prueba=PRUEBA_W, efecto_nombre="biserial de rangos", efecto=_biserial_de_rangos(d)
        )
    fila["estadistico"], fila["p"] = float(r.statistic), float(r.pvalue)
    fila["rechaza"] = bool(fila["p"] < ALFA)
    return fila


def pares(resultado, indicador: str) -> tuple[np.ndarray, np.ndarray]:
    """Valores de pretest y postest del indicador, en el mismo orden de docentes."""
    por = {(f["codigo"], f["momento"]): f[indicador] for f in resultado.filas}
    codigos = sorted({f["codigo"] for f in resultado.filas})
    pre = np.array([por[(c, "pretest")] for c in codigos], dtype=float)
    post = np.array([por[(c, "postest")] for c in codigos], dtype=float)
    return pre, post


# --- Decisiones ---------------------------------------------------------------------------------


def decidir(contrastes: dict) -> dict:
    """Regla propuesta (ajustes-cap3, punto 10). Solo cuenta lo que está en ``HIPOTESIS_DE``."""
    decision = {
        he: all(contrastes[i]["rechaza"] for i, h in HIPOTESIS_DE.items() if h == he)
        for he in HIPOTESIS
    }
    decision["HG"] = all(decision[he] for he in HIPOTESIS)
    return decision


def _texto_indicador(indicador: str, rechaza: bool) -> str:
    texto = "Se rechaza H₀" if rechaza else "No se rechaza H₀"
    if indicador not in HIPOTESIS_DE:
        return f"{texto} (apoyo; no entra en HE ni HG; datos simulados)"
    return f"{texto} (datos simulados)"


def _tabla_decisiones(decision: dict) -> list[dict]:
    filas = []
    for he in HIPOTESIS:
        indicadores = [INDICADORES[i]["nombre"] for i, h in HIPOTESIS_DE.items() if h == he]
        texto = (
            "Se rechaza H₀ en todos sus indicadores"
            if decision[he]
            else "No se rechaza H₀ en al menos un indicador"
        )
        filas.append({
            "hipotesis": he,
            "indicadores": "; ".join(indicadores),
            COLUMNA_DECISION: f"{texto} (regla propuesta, punto 10; datos simulados)",
        })  # fmt: skip
    texto = "HE1, HE2 y HE3 rechazan H₀" if decision["HG"] else "Al menos una HE no rechaza H₀"
    filas.append({
        "hipotesis": "HG",
        "indicadores": "HE1, HE2 y HE3",
        COLUMNA_DECISION: f"{texto} (regla propuesta, punto 10; datos simulados)",
    })  # fmt: skip
    return filas


def analizar(resultado) -> dict:
    contrastes = {}
    for indicador, meta in INDICADORES.items():
        fila = contrastar(*pares(resultado, indicador), meta["sentido"])
        fila[COLUMNA_DECISION] = _texto_indicador(indicador, fila["rechaza"])
        contrastes[indicador] = fila
    decision = decidir(contrastes)
    return {
        "contrastes": contrastes,
        "decisiones": decision,
        "decisiones_tabla": _tabla_decisiones(decision),
    }


# --- Réplicas -----------------------------------------------------------------------------------


def _procesos(procesos: int | None) -> int:
    return procesos or max(1, (os.cpu_count() or 2) - 1)


def _mapear(funcion, tareas: list, procesos: int | None) -> list:
    procesos = _procesos(procesos)
    if procesos == 1 or len(tareas) < 2:
        return [funcion(t) for t in tareas]
    trozo = max(1, len(tareas) // (procesos * 4))
    with ProcessPoolExecutor(max_workers=procesos) as ejecutor:
        return list(ejecutor.map(funcion, tareas, chunksize=trozo))


def _una_replica(tarea) -> list[dict]:
    valores, tabla, semilla = tarea
    resultado = medicion.simular(valores, semilla, tabla)
    filas = []
    for indicador, meta in INDICADORES.items():
        c = contrastar(*pares(resultado, indicador), meta["sentido"])
        filas.append({
            "semilla": semilla,
            "indicador": indicador,
            "prueba": c["prueba"],
            "shapiro_p": c["shapiro_p"],
            "p": c["p"],
            "dif_media": c["dif_media"],
            "efecto": c["efecto"],
            "rechaza": c["rechaza"],
        })  # fmt: skip
    return filas


def replicas(valores: dict, tabla: dict, semillas, procesos: int | None = None) -> list[dict]:
    """Una fila por semilla e indicador. No toca la base: solo ``medicion.simular``."""
    tareas = [(valores, tabla, int(s)) for s in semillas]
    return [fila for filas in _mapear(_una_replica, tareas, procesos) for fila in filas]


_correr_replicas = replicas  # ejecutar_principal recibe un argumento con el mismo nombre


def resumir_replicas(filas: list[dict]) -> dict:
    por = defaultdict(list)
    for fila in filas:
        por[fila["indicador"]].append(fila)
    resumen = {}
    for indicador, grupo in por.items():
        dif = [f["dif_media"] for f in grupo]
        resumen[indicador] = {
            "replicas": len(grupo),
            "pct_rechazo": 100 * sum(f["rechaza"] for f in grupo) / len(grupo),
            "p_mediana": float(np.nanmedian([f["p"] for f in grupo])),
            "dif_media_media": float(np.mean(dif)),
            "dif_p2_5": float(np.percentile(dif, 2.5)),
            "dif_p97_5": float(np.percentile(dif, 97.5)),
            "pct_t": 100 * sum(f["prueba"] == PRUEBA_T for f in grupo) / len(grupo),
            "pct_wilcoxon": 100 * sum(f["prueba"] == PRUEBA_W for f in grupo) / len(grupo),
        }
    return resumen


def resumir_hipotesis(filas: list[dict]) -> dict:
    """% de réplicas en que cada HE (y la HG) rechaza H₀ con la regla propuesta."""
    por_semilla = defaultdict(dict)
    for fila in filas:
        por_semilla[fila["semilla"]][fila["indicador"]] = fila["rechaza"]
    conteo = defaultdict(int)
    validas = defaultdict(int)
    for rechazos in por_semilla.values():
        decision = {}
        for he in HIPOTESIS:
            indicadores = [i for i, h in HIPOTESIS_DE.items() if h == he]
            if all(i in rechazos for i in indicadores):
                decision[he] = all(rechazos[i] for i in indicadores)
        if len(decision) == len(HIPOTESIS):
            decision["HG"] = all(decision.values())
        for clave, valor in decision.items():
            validas[clave] += 1
            conteo[clave] += valor
    return {clave: 100 * conteo[clave] / validas[clave] for clave in validas}


# --- Punto de quiebre (DEC-2) -------------------------------------------------------------------


def escalar_o1(valores: dict, tarea: str, factor: float) -> dict:
    """Copia de ``valores`` con los tiempos de O1 de la tarea multiplicados por ``factor``."""
    otro = copy.deepcopy(valores)
    for ruta in PARAMETROS_QUIEBRE[tarea]:
        *grupos, hoja = ruta.split(".")
        nodo = otro
        for g in grupos:
            nodo = nodo[g]
        nodo[hoja] = nodo[hoja] * factor
    return otro


def _contraste_tarea(tarea_args) -> dict:
    valores, tabla, tarea, semilla, factor = tarea_args
    indicador = INDICADOR_DE_TAREA[tarea]
    resultado = medicion.simular(escalar_o1(valores, tarea, factor), semilla, tabla)
    return contrastar(*pares(resultado, indicador), INDICADORES[indicador]["sentido"])


def p_de_tarea(valores, tabla, tarea, semilla, factor) -> float:
    return _contraste_tarea((valores, tabla, tarea, semilla, factor))["p"]


def umbral_de_barrido(factores: list, rechazos: list) -> float | None:
    """El menor factor desde el cual todos los factores mayores rechazan H₀."""
    umbral = None
    for factor, rechaza in reversed(list(zip(factores, rechazos, strict=True))):
        if not rechaza:
            break
        umbral = factor
    return umbral


def quiebre_principal(
    valores, tabla, tarea, semilla, paso=0.01, maximo=5.0, procesos: int | None = 1
) -> dict:
    factores = [round(paso * k, 6) for k in range(1, int(round(maximo / paso)) + 1)]
    tareas = [(valores, tabla, tarea, semilla, f) for f in factores]
    contrastes = _mapear(_contraste_tarea, tareas, procesos)
    factor = umbral_de_barrido(factores, [c["rechaza"] for c in contrastes])
    media_o1 = None
    if factor is not None:
        media_o1 = contrastes[factores.index(factor)]["pre_media"]
    return {"tarea": tarea, "factor": factor, "media_o1": media_o1, "paso": paso, "maximo": maximo}


def biseccion(funcion, inferior, superior, meta, tolerancia) -> float | None:
    """Menor x (± tolerancia) con ``funcion(x) >= meta``, si la función crece con x."""
    if funcion(superior) < meta:
        return None
    if funcion(inferior) >= meta:
        return inferior
    while superior - inferior > tolerancia:
        medio = (inferior + superior) / 2
        if funcion(medio) >= meta:
            superior = medio
        else:
            inferior = medio
    return superior


def _rechaza_tarea(tarea_args) -> bool:
    return _contraste_tarea(tarea_args)["rechaza"]


def pct_rechazo_tarea(valores, tabla, tarea, semillas, factor, procesos=None) -> float:
    tareas = [(valores, tabla, tarea, int(s), factor) for s in semillas]
    rechazos = _mapear(_rechaza_tarea, tareas, procesos)
    return 100 * sum(rechazos) / len(rechazos)


def quiebre_replicas(
    valores, tabla, tarea, semillas, procesos=None, inferior=0.01, superior=5.0, tolerancia=0.01
) -> float | None:
    def funcion(factor):
        return pct_rechazo_tarea(valores, tabla, tarea, semillas, factor, procesos)

    return biseccion(funcion, inferior, superior, META_REPLICAS, tolerancia)


CRITERIO_PRINCIPAL = "corrida principal (p < 0,05)"
CRITERIO_REPLICAS = f"réplicas ({META_REPLICAS} %)"
DEPENDE = "depende del supuesto"
ROBUSTA = "robusta"
NO_SE_ALCANZA = "robusta (no se alcanza con f ≤ 5)"


def parametros_en_quiebre(arbol: dict, valores: dict, tarea: str, factor: float) -> list[dict]:
    """Cada parámetro de O1 de la tarea multiplicado por ``factor``, frente a su rango DEC-1.

    Un rango que empieza en 0 contiene cualquier valor reducido: no informa, así que no cuenta
    como «dentro del rango» (``dentro_del_rango`` = ``None``) y no entra en la conclusión.
    """
    rangos = dict(parametros.supuestos(arbol))
    filas = []
    for ruta in PARAMETROS_QUIEBRE[tarea]:
        actual = parametros.valor(arbol, ruta)
        nuevo = actual * factor
        minimo, maximo = rangos[ruta]
        desde_cero = minimo == 0
        filas.append({
            "tarea": tarea,
            "parametro": ruta,
            "valor_actual": actual,
            "factor": factor,
            "valor_en_quiebre": nuevo,
            "rango_min": minimo,
            "rango_max": maximo,
            "rango_desde_cero": desde_cero,
            "dentro_del_rango": None if desde_cero else bool(minimo <= nuevo <= maximo),
        })  # fmt: skip
    return filas


def conclusion_quiebre(filas: list[dict]) -> str:
    """«Depende del supuesto» si el quiebre se alcanza sin sacar de su rango ningún parámetro
    evaluado (todos los que no empiezan en 0 siguen dentro); si no, «robusta».

    Sin filas, el quiebre no se alcanzó con f ≤ 5.
    """
    if not filas:
        return NO_SE_ALCANZA
    evaluados = [f["dentro_del_rango"] for f in filas if f["dentro_del_rango"] is not None]
    return DEPENDE if evaluados and all(evaluados) else ROBUSTA


# --- Salidas ------------------------------------------------------------------------------------


def num(x, decimales: int = 2) -> str:
    """Número con coma decimal y signo menos tipográfico; «—» si no hay valor."""
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "—"
    texto = f"{abs(x):.{decimales}f}".replace(".", ",")
    negativo = x < 0 and any(c not in "0," for c in texto)
    return f"−{texto}" if negativo else texto


def _celda_csv(valor):
    if isinstance(valor, bool):
        return "sí" if valor else "no"
    if valor is None:
        return ""
    return valor


def escribir_csv(ruta: Path, filas: list[dict]) -> None:
    """CSV con coma como separador y punto decimal; ``origen`` = «Datos simulados» en cada fila."""
    columnas = ["origen"]
    for fila in filas:
        columnas += [c for c in fila if c not in columnas]
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=columnas, lineterminator="\n")
        escritor.writeheader()
        for fila in filas:
            escritor.writerow({**{c: _celda_csv(v) for c, v in fila.items()}, "origen": ORIGEN})


def _filas_docentes(resultado) -> list[dict]:
    rasgos = {d.codigo: d for d in resultado.docentes}
    filas = []
    for fila in resultado.filas:
        d = rasgos[fila["codigo"]]
        base = {k: v for k, v in fila.items() if k not in ("origen", "asistencia_jornadas_min")}
        jornadas = {
            f"asistencia_jornada_{i}_min": x
            for i, x in enumerate(fila["asistencia_jornadas_min"], start=1)
        }
        filas.append({
            "codigo": d.codigo, "grado": d.grado, "seccion": d.seccion, "persona": d.persona,
            "modalidad_asistencia": d.modalidad, "medio_notas_o1": d.medio_notas_o1,
            "n_estudiantes": d.n_estudiantes, **base, **jornadas,
        })  # fmt: skip
    return filas


def _filas_jamovi(resultado) -> list[dict]:
    """Formato ancho (una fila por docente, pre y post lado a lado) para la prueba en Jamovi."""
    filas = {}
    for indicador in INDICADORES:
        pre, post = pares(resultado, indicador)
        codigos = sorted({f["codigo"] for f in resultado.filas})
        for c, a, b in zip(codigos, pre, post, strict=True):
            fila = filas.setdefault(c, {"codigo": c})
            fila[f"{indicador}_pre"], fila[f"{indicador}_post"] = a, b
    return list(filas.values())


def figura(resultado, indicador: str):
    """Diagrama de cajas pre/post de un indicador (3.5.1)."""
    from matplotlib.figure import Figure
    from matplotlib.ticker import FuncFormatter

    meta = INDICADORES[indicador]
    pre, post = pares(resultado, indicador)
    fig = Figure(figsize=(5.5, 4.2), layout="constrained")
    ax = fig.subplots()
    ax.boxplot([pre, post], widths=0.5)
    ax.set_xticks([1, 2], ["Pretest (O1)", "Postest (O2)"])
    ax.set_ylabel(meta["unidad"])
    ax.set_title(f"{meta['nombre']}\n(Datos simulados)", fontsize=10)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}".replace(".", ",")))
    ax.grid(axis="y", alpha=0.3)
    return fig


def _blob(ruta: Path) -> str:
    contenido = ruta.read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(contenido) + contenido).hexdigest()[:7]  # noqa: S324


def _commit_de(ruta: Path) -> str:
    try:
        salida = subprocess.run(
            ["git", "log", "-1", "--format=%h", "--", str(ruta)],
            capture_output=True, text=True, check=True, cwd=ruta.parent,
        )  # fmt: skip
        return salida.stdout.strip() or "sin commit"
    except (OSError, subprocess.CalledProcessError):
        return "sin git"


def _versiones() -> str:
    import matplotlib
    import scipy

    return f"NumPy {np.__version__}, SciPy {scipy.__version__}, matplotlib {matplotlib.__version__}"


def _tabla_md(titulo: str, cabecera: list[str], filas: list[list[str]], nota: str = "") -> str:
    lineas = [f"**{titulo}**", "", "| " + " | ".join(cabecera) + " |"]
    lineas.append("|" + "|".join("---" for _ in cabecera) + "|")
    lineas += ["| " + " | ".join(fila) + " |" for fila in filas]
    if nota:
        lineas += ["", f"*Nota.* {nota}"]
    return "\n".join(lineas) + "\n"


def _p(p) -> str:
    if p is None or (isinstance(p, float) and math.isnan(p)):
        return "—"
    return "< 0,001" if p < 0.001 else num(p, 3)


def _tablas_principal(contexto: dict) -> list[str]:
    c = contexto["analisis"]["contrastes"]
    resultado = contexto["resultado"]
    nota_sim = (
        f"Datos simulados (semilla {contexto['semilla']}; n = {len(resultado.docentes)} docentes). "
        "No son mediciones reales."
    )
    bloques = []
    filas = []
    for i, meta in INDICADORES.items():
        f = c[i]
        filas.append([
            meta["nombre"], meta["unidad"],
            f"{num(f['pre_media'])} ({num(f['pre_de'])})", num(f["pre_mediana"]),
            f"{num(f['pre_minimo'])}–{num(f['pre_maximo'])}",
            f"{num(f['post_media'])} ({num(f['post_de'])})", num(f["post_mediana"]),
            f"{num(f['post_minimo'])}–{num(f['post_maximo'])}",
            num(f["variacion_pct"], 1),
        ])  # fmt: skip
    bloques.append(_tabla_md(
        "Tabla S1. Descriptivos del pretest y el postest por indicador (Datos simulados)",
        ["Indicador", "Unidad", "Pre: media (DE)", "Pre: mediana", "Pre: mín.–máx.",
         "Post: media (DE)", "Post: mediana", "Post: mín.–máx.", "Variación (%)"],
        filas,
        nota_sim + " Variación (%) = (media post − media pre) ÷ media pre × 100 (3.5.1).",
    ))  # fmt: skip

    filas = [
        [INDICADORES[i]["nombre"], num(c[i]["shapiro_w"], 3), _p(c[i]["shapiro_p"]), c[i]["prueba"]]
        for i in INDICADORES
    ]
    bloques.append(_tabla_md(
        "Tabla S2. Prueba de normalidad de Shapiro-Wilk sobre las diferencias (Datos simulados)",
        ["Indicador", "W", "p", "Prueba elegida"],
        filas,
        nota_sim + " Diferencia = postest − pretest. Con p ≥ 0,05 se usa t de Student; si no, "
        "Wilcoxon (3.5.2 a y b).",
    ))  # fmt: skip

    filas = []
    for i, meta in INDICADORES.items():
        f = c[i]
        filas.append([
            meta["nombre"], f["h1"], f["prueba"], num(f["estadistico"], 2), _p(f["p"]),
            f"{f['efecto_nombre']} = {num(f['efecto'], 2)}" if f["efecto_nombre"] else "—",
            f"{num(f['dif_media'])} [{num(f['ic95_inf'])}; {num(f['ic95_sup'])}]",
            f[COLUMNA_DECISION],
        ])  # fmt: skip
    bloques.append(_tabla_md(
        "Tabla S3. Prueba de hipótesis por indicador (Datos simulados)",
        ["Indicador", "H₁", "Prueba", "Estadístico", "p (unilateral)", "Tamaño del efecto",
         "Dif. de medias [IC 95 %]", COLUMNA_DECISION],
        filas,
        nota_sim + " α = 0,05. Pruebas unilaterales en el sentido de H₁ (ajustes-cap3, punto 9). "
        "Wilcoxon descarta las diferencias en cero y corrige por continuidad, como Jamovi; "
        "su estadístico es la suma de rangos positivos. El IC 95 % de la diferencia de medias es "
        "bilateral (t). El puntaje global del cuestionario es evidencia de apoyo.",
    ))  # fmt: skip

    filas = [[d["hipotesis"], d["indicadores"], d[COLUMNA_DECISION]]
             for d in contexto["analisis"]["decisiones_tabla"]]  # fmt: skip
    bloques.append(_tabla_md(
        "Tabla S4. Decisión por hipótesis con la regla propuesta (Datos simulados)",
        ["Hipótesis", "Indicadores", COLUMNA_DECISION],
        filas,
        nota_sim + " Regla propuesta, pendiente de decisión del equipo (ajustes-cap3, punto 10): "
        "una HE rechaza H₀ si la rechazan todos sus indicadores; la HG, si la rechazan las tres "
        "HE. El puntaje global del cuestionario no entra en la regla.",
    ))  # fmt: skip
    bloques.append(_tabla_likert(resultado, nota_sim))
    bloques.append(_tabla_sus_autorregistro(resultado, nota_sim))
    return bloques


def _filas_de(resultado, momento):
    return [f for f in resultado.filas if f["momento"] == momento]


def _tabla_likert(resultado, nota_sim) -> str:
    filas = []
    for dim in (*medicion.DIMENSIONES, "global"):
        celdas = [NOMBRE_DIMENSION[dim]]
        for momento in ("pretest", "postest"):
            grupo = _filas_de(resultado, momento)
            x = np.array([f[f"likert_{dim}"] for f in grupo], dtype=float)
            niveles = [f[f"likert_{dim}_nivel"] for f in grupo]
            conteo = "/".join(
                str(niveles.count(n)) for n in ("desfavorable", "regular", "favorable")
            )
            celdas += [f"{num(x.mean())} ({num(x.std(ddof=1))})", conteo]
        filas.append(celdas)
    return _tabla_md(
        "Tabla S5. Cuestionario de percepción (Anexo 4) por dimensión (Datos simulados)",
        ["Dimensión", "Pre: media (DE)", "Pre: D/R/F", "Post: media (DE)", "Post: D/R/F"],
        filas,
        nota_sim + " D/R/F: docentes en nivel desfavorable, regular y favorable según los cortes "
        "del Anexo 4. Solo el puntaje global se contrasta (Tabla S3).",
    )


def _tabla_sus_autorregistro(resultado, nota_sim) -> str:
    sus = np.array([f["sus"] for f in _filas_de(resultado, "postest")], dtype=float)
    filas = [[
        "SUS (solo postest, 0 a 100)", "—",
        f"{num(sus.mean(), 1)} ({num(sus.std(ddof=1), 1)})",
    ]]  # fmt: skip
    for clave, nombre in (
        ("autorregistro_sesiones", "Autorregistro: sesiones planificadas en la semana"),
        ("autorregistro_total_min", "Autorregistro: minutos totales en la semana"),
    ):
        celdas = [nombre]
        for momento in ("pretest", "postest"):
            x = np.array([f[clave] for f in _filas_de(resultado, momento)], dtype=float)
            celdas.append(f"{num(x.mean(), 1)} ({num(x.std(ddof=1), 1)})")
        filas.append(celdas)
    return _tabla_md(
        "Tabla S6. Instrumentos complementarios: SUS y autorregistro (Datos simulados)",
        ["Instrumento", "Pre: media (DE)", "Post: media (DE)"],
        filas,
        nota_sim + " Complementarios (3.4.2 d y e): no contrastan hipótesis.",
    )


def _tablas_replicas(contexto: dict) -> list[str]:
    resumen, hip = contexto["resumen_replicas"], contexto["hipotesis_replicas"]
    n = contexto["n_replicas"]
    semillas = contexto["semillas"]
    nota = (
        f"Datos simulados: {n} réplicas con semillas {semillas[0]}…{semillas[-1]}, cada una con "
        "nuevas docentes, O1 y O2, y la misma regla de 3.5.2 (Shapiro-Wilk, luego t o Wilcoxon, "
        "unilateral, α = 0,05). El intervalo 2,5–97,5 % es el de la diferencia de medias entre "
        "réplicas."
    )
    filas = []
    for i, meta in INDICADORES.items():
        r = resumen[i]
        filas.append([
            meta["nombre"], num(r["pct_rechazo"], 1), _p(r["p_mediana"]),
            f"{num(r['dif_media_media'])} [{num(r['dif_p2_5'])}; {num(r['dif_p97_5'])}]",
            f"{num(r['pct_t'], 1)} / {num(r['pct_wilcoxon'], 1)}",
        ])  # fmt: skip
    bloques = [_tabla_md(
        "Tabla S7. Réplicas: % que rechaza H₀ por indicador (Datos simulados)",
        ["Indicador", "% que rechaza H₀", "p mediano", "Dif. de medias: media [2,5 %; 97,5 %]",
         "% t / % Wilcoxon"],
        filas, nota,
    )]  # fmt: skip
    filas = [[h, num(hip[h], 1)] for h in (*HIPOTESIS, "HG")]
    bloques.append(_tabla_md(
        "Tabla S8. Réplicas: % en que cada hipótesis rechaza H₀ con la regla propuesta "
        "(Datos simulados)",
        ["Hipótesis", "% de réplicas"],
        filas,
        nota + " Regla propuesta (ajustes-cap3, punto 10).",
    ))  # fmt: skip
    return bloques


def _tablas_quiebre(contexto: dict) -> list[str]:
    filas = []
    for q in contexto["quiebre"]:
        filas.append([
            q["tarea"], num(q["media_o1_actual"]), num(q["media_o2"]),
            num(q["pct_rechazo_actual"], 1),
            num(q["factor_principal"]), num(q["media_o1_en_factor_principal"]),
            num(q["factor_replicas"]), num(q["media_o1_en_factor_replicas"]),
        ])  # fmt: skip
    bloques = [_tabla_md(
        "Tabla S9. Punto de quiebre por tarea (Datos simulados)",
        ["Tarea", "O1 media hoy (min)", "O2 media (min)", "% réplicas que rechaza hoy",
         "Factor f: corrida principal", "O1 media en f (min)",
         f"Factor f: {META_REPLICAS} % de réplicas", "O1 media en f (min)"],
        filas,
        "Datos simulados. f multiplica solo los tiempos de O1 propios de la tarea (sesión: la "
        "entrega; la elaboración es igual en O1 y O2). Corrida principal: el menor f desde el "
        f"cual todos los f mayores dan p < 0,05 (barrido de {num(contexto['paso_quiebre'])} en "
        f"{num(contexto['paso_quiebre'])} hasta 5). Réplicas: el menor f con el que al menos "
        f"{META_REPLICAS} % de las réplicas rechaza H₀ (bisección, tolerancia "
        f"{num(contexto['tolerancia_quiebre'])}). «—»: no se alcanza con f ≤ 5. La O1 media en f "
        "es la de la corrida principal.",
    )]  # fmt: skip
    filas = []
    for q in contexto["quiebre"]:
        detalle = [p for p in contexto["parametros_quiebre"] if p["tarea"] == q["tarea"]]
        evaluados = {p["parametro"] for p in detalle if p["dentro_del_rango"] is not None}
        filas.append([
            q["tarea"], str(len(evaluados)),
            num(q["factor_principal"]), q["conclusion_principal"],
            num(q["factor_replicas"]), q["conclusion_replicas"],
        ])  # fmt: skip
    bloques.append(_tabla_md(
        "Tabla S10. ¿El punto de quiebre cae dentro de los rangos de DEC-1? Conclusión por tarea "
        "(Datos simulados)",
        ["Tarea", "Parámetros evaluados", "f: corrida principal", "Conclusión (corrida principal)",
         f"f: {META_REPLICAS} % de réplicas", f"Conclusión ({META_REPLICAS} % de réplicas)"],
        filas,
        "Datos simulados. Cada parámetro de O1 de la tarea se multiplica por f (Tabla S9) y se "
        "compara con su rango de DEC-1. «Depende del supuesto»: todos los parámetros evaluados "
        "siguen dentro de su rango, así que el quiebre se alcanza sin salir de lo que el equipo "
        "consideró plausible. «Robusta»: al menos uno sale de su rango. Un rango que empieza en 0 "
        "no cuenta como «dentro del rango» (contiene cualquier valor reducido, así que no "
        "informa) y ese parámetro no se evalúa. El detalle por parámetro está en "
        "simulados_quiebre.csv. parametros.yaml no se modifica.",
    ))  # fmt: skip
    return bloques


def _encabezado(contexto: dict) -> str:
    return (
        "# Tablas de la simulación (Datos simulados)\n\n"
        "Nada de lo que sigue es una medición real: es el ensayo del plan de análisis de 3.5 con "
        "datos simulados (plan.md, decisión 1). Numeradas «S» para no confundirlas con las tablas "
        "de la tesis.\n\n"
        f"- Semilla principal: {contexto['semilla']}. Réplicas: {contexto['n_replicas']} "
        f"(semillas {contexto['semillas'][0]}…{contexto['semillas'][-1]}).\n"
        f"- parametros.yaml: blob {contexto['blob']} (último commit {contexto['commit']}); "
        "no se modifica.\n"
        f"- {_versiones()}.\n"
        "- Figuras: `figuras/<indicador>.png` (diagramas de cajas pre/post, 3.5.1).\n"
    )


def _guardar_figuras(resultado, carpeta: Path) -> None:
    carpeta.mkdir(parents=True, exist_ok=True)
    for indicador in INDICADORES:
        fig = figura(resultado, indicador)
        fig.savefig(carpeta / f"{indicador}.png", dpi=150)


def ejecutar_principal(
    salida: Path = SALIDA,
    replicas: int | None = None,
    procesos: int | None = None,
    paso_quiebre: float = 0.01,
) -> dict:
    """Corrida principal, réplicas, punto de quiebre y figuras; escribe CSV, tablas.md y PNG."""
    salida = Path(salida)
    arbol = parametros.cargar()
    valores = parametros.valores(arbol)
    tabla = klm.construir_tabla(klm.cargar_rutas(), valores)
    semilla = valores["semillas"]["principal"]
    primera, ultima = valores["semillas"]["replicas"]
    cantidad = replicas if replicas is not None else ultima - primera + 1
    semillas = list(range(primera, primera + cantidad))

    resultado = medicion.simular(valores, semilla, tabla)
    principal = analizar(resultado)
    filas_replicas = _correr_replicas(valores, tabla, semillas, procesos)
    resumen = resumir_replicas(filas_replicas)
    hipotesis = resumir_hipotesis(filas_replicas)

    tolerancia = max(paso_quiebre, 0.01)
    quiebre, en_quiebre = [], []
    for tarea, indicador in INDICADOR_DE_TAREA.items():
        q = quiebre_principal(valores, tabla, tarea, semilla, paso_quiebre, 5.0, procesos)
        f_rep = quiebre_replicas(
            valores, tabla, tarea, semillas, procesos, inferior=paso_quiebre, tolerancia=tolerancia
        )
        media_rep = None
        conclusiones = {}
        for criterio, factor in ((CRITERIO_PRINCIPAL, q["factor"]), (CRITERIO_REPLICAS, f_rep)):
            detalle = []
            if factor is not None:
                detalle = parametros_en_quiebre(arbol, valores, tarea, factor)
                en_quiebre += [{"criterio": criterio, **p} for p in detalle]
            conclusiones[criterio] = conclusion_quiebre(detalle)
        if f_rep is not None:
            media_rep = _contraste_tarea((valores, tabla, tarea, semilla, f_rep))["pre_media"]
        quiebre.append({
            "tarea": tarea,
            "indicador": indicador,
            "media_o1_actual": principal["contrastes"][indicador]["pre_media"],
            "media_o2": principal["contrastes"][indicador]["post_media"],
            "p_actual": principal["contrastes"][indicador]["p"],
            "pct_rechazo_actual": resumen[indicador]["pct_rechazo"],
            "factor_principal": q["factor"],
            "media_o1_en_factor_principal": q["media_o1"],
            "factor_replicas": f_rep,
            "media_o1_en_factor_replicas": media_rep,
            "conclusion_principal": conclusiones[CRITERIO_PRINCIPAL],
            "conclusion_replicas": conclusiones[CRITERIO_REPLICAS],
            "paso_barrido": paso_quiebre,
            "tolerancia_biseccion": tolerancia,
            "replicas": cantidad,
        })  # fmt: skip

    contexto = {
        "resultado": resultado, "analisis": principal, "semilla": semilla,
        "semillas": semillas, "n_replicas": cantidad, "resumen_replicas": resumen,
        "hipotesis_replicas": hipotesis, "quiebre": quiebre, "parametros_quiebre": en_quiebre,
        "paso_quiebre": paso_quiebre, "tolerancia_quiebre": tolerancia,
        "blob": _blob(parametros.ARCHIVO), "commit": _commit_de(parametros.ARCHIVO),
    }  # fmt: skip

    escribir_csv(salida / "simulados_principal_filas.csv", _filas_docentes(resultado))
    escribir_csv(salida / "simulados_principal_jamovi.csv", _filas_jamovi(resultado))
    escribir_csv(
        salida / "simulados_principal_contrastes.csv",
        [{"indicador": i, "nombre": INDICADORES[i]["nombre"], "semilla": semilla, **f}
         for i, f in principal["contrastes"].items()]
        + [{"indicador": d["hipotesis"], "nombre": d["indicadores"], "semilla": semilla,
            COLUMNA_DECISION: d[COLUMNA_DECISION]} for d in principal["decisiones_tabla"]],
    )  # fmt: skip
    escribir_csv(salida / "simulados_replicas.csv", filas_replicas)
    escribir_csv(
        salida / "simulados_replicas_resumen.csv",
        [{"indicador": i, **r} for i, r in resumen.items()]
        + [{"indicador": h, "replicas": cantidad, "pct_rechazo": p} for h, p in hipotesis.items()],
    )  # fmt: skip
    escribir_csv(salida / "simulados_quiebre.csv", quiebre + en_quiebre)
    _guardar_figuras(resultado, salida / "figuras")

    bloques = [_encabezado(contexto), *_tablas_principal(contexto)]
    bloques += [*_tablas_replicas(contexto), *_tablas_quiebre(contexto)]
    (salida / "tablas.md").write_text("\n".join(bloques), encoding="utf-8")
    return contexto


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="Análisis de la simulación (datos simulados).")
    sub = parser.add_subparsers(dest="orden", required=True)
    p = sub.add_parser("principal", help="corrida principal, réplicas, quiebre y figuras")
    p.add_argument("--replicas", type=int, default=None, help="por omisión, las de parametros")
    p.add_argument("--procesos", type=int, default=None)
    p.add_argument("--paso-quiebre", type=float, default=0.01)
    p.add_argument("--salida", type=Path, default=SALIDA)
    args = parser.parse_args(argv)
    if args.orden == "principal":
        ejecutar_principal(args.salida, args.replicas, args.procesos, args.paso_quiebre)
        print(f"Salidas (datos simulados) en {args.salida}")


if __name__ == "__main__":
    main()
