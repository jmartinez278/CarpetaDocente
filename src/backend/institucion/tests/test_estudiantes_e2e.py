"""Diálogo de la lista de estudiantes en el navegador (spec estudiantes-seccion; US-006, D6 y D10).

Abrir con "Ver estudiantes", cerrar con Esc y "Cerrar" (el foco vuelve al enlace), Atrás que cierra
el diálogo, axe de la portada y de la lista vacía en ambos temas a 360 y 1280 px, y 320 px sin
desplazamiento horizontal.
Necesita el CSS compilado y Chromium: ``uv run pytest -m e2e --browser chromium``.
"""

import re

import pytest
from playwright.sync_api import expect

from actividad.tests.intentos import SIN_PERMISO, motivos, pasar_a_otra_docente
from cuentas.tests.e2e import (
    ANCHOS,
    TEMAS,
    con_pantalla,
    envejecer_sesion,
    ingresar,
    revisar_con_axe,
    saludo_de,
)

pytestmark = pytest.mark.e2e

TITULO = "Estudiantes de 2.º A"


@pytest.fixture
def docente_con_seccion(seccion, docente):
    seccion.docente = docente
    seccion.save()
    return docente


@pytest.fixture
def portada(live_server, page, docente_con_seccion, clave):
    ingresar(page, live_server, docente_con_seccion, clave)
    expect(page).to_have_url(f"{live_server.url}/docente/")
    return page


def ver_estudiantes(page):
    return page.get_by_role("link", name="Ver estudiantes")


def dialogo(page):
    return page.get_by_role("dialog", name=TITULO)


def abrir(page):
    # Recién ingresada, la portada puede no tener HTMX aún: el clic abriría la página completa.
    page.wait_for_url("**/docente/")
    ver_estudiantes(page).click()
    expect(dialogo(page)).to_be_visible()


def test_ver_estudiantes_abre_el_dialogo_sin_cambiar_la_direccion(live_server, portada):
    abrir(portada)

    expect(portada.get_by_role("heading", name=TITULO)).to_be_visible()
    expect(dialogo(portada)).to_contain_text("0 estudiantes")
    expect(dialogo(portada)).to_contain_text("Tu sección aún no tiene estudiantes.")
    expect(dialogo(portada).get_by_role("link", name="Agregar uno por uno")).to_be_visible()
    expect(dialogo(portada).get_by_role("link", name="Pegar lista")).to_be_visible()
    expect(portada).to_have_url(f"{live_server.url}/docente/")


def test_el_foco_entra_al_titulo_del_dialogo(portada):
    abrir(portada)

    expect(portada.locator("#modal-titulo")).to_be_focused()


def test_esc_cierra_el_dialogo_y_el_foco_vuelve_al_enlace(portada):
    abrir(portada)

    portada.keyboard.press("Escape")

    expect(dialogo(portada)).to_be_hidden()
    expect(ver_estudiantes(portada)).to_be_focused()


def test_cerrar_cierra_el_dialogo_y_el_foco_vuelve_al_enlace(portada):
    abrir(portada)

    dialogo(portada).get_by_role("button", name="Cerrar").click()

    expect(dialogo(portada)).to_be_hidden()
    expect(ver_estudiantes(portada)).to_be_focused()


def test_atras_cierra_el_dialogo_y_la_portada_sigue(live_server, portada):
    abrir(portada)

    portada.go_back()

    expect(dialogo(portada)).to_be_hidden()
    expect(portada).to_have_url(f"{live_server.url}/docente/")
    expect(portada.get_by_role("heading", name=saludo_de("Ana Quispe"))).to_be_visible()


def test_cerrar_consume_la_entrada_del_historial_y_se_puede_volver_a_abrir(portada):
    assert portada.evaluate("history.state") is None
    abrir(portada)
    assert portada.evaluate("history.state") == {"estudiantes": True}

    portada.keyboard.press("Escape")
    expect(dialogo(portada)).to_be_hidden()
    portada.wait_for_function("history.state === null")

    abrir(portada)
    portada.get_by_role("button", name="Cerrar").click()
    expect(dialogo(portada)).to_be_hidden()
    portada.wait_for_function("history.state === null")


def test_el_dialogo_deja_la_portada_inerte_y_sin_desplazamiento(portada):
    abrir(portada)

    assert portada.evaluate("document.body.classList.contains('con-dialogo')")
    assert portada.evaluate("getComputedStyle(document.body).overflow") == "hidden"
    portada.keyboard.press("Escape")
    expect(portada.locator("body")).not_to_have_class(re.compile("con-dialogo"))


@pytest.mark.parametrize("tema", TEMAS)
@pytest.mark.parametrize("ancho", ANCHOS)
def test_la_portada_con_el_aviso_pasa_axe(
    live_server, page, docente_con_seccion, clave, ancho, tema
):
    con_pantalla(page, ancho, tema)
    ingresar(page, live_server, docente_con_seccion, clave)
    expect(page.locator("#aviso-portada")).to_contain_text("Tu sección aún no tiene estudiantes")

    revisar_con_axe(page, f"portada-aviso-{ancho}-{tema}")


@pytest.mark.parametrize("tema", TEMAS)
@pytest.mark.parametrize("ancho", ANCHOS)
def test_la_lista_vacia_en_el_dialogo_pasa_axe(
    live_server, page, docente_con_seccion, clave, ancho, tema
):
    con_pantalla(page, ancho, tema)
    ingresar(page, live_server, docente_con_seccion, clave)
    abrir(page)

    revisar_con_axe(page, f"lista-vacia-dialogo-{ancho}-{tema}")


