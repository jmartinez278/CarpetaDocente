"""Las competencias del periodo en el navegador (spec competencias-periodo; design de US-029, D9).

El servidor dibuja la lista con el estado del periodo que abre y ``competencias.js`` agrega el
marcado, los borradores, el guardado y el diálogo de salida. El 30 de octubre de 2027, hora de
Lima, es el bimestre 3 vigente. Necesita el CSS compilado y Chromium:
``DJANGO_ALLOW_ASYNC_UNSAFE=true uv run pytest -m e2e --browser chromium src/backend/notas``.
"""

import datetime
import re
from zoneinfo import ZoneInfo

import pytest
from playwright.sync_api import expect

from actividad.tests.intentos import SIN_PERMISO, motivos, pasar_a_otra_docente
from cuentas.tests.e2e import (
    ANCHOS,
    TEMAS,
    con_pantalla,
    envejecer_sesion,
    fijar_hora_de_lima,
    ingresar,
    revisar_con_axe,
)
from notas.models import CompetenciaPeriodo
from notas.tests.conftest import (
    AGO_1,
    COMUNICACION,
    MATEMATICA,
    NOV_20,
    OCT_30,
    con_notas,
    ids_de,
)

# live_server usa una base transaccional que vacía las tablas al terminar cada prueba, y con ellas
# el catálogo que carga la migración de catalogo (áreas y competencias). No se usa
# serialized_rollback: tras otra e2e que vació la base, restaurar vuelve a insertar los tipos de
# contenido que post_migrate ya recreó y choca. La fixture ``catalogo`` solo repone el catálogo.
pytestmark = [pytest.mark.e2e, pytest.mark.django_db(transaction=True)]


@pytest.fixture(autouse=True)
def _catalogo_cargado(catalogo):
    """El catálogo debe estar antes de crear la institución, que copia sus áreas."""


LIMA = ZoneInfo("America/Lima")
MENSAJE_NOTAS = "La competencia tiene notas registradas en este periodo"
MENSAJE_ANUAL = "Debe tener nivel al cerrar el año"
MENSAJE_FALLO = "Tus cambios siguen aquí. Reintenta."


@pytest.fixture
def abrir_competencias(live_server, page, docente, clave, seccion_tutora, monkeypatch):
    """Abre la pantalla de la tutora el día pedido (el 30 de octubre por defecto)."""

    def abrir(ancho=1280, tema="light", dia=OCT_30, **parametros):
        fijar_hora_de_lima(
            monkeypatch, datetime.datetime(dia.year, dia.month, dia.day, 9, 0, tzinfo=LIMA)
        )
        con_pantalla(page, ancho, tema)
        ingresar(page, live_server, docente, clave)
        page.wait_for_url(f"{live_server.url}/docente/")
        page.goto(url_competencias(live_server, seccion_tutora, **parametros))
        return page

    return abrir


def url_competencias(live_server, seccion, **parametros):
    consulta = "&".join(f"{k}={v}" for k, v in parametros.items())
    base = f"{live_server.url}/docente/secciones/{seccion.pk}/competencias/"
    return f"{base}?{consulta}" if consulta else base


def casilla(page, competencia):
    return page.locator(f"#c-{competencia}")


def alternar(page, competencia, bloqueada=False):
    """Toca la fila entera, como lo hace la tutora.

    Playwright no actúa sobre un control con aria-disabled: para una competencia bloqueada
    ``bloqueada=True`` fuerza el toque, que es el que hace la tutora.
    """
    page.locator(f'label[for="c-{competencia}"]').click(force=bloqueada)


def boton_periodo(page, numero):
    return page.locator(f'[data-periodo="{numero}"]')


def estado(page):
    return page.locator("[data-texto-guardado]")


def guardar(page):
    page.locator("#guardar").click()


def marcas_en_la_base(numero):
    return set(
        CompetenciaPeriodo.objects.filter(periodo__numero=numero).values_list(
            "competencia_id", flat=True
        )
    )


def marcar_bimestres(seccion, bimestres, ids, hasta=3):
    CompetenciaPeriodo.objects.bulk_create(
        CompetenciaPeriodo(seccion=seccion, periodo=periodo, competencia_id=i)
        for periodo in bimestres[:hasta]
        for i in ids
    )


