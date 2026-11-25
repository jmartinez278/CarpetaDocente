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
from functools import partial
from pathlib import Path

import numpy as np
from scipy import stats
from scipy.stats import rankdata

from simulacion import docentes as modulo_docentes
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
    if indicador == "likert_global":
        return f"{texto} (apoyo; no entra en HE ni HG; datos simulados)"
    if indicador not in HIPOTESIS_DE:
        return f"{texto} (complementario del escenario; no entra en HE ni HG; datos simulados)"
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


def analizar(resultado, indicadores: dict | None = None) -> dict:
    contrastes = {}
    for indicador, meta in (indicadores or INDICADORES).items():
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


def _simular(valores, tabla, semilla, ajuste=None):
    resultado = medicion.simular(valores, semilla, tabla)
    return ajuste(resultado, valores, tabla, semilla) if ajuste else resultado


def _una_replica(tarea) -> list[dict]:
    valores, tabla, semilla, ajuste, indicadores = tarea
    resultado = _simular(valores, tabla, semilla, ajuste)
    filas = []
    for indicador, meta in indicadores.items():
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


def replicas(
    valores: dict,
    tabla: dict,
    semillas,
    procesos: int | None = None,
    ajuste=None,
    indicadores: dict | None = None,
) -> list[dict]:
    """Una fila por semilla e indicador. No toca la base: solo ``medicion.simular``.

    ``ajuste`` (escenarios) recibe el resultado de cada semilla y devuelve otro.
    """
    indicadores = indicadores or INDICADORES
    tareas = [(valores, tabla, int(s), ajuste, indicadores) for s in semillas]
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


# --- Escenarios ---------------------------------------------------------------------------------
# Cada escenario cambia una copia de los valores o de las rutas; la corrida principal y
# parametros.yaml no cambian. Se corre con la semilla principal y con las mismas réplicas.

MARCA_MASIVO = "restantes"  # «Marcar los N restantes como Asistió» (marcado masivo)


def rutas_sin_marcado_masivo(rutas: list[dict]) -> list[dict]:
    """Asistencia marcada estudiante por estudiante, como quien no encuentra el botón masivo.

    Quita el paso del marcado masivo y los pasos ``por_excepcion`` pasan a ``por_estudiante``.
    No cuenta un segundo toque para quien no asistió: es una cota inferior del tiempo.
    """
    salida = []
    for ruta in rutas:
        ruta = copy.deepcopy(ruta)
        if ruta["tarea"].startswith("asistencia_"):
            masivos = [p for p in ruta["pasos"] if MARCA_MASIVO in p["objetivo"]]
            if len(masivos) != 1:
                raise ValueError(
                    f"{ruta['persona']} · {ruta['tarea']}: se esperaba un paso de marcado masivo "
                    f"(«{MARCA_MASIVO}» en el objetivo) y hay {len(masivos)}."
                )
            pasos = []
            for paso in ruta["pasos"]:
                if paso is masivos[0]:
                    continue
                if paso.pop("por_excepcion", False):
                    paso["por_estudiante"] = True
                pasos.append(paso)
            ruta["pasos"] = pasos
        salida.append(ruta)
    return salida


def valores_tutora_marca_todas(valores: dict) -> dict:
    """La tutora marca también Inglés y Educación Física (nota de ``areas_de_docente_de_curso``)."""
    otros = copy.deepcopy(valores)
    otros["catalogo"]["areas_de_docente_de_curso"] = []
    return otros


ARCHIVO_ESCENARIOS = Path(__file__).with_name("escenarios.yaml")
INDICADOR_DIA = {
    "sesion_dia_min": {
        "nombre": "Tiempo de elaborar y entregar las sesiones de un día (escenario)",
        "unidad": "min por día",
        "sentido": "menor",
    }
}


def cargar_escenarios(ruta: Path = ARCHIVO_ESCENARIOS) -> dict:
    """Supuestos de los escenarios, con el validador de parametros.yaml."""
    return parametros.cargar(ruta)


def _rng_escenario(semilla: int) -> np.random.Generator:
    """Quinto hijo de la semilla: no cambia docentes, O1, O2 ni la carga (G3)."""
    return np.random.default_rng(np.random.SeedSequence(semilla).spawn(5)[4])


def _copiar(resultado):
    return medicion.Resultado(docentes=resultado.docentes, filas=copy.deepcopy(resultado.filas))