@pytest.mark.parametrize("tema", TEMAS)
@pytest.mark.parametrize("ancho", ANCHOS)
def test_la_lista_vacia_como_pagina_completa_pasa_axe(
    live_server, page, docente_con_seccion, seccion, clave, ancho, tema
):
    con_pantalla(page, ancho, tema)
    ingresar(page, live_server, docente_con_seccion, clave)
    page.goto(f"{live_server.url}/docente/secciones/{seccion.pk}/estudiantes/")
    expect(page.get_by_role("heading", level=1, name=TITULO)).to_be_visible()

    revisar_con_axe(page, f"lista-vacia-pagina-{ancho}-{tema}")


@pytest.mark.parametrize("tema", TEMAS)
@pytest.mark.parametrize("ancho", [320, 360, 1280])
def test_la_portada_y_la_lista_vacia_no_se_desplazan_en_horizontal(
    live_server, page, docente_con_seccion, seccion, clave, ancho, tema
):
    con_pantalla(page, ancho, tema)
    ingresar(page, live_server, docente_con_seccion, clave)
    page.evaluate("document.fonts.ready")
    assert page.evaluate("document.documentElement.scrollWidth") <= ancho

    page.goto(f"{live_server.url}/docente/secciones/{seccion.pk}/estudiantes/")
    page.evaluate("document.fonts.ready")
    assert page.evaluate("document.documentElement.scrollWidth") <= ancho


# --- Foco del título y desplazamiento de la página de atrás ---


def contorno(page, selector):
    return page.evaluate(
        """(selector) => {
            const estilo = getComputedStyle(document.querySelector(selector));
            return { estilo: estilo.outlineStyle, ancho: estilo.outlineWidth };
        }""",
        selector,
    )


@pytest.mark.parametrize("tema", TEMAS)
def test_el_titulo_recibe_el_foco_sin_contorno_y_los_controles_si(portada, tema):
    portada.emulate_media(color_scheme=tema)
    abrir(portada)

    expect(portada.locator("#modal-titulo")).to_be_focused()
    assert portada.evaluate("document.getElementById('modal-titulo').tabIndex") == -1
    assert contorno(portada, "#modal-titulo")["estilo"] == "none"

    portada.keyboard.press("Tab")
    expect(dialogo(portada).get_by_role("button", name="Cerrar")).to_be_focused()
    assert contorno(portada, "#estudiantes [data-cerrar]") == {"estilo": "solid", "ancho": "2px"}

    # Desde rebrand-us-006 el cuerpo es una región enfocable que se desplaza con el teclado.
    portada.keyboard.press("Tab")
    expect(portada.locator("#modal-cuerpo")).to_be_focused()
    assert contorno(portada, "#modal-cuerpo")["ancho"] == "2px"

    portada.keyboard.press("Tab")
    expect(dialogo(portada).get_by_role("link", name="Agregar uno por uno")).to_be_focused()
    assert contorno(portada, "#estudiantes .btn--primary")["ancho"] == "2px"


@pytest.mark.parametrize("tema", TEMAS)
@pytest.mark.parametrize("ancho", ANCHOS)
def test_la_portada_con_el_aviso_carga_empezando_arriba(
    live_server, page, docente_con_seccion, clave, ancho, tema
):
    con_pantalla(page, ancho, tema)
    ingresar(page, live_server, docente_con_seccion, clave)
    expect(page.locator("#aviso-portada")).to_be_visible()
    page.evaluate("document.fonts.ready")
    page.wait_for_timeout(300)
    assert page.evaluate("window.scrollY") == 0

    page.goto(f"{live_server.url}/docente/")
    page.wait_for_timeout(300)
    assert page.evaluate("window.scrollY") == 0


@pytest.mark.parametrize("tema", TEMAS)
def test_cerrar_es_un_boton_con_borde_de_44_px_con_icono_y_texto(portada, tema):
    portada.emulate_media(color_scheme=tema)
    abrir(portada)

    cerrar = dialogo(portada).get_by_role("button", name="Cerrar")
    estilo = cerrar.evaluate(
        """(el) => {
            const e = getComputedStyle(el), secundario = document.createElement("a");
            secundario.className = "btn btn--secondary";
            document.body.append(secundario);
            const s = getComputedStyle(secundario);
            const datos = {
                alto: el.getBoundingClientRect().height,
                borde: e.borderTopWidth + " " + e.borderTopStyle,
                color: e.borderTopColor,
                colorSecundario: s.borderTopColor,
                radio: e.borderTopLeftRadius,
                radioSecundario: s.borderTopLeftRadius,
                icono: !!el.querySelector("svg.icono"),
            };
            secundario.remove();
            return datos;
        }"""
    )
    assert estilo["alto"] >= 44
    assert estilo["borde"] == "1px solid"
    assert estilo["color"] == estilo["colorSecundario"]
    assert estilo["radio"] == estilo["radioSecundario"]
    assert estilo["icono"]
    expect(cerrar).to_have_text("Cerrar")


# --- Pegar lista y Revisar lista (spec "Pegar lista", sus errores y la sesión vencida) ---

