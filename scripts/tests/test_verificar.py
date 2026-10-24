"""Pruebas del script de verificación antes de un commit o PR (scripts/verificar.py)."""

import json
import os
import shutil
import stat
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pytest

import verificar
from verificar import Salida

NOREPLY = "145754609+alguien@users.noreply.github.com"
SALIDA_PYTEST = (
    "collected 69 items\n"
    "TOTAL                                 222     21    91%\n"
    "Required test coverage of 80.0% reached. Total coverage: 90.95%\n"
    "====================== 69 passed, 4 deselected in 6.68s =======================\n"
)


def registro(hash_, correo, asunto, cuerpo=""):
    mensaje = f"{asunto}\n\n{cuerpo}" if cuerpo else asunto
    return f"{hash_}\x1f{correo}\x1f{asunto}\x1f{mensaje}\n\x1e"


class EjecutorFalso:
    """Responde a cada comando con una Salida fija y anota lo que se ejecutó."""

    def __init__(self):
        self.respuestas = {
            verificar.RAMA: Salida(0, "chore/verificacion-automatica\n"),
            verificar.comando_log("main"): Salida(
                0,
                registro("a" * 40, NOREPLY, "chore: hooks")
                + registro("b" * 40, NOREPLY, "chore: script"),
            ),
            verificar.ESTADO: Salida(0, ""),
            verificar.ARCHIVOS: Salida(0, "README.md\0scripts/verificar.py\0"),
            verificar.RUFF_CHECK: Salida(0, "All checks passed!\n"),
            verificar.RUFF_FORMAT: Salida(0, "110 files already formatted\n"),
            verificar.PYTEST: Salida(0, SALIDA_PYTEST),
            verificar.comando_atraso("main"): Salida(0, "0\n"),
            verificar.comando_checks("53"): Salida(0, "Ruff\tpass\t20s\nPruebas\tpass\t1m\n"),
            verificar.comando_revisiones("53"): Salida(
                0,
                json.dumps(
                    {
                        "reviewDecision": "APPROVED",
                        "latestReviews": [{"author": {"login": "x"}, "state": "APPROVED"}],
                    }
                ),
            ),
        }
        self.ejecutados = []
        self.entornos = {}
        self.carpetas = {}
        # git checkout-index lleva la ruta temporal: se responde aparte.
        self.copia = Salida(0, "")
        self.copias = []
        self.al_copiar = None
        self.al_correr_pytest = None

    def __call__(self, comando, entorno=None, carpeta=None):
        comando = tuple(comando)
        self.ejecutados.append(comando)
        if entorno is not None:
            self.entornos[comando] = entorno
        if carpeta is not None:
            self.carpetas[comando] = carpeta
        if comando[:2] == ("git", "checkout-index"):
            destino = Path(comando[-1].removeprefix("--prefix="))
            self.copias.append(destino)
            if self.al_copiar:
                self.al_copiar(destino)
            return self.copia
        if comando == verificar.PYTEST and self.al_correr_pytest:
            self.al_correr_pytest(carpeta)
        return self.respuestas[comando]


@pytest.fixture
def ejecutor():
    return EjecutorFalso()


@pytest.fixture(autouse=True)
def sin_env_de_la_laptop(tmp_path, monkeypatch):
    """Las pruebas no leen el .env real: cada una arma el suyo si lo necesita."""
    monkeypatch.setattr(verificar, "ARCHIVO_ENV", tmp_path / "sin-env" / ".env")


def nombres_fallidos(informe):
    return [r.nombre for r in informe.resultados if not r.ok]


# --- Todo en orden ---


def test_todo_en_orden_pasa(ejecutor):
    informe = verificar.verificar(ejecutor)
    assert informe.pasa
    assert informe.fallas == []
    assert informe.rama == "chore/verificacion-automatica"
    assert [c.asunto for c in informe.commits] == ["chore: hooks", "chore: script"]
    assert informe.cobertura == pytest.approx(90.95)


def test_sin_pr_no_llama_a_gh(ejecutor):
    verificar.verificar(ejecutor)
    assert not any(comando[0] == "gh" for comando in ejecutor.ejecutados)


def test_pytest_se_corre_con_cobertura_y_umbral_80():
    assert verificar.PYTEST == ("uv", "run", "pytest", "--cov", "--cov-fail-under=80")


# --- Commits sobre main ---


def test_correo_que_no_es_noreply_falla(ejecutor):
    ejecutor.respuestas[verificar.comando_log("main")] = Salida(
        0, registro("c" * 40, "persona@gmail.com", "chore: algo")
    )
    informe = verificar.verificar(ejecutor)
    assert not informe.pasa
    assert "Correo noreply en los commits" in nombres_fallidos(informe)
    assert any("persona@gmail.com" in falla for falla in informe.fallas)


def test_commit_con_atribucion_falla(ejecutor):
    ejecutor.respuestas[verificar.comando_log("main")] = Salida(
        0,
        registro(
            "d" * 40,
            NOREPLY,
            "chore: algo",
            "🤖 Generated with [Claude Code](https://claude.com/claude-code)",
        ),
    )
    informe = verificar.verificar(ejecutor)
    assert "Commits sin atribuciones" in nombres_fallidos(informe)
    assert any("ddddddd" in falla for falla in informe.fallas)