def ajustar_cola(resultado, valores, tabla, semilla, esc, n_fijo=None, impresion=False):
    """«Entrega con cola»: O1 = ir a la puerta + cola (una vez al día) + revisión presencial por
    sesión (+ impresión en la variante). O2 sigue con el KLM de subir y enviar.

    Por sesión: (puerta + cola [+ librería]) ÷ n + revisión [+ impresión propia]. Por día: n
    elaboraciones + la entrega del día. La cola, la revisión y la impresión no dependen del ritmo
    de la docente: solo llevan el ruido de medición.
    """
    rng = _rng_escenario(semilla)
    cv = valores["ruido"]["medicion_cv"]

    def ruido():
        return float(modulo_docentes.factor_lognormal(rng, cv))

    otro = _copiar(resultado)
    por = {(f["codigo"], f["momento"]): f for f in otro.filas}
    minimo, maximo = esc["sesiones_dia"]
    imp = esc["impresion"]
    mediana = valores["o1"]["sesion"]["elaboracion_mediana"]
    for momento in ("pretest", "postest"):
        for d in otro.docentes:
            fila = por[(d.codigo, momento)]
            n = n_fijo or int(rng.integers(minimo, maximo + 1))
            elaboraciones = fila["sesion_elaboracion_min"] + sum(
                mediana * d.ritmo * ruido() for _ in range(n - 1)
            )
            propia = rng.random() < imp["proporcion_impresora_propia"]
            if momento == "pretest":
                dia = (esc["ir_a_la_puerta"] + esc["espera_cola"]) * ruido()
                dia += sum(esc["revision_presencial"] * ruido() for _ in range(n))
                if impresion:
                    dia += (
                        n * imp["propia_por_sesion"] * ruido()
                        if propia
                        else imp["libreria_por_dia"] * ruido()
                    )
                fila["sesion_entrega_min"] = dia / n
                fila["sesion_min"] = fila["sesion_elaboracion_min"] + dia / n
            else:
                lento = valores["o2"][f"factor_no_experto_{d.persona.lower()}"] * d.ritmo
                envio = medicion._klm(tabla, d.persona, "sesion_entrega", d.n_estudiantes)
                dia = fila["sesion_entrega_min"] + sum(
                    envio * lento * ruido() for _ in range(n - 1)
                )
            fila["sesiones_dia"] = n
            fila["sesion_dia_min"] = elaboraciones + dia
    return otro


def ajustar_banco(resultado, valores, tabla, semilla, esc):
    """«Con banco de sesiones»: en O2, quien no tiene una sesión propia adecuada y encuentra una
    en el repositorio la descarga y la adapta (fracción de la elaboración + descarga). O1 no
    cambia. La descarga es SUPUESTO hasta grabar la ruta del agente (pendientes.md).
    """
    rng = _rng_escenario(semilla)
    cv = valores["ruido"]["medicion_cv"]
    otro = _copiar(resultado)
    por = {(f["codigo"], f["momento"]): f for f in otro.filas}
    for d in otro.docentes:
        tiene_propia = rng.random() < esc["proporcion_con_archivo_propio"]
        encuentra = rng.random() < esc["cobertura_repositorio"]
        ruido = float(modulo_docentes.factor_lognormal(rng, cv))
        if tiene_propia or not encuentra:
            continue
        fila = por[(d.codigo, "postest")]
        elaboracion = (
            fila["sesion_elaboracion_min"] * esc["fraccion_adaptacion"]
            + esc["descarga"] * d.ritmo * ruido
        )
        fila["sesion_elaboracion_min"] = elaboracion
        fila["sesion_min"] = elaboracion + fila["sesion_entrega_min"]
    return otro


def _ajuste_cola(esc, **opciones):
    return partial(ajustar_cola, esc=esc["entrega_con_cola"], **opciones)


def _ajuste_banco(esc):
    return partial(ajustar_banco, esc=esc["con_banco"])


