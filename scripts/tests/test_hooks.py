"""Pruebas de los hooks de git (.githooks/) y de las reglas que comparten con verificar.py."""

import shutil
import subprocess
from pathlib import Path

import pytest

import hooks
import reglas

RAIZ = Path(__file__).resolve().parents[2]
LINEAS_AGREGADAS_REAL = hooks.lineas_agregadas


@pytest.fixture(autouse=True)
def indice_sin_lineas(monkeypatch):
    """Por defecto, pre-commit no lee el diff real del repo: cada prueba pone el suyo."""
    monkeypatch.setattr(hooks, "lineas_agregadas", lambda: [])


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
        "insumos/prototipo/pantalla.html",
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


# --- Claves en las líneas agregadas (Tramo 1b) ---
# Los valores se arman por partes: así este archivo no tiene ninguna clave escrita entera.

HEX40 = "0123456789abcdef" * 2 + "01234567"
ALNUM36 = "A1b2C3d4E5" * 3 + "F6g7H8"

CLAVES = [
    ("SECRET" + '_KEY = "django-' + 'insecure-abc123"', "clave de Django"),
    ("SECRET" + '_KEY = "x9s8d7f6g5h4"', "SECRET_KEY con valor literal"),
    ("SECRET" + "_KEY='x9s8d7f6g5h4'", "SECRET_KEY con valor literal"),
    ('"DJANGO_SECRET' + '_KEY": "x9s8d7f6g5h4",', "SECRET_KEY con valor literal"),
    ("token = '" + "sqp" + "_" + HEX40 + "'", "token de SonarQube"),
    ("token = '" + "sqa" + "_" + HEX40 + "'", "token de SonarQube"),
    ("token = '" + "squ" + "_" + HEX40 + "'", "token de SonarQube"),
    ("token = '" + "ghp" + "_" + ALNUM36 + "'", "token de GitHub"),
    ("token = '" + "gho" + "_" + ALNUM36 + "'", "token de GitHub"),
    ("token = '" + "github" + "_pat_" + "11ABCDEFG0" + ALNUM36 + "'", "token de GitHub"),
    ("aws = " + "AK" + "IA" + "ABCDEFGHIJ234567", "clave de acceso de AWS"),
    ("-----BEGIN " + "RSA PRIVATE KEY-----", "llave privada"),
    ("-----BEGIN " + "PRIVATE KEY-----", "llave privada"),
    ("-----BEGIN " + "OPENSSH PRIVATE KEY-----", "llave privada"),
    ("DATABASE_URL=postgres://" + "admin:" + "s3cr3t@db.example.com/x", "cadena de conexión"),
    ("url = 'postgresql://" + "admin:" + "s3cr3t@localhost:5432/x'", "cadena de conexión"),
]


@pytest.mark.parametrize(("linea", "tipo"), CLAVES)
def test_claves_en_linea_detecta(linea, tipo):
    hallazgos = reglas.claves_en_linea("src/backend/config/algo.py", linea)
    assert [nombre for nombre, _ in hallazgos] == [tipo]


@pytest.mark.parametrize(("linea", "tipo"), CLAVES)
def test_fragmento_no_muestra_el_valor_completo(linea, tipo):
    [(_, fragmento)] = reglas.claves_en_linea("src/backend/config/algo.py", linea)
    assert fragmento.endswith("…")
    assert len(fragmento) <= 5
    assert fragmento[:-1] in linea


@pytest.mark.parametrize(
    "linea",
    [
        'SECRET_KEY = env("DJANGO_SECRET_KEY")',
        'SECRET_KEY = ""',
        "DATABASE_URL: postgres://postgres@localhost:5432/carpetadocente",
        "| `DATABASE_URL` | `postgres://<usuario>:<contraseña>@localhost:<puerto>/<base>` |",
        "Patrones de claves (`django-insecure`, tokens `sqp_`/`sqa_`, `ghp_`): ninguno.",
        "AKIA sola no es una clave",
        "https://claude.com/claude-code",
    ],
)
def test_claves_en_linea_no_marca_lo_que_no_es_clave(linea):
    assert reglas.claves_en_linea("README.md", linea) == []


def test_env_example_queda_exento():
    linea = "DATABASE_URL=postgres://" + "admin:" + "s3cr3t@localhost/x"
    assert reglas.claves_en_linea(".env.example", linea) == []


@pytest.mark.parametrize(
    "ruta", ["src/backend/config/tests/test_settings.py", "scripts/tests/test_x.py", "test_y.py"]
)
def test_prueba_con_valor_marcado_como_ficticio_queda_exenta(ruta):
    linea = '"DATABASE_URL": "postgres://' + 'usuario_ficticio:clave_ficticia@servidor/x",'
    assert reglas.claves_en_linea(ruta, linea) == []


