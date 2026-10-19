"""Pruebas de la copia del repo para el Proyecto de claude.ai (scripts/copiar_para_proyecto.py)."""

from pathlib import Path

import pytest

import copiar_para_proyecto as copia

INCLUIDOS = [
    "README.md",
    "CLAUDE.md",
    "pyproject.toml",
    "docs/02 Planificación/01 Transformando a ágil V_1_2_0.md",
    "docs/03 Implementación/verificacion.md",
    "openspec/config.yaml",
    "openspec/specs/cuentas/spec.md",
    "openspec/changes/archive/2026-10-01-en-01/tasks.md",
    "src/backend/cuentas/models.py",
    "src/backend/notas/services.py",
    "src/backend/config/settings.py",
    "src/backend/config/urls.py",
]
EXCLUIDOS = [
    # Fuera de lo útil para el chat del Proyecto.
    ".env.example",
    ".gitignore",
    ".gitattributes",
    ".dockerignore",
    ".python-version",
    "Dockerfile",
    "docker-compose.yml",
    "sonar-project.properties",
    ".github/workflows/ci.yml",
    ".githooks/pre-commit",
    "scripts/verificar.py",
    "scripts/tests/test_verificar.py",
    "src/backend/manage.py",
    "src/backend/cuentas/__init__.py",
    "src/backend/cuentas/apps.py",
    "src/backend/cuentas/admin.py",
    "src/backend/cuentas/views.py",
    "src/backend/cuentas/migrations/0001_initial.py",
    "src/backend/cuentas/migrations/__init__.py",
    "src/backend/cuentas/tests/test_modelos.py",
    "src/backend/cuentas/tests/models.py",
    "src/backend/cuentas/migrations/services.py",
    "src/backend/config/asgi.py",
    "src/backend/config/wsgi.py",
    "src/backend/config/tests/test_settings.py",
    "src/backend/templates/base.html",
    "src/backend/static/img/logo.svg",
    "src/frontend/package.json",
    "src/frontend/css/app.css",
    "otra/models.py",
    # Prohibidos o generados.
    ".git/HEAD",
    ".venv/Lib/site.py",
    "node_modules/x/index.js",
    "src/frontend/node_modules/x/index.js",
    "uv.lock",
    "src/frontend/package-lock.json",
    "coverage.xml",
    "src/backend/static/dist/app.css",
    "insumos/stitch/pantalla.html",
    ".env",
    ".env.local",
    "docs/.env",
    ".claude/settings.local.json",
    ".claude/skills/tesis/SKILL.md",
    ".claude/commands/opsx/apply.md",
    ".coverage",
    "htmlcov/index.html",
    "src/backend/config/__pycache__/settings.cpython-313.pyc",
    ".pytest_cache/v/cache/nodeids",
    ".ruff_cache/0.17.1/abc",
    "test-results/traza.zip",
]


def crear(raiz: Path, rutas, contenido="x"):
    for ruta in rutas:
        archivo = raiz / ruta
        archivo.parent.mkdir(parents=True, exist_ok=True)
        archivo.write_text(contenido, encoding="utf-8")


def archivos_de(carpeta: Path) -> set[str]:
    return {p.relative_to(carpeta).as_posix() for p in carpeta.rglob("*") if p.is_file()}


@pytest.fixture
def repo(tmp_path):
    origen = tmp_path / "CarpetaDocente"
    crear(origen, INCLUIDOS + EXCLUIDOS)
    return origen


def no_preguntar(_):
    raise AssertionError("no debía preguntar")


# --- Qué se copia ---


@pytest.mark.parametrize("ruta", EXCLUIDOS)
def test_excluido(ruta):
    assert copia.excluido(ruta)


@pytest.mark.parametrize("ruta", INCLUIDOS)
def test_incluido(ruta):
    assert not copia.excluido(ruta)


def test_copia_solo_lo_permitido(repo, tmp_path):
    destino = tmp_path / "CarpetaDocente_para_Proyecto"
    resumen = copia.copiar(repo, destino, preguntar=no_preguntar)
    assert archivos_de(destino) == set(INCLUIDOS)
    assert resumen.cantidad == len(INCLUIDOS)
    assert resumen.tamano == len(INCLUIDOS)  # un byte por archivo


def test_cinco_archivos_mas_pesados(repo, tmp_path):
    for indice, ruta in enumerate(INCLUIDOS):
        (repo / ruta).write_bytes(b"x" * (indice + 1) * 100)
    resumen = copia.copiar(repo, tmp_path / "destino", preguntar=no_preguntar)
    assert [ruta for ruta, _ in resumen.mas_pesados] == list(reversed(INCLUIDOS))[:5]
    assert resumen.mas_pesados[0][1] == len(INCLUIDOS) * 100


def test_destino_por_defecto_se_llama_carpetadocente_junto_al_repo():
    origen = Path("C:/Proyectos/CarpetaDocente")
    destino = copia.destino_por_defecto(origen)
    assert destino == Path("C:/Proyectos/_para_Proyecto/CarpetaDocente")
    assert destino.name == "CarpetaDocente"


# --- Destino que ya existe ---