CON_DIA = {**INDICADORES, **INDICADOR_DIA}
ESCENARIOS = {
    "sin_marcado_masivo": {
        "nombre": "Sin marcado masivo (asistencia uno por uno)",
        "rutas": rutas_sin_marcado_masivo,
    },
    "tutora_marca_todas": {
        "nombre": "La tutora marca todas las áreas",
        "valores": valores_tutora_marca_todas,
    },
    "entrega_con_cola": {
        "nombre": "Entrega con cola (n de 2 a 4)",
        "ajuste": _ajuste_cola,
        "indicadores": CON_DIA,
    },
    "entrega_con_cola_n2": {
        "nombre": "Entrega con cola (n = 2)",
        "ajuste": partial(_ajuste_cola, n_fijo=2),
        "indicadores": CON_DIA,
    },
    "entrega_con_cola_n4": {
        "nombre": "Entrega con cola (n = 4)",
        "ajuste": partial(_ajuste_cola, n_fijo=4),
        "indicadores": CON_DIA,
    },
    "entrega_con_cola_impresion": {
        "nombre": "Entrega con cola y con impresión (variante)",
        "ajuste": partial(_ajuste_cola, impresion=True),
        "indicadores": CON_DIA,
    },
    "con_banco": {"nombre": "Con banco de sesiones", "ajuste": _ajuste_banco},
}


def correr_escenario(
    valores, rutas, semilla, semillas, procesos=None, ajuste=None, indicadores=None
) -> dict:
    indicadores = indicadores or INDICADORES
    tabla = klm.construir_tabla(rutas, valores)
    filas = _correr_replicas(valores, tabla, semillas, procesos, ajuste, indicadores)
    return {
        "principal": analizar(_simular(valores, tabla, semilla, ajuste), indicadores),
        "resumen": resumir_replicas(filas),
        "hipotesis": resumir_hipotesis(filas),
        "indicadores": indicadores,
    }


BARRIDO_COBERTURAS = [round(0.1 * k, 1) for k in range(7)]
BARRIDO_FRACCIONES = [round(0.3 + 0.1 * k, 1) for k in range(6)]


def barrido_banco(
    replicas: int | None = None,
    procesos: int | None = None,
    coberturas=None,
    fracciones=None,
    propias=None,
) -> list[dict]:
    """% de réplicas en que HE1 rechaza H₀, por cobertura × fracción de adaptación, con la
    proporción con archivo propio en su valor central y en sus extremos."""
    arbol_esc = cargar_escenarios()
    esc = parametros.valores(arbol_esc)["con_banco"]
    valores = parametros.valores(parametros.cargar())
    tabla = klm.construir_tabla(klm.cargar_rutas(), valores)
    primera, ultima = valores["semillas"]["replicas"]
    cantidad = replicas if replicas is not None else ultima - primera + 1
    semillas = range(primera, primera + cantidad)
    rango = dict(parametros.supuestos(arbol_esc))["con_banco.proporcion_con_archivo_propio"]
    propias = propias or [rango[0], esc["proporcion_con_archivo_propio"], rango[1]]
    solo_he1 = {"sesion_min": INDICADORES["sesion_min"]}
    filas = []
    for propia in propias:
        for fraccion in fracciones or BARRIDO_FRACCIONES:
            for cobertura in coberturas or BARRIDO_COBERTURAS:
                otro = dict(
                    esc,
                    proporcion_con_archivo_propio=propia,
                    cobertura_repositorio=cobertura,
                    fraccion_adaptacion=fraccion,
                )
                ajuste = partial(ajustar_banco, esc=otro)
                r = _correr_replicas(valores, tabla, semillas, procesos, ajuste, solo_he1)
                filas.append({
                    "proporcion_con_archivo_propio": propia,
                    "fraccion_adaptacion": fraccion,
                    "cobertura_repositorio": cobertura,
                    "replicas": cantidad,
                    "pct_rechazo_he1": resumir_replicas(r)["sesion_min"]["pct_rechazo"],
                })  # fmt: skip
    return filas


def _tabla_barrido(filas: list[dict]) -> str:
    coberturas = sorted({f["cobertura_repositorio"] for f in filas})
    celdas = {}
    for f in filas:
        clave = (f["proporcion_con_archivo_propio"], f["fraccion_adaptacion"])
        celdas.setdefault(clave, {})[f["cobertura_repositorio"]] = f["pct_rechazo_he1"]
    filas_md = [
        [num(p, 2), num(fr, 1), *(num(c[cob], 1) for cob in coberturas)]
        for (p, fr), c in sorted(celdas.items())
    ]
    return _tabla_md(
        "Tabla S13. Con banco de sesiones: % de réplicas en que HE1 rechaza H₀ por cobertura del "
        "repositorio y fracción de adaptación (Datos simulados)",
        ["Con archivo propio", "Fracción de adaptación",
         *(f"Cobertura {num(c, 1)}" for c in coberturas)],
        filas_md,
        f"Datos simulados ({filas[0]['replicas']} réplicas por celda). Solo ahorra en O2 quien no "
        "tiene una sesión propia adecuada y encuentra una en el repositorio: la descarga (1 min, "
        "SUPUESTO hasta grabar la ruta del agente) y la adapta en una fracción del tiempo de "
        "elaborarla. Cobertura 0 equivale a la corrida principal. HE1 sigue midiendo «elaborar» "
        "(ajustes-cap3, punto 13).",
    )  # fmt: skip


