"""Sesiones en el navegador (spec envio-sesiones; design de US-010, US-014 y EN-03, D5, D7 y D8).

Popup «Subir una sesión», campos, validación en el navegador, términos (4a), envío con
``XMLHttpRequest`` y el éxito. Los archivos son los ficticios de ``archivos.py``.
Necesita el CSS compilado y Chromium:
``DJANGO_ALLOW_ASYNC_UNSAFE=true uv run pytest -m e2e --browser chromium src/backend/repositorio``.
"""

import re
import time

import pytest
from django.core.files.storage import storages
from playwright.sync_api import expect

from actividad.models import Operacion, RegistroActividad
from catalogo.models import InstitucionArea
from cuentas.tests.e2e import ANCHOS, TEMAS, con_pantalla, ingresar, revisar_con_axe
from repositorio.models import Sesion
from repositorio.tests.archivos import docx_bytes, pdf_bytes

pytestmark = pytest.mark.e2e

URL = "/docente/sesiones/"
# 1,2 MB como los cuenta el navegador y filesizeformat (base 1024).
UN_COMA_DOS_MB = 1258291
CUATRO_MB = 4 * 1024 * 1024


@pytest.fixture(autouse=True)
def _catalogo(catalogo):
    """Las áreas de la institución salen del catálogo, que las e2e vacían al terminar."""


@pytest.fixture
def docente_con_seccion(seccion, docente):
    seccion.docente = docente
    seccion.save()
    return docente


@pytest.fixture
def pantalla(live_server, page, docente_con_seccion, clave):
    ingresar(page, live_server, docente_con_seccion, clave)
    expect(page).to_have_url(f"{live_server.url}/docente/")
    page.goto(f"{live_server.url}{URL}")
    expect(boton_subir(page)).to_be_visible()
    return page


# --- Ayudas ---


def boton_subir(page):
    return page.get_by_role("button", name="Subir una sesión")


def popup(page):
    return page.get_by_role("dialog", name="Subir una sesión")


def terminos(page):
    return page.get_by_role("dialog", name="Antes de compartir")


def enviar(page):
    return popup(page).get_by_role(
        "button", name=re.compile(r"Enviar a la dirección|Enviando…|Reintentar envío")
    )


def cancelar(page):
    return popup(page).get_by_role("button", name="Cancelar")


def resultado(page):
    return page.locator("[data-resultado]")


def abrir(page):
    boton_subir(page).click()
    expect(popup(page)).to_be_visible()


def elegir(page, nombre, contenido, tipo="application/pdf"):
    page.locator("#archivo").set_input_files(
        {"name": nombre, "mimeType": tipo, "buffer": contenido}
    )


def elegir_pdf(page, nombre="leemos-un-cuento.pdf", tamano=UN_COMA_DOS_MB):
    elegir(page, nombre, pdf_bytes(tamano))
    expect(page.locator("[data-archivo-detalle]")).to_contain_text("PDF ·")


def llenar(page, titulo="Leemos un cuento", area="Comunicación"):
    elegir_pdf(page)
    page.locator("#area").select_option(label=area)
    page.locator("#titulo").fill(titulo)


def id_enviado(peticion):
    """El ``id`` (UUID del navegador, D5) del cuerpo multipart de un envío."""
    cuerpo = peticion.post_data_buffer.decode("latin-1")
    return re.search(r'name="id"\r\n\r\n([0-9a-f-]{36})', cuerpo).group(1)


def error_de(page, campo):
    return page.locator(f"#{campo}-error")


def esperar_exito(page, texto="Sesión enviada a la dirección"):
    expect(popup(page)).to_be_hidden()
    expect(resultado(page)).to_contain_text(texto)


# --- Popup «Subir una sesión» ---