# --- Escenario "Camino ideal": marcar, guardar y volver a abrir ---


def test_desmarcar_y_guardar_persiste_al_recargar(abrir_competencias, ie, seccion_tutora):
    page = abrir_competencias()
    quitada = sorted(ids_de(MATEMATICA))[0]
    expect(page.locator("[data-conteo]")).to_have_text("21 de 21 seleccionadas")

    alternar(page, quitada)
    expect(casilla(page, quitada)).not_to_be_checked()
    expect(page.locator("[data-conteo]")).to_have_text("20 de 21 seleccionadas")
    guardar(page)

    expect(estado(page)).to_have_text("Guardado · B3")
    assert marcas_en_la_base(3) == ie - {quitada}
    page.reload()
    expect(casilla(page, quitada)).not_to_be_checked()
    expect(page.locator("[data-conteo]")).to_have_text("20 de 21 seleccionadas")
    expect(estado(page)).to_have_text("Sin cambios")


def test_guardar_sin_tocar_nada_guarda_todo_marcado(abrir_competencias, ie):
    page = abrir_competencias()
    expect(page.locator("#guardar")).to_have_attribute("aria-disabled", "false")

    guardar(page)

    expect(estado(page)).to_have_text("Guardado · B3")
    assert marcas_en_la_base(3) == ie
    expect(page.locator("#guardar")).to_have_attribute("aria-disabled", "true")


def test_desmarcar_todo_no_se_guarda_y_dice_por_que(abrir_competencias, ie):
    """Escenario "Conjunto vacío"."""
    page = abrir_competencias()
    for competencia in ie:
        alternar(page, competencia)
    expect(page.locator("[data-conteo]")).to_have_text("0 de 21 seleccionadas")

    guardar(page)

    expect(page.locator("[data-ayuda-guardado]")).to_have_text(
        "Marca al menos una competencia para guardar."
    )
    expect(estado(page)).to_have_text("No se pudo guardar")
    assert marcas_en_la_base(3) == set()


def test_las_areas_del_docente_de_curso_no_se_pueden_marcar(abrir_competencias, ie):
    page = abrir_competencias()

    for casilla_de_curso in page.locator(".comp-area--curso input").all():
        expect(casilla_de_curso).to_be_disabled()
        expect(casilla_de_curso).not_to_be_checked()


# --- Celular: la cápsula de áreas ---


def test_la_capsula_muestra_un_area_a_la_vez(abrir_competencias, ie):
    page = abrir_competencias(360)

    expect(page.locator("[data-posicion-area]")).to_have_text("1 de 10")
    expect(page.locator(".comp-area:visible")).to_have_count(1)
    expect(page.get_by_role("heading", name="Arte y Cultura")).to_be_visible()
    expect(page.locator("[data-area-anterior]")).to_be_disabled()

    page.locator("[data-area-siguiente]").click()

    expect(page.locator("[data-posicion-area]")).to_have_text("2 de 10")
    expect(page.locator(".comp-area:visible")).to_have_count(1)
    expect(page.get_by_role("heading", name="Inglés como lengua extranjera")).to_be_visible()


def test_la_capsula_no_da_la_vuelta_en_los_extremos(abrir_competencias, ie):
    page = abrir_competencias(360)

    page.locator("#area-elegida").select_option(index=9)

    expect(page.locator("[data-posicion-area]")).to_have_text("10 de 10")
    expect(page.locator("[data-area-siguiente]")).to_be_disabled()
    expect(page.locator("[data-area-anterior]")).to_be_enabled()
    expect(
        page.get_by_role("heading", name="Gestiona su aprendizaje de manera autónoma")
    ).to_be_visible()


def test_las_marcas_de_un_area_se_conservan_y_se_guardan_desde_otra(abrir_competencias, ie):
    """Escenario "Guardar desde otra área en el celular"."""
    page = abrir_competencias(360)
    quitada = min(ids_de("0001"))

    alternar(page, quitada)
    page.locator("[data-area-siguiente]").click()
    page.locator("[data-area-anterior]").click()
    expect(casilla(page, quitada)).not_to_be_checked()
    page.locator("[data-area-siguiente]").click()
    expect(page.locator("#guardar")).to_have_attribute("aria-disabled", "false")
    guardar(page)

    expect(estado(page)).to_have_text("Guardado · B3")
    assert marcas_en_la_base(3) == ie - {quitada}


