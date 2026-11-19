"""Completar la plantilla del SIAGIE en el navegador (spec plantilla-notas-siagie; US-024/025).

Las seis de D12: el flujo principal con la descarga, elegir la sección y corregirla, el rechazo, el
corte de red, el resumen a 360 px y axe en ambos temas. ``plantilla-siagie.js`` envía con
``XMLHttpRequest`` y pinta el paso de la sección o el resumen. Las plantillas son las ficticias de
``plantilla.py``. Necesita el CSS compilado y Chromium:
``DJANGO_ALLOW_ASYNC_UNSAFE=true uv run pytest -m e2e --browser chromium <este archivo>``.
"""

import io

import pytest
from openpyxl import load_workbook
from playwright.sync_api import expect

from cuentas.tests.e2e import TEMAS, con_pantalla, ingresar, revisar_con_axe
from exportaciones.models import EquivalenciaSeccion
from exportaciones.tests.plantilla import generar

pytestmark = [pytest.mark.e2e, pytest.mark.django_db(transaction=True)]

TIPO_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
URL_ENVIO = "**/direccion/plantilla-siagie/"
URL_BORRAR = "**/direccion/plantilla-siagie/equivalencias/*/borrar/"
NOMBRE_ARCHIVO = "RegNotas_2_B_B3.xlsx"
AVISO_BORRADA = (
    "Quitamos la equivalencia. "
    "La próxima plantilla de 2.º TRIUNFADORES te pedirá elegir la sección."
)
NOMBRE_60 = "A" * 29 + ", " + "B" * 29  # 60 caracteres, sin espacios por donde cortar


@pytest.fixture(autouse=True)
def _catalogo_cargado(catalogo):
    """El catálogo debe estar antes de crear la institución, que copia sus áreas."""


def plantilla(**campos):
    campos.setdefault("nombre_seccion", "B")
    campos.setdefault("nombres", ["PEREZ QUISPE, MARIA"])
    campos.setdefault("hojas", {"063-MATE": 4})
    return generar(**campos)


@pytest.fixture
def inicio(live_server, page, b_con_notas, direccion, clave):
    """El inicio de la dirección, con 2.º B con notas en el bimestre 3."""
    con_pantalla(page, 1280, "light")
    ingresar(page, live_server, direccion, clave)
    expect(page).to_have_url(f"{live_server.url}/direccion/")
    return page


# --- Ayudas ---


def boton_subir(page):
    return page.get_by_role("button", name="Subir plantilla", exact=True)


def dialogo(page):
    return page.get_by_role("dialog")


def completar(page):
    return dialogo(page).get_by_role("button", name="Completar plantilla")


def quieto(page):
    """Espera a que el diálogo termine su entrada o su salida (sondeo de 100 ms)."""
    page.wait_for_function("document.getAnimations().length === 0", polling=100)


def abrir(page):
    boton_subir(page).click()
    expect(dialogo(page)).to_be_visible()
    quieto(page)


def elegir(page, contenido, nombre=NOMBRE_ARCHIVO):
    page.locator("#archivo").set_input_files(
        {"name": nombre, "mimeType": TIPO_XLSX, "buffer": contenido}
    )
    expect(page.locator("[data-archivo-detalle]")).to_have_text("Excel (.xlsx)")


def resumen(page):
    return page.locator('[data-paso="resumen"]')


def completar_con(page, contenido, nombre=NOMBRE_ARCHIVO):
    abrir(page)
    elegir(page, contenido, nombre)
    completar(page).click()


# --- Flujo principal ---


def test_completa_la_plantilla_descarga_el_archivo_y_cancelar_devuelve_el_foco(inicio):
    """Escenarios «Abrir el diálogo», «Cancelar», «Camino ideal» y «Descargar»."""
    page = inicio
    abrir(page)
    expect(
        dialogo(page).get_by_role("heading", name="Sube la plantilla del SIAGIE")
    ).to_be_focused()
    expect(completar(page)).to_be_disabled()
    dialogo(page).get_by_role("button", name="Cancelar").click()
    expect(dialogo(page)).to_be_hidden()
    expect(boton_subir(page)).to_be_focused()

    completar_con(page, plantilla())

    expect(resumen(page)).to_be_visible()
    expect(page.get_by_role("heading", level=1)).to_have_text("Plantilla completada")
    expect(page.get_by_role("heading", level=1)).to_be_focused()
    expect(page.locator(".resumen-metricas li")).to_have_text(
        [
            "1estudiantes encontrados",
            "0no encontrados",
            "Faltan 0notas",
            "0celdas reemplazadas",
        ]
    )
    with page.expect_download() as descarga:
        page.get_by_role("link", name="Descargar plantilla").click()
    assert descarga.value.suggested_filename == NOMBRE_ARCHIVO
    with open(descarga.value.path(), "rb") as completada:
        assert load_workbook(io.BytesIO(completada.read()))["063-MATE"]["D3"].value == "B"