def test_abrir_el_popup_enfoca_su_titulo_y_deja_la_pantalla_inerte(pantalla):
    abrir(pantalla)

    expect(pantalla.locator("#subir-titulo")).to_be_focused()
    expect(popup(pantalla)).to_contain_text("Se enviará a la dirección.")
    assert pantalla.evaluate("document.getElementById('subir').matches(':modal')")
    expect(pantalla.locator("#compartir")).not_to_be_checked()


def test_tocar_afuera_no_cierra_el_popup(pantalla):
    con_pantalla(pantalla, 1280, "light")
    abrir(pantalla)
    pantalla.locator("#titulo").fill("Leemos un cuento")

    pantalla.mouse.click(8, 8)

    expect(popup(pantalla)).to_be_visible()
    expect(pantalla.locator("#titulo")).to_have_value("Leemos un cuento")


@pytest.mark.parametrize("como", ["boton", "esc"])
def test_cancelar_cierra_sin_guardar_y_al_abrir_otra_vez_esta_vacio(pantalla, como):
    abrir(pantalla)
    llenar(pantalla)

    if como == "boton":
        cancelar(pantalla).click()
    else:
        pantalla.keyboard.press("Escape")

    expect(popup(pantalla)).to_be_hidden()
    expect(boton_subir(pantalla)).to_be_focused()
    abrir(pantalla)
    expect(pantalla.locator("#titulo")).to_have_value("")
    expect(pantalla.locator("#area")).to_have_value("")
    expect(pantalla.locator("[data-archivo-nombre]")).to_have_text("Elige tu sesión")
    assert not Sesion.objects.exists()


@pytest.mark.parametrize("ancho", [360, 1280])
def test_orden_de_los_botones(pantalla, ancho):
    con_pantalla(pantalla, ancho, "light")
    abrir(pantalla)

    caja_enviar = enviar(pantalla).bounding_box()
    caja_cancelar = cancelar(pantalla).bounding_box()

    if ancho == 360:
        assert caja_enviar["y"] < caja_cancelar["y"], "en el celular «Enviar» va arriba"
    else:
        assert caja_cancelar["x"] < caja_enviar["x"], "en la PC «Cancelar» va a la izquierda"


# --- Campos ---


def test_las_areas_son_las_que_trabaja_la_institucion_en_orden_siagie(pantalla, institucion):
    abrir(pantalla)

    esperadas = [
        fila.area.nombre
        for fila in InstitucionArea.objects.filter(institucion=institucion, se_trabaja=True)
        .select_related("area")
        .order_by("area__orden")
    ]
    opciones = pantalla.locator("#area option").all_inner_texts()
    assert opciones == ["Elige el área", *esperadas]


def test_archivo_elegido_muestra_nombre_tipo_tamano_y_cambiar(pantalla):
    abrir(pantalla)

    elegir_pdf(pantalla)

    expect(pantalla.locator("[data-archivo-nombre]")).to_have_text("leemos-un-cuento.pdf")
    expect(pantalla.locator("[data-archivo-detalle]")).to_have_text("PDF · 1,2 MB")
    expect(pantalla.locator("[data-archivo-accion]")).to_have_text("Cambiar")


def test_un_docx_se_reconoce_como_word(pantalla):
    abrir(pantalla)

    elegir(pantalla, "leemos-un-cuento.docx", docx_bytes(), "application/octet-stream")

    expect(pantalla.locator("[data-archivo-detalle]")).to_contain_text("Word ·")
    expect(error_de(pantalla, "archivo")).to_be_hidden()


def test_el_grado_viene_con_el_de_su_seccion(pantalla):
    abrir(pantalla)

    expect(pantalla.locator("#grado")).to_have_value("2")
    expect(pantalla.locator("#grado-ayuda")).to_have_text(
        "Grado de tu sección: 2.º A. Puedes cambiarlo."
    )


# --- Datos que faltan ---