# Los 25 nombres ficticios del boceto.
NOMBRES = [
    "AGUILAR FLORES, LUCIANA",
    "ALARCÓN HUAMÁN, DIEGO ALONSO",
    "ALVARADO ROJAS, MARÍA FERNANDA",
    "CÁRDENAS QUISPE, JOSÉ LUIS",
    "CASTILLO HUAMÁN, CAMILA",
    "CHÁVEZ CONDORI, MATEO",
    "CONDORI MAMANI, DANIELA",
    "CRUZ HUAMÁN, SEBASTIÁN",
    "FLORES SALAZAR, VALERIA",
    "GARCÍA ROJAS, ADRIÁN",
    "GÓMEZ TORRES, ANTONELLA",
    "GONZALES RAMOS, BRUNO",
    "GUTIÉRREZ SOTO, THIAGO",
    "HUAMÁN QUISPE, SOFÍA",
    "MAMANI ROJAS, PAOLA",
    "MEDINA CASTRO, GABRIEL",
    "MENDOZA DÍAZ, LUCAS",
    "QUISPE MAMANI, ANA LUCÍA",
    "RAMÍREZ FLORES, LUIS MIGUEL",
    "RAMOS HUAMÁN, VALENTÍN",
    "ROJAS MEDINA, ISABELLA",
    "SALAZAR QUISPE, EMILIA",
    "SÁNCHEZ VARGAS, JOSÉ ANTONIO",
    "TORRES PAREDES, ALEJANDRA",
    "VARGAS GUTIÉRREZ, SANTIAGO",
]
# Las filas copiadas de una hoja de cálculo, con líneas en blanco en medio y al final.
LISTA_25 = "\n".join(NOMBRES[:10]) + "\n\n" + "\n".join(NOMBRES[10:]) + "\n\n"
LISTA_CON_ERRORES = (
    "AGUILAR FLORES, LUCIANA\n, MATEO\nCRUZ HUAMÁN, SEBASTIÁN\nCRUZ HUAMÁN, SEBASTIÁN"
)


def cuadro(page):
    return dialogo(page).get_by_label("Apellidos y nombres")


def abrir_pegar(page):
    abrir(page)
    dialogo(page).get_by_role("link", name="Pegar lista").click()
    expect(cuadro(page)).to_be_focused()


def importar(page, texto):
    cuadro(page).fill(texto)
    dialogo(page).get_by_role("button", name="Importar").click()


def test_camino_ideal_importa_los_25_con_lineas_en_blanco(live_server, portada, seccion):
    abrir_pegar(portada)

    importar(portada, LISTA_25)

    expect(dialogo(portada)).to_contain_text("25 estudiantes importados")
    expect(dialogo(portada)).to_contain_text("Revisa los nombres; puedes corregirlos con Editar")
    expect(portada.locator("#modal-cantidad")).to_have_text("25 estudiantes")
    expect(portada).to_have_url(f"{live_server.url}/docente/")
    assert seccion.estudiantes.count() == 25


def test_caso_de_error_no_guarda_nada_y_conserva_el_texto(portada, seccion):
    abrir_pegar(portada)

    importar(portada, LISTA_CON_ERRORES)

    expect(dialogo(portada).get_by_role("alert")).to_contain_text("No se guardó ningún estudiante")
    expect(dialogo(portada)).to_contain_text("Línea 2: faltan los apellidos")
    expect(dialogo(portada)).to_contain_text("Líneas 3 y 4: el mismo estudiante")
    expect(cuadro(portada)).to_have_value(LISTA_CON_ERRORES)
    expect(cuadro(portada)).to_have_attribute("aria-invalid", "true")
    expect(portada.locator(".vista-titulo")).to_be_focused()
    expect(portada.locator("#modal-cantidad")).to_have_text("0 estudiantes")
    assert seccion.estudiantes.count() == 0


def test_sesion_vencida_al_importar_lleva_la_pagina_a_ingresar(live_server, portada, seccion):
    abrir_pegar(portada)
    cuadro(portada).fill(LISTA_25)
    envejecer_sesion(portada, 61)

    dialogo(portada).get_by_role("button", name="Importar").click()

    expect(portada).to_have_url(re.compile(r"/ingresar/\?next=/docente/"))
    expect(portada.locator(".message--aviso")).to_contain_text(
        "Tu sesión se cerró por inactividad."
    )
    expect(portada.locator("dialog")).to_have_count(0)
    assert seccion.estudiantes.count() == 0


def esperar_animaciones(page):
    # axe mide el color calculado: a media animación de entrada lo mezcla con la opacidad.
    page.wait_for_function("document.getAnimations().length === 0")


@pytest.mark.parametrize("tema", TEMAS)
@pytest.mark.parametrize("ancho", ANCHOS)
def test_pegar_y_revisar_lista_pasan_axe(
    live_server, page, docente_con_seccion, clave, ancho, tema
):
    con_pantalla(page, ancho, tema)
    ingresar(page, live_server, docente_con_seccion, clave)
    abrir_pegar(page)
    revisar_con_axe(page, f"pegar-lista-{ancho}-{tema}")

    importar(page, LISTA_CON_ERRORES)
    expect(dialogo(page).get_by_role("alert")).to_be_visible()
    esperar_animaciones(page)
    revisar_con_axe(page, f"revisar-lista-{ancho}-{tema}")
    assert page.evaluate("document.getElementById('estudiantes').scrollWidth") <= ancho


def test_tras_importar_y_cerrar_la_portada_ya_no_muestra_el_aviso(portada):
    expect(portada.locator("#aviso-portada")).to_contain_text("Tu sección aún no tiene estudiantes")
    portada.evaluate("window.sinRecargar = true")
    abrir_pegar(portada)
    importar(portada, LISTA_25)
    expect(dialogo(portada)).to_contain_text("25 estudiantes importados")

    dialogo(portada).get_by_role("button", name="Cerrar").click()

    expect(dialogo(portada)).to_be_hidden()
    expect(portada.locator("#aviso-portada")).to_be_empty()
    assert portada.evaluate("window.sinRecargar") is True


# --- Lista con estudiantes (spec "Lista de la sección" y "Nombre largo a 320 px") ---


@pytest.fixture
def con_25(seccion):
    from institucion.models import Estudiante

    for nombre in NOMBRES:
        apellidos, nombres = nombre.split(", ")
        Estudiante.objects.create(seccion=seccion, apellidos=apellidos, nombres=nombres)


