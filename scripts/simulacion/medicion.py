"""Mediciones O1 (pretest) y O2 (postest) de cada docente simulada (G1). Datos simulados.

Por docente y momento: tiempos del Anexo 1 (sesión = elaboración + entrega, notas de una
competencia, asistencia de 5 jornadas), conteos E1–E4 y exactitud del Anexo 3, cuestionario del
Anexo 4, SUS (solo postest) y autorregistro del Anexo 2.

Los tiempos de O2 salen de la tabla KLM de G2 (por persona y tarea), nunca de un reloj. La
semilla se reparte en tres generadores (docentes, O1, O2): cambiar la tabla KLM no cambia O1
ni los rasgos.
"""

from dataclasses import dataclass

import numpy as np

from simulacion import docentes as modulo_docentes
from simulacion.parametros import competencias_tutora

ORIGEN = "Datos simulados"
PERSONAS = ("P1", "P2", "P3")
TAREAS_KLM = (
    "sesion_entrega",
    "notas",
    "asistencia_momento",
    "asistencia_diferido",
    "corregir_nota",
)
JORNADAS = 5  # Anexo 1 (C) y Anexo 3 (B): una semana de 5 jornadas
DIMENSIONES = ("planificacion", "notas", "asistencia")
TOPE_TASA = 0.3  # ninguna tasa por registro pasa de aquí, aunque el cuidado sea bajo


class KLMFaltante(LookupError):
    """O2 no corre sin la tabla KLM completa de G2."""


@dataclass(frozen=True)
class Resultado:
    docentes: list
    filas: list[dict]


def _revisar_klm(klm) -> None:
    if klm is None:
        raise KLMFaltante("Falta la tabla KLM (G2): O2 no se estima sin ella.")
    faltan = [
        f"{persona} · {tarea}"
        for persona in PERSONAS
        for tarea in TAREAS_KLM
        if tarea not in klm.get(persona, {})
    ]
    if faltan:
        raise KLMFaltante("Faltan en la tabla KLM: " + ", ".join(faltan))


def _klm(klm, persona, tarea, n_estudiantes) -> float:
    fila = klm[persona][tarea]
    return fila["fijo"] + fila["por_estudiante"] * n_estudiantes


def nivel(puntaje: int, niveles: dict) -> str:
    """Nivel de percepción del Anexo 4 según sus cortes."""
    for nombre, (desde, hasta) in niveles.items():
        if desde <= puntaje <= hasta:
            return nombre
    raise ValueError(f"Puntaje {puntaje} fuera de los niveles {niveles}.")


def puntaje_sus(respuestas) -> float:
    """SUS: (Σ(impar − 1) + Σ(5 − par)) × 2,5, con los ítems numerados desde 1."""
    impares = sum(r - 1 for r in respuestas[0::2])
    pares = sum(5 - r for r in respuestas[1::2])
    return (impares + pares) * 2.5


def _escala(rng, latente, ruido_item, umbrales, cantidad) -> list[int]:
    items = latente + rng.normal(0.0, ruido_item, cantidad)
    return [int(x) for x in np.searchsorted(umbrales, items) + 1]


def _errores(rng, unidades, por_unidad, tasas, tasa_e4_unidad, tasa_olvido, cuidado):
    """Conteos E1–E4. Cada registro cae en una sola categoría (nota del Anexo 3).

    ``tasas`` son E1, E2 y E3 por registro. E4 marca una unidad entera (competencia sin niveles,
    jornada con fecha errónea) y el olvido deja una unidad entera sin estado (E1).
    """
    p = [min(t * cuidado, TOPE_TASA) for t in tasas]
    codigos = rng.choice(4, size=(unidades, por_unidad), p=[1 - sum(p), *p])
    e4 = rng.random(unidades) < min(tasa_e4_unidad * cuidado, 1.0)
    olvido = rng.random(unidades) < min(tasa_olvido * cuidado, 1.0)
    codigos[e4] = 4
    codigos[olvido] = 1
    conteos = {f"E{i}": int((codigos == i).sum()) for i in range(1, 5)}
    revisados = unidades * por_unidad
    con_error = sum(conteos.values())
    return revisados, conteos, con_error