def test_sin_area_ni_titulo_muestra_sus_errores_y_enfoca_el_primero(pantalla):
    abrir(pantalla)
    elegir_pdf(pantalla)

    enviar(pantalla).click()

    expect(error_de(pantalla, "area")).to_have_text("Falta indicar el área.")
    expect(error_de(pantalla, "titulo")).to_have_text("Falta indicar el título.")
    expect(pantalla.locator("#area")).to_have_attribute("aria-invalid", "true")
    expect(pantalla.locator("#area")).to_be_focused()
    expect(popup(pantalla)).to_be_visible()
    assert not Sesion.objects.exists()


def test_sin_archivo_lo_pide(pantalla):
    abrir(pantalla)
    pantalla.locator("#area").select_option(label="Comunicación")
    pantalla.locator("#titulo").fill("Leemos un cuento")

    enviar(pantalla).click()

    expect(error_de(pantalla, "archivo")).to_have_text("Elige un archivo PDF o Word (.docx).")
    expect(pantalla.locator("#archivo")).to_be_focused()


def test_corregir_un_campo_quita_su_error(pantalla):
    abrir(pantalla)
    enviar(pantalla).click()
    expect(error_de(pantalla, "titulo")).to_be_visible()

    pantalla.locator("#titulo").fill("Leemos un cuento")

    expect(error_de(pantalla, "titulo")).to_be_hidden()


# --- Archivo en el navegador ---


def test_un_archivo_que_no_es_pdf_aunque_se_llame_asi_se_rechaza(pantalla):
    abrir(pantalla)
    pantalla.locator("#area").select_option(label="Comunicación")
    pantalla.locator("#titulo").fill("Leemos un cuento")

    elegir(pantalla, "sesion.pdf", b"MZ\x90\x00" + b"\x00" * 200, "application/pdf")

    mensaje = "Este archivo no es PDF ni Word (.docx). Elige otro archivo."
    expect(error_de(pantalla, "archivo")).to_have_text(mensaje)
    expect(pantalla.locator("[data-archivo-detalle]")).to_contain_text("No se ha subido")
    enviar(pantalla).click()
    expect(error_de(pantalla, "archivo")).to_have_text(mensaje)
    expect(popup(pantalla)).to_be_visible()
    assert not Sesion.objects.exists()


def test_un_archivo_de_mas_de_4_mb_se_rechaza(pantalla):
    abrir(pantalla)

    elegir(pantalla, "leemos-un-cuento.pdf", pdf_bytes(CUATRO_MB + 1))

    expect(error_de(pantalla, "archivo")).to_have_text(
        "El archivo supera los 4 MB. Elige uno más pequeño."
    )


# --- Compartir y términos ---


def test_enviar_sin_compartir_va_directo_y_muestra_el_exito(pantalla):
    abrir(pantalla)
    llenar(pantalla)

    enviar(pantalla).click()

    expect(terminos(pantalla)).to_be_hidden()
    esperar_exito(pantalla)
    exito = resultado(pantalla)
    expect(exito).not_to_contain_text("compartida en el repositorio")
    for texto in ["Leemos un cuento", "2.º grado", "Comunicación", "leemos-un-cuento.pdf"]:
        expect(exito).to_contain_text(texto)
    expect(exito).to_contain_text("PDF · 1,2\xa0MB")
    expect(exito).to_have_attribute("role", "status")
    expect(exito.get_by_role("heading", name="Leemos un cuento")).to_be_focused()
    expect(boton_subir(pantalla)).to_be_hidden()
    expect(pantalla.get_by_text("Aquí verás las sesiones que envíes y su estado.")).to_be_visible()
    sesion = Sesion.objects.get()
    assert sesion.compartida is False
    assert sesion.terminos_aceptados_en is None


def test_aceptar_y_enviar_comparte_y_guarda_la_aceptacion(pantalla):
    abrir(pantalla)
    llenar(pantalla)
    pantalla.locator("#compartir").check()

    enviar(pantalla).click()

    expect(terminos(pantalla)).to_be_visible()
    expect(pantalla.locator("#terminos-titulo")).to_be_focused()
    expect(terminos(pantalla)).to_contain_text("Soy autor(a) de la sesión")
    terminos(pantalla).get_by_role("button", name="Acepto y envío").click()

    esperar_exito(pantalla, "Sesión enviada a la dirección y compartida en el repositorio")
    expect(terminos(pantalla)).to_be_hidden()
    sesion = Sesion.objects.get()
    assert sesion.compartida is True
    assert sesion.terminos_aceptados_en is not None


