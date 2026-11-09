"""Marco del rebrand en «sin permiso» (specs pantallas-de-inicio y cierre-sesion; rebrand-base,
D4, D7 y D8).

Comprueba el HTML que sale del servidor, sin JavaScript: hoja única, barra, ☰ (enlace a la portada
y diálogo cerrado), cuenta y pie. La conducta en el navegador está en ``test_marco_rebrand_e2e.py``.
"""

import re
from html import unescape

import pytest
from django.urls import reverse

from institucion.models import AnioEscolar, Seccion

pytestmark = pytest.mark.django_db

URL = "/docente/sin-permiso/"
IE = "I.E. Virgen del Carmen"


@pytest.fixture
def html_de(client):
    def abrir(usuario, url=URL):
        client.force_login(usuario)
        respuesta = client.get(url)
        assert respuesta.status_code == 200
        return unescape(respuesta.content.decode())

    return abrir


@pytest.fixture
def con_seccion(docente, institucion):
    anio = AnioEscolar.objects.create(institucion=institucion, anio=2027)
    return Seccion.objects.create(anio_escolar=anio, grado=2, nombre="A", docente=docente)


def bloque(html, patron):
    encontrado = re.search(patron, html, re.DOTALL)
    assert encontrado, f"no se halló {patron!r}"
    return encontrado.group(0)


def cabecera(html):
    return bloque(html, r"<header\b.*?</header>")


def dialogo(html):
    return bloque(html, r"<dialog\b.*?</dialog>")


def cuenta(html):
    return bloque(html, r"<details\b[^>]*data-menu-cuenta.*?</details>")


def destinos(html):
    """``(texto, href | None)`` de cada destino de la lista del ☰, en orden."""
    nav = bloque(dialogo(html), r"<nav\b.*?</nav>")
    salida = []
    for item in re.findall(r"<li\b.*?</li>", nav, re.DOTALL):
        enlace = re.search(r'<a\b[^>]*href="([^"]+)"', item)
        texto = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", item)).strip()
        salida.append((texto, enlace.group(1) if enlace else None))
    return salida


# --- Hoja única y fuente (D8, D9) ---


def test_carga_solo_la_hoja_del_rebrand_y_precarga_instrument_sans(html_de, docente):
    html = html_de(docente)

    assert "dist/rebrand.css" in html
    assert "dist/app.css" not in html
    assert "besley" not in html.lower()
    for peso in (400, 500):
        assert re.search(
            rf'<link rel="preload" href="[^"]*instrument-sans-latin-{peso}-normal\.woff2"'
            r' as="font" type="font/woff2" crossorigin>',
            html,
        )


# --- Barra (escenario «Barra de una pantalla interior») ---


def test_ir_al_contenido_lleva_al_main(html_de, docente):
    html = html_de(docente)

    assert re.search(r'<a [^>]*href="#contenido"[^>]*>Ir al contenido</a>', html)
    assert '<main id="contenido"' in html


def test_la_barra_lleva_el_menu_el_titulo_y_la_cuenta_en_orden(html_de, docente):
    barra = cabecera(html_de(docente))

    menu = re.search(r"<a\b[^>]*data-menu-navegacion[^>]*>", barra)
    assert menu, "sin JS el ☰ es un enlace"
    assert 'href="/docente/"' in menu.group(0)
    assert 'aria-label="Inicio"' in menu.group(0)
    posiciones = [barra.index("data-menu-navegacion"), barra.index("Sin permiso")]
    posiciones.append(barra.index("data-menu-cuenta"))
    assert posiciones == sorted(posiciones)


def test_la_barra_no_lleva_el_nombre_de_la_ie(html_de, docente):
    barra = cabecera(html_de(docente))

    assert IE not in barra.replace(cuenta(barra), "")


# --- ☰ (requisito «Navegación de la docente»; D4 y D6) ---


