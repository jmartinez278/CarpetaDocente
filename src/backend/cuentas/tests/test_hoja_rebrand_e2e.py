"""Hoja del rebrand compilada: tokens, fuentes y capas (rebrand-base, D1 y D3).

Lee ``static/dist/rebrand.css`` y ``app.css`` tal como salen de ``npm run build`` en
``src/frontend/``; por eso va con la marca e2e: ``uv run pytest -m e2e --browser chromium``.
Los valores esperados salen del Quick Start de ``DESIGN.md``.
"""

import re

import pytest

from cuentas.tests.e2e import RAIZ

pytestmark = pytest.mark.e2e

DIST = RAIZ / "src" / "backend" / "static" / "dist"
DECLARACION = re.compile(r"(--[\w-]+|color-scheme)\s*:\s*([^;{}]+)")


# --- Lectura del Quick Start y de la hoja compilada -------------------------------------------


def _quick_start():
    texto = (RAIZ / "DESIGN.md").read_text(encoding="utf-8")
    seccion = texto[texto.index("## Quick Start") :]
    return seccion[seccion.index("```css") : seccion.index("```", seccion.index("```css") + 6)]


def _bloque(texto, apertura):
    """Contenido del bloque ``{ … }`` que empieza en ``apertura`` (con llaves anidadas)."""
    inicio = texto.index(apertura) + len(apertura)
    nivel = 1
    for posicion in range(inicio, len(texto)):
        nivel += {"{": 1, "}": -1}.get(texto[posicion], 0)
        if nivel == 0:
            return texto[inicio:posicion]
    raise AssertionError(f"bloque sin cerrar: {apertura}")


def _bloque_por_patron(texto, patron):
    """Como ``_bloque``, pero la apertura es una expresión regular que termina en ``{``."""
    encontrado = re.search(patron, texto)
    assert encontrado, f"no se encontró {patron!r}"
    return _bloque(texto[encontrado.start() :], encontrado.group(0))


def _declaraciones(bloque):
    return {nombre: valor.strip() for nombre, valor in DECLARACION.findall(bloque)}


def _capa(css, nombre):
    """Todo lo que la hoja pone en ``@layer <nombre>{…}`` (puede haber varios bloques)."""
    partes, resto = [], css
    while (posicion := resto.find(f"@layer {nombre}{{")) != -1:
        resto = resto[posicion:]
        bloque = _bloque(resto, f"@layer {nombre}{{")
        partes.append(bloque)
        resto = resto[len(bloque) :]
    return "".join(partes)


def _clases(css):
    """Clases nombradas en los selectores (no en las condiciones de ``@media`` ni en valores)."""
    clases = set()
    for selector in re.findall(r"([^{};]+)\{", css):
        if not selector.strip().startswith("@"):
            clases.update(re.findall(r"\.((?:\\.|[\w-])+)", selector))
    return clases


def _hex_largo(color):
    """``#abc`` → ``#aabbcc``; ``#abcd`` → ``#aabbccdd``."""
    cuerpo = color[1:]
    return "#" + ("".join(c * 2 for c in cuerpo) if len(cuerpo) in (3, 4) else cuerpo)


def _rgb_a_hex(encontrado):
    r, g, b, alfa = encontrado.groups()
    canales = [int(r), int(g), int(b)]
    if alfa is not None:
        canales.append(round(float(alfa) * 255))
    return "#" + "".join(f"{c:02x}" for c in canales)


def _normal(valor):
    """Iguala la escritura del Quick Start con la de la hoja minificada sin cambiar el valor."""
    valor = valor.lower().replace("'", "").replace('"', "")
    valor = re.sub(r"rgb\(\s*(\d+)\s+(\d+)\s+(\d+)\s*(?:/\s*([\d.]+))?\s*\)", _rgb_a_hex, valor)
    valor = re.sub(r"#[0-9a-f]{3,8}\b", lambda m: _hex_largo(m.group(0)), valor)
    valor = re.sub(r"(\d*\.?\d+)ms\b", lambda m: f"{float(m.group(1)) / 1000:g}s", valor)
    valor = re.sub(r"(?<![\d.])0(\.\d)", r"\1", valor)
    valor = re.sub(r"(\.\d*?)0+\b", r"\1", valor)
    return re.sub(r"\s*([,/()])\s*", r"\1", " ".join(valor.split()))


def _iguales(esperadas, encontradas):
    faltan = sorted(set(esperadas) - set(encontradas))
    distintas = {
        nombre: (valor, encontradas[nombre])
        for nombre, valor in esperadas.items()
        if nombre in encontradas and _normal(valor) != _normal(encontradas[nombre])
    }
    assert not faltan, f"faltan en la hoja: {faltan}"
    assert not distintas, f"valores distintos del Quick Start: {distintas}"