@pytest.mark.parametrize("como", ["boton", "esc"])
def test_volver_cierra_solo_los_terminos_y_conserva_el_formulario(pantalla, como):
    abrir(pantalla)
    llenar(pantalla)
    pantalla.locator("#compartir").check()
    enviar(pantalla).click()
    expect(terminos(pantalla)).to_be_visible()

    if como == "boton":
        terminos(pantalla).get_by_role("button", name="Volver").click()
    else:
        pantalla.keyboard.press("Escape")

    expect(terminos(pantalla)).to_be_hidden()
    expect(popup(pantalla)).to_be_visible()
    expect(enviar(pantalla)).to_be_focused()
    expect(pantalla.locator("#titulo")).to_have_value("Leemos un cuento")
    expect(pantalla.locator("#compartir")).to_be_checked()
    expect(pantalla.locator("[data-archivo-nombre]")).to_have_text("leemos-un-cuento.pdf")
    assert not Sesion.objects.exists()


def test_datos_incompletos_con_la_casilla_marcada_no_abren_los_terminos(pantalla):
    abrir(pantalla)
    elegir_pdf(pantalla)
    pantalla.locator("#area").select_option(label="Comunicación")
    pantalla.locator("#compartir").check()

    enviar(pantalla).click()

    expect(error_de(pantalla, "titulo")).to_have_text("Falta indicar el título.")
    expect(terminos(pantalla)).to_be_hidden()


# --- Después del éxito ---


def test_subir_otra_abre_un_formulario_nuevo(pantalla):
    abrir(pantalla)
    llenar(pantalla)
    id_primero = pantalla.locator("input[name=id]").input_value()
    enviar(pantalla).click()
    esperar_exito(pantalla)

    resultado(pantalla).get_by_role("button", name="Subir otra").click()

    expect(popup(pantalla)).to_be_visible()
    expect(pantalla.locator("#titulo")).to_have_value("")
    assert pantalla.locator("input[name=id]").input_value() not in ("", id_primero)
    llenar(pantalla, titulo="Contamos hasta veinte", area="Matemática")
    enviar(pantalla).click()
    expect(resultado(pantalla)).to_contain_text("Contamos hasta veinte")
    assert Sesion.objects.count() == 2


def test_recargar_despues_del_exito_no_muestra_el_mensaje_ni_envia_otra(pantalla):
    abrir(pantalla)
    llenar(pantalla)
    enviar(pantalla).click()
    esperar_exito(pantalla)

    pantalla.reload()

    expect(boton_subir(pantalla)).to_be_visible()
    expect(resultado(pantalla)).to_be_empty()
    assert Sesion.objects.count() == 1


# --- Botón «atrás» (D8) ---

ENVIO = "**/docente/sesiones/enviar/"


def test_atras_en_el_formulario_lo_cierra_y_sigue_en_sesiones(live_server, pantalla):
    abrir(pantalla)
    pantalla.locator("#titulo").fill("Leemos un cuento")

    pantalla.go_back()

    expect(popup(pantalla)).to_be_hidden()
    expect(pantalla).to_have_url(f"{live_server.url}{URL}")
    expect(boton_subir(pantalla)).to_be_visible()


