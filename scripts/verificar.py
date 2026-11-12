"""Verificación antes de un commit o PR: las comprobaciones que antes se hacían a mano.

Uso:
    uv run python scripts/verificar.py --antes-del-commit  # Ruff y pytest de lo del índice
    uv run python scripts/verificar.py --completo       # suite entera con cobertura (cierre)
    uv run python scripts/verificar.py                  # igual que --completo
    uv run python scripts/verificar.py --pr 53          # además, checks y aprobación del PR (gh)
    uv run python scripts/verificar.py --markdown       # bloque listo para verificacion.md

Antes de pytest comprueba que PostgreSQL responde; si no, no corre pytest y no pasa.

Sale con 0 si el veredicto es PASA y con 1 si es NO PASA.
"""

import argparse
import json
import os
import re
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

import reglas

UMBRAL_COBERTURA = 80
RAIZ = Path(__file__).resolve().parent.parent
# Salida completa de pytest cuando falla, para no perder el detalle (D13 de US-001).
REGISTROS = RAIZ / ".verificar"
DOMINIO_NOREPLY = "@users.noreply.github.com"
# Antes del commit, Ruff y pytest corren en una copia del índice fuera del repo, con el
# .venv de este script (uv run) sin sincronizar y las variables de .env en el entorno.
ENTORNO_VIRTUAL = Path(sys.prefix)
ARCHIVO_ENV = RAIZ / ".env"
DEPENDENCIAS = ("pyproject.toml", "uv.lock")
_LINEA_ENV = re.compile(r"\A(?:export )?([A-Za-z_0-9]+)=(.*)\Z")

RAMA = ("git", "rev-parse", "--abbrev-ref", "HEAD")
ESTADO = ("git", "status", "--porcelain")
ARCHIVOS = ("git", "ls-files", "-z")
RUFF_CHECK = ("uv", "run", "ruff", "check")
RUFF_FORMAT = ("uv", "run", "ruff", "format", "--check")
PYTEST_BASE = ("uv", "run", "pytest")
PYTEST = (*PYTEST_BASE, "--cov", f"--cov-fail-under={UMBRAL_COBERTURA}")
# Lo que cambia en el índice frente a HEAD. Sin renombres: salen la ruta vieja y la nueva.
INDICE = ("git", "diff", "--cached", "--name-only", "--no-renames", "-z")

# Antes de pytest se abre una conexión al puerto de DATABASE_URL con esta espera (segundos).
ESPERA_BASE = 3
NOMBRE_BASE = "PostgreSQL"
FALLA_BASE_APAGADA = "la base no responde (docker compose up -d db)"
# Antes del commit, cambiar esto corre la suite completa: lo usan todas las apps.
COMPARTIDOS = frozenset(DEPENDENCIAS)
CARPETA_APPS = ("src", "backend")
# Sin pruebas de pytest propias (las cubren las e2e del cierre).
ESTATICOS = (*CARPETA_APPS, "static")
# Sus pruebas (paquete y build de Vercel) están en scripts/tests.
FRONTEND = ("src", "frontend")
APPS_COMPARTIDAS = frozenset({"config"})

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


def comando_copia(carpeta: Path) -> tuple[str, ...]:
    # Con --prefix, git escribe los archivos del índice en esa carpeta y no toca el índice.
    return ("git", "checkout-index", "--all", f"--prefix={carpeta.as_posix()}/")


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
    def sin_base(self) -> bool:
        return any(r.nombre == NOMBRE_BASE and not r.ok for r in self.resultados)

    @property
    def fallas(self) -> list[str]:
        lista = []
        for resultado in self.resultados:
            if not resultado.ok:
                detalles = resultado.fallas or ["falló"]
                lista.extend(f"{resultado.nombre}: {detalle}" for detalle in detalles)
        return lista


Ejecutor = Callable[..., Salida]


