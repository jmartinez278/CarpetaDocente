"""Pruebas del script de verificación antes de un commit o PR (scripts/verificar.py)."""

import json
import subprocess
from datetime import datetime

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

    def __call__(self, comando):
        comando = tuple(comando)
        self.ejecutados.append(comando)
        return self.respuestas[comando]


@pytest.fixture
def ejecutor():
    return EjecutorFalso()


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

NOMBRE_INDICE = "Todo lo del commit está en el índice"


def test_antes_del_commit_acepta_cambios_solo_en_el_indice(ejecutor):
    ejecutor.respuestas[verificar.ESTADO] = Salida(
        0, "M  README.md\nA  scripts/nuevo.py\nD  viejo.py\n"
    )
    informe = verificar.verificar(ejecutor, antes_del_commit=True)
    assert informe.pasa
    nombres = [r.nombre for r in informe.resultados]
    assert NOMBRE_INDICE in nombres
    assert "git status limpio" not in nombres


@pytest.mark.parametrize(
    "linea",
    [" M README.md", "MM README.md", "AM scripts/nuevo.py", " D viejo.py", "?? suelto.py"],
)
def test_antes_del_commit_falla_con_cambios_fuera_del_indice(ejecutor, linea):
    ejecutor.respuestas[verificar.ESTADO] = Salida(0, f"M  CLAUDE.md\n{linea}\n")
    informe = verificar.verificar(ejecutor, antes_del_commit=True)
    assert nombres_fallidos(informe) == [NOMBRE_INDICE]
    assert informe.fallas == [f"{NOMBRE_INDICE}: {linea}"]


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
    assert NOMBRE_INDICE in nombres_fallidos(informe)


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