def test_atras_en_los_terminos_cierra_solo_los_terminos(pantalla):
    abrir(pantalla)
    llenar(pantalla)
    pantalla.locator("#compartir").check()
    enviar(pantalla).click()
    expect(terminos(pantalla)).to_be_visible()

    pantalla.go_back()

    expect(terminos(pantalla)).to_be_hidden()
    expect(popup(pantalla)).to_be_visible()
    expect(pantalla.locator("#titulo")).to_have_value("Leemos un cuento")
    expect(pantalla.locator("#compartir")).to_be_checked()
    expect(pantalla.locator("[data-archivo-nombre]")).to_have_text("leemos-un-cuento.pdf")
    pantalla.go_back()
    expect(popup(pantalla)).to_be_hidden()


# --- Subida (D7, D8) ---


@pytest.fixture
def retenida(pantalla):
    """El envío queda detenido hasta ``soltar()``: la subida sigue «en curso»."""
    detenidas = []

    def detener(ruta):
        detenidas.append(ruta)

    pantalla.route(ENVIO, detener)

    def soltar():
        assert detenidas, "el navegador mandó el envío"
        detenidas.pop().continue_()

    return soltar


def enviar_y_esperar_subida(page):
    llenar(page)
    enviar(page).click()
    expect(page.locator("[data-progreso]")).to_be_visible()


def test_subiendo_bloquea_campos_botones_y_esc(pantalla, retenida):
    abrir(pantalla)
    enviar_y_esperar_subida(pantalla)

    expect(pantalla.locator("[data-progreso-texto]")).to_have_text(re.compile(r"^Subiendo… \d+ %$"))
    expect(pantalla.locator("[data-progreso] progress")).to_be_visible()
    for campo in ["#archivo", "#grado", "#area", "#titulo", "#proposito", "#compartir"]:
        expect(pantalla.locator(campo)).to_be_disabled()
    expect(enviar(pantalla)).to_have_attribute("aria-disabled", "true")
    expect(cancelar(pantalla)).to_have_attribute("aria-disabled", "true")

    pantalla.keyboard.press("Escape")
    cancelar(pantalla).click(force=True)  # aria-disabled: el clic llega y no hace nada
    enviar(pantalla).click(force=True)

    expect(popup(pantalla)).to_be_visible()
    retenida()
    esperar_exito(pantalla)
    assert Sesion.objects.count() == 1


def test_atras_mientras_sube_no_cierra_y_la_subida_sigue(pantalla, retenida):
    abrir(pantalla)
    enviar_y_esperar_subida(pantalla)

    pantalla.go_back()

    expect(popup(pantalla)).to_be_visible()
    expect(pantalla.locator("[data-progreso]")).to_be_visible()
    retenida()
    esperar_exito(pantalla)
    assert Sesion.objects.count() == 1


def test_recargar_mientras_sube_pide_confirmar(pantalla, retenida):
    abrir(pantalla)
    enviar_y_esperar_subida(pantalla)
    avisos = []

    def responder(dialogo):
        avisos.append(dialogo.type)
        dialogo.dismiss()

    pantalla.on("dialog", responder)
    pantalla.close(run_before_unload=True)
    pantalla.wait_for_timeout(500)

    assert avisos == ["beforeunload"]
    assert not pantalla.is_closed()


# --- Corte de red y reintento (D5) ---


def test_se_corta_y_al_reintentar_se_envia_una_sola_vez(pantalla):
    envios = []

    def cortar_una_vez(ruta):
        envios.append(ruta.request)
        if len(envios) == 1:
            ruta.abort("failed")
        else:
            ruta.continue_()

    pantalla.route(ENVIO, cortar_una_vez)
    abrir(pantalla)
    llenar(pantalla)

    enviar(pantalla).click()

    expect(popup(pantalla).locator("[data-error-red]")).to_contain_text("Se cortó la conexión")
    expect(enviar(pantalla)).to_have_text("Reintentar envío")
    expect(pantalla.locator("#titulo")).to_be_enabled()
    expect(pantalla.locator("#titulo")).to_have_value("Leemos un cuento")
    expect(pantalla.locator("[data-archivo-nombre]")).to_have_text("leemos-un-cuento.pdf")
    expect(pantalla.locator("[data-progreso]")).to_be_hidden()

    enviar(pantalla).click()

    esperar_exito(pantalla)
    assert len(envios) == 2
    assert id_enviado(envios[0]) == id_enviado(envios[1])
    assert Sesion.objects.count() == 1