def test_el_dialogo_del_menu_va_cerrado_y_con_su_titulo(html_de, docente):
    panel = dialogo(html_de(docente))

    apertura = re.match(r"<dialog\b[^>]*>", panel).group(0)
    assert " open" not in apertura
    assert 'aria-labelledby="navegacion-titulo"' in apertura
    assert re.search(r'id="navegacion-titulo"[^>]*>CarpetaDocente<', panel)
    assert re.search(
        r'<button type="button"[^>]*aria-label="Cerrar navegación"[^>]*data-cerrar', panel
    )
    assert 'aria-label="Navegación principal"' in panel


def test_sin_seccion_unica_solo_inicio_enlaza(html_de, docente):
    """Escenario «Destino no disponible»."""
    assert destinos(html_de(docente)) == [
        ("Inicio", "/docente/"),
        ("Sesiones Próximamente", None),
        ("Asistencia Próximamente", None),
        ("Notas Próximamente", None),
    ]


def test_con_seccion_unica_enlaza_como_las_tarjetas(html_de, docente, con_seccion):
    """Escenario «Abrir el ☰»."""
    assert destinos(html_de(docente)) == [
        ("Inicio", "/docente/"),
        ("Sesiones Próximamente", None),
        ("Asistencia", reverse("asistencia:hoy", args=[con_seccion.pk])),
        ("Notas", reverse("notas:hoja", args=[con_seccion.pk])),
    ]


def test_desde_sin_permiso_ningun_destino_es_el_actual(html_de, docente, con_seccion):
    """Escenario «Ubicación actual»."""
    assert "aria-current" not in dialogo(html_de(docente))


# --- Cuenta (spec cierre-sesion, «Menú de la cuenta»; D7) ---


def test_la_cuenta_va_con_sus_ganchos_y_su_formulario(html_de, docente):
    menu = cuenta(html_de(docente))

    assert '<summary class="btn icon-button" aria-label="Menú de la cuenta">' in menu
    assert "data-cuenta-panel" in menu
    assert re.search(r"data-cuenta-nombre[^>]*>Ana Quispe<", menu)
    assert re.search(rf'<form [^>]*data-salir data-usuario="{docente.pk}"', menu)
    assert 'name="csrfmiddlewaretoken"' in menu
    textos = ["Tu cuenta", "Ana Quispe", IE, "Cerrar sesión"]
    assert [menu.index(t) for t in textos] == sorted(menu.index(t) for t in textos)


def test_la_cuenta_sin_seccion_no_lleva_linea(html_de, docente):
    """Escenario «Docente sin sección»."""
    assert "grado, sección" not in cuenta(html_de(docente))
    assert "Tu sección aparecerá" not in cuenta(html_de(docente))


def test_la_cuenta_con_seccion_la_muestra_bajo_la_ie(html_de, docente, con_seccion):
    """Escenario «Docente con sección»."""
    menu = cuenta(html_de(docente))

    assert menu.index(IE) < menu.index("2.º grado, sección A") < menu.index("Cerrar sesión")


def test_la_cuenta_sin_nombre_muestra_el_usuario(html_de, docente):
    docente.first_name = docente.last_name = ""
    docente.save()

    assert re.search(r"data-cuenta-nombre[^>]*>ana\.quispe<", cuenta(html_de(docente)))


def test_el_menu_viejo_tambien_lleva_los_ganchos(html_de, docente):
    menu = cuenta(html_de(docente, "/docente/"))

    assert "data-cuenta-panel" in menu
    assert re.search(r"data-cuenta-nombre[^>]*>Ana Quispe<", menu)


# --- Pie (escenario «Pie») ---


def test_el_pie_va_despues_del_main_con_sus_dos_textos(html_de, docente):
    html = html_de(docente)

    pie = bloque(html, r"<footer\b.*?</footer>")
    assert html.index("</main>") < html.index(pie)
    assert pie.index("CarpetaDocente · 2026") < pie.index(IE)