def _filas_escenario(clave: str, nombre: str, r: dict) -> list[dict]:
    filas = []
    for indicador, meta in r["indicadores"].items():
        c = r["principal"]["contrastes"][indicador]
        rep = r["resumen"][indicador]
        filas.append({
            "escenario": clave, "nombre_escenario": nombre, "indicador": indicador,
            "nombre": meta["nombre"], "pre_media": c["pre_media"], "post_media": c["post_media"],
            "dif_media": c["dif_media"], "prueba": c["prueba"], "p": c["p"],
            "efecto_nombre": c["efecto_nombre"], "efecto": c["efecto"],
            COLUMNA_DECISION: c[COLUMNA_DECISION], "replicas": rep["replicas"],
            "pct_rechazo_replicas": rep["pct_rechazo"],
        })  # fmt: skip
    for h, pct in r["hipotesis"].items():
        decision = next(
            d[COLUMNA_DECISION] for d in r["principal"]["decisiones_tabla"] if d["hipotesis"] == h
        )
        filas.append({
            "escenario": clave, "nombre_escenario": nombre, "indicador": h,
            COLUMNA_DECISION: decision, "pct_rechazo_replicas": pct,
        })  # fmt: skip
    return filas


def _tablas_escenarios(resultados: dict, contexto: dict) -> str:
    nota = (
        f"Datos simulados (semilla {contexto['semilla']}; {contexto['n_replicas']} réplicas con "
        f"semillas {contexto['semillas'][0]}…{contexto['semillas'][-1]}). Cada escenario cambia "
        "una copia de los valores o de las rutas; parametros.yaml no se modifica. Misma regla de "
        "3.5.2 (unilateral, α = 0,05)."
    )
    filas = []
    for clave, nombre in contexto["nombres"]:
        for indicador, meta in resultados[clave]["indicadores"].items():
            c = resultados[clave]["principal"]["contrastes"][indicador]
            filas.append([
                nombre, meta["nombre"], num(c["pre_media"]), num(c["post_media"]),
                num(c["variacion_pct"], 1), _p(c["p"]), c[COLUMNA_DECISION],
                num(resultados[clave]["resumen"][indicador]["pct_rechazo"], 1),
            ])  # fmt: skip
    bloques = [
        "# Escenarios de la simulación (Datos simulados)\n\n"
        "Nada de lo que sigue es una medición real. «Base» es la corrida principal de tablas.md.\n"
        f"parametros.yaml: blob {contexto['blob']}; no se modifica.\n",
        _tabla_md(
            "Tabla S11. Escenarios: medias, p de la corrida principal y % de réplicas que rechaza "
            "H₀ (Datos simulados)",
            ["Escenario", "Indicador", "O1 media", "O2 media", "Variación (%)",
             "p (corrida principal)", COLUMNA_DECISION, "% réplicas que rechaza H₀"],
            filas,
            nota + " «Sin marcado masivo»: la asistencia se marca estudiante por estudiante (sin "
            "segundo toque para quien no asistió: cota inferior). «La tutora marca todas»: "
            "también Inglés y Educación Física; como suma competencias, cambia cuántos números "
            "saca el generador y las demás mediciones de ese escenario también varían por azar "
            "(por ejemplo, sesión), no por efecto del escenario.",
        ),
    ]  # fmt: skip
    filas = []
    for clave, nombre in contexto["nombres"]:
        r = resultados[clave]
        for d in r["principal"]["decisiones_tabla"]:
            filas.append([
                nombre, d["hipotesis"], d[COLUMNA_DECISION], num(r["hipotesis"][d["hipotesis"]], 1)
            ])  # fmt: skip
    bloques.append(
        _tabla_md(
            "Tabla S12. Escenarios: decisión por hipótesis con la regla propuesta "
            "(Datos simulados)",
            ["Escenario", "Hipótesis", f"{COLUMNA_DECISION}, corrida principal", "% réplicas"],
            filas,
            nota + " Regla propuesta (ajustes-cap3, punto 10).",
        )
    )
    return "\n".join(bloques)