def ejecutar(
    comando: tuple[str, ...], entorno: dict[str, str] | None = None, carpeta: Path | None = None
) -> Salida:
    """Corre el comando sin shell y junta stdout y stderr, como se ven en la terminal.

    ``entorno`` agrega variables a las de la terminal solo para ese comando, y
    ``carpeta`` lo corre en otra carpeta.
    """
    try:
        proceso = subprocess.run(
            list(comando),
            cwd=carpeta,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            env={**os.environ, **entorno} if entorno else None,
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


def _avisos_del_indice(cambios: list[str]) -> list[str]:
    """Lo que queda fuera del commit y las dependencias que cambian en el índice."""
    avisos = []
    fuera = [f"- {linea}" for linea in cambios if _fuera_del_indice(linea)]
    if fuera:
        avisos.append("\n".join(["Fuera de este commit (no se verifica):", *fuera]))
    for linea in cambios:
        if linea[0] not in " ?" and linea[3:] in DEPENDENCIAS:
            avisos.append(
                f"Cambia {linea[3:]} en el índice: el .venv no se sincroniza en la copia, "
                "corre uv sync"
            )
    return avisos


def _revisar_arbol(ejecutar: Ejecutor, antes_del_commit: bool) -> tuple[list[Resultado], list[str]]:
    estado = ejecutar(ESTADO)
    cambios = [linea for linea in estado.texto.splitlines() if linea.strip()]
    avisos = []
    if antes_del_commit:
        # Solo cuenta el índice: lo que está fuera de él se avisa y no hace fallar.
        nombre_estado = "git status sin errores"
        avisos = _avisos_del_indice(cambios)
        cambios = []
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
    ], avisos


def ruta_legible(archivo: Path) -> str:
    """Ruta relativa a la raíz del repo si está dentro de él; si no, la ruta completa."""
    try:
        return archivo.relative_to(RAIZ).as_posix()
    except ValueError:
        return str(archivo)


def _guardar_salida(registros: Path, momento: datetime, texto: str) -> Path:
    registros.mkdir(parents=True, exist_ok=True)
    archivo = registros / f"pytest-{momento:%Y%m%d-%H%M%S}.txt"
    archivo.write_text(texto, encoding="utf-8")
    return archivo


def _datos_de_cobertura() -> Path:
    """Archivo de cobertura propio de esta ejecución (D13 de US-001).

    Con el ``.coverage`` de la raíz, otro pytest corriendo al mismo tiempo le borra
    o le mezcla los datos y la corrida termina en INTERNALERROR.
    """
    return RAIZ / ".verificar" / f".coverage-{os.getpid()}"


def leer_env(archivo: Path) -> dict[str, str]:
    """Variables de ``.env`` como las lee django-environ, sin escribirlas en ningún archivo."""
    try:
        texto = archivo.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}
    variables = {}
    for linea in texto.splitlines():
        if encontrada := _LINEA_ENV.match(linea.strip()):
            clave, valor = encontrada.groups()
            if len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in "'\"":
                valor = valor[1:-1]
            variables[clave] = valor
    return variables


def _entornos_de_la_copia(copia: Path) -> tuple[dict[str, str], dict[str, str]]:
    """Entorno de Ruff y de pytest en la copia del índice."""
    uv = {"UV_PROJECT_ENVIRONMENT": str(ENTORNO_VIRTUAL), "UV_NO_SYNC": "1"}
    # Como en settings.py, lo que ya está en la terminal tiene prioridad sobre .env.
    env = {
        clave: valor for clave, valor in leer_env(ARCHIVO_ENV).items() if clave not in os.environ
    }
    return uv, {**env, **uv, "COVERAGE_FILE": str(copia / ".coverage")}


def comprobar_base(espera: float = ESPERA_BASE) -> bool:
    """True si el puerto de PostgreSQL de DATABASE_URL acepta la conexión antes de ``espera``.

    Sin DATABASE_URL (ni en la terminal ni en .env) no se comprueba: pytest dirá qué falta.
    """
    url = os.environ.get("DATABASE_URL") or leer_env(ARCHIVO_ENV).get("DATABASE_URL")
    if not url:
        return True
    partes = urlsplit(url)
    try:
        with socket.create_connection(
            (partes.hostname or "localhost", partes.port or 5432), espera
        ):
            return True
    except (OSError, ValueError):
        return False