def test_el_guardado_fijo_del_celular_dice_el_total_global(abrir_competencias, ie):
    page = abrir_competencias(360)
    alternar(page, min(ids_de("0001")))

    expect(page.locator("[data-ayuda-guardado]")).to_have_text("B3 · 20 de 21 en total")


def test_en_pc_se_ven_las_diez_areas_y_el_panel(abrir_competencias, ie):
    page = abrir_competencias(1280)

    expect(page.locator(".comp-area:visible")).to_have_count(10)
    expect(page.get_by_role("heading", name="Tu selección")).to_be_visible()
    expect(page.locator("#guardar")).to_be_visible()
    expect(page.locator(".comp-navegacion")).to_be_hidden()


# --- Borradores entre periodos ---


def test_el_borrador_de_un_periodo_se_conserva_y_el_boton_lo_dice(abrir_competencias, ie):
    """Escenario "Cambiar de periodo con cambios"."""
    page = abrir_competencias()
    quitada = min(ids_de(MATEMATICA))
    alternar(page, quitada)

    boton_periodo(page, 2).click()
    expect(boton_periodo(page, 2)).to_have_attribute("aria-pressed", "true")
    expect(boton_periodo(page, 3)).to_contain_text("Sin guardar")
    expect(casilla(page, quitada)).to_be_checked()
    boton_periodo(page, 3).click()

    expect(casilla(page, quitada)).not_to_be_checked()
    expect(boton_periodo(page, 3)).to_contain_text("Sin guardar")
    expect(boton_periodo(page, 3)).to_have_attribute("aria-pressed", "true")
    expect(page.locator("[data-fecha-periodo]")).to_have_text("10 ago. – 30 oct.")


def test_corregir_un_periodo_anterior_no_toca_el_vigente(
    abrir_competencias, ie, seccion_tutora, bimestres
):
    """Escenario "Corregir un periodo anterior"."""
    marcar_bimestres(seccion_tutora, bimestres, ie, hasta=3)
    page = abrir_competencias()
    quitada = min(ids_de(MATEMATICA))

    boton_periodo(page, 1).click()
    alternar(page, quitada)
    guardar(page)

    expect(estado(page)).to_have_text("Guardado · B1")
    assert marcas_en_la_base(1) == ie - {quitada}
    assert marcas_en_la_base(3) == ie


def test_el_periodo_futuro_no_se_puede_elegir(abrir_competencias, ie):
    page = abrir_competencias()

    expect(boton_periodo(page, 4)).to_be_disabled()
    expect(boton_periodo(page, 4)).to_contain_text("Futuro")


def test_deshacer_vuelve_a_lo_guardado(abrir_competencias, ie, seccion_tutora, bimestres):
    marcar_bimestres(seccion_tutora, bimestres, sorted(ie)[:18], hasta=3)
    page = abrir_competencias()
    expect(page.locator("[data-conteo]")).to_have_text("18 de 21 seleccionadas")
    expect(page.get_by_role("button", name="Deshacer cambios")).to_be_hidden()
    marcada = sorted(ie)[0]
    nueva = sorted(ie)[20]

    alternar(page, marcada)
    alternar(page, nueva)
    expect(estado(page)).to_have_text("2 cambios sin guardar")
    page.get_by_role("button", name="Deshacer cambios").click()

    expect(page.locator("[data-conteo]")).to_have_text("18 de 21 seleccionadas")
    expect(casilla(page, marcada)).to_be_checked()
    expect(casilla(page, nueva)).not_to_be_checked()
    expect(page.get_by_role("button", name="Deshacer cambios")).to_be_hidden()
    expect(page.locator("#guardar")).to_be_focused()


# --- Último periodo: obligatorias ---


@pytest.fixture
def ultimo_periodo(abrir_competencias, ie, seccion_tutora, bimestres):
    """El 20 de noviembre: bimestre 4 vigente y 5 competencias sin notas en el 1 al 3."""
    faltan = sorted(ie)[:5]
    marcar_bimestres(seccion_tutora, bimestres, ie - set(faltan), hasta=3)
    con_notas(seccion_tutora, bimestres[0], ie - set(faltan))
    return abrir_competencias(dia=NOV_20), faltan