def ejecutar_escenarios(
    salida: Path = SALIDA,
    nombres: list[str] | None = None,
    replicas: int | None = None,
    procesos: int | None = None,
    barrido: bool = True,
) -> dict:
    """Corre «base» y cada escenario; escribe simulados_escenarios.csv y tablas_escenarios.md.

    Con ``barrido`` y el escenario del banco, agrega el barrido cobertura × fracción (S13).
    """
    salida = Path(salida)
    nombres = list(nombres or ESCENARIOS)
    valores = parametros.valores(parametros.cargar())
    rutas = klm.cargar_rutas()
    semilla = valores["semillas"]["principal"]
    primera, ultima = valores["semillas"]["replicas"]
    cantidad = replicas if replicas is not None else ultima - primera + 1
    semillas = list(range(primera, primera + cantidad))

    resultados = {"base": correr_escenario(valores, rutas, semilla, semillas, procesos)}
    etiquetas = [("base", "Base")]
    esc = parametros.valores(cargar_escenarios())
    for clave in nombres:
        definicion = ESCENARIOS[clave]
        v = definicion.get("valores", lambda x: x)(valores)
        r = definicion.get("rutas", lambda x: x)(rutas)
        ajuste = definicion["ajuste"](esc) if "ajuste" in definicion else None
        resultados[clave] = correr_escenario(
            v, r, semilla, semillas, procesos, ajuste, definicion.get("indicadores")
        )
        etiquetas.append((clave, definicion["nombre"]))

    filas = []
    for clave, nombre in etiquetas:
        filas += _filas_escenario(clave, nombre, resultados[clave])
    escribir_csv(salida / "simulados_escenarios.csv", filas)
    contexto = {
        "semilla": semilla, "semillas": semillas, "n_replicas": cantidad,
        "nombres": etiquetas, "blob": _blob(parametros.ARCHIVO),
    }  # fmt: skip
    texto = _tablas_escenarios(resultados, contexto)
    if barrido and "con_banco" in nombres:
        filas_barrido = barrido_banco(replicas, procesos)
        escribir_csv(salida / "simulados_banco_barrido.csv", filas_barrido)
        texto += "\n" + _tabla_barrido(filas_barrido)
    (salida / "tablas_escenarios.md").write_text(texto, encoding="utf-8")
    return resultados


# --- Sensibilidad -------------------------------------------------------------------------------
# Un supuesto a la vez, en el mínimo y el máximo de su rango (DEC-1), con la semilla principal y
# las mismas réplicas. Los de escenarios.yaml se varían dentro de su escenario. Quedan fuera: los
# cortes del Likert (una lista), las n de la cola (escenarios n = 2 y n = 4), la impresión (es una
# variante) y las proporciones del banco (barrido de la Tabla S13).

SUPUESTOS_ESCENARIO = {
    "entrega_con_cola.ir_a_la_puerta": "entrega_con_cola",
    "entrega_con_cola.espera_cola": "entrega_con_cola",
    "entrega_con_cola.revision_presencial": "entrega_con_cola",
    "con_banco.descarga": "con_banco",
}
CONTEXTOS = ("base", "entrega_con_cola", "con_banco")


def variantes_sensibilidad(arbol: dict, cargar_esc: bool = True) -> list[dict]:
    variantes = []
    fuentes = [("parametros", arbol, None)]
    if cargar_esc:
        fuentes.append(("escenarios", cargar_escenarios(), SUPUESTOS_ESCENARIO))
    for archivo, origen, filtro in fuentes:
        for ruta, (minimo, maximo) in parametros.supuestos(origen):
            if isinstance(parametros.valor(origen, ruta), list):
                continue
            if filtro is not None and ruta not in filtro:
                continue
            contexto = filtro[ruta] if filtro else "base"
            for extremo, valor in (("mínimo", minimo), ("máximo", maximo)):
                variantes.append({
                    "parametro": ruta, "archivo": archivo, "contexto": contexto,
                    "extremo": extremo, "valor": valor,
                    "valor_actual": parametros.valor(origen, ruta),
                })  # fmt: skip
    return variantes


