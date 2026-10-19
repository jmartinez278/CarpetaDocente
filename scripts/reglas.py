"""Reglas que comparten los hooks de git (.githooks/) y el script de verificación.

Una sola lista de marcas y de archivos prohibidos: si cambia, cambia en los dos lados.
"""

import re
from pathlib import PurePosixPath

# Atribuciones que no van en los commits (CLAUDE.md, "Git y Pull Requests").
MARCAS_PROHIBIDAS = ("Co-Authored-By", "Generated with Claude Code", "Claude-Session")

_ENLACE_MARKDOWN = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_NI_LETRA_NI_GUION = re.compile(r"[^\w\s:-]")


def _normalizar(linea: str) -> str:
    """Minúsculas, sin enlaces de Markdown, emojis ni signos; espacios simples."""
    linea = _ENLACE_MARKDOWN.sub(r"\1", linea)
    return " ".join(_NI_LETRA_NI_GUION.sub(" ", linea).split()).lower()


def _linea_tiene(marca: str, linea: str) -> bool:
    if marca == "Generated with Claude Code":
        # Con o sin emoji y enlace: "🤖 Generated with [Claude Code](https://...)".
        return "generated with" in linea and "claude code" in linea
    return marca.lower() in linea


def marcas_en_mensaje(mensaje: str) -> list[str]:
    """Marcas prohibidas presentes en el mensaje, sin contar los comentarios del editor."""
    lineas = [_normalizar(linea) for linea in mensaje.splitlines() if not linea.startswith("#")]
    return [
        marca for marca in MARCAS_PROHIBIDAS if any(_linea_tiene(marca, texto) for texto in lineas)
    ]


def motivo_prohibido(ruta: str) -> str | None:
    """Por qué la ruta no puede entrar al repo, o None si está permitida."""
    ruta = ruta.replace("\\", "/")
    partes = PurePosixPath(ruta).parts
    nombre = partes[-1] if partes else ""
    if nombre == ".env" or (nombre.startswith(".env.") and nombre != ".env.example"):
        return "secretos (.env); solo se sube .env.example sin valores"
    if partes and partes[0] == "insumos":
        return "material local (insumos/)"
    if "node_modules" in partes:
        return "dependencias de Node (node_modules/)"
    if "static/dist/" in ruta + "/":
        return "CSS y JS compilados (static/dist/)"
    if nombre == "coverage.xml":
        return "informe de cobertura generado (coverage.xml)"
    return None


def archivos_prohibidos(rutas: list[str]) -> list[tuple[str, str]]:
    """Pares (ruta, motivo) de las rutas prohibidas, en el orden recibido."""
    return [(ruta, motivo) for ruta in rutas if (motivo := motivo_prohibido(ruta))]