@pytest.mark.parametrize("ancho", [320, 360])
def test_un_nombre_de_120_mas_120_se_lee_completo_en_el_dialogo(
    live_server, page, docente_con_seccion, seccion, clave, ancho
):
    from institucion.models import Estudiante

    apellidos, nombres = ("HUAMÁN " * 18)[:120], ("MARÍA " * 21)[:119] + "A"
    assert (len(apellidos), len(nombres)) == (120, 120)
    Estudiante.objects.create(seccion=seccion, apellidos=apellidos, nombres=nombres)
    con_pantalla(page, ancho, "light")
    ingresar(page, live_server, docente_con_seccion, clave)

    abrir(page)

    nombre = dialogo(page).locator(".estudiante-nombre")
    expect(nombre).to_have_text(f"{apellidos}, {nombres}")
    assert nombre.evaluate("(el) => el.scrollWidth <= el.clientWidth")
    assert nombre.evaluate("(el) => getComputedStyle(el).textOverflow") != "ellipsis"
    assert page.evaluate("document.getElementById('estudiantes').scrollWidth") <= ancho
    page.goto(f"{live_server.url}/docente/secciones/{seccion.pk}/estudiantes/")
    assert page.evaluate("document.documentElement.scrollWidth") <= ancho


@pytest.mark.parametrize("tema", TEMAS)
@pytest.mark.parametrize("ancho", ANCHOS)
def test_la_lista_con_estudiantes_pasa_axe(
    live_server, page, docente_con_seccion, clave, ancho, tema
):
    con_pantalla(page, ancho, tema)
    ingresar(page, live_server, docente_con_seccion, clave)
    abrir_pegar(page)
    importar(page, LISTA_25)
    expect(dialogo(page).get_by_role("status")).to_contain_text("25 estudiantes importados")
    esperar_animaciones(page)

    revisar_con_axe(page, f"lista-dialogo-{ancho}-{tema}")
    assert page.evaluate("document.getElementById('estudiantes').scrollWidth") <= ancho


@pytest.mark.parametrize("tema", TEMAS)
@pytest.mark.parametrize("ancho", ANCHOS)
def test_la_lista_como_pagina_completa_pasa_axe(
    live_server, page, docente_con_seccion, seccion, con_25, clave, ancho, tema
):
    con_pantalla(page, ancho, tema)
    ingresar(page, live_server, docente_con_seccion, clave)
    page.goto(f"{live_server.url}/docente/secciones/{seccion.pk}/estudiantes/")
    expect(page.get_by_role("link", name="Editar a AGUILAR FLORES, LUCIANA")).to_be_visible()

    revisar_con_axe(page, f"lista-pagina-{ancho}-{tema}")
    assert page.evaluate("document.documentElement.scrollWidth") <= ancho


@pytest.mark.parametrize("tema", TEMAS)
@pytest.mark.parametrize("ancho", ANCHOS)
def test_revisar_lista_como_pagina_completa_pasa_axe(
    live_server, page, docente_con_seccion, seccion, clave, ancho, tema
):
    con_pantalla(page, ancho, tema)
    ingresar(page, live_server, docente_con_seccion, clave)
    page.goto(f"{live_server.url}/docente/secciones/{seccion.pk}/estudiantes/pegar/")
    page.get_by_label("Apellidos y nombres").fill(LISTA_CON_ERRORES)
    page.get_by_role("button", name="Importar").click()
    expect(page.get_by_role("alert")).to_be_visible()
    esperar_animaciones(page)

    revisar_con_axe(page, f"revisar-lista-pagina-{ancho}-{tema}")
    assert page.evaluate("document.documentElement.scrollWidth") <= ancho


# --- Agregar y Editar (spec "Agregar un estudiante" y "Editar un estudiante") ---


def campo(page, etiqueta):
    return dialogo(page).get_by_label(etiqueta, exact=True)


def test_flujo_alternativo_valido_agrega_y_la_cabecera_pasa_a_26(portada, con_25, seccion):
    abrir(portada)
    expect(portada.locator("#modal-cantidad")).to_have_text("25 estudiantes")
    dialogo(portada).get_by_role("link", name="Agregar estudiante").click()
    expect(campo(portada, "Apellidos")).to_be_focused()

    campo(portada, "Apellidos").fill("aguirre huamán")
    campo(portada, "Nombres").fill("lucía")
    dialogo(portada).get_by_role("button", name="Guardar y agregar otro").click()

    expect(dialogo(portada).get_by_role("status")).to_contain_text("Estudiante agregado")
    expect(portada.locator("#modal-cantidad")).to_have_text("26 estudiantes")
    expect(campo(portada, "Apellidos")).to_be_focused()
    expect(campo(portada, "Apellidos")).to_have_value("")
    expect(campo(portada, "Nombres")).to_have_value("")
    assert seccion.estudiantes.filter(apellidos="AGUIRRE HUAMÁN", nombres="LUCÍA").exists()


def test_corregir_un_nombre_vuelve_a_la_lista_con_el_nombre_corregido(portada, seccion):
    from institucion.models import Estudiante

    Estudiante.objects.create(seccion=seccion, apellidos="QUISPE MAMANI", nombres="ANA LUCIA")
    abrir(portada)
    dialogo(portada).get_by_role("link", name="Editar a QUISPE MAMANI, ANA LUCIA").click()
    expect(campo(portada, "Apellidos")).to_be_focused()

    campo(portada, "Nombres").fill("ana lucía")
    dialogo(portada).get_by_role("button", name="Guardar cambios").click()

    expect(dialogo(portada).locator(".estudiante-nombre")).to_have_text("QUISPE MAMANI, ANA LUCÍA")
    expect(portada.locator("#modal-titulo")).to_be_focused()


