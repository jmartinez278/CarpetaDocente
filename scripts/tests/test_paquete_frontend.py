"""Pruebas del paquete de src/frontend: una hoja de Tailwind y su vigilancia.

rebrand-base, D2 y D3; rebrand-cierre, D2 (se retira la hoja vieja).
"""

import json
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
FRONTEND = RAIZ / "src" / "frontend"


@pytest.fixture(scope="module")
def scripts():
    return json.loads((FRONTEND / "package.json").read_text(encoding="utf-8"))["scripts"]


def _tailwind(comando):
    """Cada llamada a tailwindcss del comando, como lista de argumentos."""
    return [parte.split() for parte in comando.split("&&") if "tailwindcss" in parte]


def test_build_compila_una_sola_hoja_minificada(scripts):
    llamadas = _tailwind(scripts["build"])

    pares = [(ll[ll.index("-i") + 1], ll[ll.index("-o") + 1]) for ll in llamadas]
    assert pares == [("./css/rebrand.css", "../backend/static/dist/rebrand.css")]
    assert all("--minify" in ll for ll in llamadas)
    assert scripts["build"].startswith("npm run copiar-vendor && ")


def test_dev_y_dev_contenedor_usan_vigilar_mjs(scripts):
    assert scripts["dev"] == "npm run copiar-vendor && node scripts/vigilar.mjs"
    assert scripts["dev:contenedor"] == (
        "npm run copiar-vendor && node scripts/vigilar.mjs --poll=1000"
    )


def test_vigilar_mjs_nombra_una_sola_entrada_y_su_salida():
    texto = (FRONTEND / "scripts" / "vigilar.mjs").read_text(encoding="utf-8")

    assert re.findall(r'"\./css/[\w-]+\.css"', texto) == ['"./css/rebrand.css"']
    assert re.findall(r'"\.\./backend/static/dist/[\w-]+\.css"', texto) == [
        '"../backend/static/dist/rebrand.css"'
    ]
    assert "--watch=always" in texto


def test_no_queda_la_entrada_vieja_de_tailwind():
    assert not (FRONTEND / "css" / "app.css").exists()


def test_copiar_vendor_copia_instrument_sans_y_su_licencia_sin_pisar_la_de_besley():
    texto = (FRONTEND / "scripts" / "copiar-vendor.mjs").read_text(encoding="utf-8")
    origen = "node_modules/@fontsource/instrument-sans"

    for peso in (400, 500):
        nombre = f"instrument-sans-latin-{peso}-normal.woff2"
        assert f'"{origen}/files/{nombre}"' in texto
        assert re.search(rf'"fuentes",\s*"{nombre}"', texto)
    assert re.search(rf'"{origen}/LICENSE",\s*"fuentes",\s*"LICENSE-instrument-sans"', texto)
    assert re.search(r'"node_modules/@fontsource/besley/LICENSE",\s*"fuentes",\s*"LICENSE"', texto)


def test_instrument_sans_es_dependencia_del_paquete():
    paquete = json.loads((FRONTEND / "package.json").read_text(encoding="utf-8"))

    assert "@fontsource/instrument-sans" in paquete["dependencies"]


def test_rebrand_css_vigila_sus_parciales_tambien_con_sondeo():
    """Con ``--poll`` la CLI solo ve cambios en sus ``@source`` y en la entrada; con
    ``source(none)``, los parciales importados de ``css/rebrand/`` tienen que ser una."""
    texto = (FRONTEND / "css" / "rebrand.css").read_text(encoding="utf-8")

    assert "source(none)" in texto
    assert '@source "./rebrand";' in texto