def _bloque_errores(prefijo, revisados, conteos, con_error) -> dict:
    return {
        f"{prefijo}_revisados": revisados,
        **{f"{prefijo}_{k}": v for k, v in conteos.items()},
        f"{prefijo}_con_error": con_error,
        f"{prefijo}_exactitud": (revisados - con_error) / revisados * 100,
    }


def _tiempos_o1(rng, d, v, ruido):
    o1 = v["o1"]
    elaboracion = o1["sesion"]["elaboracion_mediana"] * d.ritmo * ruido()
    entrega = o1["sesion"]["entrega_mediana"] * d.ritmo * ruido()
    por_estudiante = o1["notas"][f"por_estudiante_{d.medio_notas_o1}"]
    notas = (o1["notas"]["apertura"] + por_estudiante * d.n_estudiantes) * d.ritmo * ruido()
    if rng.random() < o1["corregir_nota"]["probabilidad"]:
        notas += o1["corregir_nota"]["costo"] * d.ritmo
    a = o1["asistencia"]
    base = a["por_estudiante"] * d.n_estudiantes
    if d.modalidad == "diferido":
        base += a["transcripcion_apertura"] + a["transcripcion_por_estudiante"] * d.n_estudiantes
    jornadas = [base * d.ritmo * ruido() for _ in range(JORNADAS)]
    return elaboracion, entrega, notas, jornadas


def _tiempos_o2(rng, d, v, ruido, klm):
    o2 = v["o2"]
    lento = o2[f"factor_no_experto_{d.persona.lower()}"] * d.ritmo
    elaboracion = v["o1"]["sesion"]["elaboracion_mediana"] * d.ritmo * ruido()
    entrega = _klm(klm, d.persona, "sesion_entrega", d.n_estudiantes) * lento * ruido()
    notas = _klm(klm, d.persona, "notas", d.n_estudiantes) * lento * ruido()
    if rng.random() < v["o1"]["corregir_nota"]["probabilidad"]:
        notas += _klm(klm, d.persona, "corregir_nota", d.n_estudiantes) * lento
    asistencia = _klm(klm, d.persona, f"asistencia_{d.modalidad}", d.n_estudiantes)
    jornadas = [asistencia * lento * ruido() for _ in range(JORNADAS)]
    return elaboracion, entrega, notas, jornadas


def _errores_o1(rng, d, v, competencias):
    e = v["errores_o1"]
    n, m = e["notas"], d.medio_notas_o1
    notas = _errores(
        rng, competencias, d.n_estudiantes,
        (n["E1"], n[f"E2_{m}"], n[f"E3_{m}"]), n["E4"], 0.0, d.cuidado,
    )  # fmt: skip
    a, mod = e["asistencia"], d.modalidad
    asistencia = _errores(
        rng, JORNADAS, d.n_estudiantes,
        (a[f"E1_{mod}"], a["E2"], a[f"E3_{mod}"]), a[f"E4_{mod}"],
        a["olvida_dia"] if mod == "diferido" else 0.0, d.cuidado,
    )  # fmt: skip
    return notas, asistencia


def _errores_o2(rng, d, v, competencias):
    e = v["errores_o2"]
    n = e["notas"]
    notas = _errores(
        rng, competencias, d.n_estudiantes,
        (n["E1"], n["E2"], n["E3"] + n["E3_escala_invalida"]), n["E4"], 0.0, d.cuidado,
    )  # fmt: skip
    a = e["asistencia"]
    diferido = d.modalidad == "diferido"
    asistencia = _errores(
        rng, JORNADAS, d.n_estudiantes,
        (a["E1"], a["E2"], a["E3"]),
        a["E4_diferido"] if diferido else a["E4_futuro_o_fin_de_semana"],
        a["olvida_dia"] if diferido else 0.0, d.cuidado,
    )  # fmt: skip
    return notas, asistencia