def test_base_configurable(ejecutor):
    ejecutor.respuestas[verificar.comando_log("origin/main")] = Salida(0, "")
    informe = verificar.verificar(ejecutor, base="origin/main")
    assert informe.commits == []
    assert informe.pasa


def test_git_log_con_error_falla(ejecutor):
    ejecutor.respuestas[verificar.comando_log("main")] = Salida(128, "fatal: bad revision\n")
    informe = verificar.verificar(ejecutor)
    assert "Commits sobre la base" in nombres_fallidos(informe)


# --- Árbol de trabajo ---


def test_git_status_sucio_falla(ejecutor):
    ejecutor.respuestas[verificar.ESTADO] = Salida(0, " M README.md\n?? nuevo.py\n")
    informe = verificar.verificar(ejecutor)
    assert "git status limpio" in nombres_fallidos(informe)


def test_archivo_prohibido_versionado_falla(ejecutor):
    ejecutor.respuestas[verificar.ARCHIVOS] = Salida(0, "README.md\0coverage.xml\0")
    informe = verificar.verificar(ejecutor)
    assert "Sin archivos prohibidos" in nombres_fallidos(informe)
    assert any("coverage.xml" in falla for falla in informe.fallas)


# --- Calidad ---


@pytest.mark.parametrize(
    ("comando", "nombre"),
    [
        (verificar.RUFF_CHECK, "ruff check"),
        (verificar.RUFF_FORMAT, "ruff format --check"),
        (verificar.PYTEST, "pytest --cov (mínimo 80 %)"),
    ],
)
def test_comando_de_calidad_que_falla(ejecutor, comando, nombre):
    ejecutor.respuestas[comando] = Salida(1, "algo falló\n")
    informe = verificar.verificar(ejecutor)
    assert nombre in nombres_fallidos(informe)


def test_cobertura_bajo_el_umbral(ejecutor):
    ejecutor.respuestas[verificar.PYTEST] = Salida(
        1, "FAIL Required test coverage of 80.0% not reached. Total coverage: 75.10%\n"
    )
    informe = verificar.verificar(ejecutor)
    assert informe.cobertura == pytest.approx(75.10)
    assert not informe.pasa


def test_cobertura_desconocida_si_pytest_no_la_imprime(ejecutor):
    ejecutor.respuestas[verificar.PYTEST] = Salida(4, "ERROR: usage\n")
    informe = verificar.verificar(ejecutor)
    assert informe.cobertura is None


# --- PR con gh ---


def test_pr_con_checks_y_aprobacion_pasa(ejecutor):
    informe = verificar.verificar(ejecutor, pr="53", gh_disponible=True)
    assert informe.pasa
    assert "Checks del PR #53" in [r.nombre for r in informe.resultados]


@pytest.mark.parametrize("codigo", [1, 8])
def test_pr_con_checks_fallidos_o_pendientes(ejecutor, codigo):
    ejecutor.respuestas[verificar.comando_checks("53")] = Salida(codigo, "Ruff\tfail\n")
    informe = verificar.verificar(ejecutor, pr="53", gh_disponible=True)
    assert "Checks del PR #53" in nombres_fallidos(informe)


@pytest.mark.parametrize(
    "datos",
    [
        {"reviewDecision": "REVIEW_REQUIRED", "latestReviews": []},
        {"reviewDecision": "CHANGES_REQUESTED", "latestReviews": [{"state": "APPROVED"}]},
        {"reviewDecision": "", "latestReviews": [{"state": "COMMENTED"}]},
    ],
)
def test_pr_sin_aprobacion(ejecutor, datos):
    ejecutor.respuestas[verificar.comando_revisiones("53")] = Salida(0, json.dumps(datos))
    informe = verificar.verificar(ejecutor, pr="53", gh_disponible=True)
    assert "Aprobación del PR #53" in nombres_fallidos(informe)


def test_pr_aprobado_sin_revision_obligatoria(ejecutor):
    datos = {"reviewDecision": "", "latestReviews": [{"state": "APPROVED"}]}
    ejecutor.respuestas[verificar.comando_revisiones("53")] = Salida(0, json.dumps(datos))
    informe = verificar.verificar(ejecutor, pr="53", gh_disponible=True)
    assert informe.pasa


def test_pr_con_error_de_gh_falla(ejecutor):
    ejecutor.respuestas[verificar.comando_revisiones("53")] = Salida(4, "gh auth login\n")
    informe = verificar.verificar(ejecutor, pr="53", gh_disponible=True)
    assert "Aprobación del PR #53" in nombres_fallidos(informe)


def test_pr_sin_gh_se_omite_sin_fallar(ejecutor):
    informe = verificar.verificar(ejecutor, pr="53", gh_disponible=False)
    assert informe.pasa
    assert informe.omitidas == ["PR #53: gh no está disponible"]
    assert not any(comando[0] == "gh" for comando in ejecutor.ejecutados)


# --- Salida en texto ---


def test_texto_con_veredicto_pasa(ejecutor):
    texto = verificar.formatear_texto(verificar.verificar(ejecutor))
    assert "chore/verificacion-automatica" in texto
    assert f"aaaaaaa {NOREPLY} chore: hooks" in texto
    assert texto.rstrip().endswith("PASA")


def test_texto_con_veredicto_no_pasa_y_fallas(ejecutor):
    ejecutor.respuestas[verificar.ESTADO] = Salida(0, " M README.md\n")
    texto = verificar.formatear_texto(verificar.verificar(ejecutor))
    assert "NO PASA" in texto
    assert "README.md" in texto