def pruebas_del_indice(rutas: list[str], apps: set[str]) -> tuple[str, ...] | None:
    """Carpetas que pytest debe correr por lo que cambia en el índice.

    ``None`` es la suite completa: cambia algo compartido o algo que no se puede atribuir a
    una app con pruebas propias. La tupla vacía es que no hay código que probar.
    """
    carpetas = set()
    for ruta in rutas:
        partes = ruta.split("/")
        if ruta in COMPARTIDOS or partes[-1] == "conftest.py":
            return None
        if partes[0] == "scripts" or tuple(partes[:2]) == FRONTEND:
            carpetas.add("scripts")
            continue
        if partes[0] != "src" or tuple(partes[:3]) == ESTATICOS:
            continue  # documentos, openspec, .github y estáticos: sin pruebas de pytest
        resto = partes[2:] if tuple(partes[:2]) == CARPETA_APPS else []
        if resto[:1] == ["templates"]:
            resto = resto[1:]
            if resto[:1] == ["admin"]:
                resto = resto[1:]
        app = resto[0] if len(resto) > 1 else None
        if app not in apps or app in APPS_COMPARTIDAS:
            return None
        carpetas.add("/".join((*CARPETA_APPS, app)))
    return tuple(sorted(carpetas))


def _apps_con_pruebas(raiz: Path) -> set[str]:
    carpeta = raiz.joinpath(*CARPETA_APPS)
    if not carpeta.is_dir():
        return set()
    return {app.name for app in carpeta.iterdir() if (app / "tests").is_dir()}


def _pytest_del_indice(ejecutar: Ejecutor, copia: Path) -> tuple[tuple[str, ...] | None, str]:
    """Comando de pytest antes del commit y el nombre de su resultado (``None``: no se corre)."""
    salida = ejecutar(INDICE)
    if salida.codigo != 0:
        carpetas = None  # sin saber qué cambia, se prueba todo
    else:
        rutas = [ruta for ruta in salida.texto.split("\0") if ruta]
        carpetas = pruebas_del_indice(rutas, _apps_con_pruebas(copia))
    if carpetas is None:
        return PYTEST_BASE, "pytest, suite completa (sin cobertura)"
    if not carpetas:
        return None, "pytest: sin pruebas que correr (el índice no toca apps ni scripts)"
    nombres = ", ".join(carpeta.rsplit("/", 1)[-1] for carpeta in carpetas)
    return (*PYTEST_BASE, *carpetas), f"pytest de {nombres} (sin cobertura)"