def test_deshacer_no_aparece_en_el_bimestre_4_sin_cambios(ultimo_periodo):
    page, faltan = ultimo_periodo

    expect(boton_periodo(page, 4)).to_have_attribute("aria-pressed", "true")
    expect(page.get_by_role("button", name="Deshacer cambios")).to_be_hidden()
    expect(estado(page)).to_have_text("Sin guardar")


def test_deshacer_aparece_con_un_cambio_en_el_bimestre_4(ultimo_periodo, ie):
    page, faltan = ultimo_periodo
    libre = sorted(ie - set(faltan))[0]

    alternar(page, libre)

    expect(page.get_by_role("button", name="Deshacer cambios")).to_be_visible()


def test_la_obligatoria_con_espacio_no_cambia_y_anuncia_su_motivo(ultimo_periodo):
    """Escenario "Teclado en una competencia bloqueada"."""
    page, faltan = ultimo_periodo
    obligatoria = casilla(page, faltan[0])
    expect(obligatoria).to_be_checked()
    expect(obligatoria).to_have_attribute("aria-disabled", "true")
    expect(page.locator(f"#c-{faltan[0]}").locator("xpath=ancestor::li")).to_contain_text(
        MENSAJE_ANUAL
    )

    obligatoria.focus()
    page.keyboard.press("Space")

    expect(obligatoria).to_be_checked()
    expect(page.get_by_role("alert")).to_have_text(MENSAJE_ANUAL)
    expect(page.locator("[data-conteo]")).to_have_text("21 de 21 seleccionadas")


def test_las_obligatorias_se_guardan_con_las_demas(ultimo_periodo, ie):
    """Escenario "Guardado sin las obligatorias": el servidor las agrega."""
    page, faltan = ultimo_periodo
    quitada = sorted(ie - set(faltan))[0]

    alternar(page, quitada)
    guardar(page)

    expect(estado(page)).to_have_text("Guardado · B4")
    assert marcas_en_la_base(4) == ie - {quitada}


def test_el_resumen_cuenta_las_obligatorias(ultimo_periodo):
    page, faltan = ultimo_periodo

    expect(page.locator("[data-resumen-bloqueos]")).to_contain_text("Por cierre de año")
    expect(page.locator("[data-resumen-bloqueos]")).to_contain_text("5")


def test_el_ultimo_periodo_explica_las_obligatorias(ultimo_periodo):
    page, faltan = ultimo_periodo

    expect(page.locator("[data-nota-periodo]")).to_contain_text("Último bimestre del año")


# --- Competencia con notas ---


def test_desmarcar_una_competencia_con_notas_muestra_el_motivo(
    abrir_competencias, ie, seccion_tutora, bimestres
):
    """Escenario "Caso de error"."""
    elegida = min(ie)
    con_notas(seccion_tutora, bimestres[2], [elegida])
    page = abrir_competencias()
    expect(casilla(page, elegida)).to_be_checked()
    expect(page.locator(f'[data-competencia-fila="{elegida}"]')).to_contain_text(MENSAJE_NOTAS)

    alternar(page, elegida, bloqueada=True)

    expect(casilla(page, elegida)).to_be_checked()
    expect(page.get_by_role("alert")).to_have_text(MENSAJE_NOTAS)
    expect(estado(page)).to_have_text("Sin guardar")


def test_un_guardado_que_choca_con_notas_las_bloquea_en_pantalla(
    abrir_competencias, ie, seccion_tutora, bimestres
):
    """Las notas llegan después de abrir la pantalla: el servidor rechaza y la pantalla lo avisa."""
    marcar_bimestres(seccion_tutora, bimestres, ie, hasta=3)
    elegida = min(ie)
    page = abrir_competencias()
    alternar(page, elegida)
    expect(casilla(page, elegida)).not_to_be_checked()
    con_notas(seccion_tutora, bimestres[2], [elegida])

    guardar(page)

    expect(casilla(page, elegida)).to_be_checked()
    expect(casilla(page, elegida)).to_have_attribute("aria-disabled", "true")
    expect(page.locator(f'[data-competencia-fila="{elegida}"]')).to_contain_text(MENSAJE_NOTAS)
    expect(estado(page)).to_have_text("No se pudo guardar")
    expect(page.get_by_role("alert")).to_contain_text(MENSAJE_NOTAS)
    assert marcas_en_la_base(3) == ie