def test_texto_sin_commits_sobre_la_base(ejecutor):
    ejecutor.respuestas[verificar.comando_log("main")] = Salida(0, "")
    texto = verificar.formatear_texto(verificar.verificar(ejecutor))
    assert "sin commits sobre main" in texto


# --- Bloque Markdown para verificacion.md ---


def test_markdown_con_fecha_resultados_y_cobertura(ejecutor):
    informe = verificar.verificar(ejecutor)
    bloque = verificar.formatear_markdown(informe, datetime(2026, 10, 19, 14, 30))
    assert "Fecha: 19/10/2026 14:30." in bloque
    assert "`chore/verificacion-automatica`" in bloque
    assert "Cobertura total: **90,95 %**" in bloque
    assert "| ruff check | Pasa |" in bloque
    assert "$ uv run pytest --cov --cov-fail-under=80" in bloque
    assert "Total coverage: 90.95%" in bloque
    assert "collected 69 items" not in bloque  # salida resumida
    assert bloque.count("```") % 2 == 0


def test_markdown_no_pasa_lista_las_fallas(ejecutor):
    ejecutor.respuestas[verificar.PYTEST] = Salida(1, "FAILED x\n=== 1 failed ===\n")
    bloque = verificar.formatear_markdown(verificar.verificar(ejecutor), datetime(2026, 10, 19))
    assert "Veredicto: **NO PASA**" in bloque
    assert "Cobertura total: no disponible" in bloque
    assert "| pytest --cov (mínimo 80 %) | No pasa |" in bloque


# --- main ---


def test_main_devuelve_0_si_pasa(ejecutor, capsys):
    assert verificar.main([], ejecutar=ejecutor, gh=lambda _: None) == 0
    assert capsys.readouterr().out.rstrip().endswith("PASA")


def test_main_devuelve_1_si_no_pasa(ejecutor, capsys):
    ejecutor.respuestas[verificar.ESTADO] = Salida(0, "?? x\n")
    assert verificar.main([], ejecutar=ejecutor, gh=lambda _: None) == 1
    assert "NO PASA" in capsys.readouterr().out


def test_main_con_pr_y_markdown(ejecutor, capsys):
    codigo = verificar.main(
        ["--pr", "53", "--markdown"],
        ejecutar=ejecutor,
        gh=lambda _: "gh",
        ahora=lambda: datetime(2026, 10, 19, 9, 5),
    )
    salida = capsys.readouterr().out
    assert codigo == 0
    assert "Fecha: 19/10/2026 09:05." in salida
    assert "| Aprobación del PR #53 | Pasa |" in salida


def test_main_con_base(ejecutor):
    ejecutor.respuestas[verificar.comando_log("origin/main")] = Salida(0, "")
    assert verificar.main(["--base", "origin/main"], ejecutar=ejecutor, gh=lambda _: None) == 0


# --- Ejecutor real ---


def test_ejecutar_junta_stdout_y_stderr(monkeypatch):
    def falso_run(comando, **kwargs):
        assert kwargs["stderr"] is subprocess.STDOUT
        return subprocess.CompletedProcess(comando, 2, stdout="salida y error\n")

    monkeypatch.setattr(verificar.subprocess, "run", falso_run)
    assert verificar.ejecutar(("git", "status")) == Salida(2, "salida y error\n")


def test_ejecutar_comando_inexistente(monkeypatch):
    def falso_run(comando, **kwargs):
        raise FileNotFoundError(comando[0])

    monkeypatch.setattr(verificar.subprocess, "run", falso_run)
    salida = verificar.ejecutar(("noexiste",))
    assert salida.codigo == 127
    assert "noexiste" in salida.texto


def test_git_status_con_error_falla(ejecutor):
    ejecutor.respuestas[verificar.ESTADO] = Salida(128, "")
    informe = verificar.verificar(ejecutor)
    assert "git status limpio" in nombres_fallidos(informe)


def test_pr_con_respuesta_de_gh_que_no_es_json(ejecutor):
    ejecutor.respuestas[verificar.comando_revisiones("53")] = Salida(0, "no es json")
    informe = verificar.verificar(ejecutor, pr="53", gh_disponible=True)
    assert "Aprobación del PR #53" in nombres_fallidos(informe)


# --- Base de datos apagada ---

SALIDA_SIN_BASE = (
    "E   psycopg.OperationalError: connection failed: connection to server at "
    '"127.0.0.1", port 5432 failed: Connection refused\n'
    "E           Multiple connection attempts failed. All failures were:\n"
    "=========== 37 passed, 23 errors in 47.53s ===========\n"
)


def test_pytest_sin_base_de_datos_pide_encender_docker(ejecutor):
    ejecutor.respuestas[verificar.PYTEST] = Salida(1, SALIDA_SIN_BASE)
    informe = verificar.verificar(ejecutor)
    assert not informe.pasa
    assert informe.fallas == [
        "pytest --cov (mínimo 80 %): ¿Docker encendido? La base de datos no responde"
    ]


def test_pytest_que_falla_por_otra_causa_no_menciona_docker(ejecutor):
    ejecutor.respuestas[verificar.PYTEST] = Salida(1, "FAILED x\n=== 1 failed ===\n")
    informe = verificar.verificar(ejecutor)
    assert not any("Docker" in falla for falla in informe.fallas)


# --- main local desactualizada ---


