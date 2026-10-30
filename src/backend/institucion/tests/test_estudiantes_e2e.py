"""Diálogo de la lista de estudiantes en el navegador (spec estudiantes-seccion; US-006, D6 y D10).

Abrir con "Ver estudiantes", cerrar con Esc y "Cerrar" (el foco vuelve al enlace), Atrás que cierra
el diálogo, axe de la portada y de la lista vacía en ambos temas a 360 y 1280 px, y 320 px sin
desplazamiento horizontal.
Necesita el CSS compilado y Chromium: ``uv run pytest -m e2e --browser chromium``.
"""

import re

import pytest
from playwright.sync_api import expect

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

    abrir(page)
    ancho_del_dialogo = page.evaluate("document.getElementById('estudiantes').scrollWidth")
    assert ancho_del_dialogo <= ancho

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

    portada.keyboard.press("Tab")
    expect(dialogo(portada).get_by_role("link", name="Agregar uno por uno")).to_be_focused()
    assert contorno(portada, "#estudiantes .boton-principal")["ancho"] == "2px"


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
            secundario.className = "boton-secundario";
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
    expect(portada.locator(".mensaje--aviso")).to_contain_text(
        "Tu sesión se cerró por inactividad."
    )
    expect(portada.locator("dialog")).to_have_count(0)
    assert seccion.estudiantes.count() == 0


def esperar_animaciones(page):
    # axe mide el color calculado: a media animación de entrada lo mezcla con la opacidad. Solo los
    # mensajes: el carrusel de la portada (detrás del diálogo, en el celular) no deja de animarse.
    page.wait_for_function(
        "[...document.querySelectorAll('.mensaje')].every((m) => m.getAnimations().length === 0)"
    )


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
def test_un_nombre_de_120_mas_120_se_lee_completo_sin_desplazamiento(
    live_server, page, docente_con_seccion, seccion, clave, ancho
):
    from institucion.models import Estudiante

    apellidos, nombres = ("HUAMÁN " * 18)[:120], ("MARÍA " * 21)[:119] + "A"
    assert (len(apellidos), len(nombres)) == (120, 120)
    Estudiante.objects.create(seccion=seccion, apellidos=apellidos, nombres=nombres)
    con_pantalla(page, ancho, "light")
    ingresar(page, live_server, docente_con_seccion, clave)

    abrir(page)

    nombre = dialogo(page).locator(".estudiante__nombre")
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

    expect(dialogo(portada).locator(".estudiante__nombre")).to_have_text("QUISPE MAMANI, ANA LUCÍA")
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
        expect(page.locator(".estudiantes")).to_contain_text("QUISPE MAMANI, ANA LUCÍA")

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
    alto = tomar_asistencia(portada).bounding_box()["height"]
    assert alto >= 44, alto

    tomar_asistencia(portada).click()

    expect(portada).to_have_url(f"{live_server.url}/docente/secciones/{seccion.pk}/asistencia/")
    expect(portada.get_by_role("heading", level=1)).to_have_text("Asistencia · 2.º A")
    expect(portada.locator("dialog")).to_have_count(0)


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
