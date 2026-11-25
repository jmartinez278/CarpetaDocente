"""Parámetros de la simulación (G1): carga, validación y acceso a ``parametros.yaml``.

Cada parámetro es un mapa con ``valor`` y su origen: ``fuente`` o ``supuesto: true`` con
``ancla`` y, si el valor es numérico, ``rango`` [mínimo, máximo] para la sensibilidad. Un grupo
es un mapa sin ``valor``. Datos simulados: nada de esto es una medición real.
"""

import copy
import importlib
import sys
from collections.abc import Iterator
from numbers import Real
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[2]
ARCHIVO = Path(__file__).with_name("parametros.yaml")
MIGRACION_CATALOGO = "catalogo.migrations.0002_catalogo_siagie"


class ParametroInvalido(ValueError):
    """Un parámetro no declara su origen o su valor no calza con su rango."""


def cargar(ruta: Path = ARCHIVO) -> dict:
    """Lee el YAML y lo valida; devuelve el árbol con sus metadatos."""
    arbol = yaml.safe_load(ruta.read_text(encoding="utf-8"))
    validar(arbol)
    return arbol


def _es_parametro(nodo) -> bool:
    return isinstance(nodo, dict) and "valor" in nodo


def _recorrer(arbol: dict, prefijo: str = "") -> Iterator[tuple[str, dict]]:
    for clave, nodo in arbol.items():
        ruta = f"{prefijo}{clave}"
        if _es_parametro(nodo):
            yield ruta, nodo
        elif isinstance(nodo, dict):
            yield from _recorrer(nodo, f"{ruta}.")
        else:
            raise ParametroInvalido(f"{ruta}: no es un parámetro (falta «valor») ni un grupo.")


def _numeros(valor) -> list[Real] | None:
    """Los números del valor (escalar o lista de números); ``None`` si no es numérico."""
    if isinstance(valor, bool):
        return None
    if isinstance(valor, Real):
        return [valor]
    if isinstance(valor, list) and valor and all(_numeros(x) for x in valor):
        return list(valor)
    return None


def _error_de(ruta: str, nodo: dict) -> str | None:
    fuente = bool(nodo.get("fuente"))
    supuesto = nodo.get("supuesto") is True
    if fuente and supuesto:
        return f"{ruta}: declara fuente y SUPUESTO; ambos no."
    if not fuente and not supuesto:
        return f"{ruta}: sin fuente ni SUPUESTO."
    if fuente:
        return None
    if not nodo.get("ancla"):
        return f"{ruta}: SUPUESTO sin ancla (si no hay, «sin ancla»)."
    numeros = _numeros(nodo["valor"])
    if numeros is None:
        return None
    rango = nodo.get("rango")
    if not (isinstance(rango, list) and len(rango) == 2 and _numeros(rango)):
        return f"{ruta}: SUPUESTO numérico sin rango [mínimo, máximo]."
    if any(not rango[0] <= x <= rango[1] for x in numeros):
        return f"{ruta}: valor fuera de su rango {rango}."
    return None


def validar(arbol: dict) -> None:
    """Lanza ``ParametroInvalido`` con todos los problemas juntos."""
    errores = [e for ruta, nodo in _recorrer(arbol) if (e := _error_de(ruta, nodo))]
    if errores:
        raise ParametroInvalido("\n".join(errores))


def valores(arbol: dict) -> dict:
    """El mismo árbol con solo los valores (una copia que se puede modificar)."""
    return {
        clave: copy.deepcopy(nodo["valor"]) if _es_parametro(nodo) else valores(nodo)
        for clave, nodo in arbol.items()
    }


def _nodo(arbol: dict, ruta: str) -> dict:
    nodo = arbol
    for clave in ruta.split("."):
        nodo = nodo[clave]
    if not _es_parametro(nodo):
        raise KeyError(ruta)
    return nodo


def valor(arbol: dict, ruta: str):
    return _nodo(arbol, ruta)["valor"]


def con_valor(arbol: dict, ruta: str, nuevo) -> dict:
    """Copia del árbol con un valor cambiado (para la sensibilidad); el original no cambia."""
    otro = copy.deepcopy(arbol)
    _nodo(otro, ruta)["valor"] = nuevo
    return otro


def supuestos(arbol: dict) -> list[tuple[str, list]]:
    """Cada SUPUESTO numérico con su rango, en el orden del YAML."""
    return [
        (ruta, nodo["rango"])
        for ruta, nodo in _recorrer(arbol)
        if nodo.get("supuesto") is True and _numeros(nodo["valor"]) is not None
    ]


def _catalogo():
    backend = str(RAIZ / "src" / "backend")
    if backend not in sys.path:
        sys.path.insert(0, backend)
    return importlib.import_module(MIGRACION_CATALOGO)


def competencias_tutora(areas_de_docente_de_curso) -> int:
    """Competencias que marca la tutora, contadas del catálogo SIAGIE del repo."""
    catalogo = _catalogo()
    excluidas = set(catalogo.AREAS_QUE_NO_SE_TRABAJAN) | set(areas_de_docente_de_curso)
    return sum(
        len(competencias)
        for codigo, _nombre, _transversal, _exonera, competencias in catalogo.CATALOGO
        if codigo not in excluidas
    )