def _compacta(css):
    """Lleva la salida de ``npm run dev`` (sin minificar) a la forma de ``npm run build``."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)
    return re.sub(r"\s*([{}:;,])\s*", r"\1", css)


@pytest.fixture(scope="module")
def rebrand():
    return _compacta((DIST / "rebrand.css").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def quick_start():
    return _quick_start()


# --- Tokens ----------------------------------------------------------------------------------


def test_tokens_claros_del_quick_start_en_la_capa_theme(rebrand, quick_start):
    esperadas = {
        nombre: valor
        for nombre, valor in _declaraciones(_bloque(quick_start, ":root {")).items()
        if nombre.startswith("--")
    }
    tema = _capa(rebrand, "theme")

    _iguales(esperadas, _declaraciones(_bloque_por_patron(tema, r":root,\s*:host\s*\{")))


def test_tema_oscuro_elegido(rebrand, quick_start):
    esperadas = _declaraciones(_bloque(quick_start, "html[data-theme=dark] {"))

    _iguales(esperadas, _declaraciones(_bloque_por_patron(rebrand, r"html\[data-theme=dark\]\{")))


def test_tema_oscuro_del_sistema_salvo_eleccion_clara(rebrand, quick_start):
    esperadas = _declaraciones(_bloque(quick_start, ":root:not([data-theme=light]) {"))
    media = _bloque_por_patron(rebrand, r"@media\s*\(prefers-color-scheme:\s*dark\)\s*\{")

    _iguales(
        esperadas,
        _declaraciones(_bloque_por_patron(media, r":root:not\(\[data-theme=light\]\)\{")),
    )


def test_variables_de_celular_solo_hasta_699_px(rebrand, quick_start):
    esperadas = _declaraciones(
        _bloque(_bloque(quick_start, "@media (max-width:699px) {"), ":root {")
    )
    media = _bloque_por_patron(rebrand, r"@media\s*\((?:max-width:\s*699px|width\s*<=\s*699px)\)\{")

    _iguales(esperadas, _declaraciones(_bloque_por_patron(media, r":root\{")))


def test_app_css_no_trae_los_tokens_del_rebrand():
    assert "--g-main" not in (DIST / "app.css").read_text(encoding="utf-8")


# --- Fuentes ---------------------------------------------------------------------------------


def test_instrument_sans_400_y_500_en_woff2_con_swap_y_besley_solo_600_optional(rebrand):
    caras = re.findall(r"@font-face\{([^}]*)\}", rebrand)
    instrument = [c for c in caras if "instrument sans" in c.lower()]
    besley = [c for c in caras if "besley" in c.lower()]

    # Besley: una sola cara, para el nombre de la I.E. del inicio de sesión (rebrand-us-001, D5).
    assert len(besley) == 1
    assert re.search(r"font-weight:\s*600", besley[0])
    assert re.search(r"font-display:\s*optional", besley[0])
    assert re.search(r"url\([\"']?fuentes/besley-latin-600-normal\.woff2", besley[0])
    assert sorted(re.search(r"font-weight:\s*(\d+)", c).group(1) for c in instrument) == [
        "400",
        "500",
    ]
    for cara in instrument:
        assert re.search(r"font-display:\s*swap", cara)
        assert re.search(r"url\([\"']?fuentes/instrument-sans-latin-\d00-normal\.woff2", cara)
        assert re.search(r"format\([\"']?woff2", cara)


# --- Movimiento y capas ----------------------------------------------------------------------


def test_ninguna_transicion_de_ancho_ni_alto(rebrand):
    for valor in re.findall(r"transition(?:-property)?:([^;}]*)", rebrand):
        assert not re.search(r"\b(width|height)\b", valor), valor


def test_ninguna_utilidad_repite_una_clase_de_componente(rebrand):
    repetidas = _clases(_capa(rebrand, "utilities")) & _clases(_capa(rebrand, "components"))

    assert not repetidas


# --- Diálogo (rebrand-us-010, D3 y D4) -------------------------------------------------------


def _reglas(css, selector):
    """Cuerpos de las reglas cuyo selector (de una lista con comas) es exactamente ``selector``."""
    cuerpos = []
    for lista, cuerpo in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
        if selector in [parte.strip() for parte in lista.split(",")]:
            cuerpos.append(cuerpo)
    return cuerpos


def _propiedades_de_transicion(cuerpos):
    """Nombres de propiedad que ``transition`` o ``transition-property`` declaran en ``cuerpos``."""
    propiedades = set()
    for cuerpo in cuerpos:
        for valor in re.findall(r"(?:^|;)transition(?:-property)?:([^;]*)", cuerpo):
            for parte in re.split(r",(?![^(]*\))", valor):
                nombre = parte.split()[0] if parte.split() else ""
                if nombre and nombre != "none":
                    propiedades.add(nombre)
    return propiedades


def _medios(css, condicion):
    """Contenido de cada ``@media <condicion>{…}`` de la hoja."""
    return [
        _bloque(css[m.start() :], m.group(0))
        for m in re.finditer(rf"@media\s*\({condicion}\)\s*\{{", css)
    ]


def test_el_dialogo_transiciona_solo_transform_opacity_display_y_overlay(rebrand):
    cuerpos = _reglas(rebrand, ".dialog")

    assert cuerpos, "falta .dialog en la hoja"
    assert _propiedades_de_transicion(cuerpos) == {"transform", "opacity", "display", "overlay"}
    assert "allow-discrete" in "".join(cuerpos)


def test_el_dialogo_y_su_velo_entran_con_starting_style(rebrand):
    estilos = "".join(
        _bloque(rebrand[m.start() :], m.group(0))
        for m in re.finditer(r"@starting-style\s*\{", rebrand)
    )

    assert ".dialog[open]{" in estilos
    assert ".dialog[open]::backdrop{" in estilos


def test_el_velo_del_dialogo_solo_transiciona_opacidad_display_y_overlay(rebrand):
    cuerpos = _reglas(rebrand, ".dialog::backdrop")

    assert cuerpos, "falta .dialog::backdrop en la hoja"
    assert _propiedades_de_transicion(cuerpos) == {"opacity", "display", "overlay"}


def test_con_la_marca_de_teclado_el_dialogo_y_su_velo_no_transicionan(rebrand):
    for selector in ("html[data-teclado] .dialog", "html[data-teclado] .dialog::backdrop"):
        cuerpos = _reglas(rebrand, selector)
        assert cuerpos, f"falta {selector}"
        assert any("transition:none" in c for c in cuerpos), selector


def test_con_movimiento_reducido_el_dialogo_no_se_desplaza(rebrand):
    medios = "".join(_medios(rebrand, "prefers-reduced-motion:reduce"))
    cuerpos = _reglas(medios, ".dialog") + [
        c
        for m in re.finditer(r"@starting-style\s*\{", medios)
        for c in _reglas(_bloque(medios[m.start() :], m.group(0)), ".dialog[open]")
    ]

    assert cuerpos, "falta .dialog dentro de prefers-reduced-motion: reduce"
    assert "transform" not in _propiedades_de_transicion(cuerpos)
    for cuerpo in cuerpos:
        for valor in re.findall(r"(?:^|;)transform:([^;]*)", cuerpo):
            assert valor == "none", valor


def test_ninguna_regla_del_dialogo_anima_ancho_ni_alto(rebrand):
    cuerpos = _reglas(rebrand, ".dialog") + _reglas(rebrand, ".dialog::backdrop")

    assert not _propiedades_de_transicion(cuerpos) & {"width", "height"}


def test_el_alto_del_dialogo_y_de_la_hoja_usa_dvh_no_svh(rebrand):
    """E-02: con ``interactive-widget=resizes-content``, ``dvh`` sigue al teclado; ``svh`` no."""
    for selector in (".dialog", ".dialog--hoja"):
        cuerpos = _reglas(rebrand, selector)
        assert cuerpos, f"falta {selector} en la hoja"
        assert not any("svh" in c for c in cuerpos), selector
        assert any(re.search(r"max-height:[^;]*dvh", c) for c in cuerpos), selector


def test_el_dialogo_de_la_lista_mide_760_sin_svh_ni_transiciones_de_ancho_o_alto(rebrand):
    """rebrand-us-006, D3 y D8: ventana de 760 px de ancho, alto en ``dvh`` y sin animar medidas."""
    cuerpos = _reglas(rebrand, ".dialog--lista")

    assert cuerpos, "falta .dialog--lista en la hoja"
    assert not any("svh" in c for c in cuerpos)
    assert any(re.search(r"width:min\(760px", c) for c in cuerpos)
    assert any(re.search(r"height:[^;]*dvh", c) for c in cuerpos)
    assert not _propiedades_de_transicion(cuerpos) & {"width", "height"}


# --- Cifras tabulares (decisión 4) -----------------------------------------------------------

CIFRAS = """
<p style="font: 400 32px 'Instrument Sans'; font-variant-numeric: {variante}">
  <span id="ceros">0000</span><br><span id="unos">1111</span>
