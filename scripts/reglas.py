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


# Patrones de claves en las líneas agregadas (pre-commit). Cada expresión está escrita de
# forma que no se detecta a sí misma: este archivo pasa por el mismo hook.
PATRONES_CLAVE = (
    ("clave de Django", re.compile(r"django-insecure[-]")),
    (
        "SECRET_KEY con valor literal",
        re.compile(r"SECRET_KEY['\"]?\s*[:=]\s*['\"][^'\"]+['\"]"),
    ),
    ("token de SonarQube", re.compile(r"\bsq[pau]_[0-9a-f]{40}\b")),
    (
        "token de GitHub",
        re.compile(r"\b(?:gh[po]_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{22,})"),
    ),
    ("clave de acceso de AWS", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("llave privada", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    # usuario:contraseña@ en una URL. Los marcadores <usuario>:<contraseña> no cuentan.
    ("cadena de conexión", re.compile(r"\b[a-z][a-z0-9+.-]*://[^\s:/@<>'\"]+:[^\s@/<>'\"]+@")),
)
ARCHIVOS_EXENTOS_DE_CLAVES = {".env.example"}
# Las pruebas pueden usar valores falsos si la línea lo dice: "clave_ficticia", "ficticio"...
_MARCA_FICTICIA = re.compile(r"fictici[oa]", re.IGNORECASE)


def _es_prueba(partes: tuple[str, ...]) -> bool:
    return "tests" in partes[:-1] or (bool(partes) and partes[-1].startswith("test_"))


def claves_en_linea(ruta: str, linea: str) -> list[tuple[str, str]]:
    """(tipo, fragmento) de la primera clave que aparece en la línea, o [] si no hay.

    El fragmento son los primeros caracteres seguidos de "…": nunca el valor completo.
    """
    partes = PurePosixPath(ruta.replace("\\", "/")).parts
    if partes and partes[-1] in ARCHIVOS_EXENTOS_DE_CLAVES:
        return []
    if _es_prueba(partes) and _MARCA_FICTICIA.search(linea):
        return []
    for nombre, patron in PATRONES_CLAVE:
        if encontrada := patron.search(linea):
            return [(nombre, encontrada.group(0)[:4] + "…")]
    return []