def test_se_guardo_pero_no_llego_la_respuesta_y_el_reintento_da_el_mismo_exito(pantalla):
    envios = []

    def perder_la_primera_respuesta(ruta):
        envios.append(ruta.request.post_data_buffer)
        if len(envios) == 1:
            ruta.fetch()  # el servidor guarda la sesión
            ruta.abort("failed")  # y la respuesta no llega
        else:
            ruta.continue_()

    pantalla.route(ENVIO, perder_la_primera_respuesta)
    abrir(pantalla)
    llenar(pantalla)
    enviar(pantalla).click()
    expect(enviar(pantalla)).to_have_text("Reintentar envío")
    assert Sesion.objects.count() == 1

    enviar(pantalla).click()

    esperar_exito(pantalla)
    assert Sesion.objects.count() == 1
    assert RegistroActividad.objects.filter(operacion=Operacion.SESION_ENVIADA).count() == 1
    assert len(storages["sesiones"].listdir("sesiones")[1]) == 1


# --- Pantalla accesible y sin desplazamiento horizontal ---

# Objetivos táctiles de la capa de arriba (el popup abierto o la página): 44 px o más.
OBJETIVOS_PEQUENOS = """() => {
  const capas = [...document.querySelectorAll("dialog[open]")];
  const raiz = capas.length ? capas[capas.length - 1] : document;
  const selector = "button, a[href], select, textarea, summary, label.elegir-archivo,"
    + " label.casilla, input:not([type=hidden]):not([type=file]):not([type=checkbox])";
  return [...raiz.querySelectorAll(selector)]
    .filter((el) => el.getClientRects().length && getComputedStyle(el).visibility !== "hidden")
    .map((el) => ({ el: el.outerHTML.slice(0, 80), caja: el.getBoundingClientRect() }))
    .filter(({ caja }) => caja.height < 44 || caja.width < 44)
    .map(({ el, caja }) => `${el} ${Math.round(caja.width)}x${Math.round(caja.height)}`);
}"""


def revisar_estado(page, estado, tema, ancho):
    revisar_con_axe(page, f"sesiones-{estado}-{tema}-{ancho}")
    assert page.evaluate(
        "document.documentElement.scrollWidth <= document.documentElement.clientWidth"
    ), f"desplazamiento horizontal en el estado {estado}"
    assert page.evaluate(OBJETIVOS_PEQUENOS) == [], f"objetivos de menos de 44 px en {estado}"