def _revisar_calidad(
    ejecutar: Ejecutor,
    registros: Path | None,
    ahora: Callable[[], datetime],
    copia: Path | None = None,
) -> tuple[list[Resultado], float | None]:
    if copia is None:
        datos = _datos_de_cobertura()
        datos.parent.mkdir(parents=True, exist_ok=True)
        entorno_ruff, entorno_pytest = None, {"COVERAGE_FILE": str(datos)}
        pytest_, nombre = PYTEST, f"pytest --cov (mínimo {UMBRAL_COBERTURA} %)"
    else:
        datos = None  # queda dentro de la copia y se borra con ella
        entorno_ruff, entorno_pytest = _entornos_de_la_copia(copia)
        pytest_, nombre = _pytest_del_indice(ejecutar, copia)

    resultados = []
    for nombre_ruff, comando in (("ruff check", RUFF_CHECK), ("ruff format --check", RUFF_FORMAT)):
        salida = ejecutar(comando, entorno_ruff, copia)
        resumen = _ultimas_lineas(salida.texto)
        fallas = [] if salida.codigo == 0 else [resumen or f"salió con código {salida.codigo}"]
        resultados.append(Resultado(nombre_ruff, salida.codigo == 0, fallas, comando, resumen))

    if pytest_ is None:
        resultados.append(Resultado(nombre, True))
        return resultados, None
    # Se busca en el módulo al llamar: las pruebas lo reemplazan sin tocar la firma.
    if not comprobar_base():
        resultados.append(Resultado(NOMBRE_BASE, False, [FALLA_BASE_APAGADA]))
        if datos is not None:
            datos.unlink(missing_ok=True)
        return resultados, None

    salida = ejecutar(pytest_, entorno_pytest, copia)
    if datos is not None:
        datos.unlink(missing_ok=True)
    encontrada = _COBERTURA.search(salida.texto)
    # Antes del commit no se pide --cov: lo que diga la salida no es la cobertura total.
    cobertura = float(encontrada.group(1)) if encontrada and copia is None else None
    resumen = _resumen_pytest(salida.texto)
    if salida.codigo == 0:
        fallas = []
    elif _SIN_BASE.search(salida.texto):
        fallas = [FALLA_SIN_BASE]
    else:
        fallas = [_ultimas_lineas(resumen, 1)]
    if salida.codigo != 0 and registros is not None:
        archivo = _guardar_salida(registros, ahora(), salida.texto)
        fallas.append(f"salida completa en {ruta_legible(archivo)}")
    resultados.append(Resultado(nombre, salida.codigo == 0, fallas, pytest_, resumen))
    return resultados, cobertura


def borrar_copia(copia: Path) -> list[str]:
    """Borra la copia del índice; devuelve un aviso con su ruta si algo no se pudo borrar.

    En Windows, un archivo de solo lectura o bloqueado un momento (antivirus, indexador)
    hace fallar el borrado: se le quita el solo lectura y se reintenta.
    """

    def reintentar(funcion: Callable[[str], object], ruta: str, _error: BaseException) -> None:
        for _intento in range(3):
            try:
                # Se suma la escritura: fijarla dejaría un directorio sin acceso en Linux.
                os.chmod(ruta, os.stat(ruta).st_mode | stat.S_IWRITE)
                funcion(ruta)
                return
            except FileNotFoundError:
                return
            except OSError:
                time.sleep(0.1)

    shutil.rmtree(copia, onexc=reintentar)
    if copia.exists():
        return [f"No se pudo borrar la copia temporal del índice: {copia} (bórrala a mano)"]
    return []


def _revisar_calidad_del_indice(
    ejecutar: Ejecutor,
    registros: Path | None,
    ahora: Callable[[], datetime],
    temporal: Path | None,
) -> tuple[list[Resultado], float | None, list[str]]:
    """Ruff y pytest (solo lo tocado) sobre una copia del índice fuera del repo, que se borra
    al terminar."""
    copia = Path(tempfile.mkdtemp(prefix="verificar-indice-", dir=temporal))
    terminado = False
    try:
        salida = ejecutar(comando_copia(copia))
        if salida.codigo == 0:
            resultados, cobertura = _revisar_calidad(ejecutar, registros, ahora, copia)
        else:
            falla = _ultimas_lineas(salida.texto, 1) or f"salió con código {salida.codigo}"
            resultados, cobertura = [Resultado("Copia del índice", False, [falla])], None
        terminado = True
    finally:
        restos = borrar_copia(copia)
        if restos and not terminado:
            # Con Ctrl+C o un error no hay informe: el aviso va directo a la terminal.
            print("\n".join(f"[AVISO] {resto}" for resto in restos), file=sys.stderr)
    return resultados, cobertura, restos


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
    registros: Path | None = None,
    ahora: Callable[[], datetime] = datetime.now,
    temporal: Path | None = None,
) -> Informe:
    """Corre las verificaciones; si pytest falla y hay ``registros``, guarda ahí su salida.

    Con ``antes_del_commit``, Ruff y pytest corren en una copia del índice dentro de
    ``temporal`` (la carpeta temporal del sistema si no se indica).
    """
    rama = ejecutar(RAMA).texto.strip()
    commits, resultados = _revisar_commits(ejecutar, base)
    arbol, avisos = _revisar_arbol(ejecutar, antes_del_commit)
    resultados += arbol
    if antes_del_commit:
        calidad, cobertura, restos = _revisar_calidad_del_indice(
            ejecutar, registros, ahora, temporal
        )
        avisos += restos
    else:
        calidad, cobertura = _revisar_calidad(ejecutar, registros, ahora)
    resultados += calidad
    omitidas = []
    if pr is not None:
        if gh_disponible:
            resultados += _revisar_pr(ejecutar, pr)
        else:
            omitidas.append(f"PR #{pr}: gh no está disponible")
    avisos += _revisar_atraso(ejecutar, base)
    return Informe(rama, base, commits, resultados, cobertura, omitidas, avisos, antes_del_commit)


