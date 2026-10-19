"""Pruebas de los hooks de git (.githooks/) y de las reglas que comparten con verificar.py."""

import shutil
import subprocess
from pathlib import Path

import pytest

import hooks
import reglas

RAIZ = Path(__file__).resolve().parents[2]


# --- Reglas del mensaje de commit ---


@pytest.mark.parametrize(
    "mensaje",
    [
        "EN-01: algo\n\nCo-Authored-By: Alguien <a@b.c>\n",
        "EN-01: algo\n\nco-authored-by: Alguien <a@b.c>\n",
        "EN-01: algo\n\n🤖 Generated with Claude Code\n",
        "EN-01: algo\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)\n",
        "EN-01: algo\n\nGenerated with **[Claude  Code]**\n",
        "EN-01: algo\n\nClaude-Session: abc123\n",
    ],
)
def test_marcas_en_mensaje_detecta_atribuciones(mensaje):
    assert reglas.marcas_en_mensaje(mensaje)


def test_marcas_en_mensaje_acepta_mensaje_limpio():
    assert reglas.marcas_en_mensaje("EN-01: proyecto Django\n\nDetalle del cambio.\n") == []


def test_marcas_en_mensaje_ignora_comentarios_del_editor():
    assert reglas.marcas_en_mensaje("EN-01: algo\n# Co-Authored-By en un comentario\n") == []


# --- Reglas de archivos prohibidos ---


@pytest.mark.parametrize(
    "ruta",
    [
        ".env",
        ".env.local",
        "src/.env",
        "insumos/stitch/pantalla.html",
        "node_modules/x/index.js",
        "src/frontend/node_modules/x/index.js",
        "src/backend/static/dist/app.css",
        "coverage.xml",
    ],
)
def test_archivo_prohibido(ruta):
    assert reglas.motivo_prohibido(ruta)


@pytest.mark.parametrize(
    "ruta",
    [".env.example", "src/backend/static/img/logo.svg", "docs/insumos.md", "README.md"],
)
def test_archivo_permitido(ruta):
    assert reglas.motivo_prohibido(ruta) is None


def test_archivos_prohibidos_lista_solo_los_prohibidos():
    resultado = reglas.archivos_prohibidos(["README.md", ".env", "coverage.xml"])
    assert [ruta for ruta, _ in resultado] == [".env", "coverage.xml"]


# --- commit-msg ---


def test_commit_msg_rechaza_atribucion(tmp_path, capsys):
    archivo = tmp_path / "COMMIT_EDITMSG"
    archivo.write_text("EN-01: algo\n\nCo-Authored-By: X <x@y.z>\n", encoding="utf-8")
    assert hooks.main(["commit-msg", str(archivo)]) == 1
    assert "Co-Authored-By" in capsys.readouterr().err


def test_commit_msg_acepta_mensaje_limpio(tmp_path):
    archivo = tmp_path / "COMMIT_EDITMSG"
    archivo.write_text("EN-01: algo\n", encoding="utf-8")
    assert hooks.main(["commit-msg", str(archivo)]) == 0


# --- pre-commit ---


def test_pre_commit_rechaza_archivo_prohibido_sin_correr_ruff(monkeypatch, capsys):
    monkeypatch.setattr(hooks, "archivos_en_indice", lambda: ["README.md", ".env"])
    llamadas = []
    monkeypatch.setattr(hooks, "correr", lambda comando: llamadas.append(comando) or 0)
    assert hooks.main(["pre-commit"]) == 1
    assert ".env" in capsys.readouterr().err
    assert llamadas == []


def test_pre_commit_corre_ruff_check_y_format(monkeypatch):
    monkeypatch.setattr(hooks, "archivos_en_indice", lambda: ["README.md"])
    llamadas = []
    monkeypatch.setattr(hooks, "correr", lambda comando: llamadas.append(comando) or 0)
    assert hooks.main(["pre-commit"]) == 0
    assert llamadas == [list(c) for c in hooks.COMANDOS_RUFF]


def test_pre_commit_falla_si_ruff_falla(monkeypatch, capsys):
    monkeypatch.setattr(hooks, "archivos_en_indice", lambda: ["README.md"])
    monkeypatch.setattr(hooks, "correr", lambda comando: 1 if "format" in comando else 0)
    assert hooks.main(["pre-commit"]) == 1
    assert "ruff format" in capsys.readouterr().err


def test_archivos_en_indice_lee_git(monkeypatch):
    def falso_run(comando, **kwargs):
        assert comando[:3] == ["git", "diff", "--cached"]
        return subprocess.CompletedProcess(comando, 0, stdout="a.py\0.env\0")

    monkeypatch.setattr(hooks.subprocess, "run", falso_run)
    assert hooks.archivos_en_indice() == ["a.py", ".env"]


def test_correr_devuelve_codigo_de_salida(monkeypatch):
    monkeypatch.setattr(
        hooks.subprocess, "run", lambda comando, **kw: subprocess.CompletedProcess(comando, 3)
    )
    assert hooks.correr(["uv", "run", "ruff", "check"]) == 3


def test_main_rechaza_hook_desconocido(capsys):
    assert hooks.main(["post-commit"]) == 2
    assert "desconocido" in capsys.readouterr().err


# --- Integración: los .githooks reales en un repo temporal ---

requiere_uv = pytest.mark.skipif(shutil.which("uv") is None, reason="uv no está en el PATH")


@pytest.fixture
def repo_con_hooks(tmp_path):
    def git(*args):
        return subprocess.run(
            ["git", *args], cwd=tmp_path, capture_output=True, text=True, check=False
        )

    git("init", "-q")
    git("config", "user.name", "Prueba")
    git("config", "user.email", "prueba@users.noreply.github.com")
    git("config", "core.hooksPath", str(RAIZ / ".githooks"))
    return tmp_path, git


@requiere_uv
def test_hook_real_commit_msg_rechaza_atribucion(repo_con_hooks):
    _, git = repo_con_hooks
    resultado = git("commit", "-q", "--allow-empty", "--no-verify", "-m", "x")
    assert resultado.returncode == 0  # base sin hooks
    resultado = git("commit", "--allow-empty", "-m", "EN-01: algo\n\nClaude-Session: abc")
    assert resultado.returncode != 0
    assert "Claude-Session" in resultado.stderr


@requiere_uv
def test_hook_real_pre_commit_rechaza_env(repo_con_hooks):
    carpeta, git = repo_con_hooks
    (carpeta / ".env").write_text("CLAVE=x\n", encoding="utf-8")
    git("add", "-f", ".env")
    resultado = git("commit", "-m", "EN-01: algo")
    assert resultado.returncode != 0
    assert ".env" in resultado.stderr


def test_marcas_en_mensaje_exige_generated_y_claude_code_en_la_misma_linea():
    assert reglas.marcas_en_mensaje("EN-01: Generated with care\n\nRevisado en Claude Code\n") == []
