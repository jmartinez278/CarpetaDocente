"""Asistencia de hoy en el navegador (spec asistencia-jornada; design de US-030, D3, D4 y D7).

El toque cicla el estado y lo guarda solo, una petición por fila sin abortar (gana el último toque),
la franja dice "Guardando…" y "✓ Guardado", el avance y los totales cambian con cada toque y la
nota se guarda al salir del campo. Cada guardado se cuenta en la base. Necesita el CSS compilado y
Chromium: ``uv run pytest -m e2e --browser chromium``.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from playwright.sync_api import expect

from asistencia.models import Asistencia, Jornada
from cuentas.tests.e2e import (
    ANCHOS,
    TEMAS,
    con_pantalla,
    fijar_hora_de_lima,
    ingresar,
    revisar_con_axe,
)

pytestmark = pytest.mark.e2e

MIERCOLES = datetime(2026, 10, 28, 9, 0, tzinfo=ZoneInfo("America/Lima"))
TOQUES = {"ASISTIO": 1, "FALTO": 2, "TARDE": 3, "JUSTIFICADO": 4}
# El día del spec: 21 Asistió, 1 Tarde, 2 Faltó y 1 Justificado.
DIA_DEL_SPEC = ["ASISTIO"] * 21 + ["TARDE", "FALTO", "FALTO", "JUSTIFICADO"]


@pytest.fixture
def seccion_de_ana(monkeypatch, seccion, docente, veinticinco):
    """Un miércoles a las 9:00 de Lima, con los 25 estudiantes del boceto en la sección de Ana."""
    fijar_hora_de_lima(monkeypatch, MIERCOLES)
    seccion.docente = docente
    seccion.save()
    return seccion


@pytest.fixture
def abrir_asistencia(live_server, page, docente, clave, seccion_de_ana):
    def abrir(ancho=360, tema="light"):
        con_pantalla(page, ancho, tema)
        ingresar(page, live_server, docente, clave)
        page.wait_for_url(f"{live_server.url}/docente/")
        page.goto(url_asistencia(live_server, seccion_de_ana))
        return page

    return abrir


def url_asistencia(live_server, seccion):
    return f"{live_server.url}/docente/secciones/{seccion.pk}/asistencia/"


def circulo(page, estudiante):
    return page.locator(f"#fila-{estudiante.pk} [data-marcar]")


def tocar(page, estudiante, veces=1):
    for _ in range(veces):
        circulo(page, estudiante).click()


def guardado(page):
    """El estado del guardado que se ve: la franja en el celular, el panel en PC."""
    return page.locator("[data-guardado]:visible")


def esperar_guardado(page):
    expect(guardado(page)).to_have_text("Guardado")


def estados_en_la_base():
    return {a.estudiante_id: a.estado for a in Asistencia.objects.all()}


def test_camino_ideal(abrir_asistencia, veinticinco):
    page = abrir_asistencia()
    expect(page.get_by_role("button", name="Guardar")).to_have_count(0)

    for estudiante, estado in zip(veinticinco, DIA_DEL_SPEC, strict=True):
        tocar(page, estudiante, TOQUES[estado])
    esperar_guardado(page)

    expect(page.locator("[data-resumen-completo]:visible")).to_have_text(
        "Asistió: 21 · Tarde: 1 · Faltó: 2 · Justificado: 1"
    )
    assert Jornada.objects.count() == 1
    assert estados_en_la_base() == {
        e.pk: estado for e, estado in zip(veinticinco, DIA_DEL_SPEC, strict=True)
    }


def test_el_avance_y_los_totales_cambian_con_cada_toque(abrir_asistencia, veinticinco):
    page = abrir_asistencia(1280)

    tocar(page, veinticinco[0])
    tocar(page, veinticinco[1], 2)

    panel = page.locator(".panel-jornada")
    expect(panel.locator("[data-marcados]")).to_have_text("2")
    expect(panel.locator("[data-sin-marcar]")).to_have_text("23 sin marcar")
    expect(panel.locator('[data-total="ASISTIO"]')).to_have_text("1")
    expect(panel.locator('[data-total="FALTO"]')).to_have_text("1")
    expect(panel.locator("[data-progreso]")).to_have_attribute("value", "2")
    expect(panel.locator("[data-marcar-todos]")).to_have_text(
        "Marcar los 23 restantes como Asistió"
    )
    fila = page.locator(f"#fila-{veinticinco[1].pk}")
    expect(fila.locator("[data-etiqueta]")).to_have_text("Faltó")
    expect(circulo(page, veinticinco[1])).to_have_accessible_name(
        "ALARCÓN HUAMÁN, DIEGO ALONSO: Faltó. Cambiar a Tarde"
    )
    esperar_guardado(page)


def test_volver_a_abrir_muestra_lo_guardado(
    abrir_asistencia, live_server, seccion_de_ana, veinticinco
):
    page = abrir_asistencia()
    for estudiante in veinticinco[:10]:
        tocar(page, estudiante, 2)
    esperar_guardado(page)

    page.goto(url_asistencia(live_server, seccion_de_ana))

    for estudiante in veinticinco[:10]:
        expect(page.locator(f"#fila-{estudiante.pk} [data-etiqueta]")).to_have_text("Faltó")
    for estudiante in veinticinco[10:]:
        expect(page.locator(f"#fila-{estudiante.pk} [data-etiqueta]")).to_have_text("Sin marcar")
    expect(page.locator("[data-marcados]:visible")).to_have_text("10")


def test_toques_rapidos_mientras_se_guarda(abrir_asistencia, veinticinco):
    page = abrir_asistencia()
    retenidas = []
    enviados = []

    def retener_la_primera(route):
        enviados.append(route.request.post_data)
        if len(enviados) == 1:
            retenidas.append(route)
        else:
            route.continue_()

    page.route("**/estudiantes/*/", retener_la_primera)

    tocar(page, veinticinco[0], 3)
    expect(page.locator(f"#fila-{veinticinco[0].pk} [data-etiqueta]")).to_have_text("Tarde")
    page.wait_for_timeout(300)
    assert len(enviados) == 1, "una sola petición en curso por fila"

    retenidas[0].continue_()
    esperar_guardado(page)

    assert estados_en_la_base() == {veinticinco[0].pk: "TARDE"}
    assert len(enviados) == 2, "la segunda lleva el último toque, sin pasar por Faltó"
    assert "estado=TARDE" in enviados[1]


def test_guardado_sano(abrir_asistencia, veinticinco):
    page = abrir_asistencia()
    retenidas = []
    page.route("**/estudiantes/*/", lambda route: retenidas.append(route))
    expect(guardado(page)).to_have_text("Sin cambios")

    tocar(page, veinticinco[0])

    expect(guardado(page)).to_have_text("Guardando…")
    retenidas[0].continue_()
    esperar_guardado(page)
    expect(page.get_by_text("sin guardar")).to_have_count(0)
    expect(page.locator("[data-fallo]:visible")).to_have_count(0)


def test_la_nota_se_guarda_al_salir_del_campo(abrir_asistencia, veinticinco):
    page = abrir_asistencia()
    estudiante = veinticinco[3]
    campo = page.locator(f"#nota-{estudiante.pk}")
    expect(campo).to_be_hidden()

    tocar(page, estudiante, 4)
    expect(campo).to_be_visible()
    expect(circulo(page, estudiante)).to_be_focused()
    campo.fill("Constancia entregada a la docente")
    expect(page.locator(f"#fila-{estudiante.pk} [data-contador]")).to_have_text("33")
    campo.press("Tab")
    esperar_guardado(page)

    asistencia = Asistencia.objects.get(estudiante=estudiante)
    assert (asistencia.estado, asistencia.nota_justificacion) == (
        "JUSTIFICADO",
        "Constancia entregada a la docente",
    )

    tocar(page, estudiante)
    expect(campo).to_be_hidden()
    esperar_guardado(page)
    asistencia.refresh_from_db()
    assert (asistencia.estado, asistencia.nota_justificacion) == ("ASISTIO", "")


def test_la_nota_se_guarda_sola_al_dejar_de_escribir(abrir_asistencia, veinticinco):
    page = abrir_asistencia()
    estudiante = veinticinco[3]
    tocar(page, estudiante, 4)
    esperar_guardado(page)

    page.locator(f"#nota-{estudiante.pk}").press_sequentially("Constancia")
    expect(guardado(page)).to_have_text("Guardando…")
    esperar_guardado(page)

    assert Asistencia.objects.get(estudiante=estudiante).nota_justificacion == "Constancia"


def test_intro_y_espacio_en_el_circulo(abrir_asistencia, veinticinco):
    page = abrir_asistencia(1280)
    boton = circulo(page, veinticinco[0])
    boton.focus()

    page.keyboard.press("Enter")
    expect(boton).to_have_accessible_name("AGUILAR FLORES, LUCIANA: Asistió. Cambiar a Faltó")
    page.keyboard.press(" ")
    expect(boton).to_have_accessible_name("AGUILAR FLORES, LUCIANA: Faltó. Cambiar a Tarde")
    esperar_guardado(page)

    assert estados_en_la_base() == {veinticinco[0].pk: "FALTO"}


@pytest.mark.parametrize("tema", TEMAS)
@pytest.mark.parametrize("ancho", ANCHOS)
def test_la_lista_a_medio_marcar_pasa_axe(abrir_asistencia, veinticinco, ancho, tema):
    page = abrir_asistencia(ancho, tema)
    tocar(page, veinticinco[0])
    tocar(page, veinticinco[1], 4)
    tocar(page, veinticinco[2], 3)
    esperar_guardado(page)

    revisar_con_axe(page, f"asistencia-a-medio-marcar-{ancho}-{tema}")
    assert page.evaluate("document.documentElement.scrollWidth") <= ancho


def test_n_sin_marcar_lleva_a_la_primera_fila_sin_marcar(abrir_asistencia, veinticinco):
    page = abrir_asistencia()
    for estudiante in veinticinco[:18]:
        tocar(page, estudiante)
    esperar_guardado(page)
    page.evaluate("window.scrollTo(0, 0)")

    page.locator("[data-sin-marcar]:visible").click()

    boton = circulo(page, veinticinco[18])
    expect(boton).to_be_focused()
    expect(boton).to_be_in_viewport()
    # Ni la barra ni la franja fija lo tapan.
    franja = page.locator(".controles").bounding_box()
    assert boton.bounding_box()["y"] >= franja["y"] + franja["height"]


@pytest.fixture
def sabado(monkeypatch):
    fijar_hora_de_lima(monkeypatch, datetime(2026, 10, 31, 9, 0, tzinfo=ZoneInfo("America/Lima")))


@pytest.mark.parametrize("tema", TEMAS)
@pytest.mark.parametrize("ancho", ANCHOS)
def test_el_fin_de_semana_pasa_axe(abrir_asistencia, sabado, ancho, tema):
    page = abrir_asistencia(ancho, tema)
    expect(page.get_by_text("Hoy no hay clases")).to_be_visible()

    revisar_con_axe(page, f"asistencia-fin-de-semana-{ancho}-{tema}")
    assert page.evaluate("document.documentElement.scrollWidth") <= ancho


@pytest.mark.parametrize("tema", TEMAS)
@pytest.mark.parametrize("ancho", ANCHOS)
def test_la_seccion_sin_estudiantes_pasa_axe(abrir_asistencia, seccion_de_ana, ancho, tema):
    seccion_de_ana.estudiantes.all().delete()
    page = abrir_asistencia(ancho, tema)
    expect(page.get_by_text("Tu sección aún no tiene estudiantes")).to_be_visible()

    revisar_con_axe(page, f"asistencia-sin-estudiantes-{ancho}-{tema}")
    assert page.evaluate("document.documentElement.scrollWidth") <= ancho