@pytest.mark.parametrize("tema", TEMAS)
@pytest.mark.parametrize("ancho", ANCHOS)
def test_los_estados_del_boceto_son_accesibles_y_sin_desplazamiento(pantalla, tema, ancho):
    con_pantalla(pantalla, ancho, tema)
    revisar_estado(pantalla, "1", tema, ancho)

    abrir(pantalla)
    revisar_estado(pantalla, "2", tema, ancho)

    llenar(pantalla)
    pantalla.locator("#compartir").check()
    revisar_estado(pantalla, "3", tema, ancho)

    enviar(pantalla).click()
    expect(terminos(pantalla)).to_be_visible()
    revisar_estado(pantalla, "4a", tema, ancho)
    terminos(pantalla).get_by_role("button", name="Volver").click()

    pantalla.locator("#compartir").uncheck()
    pantalla.locator("#area").select_option("")
    pantalla.locator("#titulo").fill("")
    enviar(pantalla).click()
    expect(error_de(pantalla, "titulo")).to_be_visible()
    revisar_estado(pantalla, "5", tema, ancho)

    elegir(pantalla, "foto-de-la-sesion.jpg", b"\xff\xd8\xff\xe0" + b"\x00" * 900, "image/jpeg")
    expect(error_de(pantalla, "archivo")).to_be_visible()
    revisar_estado(pantalla, "6a", tema, ancho)

    elegir(pantalla, "leemos-un-cuento.pdf", pdf_bytes(CUATRO_MB + 1))
    expect(error_de(pantalla, "archivo")).to_contain_text("4 MB")
    revisar_estado(pantalla, "6b", tema, ancho)

    detenidas = []

    def detener(ruta):
        detenidas.append(ruta)

    pantalla.route(ENVIO, detener)
    llenar(pantalla)
    enviar(pantalla).click()
    expect(pantalla.locator("[data-progreso]")).to_be_visible()
    revisar_estado(pantalla, "7", tema, ancho)

    detenidas.pop().abort("failed")
    expect(popup(pantalla).locator("[data-error-red]")).to_be_visible()
    revisar_estado(pantalla, "8", tema, ancho)

    pantalla.unroute(ENVIO)
    enviar(pantalla).click()
    esperar_exito(pantalla)
    revisar_estado(pantalla, "9", tema, ancho)

    resultado(pantalla).get_by_role("button", name="Subir otra").click()
    llenar(pantalla)
    pantalla.locator("#compartir").check()
    enviar(pantalla).click()
    terminos(pantalla).get_by_role("button", name="Acepto y envío").click()
    esperar_exito(pantalla, "compartida en el repositorio")
    revisar_estado(pantalla, "10", tema, ancho)


def test_pantalla_baja_los_terminos_se_desplazan_y_sus_botones_siguen_a_la_vista(pantalla):
    pantalla.set_viewport_size({"width": 360, "height": 560})
    abrir(pantalla)
    llenar(pantalla)
    pantalla.locator("#compartir").check()
    enviar(pantalla).click()
    expect(terminos(pantalla)).to_be_visible()

    cuerpo = terminos(pantalla).locator(".modal-cuerpo")
    assert cuerpo.evaluate("(el) => el.scrollHeight > el.clientHeight"), "el cuerpo se desplaza"
    for nombre in ["Acepto y envío", "Volver"]:
        caja = terminos(pantalla).get_by_role("button", name=nombre).bounding_box()
        assert caja["y"] >= 0 and caja["y"] + caja["height"] <= 560, nombre


SLOW_4G = {
    "offline": False,
    "downloadThroughput": 1.6 * 1024 * 1024 / 8 * 0.9,
    "uploadThroughput": 750 * 1024 / 8 * 0.9,
    "latency": 150 * 3.75,
}


def test_sesiones_carga_con_slow_4g(live_server, page, docente_con_seccion, clave, browser_name):
    """RNF-002: la pantalla, sin caché y con Slow 4G, usable en 5 s y con 2 MB o menos."""
    if browser_name != "chromium":
        pytest.skip("El perfil de red por CDP existe solo en Chromium.")
    con_pantalla(page, 360, "light")
    ingresar(page, live_server, docente_con_seccion, clave)
    page.wait_for_url(f"{live_server.url}/docente/")
    sesion = page.context.new_cdp_session(page)
    sesion.send("Network.enable")
    sesion.send("Network.setCacheDisabled", {"cacheDisabled": True})
    sesion.send("Network.emulateNetworkConditions", SLOW_4G)
    transferidos = []
    sesion.on(
        "Network.loadingFinished", lambda evento: transferidos.append(evento["encodedDataLength"])
    )

    inicio = time.perf_counter()
    page.goto(f"{live_server.url}{URL}")
    expect(boton_subir(page)).to_be_visible()
    page.evaluate("document.fonts.ready")
    abrir(page)
    segundos = time.perf_counter() - inicio

    assert transferidos
    total = sum(transferidos)
    print(f"\nSlow 4G en Sesiones: {total / 1024:.1f} KB, {segundos:.2f} s")
    assert total <= 2 * 1024 * 1024, f"{total} bytes"
    assert segundos <= 5, f"{segundos:.2f} s"
