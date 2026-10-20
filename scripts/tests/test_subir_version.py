"""Pruebas de la subida de versión de un documento (scripts/subir_version.py)."""

import subprocess
from pathlib import Path

import pytest

import subir_version as sv

DOC = """[← Volver al README Principal](../../README.md)

# 07. Requisitos no funcionales

| Campo | Detalle |
|---|---|
| **Asesor** | Ing. Ejemplo |
| **Fecha** | 14/10/2026 |
| **Versión** | 1.0.0 |

---

## 1. Algo

Texto.

## Historial de cambios

| Versión | Fecha | Autor | Descripción |
|---|---|---|---|
| 1.0.0 | 14/10/2026 | Equipo del proyecto | Versión inicial. |

[← Volver al README Principal](../../README.md)
"""

README = """# Proyecto

7. [Requisitos no funcionales](<docs/01 Inicio/07. Requisitos no funcionales V_1_0_0.md>)
8. [Usuarios](<docs/01 Inicio/08. Usuarios V_1_1_0.md>)
"""

RUTA = "docs/01 Inicio/07. Requisitos no funcionales V_1_0_0.md"


def test_version_menor_sube_el_segundo_numero():
    assert sv.siguiente_version("1.3.0") == "1.4.0"


def test_version_mayor_sube_el_primero_y_reinicia_los_demas():
    assert sv.siguiente_version("1.3.2", mayor=True) == "2.0.0"


def test_version_del_nombre_del_archivo():
    assert sv.version_del_nombre(RUTA) == "1.0.0"


def test_nombre_sin_version_se_rechaza():
    with pytest.raises(sv.DocumentoInvalido):
        sv.version_del_nombre("docs/01 Inicio/sin version.md")


def test_ruta_con_la_nueva_version():
    assert sv.ruta_con_version(RUTA, "1.1.0") == (
        "docs/01 Inicio/07. Requisitos no funcionales V_1_1_0.md"
    )


def test_encabezado_con_nueva_version_y_fecha():
    texto = sv.actualizar_encabezado(DOC, "1.1.0", "19/10/2026")
    assert "| **Versión** | 1.1.0 |" in texto
    assert "| **Fecha** | 19/10/2026 |" in texto
    assert "| 1.0.0 | 14/10/2026 |" in texto  # el historial no se toca


def test_encabezado_sin_campo_version_se_rechaza():
    with pytest.raises(sv.DocumentoInvalido):
        sv.actualizar_encabezado("# Sin encabezado\n", "1.1.0", "19/10/2026")


def test_fila_nueva_al_final_del_historial():
    texto = sv.agregar_historial(DOC, "1.1.0", "19/10/2026", "Equipo del proyecto", "Cambio X.")
    filas = [linea for linea in texto.splitlines() if linea.startswith("| 1.")]
    assert filas[-1] == "| 1.1.0 | 19/10/2026 | Equipo del proyecto | Cambio X. |"
    assert texto.endswith("[← Volver al README Principal](../../README.md)\n")


def test_documento_sin_historial_se_rechaza():
    with pytest.raises(sv.DocumentoInvalido):
        sv.agregar_historial("# Sin historial\n", "1.1.0", "19/10/2026", "E", "D")


def test_descripcion_con_barra_vertical_se_rechaza():
    with pytest.raises(sv.DocumentoInvalido):
        sv.agregar_historial(DOC, "1.1.0", "19/10/2026", "E", "A | B")


def test_enlace_del_readme_apunta_al_nuevo_nombre():
    nueva = sv.ruta_con_version(RUTA, "1.1.0")
    texto = sv.actualizar_readme(README, RUTA, nueva)
    assert f"(<{nueva}>)" in texto
    assert RUTA not in texto
    assert "08. Usuarios V_1_1_0.md" in texto


def test_readme_sin_el_enlace_se_rechaza():
    with pytest.raises(sv.DocumentoInvalido):
        sv.actualizar_readme("# Vacío\n", RUTA, "otra.md")


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True, encoding="utf-8"
    ).stdout


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "prueba@users.noreply.github.com")
    _git(tmp_path, "config", "user.name", "Prueba")
    doc = tmp_path / RUTA
    doc.parent.mkdir(parents=True)
    doc.write_text(DOC, encoding="utf-8")
    (tmp_path / "README.md").write_text(README, encoding="utf-8")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-q", "-m", "inicio")
    return tmp_path


def test_subir_renombra_con_git_mv_y_actualiza_todo(repo: Path):
    nueva = sv.subir(repo, RUTA, "Cambio X.", fecha="19/10/2026")

    assert nueva == "docs/01 Inicio/07. Requisitos no funcionales V_1_1_0.md"
    assert not (repo / RUTA).exists()
    texto = (repo / nueva).read_text(encoding="utf-8")
    assert "| **Versión** | 1.1.0 |" in texto
    assert "| 1.1.0 | 19/10/2026 | Equipo del proyecto | Cambio X. |" in texto
    assert f"(<{nueva}>)" in (repo / "README.md").read_text(encoding="utf-8")
    # git mv deja el cambio de nombre en el índice
    assert "R" in _git(repo, "status", "--porcelain", "--", nueva)


def test_subir_sin_enlace_en_el_readme_no_cambia_nada(repo: Path):
    (repo / "README.md").write_text("# Sin enlaces\n", encoding="utf-8")

    with pytest.raises(sv.DocumentoInvalido):
        sv.subir(repo, RUTA, "Cambio X.", fecha="19/10/2026")

    assert (repo / RUTA).read_text(encoding="utf-8") == DOC


def test_main_informa_la_ruta_nueva(repo: Path, capsys):
    codigo = sv.main([RUTA, "--descripcion", "Cambio X.", "--fecha", "19/10/2026"], raiz=repo)

    assert codigo == 0
    assert "V_1_1_0.md" in capsys.readouterr().out


def test_main_con_error_sale_con_2(repo: Path, capsys):
    codigo = sv.main(["docs/no existe V_1_0_0.md", "--descripcion", "X."], raiz=repo)

    assert codigo == 2
    assert "No se cambió nada" in capsys.readouterr().err