def test_prueba_sin_marca_de_ficticio_no_queda_exenta():
    linea = '"DATABASE_URL": "postgres://' + 'admin:s3cr3t@servidor/x",'
    assert reglas.claves_en_linea("src/backend/config/tests/test_settings.py", linea)


def test_marca_de_ficticio_fuera_de_las_pruebas_no_exime():
    linea = "DATABASE_URL = 'postgres://" + "usuario_ficticio:clave_ficticia@servidor/x'"
    assert reglas.claves_en_linea("src/backend/config/settings.py", linea)


# --- Lectura del diff del índice ---

DIFF = (
    "diff --git src/a.py src/a.py\n"
    "index 111..222 100644\n"
    "--- src/a.py\n"
    "+++ src/a.py\n"
    "@@ -3,0 +4,2 @@ def f():\n"
    "+linea cuatro\n"
    "+linea cinco\n"
    "@@ -10 +12 @@\n"
    "-vieja\n"
    "+++ esta línea agregada empieza con dos +\n"
    "diff --git docs/con espacio.md docs/con espacio.md\n"
    "new file mode 100644\n"
    "--- /dev/null\n"
    "+++ docs/con espacio.md\n"
    "@@ -0,0 +1 @@\n"
    "+hola\n"
    "\\ No newline at end of file\n"
    "diff --git logo.png logo.png\n"
    "new file mode 100644\n"
    "Binary files /dev/null and logo.png differ\n"
)


def test_leer_diff_numera_las_lineas_agregadas():
    assert hooks.leer_diff(DIFF) == [
        ("src/a.py", 4, "linea cuatro"),
        ("src/a.py", 5, "linea cinco"),
        ("src/a.py", 12, "++ esta línea agregada empieza con dos +"),
        ("docs/con espacio.md", 1, "hola"),
    ]


def test_lineas_agregadas_lee_el_indice_sin_prefijos(monkeypatch):
    def falso_run(comando, **kwargs):
        assert comando == list(hooks.DIFF_INDICE)
        return subprocess.CompletedProcess(comando, 0, stdout=DIFF)

    monkeypatch.setattr(hooks.subprocess, "run", falso_run)
    assert LINEAS_AGREGADAS_REAL()[0] == ("src/a.py", 4, "linea cuatro")


def test_diff_del_indice_sin_color_ni_prefijos():
    assert "--cached" in hooks.DIFF_INDICE
    assert "--no-prefix" in hooks.DIFF_INDICE
    assert "--no-color" in hooks.DIFF_INDICE
    assert "core.quotePath=false" in hooks.DIFF_INDICE


# --- pre-commit con claves ---


def test_pre_commit_rechaza_clave_con_archivo_y_linea_sin_el_valor(monkeypatch, capsys):
    token = "ghp" + "_" + ALNUM36
    monkeypatch.setattr(hooks, "archivos_en_indice", lambda: ["src/a.py"])
    monkeypatch.setattr(hooks, "lineas_agregadas", lambda: [("src/a.py", 7, f"TOKEN = '{token}'")])
    llamadas = []
    monkeypatch.setattr(hooks, "correr", lambda comando: llamadas.append(comando) or 0)
    assert hooks.main(["pre-commit"]) == 1
    error = capsys.readouterr().err
    assert "src/a.py:7" in error
    assert "token de GitHub" in error
    assert token not in error
    assert ALNUM36 not in error
    assert llamadas == []


def test_pre_commit_sin_claves_sigue_con_ruff(monkeypatch):
    monkeypatch.setattr(hooks, "archivos_en_indice", lambda: ["src/a.py"])
    monkeypatch.setattr(hooks, "lineas_agregadas", lambda: [("src/a.py", 1, "x = 1")])
    llamadas = []
    monkeypatch.setattr(hooks, "correr", lambda comando: llamadas.append(comando) or 0)
    assert hooks.main(["pre-commit"]) == 0
    assert len(llamadas) == 2


@requiere_uv
def test_hook_real_pre_commit_rechaza_clave_en_el_contenido(repo_con_hooks):
    carpeta, git = repo_con_hooks
    token = "ghp" + "_" + ALNUM36
    (carpeta / "config con espacio.py").write_text(f"x = 1\nTOKEN = '{token}'\n", encoding="utf-8")
    git("add", "config con espacio.py")
    resultado = git("commit", "-m", "EN-01: algo")
    assert resultado.returncode != 0
    assert "config con espacio.py:2" in resultado.stderr
    assert token not in resultado.stderr