def test_base_detras_de_origin_avisa_sin_fallar(ejecutor):
    ejecutor.respuestas[verificar.comando_atraso("main")] = Salida(0, "3\n")
    informe = verificar.verificar(ejecutor)
    assert informe.pasa
    assert informe.avisos == [
        "main local desactualizada: haz git pull (3 commits detrás de origin/main)"
    ]
    texto = verificar.formatear_texto(informe)
    assert "[AVISO] main local desactualizada: haz git pull" in texto
    assert texto.rstrip().endswith("PASA")
    bloque = verificar.formatear_markdown(informe, datetime(2026, 10, 19))
    assert "- main local desactualizada: haz git pull" in bloque


def test_base_al_dia_no_avisa(ejecutor):
    assert verificar.verificar(ejecutor).avisos == []


def test_sin_origin_main_no_avisa(ejecutor):
    ejecutor.respuestas[verificar.comando_atraso("main")] = Salida(128, "fatal: bad revision\n")
    assert verificar.verificar(ejecutor).avisos == []


def test_base_remota_no_se_compara_consigo_misma(ejecutor):
    ejecutor.respuestas[verificar.comando_log("origin/main")] = Salida(0, "")
    verificar.verificar(ejecutor, base="origin/main")
    assert not any(comando[:2] == ("git", "rev-list") for comando in ejecutor.ejecutados)


def test_comando_atraso_compara_con_la_referencia_local_sin_fetch():
    assert verificar.comando_atraso("main") == ("git", "rev-list", "--count", "main..origin/main")


# --- Modo --antes-del-commit ---

NOMBRE_ESTADO = "git status sin errores"


def test_antes_del_commit_acepta_cambios_solo_en_el_indice(ejecutor):
    ejecutor.respuestas[verificar.ESTADO] = Salida(
        0, "M  README.md\nA  scripts/nuevo.py\nD  viejo.py\n"
    )
    informe = verificar.verificar(ejecutor, antes_del_commit=True)
    assert informe.pasa
    assert informe.avisos == []
    nombres = [r.nombre for r in informe.resultados]
    assert NOMBRE_ESTADO in nombres
    assert "git status limpio" not in nombres


@pytest.mark.parametrize(
    "linea",
    [" M README.md", "MM README.md", "AM scripts/nuevo.py", " D viejo.py", "?? suelto.py"],
)
def test_antes_del_commit_avisa_sin_fallar_lo_que_queda_fuera_del_indice(ejecutor, linea):
    ejecutor.respuestas[verificar.ESTADO] = Salida(0, f"M  CLAUDE.md\n{linea}\n")
    informe = verificar.verificar(ejecutor, antes_del_commit=True)
    assert informe.pasa
    assert informe.avisos == [f"Fuera de este commit (no se verifica):\n- {linea}"]


def test_aviso_fuera_del_commit_en_texto_y_markdown(ejecutor):
    ejecutor.respuestas[verificar.ESTADO] = Salida(0, " M README.md\n?? suelto.py\n")
    informe = verificar.verificar(ejecutor, antes_del_commit=True)

    texto = verificar.formatear_texto(informe)
    assert (
        "[AVISO] Fuera de este commit (no se verifica):\n"
        "        -  M README.md\n"
        "        - ?? suelto.py\n"
    ) in texto
    assert texto.rstrip().endswith("PASA")
    bloque = verificar.formatear_markdown(informe, datetime(2026, 10, 22))
    assert "- Fuera de este commit (no se verifica):\n  -  M README.md\n  - ?? suelto.py" in bloque


@pytest.mark.parametrize("linea", ["M  uv.lock", "M  pyproject.toml", "MM uv.lock"])
def test_antes_del_commit_avisa_si_cambian_dependencias_en_el_indice(ejecutor, linea):
    ejecutor.respuestas[verificar.ESTADO] = Salida(0, f"{linea}\n")
    informe = verificar.verificar(ejecutor, antes_del_commit=True)
    assert informe.pasa
    ruta = linea[3:]
    assert (
        f"Cambia {ruta} en el índice: el .venv no se sincroniza en la copia, corre uv sync"
        in informe.avisos
    )


@pytest.mark.parametrize("linea", [" M uv.lock", "?? pyproject.toml", "M  src/pyproject.toml"])
def test_sin_aviso_de_dependencias_si_no_cambian_en_el_indice(ejecutor, linea):
    ejecutor.respuestas[verificar.ESTADO] = Salida(0, f"{linea}\n")
    informe = verificar.verificar(ejecutor, antes_del_commit=True)
    assert not any("uv sync" in aviso for aviso in informe.avisos)


def test_modo_normal_no_avisa_lo_de_fuera_del_indice(ejecutor):
    ejecutor.respuestas[verificar.ESTADO] = Salida(0, "M  uv.lock\n?? suelto.py\n")
    informe = verificar.verificar(ejecutor)
    assert informe.avisos == []
    assert "git status limpio" in nombres_fallidos(informe)


def test_antes_del_commit_revisa_prohibidos_en_el_indice(ejecutor):
    ejecutor.respuestas[verificar.ESTADO] = Salida(0, "A  .env\n")
    ejecutor.respuestas[verificar.ARCHIVOS] = Salida(0, "README.md\0.env\0")
    informe = verificar.verificar(ejecutor, antes_del_commit=True)
    assert "Sin archivos prohibidos en el índice" in nombres_fallidos(informe)


