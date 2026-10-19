"""Verificación antes de un commit o PR: las comprobaciones que antes se hacían a mano.

Uso:
    uv run python scripts/verificar.py --antes-del-commit  # con lo del commit en el índice
    uv run python scripts/verificar.py                  # veredicto en la terminal
    uv run python scripts/verificar.py --pr 53          # además, checks y aprobación del PR (gh)
    uv run python scripts/verificar.py --markdown       # bloque listo para verificacion.md

Sale con 0 si el veredicto es PASA y con 1 si es NO PASA.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime

import reglas

UMBRAL_COBERTURA = 80
DOMINIO_NOREPLY = "@users.noreply.github.com"

RAMA = ("git", "rev-parse", "--abbrev-ref", "HEAD")
ESTADO = ("git", "status", "--porcelain")
ARCHIVOS = ("git", "ls-files", "-z")
RUFF_CHECK = ("uv", "run", "ruff", "check")
RUFF_FORMAT = ("uv", "run", "ruff", "format", "--check")
PYTEST = ("uv", "run", "pytest", "--cov", f"--cov-fail-under={UMBRAL_COBERTURA}")

_COBERTURA = re.compile(r"Total coverage: (\d+(?:\.\d+)?)%")
# Líneas de pytest que van en la salida resumida: total, umbral y conteo final.
_RESUMEN_PYTEST = re.compile(r"TOTAL|Total coverage|FAIL|ERROR|passed|failed|error")
# Errores de psycopg cuando PostgreSQL (docker compose up -d db) no está levantado.
_SIN_BASE = re.compile(
    r"connection failed|Connection refused|could not connect to server|"
    r"Multiple connection attempts failed",
    re.IGNORECASE,
)
FALLA_SIN_BASE = "¿Docker encendido? La base de datos no responde"


def comando_log(base: str) -> tuple[str, ...]:
    # Campos separados por \x1f y registros por \x1e: el cuerpo puede tener saltos de línea.
    return ("git", "log", "--format=%H%x1f%ae%x1f%s%x1f%B%x1e", f"{base}..HEAD")


def comando_atraso(base: str) -> tuple[str, ...]:
    # Solo la referencia local origin/<base>: no hace fetch ni usa la red.
    return ("git", "rev-list", "--count", f"{base}..origin/{base}")


def comando_checks(pr: str) -> tuple[str, ...]:
    return ("gh", "pr", "checks", pr)


def comando_revisiones(pr: str) -> tuple[str, ...]:
    return ("gh", "pr", "view", pr, "--json", "reviewDecision,latestReviews")


@dataclass(frozen=True)
class Salida:
    codigo: int
    texto: str


@dataclass(frozen=True)
class Commit:
    hash: str
    correo: str
    asunto: str
    mensaje: str

    @property
    def corto(self) -> str:
        return self.hash[:7]


@dataclass
class Resultado:
    nombre: str
    ok: bool
    fallas: list[str] = field(default_factory=list)
    comando: tuple[str, ...] | None = None
    resumen: str = ""


@dataclass
class Informe:
    rama: str
    base: str
    commits: list[Commit]
    resultados: list[Resultado]
    cobertura: float | None
    omitidas: list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)
    antes_del_commit: bool = False

    @property
    def pasa(self) -> bool:
        return all(resultado.ok for resultado in self.resultados)

    @property
    def fallas(self) -> list[str]:
        lista = []
        for resultado in self.resultados:
            if not resultado.ok:
                detalles = resultado.fallas or ["falló"]
                lista.extend(f"{resultado.nombre}: {detalle}" for detalle in detalles)
        return lista


Ejecutor = Callable[[tuple[str, ...]], Salida]


def ejecutar(comando: tuple[str, ...]) -> Salida:
    """Corre el comando sin shell y junta stdout y stderr, como se ven en la terminal."""
    try:
        proceso = subprocess.run(
            list(comando),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except FileNotFoundError:
        return Salida(127, f"{comando[0]}: no se encontró el comando\n")
    return Salida(proceso.returncode, proceso.stdout or "")


def _ultimas_lineas(texto: str, cantidad: int = 3) -> str:
    lineas = [linea for linea in texto.splitlines() if linea.strip()]
    return "\n".join(lineas[-cantidad:])


def _resumen_pytest(texto: str) -> str:
    lineas = [linea for linea in texto.splitlines() if _RESUMEN_PYTEST.search(linea)]
    return "\n".join(lineas[-6:]) or _ultimas_lineas(texto)


def _leer_commits(texto: str) -> list[Commit]:
    commits = []
    for registro in texto.split("\x1e"):
        registro = registro.lstrip("\n")
        if registro.strip():
            hash_, correo, asunto, mensaje = registro.split("\x1f", 3)
            commits.append(Commit(hash_, correo, asunto, mensaje))
    return commits


def _revisar_commits(ejecutar: Ejecutor, base: str) -> tuple[list[Commit], list[Resultado]]:
    salida = ejecutar(comando_log(base))
    if salida.codigo != 0:
        falla = Resultado(
            "Commits sobre la base", False, [_ultimas_lineas(salida.texto, 1)], comando_log(base)
        )
        return [], [falla]
    commits = _leer_commits(salida.texto)
    ajenos = [f"{c.corto} {c.correo}" for c in commits if not c.correo.endswith(DOMINIO_NOREPLY)]
    atribuidos = [
        f"{c.corto} {', '.join(marcas)}"
        for c in commits
        if (marcas := reglas.marcas_en_mensaje(c.mensaje))
    ]
    return commits, [
        Resultado("Correo noreply en los commits", not ajenos, ajenos),
        Resultado("Commits sin atribuciones", not atribuidos, atribuidos),
    ]


def _fuera_del_indice(linea: str) -> bool:
    # git status --porcelain: XY ruta. X es el índice e Y la carpeta de trabajo.
    return linea.startswith("??") or linea[1:2] != " "


def _revisar_arbol(ejecutar: Ejecutor, antes_del_commit: bool) -> list[Resultado]:
    estado = ejecutar(ESTADO)
    cambios = [linea for linea in estado.texto.splitlines() if linea.strip()]
    if antes_del_commit:
        # Antes del commit lo que va a entrar está en el índice: solo sobra lo que no.
        nombre_estado = "Todo lo del commit está en el índice"
        cambios = [linea for linea in cambios if _fuera_del_indice(linea)]
        nombre_prohibidos = "Sin archivos prohibidos en el índice"
    else:
        nombre_estado = "git status limpio"
        nombre_prohibidos = "Sin archivos prohibidos"
    if estado.codigo != 0:
        cambios = cambios or ["git status falló"]
    # git ls-files lista el índice: incluye lo agregado que todavía no tiene commit.
    archivos = [ruta for ruta in ejecutar(ARCHIVOS).texto.split("\0") if ruta]
    prohibidos = [f"{ruta} ({motivo})" for ruta, motivo in reglas.archivos_prohibidos(archivos)]
    return [
        Resultado(nombre_estado, not cambios, cambios, ESTADO, _ultimas_lineas(estado.texto)),
        Resultado(nombre_prohibidos, not prohibidos, prohibidos),
    ]


def _revisar_calidad(ejecutar: Ejecutor) -> tuple[list[Resultado], float | None]:
    resultados = []
    for nombre, comando in (("ruff check", RUFF_CHECK), ("ruff format --check", RUFF_FORMAT)):
        salida = ejecutar(comando)
        resumen = _ultimas_lineas(salida.texto)
        fallas = [] if salida.codigo == 0 else [resumen or f"salió con código {salida.codigo}"]
        resultados.append(Resultado(nombre, salida.codigo == 0, fallas, comando, resumen))

    salida = ejecutar(PYTEST)
    encontrada = _COBERTURA.search(salida.texto)
    cobertura = float(encontrada.group(1)) if encontrada else None
    resumen = _resumen_pytest(salida.texto)
    if salida.codigo == 0:
        fallas = []
    elif _SIN_BASE.search(salida.texto):
        fallas = [FALLA_SIN_BASE]
    else:
        fallas = [_ultimas_lineas(resumen, 1)]
    nombre = f"pytest --cov (mínimo {UMBRAL_COBERTURA} %)"
    resultados.append(Resultado(nombre, salida.codigo == 0, fallas, PYTEST, resumen))
    return resultados, cobertura


def _revisar_atraso(ejecutar: Ejecutor, base: str) -> list[str]:
    """Aviso, sin hacer fallar el veredicto, si la base local está detrás de origin."""
    if base.startswith("origin/"):
        return []
    salida = ejecutar(comando_atraso(base))
    atraso = salida.texto.strip()
    if salida.codigo != 0 or not atraso.isdigit() or int(atraso) == 0:
        return []
    return [f"{base} local desactualizada: haz git pull ({atraso} commits detrás de origin/{base})"]


def _aprobado(datos: dict) -> bool:
    decision = datos.get("reviewDecision") or ""
    if decision:
        return decision == "APPROVED"
    # Sin revisión obligatoria, GitHub no da decisión: basta una aprobación vigente.
    return any(r.get("state") == "APPROVED" for r in datos.get("latestReviews") or [])


def _revisar_pr(ejecutar: Ejecutor, pr: str) -> list[Resultado]:
    checks = ejecutar(comando_checks(pr))
    if checks.codigo == 0:
        fallas_checks = []
    elif checks.codigo == 8:
        fallas_checks = ["hay checks pendientes"]
    else:
        fallas_checks = [f"gh pr checks salió con código {checks.codigo}"]

    revisiones = ejecutar(comando_revisiones(pr))
    try:
        aprobado = revisiones.codigo == 0 and _aprobado(json.loads(revisiones.texto))
    except json.JSONDecodeError:
        aprobado = False
    falla_revision = [] if aprobado else ["no tiene una aprobación vigente"]
    return [
        Resultado(
            f"Checks del PR #{pr}",
            checks.codigo == 0,
            fallas_checks,
            comando_checks(pr),
            _ultimas_lineas(checks.texto, 10),
        ),
        Resultado(
            f"Aprobación del PR #{pr}",
            aprobado,
            falla_revision,
            comando_revisiones(pr),
            _ultimas_lineas(revisiones.texto, 1),
        ),
    ]


def verificar(
    ejecutar: Ejecutor = ejecutar,
    base: str = "main",
    pr: str | None = None,
    gh_disponible: bool = False,
    antes_del_commit: bool = False,
) -> Informe:
    rama = ejecutar(RAMA).texto.strip()
    commits, resultados = _revisar_commits(ejecutar, base)
    resultados += _revisar_arbol(ejecutar, antes_del_commit)
    calidad, cobertura = _revisar_calidad(ejecutar)
    resultados += calidad
    omitidas = []
    if pr is not None:
        if gh_disponible:
            resultados += _revisar_pr(ejecutar, pr)
        else:
            omitidas.append(f"PR #{pr}: gh no está disponible")
    avisos = _revisar_atraso(ejecutar, base)
    return Informe(rama, base, commits, resultados, cobertura, omitidas, avisos, antes_del_commit)


def _cobertura_texto(cobertura: float | None) -> str:
    return "no disponible" if cobertura is None else f"{cobertura:.2f} %".replace(".", ",")


def formatear_texto(informe: Informe) -> str:
    lineas = [f"Rama: {informe.rama}", f"Commits sobre {informe.base}: {len(informe.commits)}"]
    if informe.antes_del_commit:
        lineas.insert(0, "Modo: antes del commit (lo que va a entrar, en el índice)")
    lineas += [f"  {c.corto} {c.correo} {c.asunto}" for c in informe.commits]
    if not informe.commits:
        lineas.append(f"  (sin commits sobre {informe.base})")
    lineas.append("")
    for resultado in informe.resultados:
        lineas.append(f"[{'OK' if resultado.ok else 'FALLA'}] {resultado.nombre}")
        lineas += [f"        - {falla}" for falla in resultado.fallas]
    lineas += [f"[OMITIDA] {omitida}" for omitida in informe.omitidas]
    lineas += [f"[AVISO] {aviso}" for aviso in informe.avisos]
    lineas += ["", f"Cobertura total: {_cobertura_texto(informe.cobertura)}", ""]
    if informe.pasa:
        lineas.append("PASA")
    else:
        lineas.append("NO PASA")
        lineas += [f"  - {falla}" for falla in informe.fallas]
    return "\n".join(lineas) + "\n"


def _celda(texto: str) -> str:
    return texto.replace("|", "\\|").replace("\n", " · ")


def formatear_markdown(informe: Informe, fecha: datetime) -> str:
    veredicto = "PASA" if informe.pasa else "NO PASA"
    cobertura = _cobertura_texto(informe.cobertura)
    if informe.cobertura is not None:
        cobertura = f"**{cobertura}**"
    lineas = [
        "## Verificación automática",
        "",
        f"Fecha: {fecha:%d/%m/%Y %H:%M}. Rama: `{informe.rama}`, "
        f"{len(informe.commits)} commits sobre `{informe.base}`. "
        f"Veredicto: **{veredicto}**. Cobertura total: {cobertura} "
        f"(mínimo {UMBRAL_COBERTURA} %). Generado con `scripts/verificar.py`.",
        "",
        "| Verificación | Resultado | Detalle |",
        "| --- | --- | --- |",
    ]
    for resultado in informe.resultados:
        estado = "Pasa" if resultado.ok else "No pasa"
        lineas.append(f"| {resultado.nombre} | {estado} | {_celda('; '.join(resultado.fallas))} |")
    lineas += [f"| {omitida} | Omitida | |" for omitida in informe.omitidas]
    if not informe.pasa:
        lineas += ["", "Fallas:", ""] + [f"- {falla}" for falla in informe.fallas]
    if informe.avisos:
        lineas += ["", "Avisos (no cambian el veredicto):", ""]
        lineas += [f"- {aviso}" for aviso in informe.avisos]

    lineas += ["", "```text", f"$ git log {informe.base}..HEAD"]
    lineas += [f"{c.corto} {c.correo} {c.asunto}" for c in informe.commits]
    for resultado in informe.resultados:
        if resultado.comando:
            lineas += ["", f"$ {' '.join(resultado.comando)}"]
            if resultado.resumen:
                lineas.append(resultado.resumen.replace("```", "'''"))
    lineas.append("```")
    return "\n".join(lineas) + "\n"


def main(
    argv: list[str] | None = None,
    ejecutar: Ejecutor = ejecutar,
    gh: Callable[[str], str | None] = shutil.which,
    ahora: Callable[[], datetime] = datetime.now,
) -> int:
    parser = argparse.ArgumentParser(description="Verificación antes de un commit o PR.")
    parser.add_argument("--pr", help="número del PR: revisa sus checks y su aprobación con gh")
    parser.add_argument("--base", default="main", help="rama base de los commits (main)")
    parser.add_argument(
        "--markdown", action="store_true", help="imprime un bloque para verificacion.md"
    )
    parser.add_argument(
        "--antes-del-commit",
        action="store_true",
        help="acepta cambios en el índice; falla con cambios fuera de él o sin seguimiento",
    )
    args = parser.parse_args(argv)

    informe = verificar(
        ejecutar,
        args.base,
        args.pr,
        gh_disponible=gh("gh") is not None,
        antes_del_commit=args.antes_del_commit,
    )
    if args.markdown:
        print(formatear_markdown(informe, ahora()), end="")
    else:
        print(formatear_texto(informe), end="")
    return 0 if informe.pasa else 1


if __name__ == "__main__":
    # Los asuntos de los commits pueden traer caracteres fuera de la página de códigos.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