# --- Guardado: red caída y sesión vencida ---


def test_sin_red_dice_que_no_se_pudo_guardar_y_un_guardado_despues_lo_quita(
    abrir_competencias, ie, page
):
    """Escenario "Falla la red"."""
    pagina = abrir_competencias()
    quitada = min(ids_de(MATEMATICA))
    alternar(pagina, quitada)

    page.context.set_offline(True)
    guardar(pagina)

    expect(estado(pagina)).to_have_text("No se pudo guardar")
    expect(pagina.locator("[data-ayuda-guardado]")).to_have_text(MENSAJE_FALLO)
    expect(pagina.get_by_role("alert")).to_contain_text("No se pudo guardar")
    expect(casilla(pagina, quitada)).not_to_be_checked()
    assert marcas_en_la_base(3) == set()

    page.context.set_offline(False)
    guardar(pagina)

    expect(estado(pagina)).to_have_text("Guardado · B3")
    expect(pagina.locator("[data-ayuda-guardado]")).not_to_have_text(MENSAJE_FALLO)
    assert marcas_en_la_base(3) == ie - {quitada}


def test_con_la_sesion_vencida_no_guarda_y_ofrece_volver_a_ingresar(abrir_competencias, ie, page):
    """Escenario "Sesión vencida"."""
    pagina = abrir_competencias()
    alternar(pagina, min(ids_de(MATEMATICA)))
    envejecer_sesion(page, 61)

    guardar(pagina)

    expect(estado(pagina)).to_have_text("Tu sesión venció")
    enlace = pagina.get_by_role("link", name="Volver a ingresar")
    expect(enlace).to_be_visible()
    expect(enlace).to_have_attribute("href", re.compile(r"/ingresar/"))
    assert marcas_en_la_base(3) == set()


def test_guardar_en_una_seccion_que_ya_no_es_suya_lleva_a_sin_permiso(
    abrir_competencias, ie, seccion_tutora, otra_docente
):
    """Spec competencias-periodo y acceso-secciones: un guardado con 403 lleva a «sin permiso», no
    a «Tu sesión venció», sin el aviso de salida y con una sola entrada (US-004, D6)."""
    pagina = abrir_competencias()
    alternar(pagina, min(ids_de(MATEMATICA)))
    dialogos = []
    pagina.on("dialog", lambda dialogo: (dialogos.append(dialogo.type), dialogo.dismiss()))
    pasar_a_otra_docente(seccion_tutora, otra_docente)

    guardar(pagina)

    pagina.wait_for_url(re.compile(r"/docente/sin-permiso/$"))
    expect(pagina.get_by_role("heading", name=SIN_PERMISO)).to_be_visible()
    expect(pagina.get_by_text("Tu sesión venció")).to_have_count(0)
    assert dialogos == []
    assert marcas_en_la_base(3) == set()
    assert motivos() == ["ajena"]


# --- Salir sin guardar ---


def abrir_menu_y_salir(page):
    page.locator("summary[aria-label='Menú de la cuenta']").click()
    page.get_by_role("button", name="Cerrar sesión").click()


def test_el_dialogo_de_salida_nombra_los_periodos_y_pone_el_foco_en_seguir_editando(
    abrir_competencias, ie
):
    """Escenario "Salir con cambios"."""
    page = abrir_competencias()
    alternar(page, min(ids_de(MATEMATICA)))
    boton_periodo(page, 2).click()
    alternar(page, min(ids_de(COMUNICACION)))

    abrir_menu_y_salir(page)

    dialogo = page.get_by_role("dialog", name="¿Salir sin guardar?")
    expect(dialogo).to_be_visible()
    expect(dialogo).to_contain_text("B2 y B3")
    expect(page.get_by_role("button", name="Seguir editando")).to_be_focused()