def _percepcion(rng, d, v, momento) -> dict:
    lk = v["likert"]
    fila = {}
    items = []
    for dim in DIMENSIONES:
        latente = (
            lk["media_pre"]
            + (lk["efecto_post"] if momento == "postest" else 0.0)
            + lk["carga_actitud"] * d.actitud
            + rng.normal(0.0, lk["ruido_docente"])
        )
        respuestas = _escala(
            rng, latente, lk["ruido_item"], lk["umbrales"], lk["items_por_dimension"]
        )
        items += respuestas
        fila[f"likert_{dim}"] = sum(respuestas)
        fila[f"likert_{dim}_nivel"] = nivel(sum(respuestas), lk["niveles_dimension"])
    fila.update({f"likert_{i}": x for i, x in enumerate(items, start=1)})
    fila["likert_global"] = sum(items)
    fila["likert_global_nivel"] = nivel(sum(items), lk["niveles_global"])
    fila["sus"] = None
    if momento == "postest":
        s = v["sus"]
        latente = (
            s["media_latente"]
            + s["carga_destreza"] * d.destreza
            + rng.normal(0.0, lk["ruido_docente"])
        )
        acuerdo = _escala(rng, latente, lk["ruido_item"], lk["umbrales"], s["items"])
        respuestas = [r if i % 2 == 0 else 6 - r for i, r in enumerate(acuerdo)]
        fila["sus"] = puntaje_sus(respuestas)
    return fila


def _autorregistro(rng, d, v, ruido) -> dict:
    sesiones = int(rng.poisson(v["autorregistro"]["sesiones_semana"]))
    mediana = v["o1"]["sesion"]["elaboracion_mediana"]
    total = sum(mediana * d.ritmo * ruido() for _ in range(sesiones))
    return {"autorregistro_sesiones": sesiones, "autorregistro_total_min": total}


def _medir(rng, d, v, momento, competencias, klm) -> dict:
    cv = v["ruido"]["medicion_cv"]

    def ruido():
        return float(modulo_docentes.factor_lognormal(rng, cv))

    if momento == "pretest":
        elaboracion, entrega, notas_min, jornadas = _tiempos_o1(rng, d, v, ruido)
        notas, asistencia = _errores_o1(rng, d, v, competencias)
    else:
        elaboracion, entrega, notas_min, jornadas = _tiempos_o2(rng, d, v, ruido, klm)
        notas, asistencia = _errores_o2(rng, d, v, competencias)
    return {
        "origen": ORIGEN,
        "codigo": d.codigo,
        "momento": momento,
        "sesion_elaboracion_min": elaboracion,
        "sesion_entrega_min": entrega,
        "sesion_min": elaboracion + entrega,
        "notas_min": notas_min,
        "asistencia_jornadas_min": jornadas,
        "asistencia_min": float(np.mean(jornadas)),
        **_bloque_errores("notas", *notas),
        **_bloque_errores("asistencia", *asistencia),
        **_percepcion(rng, d, v, momento),
        **_autorregistro(rng, d, v, ruido),
    }


def simular(valores: dict, semilla: int, klm) -> Resultado:
    """Una corrida completa: docentes, O1 y O2. La misma semilla da la misma salida."""
    _revisar_klm(klm)
    rng_docentes, rng_o1, rng_o2 = (
        np.random.default_rng(s) for s in np.random.SeedSequence(semilla).spawn(3)
    )
    lista = modulo_docentes.generar(valores, rng_docentes)
    competencias = competencias_tutora(valores["catalogo"]["areas_de_docente_de_curso"])
    filas = [_medir(rng_o1, d, valores, "pretest", competencias, klm) for d in lista]
    filas += [_medir(rng_o2, d, valores, "postest", competencias, klm) for d in lista]
    return Resultado(docentes=lista, filas=filas)