def _resumen_he(r: dict) -> dict:
    return {"decisiones": r["principal"]["decisiones"], "pct": r["hipotesis"]}


def es_clave(base: dict, variante: dict) -> bool:
    """Cambia una decisión de la corrida principal o cruza el 80 % de réplicas en alguna HE."""
    for h, decision in base["decisiones"].items():
        if variante["decisiones"].get(h) != decision:
            return True
        if (base["pct"][h] >= META_REPLICAS) != (variante["pct"][h] >= META_REPLICAS):
            return True
    return False


def _correr_contexto(contexto, valores, rutas, esc, semilla, semillas, procesos):
    if contexto == "base":
        return correr_escenario(valores, rutas, semilla, semillas, procesos)
    definicion = ESCENARIOS[contexto]
    return correr_escenario(
        valores, rutas, semilla, semillas, procesos, definicion["ajuste"](esc),
        definicion.get("indicadores"),
    )  # fmt: skip


def ejecutar_sensibilidad(
    salida: Path = SALIDA,
    replicas: int | None = None,
    procesos: int | None = None,
    solo: list[str] | None = None,
) -> list[dict]:
    """Escribe simulados_sensibilidad.csv y tablas_sensibilidad.md (S14 y S15)."""
    salida = Path(salida)
    arbol = parametros.cargar()
    arbol_esc = cargar_escenarios()
    valores = parametros.valores(arbol)
    esc = parametros.valores(arbol_esc)
    rutas = klm.cargar_rutas()
    semilla = valores["semillas"]["principal"]
    primera, ultima = valores["semillas"]["replicas"]
    cantidad = replicas if replicas is not None else ultima - primera + 1
    semillas = list(range(primera, primera + cantidad))

    variantes = [v for v in variantes_sensibilidad(arbol) if not solo or v["parametro"] in solo]
    contextos = {v["contexto"] for v in variantes}
    bases = {
        c: _resumen_he(_correr_contexto(c, valores, rutas, esc, semilla, semillas, procesos))
        for c in CONTEXTOS
        if c in contextos
    }
    filas, resumen = [], []
    for v in variantes:
        if v["archivo"] == "parametros":
            vals, e = (
                parametros.valores(parametros.con_valor(arbol, v["parametro"], v["valor"])),
                esc,
            )
        else:
            vals = valores
            e = parametros.valores(parametros.con_valor(arbol_esc, v["parametro"], v["valor"]))
        r = _correr_contexto(v["contexto"], vals, rutas, e, semilla, semillas, procesos)
        he = _resumen_he(r)
        clave = es_clave(bases[v["contexto"]], he)
        resumen.append({**v, "clave": clave, "base": bases[v["contexto"]], "he": he})
        for indicador in r["indicadores"]:
            c = r["principal"]["contrastes"][indicador]
            filas.append({
                **v, "indicador": indicador, "p_principal": c["p"],
                COLUMNA_DECISION: c[COLUMNA_DECISION],
                "pct_rechazo_replicas": r["resumen"][indicador]["pct_rechazo"],
                "replicas": cantidad, "clave": clave,
            })  # fmt: skip
        for h in (*HIPOTESIS, "HG"):
            filas.append({
                **v, "indicador": h, "decision_principal": he["decisiones"][h],
                "pct_rechazo_replicas": he["pct"][h], "replicas": cantidad, "clave": clave,
            })  # fmt: skip
    escribir_csv(salida / "simulados_sensibilidad.csv", filas)
    (salida / "tablas_sensibilidad.md").write_text(
        _tablas_sensibilidad(resumen, cantidad, semillas), encoding="utf-8"
    )
    return resumen