@pytest.mark.parametrize("tema", TEMAS)
@pytest.mark.parametrize("ancho", ANCHOS)
def test_agregar_y_editar_pasan_axe(
    live_server, page, docente_con_seccion, con_25, clave, ancho, tema
):
    con_pantalla(page, ancho, tema)
    ingresar(page, live_server, docente_con_seccion, clave)
    abrir(page)
    dialogo(page).get_by_role("link", name="Agregar estudiante").click()
    expect(campo(page, "Apellidos")).to_be_focused()
    revisar_con_axe(page, f"agregar-{ancho}-{tema}")

    campo(page, "Apellidos").fill("AGUIRRE HUAMÁN")
    dialogo(page).get_by_role("button", name="Guardar y agregar otro").click()
    expect(campo(page, "Nombres")).to_have_attribute("aria-invalid", "true")
    revisar_con_axe(page, f"agregar-error-{ancho}-{tema}")

    campo(page, "Nombres").fill("LUCÍA")
    dialogo(page).get_by_role("button", name="Guardar y agregar otro").click()
    expect(dialogo(page).get_by_role("status")).to_contain_text("Estudiante agregado")
    esperar_animaciones(page)
    revisar_con_axe(page, f"agregar-exito-{ancho}-{tema}")

    dialogo(page).get_by_role("link", name="Volver a la lista").click()
    dialogo(page).get_by_role("link", name="Editar a AGUILAR FLORES, LUCIANA").click()
    expect(campo(page, "Apellidos")).to_be_focused()
    revisar_con_axe(page, f"editar-{ancho}-{tema}")
    assert page.evaluate("document.getElementById('estudiantes').scrollWidth") <= ancho


@pytest.mark.parametrize("tema", TEMAS)
@pytest.mark.parametrize("ancho", ANCHOS)
def test_agregar_con_homonimo_como_pagina_completa_pasa_axe(
    live_server, page, docente_con_seccion, seccion, con_25, clave, ancho, tema
):
    con_pantalla(page, ancho, tema)
    ingresar(page, live_server, docente_con_seccion, clave)
    page.goto(f"{live_server.url}/docente/secciones/{seccion.pk}/estudiantes/agregar/")
    page.get_by_label("Apellidos", exact=True).fill("aguilar flores")
    page.get_by_label("Nombres", exact=True).fill("luciana")
    page.get_by_role("button", name="Guardar y agregar otro").click()
    expect(page.get_by_role("alert")).to_contain_text("Este estudiante ya está en la lista")
    esperar_animaciones(page)

    revisar_con_axe(page, f"agregar-homonimo-pagina-{ancho}-{tema}")
    assert page.evaluate("document.documentElement.scrollWidth") <= ancho


# --- Quitar, vaciar y sus bloqueos (spec "Quitar y vaciar" y "Sin JavaScript") ---


def test_quitar_uno_baja_la_cabecera_en_uno(portada, con_25, seccion):
    abrir(portada)
    dialogo(portada).get_by_role("link", name="Editar a QUISPE MAMANI, ANA LUCÍA").click()
    dialogo(portada).get_by_role("link", name="Quitar estudiante").click()
    expect(dialogo(portada)).to_contain_text("¿Quitar a QUISPE MAMANI, ANA LUCÍA?")
    expect(portada.locator(".vista-titulo")).to_be_focused()

    dialogo(portada).get_by_role("button", name="Quitar estudiante").click()

    expect(portada.locator("#modal-cantidad")).to_have_text("24 estudiantes")
    expect(dialogo(portada)).not_to_contain_text("QUISPE MAMANI, ANA LUCÍA")
    assert seccion.estudiantes.count() == 24


def test_vaciar_25_deja_la_lista_vacia_y_el_aviso_vuelve_a_la_portada(portada, con_25, seccion):
    portada.reload()
    expect(portada.locator("#aviso-portada")).to_be_empty()
    abrir(portada)
    dialogo(portada).get_by_role("link", name="Vaciar lista").click()
    expect(dialogo(portada)).to_contain_text("Se quitarán los 25 estudiantes.")

    dialogo(portada).get_by_role("button", name="Vaciar lista").click()

    expect(dialogo(portada)).to_contain_text("Tu sección aún no tiene estudiantes.")
    expect(portada.locator("#modal-cantidad")).to_have_text("0 estudiantes")
    dialogo(portada).get_by_role("button", name="Cerrar").click()
    expect(portada.locator("#aviso-portada")).to_contain_text("Tu sección aún no tiene estudiantes")
    assert seccion.estudiantes.count() == 0


def test_sin_javascript_todo_funciona_como_pagina_completa(
    live_server, browser, docente_con_seccion, seccion, clave
):
    contexto = browser.new_context(java_script_enabled=False)
    page = contexto.new_page()
    try:
        ingresar(page, live_server, docente_con_seccion, clave)
        ver_estudiantes(page).click()
        expect(page.get_by_role("heading", level=1, name=TITULO)).to_be_visible()

        page.get_by_role("link", name="Pegar lista").click()
        page.get_by_label("Apellidos y nombres").fill("\n".join(NOMBRES[:3]))
        page.get_by_role("button", name="Importar").click()
        expect(page.get_by_role("status")).to_contain_text("3 estudiantes importados")

        page.get_by_role("link", name="Agregar estudiante").click()
        page.get_by_label("Apellidos", exact=True).fill("quispe mamani")
        page.get_by_label("Nombres", exact=True).fill("ana lucia")
        page.get_by_role("button", name="Guardar y agregar otro").click()
        expect(page.get_by_role("status")).to_contain_text("Estudiante agregado")
        expect(page.locator("#modal-cantidad")).to_have_text("4 estudiantes")

        page.get_by_role("link", name="Volver a la lista").click()
        page.get_by_role("link", name="Editar a QUISPE MAMANI, ANA LUCIA").click()
        page.get_by_label("Nombres", exact=True).fill("ana lucía")
        page.get_by_role("button", name="Guardar cambios").click()
        expect(page.locator(".estudiantes-lista")).to_contain_text("QUISPE MAMANI, ANA LUCÍA")

        page.get_by_role("link", name="Editar a QUISPE MAMANI, ANA LUCÍA").click()
        page.get_by_role("link", name="Quitar estudiante").click()
        page.get_by_role("button", name="Quitar estudiante").click()
        expect(page.locator("#modal-cantidad")).to_have_text("3 estudiantes")

        page.get_by_role("link", name="Vaciar lista").click()
        page.get_by_role("button", name="Vaciar lista").click()
        expect(page.get_by_text("Tu sección aún no tiene estudiantes.")).to_be_visible()
        expect(page.get_by_role("heading", level=1, name=TITULO)).to_be_visible()
        assert seccion.estudiantes.count() == 0
    finally:
        contexto.close()