def test_antes_del_commit_mantiene_commits_ruff_y_pytest(ejecutor):
    ejecutor.respuestas[verificar.comando_log("main")] = Salida(
        0, registro("e" * 40, "persona@gmail.com", "chore: algo")
    )
    ejecutor.respuestas[verificar.RUFF_CHECK] = Salida(1, "E501\n")
    ejecutor.respuestas[verificar.PYTEST] = Salida(1, "=== 1 failed ===\n")
    informe = verificar.verificar(ejecutor, antes_del_commit=True)
    assert nombres_fallidos(informe) == [
        "Correo noreply en los commits",
        "ruff check",
        "pytest --cov (mínimo 80 %)",
    ]


def test_antes_del_commit_con_git_status_que_falla(ejecutor):
    ejecutor.respuestas[verificar.ESTADO] = Salida(128, "")
    informe = verificar.verificar(ejecutor, antes_del_commit=True)
    assert NOMBRE_ESTADO in nombres_fallidos(informe)


def test_texto_indica_el_modo_antes_del_commit(ejecutor):
    texto = verificar.formatear_texto(verificar.verificar(ejecutor, antes_del_commit=True))
    assert "Modo: antes del commit" in texto


def test_modo_normal_no_cambia_con_cambios_en_el_indice(ejecutor):
    ejecutor.respuestas[verificar.ESTADO] = Salida(0, "M  README.md\n")
    informe = verificar.verificar(ejecutor)
    assert "git status limpio" in nombres_fallidos(informe)
    assert "Modo:" not in verificar.formatear_texto(informe)


def test_main_con_antes_del_commit(ejecutor, capsys):
    ejecutor.respuestas[verificar.ESTADO] = Salida(0, "M  README.md\n")
    assert verificar.main(["--antes-del-commit"], ejecutar=ejecutor, gh=lambda _: None) == 0
    assert capsys.readouterr().out.rstrip().endswith("PASA")


# --- Antes del commit: Ruff y pytest sobre una copia del índice ---

UV_SIN_SINCRONIZAR = {"UV_PROJECT_ENVIRONMENT": str(verificar.ENTORNO_VIRTUAL), "UV_NO_SYNC": "1"}


def test_antes_del_commit_copia_el_indice_fuera_del_repo(ejecutor, tmp_path):
    verificar.verificar(ejecutor, antes_del_commit=True, temporal=tmp_path)

    [copia] = ejecutor.copias
    assert copia.parent == tmp_path
    assert not copia.is_relative_to(verificar.RAIZ)
    assert ("git", "checkout-index", "--all", f"--prefix={copia.as_posix()}/") in (
        ejecutor.ejecutados
    )


def test_antes_del_commit_corre_ruff_y_pytest_en_la_copia(ejecutor, tmp_path):
    verificar.verificar(ejecutor, antes_del_commit=True, temporal=tmp_path)

    [copia] = ejecutor.copias
    for comando in (verificar.RUFF_CHECK, verificar.RUFF_FORMAT, verificar.PYTEST):
        assert ejecutor.carpetas[comando] == copia
    assert ejecutor.entornos[verificar.RUFF_CHECK] == UV_SIN_SINCRONIZAR
    assert ejecutor.entornos[verificar.RUFF_FORMAT] == UV_SIN_SINCRONIZAR
    assert ejecutor.entornos[verificar.PYTEST] == {
        **UV_SIN_SINCRONIZAR,
        "COVERAGE_FILE": str(copia / ".coverage"),
    }


def test_el_entorno_virtual_es_el_del_script():
    """uv run corre verificar.py con el .venv del repo: la copia usa ese mismo."""
    assert Path(sys.prefix) == verificar.ENTORNO_VIRTUAL


def test_modo_normal_corre_en_la_carpeta_de_trabajo(ejecutor):
    verificar.verificar(ejecutor)
    assert ejecutor.copias == []
    assert ejecutor.carpetas == {}


def test_si_falla_la_copia_del_indice_no_corre_ruff_ni_pytest(ejecutor, tmp_path):
    ejecutor.copia = Salida(128, "fatal: unable to write new index file\n")
    informe = verificar.verificar(ejecutor, antes_del_commit=True, temporal=tmp_path)

    assert nombres_fallidos(informe) == ["Copia del índice"]
    assert informe.fallas == ["Copia del índice: fatal: unable to write new index file"]
    assert verificar.RUFF_CHECK not in ejecutor.ejecutados
    assert verificar.PYTEST not in ejecutor.ejecutados
    assert list(tmp_path.iterdir()) == []


# --- Variables del .env sin escribir archivos ---


def test_pytest_recibe_las_variables_del_env_sin_copiar_el_archivo(ejecutor, tmp_path, monkeypatch):
    archivo = tmp_path / ".env"
    archivo.write_text("VARIABLE_DE_PRUEBA=valor-ficticio\n", encoding="utf-8")
    monkeypatch.setattr(verificar, "ARCHIVO_ENV", archivo)
    monkeypatch.delenv("VARIABLE_DE_PRUEBA", raising=False)
    archivos_en_la_copia = []
    ejecutor.al_correr_pytest = lambda copia: archivos_en_la_copia.extend(copia.iterdir())
    temporal = tmp_path / "temporal"
    temporal.mkdir()

    verificar.verificar(ejecutor, antes_del_commit=True, temporal=temporal)

    assert ejecutor.entornos[verificar.PYTEST]["VARIABLE_DE_PRUEBA"] == "valor-ficticio"
    assert "VARIABLE_DE_PRUEBA" not in ejecutor.entornos[verificar.RUFF_CHECK]
    assert archivos_en_la_copia == []


