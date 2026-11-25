"""Docentes simuladas ``sim01…sim24`` con sus rasgos (G1). Datos simulados.

Cada docente tiene una sección fija (1.º A, 1.º B… 6.º D, en orden) y rasgos sacados con la
semilla: destreza digital (define la persona P1, P2 o P3), actitud (correlacionada con la
destreza), ritmo y cuidado (factores lognormales de mediana 1), modalidad de la asistencia
(en el momento o en diferido, igual en O1 y O2) y medio de las notas en O1 (cuaderno o Excel).
"""

import math
import string
from dataclasses import dataclass

import numpy as np
from scipy.stats import norm


@dataclass(frozen=True)
class Docente:
    usuario: str
    codigo: str
    grado: int
    seccion: str
    n_estudiantes: int
    destreza: float
    actitud: float
    persona: str
    ritmo: float
    cuidado: float
    modalidad: str
    medio_notas_o1: str


def factor_lognormal(rng: np.random.Generator, cv: float, tamano=None):
    """Factor de mediana 1 y coeficiente de variación ``cv``."""
    return rng.lognormal(0.0, math.sqrt(math.log1p(cv**2)), tamano)


def _persona(destreza: float, p1: float, p3: float) -> str:
    """Cortes de la normal estándar: con proporción 0 nadie cae en esa persona."""
    if p1 > 0 and destreza < norm.ppf(p1):
        return "P1"
    if p3 > 0 and destreza >= norm.ppf(1 - p3):
        return "P3"
    return "P2"


def generar(valores: dict, rng: np.random.Generator) -> list[Docente]:
    poblacion, rasgos = valores["poblacion"], valores["rasgos"]
    n = poblacion["n_docentes"]
    por_grado = poblacion["secciones_por_grado"]
    if n != poblacion["grados"] * por_grado:
        raise ValueError("n_docentes debe ser grados × secciones_por_grado (una por sección).")
    p1, p3 = rasgos["proporcion_p1"], rasgos["proporcion_p3"]
    if p1 + p3 > 1:
        raise ValueError("proporcion_p1 + proporcion_p3 no puede pasar de 1.")

    # El orden de las extracciones es fijo: cambiarlo cambia todas las corridas.
    centro, amplitud = poblacion["estudiantes_centro"], poblacion["estudiantes_amplitud"]
    estudiantes = rng.integers(centro - amplitud, centro + amplitud + 1, n)
    rho = rasgos["correlacion_destreza_actitud"]
    z = rng.standard_normal((n, 2))
    destreza = z[:, 0]
    actitud = rho * z[:, 0] + math.sqrt(1 - rho**2) * z[:, 1]
    ritmo = factor_lognormal(rng, rasgos["ritmo_cv"], n)
    cuidado = factor_lognormal(rng, rasgos["cuidado_cv"], n)
    diferido = rng.random(n) < rasgos["proporcion_diferido"]
    excel = rng.random(n) < rasgos["proporcion_excel"]

    ancho = max(2, len(str(n)))
    return [
        Docente(
            usuario=f"sim{i + 1:0{ancho}d}",
            codigo=f"D{i + 1:0{ancho}d}",
            grado=i // por_grado + 1,
            seccion=string.ascii_uppercase[i % por_grado],
            n_estudiantes=int(estudiantes[i]),
            destreza=float(destreza[i]),
            actitud=float(actitud[i]),
            persona=_persona(float(destreza[i]), p1, p3),
            ritmo=float(ritmo[i]),
            cuidado=float(cuidado[i]),
            modalidad="diferido" if diferido[i] else "momento",
            medio_notas_o1="excel" if excel[i] else "cuaderno",
        )
        for i in range(n)
    ]
