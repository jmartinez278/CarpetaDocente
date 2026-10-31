"""Periodos en la ficha del año, en el navegador (spec periodos-anio-escolar; design de US-028, D5).

El Administrador llena los 4 bimestres y guarda; un cruce se muestra junto a la fila; la ficha con
filas vacías, con el error y de solo lectura (año CERRADO) pasa axe en ambos temas a 360 y 1280 px
y no se desplaza en horizontal a 360 px. Necesita el CSS compilado y Chromium; se pide con
``uv run pytest -m e2e --browser chromium`` y ``DJANGO_ALLOW_ASYNC_UNSAFE=true``.
"""

import pytest
from playwright.sync_api import expect

from cuentas.tests.e2e import ANCHOS, TEMAS, con_pantalla, ingresar, revisar_con_axe
from institucion.models import MENSAJE_CRUCE, AnioEscolar, Institucion, Periodo

pytestmark = pytest.mark.e2e

BIMESTRES = [
    ("2027-03-16", "2027-05-15"),
    ("2027-05-25", "2027-07-24"),
    ("2027-08-10", "2027-10-09"),
    ("2027-10-19", "2027-12-18"),
]


@pytest.fixture
def anio(anio_abierto):
    institucion = anio_abierto.institucion
    institucion.organizacion_periodos = Institucion.OrganizacionPeriodos.BIMESTRE
    institucion.save()
    return anio_abierto


@pytest.fixture
def anio_cerrado(anio):
    for numero, (inicio, fin) in enumerate(BIMESTRES, start=1):
        Periodo.objects.create(anio_escolar=anio, numero=numero, fecha_inicio=inicio, fecha_fin=fin)
    AnioEscolar.objects.filter(pk=anio.pk).update(estado=AnioEscolar.Estado.CERRADO)
    return anio


def abrir_ficha(page, live_server, anio):
    page.goto(f"{live_server.url}/admin/institucion/anioescolar/{anio.pk}/change/")
    expect(page.locator("#periodos-group")).to_be_visible()
    page.evaluate("document.fonts.ready")


def llenar(page, filas):
    for indice, (inicio, fin) in enumerate(filas):
        page.locator(f"#id_periodos-{indice}-fecha_inicio").fill(inicio)
        page.locator(f"#id_periodos-{indice}-fecha_fin").fill(fin)


def guardar(page):
    page.get_by_role("button", name="Guardar", exact=True).click()


def test_el_administrador_llena_los_cuatro_bimestres_y_guarda(
    live_server, page, administrador, anio, clave
):
    ingresar(page, live_server, administrador, clave)
    abrir_ficha(page, live_server, anio)
    expect(page.locator("#periodos-group tbody tr.form-row:not(.empty-form)")).to_have_count(4)

    llenar(page, BIMESTRES)
    guardar(page)

    expect(page.locator(".messagelist")).to_be_visible()
    assert anio.periodos.count() == 4


def test_un_cruce_muestra_el_mensaje_junto_a_la_fila(live_server, page, administrador, anio, clave):
    ingresar(page, live_server, administrador, clave)
    abrir_ficha(page, live_server, anio)
    cruzados = [BIMESTRES[0], ("2027-05-01", "2027-07-24"), *BIMESTRES[2:]]

    llenar(page, cruzados)
    guardar(page)

    expect(page.locator("#periodos-group .errorlist")).to_contain_text(MENSAJE_CRUCE)
    assert not anio.periodos.exists()


@pytest.mark.parametrize("ancho", ANCHOS)
@pytest.mark.parametrize("tema", TEMAS)
def test_la_ficha_con_filas_vacias_pasa_axe(
    live_server, page, administrador, anio, clave, ancho, tema
):
    con_pantalla(page, ancho, tema)
    ingresar(page, live_server, administrador, clave)
    abrir_ficha(page, live_server, anio)

    revisar_con_axe(page, f"periodos-vacios-{ancho}-{tema}")


@pytest.mark.parametrize("ancho", ANCHOS)
@pytest.mark.parametrize("tema", TEMAS)
def test_la_ficha_con_el_error_pasa_axe(live_server, page, administrador, anio, clave, ancho, tema):
    con_pantalla(page, ancho, tema)
    ingresar(page, live_server, administrador, clave)
    abrir_ficha(page, live_server, anio)
    llenar(page, [BIMESTRES[0], ("2027-05-01", "2027-07-24"), *BIMESTRES[2:]])
    guardar(page)
    expect(page.locator("#periodos-group .errorlist")).to_be_visible()

    revisar_con_axe(page, f"periodos-error-{ancho}-{tema}")


@pytest.mark.parametrize("ancho", ANCHOS)
@pytest.mark.parametrize("tema", TEMAS)
def test_la_ficha_de_un_anio_cerrado_pasa_axe(
    live_server, page, administrador, anio_cerrado, clave, ancho, tema
):
    con_pantalla(page, ancho, tema)
    ingresar(page, live_server, administrador, clave)
    abrir_ficha(page, live_server, anio_cerrado)

    revisar_con_axe(page, f"periodos-cerrado-{ancho}-{tema}")


@pytest.mark.parametrize("tema", TEMAS)
def test_a_360_px_la_ficha_no_se_desplaza_en_horizontal(
    live_server, page, administrador, anio, clave, tema
):
    con_pantalla(page, 360, tema)
    ingresar(page, live_server, administrador, clave)
    abrir_ficha(page, live_server, anio)

    assert page.evaluate("document.documentElement.scrollWidth") <= 360