def test_las_variables_de_la_terminal_tienen_prioridad_sobre_el_env(
    ejecutor, tmp_path, monkeypatch
):
    """Igual que settings.py: django-environ no pisa lo que ya está en el entorno."""
    archivo = tmp_path / ".env"
    archivo.write_text("YA_DEFINIDA=del-archivo\n", encoding="utf-8")
    monkeypatch.setattr(verificar, "ARCHIVO_ENV", archivo)
    monkeypatch.setenv("YA_DEFINIDA", "de-la-terminal")

    verificar.verificar(ejecutor, antes_del_commit=True, temporal=tmp_path)

    assert "YA_DEFINIDA" not in ejecutor.entornos[verificar.PYTEST]


def test_leer_env_como_django_environ(tmp_path):
    archivo = tmp_path / ".env"
    archivo.write_text(
        "# comentario\n"
        "\n"
        "SIMPLE=valor-ficticio\n"
        "VACIA=\n"
        "export EXPORTADA=uno\n"
        'COMILLAS_DOBLES="dos tres"\n'
        "COMILLAS_SIMPLES='cuatro'\n"
        "CON_IGUAL=a=b\n"
        "linea sin igual\n",
        encoding="utf-8",
    )
    assert verificar.leer_env(archivo) == {
        "SIMPLE": "valor-ficticio",
        "VACIA": "",
        "EXPORTADA": "uno",
        "COMILLAS_DOBLES": "dos tres",
        "COMILLAS_SIMPLES": "cuatro",
        "CON_IGUAL": "a=b",
    }


def test_leer_env_sin_archivo(tmp_path):
    assert verificar.leer_env(tmp_path / "no-existe") == {}


# --- La copia temporal se borra siempre ---


def _con_un_archivo(copia):
    (copia / "modulo.py").write_text("VALOR = 1\n", encoding="utf-8")


@pytest.mark.parametrize("pytest_pasa", [True, False])
def test_la_copia_temporal_ya_no_existe_al_terminar(ejecutor, tmp_path, pytest_pasa):
    ejecutor.al_copiar = _con_un_archivo
    if not pytest_pasa:
        ejecutor.respuestas[verificar.PYTEST] = Salida(1, "=== 1 failed ===\n")

    informe = verificar.verificar(ejecutor, antes_del_commit=True, temporal=tmp_path)

    assert informe.pasa is pytest_pasa
    [copia] = ejecutor.copias
    assert not copia.exists()
    assert list(tmp_path.iterdir()) == []


def test_la_copia_se_borra_tambien_con_ctrl_c(ejecutor, tmp_path):
    ejecutor.al_copiar = _con_un_archivo

    def interrumpir(_copia):
        raise KeyboardInterrupt

    ejecutor.al_correr_pytest = interrumpir

    with pytest.raises(KeyboardInterrupt):
        verificar.verificar(ejecutor, antes_del_commit=True, temporal=tmp_path)

    assert list(tmp_path.iterdir()) == []


@pytest.fixture
def archivo_bloqueado(monkeypatch):
    """Simula el bloqueo de Windows: bloqueado.txt no se puede borrar."""
    unlink = os.unlink

    def falso_unlink(ruta, *args, **kwargs):
        if os.path.basename(ruta) == "bloqueado.txt":
            raise PermissionError(13, "El proceso no tiene acceso al archivo", str(ruta))
        return unlink(ruta, *args, **kwargs)

    monkeypatch.setattr(os, "unlink", falso_unlink)
    monkeypatch.setattr(verificar.time, "sleep", lambda _segundos: None)


def _con_un_archivo_bloqueado(copia):
    _con_un_archivo(copia)
    (copia / "bloqueado.txt").write_text("x", encoding="utf-8")


def test_archivo_bloqueado_al_borrar_avisa_con_la_ruta(ejecutor, tmp_path, archivo_bloqueado):
    ejecutor.al_copiar = _con_un_archivo_bloqueado

    informe = verificar.verificar(ejecutor, antes_del_commit=True, temporal=tmp_path)

    [copia] = ejecutor.copias
    assert informe.pasa
    assert f"No se pudo borrar la copia temporal del índice: {copia} (bórrala a mano)" in (
        informe.avisos
    )
    assert [p.name for p in copia.iterdir()] == ["bloqueado.txt"]


def test_archivo_bloqueado_con_ctrl_c_avisa_en_stderr(
    ejecutor, tmp_path, archivo_bloqueado, capsys
):
    ejecutor.al_copiar = _con_un_archivo_bloqueado

    def interrumpir(_copia):
        raise KeyboardInterrupt

    ejecutor.al_correr_pytest = interrumpir

    with pytest.raises(KeyboardInterrupt):
        verificar.verificar(ejecutor, antes_del_commit=True, temporal=tmp_path)

    [copia] = ejecutor.copias
    assert f"No se pudo borrar la copia temporal del índice: {copia}" in capsys.readouterr().err


