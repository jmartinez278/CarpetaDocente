"""Sube la versión de un documento de docs/: git mv, encabezado, historial y enlace del README.

Uso:
    uv run python scripts/subir_version.py "docs/01 Inicio/07. ... V_1_0_0.md" --descripcion "..."
    uv run python scripts/subir_version.py <ruta> --descripcion "..." --mayor   # V_2_0_0
    uv run python scripts/subir_version.py <ruta> --descripcion "..." --fecha 19/10/2026

Versión menor por defecto (V_1_x_0). Renombra con `git mv` (el cambio queda en el
índice), actualiza los campos Versión y Fecha del encabezado, agrega la fila al final
del historial de cambios y cambia el enlace del README. Si algo falta, no cambia nada.
El contenido del documento se edita aparte; no hace commit.
"""

import argparse
import re
import subprocess
import sys
from datetime import date
from pathlib import Path, PurePosixPath

RAIZ = Path(__file__).resolve().parents[1]
AUTOR = "Equipo del proyecto"

_VERSION_NOMBRE = re.compile(r" V_(\d+)_(\d+)_(\d+)\.md$")
_CAMPO_VERSION = re.compile(r"^\| \*\*Versión\*\* \| [^|]+ \|$", re.MULTILINE)
_CAMPO_FECHA = re.compile(r"^\| \*\*Fecha\*\* \| [^|]+ \|$", re.MULTILINE)
_HISTORIAL = "## Historial de cambios"


class DocumentoInvalido(Exception):
    """Falta algo que la subida necesita: no se cambia ningún archivo."""


def version_del_nombre(ruta: str) -> str:
    coincidencia = _VERSION_NOMBRE.search(ruta)
    if coincidencia is None:
        raise DocumentoInvalido(f"el nombre no termina en V_x_y_z.md: {ruta}")
    return ".".join(coincidencia.groups())


def siguiente_version(version: str, mayor: bool = False) -> str:
    principal, menor, _ = (int(n) for n in version.split("."))
    return f"{principal + 1}.0.0" if mayor else f"{principal}.{menor + 1}.0"


def ruta_con_version(ruta: str, version: str) -> str:
    return _VERSION_NOMBRE.sub(f" V_{version.replace('.', '_')}.md", ruta)


def actualizar_encabezado(texto: str, version: str, fecha: str) -> str:
    if not _CAMPO_VERSION.search(texto) or not _CAMPO_FECHA.search(texto):
        raise DocumentoInvalido("el encabezado no tiene los campos Versión y Fecha")
    texto = _CAMPO_VERSION.sub(f"| **Versión** | {version} |", texto, count=1)
    return _CAMPO_FECHA.sub(f"| **Fecha** | {fecha} |", texto, count=1)


def agregar_historial(texto: str, version: str, fecha: str, autor: str, descripcion: str) -> str:
    if "|" in descripcion:
        raise DocumentoInvalido("la descripción no puede llevar '|': rompe la tabla")
    lineas = texto.split("\n")
    try:
        inicio = lineas.index(_HISTORIAL)
    except ValueError:
        raise DocumentoInvalido(f"no tiene la sección '{_HISTORIAL}'") from None
    ultima = None
    for i in range(inicio + 1, len(lineas)):
        if lineas[i].startswith("|"):
            ultima = i
        elif ultima is not None:
            break
    if ultima is None:
        raise DocumentoInvalido("el historial de cambios no tiene tabla")
    lineas.insert(ultima + 1, f"| {version} | {fecha} | {autor} | {descripcion} |")
    return "\n".join(lineas)


def actualizar_readme(texto: str, ruta_vieja: str, ruta_nueva: str) -> str:
    enlace = f"(<{ruta_vieja}>)"
    if enlace not in texto:
        raise DocumentoInvalido(f"el README no enlaza a {ruta_vieja}")
    return texto.replace(enlace, f"(<{ruta_nueva}>)")


def subir(
    raiz: Path,
    ruta: str,
    descripcion: str,
    mayor: bool = False,
    fecha: str | None = None,
    autor: str = AUTOR,
) -> str:
    """Sube la versión de `ruta` (relativa a `raiz`, con /) y devuelve la ruta nueva."""
    ruta = PurePosixPath(ruta).as_posix()
    origen = raiz / ruta
    if not origen.is_file():
        raise DocumentoInvalido(f"no existe {ruta}")
    fecha = fecha or date.today().strftime("%d/%m/%Y")
    version = siguiente_version(version_del_nombre(ruta), mayor)
    nueva = ruta_con_version(ruta, version)

    # Se arma todo en memoria antes de tocar el disco: si algo falta, no cambia nada.
    texto = origen.read_text(encoding="utf-8")
    texto = agregar_historial(
        actualizar_encabezado(texto, version, fecha), version, fecha, autor, descripcion
    )
    readme = raiz / "README.md"
    texto_readme = actualizar_readme(readme.read_text(encoding="utf-8"), ruta, nueva)

    subprocess.run(["git", "mv", ruta, nueva], cwd=raiz, check=True, capture_output=True)
    (raiz / nueva).write_text(texto, encoding="utf-8", newline="")
    readme.write_text(texto_readme, encoding="utf-8", newline="")
    return nueva


def main(argv: list[str] | None = None, raiz: Path = RAIZ) -> int:
    parser = argparse.ArgumentParser(description="Sube la versión de un documento de docs/.")
    parser.add_argument("ruta", help="ruta del documento, relativa a la raíz del repo")
    parser.add_argument("--descripcion", required=True, help="fila del historial de cambios")
    parser.add_argument("--mayor", action="store_true", help="cambio estructural: V_(x+1)_0_0")
    parser.add_argument("--fecha", help="dd/mm/aaaa (por defecto, hoy)")
    parser.add_argument("--autor", default=AUTOR, help=f"por defecto, {AUTOR}")
    args = parser.parse_args(argv)
    try:
        nueva = subir(raiz, args.ruta, args.descripcion, args.mayor, args.fecha, args.autor)
    except DocumentoInvalido as error:
        print(f"No se cambió nada: {error}.", file=sys.stderr)
        return 2
    print(f"{args.ruta}\n  → {nueva}")
    return 0


if __name__ == "__main__":
    # En Windows, sin esto los acentos salen rotos cuando la salida no es una consola.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