def test_subir_otra_plantilla_abre_el_dialogo_vacio(inicio):
    """Escenario «Subir otra»."""
    page = inicio
    completar_con(page, plantilla())
    expect(resumen(page)).to_be_visible()

    page.get_by_role("button", name="Subir otra plantilla").click()

    expect(dialogo(page)).to_be_visible()
    expect(page.locator("[data-archivo-nombre]")).to_have_text("Elige tu plantilla")
    expect(completar(page)).to_be_disabled()


# --- Elegir la sección y corregir la equivalencia ---


def test_elige_la_seccion_completa_sin_volver_a_elegir_el_archivo_y_la_corrige(inicio):
    """Escenarios «El nombre no coincide», «Guardar y completar» y «Borrar una equivalencia»."""
    page = inicio
    envios = []
    page.on("request", lambda r: envios.append(r) if r.method == "POST" else None)

    archivo = plantilla(nombre_seccion="TRIUNFADORES")
    completar_con(page, archivo, "RegNotas_2_TRIUNFADORES_B3.xlsx")

    expect(dialogo(page).get_by_role("heading", name="Elige la sección")).to_be_focused()
    expect(dialogo(page)).to_contain_text("2.º TRIUNFADORES · Tercer bimestre 2027")
    opciones = dialogo(page).get_by_role("radio")
    expect(opciones).to_have_count(4)
    for n in range(4):
        expect(opciones.nth(n)).not_to_be_checked()
    guardar = dialogo(page).get_by_role("button", name="Guardar y completar")
    expect(guardar).to_be_disabled()
    dialogo(page).get_by_label("2.º B").check()
    expect(guardar).to_be_enabled()
    guardar.click()

    expect(resumen(page)).to_be_visible()
    assert EquivalenciaSeccion.objects.get().seccion.nombre == "B"
    # El archivo no se guardó entre pasos: el segundo envío lo trae otra vez (el servidor completó
    # la plantilla sin que la prueba lo volviera a elegir) y va por multipart.
    assert len(envios) == 2
    assert all(e.headers["content-type"].startswith("multipart/form-data") for e in envios)

    page.get_by_role("button", name="¿No es esta sección?").click()

    expect(page.get_by_text(AVISO_BORRADA)).to_be_focused()
    expect(page.get_by_role("link", name="Descargar plantilla")).to_have_count(0)
    expect(page.get_by_role("button", name="¿No es esta sección?")).to_have_count(0)
    expect(page.get_by_role("button", name="Subir plantilla otra vez")).to_be_visible()
    assert not EquivalenciaSeccion.objects.exists()


def descarga_viva(page):
    """El Blob del enlace sigue vivo: ``fetch`` de una URL revocada falla."""
    return page.evaluate(
        """() => fetch(document.querySelector("[data-archivo]").href)
            .then((r) => r.ok, () => false)"""
    )


def test_un_borrado_lento_no_toca_la_descarga_de_la_exportacion_siguiente(inicio):
    """Hallazgo de Codex (parte D): la respuesta del borrado llega después de otra exportación."""
    page = inicio
    retenidas = []
    page.route(URL_BORRAR, lambda ruta: retenidas.append(ruta))
    archivo = plantilla(nombre_seccion="TRIUNFADORES")
    completar_con(page, archivo, "RegNotas_2_TRIUNFADORES_B3.xlsx")
    dialogo(page).get_by_label("2.º B").check()
    dialogo(page).get_by_role("button", name="Guardar y completar").click()
    expect(resumen(page)).to_be_visible()

    with page.expect_request(URL_BORRAR):
        page.get_by_role("button", name="¿No es esta sección?").click()
    # La siguiente se completa por el nombre («B»): su resumen no trae «¿No es esta sección?».
    page.get_by_role("button", name="Subir otra plantilla").click()
    elegir(page, plantilla(), NOMBRE_ARCHIVO)
    completar(page).click()
    expect(page.get_by_role("button", name="¿No es esta sección?")).to_have_count(0)
    expect(page.get_by_role("link", name="Descargar plantilla")).to_be_visible()
    assert descarga_viva(page)

    assert len(retenidas) == 1
    with page.expect_response(URL_BORRAR):
        retenidas[0].continue_()

    expect(page.get_by_role("link", name="Descargar plantilla")).to_be_visible()
    expect(page.get_by_text("Quitamos la equivalencia.")).to_have_count(0)
    assert descarga_viva(page)


