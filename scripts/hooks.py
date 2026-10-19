"""Lógica de los hooks de git versionados en .githooks/.

Los archivos de .githooks/ solo llaman a este módulo con `uv run`, así la lógica es
la misma en Windows (Git para Windows) y en Linux, y tiene pruebas.
"""

import re
import subprocess
import sys
from pathlib import Path

import reglas

COMANDOS_RUFF = (
    ("uv", "run", "ruff", "check"),
    ("uv", "run", "ruff", "format", "--check"),
)
# Solo las líneas agregadas (-U0), con rutas sin prefijo a/ b/ ni comillas por acentos,
# y sin color ni diff externo aunque la configuración personal de git los pida.
DIFF_INDICE = (
    "git",
    "-c",
    "core.quotePath=false",
    "diff",
    "--cached",
    "-U0",
    "--no-color",
    "--no-ext-diff",
    "--no-prefix",
    "--diff-filter=ACMR",
)
_TRAMO = re.compile(r"^@@ -\S+ \+(\d+)")


def archivos_en_indice() -> list[str]:
    """Rutas agregadas, copiadas, modificadas o renombradas en el índice."""
    salida = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    ).stdout
    return [ruta for ruta in salida.split("\0") if ruta]


def leer_diff(texto: str) -> list[tuple[str, int, str]]:
    """(ruta, número de línea, texto) de cada línea agregada en un diff unificado."""
    lineas = []
    ruta, numero, en_cabecera = None, 0, False
    for linea in texto.splitlines():
        if linea.startswith("diff --git "):
            ruta, en_cabecera = None, True
        elif en_cabecera and linea.startswith("+++ "):
            ruta = linea[4:].rstrip("\t").strip('"')
        elif tramo := _TRAMO.match(linea):
            numero, en_cabecera = int(tramo.group(1)), False
        elif not en_cabecera and ruta and linea.startswith("+"):
            lineas.append((ruta, numero, linea[1:]))
            numero += 1
    return lineas


def lineas_agregadas() -> list[tuple[str, int, str]]:
    salida = subprocess.run(
        list(DIFF_INDICE),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    ).stdout
    return leer_diff(salida)


def correr(comando: list[str]) -> int:
    return subprocess.run(comando, check=False).returncode


def commit_msg(ruta_mensaje: str) -> int:
    mensaje = Path(ruta_mensaje).read_text(encoding="utf-8", errors="replace")
    marcas = reglas.marcas_en_mensaje(mensaje)
    if not marcas:
        return 0
    print("commit-msg: commit rechazado. El mensaje contiene:", file=sys.stderr)
    for marca in marcas:
        print(f"  - {marca}", file=sys.stderr)
    print("Quita esas líneas: los commits van sin atribuciones (CLAUDE.md).", file=sys.stderr)
    return 1


def pre_commit() -> int:
    prohibidos = reglas.archivos_prohibidos(archivos_en_indice())
    if prohibidos:
        print("pre-commit: commit rechazado. Archivos que no van al repo:", file=sys.stderr)
        for ruta, motivo in prohibidos:
            print(f"  - {ruta}: {motivo}", file=sys.stderr)
        print("Sácalos del índice con: git restore --staged <archivo>", file=sys.stderr)
        return 1
    claves = [
        (ruta, numero, tipo, fragmento)
        for ruta, numero, texto in lineas_agregadas()
        for tipo, fragmento in reglas.claves_en_linea(ruta, texto)
    ]
    if claves:
        print("pre-commit: commit rechazado. Posibles claves en líneas agregadas:", file=sys.stderr)
        for ruta, numero, tipo, fragmento in claves:
            print(f"  - {ruta}:{numero}: {tipo} ({fragmento})", file=sys.stderr)
        print("Quita la clave y léela de una variable de entorno (.env).", file=sys.stderr)
        print(
            'Si es un valor falso de una prueba, escribe "ficticio" en esa misma línea.',
            file=sys.stderr,
        )
        return 1
    for comando in COMANDOS_RUFF:
        if correr(list(comando)) != 0:
            texto = " ".join(comando[2:])
            print(f"pre-commit: commit rechazado, falló `{texto}`.", file=sys.stderr)
            print("Corrige con `uv run ruff check --fix` y `uv run ruff format`.", file=sys.stderr)
            return 1
    return 0


def main(argv: list[str]) -> int:
    match argv:
        case ["commit-msg", ruta]:
            return commit_msg(ruta)
        case ["pre-commit"]:
            return pre_commit()
    print(f"hooks.py: hook desconocido {argv!r}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    # Git muestra el stderr del hook: en Windows, sin esto los acentos salen rotos.
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1:]))