@pytest.mark.parametrize("tema", TEMAS)
@pytest.mark.parametrize("ancho", ANCHOS)
def test_quitar_vaciar_y_los_bloqueos_pasan_axe(
    live_server, page, docente_con_seccion, con_25, borrado_con_registros, clave, ancho, tema
):
    con_pantalla(page, ancho, tema)
    ingresar(page, live_server, docente_con_seccion, clave)
    abrir(page)
    dialogo(page).get_by_role("link", name="Editar a AGUILAR FLORES, LUCIANA").click()
    dialogo(page).get_by_role("link", name="Quitar estudiante").click()
    expect(page.locator(".vista-titulo")).to_be_focused()
    revisar_con_axe(page, f"quitar-{ancho}-{tema}")

    dialogo(page).get_by_role("button", name="Quitar estudiante").click()
    expect(dialogo(page).get_by_role("alert")).to_contain_text("No se puede quitar")
    esperar_animaciones(page)
    revisar_con_axe(page, f"quitar-bloqueo-{ancho}-{tema}")

    dialogo(page).get_by_role("link", name="Volver a la lista").click()
    dialogo(page).get_by_role("link", name="Vaciar lista").click()
    expect(dialogo(page)).to_contain_text("Se quitarán los 25 estudiantes.")
    esperar_animaciones(page)
    revisar_con_axe(page, f"vaciar-{ancho}-{tema}")

    dialogo(page).get_by_role("button", name="Vaciar lista").click()
    expect(dialogo(page).get_by_role("alert")).to_contain_text("No se puede vaciar")
    expect(dialogo(page).get_by_role("button")).to_have_count(1)  # solo "Cerrar"
    esperar_animaciones(page)
    revisar_con_axe(page, f"vaciar-bloqueo-{ancho}-{tema}")
    assert page.evaluate("document.getElementById('estudiantes').scrollWidth") <= ancho


# --- Paso siguiente tras importar (US-030; spec "Pegar lista", "Paso siguiente tras importar") ---


def tomar_asistencia(page):
    return dialogo(page).get_by_role("link", name="Tomar la asistencia de hoy")


def test_tomar_la_asistencia_abre_la_asistencia_como_pagina_completa(live_server, portada, seccion):
    abrir_pegar(portada)
    importar(portada, LISTA_25)
    expect(dialogo(portada)).to_contain_text("25 estudiantes importados")

    tomar_asistencia(portada).click()

    expect(portada).to_have_url(f"{live_server.url}/docente/secciones/{seccion.pk}/asistencia/")
    expect(portada.get_by_role("heading", level=1)).to_have_text("Asistencia de hoy")
    expect(portada.locator("dialog#estudiantes")).to_have_count(0)


@pytest.mark.parametrize("tema", TEMAS)
@pytest.mark.parametrize("ancho", ANCHOS)
def test_la_lista_con_el_aviso_de_importados_pasa_axe(
    live_server, page, docente_con_seccion, clave, ancho, tema
):
    con_pantalla(page, ancho, tema)
    ingresar(page, live_server, docente_con_seccion, clave)
    abrir_pegar(page)
    importar(page, LISTA_25)
    expect(tomar_asistencia(page)).to_be_visible()
    esperar_animaciones(page)

    revisar_con_axe(page, f"lista-importados-{ancho}-{tema}")


def test_a_320_la_lista_con_el_aviso_no_se_desplaza_en_horizontal(
    live_server, page, docente_con_seccion, clave
):
    con_pantalla(page, 320, "light")
    ingresar(page, live_server, docente_con_seccion, clave)
    abrir_pegar(page)
    importar(page, LISTA_25)
    expect(tomar_asistencia(page)).to_be_visible()

    assert page.evaluate("document.getElementById('estudiantes').scrollWidth") <= 320
    assert page.evaluate("document.documentElement.scrollWidth") <= 320


# --- US-004: la sección deja de ser de la docente con el diálogo abierto ---


def test_agregar_en_una_seccion_que_ya_no_es_suya_lleva_a_sin_permiso(
    portada, con_25, seccion, otra_docente
):
    """Escenario "Diálogo de la portada": la pestaña pasa a la página completa, sin pintar nada en
    el diálogo, y queda una sola entrada."""
    abrir(portada)
    dialogo(portada).get_by_role("link", name="Agregar estudiante").click()
    campo(portada, "Apellidos").fill("aguirre huamán")
    campo(portada, "Nombres").fill("lucía")
    pasar_a_otra_docente(seccion, otra_docente)

    dialogo(portada).get_by_role("button", name="Guardar y agregar otro").click()

    portada.wait_for_url(re.compile(r"/docente/sin-permiso/$"))
    expect(portada.get_by_role("heading", name=SIN_PERMISO)).to_be_visible()
    # «Sin permiso» ya va en el marco del rebrand, que trae el <dialog> del ☰ (rebrand-base, D4).
    expect(portada.locator("dialog:not(#navegacion)")).to_have_count(0)
    assert seccion.estudiantes.count() == 25
    assert motivos() == ["ajena"]