def _cobertura_texto(cobertura: float | None, antes_del_commit: bool = False) -> str:
    if antes_del_commit:
        return "no se mide en este modo"
    return "no disponible" if cobertura is None else f"{cobertura:.2f} %".replace(".", ",")


def formatear_texto(informe: Informe) -> str:
    lineas = [f"Rama: {informe.rama}", f"Commits sobre {informe.base}: {len(informe.commits)}"]
    if informe.antes_del_commit:
        modo = "antes del commit (Ruff y pytest de lo que hay en el índice, sobre una copia)"
    else:
        modo = f"completo (suite entera, cobertura mínima {UMBRAL_COBERTURA} %)"
    lineas.insert(0, f"Modo: {modo}")
    lineas += [f"  {c.corto} {c.correo} {c.asunto}" for c in informe.commits]
    if not informe.commits:
        lineas.append(f"  (sin commits sobre {informe.base})")
    lineas.append("")
    for resultado in informe.resultados:
        lineas.append(f"[{'OK' if resultado.ok else 'FALLA'}] {resultado.nombre}")
        lineas += [f"        - {falla}" for falla in resultado.fallas]
    lineas += [f"[OMITIDA] {omitida}" for omitida in informe.omitidas]
    lineas += [f"[AVISO] {aviso}".replace("\n", "\n        ") for aviso in informe.avisos]
    cobertura = _cobertura_texto(informe.cobertura, informe.antes_del_commit)
    lineas += ["", f"Cobertura total: {cobertura}", ""]
    if informe.pasa:
        lineas.append("PASA")
    elif informe.sin_base and len(informe.fallas) == 1:
        lineas.append(f"NO PASA: {FALLA_BASE_APAGADA}")
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
        lineas += [f"- {aviso}".replace("\n", "\n  ") for aviso in informe.avisos]

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
    registros: Path = REGISTROS,
) -> int:
    parser = argparse.ArgumentParser(description="Verificación antes de un commit o PR.")
    parser.add_argument("--pr", help="número del PR: revisa sus checks y su aprobación con gh")
    parser.add_argument("--base", default="main", help="rama base de los commits (main)")
    parser.add_argument(
        "--markdown", action="store_true", help="imprime un bloque para verificacion.md"
    )
    modo = parser.add_mutually_exclusive_group()
    modo.add_argument(
        "--antes-del-commit",
        action="store_true",
        help="Ruff y las pruebas de las apps del índice, sin cobertura, sobre una copia del "
        "índice; lo compartido corre toda la suite y lo de fuera del índice solo se avisa",
    )
    modo.add_argument(
        "--completo",
        action="store_true",
        help=f"suite entera con cobertura mínima de {UMBRAL_COBERTURA} %% (cierre de historia); "
        "es lo que se corre sin modo",
    )
    args = parser.parse_args(argv)

    informe = verificar(
        ejecutar,
        args.base,
        args.pr,
        gh_disponible=gh("gh") is not None,
        antes_del_commit=args.antes_del_commit,
        registros=registros,
        ahora=ahora,
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