def test_borrar_copia_no_quita_el_acceso_al_directorio_que_no_pudo_borrar(
    ejecutor, tmp_path, archivo_bloqueado, monkeypatch
):
    """En Linux, fijar S_IWRITE deja el directorio sin lectura ni acceso: hay que sumarlo."""
    modos = {}
    chmod = os.chmod

    def espia(ruta, modo, *args, **kwargs):
        modos[Path(ruta)] = modo
        return chmod(ruta, modo, *args, **kwargs)

    monkeypatch.setattr(os, "chmod", espia)
    ejecutor.al_copiar = _con_un_archivo_bloqueado

    verificar.verificar(ejecutor, antes_del_commit=True, temporal=tmp_path)

    [copia] = ejecutor.copias
    assert modos[copia] & stat.S_IRWXU == stat.S_IRWXU, oct(modos[copia])


def test_borrar_copia_reintenta_los_archivos_de_solo_lectura(tmp_path):
    copia = tmp_path / "copia"
    copia.mkdir()
    solo_lectura = copia / "solo-lectura.txt"
    solo_lectura.write_text("x", encoding="utf-8")
    solo_lectura.chmod(0o444)

    assert verificar.borrar_copia(copia) == []
    assert not copia.exists()


# --- Integración: git y Ruff de verdad en un repo temporal ---

requiere_uv = pytest.mark.skipif(shutil.which("uv") is None, reason="uv no está en el PATH")

PYPROJECT_MINIMO = '[project]\nname = "prueba"\nversion = "0"\nrequires-python = ">=3.13"\n'
CON_ERROR_DE_RUFF = "import os\n"  # F401: importado y sin usar


class EjecutorMixto:
    """git y Ruff de verdad; pytest falso, para no correr la suite dentro de sí misma."""

    def __init__(self):
        self.pytest = []

    def __call__(self, comando, entorno=None, carpeta=None):
        if comando == verificar.PYTEST:
            archivos = {p.name: p.read_text(encoding="utf-8") for p in carpeta.glob("*.py")}
            self.pytest.append({"carpeta": carpeta, "archivos": archivos})
            return Salida(0, SALIDA_PYTEST)
        return verificar.ejecutar(comando, entorno, carpeta)


@pytest.fixture
def repo(tmp_path, monkeypatch):
    raiz = tmp_path / "repo"
    raiz.mkdir()

    def git(*args):
        return subprocess.run(
            ["git", *args], cwd=raiz, capture_output=True, text=True, check=True
        ).stdout

    def escribir(nombre, texto):
        (raiz / nombre).write_text(texto, encoding="utf-8")

    git("init", "-q", "-b", "main")
    git("config", "user.name", "Prueba")
    git("config", "user.email", "prueba@users.noreply.github.com")
    escribir("pyproject.toml", PYPROJECT_MINIMO)
    escribir("bien.py", "VALOR = 1\n")
    git("add", ".")
    git("commit", "-q", "-m", "chore: base")
    monkeypatch.chdir(raiz)
    temporal = tmp_path / "temporal"
    temporal.mkdir()
    return git, escribir, temporal


def verificar_indice(temporal, ejecutor=None):
    return verificar.verificar(
        ejecutor or EjecutorMixto(), antes_del_commit=True, temporal=temporal
    )


@requiere_uv
def test_indice_correcto_y_error_de_ruff_fuera_del_indice_pasa_con_aviso(repo):
    git, escribir, temporal = repo
    escribir("nuevo.py", "OTRO = 2\n")
    git("add", "nuevo.py")
    escribir("bien.py", CON_ERROR_DE_RUFF)  # fuera del índice

    ejecutor = EjecutorMixto()
    informe = verificar_indice(temporal, ejecutor)

    assert informe.pasa, informe.fallas
    assert "Fuera de este commit (no se verifica):\n-  M bien.py" in informe.avisos
    [corrida] = ejecutor.pytest
    assert corrida["archivos"]["bien.py"].strip() == "VALOR = 1"
    assert corrida["archivos"]["nuevo.py"].strip() == "OTRO = 2"


@requiere_uv
def test_indice_con_error_y_correccion_fuera_del_indice_no_pasa(repo):
    git, escribir, temporal = repo
    escribir("bien.py", CON_ERROR_DE_RUFF)
    git("add", "bien.py")
    escribir("bien.py", "VALOR = 2\n")  # la corrección no está en el índice

    informe = verificar_indice(temporal)

    assert not informe.pasa
    assert nombres_fallidos(informe) == ["ruff check"]


@requiere_uv
def test_archivo_sin_seguimiento_avisa_y_no_falla(repo):
    _, escribir, temporal = repo
    escribir("suelto.py", CON_ERROR_DE_RUFF)

    ejecutor = EjecutorMixto()
    informe = verificar_indice(temporal, ejecutor)

    assert informe.pasa, informe.fallas
    assert "Fuera de este commit (no se verifica):\n- ?? suelto.py" in informe.avisos
    assert "suelto.py" not in ejecutor.pytest[0]["archivos"]


@requiere_uv
@pytest.mark.parametrize("con_error", [False, True])
def test_no_cambia_carpeta_indice_head_ni_stash(repo, con_error):
    git, escribir, temporal = repo
    escribir("guardado.py", "GUARDADO = 1\n")
    git("add", "guardado.py")
    git("stash", "push", "-q", "-m", "trabajo guardado")
    escribir("indexado.py", CON_ERROR_DE_RUFF if con_error else "INDEXADO = 1\n")
    git("add", "indexado.py")
    escribir("bien.py", "VALOR = 3\n")
    escribir("suelto.py", "SUELTO = 1\n")

    def estado():
        return (
            git("status", "--porcelain"),
            git("stash", "list"),
            git("rev-parse", "HEAD"),
            git("ls-files", "--stage"),
            Path(".git/index").read_bytes(),
            {p.name: p.read_bytes() for p in Path().iterdir() if p.is_file()},
        )

    antes = estado()
    informe = verificar_indice(temporal)

    assert informe.pasa is not con_error
    assert estado() == antes
    assert list(temporal.iterdir()) == []


