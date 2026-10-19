"""Prepara la copia del repo que se sube al Proyecto de claude.ai.

Uso:
    uv run python scripts/copiar_para_proyecto.py                # junto al repo
    uv run python scripts/copiar_para_proyecto.py --destino D:\\copia

Copia el repo sin historial de git, entornos, dependencias, archivos generados,
material local ni la carpeta .claude/. Si el destino ya existe, pregunta antes de
reemplazarlo, y solo borra esa carpeta: rechaza un destino dentro del repo, que
contenga al repo o que sea otro repositorio de git.
"""

import argparse
import os
import shutil
import stat
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

import reglas

RAIZ = Path(__file__).resolve().parents[1]
NOMBRE_DESTINO = "CarpetaDocente_para_Proyecto"

# Además de lo que reglas.py prohíbe subir al repo (.env, insumos/, node_modules/,
# static/dist/, coverage.xml).
CARPETAS_EXCLUIDAS = {
    ".git",
    ".venv",
    "node_modules",
    "insumos",
    # Configuración, comandos y skills de Claude Code: no sirven en el Proyecto.
    ".claude",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "htmlcov",
    "test-results",
}
ARCHIVOS_EXCLUIDOS = {"uv.lock", "package-lock.json", "coverage.xml", ".coverage"}
RESPUESTAS_SI = {"s", "si", "sí"}


class DestinoInvalido(Exception):
    """El destino pondría en riesgo el repo u otra carpeta: no se toca nada."""


class CopiaCancelada(Exception):
    """El destino ya existía y no se confirmó reemplazarlo."""


@dataclass
class Resumen:
    destino: Path
    cantidad: int
    tamano: int
    mas_pesados: list[tuple[str, int]]


def excluido(ruta: str) -> bool:
    """True si la ruta (relativa al repo, con /) no va en la copia."""
    partes = PurePosixPath(ruta).parts
    return (
        any(parte in CARPETAS_EXCLUIDAS for parte in partes)
        or (bool(partes) and partes[-1] in ARCHIVOS_EXCLUIDOS)
        or reglas.motivo_prohibido(ruta) is not None
    )


def destino_por_defecto(origen: Path) -> Path:
    return origen.parent / NOMBRE_DESTINO


def _quitar_solo_lectura(funcion, ruta, _excepcion):
    # En Windows, rmtree no borra archivos de solo lectura sin este paso.
    os.chmod(ruta, stat.S_IWRITE)
    funcion(ruta)


def _preparar_destino(origen: Path, destino: Path, preguntar: Callable[[str], str]) -> None:
    if destino == origen or origen in destino.parents:
        raise DestinoInvalido(f"{destino} está dentro del repo")
    if destino in origen.parents:
        raise DestinoInvalido(f"{destino} contiene al repo")
    if not destino.exists():
        return
    if not destino.is_dir():
        raise DestinoInvalido(f"{destino} no es una carpeta")
    if (destino / ".git").exists():
        raise DestinoInvalido(f"{destino} es un repositorio de git")
    try:
        respuesta = preguntar(f"La carpeta {destino} ya existe. ¿Borrarla y reemplazarla? [s/N] ")
    except EOFError:
        respuesta = ""
    if respuesta.strip().lower() not in RESPUESTAS_SI:
        raise CopiaCancelada
    shutil.rmtree(destino, onexc=_quitar_solo_lectura)


def copiar(origen: Path, destino: Path, preguntar: Callable[[str], str] = input) -> Resumen:
    origen, destino = origen.resolve(), destino.resolve()
    _preparar_destino(origen, destino, preguntar)
    copiados: list[tuple[str, int]] = []
    for carpeta, subcarpetas, archivos in os.walk(origen):
        base = Path(carpeta).relative_to(origen)
        # Podar aquí evita recorrer .git, .venv o node_modules.
        subcarpetas[:] = [s for s in subcarpetas if not excluido((base / s).as_posix())]
        for nombre in archivos:
            relativa = (base / nombre).as_posix()
            if excluido(relativa):
                continue
            objetivo = destino / relativa
            objetivo.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(origen / relativa, objetivo)
            copiados.append((relativa, objetivo.stat().st_size))
    pesados = sorted(copiados, key=lambda par: par[1], reverse=True)[:5]
    return Resumen(destino, len(copiados), sum(t for _, t in copiados), pesados)


def tamano_legible(bytes_: int) -> str:
    if bytes_ < 1024:
        return f"{bytes_} B"
    if bytes_ < 1024 * 1024:
        return f"{bytes_ / 1024:.1f} KB".replace(".", ",")
    return f"{bytes_ / (1024 * 1024):.1f} MB".replace(".", ",")


def formatear(resumen: Resumen) -> str:
    lineas = [
        f"Copia lista en: {resumen.destino}",
        f"Archivos copiados: {resumen.cantidad}",
        f"Tamaño total: {tamano_legible(resumen.tamano)}",
        "Los 5 archivos más pesados:",
    ]
    lineas += [f"  {tamano_legible(t):>9}  {ruta}" for ruta, t in resumen.mas_pesados]
    return "\n".join(lineas) + "\n"


def main(
    argv: list[str] | None = None,
    origen: Path = RAIZ,
    preguntar: Callable[[str], str] = input,
) -> int:
    parser = argparse.ArgumentParser(description="Copia del repo para el Proyecto de claude.ai.")
    parser.add_argument(
        "--destino",
        type=Path,
        help=f"carpeta de la copia (por defecto, {NOMBRE_DESTINO} junto al repo)",
    )
    args = parser.parse_args(argv)
    destino = args.destino or destino_por_defecto(origen)
    try:
        resumen = copiar(origen, destino, preguntar)
    except DestinoInvalido as error:
        print(f"No se copió nada: {error}.", file=sys.stderr)
        return 2
    except CopiaCancelada:
        print("No se copió nada: el destino ya existe y no se confirmó.", file=sys.stderr)
        return 1
    print(formatear(resumen), end="")
    return 0


if __name__ == "__main__":
    # En Windows, sin esto los acentos salen rotos cuando la salida no es una consola.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