def test_escape_y_seguir_editando_conservan_los_cambios(abrir_competencias, ie):
    page = abrir_competencias()
    quitada = min(ids_de(MATEMATICA))
    alternar(page, quitada)

    abrir_menu_y_salir(page)
    expect(page.get_by_role("dialog")).to_be_visible()
    page.keyboard.press("Escape")
    expect(page.get_by_role("dialog")).to_be_hidden()
    expect(casilla(page, quitada)).not_to_be_checked()

    abrir_menu_y_salir(page)
    page.get_by_role("button", name="Seguir editando").click()
    expect(page.get_by_role("dialog")).to_be_hidden()
    expect(casilla(page, quitada)).not_to_be_checked()
    expect(estado(page)).to_have_text("1 cambio sin guardar")


def test_salir_sin_guardar_sale_sin_aviso_del_navegador(abrir_competencias, ie, live_server, page):
    pagina = abrir_competencias()
    alternar(pagina, min(ids_de(MATEMATICA)))
    dialogos = []
    page.on("dialog", lambda d: (dialogos.append(d.type), d.accept()))

    abrir_menu_y_salir(pagina)
    page.get_by_role("button", name="Salir sin guardar").click()

    page.wait_for_url(f"{live_server.url}/ingresar/**")
    assert dialogos == []
    assert marcas_en_la_base(3) == set()


def test_sin_cambios_no_hay_pregunta(abrir_competencias, ie, live_server, page):
    pagina = abrir_competencias()

    abrir_menu_y_salir(pagina)

    page.wait_for_url(f"{live_server.url}/ingresar/**")


def test_recargar_con_cambios_muestra_el_aviso_del_navegador(abrir_competencias, ie, page):
    """Escenario "Recargar con cambios"."""
    pagina = abrir_competencias()
    alternar(pagina, min(ids_de(MATEMATICA)))
    dialogos = []
    page.on("dialog", lambda d: (dialogos.append(d.type), d.dismiss()))

    page.close(run_before_unload=True)
    pagina.wait_for_timeout(300)

    assert dialogos == ["beforeunload"]


def test_recargar_sin_cambios_no_muestra_aviso(abrir_competencias, ie, page):
    pagina = abrir_competencias()
    alternar(pagina, min(ids_de(MATEMATICA)))
    guardar(pagina)
    expect(estado(pagina)).to_have_text("Guardado · B3")
    dialogos = []
    page.on("dialog", lambda d: (dialogos.append(d.type), d.dismiss()))

    page.reload()

    assert dialogos == []


# --- Sin periodos y vacaciones ---


def test_en_vacaciones_se_elige_un_periodo_pasado(abrir_competencias, ie):
    """Escenario "Vacaciones"."""
    page = abrir_competencias(dia=AGO_1)
    expect(page.get_by_text("Hoy no hay un periodo vigente")).to_be_visible()
    expect(page.locator("#guardar")).to_be_hidden()
    expect(page.locator("[data-instruccion]")).to_be_hidden()
    expect(boton_periodo(page, 3)).to_be_disabled()

    boton_periodo(page, 2).click()

    expect(page.locator("#guardar")).to_be_visible()
    expect(page.locator("[data-instruccion]")).to_be_visible()
    expect(page.locator("[data-conteo]")).to_have_text("21 de 21 seleccionadas")
    expect(boton_periodo(page, 2)).to_have_attribute("aria-pressed", "true")
    expect(page.locator("[data-nota-periodo]")).to_be_hidden()
    guardar(page)
    expect(estado(page)).to_have_text("Guardado · B2")
    assert marcas_en_la_base(2) == ie


def test_sin_periodos_solo_el_aviso(abrir_competencias, seccion_tutora, universo_ie):
    """Escenario "Sin periodos"."""
    page = abrir_competencias()

    expect(page.get_by_text("La dirección aún no configura los periodos")).to_be_visible()
    expect(page.locator("#guardar")).to_have_count(0)
    expect(page.locator("[data-periodo]")).to_have_count(0)


# --- Escenario "Axe en ambos temas" y sin desplazamiento horizontal ---