def _tablas_sensibilidad(resumen: list[dict], cantidad: int, semillas: list[int]) -> str:
    nota = (
        f"Datos simulados (semilla principal 2026; {cantidad} réplicas con semillas "
        f"{semillas[0]}…{semillas[-1]} por variante). Un supuesto a la vez, en el mínimo y el "
        "máximo de su rango; parametros.yaml y escenarios.yaml no se modifican. Contexto: «base» "
        "es la corrida principal; los supuestos de un escenario se varían dentro de él. Regla "
        "propuesta para HE y HG (ajustes-cap3, punto 10)."
    )
    hs = (*HIPOTESIS, "HG")
    claves = [r for r in resumen if r["clave"]]
    filas = []
    for r in claves:
        cambios = [
            h for h in hs
            if r["he"]["decisiones"][h] != r["base"]["decisiones"][h]
            or (r["he"]["pct"][h] >= META_REPLICAS) != (r["base"]["pct"][h] >= META_REPLICAS)
        ]  # fmt: skip
        filas.append([
            r["parametro"], r["contexto"], r["extremo"], num(r["valor"], 3),
            ", ".join(cambios), *(num(r["he"]["pct"][h], 1) for h in hs),
        ])  # fmt: skip
    if not filas:
        filas = [["Ninguno", "—", "—", "—", "—", "—", "—", "—", "—"]]
    bloques = [
        "# Sensibilidad de la simulación (Datos simulados)\n\n"
        "Nada de lo que sigue es una medición real.\n",
        _tabla_md(
            "Tabla S14. Supuestos clave: cambian una decisión de la corrida principal o cruzan el "
            f"{META_REPLICAS} % de réplicas (Datos simulados)",
            ["Supuesto", "Contexto", "Extremo", "Valor", "HE que cambia",
             "% HE1", "% HE2", "% HE3", "% HG"],
            filas,
            nota + f" Clave: cambia la «{COLUMNA_DECISION}» de la corrida principal en alguna HE "
            f"o la HG, o su % de réplicas cruza el {META_REPLICAS} %."
            " Un supuesto que solo cambia cuántos números saca el generad"
            "or (por ejemplo, autorregistro.sesiones_semana, que no entra"
            " en HE1) puede mover la corrida principal por azar; el % de "
            "réplicas muestra si el efecto es real.",
        ),
    ]  # fmt: skip
    por_parametro = {}
    for r in resumen:
        fila = por_parametro.setdefault((r["parametro"], r["contexto"]), {h: 100.0 for h in hs})
        for h in hs:
            fila[h] = min(fila[h], r["he"]["pct"][h])
    orden = sorted(por_parametro.items(), key=lambda kv: (kv[1]["HG"], kv[0]))
    filas = [[p, c, *(num(v[h], 1) for h in hs)] for (p, c), v in orden]
    bloques.append(
        _tabla_md(
            "Tabla S15. Sensibilidad por supuesto: el menor % de réplicas que rechaza H₀ entre "
            "sus dos extremos (Datos simulados)",
            ["Supuesto", "Contexto", "% HE1", "% HE2", "% HE3", "% HG"],
            filas,
            nota + " Ordenada de menor a mayor % de la HG.",
        )
    )
    return "\n".join(bloques)


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="Análisis de la simulación (datos simulados).")
    sub = parser.add_subparsers(dest="orden", required=True)
    p = sub.add_parser("principal", help="corrida principal, réplicas, quiebre y figuras")
    p.add_argument("--replicas", type=int, default=None, help="por omisión, las de parametros")
    p.add_argument("--procesos", type=int, default=None)
    p.add_argument("--paso-quiebre", type=float, default=0.01)
    p.add_argument("--salida", type=Path, default=SALIDA)
    e = sub.add_parser("escenarios", help="base y escenarios, con la corrida principal y réplicas")
    e.add_argument("--solo", nargs="*", choices=list(ESCENARIOS), default=None)
    e.add_argument("--replicas", type=int, default=None)
    e.add_argument("--procesos", type=int, default=None)
    e.add_argument("--salida", type=Path, default=SALIDA)
    s = sub.add_parser("sensibilidad", help="un supuesto a la vez, en el mínimo y el máximo")
    s.add_argument("--solo", nargs="*", default=None)
    s.add_argument("--replicas", type=int, default=None)
    s.add_argument("--procesos", type=int, default=None)
    s.add_argument("--salida", type=Path, default=SALIDA)
    args = parser.parse_args(argv)
    if args.orden == "principal":
        ejecutar_principal(args.salida, args.replicas, args.procesos, args.paso_quiebre)
    elif args.orden == "escenarios":
        ejecutar_escenarios(args.salida, args.solo, args.replicas, args.procesos)
    else:
        ejecutar_sensibilidad(args.salida, args.replicas, args.procesos, args.solo)
    print(f"Salidas (datos simulados) en {args.salida}")


if __name__ == "__main__":
    main()