# --- Cada vista como página completa, en el marco del rebrand (rebrand-us-006, D8) ---


def ir_a(page, live_server, seccion, usuario, clave, ancho, tema, final=""):
    """Ingresa y abre una dirección de la lista como página completa (☰ y cuenta cerrados)."""
    con_pantalla(page, ancho, tema)
    ingresar(page, live_server, usuario, clave)
    page.wait_for_url("**/docente/")
    page.goto(f"{live_server.url}/docente/secciones/{seccion.pk}/estudiantes/{final}")
    page.evaluate("document.fonts.ready")


def sin_desplazamiento(page, ancho):
    assert page.evaluate("document.documentElement.scrollWidth") <= ancho


@pytest.mark.parametrize("tema", TEMAS)
@pytest.mark.parametrize("ancho", ANCHOS)
def test_pegar_lista_como_pagina_completa_pasa_axe(
    live_server, page, docente_con_seccion, seccion, clave, ancho, tema
):
    ir_a(page, live_server, seccion, docente_con_seccion, clave, ancho, tema, "pegar/")
    expect(page.get_by_label("Apellidos y nombres")).to_be_visible()
    expect(page.locator(".bar-title")).to_have_text("Estudiantes")

    revisar_con_axe(page, f"pegar-pagina-{ancho}-{tema}")
    sin_desplazamiento(page, ancho)


@pytest.mark.parametrize("tema", TEMAS)
@pytest.mark.parametrize("ancho", ANCHOS)
def test_la_lista_con_el_aviso_de_importados_como_pagina_completa_pasa_axe(
    live_server, page, docente_con_seccion, seccion, clave, ancho, tema
):
    ir_a(page, live_server, seccion, docente_con_seccion, clave, ancho, tema, "pegar/")
    page.get_by_label("Apellidos y nombres").fill(LISTA_25)
    page.get_by_role("button", name="Importar").click()
    enlace = page.get_by_role("link", name="Tomar la asistencia de hoy")
    expect(enlace).to_be_visible()
    esperar_animaciones(page)

    assert enlace.bounding_box()["height"] >= 44
    assert (
        page.get_by_role("link", name="Editar a AGUILAR FLORES, LUCIANA").bounding_box()["height"]
        >= 44
    )
    revisar_con_axe(page, f"importados-pagina-{ancho}-{tema}")
    sin_desplazamiento(page, ancho)


@pytest.mark.parametrize("tema", TEMAS)
@pytest.mark.parametrize("ancho", ANCHOS)
def test_agregar_como_pagina_completa_pasa_axe(
    live_server, page, docente_con_seccion, seccion, con_25, clave, ancho, tema
):
    ir_a(page, live_server, seccion, docente_con_seccion, clave, ancho, tema, "agregar/")
    expect(page.get_by_label("Apellidos", exact=True)).to_be_visible()
    revisar_con_axe(page, f"agregar-pagina-{ancho}-{tema}")

    page.get_by_label("Apellidos", exact=True).fill("AGUIRRE HUAMÁN")
    page.get_by_role("button", name="Guardar y agregar otro").click()
    expect(page.get_by_label("Nombres", exact=True)).to_have_attribute("aria-invalid", "true")
    esperar_animaciones(page)
    revisar_con_axe(page, f"agregar-error-pagina-{ancho}-{tema}")

    page.get_by_label("Nombres", exact=True).fill("LUCÍA")
    page.get_by_role("button", name="Guardar y agregar otro").click()
    expect(page.get_by_role("status")).to_contain_text("Estudiante agregado")
    esperar_animaciones(page)
    revisar_con_axe(page, f"agregar-exito-pagina-{ancho}-{tema}")
    sin_desplazamiento(page, ancho)


@pytest.mark.parametrize("tema", TEMAS)
@pytest.mark.parametrize("ancho", ANCHOS)
def test_editar_como_pagina_completa_pasa_axe(
    live_server, page, docente_con_seccion, seccion, con_25, clave, ancho, tema
):
    ir_a(page, live_server, seccion, docente_con_seccion, clave, ancho, tema)
    page.get_by_role("link", name="Editar a AGUILAR FLORES, LUCIANA").click()
    expect(page.get_by_role("heading", name="Editar estudiante")).to_be_visible()

    revisar_con_axe(page, f"editar-pagina-{ancho}-{tema}")
    sin_desplazamiento(page, ancho)


@pytest.mark.parametrize("tema", TEMAS)
@pytest.mark.parametrize("ancho", ANCHOS)
def test_quitar_vaciar_y_los_bloqueos_como_pagina_completa_pasan_axe(
    live_server,
    page,
    docente_con_seccion,
    seccion,
    con_25,
    borrado_con_registros,
    clave,
    ancho,
    tema,
):
    ir_a(page, live_server, seccion, docente_con_seccion, clave, ancho, tema)
    page.get_by_role("link", name="Editar a AGUILAR FLORES, LUCIANA").click()
    page.get_by_role("link", name="Quitar estudiante").click()
    expect(page.get_by_role("button", name="Quitar estudiante")).to_be_visible()
    revisar_con_axe(page, f"quitar-pagina-{ancho}-{tema}")

    page.get_by_role("button", name="Quitar estudiante").click()
    expect(page.get_by_role("alert")).to_contain_text("No se puede quitar")
    esperar_animaciones(page)
    revisar_con_axe(page, f"quitar-bloqueo-pagina-{ancho}-{tema}")

    page.get_by_role("link", name="Volver a la lista").click()
    page.get_by_role("link", name="Vaciar lista").click()
    expect(page.get_by_text("Se quitarán los 25 estudiantes.")).to_be_visible()
    esperar_animaciones(page)
    revisar_con_axe(page, f"vaciar-pagina-{ancho}-{tema}")

    page.get_by_role("button", name="Vaciar lista").click()
    expect(page.get_by_role("alert")).to_contain_text("No se puede vaciar")
    esperar_animaciones(page)
    revisar_con_axe(page, f"vaciar-bloqueo-pagina-{ancho}-{tema}")
    sin_desplazamiento(page, ancho)