</p>
"""


def _anchos(page, live_server, variante):
    """Ancho de «0000» y «1111» en Instrument Sans 400 con ``rebrand.css`` cargada."""
    page.goto(f"{live_server.url}/static/dist/rebrand.css")
    page.set_content(
        '<link rel="stylesheet" href="/static/dist/rebrand.css">' + CIFRAS.format(variante=variante)
    )
    # Si el WOFF2 no llega, load() rechaza; check() lo dice abajo con un mensaje claro.
    page.evaluate("document.fonts.load(\"400 32px 'Instrument Sans'\").catch(() => [])")
    page.evaluate("document.fonts.ready")
    assert page.evaluate("document.fonts.check(\"400 32px 'Instrument Sans'\")"), (
        "Instrument Sans 400 no cargó: se midió la fuente de respaldo"
    )
    return [
        page.evaluate(f"document.getElementById('{id_}').getBoundingClientRect().width")
        for id_ in ("ceros", "unos")
    ]


def test_cifras_tabulares_de_instrument_sans_miden_lo_mismo(live_server, page):
    ceros, unos = _anchos(page, live_server, "tabular-nums")

    assert ceros == pytest.approx(unos, abs=0.01)


def test_sin_tabular_nums_las_cifras_son_proporcionales(live_server, page):
    """Control de la prueba anterior: la medida distingue cifras proporcionales."""
    ceros, unos = _anchos(page, live_server, "proportional-nums")

    assert ceros != pytest.approx(unos, abs=0.01)