def test_destino_existente_y_respuesta_no_lo_deja_intacto(repo, tmp_path):
    destino = tmp_path / "destino"
    crear(destino, ["viejo.txt"])
    preguntas = []
    with pytest.raises(copia.CopiaCancelada):
        copia.copiar(repo, destino, preguntar=lambda texto: preguntas.append(texto) or "n")
    assert archivos_de(destino) == {"viejo.txt"}
    assert str(destino) in preguntas[0]


@pytest.mark.parametrize("respuesta", ["s", "S", "si", "sí"])
def test_destino_existente_y_respuesta_si_lo_reemplaza(repo, tmp_path, respuesta):
    destino = tmp_path / "destino"
    crear(destino, ["viejo.txt"])
    copia.copiar(repo, destino, preguntar=lambda _: respuesta)
    assert archivos_de(destino) == set(INCLUIDOS)


def test_sin_terminal_para_preguntar_no_borra(repo, tmp_path):
    destino = tmp_path / "destino"
    crear(destino, ["viejo.txt"])

    def sin_entrada(_):
        raise EOFError

    with pytest.raises(copia.CopiaCancelada):
        copia.copiar(repo, destino, preguntar=sin_entrada)
    assert archivos_de(destino) == {"viejo.txt"}


def test_borrar_no_toca_nada_fuera_del_destino(repo, tmp_path):
    destino = tmp_path / "destino"
    crear(destino, ["viejo.txt"])
    crear(tmp_path, ["vecino.txt"])
    copia.copiar(repo, destino, preguntar=lambda _: "s")
    assert (tmp_path / "vecino.txt").exists()
    assert archivos_de(repo) == set(INCLUIDOS + EXCLUIDOS)


# --- Destinos peligrosos: se rechazan sin preguntar ni borrar ---


def test_destino_dentro_del_repo(repo):
    with pytest.raises(copia.DestinoInvalido, match="dentro del repo"):
        copia.copiar(repo, repo / "copia", preguntar=no_preguntar)


def test_destino_igual_al_repo(repo):
    with pytest.raises(copia.DestinoInvalido, match="dentro del repo"):
        copia.copiar(repo, repo, preguntar=no_preguntar)


def test_destino_que_contiene_al_repo(repo, tmp_path):
    with pytest.raises(copia.DestinoInvalido, match="contiene al repo"):
        copia.copiar(repo, tmp_path, preguntar=no_preguntar)
    assert archivos_de(repo) == set(INCLUIDOS + EXCLUIDOS)


def test_destino_que_es_otro_repo_de_git(repo, tmp_path):
    otro = tmp_path / "otro"
    crear(otro, [".git/HEAD", "a.txt"])
    with pytest.raises(copia.DestinoInvalido, match="repositorio de git"):
        copia.copiar(repo, otro, preguntar=no_preguntar)
    assert archivos_de(otro) == {".git/HEAD", "a.txt"}


def test_destino_que_es_un_archivo(repo, tmp_path):
    archivo = tmp_path / "destino.txt"
    archivo.write_text("x", encoding="utf-8")
    with pytest.raises(copia.DestinoInvalido, match="no es una carpeta"):
        copia.copiar(repo, archivo, preguntar=no_preguntar)
    assert archivo.read_text(encoding="utf-8") == "x"


# --- Salida ---


def test_tamano_legible():
    assert copia.tamano_legible(512) == "512 B"
    assert copia.tamano_legible(1536) == "1,5 KB"
    assert copia.tamano_legible(3 * 1024 * 1024) == "3,0 MB"


def test_formatear_resumen(tmp_path):
    resumen = copia.Resumen(tmp_path, 2, 2048, [("a.md", 1536), ("b.md", 512)])
    texto = copia.formatear(resumen)
    assert "Archivos copiados: 2" in texto
    assert "Tamaño total: 2,0 KB" in texto
    assert "1,5 KB  a.md" in texto
    assert str(tmp_path) in texto


# --- main ---


def test_main_copia_al_destino_indicado(repo, tmp_path, capsys):
    destino = tmp_path / "otra"
    codigo = copia.main(["--destino", str(destino)], origen=repo, preguntar=no_preguntar)
    assert codigo == 0
    assert archivos_de(destino) == set(INCLUIDOS)
    assert f"Archivos copiados: {len(INCLUIDOS)}" in capsys.readouterr().out


def test_main_usa_el_destino_por_defecto(repo, capsys):
    assert copia.main([], origen=repo, preguntar=no_preguntar) == 0
    destino = repo.parent / "_para_Proyecto" / "CarpetaDocente"
    assert archivos_de(destino) == set(INCLUIDOS)


def test_main_cancelado_devuelve_1(repo, tmp_path, capsys):
    destino = tmp_path / "destino"
    crear(destino, ["viejo.txt"])
    assert copia.main(["--destino", str(destino)], origen=repo, preguntar=lambda _: "") == 1
    assert "No se copió nada" in capsys.readouterr().err


def test_main_destino_invalido_devuelve_2(repo, capsys):
    assert copia.main(["--destino", str(repo / "x")], origen=repo, preguntar=no_preguntar) == 2
    assert "dentro del repo" in capsys.readouterr().err


def test_reemplaza_destino_con_archivos_de_solo_lectura(repo, tmp_path):
    destino = tmp_path / "destino"
    crear(destino, ["viejo.txt"])
    (destino / "viejo.txt").chmod(0o444)
    copia.copiar(repo, destino, preguntar=lambda _: "s")
    assert archivos_de(destino) == set(INCLUIDOS)