# --- Registro de la salida de pytest cuando falla (D13 de US-001) ---

SALIDA_PYTEST_FALLIDA = (
    "collected 284 items\n"
    "E   psycopg.errors.UniqueViolation: duplicate key value\n"
    "FAIL Required test coverage of 80.0% not reached. Total coverage: 75.10%\n"
    "========== 1 failed, 283 passed in 11.02s ==========\n"
)
MOMENTO = datetime(2026, 10, 22, 9, 5, 7)


def test_pytest_que_falla_guarda_la_salida_completa(ejecutor, tmp_path):
    ejecutor.respuestas[verificar.PYTEST] = Salida(1, SALIDA_PYTEST_FALLIDA)
    carpeta = tmp_path / ".verificar"

    informe = verificar.verificar(ejecutor, registros=carpeta, ahora=lambda: MOMENTO)

    archivo = carpeta / "pytest-20261022-090507.txt"
    assert archivo.read_text(encoding="utf-8") == SALIDA_PYTEST_FALLIDA
    assert any(str(archivo) in falla for falla in informe.fallas)


def test_pytest_que_pasa_no_guarda_nada(ejecutor, tmp_path):
    carpeta = tmp_path / ".verificar"

    informe = verificar.verificar(ejecutor, registros=carpeta, ahora=lambda: MOMENTO)

    assert informe.pasa
    assert not carpeta.exists()


def test_sin_carpeta_de_registros_no_guarda_nada(ejecutor, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    ejecutor.respuestas[verificar.PYTEST] = Salida(1, SALIDA_PYTEST_FALLIDA)

    verificar.verificar(ejecutor)

    assert list(tmp_path.iterdir()) == []


def test_main_guarda_la_salida_y_el_resumen_muestra_la_ruta(ejecutor, tmp_path, capsys):
    ejecutor.respuestas[verificar.PYTEST] = Salida(1, SALIDA_PYTEST_FALLIDA)

    codigo = verificar.main(
        [], ejecutar=ejecutor, gh=lambda _: None, ahora=lambda: MOMENTO, registros=tmp_path
    )

    archivo = tmp_path / "pytest-20261022-090507.txt"
    assert codigo == 1
    assert archivo.exists()
    assert f"salida completa en {archivo}" in capsys.readouterr().out


def test_la_ruta_dentro_del_repo_se_muestra_relativa(ejecutor):
    archivo = verificar.RAIZ / ".verificar" / "pytest-20261022-090507.txt"

    assert verificar.ruta_legible(archivo) == ".verificar/pytest-20261022-090507.txt"


def test_main_guarda_por_defecto_en_la_carpeta_ignorada_del_repo():
    assert verificar.REGISTROS == verificar.RAIZ / ".verificar"
    assert ".verificar/" in (verificar.RAIZ / ".gitignore").read_text(encoding="utf-8").splitlines()


# --- Cobertura propia de cada ejecución (D13 de US-001) ---


def test_pytest_usa_un_archivo_de_cobertura_propio(ejecutor):
    """Con el .coverage compartido, otro pytest al mismo tiempo rompe el de verificar.py."""
    verificar.verificar(ejecutor)

    archivo = verificar.RAIZ / ".verificar" / f".coverage-{os.getpid()}"
    assert ejecutor.entornos == {verificar.PYTEST: {"COVERAGE_FILE": str(archivo)}}


def test_ejecutar_agrega_el_entorno_pedido(monkeypatch):
    def falso_run(comando, **kwargs):
        assert kwargs["env"]["COVERAGE_FILE"] == "propio"
        assert kwargs["env"]["PATH"] == os.environ["PATH"]
        return subprocess.CompletedProcess(comando, 0, stdout="")

    monkeypatch.setattr(verificar.subprocess, "run", falso_run)
    assert verificar.ejecutar(("uv",), {"COVERAGE_FILE": "propio"}) == Salida(0, "")


def test_ejecutar_sin_entorno_hereda_el_de_la_terminal(monkeypatch):
    def falso_run(comando, **kwargs):
        assert kwargs["env"] is None
        return subprocess.CompletedProcess(comando, 0, stdout="")

    monkeypatch.setattr(verificar.subprocess, "run", falso_run)
    verificar.ejecutar(("git", "status"))


def test_borra_su_archivo_de_cobertura_al_terminar(ejecutor, monkeypatch, tmp_path):
    monkeypatch.setattr(verificar, "RAIZ", tmp_path)
    datos = tmp_path / ".verificar" / f".coverage-{os.getpid()}"

    def pytest_que_deja_datos(comando, entorno=None, carpeta=None):
        if comando == verificar.PYTEST:
            datos.parent.mkdir(parents=True, exist_ok=True)
            datos.write_text("datos", encoding="utf-8")
        return ejecutor(comando, entorno, carpeta)

    verificar.verificar(pytest_que_deja_datos)

    assert not datos.exists()