def test_cancelar_la_eleccion_no_guarda_la_equivalencia(inicio):
    """Escenario «Cancelar la elección»."""
    page = inicio
    completar_con(page, plantilla(nombre_seccion="TRIUNFADORES"))
    expect(dialogo(page).get_by_role("heading", name="Elige la sección")).to_be_visible()

    dialogo(page).get_by_role("button", name="Cancelar").click()

    expect(dialogo(page)).to_be_hidden()
    expect(boton_subir(page)).to_be_focused()
    assert not EquivalenciaSeccion.objects.exists()


# --- Rechazo y corte de red ---


def test_el_rechazo_deja_el_foco_en_el_mensaje_y_conserva_el_nombre(inicio):
    """Escenarios «Otro Excel» y «Otro tipo con nombre de Excel»."""
    page = inicio

    completar_con(page, b"%PDF-1.4 no es un libro", "Listado_2do.xlsx")

    error = page.locator("#archivo-error")
    expect(error).to_be_visible()
    expect(error).to_be_focused()
    expect(error).to_contain_text("El archivo no corresponde a la plantilla de notas del SIAGIE")
    expect(error).to_contain_text("Elige el Excel que descargaste en «Periodo por Excel».")
    expect(page.locator("[data-ruta-siagie]")).to_contain_text(
        "Evaluación → Registro de calificaciones → Periodo por Excel"
    )
    expect(page.locator("[data-archivo-nombre]")).to_have_text("Listado_2do.xlsx")
    expect(dialogo(page)).to_be_visible()

    # Se puede elegir otro archivo en el mismo diálogo.
    elegir(page, plantilla())
    expect(error).to_be_hidden()
    completar(page).click()
    expect(resumen(page)).to_be_visible()


def test_un_periodo_sin_notas_no_trae_la_ayuda_del_siagie(inicio):
    """Escenario «Periodo sin notas»."""
    page = inicio

    completar_con(page, plantilla(periodo="B4", texto_periodo="CUARTO BIMESTRE"))

    error = page.locator("#archivo-error")
    expect(error).to_contain_text("No hay notas para completar en este periodo")
    expect(error.locator("[data-error-ayuda]")).to_be_hidden()
    expect(page.locator("[data-ruta-siagie]")).to_be_hidden()


def test_el_corte_de_red_conserva_el_archivo_y_se_reintenta_sin_elegirlo(inicio):
    """Escenarios «Se corta la red» y «Procesando»."""
    page = inicio
    page.route(URL_ENVIO, lambda ruta: ruta.abort())

    completar_con(page, plantilla())

    aviso = page.locator("[data-error-red]")
    expect(aviso).to_be_visible()
    expect(aviso).to_be_focused()
    expect(aviso).to_contain_text(
        "Se cortó la conexión. Tu archivo sigue aquí: revisa tu conexión e inténtalo de nuevo."
    )
    expect(page.locator("[data-archivo-nombre]")).to_have_text(NOMBRE_ARCHIVO)
    expect(completar(page)).to_be_enabled()

    page.unroute(URL_ENVIO)
    completar(page).click()

    expect(resumen(page)).to_be_visible()


# --- 360 px y accesibilidad ---


def test_el_resumen_con_un_nombre_largo_no_se_desplaza_en_horizontal_a_360_px(inicio):
    """Escenario «360 px»."""
    page = inicio
    con_pantalla(page, 360, "light")

    completar_con(page, plantilla(nombres=["PEREZ QUISPE, MARIA", NOMBRE_60]))

    expect(resumen(page)).to_be_visible()
    expect(page.get_by_role("heading", level=1)).to_have_text(
        "Plantilla completada con observaciones"
    )
    expect(page.locator(".lista-nombres li")).to_have_text([NOMBRE_60])
    ancho = page.evaluate(
        "() => [document.documentElement.scrollWidth, document.documentElement.clientWidth]"
    )
    assert ancho[0] <= ancho[1]


@pytest.mark.parametrize("tema", TEMAS)
def test_axe_en_el_dialogo_con_error_el_paso_de_la_seccion_y_el_resumen(inicio, tema):
    """Escenario «Accesibilidad»: los tres estados, en cada tema."""
    page = inicio
    con_pantalla(page, 1280, tema)

    completar_con(page, b"%PDF-1.4 no es un libro", "Listado_2do.xlsx")
    expect(page.locator("#archivo-error")).to_be_visible()
    revisar_con_axe(page, f"plantilla-error-{tema}")

    elegir(page, plantilla(nombre_seccion="TRIUNFADORES"))
    completar(page).click()
    expect(dialogo(page).get_by_role("heading", name="Elige la sección")).to_be_visible()
    dialogo(page).get_by_label("2.º B").check()
    quieto(page)
    revisar_con_axe(page, f"plantilla-seccion-{tema}")

    dialogo(page).get_by_role("button", name="Guardar y completar").click()
    expect(resumen(page)).to_be_visible()
    revisar_con_axe(page, f"plantilla-resumen-{tema}")