@pytest.mark.parametrize("ampliado", [False, True], ids=["normal", "texto-al-200"])
@pytest.mark.parametrize("ancho", [320, 360])
def test_un_nombre_de_120_mas_120_se_lee_completo_como_pagina_completa(
    live_server, page, docente_con_seccion, seccion, clave, ancho, ampliado
):
    from institucion.models import Estudiante

    apellidos, nombres = ("HUAMÁN " * 18)[:120], ("MARÍA " * 21)[:119] + "A"
    assert (len(apellidos), len(nombres)) == (120, 120)
    Estudiante.objects.create(seccion=seccion, apellidos=apellidos, nombres=nombres)
    ir_a(page, live_server, seccion, docente_con_seccion, clave, ancho, "light")
    if ampliado:
        # El texto al 200 %: el panel se pinta al doble y sigue dentro de la misma ventana.
        page.add_style_tag(content=".panel-lista { zoom: 2; }")

    nombre = page.locator(".estudiante-nombre")
    expect(nombre).to_have_text(f"{apellidos}, {nombres}")
    assert nombre.evaluate("(el) => el.scrollWidth <= el.clientWidth")
    assert nombre.evaluate("(el) => getComputedStyle(el).textOverflow") != "ellipsis"
    editar = page.get_by_role("link", name=f"Editar a {apellidos}, {nombres}")
    caja = editar.bounding_box()
    assert caja["x"] >= 0
    assert caja["x"] + caja["width"] <= ancho
    assert caja["height"] >= 44 or ampliado
    sin_desplazamiento(page, ancho)


def test_a_360_el_pie_apila_sus_acciones_a_todo_el_ancho(
    live_server, page, docente_con_seccion, seccion, clave
):
    ir_a(page, live_server, seccion, docente_con_seccion, clave, 360, "light", "agregar/")

    principal = page.get_by_role("button", name="Guardar y agregar otro").bounding_box()
    volver = page.get_by_role("link", name="Volver a la lista").bounding_box()
    pie = page.locator("#modal-pie").bounding_box()
    relleno = float(
        page.locator("#modal-pie").evaluate("(el) => getComputedStyle(el).paddingLeft")[:-2]
    )
    assert volver["y"] > principal["y"] + principal["height"] - 1
    for caja in (principal, volver):
        assert caja["width"] >= pie["width"] - 2 * relleno - 1
        assert caja["height"] >= 44


# --- El cuerpo del diálogo vuelve arriba al cambiar de vista (rebrand-us-006, D4) ---


def test_al_cambiar_de_vista_el_cuerpo_del_dialogo_vuelve_arriba(portada, con_25):
    portada.evaluate(
        """() => {
            window.llamadasAScrollTo = [];
            const original = Element.prototype.scrollTo;
            Element.prototype.scrollTo = function (...args) {
                window.llamadasAScrollTo.push(this.id);
                return original.apply(this, args);
            };
        }"""
    )
    abrir(portada)
    portada.locator("#modal-cuerpo").evaluate("(el) => { el.scrollTop = el.scrollHeight; }")

    dialogo(portada).get_by_role("link", name="Editar a VARGAS GUTIÉRREZ, SANTIAGO").click()

    expect(campo(portada, "Apellidos")).to_be_focused()
    assert "modal-cuerpo" in portada.evaluate("window.llamadasAScrollTo")
    assert portada.locator("#modal-cuerpo").evaluate("(el) => el.scrollTop") == 0


# --- Lista más alta que el diálogo (A2 [high] de rebrand-us-006; rebrand-portada, D6) ---


@pytest.fixture
def con_40(seccion):
    from institucion.models import Estudiante

    for n in range(40):
        Estudiante.objects.create(
            seccion=seccion,
            apellidos=f"APELLIDO {chr(65 + n // 26)}{chr(65 + n % 26)}",
            nombres="ANA",
        )


@pytest.mark.parametrize("ancho", ANCHOS)
def test_con_40_el_ultimo_editar_se_alcanza_desplazando_el_cuerpo(
    live_server, page, docente_con_seccion, con_40, clave, ancho
):
    con_pantalla(page, ancho, "light")
    ingresar(page, live_server, docente_con_seccion, clave)
    abrir(page)
    cuerpo = page.locator("#modal-cuerpo")
    expect(dialogo(page)).to_contain_text("40 estudiantes")
    pagina_antes = page.evaluate("[window.scrollY, document.documentElement.scrollTop]")
    assert cuerpo.evaluate("(el) => el.scrollHeight > el.clientHeight"), "la lista cabe entera"

    cuerpo.evaluate("(el) => { el.scrollTop = el.scrollHeight; }")
    ultimo = dialogo(page).get_by_role("link", name="Editar a APELLIDO BN, ANA")

    expect(ultimo).to_be_in_viewport()
    caja = ultimo.bounding_box()
    marco = cuerpo.bounding_box()
    assert caja["y"] >= marco["y"] and caja["y"] + caja["height"] <= marco["y"] + marco["height"]
    assert page.evaluate("[window.scrollY, document.documentElement.scrollTop]") == pagina_antes
    ultimo.click()
    expect(campo(page, "Apellidos")).to_have_value("APELLIDO BN")
