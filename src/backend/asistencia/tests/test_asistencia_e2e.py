"""Asistencia de hoy en el navegador (spec asistencia-jornada; design de US-030, D3, D4 y D7).

El toque cicla el estado y lo guarda solo, una petición por fila sin abortar (gana el último toque),
la franja dice "Guardando…" y "✓ Guardado", el avance y los totales cambian con cada toque y la
nota se guarda al salir del campo. Cada guardado se cuenta en la base. Necesita el CSS compilado y
Chromium: ``uv run pytest -m e2e --browser chromium``.
"""

import re
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from playwright.sync_api import expect

from asistencia.models import Asistencia, Jornada
from cuentas.tests.e2e import (
    ANCHOS,
    TEMAS,
    boton_ingresar,
    campo_clave,
    campo_usuario,
    con_pantalla,
    envejecer_sesion,
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


# --- Parte C: lote, cortes de red, aviso al salir, sesión vencida y cierre (D3, D5, D6 y D8) ---


def marcar_restantes(page):
    page.locator("[data-marcar-todos]:visible").click()


def barra(page):
    return page.locator("[data-barra-deshacer]")


def boton_deshacer(page):
    return barra(page).get_by_role("button", name="Deshacer")


def anuncio(page):
    return page.locator("#anuncio")


def cierre(page):
    return page.locator("[data-cierre]:visible")


def fila(page, estudiante):
    return page.locator(f"#fila-{estudiante.pk}")


def etiqueta(page, estudiante):
    return fila(page, estudiante).locator("[data-etiqueta]")


def esperar_retenida(page, retenidas):
    """El manejador de ``page.route`` corre en otro momento: se espera a que retenga la petición."""
    for _ in range(50):
        if retenidas:
            return retenidas[0]
        page.wait_for_timeout(100)
    pytest.fail("ninguna petición llegó a la ruta")


def esperar_en_la_base(page, condicion, mensaje):
    """La base la escribe el live_server: se consulta hasta que se cumple (o 10 s)."""
    for _ in range(100):
        if condicion():
            return
        page.wait_for_timeout(100)
    pytest.fail(mensaje)


def test_flujo_alternativo_valido(abrir_asistencia, veinticinco):
    page = abrir_asistencia()
    marcar_restantes(page)
    expect(barra(page)).to_be_visible()
    expect(barra(page)).to_contain_text("25 marcados como Asistió")
    expect(guardado(page)).to_have_text("Pendiente de deshacer")
    assert Asistencia.objects.count() == 0, "el lote no se guarda hasta que acaba la cuenta"

    expect(barra(page)).to_be_hidden(timeout=8000)
    esperar_guardado(page)
    tocar(page, veinticinco[3])
    tocar(page, veinticinco[7], 2)
    esperar_guardado(page)

    esperados = {e.pk: "ASISTIO" for e in veinticinco}
    esperados[veinticinco[3].pk] = "FALTO"
    esperados[veinticinco[7].pk] = "TARDE"
    assert estados_en_la_base() == esperados


def test_marcar_los_restantes_no_toca_a_los_ya_marcados(abrir_asistencia, veinticinco):
    page = abrir_asistencia()
    for estudiante in veinticinco[:18]:
        tocar(page, estudiante, 2)
    esperar_guardado(page)
    expect(page.locator("[data-marcar-todos]:visible")).to_have_text(
        "Marcar los 7 restantes como Asistió"
    )

    marcar_restantes(page)
    expect(barra(page)).to_contain_text("7 marcados como Asistió")
    expect(page.locator("[data-marcar-todos]:visible")).to_have_count(0)
    expect(barra(page)).to_be_hidden(timeout=8000)
    esperar_guardado(page)

    estados = estados_en_la_base()
    assert [estados[e.pk] for e in veinticinco[:18]] == ["FALTO"] * 18
    assert [estados[e.pk] for e in veinticinco[18:]] == ["ASISTIO"] * 7


def test_deshacer_no_guarda_nada(abrir_asistencia, veinticinco):
    page = abrir_asistencia()
    marcar_restantes(page)
    expect(etiqueta(page, veinticinco[0])).to_have_text("Asistió")
    expect(boton_deshacer(page)).to_be_focused()

    boton_deshacer(page).click()

    expect(barra(page)).to_be_hidden()
    expect(guardado(page)).to_have_text("Sin cambios")
    for estudiante in veinticinco:
        expect(etiqueta(page, estudiante)).to_have_text("Sin marcar")
    expect(page.locator("[data-marcar-todos]:visible")).to_have_text(
        "Marcar los 25 restantes como Asistió"
    )
    # El foco vuelve a "Marcar…" al cerrarse la barra.
    expect(page.locator("[data-marcar-todos]:visible")).to_be_focused()
    page.wait_for_timeout(6000)
    assert Asistencia.objects.count() == 0
    assert Jornada.objects.count() == 0


def test_fin_de_la_cuenta_y_su_anuncio(abrir_asistencia, veinticinco):
    page = abrir_asistencia()
    marcar_restantes(page)
    expect(anuncio(page)).to_have_text(
        "25 marcados como Asistió. Puedes deshacer durante 5 segundos"
    )
    expect(barra(page).locator("[data-segundos]")).to_have_attribute("aria-hidden", "true")
    assert barra(page).get_attribute("aria-live") is None

    expect(anuncio(page)).to_have_text("25 guardados como Asistió", timeout=8000)
    expect(barra(page)).to_be_hidden()
    assert estados_en_la_base() == {e.pk: "ASISTIO" for e in veinticinco}


def test_toque_durante_la_cuenta(abrir_asistencia, veinticinco):
    page = abrir_asistencia()
    marcar_restantes(page)

    tocar(page, veinticinco[0])
    expect(etiqueta(page, veinticinco[0])).to_have_text("Faltó")
    expect(barra(page)).to_contain_text("24 marcados como Asistió")
    boton_deshacer(page).click()

    expect(etiqueta(page, veinticinco[0])).to_have_text("Faltó")
    for estudiante in veinticinco[1:]:
        expect(etiqueta(page, estudiante)).to_have_text("Sin marcar")
    esperar_guardado(page)
    page.wait_for_timeout(6000)
    assert estados_en_la_base() == {veinticinco[0].pk: "FALTO"}


def test_cerrar_la_pagina_durante_la_cuenta_guarda_el_lote(abrir_asistencia, veinticinco):
    page = abrir_asistencia()
    tocar(page, veinticinco[0], 2)
    esperar_guardado(page)
    marcar_restantes(page)
    expect(barra(page)).to_be_visible()
    otra = page.context.new_page()

    page.on("dialog", lambda dialogo: dialogo.accept())
    page.close(run_before_unload=True)

    esperar_en_la_base(
        otra, lambda: Asistencia.objects.count() == 25, "el lote no se guardó al cerrar la página"
    )
    esperados = {e.pk: "ASISTIO" for e in veinticinco}
    esperados[veinticinco[0].pk] = "FALTO"
    assert estados_en_la_base() == esperados


def test_la_cuenta_se_pausa_con_el_puntero(abrir_asistencia, veinticinco):
    page = abrir_asistencia()
    marcar_restantes(page)
    boton_deshacer(page).hover()
    segundos = barra(page).locator("[data-segundos]").text_content()

    page.wait_for_timeout(2500)
    expect(barra(page).locator("[data-segundos]")).to_have_text(segundos)
    assert Asistencia.objects.count() == 0

    page.mouse.move(5, 5)
    expect(barra(page)).to_be_hidden(timeout=8000)
    esperar_guardado(page)
    assert Asistencia.objects.count() == 25


def test_la_cuenta_se_pausa_con_el_foco_de_teclado(abrir_asistencia, veinticinco):
    page = abrir_asistencia(1280)
    page.locator("[data-marcar-todos]:visible").focus()
    page.keyboard.press("Enter")
    expect(boton_deshacer(page)).to_be_focused()
    # El foco que pone la pantalla no detiene la cuenta; el que llega con el teclado, sí.
    page.keyboard.press("Shift+Tab")
    page.keyboard.press("Tab")
    expect(boton_deshacer(page)).to_be_focused()
    segundos = barra(page).locator("[data-segundos]").text_content()

    page.wait_for_timeout(2500)
    expect(barra(page).locator("[data-segundos]")).to_have_text(segundos)
    assert Asistencia.objects.count() == 0


def test_el_foco_que_pone_la_pantalla_no_pausa_la_cuenta(abrir_asistencia, veinticinco):
    page = abrir_asistencia(1280)
    page.locator("[data-marcar-todos]:visible").focus()
    page.keyboard.press("Enter")
    expect(boton_deshacer(page)).to_be_focused()

    expect(barra(page)).to_be_hidden(timeout=8000)
    esperar_guardado(page)
    assert Asistencia.objects.count() == 25


def test_diez_cortes_de_red_sin_perder_ni_duplicar(abrir_asistencia, veinticinco):
    page = abrir_asistencia()
    esperados = {}
    for vuelta, estudiante in enumerate(veinticinco[:10]):
        page.context.set_offline(True)
        toques = vuelta % 4 + 1
        tocar(page, estudiante, toques)
        esperados[estudiante.pk] = list(TOQUES)[toques - 1]
        fallo = fila(page, estudiante).locator("[data-fallo]")
        expect(fallo).to_be_visible()
        expect(fallo).to_contain_text("sin guardar. Reintentando…")
        page.context.set_offline(False)
        expect(fallo).to_be_hidden()
        # Un toque con la red sana entre corte y corte.
        tocar(page, veinticinco[10 + vuelta])
        esperados[veinticinco[10 + vuelta].pk] = "ASISTIO"
    esperar_guardado(page)

    assert estados_en_la_base() == esperados
    assert Asistencia.objects.count() == 20
    assert Jornada.objects.count() == 1


def test_fallo_de_un_guardado(abrir_asistencia, veinticinco):
    page = abrir_asistencia()
    page.context.set_offline(True)

    tocar(page, veinticinco[0])

    fallo = fila(page, veinticinco[0]).locator("[data-fallo]")
    expect(fallo).to_have_text("Asistió · sin guardar. Reintentando…")
    expect(circulo(page, veinticinco[0])).to_have_accessible_description(
        "Asistió · sin guardar. Reintentando…"
    )
    expect(page.locator("[data-sin-guardar]:visible")).to_have_text("1 sin guardar")
    expect(page.locator("[data-sin-conexion]:visible")).to_have_count(0)

    page.context.set_offline(False)
    esperar_guardado(page)
    expect(page.locator("[data-sin-guardar]:visible")).to_have_count(0)
    assert estados_en_la_base() == {veinticinco[0].pk: "ASISTIO"}


def test_volver_al_estado_guardado_tras_un_fallo_se_guarda(abrir_asistencia, veinticinco):
    # Tras un fallo no se sabe qué guardó el servidor: la fila se reenvía aunque la pantalla vuelva
    # a mostrar el último estado confirmado.
    page = abrir_asistencia()
    tocar(page, veinticinco[0])
    esperar_guardado(page)
    page.context.set_offline(True)

    tocar(page, veinticinco[0], 4)
    expect(etiqueta(page, veinticinco[0])).to_have_text("Asistió")
    expect(fila(page, veinticinco[0]).locator("[data-fallo]")).to_be_visible()

    page.context.set_offline(False)
    esperar_guardado(page)
    expect(fila(page, veinticinco[0]).locator("[data-fallo]")).to_be_hidden()
    expect(page.locator("[data-sin-guardar]:visible")).to_have_count(0)
    assert estados_en_la_base() == {veinticinco[0].pk: "ASISTIO"}


def test_el_lote_no_sale_dos_veces_al_volver_la_red(abrir_asistencia, veinticinco):
    page = abrir_asistencia()
    retenidas = []
    page.route("**/restantes/", lambda route: retenidas.append(route))
    marcar_restantes(page)
    lote = esperar_retenida(page, retenidas)

    # Vuelve la red con el lote todavía en camino: no sale otro.
    page.context.set_offline(True)
    page.context.set_offline(False)
    page.wait_for_timeout(500)
    assert len(retenidas) == 1

    lote.continue_()
    page.unroute("**/restantes/")
    expect(anuncio(page)).to_have_text("25 guardados como Asistió")
    page.wait_for_timeout(500)
    expect(anuncio(page)).not_to_have_text("0 guardados como Asistió")
    expect(page.locator("[data-sin-conexion]:visible")).to_have_count(0)
    assert estados_en_la_base() == {e.pk: "ASISTIO" for e in veinticinco}


@pytest.mark.parametrize("ancho", ANCHOS)
def test_sin_conexion_solo_al_tercer_fallo_y_una_vez(abrir_asistencia, veinticinco, ancho):
    page = abrir_asistencia(ancho)
    # Cuenta las veces que un aviso pasa de oculto a visible.
    page.evaluate(
        """() => {
          window.avisosSinConexion = 0;
          const observador = new MutationObserver((cambios) => {
            for (const c of cambios) {
              if (c.oldValue !== null && !c.target.hidden) window.avisosSinConexion++;
            }
          });
          const opciones = { attributeFilter: ['hidden'], attributeOldValue: true };
          for (const el of document.querySelectorAll('[data-sin-conexion]')) {
            observador.observe(el, opciones);
          }
        }"""
    )
    aviso = page.locator("[data-sin-conexion]:visible")
    page.context.set_offline(True)

    tocar(page, veinticinco[0])
    tocar(page, veinticinco[1])
    expect(page.locator("[data-sin-guardar]:visible")).to_have_text("2 sin guardar")
    expect(aviso).to_have_count(0)
    tocar(page, veinticinco[2])
    expect(aviso).to_have_count(1)
    expect(aviso).to_contain_text("Tus marcas se guardarán cuando vuelva la señal.")
    expect(guardado(page)).to_have_text("Sin conexión")
    # Los reintentos siguen fallando sin volver a mostrarlo.
    page.wait_for_timeout(3500)

    page.context.set_offline(False)
    expect(aviso).to_have_count(0)
    esperar_guardado(page)
    assert page.evaluate("window.avisosSinConexion") == 2, "una vez cada aviso (franja y panel)"
    assert Asistencia.objects.count() == 3


def test_aviso_al_salir_con_una_marca_pendiente(abrir_asistencia, veinticinco):
    page = abrir_asistencia()
    dialogos = []

    def descartar(dialogo):
        dialogos.append(dialogo.type)
        dialogo.dismiss()

    page.on("dialog", descartar)
    page.route("**/estudiantes/*/", lambda route: None)
    tocar(page, veinticinco[0])

    page.close(run_before_unload=True)
    page.wait_for_timeout(500)
    assert dialogos == ["beforeunload"]
    assert not page.is_closed()


def test_sin_nada_pendiente_se_sale_sin_aviso(abrir_asistencia, live_server, veinticinco):
    page = abrir_asistencia()
    dialogos = []

    def descartar(dialogo):
        dialogos.append(dialogo.type)
        dialogo.dismiss()

    page.on("dialog", descartar)
    tocar(page, veinticinco[0])
    esperar_guardado(page)

    page.goto(f"{live_server.url}/docente/")
    assert dialogos == []


def test_sesion_vencida_durante_los_toques(
    abrir_asistencia, live_server, docente, clave, seccion_de_ana, veinticinco
):
    page = abrir_asistencia()
    tocar(page, veinticinco[0])
    esperar_guardado(page)
    envejecer_sesion(page, 61)
    # El primer guardado espera a que acabe el segundo toque: la marca pendiente es la de Faltó.
    retenidas = []
    page.route("**/estudiantes/*/", lambda route: retenidas.append(route))
    tocar(page, veinticinco[1], 2)
    expect(etiqueta(page, veinticinco[1])).to_have_text("Faltó")
    esperar_retenida(page, retenidas).continue_()
    page.unroute("**/estudiantes/*/")

    expect(page).to_have_url(re.compile(r"/ingresar/\?next=/docente/"))
    expect(page.locator(".mensaje--aviso")).to_contain_text("Tu sesión se cerró por inactividad.")
    assert estados_en_la_base() == {veinticinco[0].pk: "ASISTIO"}

    campo_usuario(page).fill(docente.username)
    campo_clave(page).fill(clave)
    boton_ingresar(page).click()
    page.wait_for_url(f"{live_server.url}/docente/")
    page.goto(url_asistencia(live_server, seccion_de_ana))

    expect(etiqueta(page, veinticinco[1])).to_have_text("Faltó")
    esperar_guardado(page)
    assert estados_en_la_base() == {veinticinco[0].pk: "ASISTIO", veinticinco[1].pk: "FALTO"}
    claves = page.evaluate(
        "Object.keys(sessionStorage).filter((clave) => clave.startsWith('asistencia:'))"
    )
    assert claves == []


def marcar_todos_menos_el_ultimo(page, veinticinco):
    for estudiante, estado in zip(veinticinco[:24], DIA_DEL_SPEC, strict=False):
        tocar(page, estudiante, TOQUES[estado])
    esperar_guardado(page)


def test_el_cierre_aparece_tras_el_ultimo_guardado(abrir_asistencia, veinticinco):
    page = abrir_asistencia()
    marcar_todos_menos_el_ultimo(page, veinticinco)
    retenidas = []
    page.route("**/estudiantes/*/", lambda route: retenidas.append(route))

    tocar(page, veinticinco[24], 4)
    expect(page.locator("[data-resumen-completo]:visible")).to_be_visible()
    expect(cierre(page)).to_have_count(0)

    esperar_retenida(page, retenidas).continue_()
    page.unroute("**/estudiantes/*/")
    expect(cierre(page)).to_have_text("Asistencia de hoy completa")
    expect(anuncio(page)).to_have_text("Asistencia de hoy completa")
    expect(page.locator(".vista-asistencia")).to_have_class(re.compile("jornada-completa"))


def test_sin_cierre_con_la_ultima_marca_sin_guardar(abrir_asistencia, veinticinco):
    page = abrir_asistencia()
    marcar_todos_menos_el_ultimo(page, veinticinco)
    page.context.set_offline(True)

    tocar(page, veinticinco[24])
    expect(fila(page, veinticinco[24]).locator("[data-fallo]")).to_be_visible()
    expect(cierre(page)).to_have_count(0)

    page.context.set_offline(False)
    expect(cierre(page)).to_be_visible()


def test_sin_cierre_durante_la_cuenta_ni_tras_deshacer(abrir_asistencia, veinticinco):
    page = abrir_asistencia()
    tocar(page, veinticinco[0])
    esperar_guardado(page)
    marcar_restantes(page)

    expect(page.locator("[data-resumen-completo]:visible")).to_be_visible()
    expect(cierre(page)).to_have_count(0)
    boton_deshacer(page).click()

    expect(cierre(page)).to_have_count(0)
    expect(page.locator(".vista-asistencia")).not_to_have_class(re.compile("jornada-completa"))
    expect(anuncio(page)).not_to_have_text("Asistencia de hoy completa")


def test_el_cierre_tras_la_cuenta(abrir_asistencia, veinticinco):
    page = abrir_asistencia()
    marcar_restantes(page)
    expect(cierre(page)).to_be_visible(timeout=8000)


def poner_vista_con_barra(page, veinticinco):
    tocar(page, veinticinco[0], 2)
    esperar_guardado(page)
    marcar_restantes(page)
    boton_deshacer(page).hover()  # pausa la cuenta mientras corre axe
    expect(barra(page)).to_be_visible()


def poner_vista_sin_conexion(page, veinticinco):
    page.context.set_offline(True)
    for estudiante in veinticinco[:3]:
        tocar(page, estudiante)
    expect(page.locator("[data-sin-conexion]:visible")).to_have_count(1)


def poner_vista_completa(page, veinticinco):
    marcar_restantes(page)
    expect(cierre(page)).to_be_visible(timeout=8000)
    page.wait_for_function(
        "document.getAnimations().every((animacion) => animacion.playState === 'finished')"
    )


VISTAS = {
    "con-barra": poner_vista_con_barra,
    "sin-conexion": poner_vista_sin_conexion,
    "completa": poner_vista_completa,
}


@pytest.mark.parametrize("tema", TEMAS)
@pytest.mark.parametrize("ancho", ANCHOS)
@pytest.mark.parametrize("vista", VISTAS)
def test_las_vistas_de_la_parte_c_pasan_axe(abrir_asistencia, veinticinco, vista, ancho, tema):
    page = abrir_asistencia(ancho, tema)
    VISTAS[vista](page, veinticinco)

    revisar_con_axe(page, f"asistencia-{vista}-{ancho}-{tema}")
    assert page.evaluate("document.documentElement.scrollWidth") <= ancho


def test_nombre_de_120_mas_120_a_320_px(abrir_asistencia, veinticinco):
    largo = veinticinco[0]
    largo.apellidos = ("HUAMANÍ " * 15)[:120]
    largo.nombres = ("MARÍA JOSÉ " * 11)[:120]
    largo.save()
    page = abrir_asistencia(320)
    tocar(page, largo, 4)
    page.context.set_offline(True)
    tocar(page, veinticinco[1])
    marcar_restantes(page)

    expect(fila(page, largo).locator(".estudiante__nombre")).to_be_visible()
    expect(fila(page, veinticinco[1]).locator("[data-fallo]")).to_be_visible()
    expect(barra(page)).to_be_visible()
    assert page.evaluate("document.documentElement.scrollWidth") <= 320