@pytest.mark.parametrize("tema", TEMAS)
@pytest.mark.parametrize("ancho", ANCHOS)
def test_la_pantalla_con_marcas_pasa_axe(
    abrir_competencias, ie, seccion_tutora, bimestres, ancho, tema
):
    marcar_bimestres(seccion_tutora, bimestres, sorted(ie)[:18], hasta=3)
    page = abrir_competencias(ancho, tema)
    alternar(page, sorted(ie)[0])

    revisar_con_axe(page, f"competencias-con-marcas-{ancho}-{tema}")
    assert page.evaluate("document.documentElement.scrollWidth") <= ancho


@pytest.mark.parametrize("tema", TEMAS)
@pytest.mark.parametrize("ancho", ANCHOS)
def test_la_pantalla_con_bloqueos_pasa_axe(
    abrir_competencias, ie, seccion_tutora, bimestres, ancho, tema
):
    faltan = sorted(ie)[:5]
    marcar_bimestres(seccion_tutora, bimestres, ie - set(faltan), hasta=3)
    con_notas(seccion_tutora, bimestres[0], ie - set(faltan))
    elegida = max(ie)
    con_notas(seccion_tutora, bimestres[3], [elegida])
    page = abrir_competencias(ancho, tema, dia=NOV_20)
    expect(page.locator(".comp-competencia--anual")).to_have_count(5)
    expect(page.locator(".comp-competencia--notas")).to_have_count(1)

    revisar_con_axe(page, f"competencias-con-bloqueos-{ancho}-{tema}")
    assert page.evaluate("document.documentElement.scrollWidth") <= ancho


@pytest.mark.parametrize("tema", TEMAS)
@pytest.mark.parametrize("ancho", ANCHOS)
def test_el_dialogo_de_salida_pasa_axe(abrir_competencias, ie, ancho, tema):
    page = abrir_competencias(ancho, tema)
    alternar(page, min(ids_de("0001")))  # Arte y Cultura, el área que abre en el celular
    abrir_menu_y_salir(page)
    expect(page.get_by_role("dialog")).to_be_visible()

    revisar_con_axe(page, f"competencias-dialogo-{ancho}-{tema}")


@pytest.mark.parametrize("tema", TEMAS)
@pytest.mark.parametrize("ancho", ANCHOS)
def test_sin_periodos_pasa_axe(abrir_competencias, seccion_tutora, universo_ie, ancho, tema):
    page = abrir_competencias(ancho, tema)
    expect(page.get_by_text("La dirección aún no configura los periodos")).to_be_visible()

    revisar_con_axe(page, f"competencias-sin-periodos-{ancho}-{tema}")
    assert page.evaluate("document.documentElement.scrollWidth") <= ancho


@pytest.mark.parametrize("tema", TEMAS)
@pytest.mark.parametrize("ancho", ANCHOS)
def test_en_vacaciones_pasa_axe(abrir_competencias, ie, ancho, tema):
    page = abrir_competencias(ancho, tema, dia=AGO_1)
    expect(page.get_by_text("Hoy no hay un periodo vigente")).to_be_visible()

    revisar_con_axe(page, f"competencias-vacaciones-{ancho}-{tema}")
    assert page.evaluate("document.documentElement.scrollWidth") <= ancho


@pytest.mark.parametrize("ancho", [320, 360])
def test_no_hay_desplazamiento_horizontal_a_320_y_360(abrir_competencias, ie, ancho):
    page = abrir_competencias(ancho)

    assert page.evaluate("document.documentElement.scrollWidth") <= ancho
    for numero in range(10):
        page.locator("#area-elegida").select_option(index=numero)
        assert page.evaluate("document.documentElement.scrollWidth") <= ancho


@pytest.mark.parametrize("ancho", ANCHOS)
def test_las_filas_miden_al_menos_44_px(abrir_competencias, ie, ancho):
    page = abrir_competencias(ancho)

    if ancho < 960:
        # Una sola área a la vez: se revisan las diez.
        alturas = []
        for numero in range(10):
            page.locator("#area-elegida").select_option(index=numero)
            alturas += [f["height"] for f in cajas(page, ".comp-competencia label:visible")]
    else:
        alturas = [f["height"] for f in cajas(page, ".comp-competencia label:visible")]
    assert len(alturas) == 27
    assert min(alturas) >= 44


def cajas(page, selector):
    return [fila.bounding_box() for fila in page.locator(selector).all()]
