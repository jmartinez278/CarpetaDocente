"""La hoja de notas en el navegador (spec registro-notas; design de US-020, D9, D12).

El servidor dibuja el marco y ``notas.js`` dibuja la rejilla, el panel del celular, el guardado y el
conteo de faltantes. El 30 de octubre de 2027, hora de Lima, es el bimestre 3 vigente. Necesita el
CSS compilado y Chromium:
``DJANGO_ALLOW_ASYNC_UNSAFE=true uv run pytest -m e2e --browser chromium src/backend/notas``.
"""

import datetime
import re
import time

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
from notas.models import Calificacion
from notas.tests.conftest import (
    COMUNICACION,
    CONCLUSION,
    MATEMATICA,
    competencia,
    crear_estudiantes,
    ids_de,
    marcar,
    poner_nota,
)
from notas.tests.e2e import (
    LIMA,
    boton_movil,
    entrada,
    estado,
    guardar,
    notas_en_la_base,
    url_hoja,
)

pytestmark = [pytest.mark.e2e, pytest.mark.django_db(transaction=True)]


@pytest.fixture(autouse=True)
def _catalogo_cargado(catalogo):
    """El catálogo debe estar antes de crear la institución, que copia sus áreas."""


MENSAJE_RED = "Revisa tu conexión y reintenta."
VACIA = "Una nota registrada puede corregirse, pero no quedar vacía."


# --- Nivel en la PC ---


def test_escribir_el_nivel_baja_a_la_misma_competencia_del_siguiente(abrir_hoja, estudiantes):
    """Escenarios "Escribir el nivel", "Logro destacado" y "Tecla fuera de la escala"."""
    ana, luis = estudiantes
    page = abrir_hoja()

    entrada(page, ana, 1).click()
    page.keyboard.press("Escape")
    page.keyboard.type("a")
    page.keyboard.press("Enter")

    expect(entrada(page, ana, 1)).to_have_value("A")
    expect(entrada(page, luis, 1)).to_be_focused()

    page.keyboard.type("a")
    page.keyboard.type("d")
    expect(entrada(page, luis, 1)).to_have_value("AD")

    entrada(page, luis, 2).focus()
    for tecla in ("1", "5", "+"):
        page.keyboard.type(tecla)
    expect(entrada(page, luis, 2)).to_have_value("")
    expect(page.locator("#mensaje-guardado")).to_be_hidden()


def test_la_barra_de_niveles_elige_con_flechas_y_enter(abrir_hoja, estudiantes):
    """Escenario "Barra de niveles"."""
    ana, _ = estudiantes
    page = abrir_hoja()
    entrada(page, ana, 1).focus()

    page.keyboard.press("Alt+ArrowDown")
    expect(page.locator("#lista-niveles")).to_be_visible()
    page.keyboard.press("ArrowDown")
    page.keyboard.press("ArrowDown")
    page.keyboard.press("Enter")

    expect(entrada(page, ana, 1)).to_have_value("B")
    expect(page.locator("#nota-editor")).to_be_visible()


def test_a_no_abre_ningun_recuadro(abrir_hoja, estudiantes):
    """Escenario "Nivel A sin conclusión"."""
    ana, _ = estudiantes
    page = abrir_hoja()
    entrada(page, ana, 1).focus()

    page.keyboard.type("a")

    expect(entrada(page, ana, 1)).to_have_value("A")
    expect(page.locator("#nota-editor")).to_be_hidden()


def test_el_nombre_de_la_competencia_aparece_al_recibir_el_foco(abrir_hoja, estudiantes):
    """Escenario "Nombre de la competencia"."""
    page = abrir_hoja()

    page.locator(".notas-comp__boton").first.focus()

    expect(page.locator("#competencia-detalle")).to_have_text(competencia(MATEMATICA, 1).nombre)


# --- Nivel en el celular ---


def test_el_panel_del_celular_elige_y_pasa_al_siguiente(abrir_hoja, estudiantes):
    """Escenario "Panel de la celda"."""
    ana, luis = estudiantes
    page = abrir_hoja(ancho=360)

    boton_movil(page, ana, 2).click()
    expect(page.locator("#panel-editor")).to_be_visible()
    page.locator('#panel-niveles [data-elegir="A"]').click()
    page.locator("#siguiente").click()

    expect(page.locator("#panel-estudiante")).to_have_text("ROJAS, LUIS")
    expect(page.locator("#panel-competencia")).to_contain_text("C2")
    page.locator("#cerrar-panel").click()
    expect(boton_movil(page, ana, 2)).to_contain_text("A")


# --- Conclusión en B y C ---


def test_elegir_b_abre_el_recuadro_y_listo_conserva_el_texto(abrir_hoja, estudiantes):
    """Escenarios "Conclusión en B" y "Camino ideal (US-021)"."""
    ana, _ = estudiantes
    page = abrir_hoja()
    entrada(page, ana, 1).focus()

    page.keyboard.type("b")

    expect(page.locator("#nota-titulo")).to_have_text("Rellena la conclusión")
    expect(page.locator("#ayuda-nota")).to_have_text("De 10 a 500 caracteres.")
    page.locator("#conclusion-pc").fill(CONCLUSION)
    page.locator("#listo-nota").click()
    expect(page.locator("#nota-editor")).to_be_hidden()

    guardar(page)
    expect(page.locator("#mensaje-guardado")).to_contain_text("Matemática guardada")
    expect(estado(page)).to_have_text("Sin cambios")
    comp = competencia(MATEMATICA, 1)
    assert notas_en_la_base() == {(ana.pk, comp.pk): ("B", CONCLUSION)}


def test_de_b_a_a_borra_la_conclusion_al_guardar(abrir_hoja, estudiantes, hoja_lista):
    """Escenarios "De B a A" y "Flujo alternativo válido (US-020)"."""
    ana, _ = estudiantes
    comp = competencia(MATEMATICA, 1)
    poner_nota(ana, comp, hoja_lista, "B")
    page = abrir_hoja()

    entrada(page, ana, 1).focus()
    page.keyboard.type("a")
    guardar(page)

    expect(page.locator("#mensaje-guardado")).to_contain_text("Matemática guardada")
    expect(estado(page)).to_have_text("Sin cambios")
    assert notas_en_la_base() == {(ana.pk, comp.pk): ("A", "")}


def test_la_conclusion_de_un_trasladado_se_lee_sin_editar(
    abrir_hoja, estudiantes, hoja_lista, seccion_tutora
):
    """Escenarios "Trasladado con notas" y "Conclusión de un trasladado"."""
    (mateo,) = crear_estudiantes(seccion_tutora, "SOTO, MATEO", estado="TRASLADADO")
    poner_nota(mateo, competencia(MATEMATICA, 1), hoja_lista, "C", CONCLUSION)
    page = abrir_hoja()

    expect(page.get_by_text("Con notas de este bimestre · Solo lectura")).to_be_visible()
    expect(page.get_by_text("TRASLADADO · Solo lectura")).to_be_visible()
    entrada(page, mateo, 1).focus()
    page.keyboard.press("Alt+Enter")

    expect(page.locator("#nota-titulo")).to_have_text("Conclusión · Solo lectura")
    expect(page.locator("#conclusion-pc")).to_have_value(CONCLUSION)
    expect(page.locator("#conclusion-pc")).not_to_be_editable()


# --- Una nota no vuelve a vacía ---


def test_suprimir_no_borra_una_nota_guardada(abrir_hoja, estudiantes, hoja_lista):
    """Escenario "Borrar una nota guardada"."""
    ana, _ = estudiantes
    poner_nota(ana, competencia(MATEMATICA, 1), hoja_lista, "A")
    page = abrir_hoja()

    entrada(page, ana, 1).focus()
    page.keyboard.press("Delete")

    expect(entrada(page, ana, 1)).to_have_value("A")
    expect(page.locator("[data-anuncio]")).to_have_text(VACIA)


# --- Rellenar vacías ---


def test_rellenar_vacias_solo_toca_las_vacias_y_queda_como_borrador(
    abrir_hoja, estudiantes, hoja_lista
):
    """Escenarios "Rellenar con A" y "Solo AD o A"."""
    ana, luis = estudiantes
    poner_nota(ana, competencia(MATEMATICA, 1), hoja_lista, "B")
    page = abrir_hoja()

    page.locator('.notas-rellenar[data-rellenar="0"]').click()
    expect(page.locator("#confirmar-relleno")).to_be_visible()
    expect(page.locator('[name="relleno"]')).to_have_count(2)
    expect(page.locator("#texto-relleno")).to_contain_text("Se rellenará 1 celda vacía")
    page.locator("#aplicar-relleno").click()

    expect(entrada(page, ana, 1)).to_have_value("B")
    expect(entrada(page, luis, 1)).to_have_value("A")
    assert len(notas_en_la_base()) == 1
    expect(estado(page)).to_have_text("1 cambio sin guardar")


# --- Guardar la hoja del área ---


def test_guardar_persiste_al_recargar(abrir_hoja, estudiantes):
    """Escenarios "Camino ideal (US-020)" y "Guardar con celdas vacías"."""
    ana, _ = estudiantes
    page = abrir_hoja()
    entrada(page, ana, 1).focus()
    page.keyboard.type("a")

    guardar(page)

    expect(page.locator("#mensaje-guardado")).to_contain_text("Matemática guardada")
    expect(estado(page)).to_have_text("Sin cambios")
    assert notas_en_la_base() == {(ana.pk, competencia(MATEMATICA, 1).pk): ("A", "")}
    page.reload()
    expect(entrada(page, ana, 1)).to_have_value("A")
    expect(estado(page)).to_have_text("Sin cambios")


def test_c_sin_conclusion_no_guarda_nada_y_marca_la_celda(abrir_hoja, estudiantes):
    """Escenarios "Caso de error (US-021)" y "Conclusión corta en B"."""
    ana, luis = estudiantes
    page = abrir_hoja()
    entrada(page, ana, 1).focus()
    page.keyboard.type("a")
    entrada(page, luis, 1).focus()
    page.keyboard.type("c")
    page.keyboard.press("Escape")

    guardar(page)

    mensaje = page.locator("#mensaje-guardado")
    expect(mensaje).to_contain_text("No se guardó nada")
    expect(mensaje).to_contain_text("Falta 1 conclusión en B y C.")
    expect(page.locator(f'.notas-nota[data-est="{luis.pk}"]').first).to_have_attribute(
        "aria-label", re.compile("Falta conclusión")
    )
    assert notas_en_la_base() == {}

    page.get_by_role("button", name="Ir a la primera conclusión pendiente").click()
    page.locator("#conclusion-pc").fill("Bien")
    page.locator("#listo-nota").click()
    expect(page.locator("#ayuda-nota")).to_contain_text("Escribe de 10 a 500 caracteres.")


# --- Guardado sin conexión y sesión vencida ---


def test_sin_conexion_conserva_todo_y_reintentar_guarda(abrir_hoja, estudiantes, page):
    """Escenarios "Caso de error (US-020)" y "Reintento"."""
    ana, _ = estudiantes
    pagina = abrir_hoja()
    entrada(pagina, ana, 1).focus()
    pagina.keyboard.type("a")

    page.context.set_offline(True)
    guardar(pagina)

    expect(pagina.locator("#mensaje-guardado")).to_contain_text("No se pudo guardar")
    expect(pagina.locator("#mensaje-guardado")).to_contain_text(MENSAJE_RED)
    expect(pagina.locator("#guardar")).to_have_text("Reintentar")
    expect(entrada(pagina, ana, 1)).to_have_value("A")
    assert notas_en_la_base() == {}

    page.context.set_offline(False)
    guardar(pagina)

    expect(pagina.locator("#mensaje-guardado")).to_contain_text("Matemática guardada")
    expect(estado(pagina)).to_have_text("Sin cambios")
    expect(pagina.locator("#mensaje-guardado")).not_to_contain_text("No se pudo guardar")
    assert len(notas_en_la_base()) == 1


def test_con_la_sesion_vencida_no_guarda_y_ofrece_volver_a_ingresar(abrir_hoja, estudiantes, page):
    """Escenario "Guardar con la sesión vencida"."""
    ana, _ = estudiantes
    pagina = abrir_hoja()
    entrada(pagina, ana, 1).focus()
    pagina.keyboard.type("a")
    envejecer_sesion(page, 61)

    guardar(pagina)

    expect(pagina.locator("#mensaje-guardado")).to_contain_text("Tu sesión venció")
    expect(pagina.locator("#mensaje-guardado")).to_contain_text(
        "Vuelve a ingresar para guardar. Tus cambios siguen aquí."
    )
    enlace = pagina.get_by_role("link", name="Volver a ingresar")
    expect(enlace).to_have_attribute("href", re.compile(r"/ingresar/"))
    assert notas_en_la_base() == {}


def borradores_de_la_seccion(page, seccion):
    """Las claves de ``localStorage`` con borradores de esa sección (notas-borrador.js)."""
    return page.evaluate(
        "(marca) => Object.keys(localStorage)"
        '.filter((k) => k.startsWith("cd:notas:") && k.includes(marca))',
        f":s{seccion.pk}:",
    )


def test_guardar_en_una_seccion_que_ya_no_es_suya_lleva_a_sin_permiso(
    abrir_hoja, estudiantes, seccion_tutora, otra_docente
):
    """Spec acceso-secciones, "Guardado de la hoja de notas" y "Un intento por HTMX deja una sola
    entrada" (US-004, D6)."""
    ana, _ = estudiantes
    pagina = abrir_hoja()
    entrada(pagina, ana, 1).focus()
    pagina.keyboard.type("a")
    expect(estado(pagina)).not_to_have_text("Sin cambios")
    assert borradores_de_la_seccion(pagina, seccion_tutora)
    dialogos = []
    pagina.on("dialog", lambda dialogo: (dialogos.append(dialogo.type), dialogo.dismiss()))
    pasar_a_otra_docente(seccion_tutora, otra_docente)

    guardar(pagina)

    pagina.wait_for_url(re.compile(r"/docente/sin-permiso/$"))
    expect(pagina.get_by_role("heading", name=SIN_PERMISO)).to_be_visible()
    expect(pagina.get_by_text("Tu sesión venció")).to_have_count(0)
    assert dialogos == []
    assert borradores_de_la_seccion(pagina, seccion_tutora) == []
    assert notas_en_la_base() == {}
    assert motivos() == ["ajena"]


# --- Cambiar de área y volver a las notas ---


def test_cambiar_de_area_conserva_lo_digitado_y_marca_el_punto(abrir_hoja, estudiantes):
    """Escenarios "Cambiar de área" y "Área con cambios sin guardar"."""
    ana, _ = estudiantes
    page = abrir_hoja()
    entrada(page, ana, 1).focus()
    page.keyboard.type("a")

    page.locator(f'[data-area-pildora="{COMUNICACION}"]').click()
    expect(page.locator("#titulo-area")).to_have_text("Comunicación")
    expect(page).to_have_url(re.compile(rf"area={COMUNICACION}"))
    matematica = page.locator(f'[data-area-pildora="{MATEMATICA}"]')
    expect(matematica).to_contain_text("Cambios sin guardar")

    matematica.click()
    expect(page.locator("#titulo-area")).to_have_text("Matemática")
    expect(entrada(page, ana, 1)).to_have_value("A")


def test_el_area_del_docente_de_curso_no_tiene_celdas(abrir_hoja, estudiantes):
    """Escenario "Área del docente de curso"."""
    page = abrir_hoja()

    page.locator('[data-area-pildora="0003"]').click()

    expect(page.get_by_text("Esta área la registra el docente de curso")).to_be_visible()
    expect(page.locator(".notas-nivel")).to_have_count(0)
    expect(page.locator("#guardar")).to_be_hidden()


def test_competencias_vuelve_a_las_notas_del_periodo_y_el_area(abrir_hoja, estudiantes, page):
    """Escenarios "Periodo anterior pedido" y "Volver a las notas" desde Competencias."""
    page = abrir_hoja()
    page.get_by_role("link", name="Competencias").click()
    expect(page.get_by_role("link", name="Registrar notas del III bimestre")).to_be_visible()
    page.get_by_role("button", name=re.compile(r"^II bimestre")).click()

    page.get_by_role("link", name="Registrar notas del II bimestre").click()

    expect(page.locator(".notas-periodo")).to_contain_text("B2")
    expect(page.locator(".notas-periodo")).to_contain_text("Anterior")
    expect(page.locator(f'[data-area-pildora="{MATEMATICA}"]')).to_have_attribute(
        "aria-pressed", "true"
    )


# --- Cambio al guardar (D7, servidor) ---


def test_una_nota_cambiada_desde_otro_lado_detiene_el_guardado_y_el_segundo_guarda(
    abrir_hoja, estudiantes, hoja_lista
):
    """Escenario "Cambio al guardar"."""
    ana, _ = estudiantes
    comp = competencia(MATEMATICA, 1)
    poner_nota(ana, comp, hoja_lista, "A")
    page = abrir_hoja()
    entrada(page, ana, 1).focus()
    page.keyboard.type("a")
    page.keyboard.type("d")
    expect(entrada(page, ana, 1)).to_have_value("AD")
    Calificacion.objects.filter(estudiante=ana, competencia=comp).update(
        nivel="B", conclusion_descriptiva=CONCLUSION
    )

    guardar(page)

    expect(page.locator("#mensaje-guardado")).to_contain_text(
        "1 nota cambió en otro dispositivo. Revisa las celdas marcadas y vuelve a guardar."
    )
    expect(entrada(page, ana, 1).locator("xpath=ancestor::td")).to_have_class(
        re.compile("notas-invalida")
    )
    assert notas_en_la_base() == {(ana.pk, comp.pk): ("B", CONCLUSION)}

    guardar(page)

    expect(page.locator("#mensaje-guardado")).to_contain_text("Matemática guardada")
    expect(estado(page)).to_have_text("Sin cambios")
    assert notas_en_la_base() == {(ana.pk, comp.pk): ("AD", "")}


# --- Notas faltantes del área (US-022) ---


def llenar_menos(estudiantes, periodo, omitidas):
    """Una «A» en cada celda de Matemática salvo las ``omitidas`` (pares estudiante, orden)."""
    for estudiante in estudiantes:
        for orden in range(1, 5):
            if (estudiante, orden) not in omitidas:
                poner_nota(estudiante, competencia(MATEMATICA, orden), periodo, "A")


def faltantes(page):
    return page.locator("#faltantes")


def test_la_barra_cuenta_las_notas_que_faltan(abrir_hoja, estudiantes, hoja_lista):
    """Escenario "Conteo por notas"."""
    ana, luis = estudiantes
    llenar_menos(estudiantes, hoja_lista, {(ana, 1), (ana, 3), (luis, 2)})
    page = abrir_hoja()

    expect(estado(page)).to_have_text("Sin cambios")
    expect(faltantes(page)).to_have_text("Faltan 3 notas")


def test_un_trasladado_sin_nivel_no_cuenta(abrir_hoja, estudiantes, hoja_lista, seccion_tutora):
    """Escenario "Trasladado sin nivel"."""
    ana, luis = estudiantes
    llenar_menos(estudiantes, hoja_lista, set())
    (mateo,) = crear_estudiantes(seccion_tutora, "SOTO, MATEO", estado="TRASLADADO")
    poner_nota(mateo, competencia(MATEMATICA, 1), hoja_lista, "A")
    page = abrir_hoja()

    expect(faltantes(page)).to_be_hidden()
    expect(page.locator("#cierre-area")).to_have_text("Matemática completa")


def test_el_borrador_baja_el_conteo_y_se_anuncia(abrir_hoja, estudiantes, hoja_lista):
    """Escenario "El borrador cuenta"."""
    ana, luis = estudiantes
    llenar_menos(estudiantes, hoja_lista, {(ana, 1), (luis, 1)})
    page = abrir_hoja()
    expect(faltantes(page)).to_have_text("Faltan 2 notas")

    entrada(page, ana, 1).focus()
    page.keyboard.type("a")

    expect(faltantes(page)).to_have_text("Falta 1 nota")
    expect(page.locator("#conteo-vivo")).to_have_text("Falta 1 nota en Matemática.")


def test_tocar_el_conteo_deja_solo_los_pendientes_y_enter_salta(
    abrir_hoja, estudiantes, hoja_lista
):
    """Escenarios "Flujo alternativo válido (US-022)", "Siguiente faltante" y "Fila completada"."""
    ana, luis = estudiantes
    llenar_menos(estudiantes, hoja_lista, {(ana, 2), (luis, 1), (luis, 4)})
    page = abrir_hoja()

    faltantes(page).click()

    expect(page.locator("#titulo-area")).to_have_text("Pendientes de registro · Matemática")
    expect(page.get_by_role("button", name="Ver todos")).to_be_visible()
    expect(entrada(page, ana, 2)).to_be_focused()
    page.keyboard.type("a")
    page.keyboard.press("Enter")
    expect(entrada(page, luis, 1)).to_be_focused()
    page.keyboard.type("a")
    page.keyboard.press("Enter")
    expect(entrada(page, luis, 4)).to_be_focused()
    expect(page.locator('tr[data-fila="0"]')).to_contain_text("Completa")
    expect(page.locator("#detalle-hoja")).to_have_text("1 estudiante con notas faltantes")

    page.keyboard.type("a")
    expect(page.locator("#detalle-hoja")).to_have_text("Todas las notas registradas")
    expect(page.locator('tr[data-fila="0"]')).to_be_visible()
    page.get_by_role("button", name="Ver todos").click()
    expect(page.locator("#titulo-area")).to_have_text("Matemática")


def test_en_el_celular_el_panel_salta_entre_faltantes(abrir_hoja, estudiantes, hoja_lista):
    """Escenario "Pendientes de registro" en el celular."""
    ana, luis = estudiantes
    llenar_menos(estudiantes, hoja_lista, {(ana, 2), (luis, 3)})
    page = abrir_hoja(ancho=360)

    faltantes(page).click()

    expect(page.locator("#panel-editor")).to_be_visible()
    expect(page.locator("#panel-estudiante")).to_have_text("QUISPE, ANA")
    expect(page.locator("#panel-competencia")).to_contain_text("C2")
    page.locator('#panel-niveles [data-elegir="A"]').click()
    page.locator("#siguiente").click()
    expect(page.locator("#panel-estudiante")).to_have_text("ROJAS, LUIS")
    expect(page.locator("#panel-competencia")).to_contain_text("C3")


# --- Área completa ---


def test_con_todo_guardado_dice_area_completa(abrir_hoja, estudiantes, hoja_lista):
    """Escenario "Matemática completa"."""
    llenar_menos(estudiantes, hoja_lista, set())
    page = abrir_hoja()

    expect(page.locator("#cierre-area")).to_have_text("Matemática completa")
    expect(faltantes(page)).to_be_hidden()


def test_completa_sin_guardar_dice_un_cambio_y_sin_faltantes(abrir_hoja, estudiantes, hoja_lista):
    """Escenario "Completa sin guardar"."""
    ana, _ = estudiantes
    llenar_menos(estudiantes, hoja_lista, {(ana, 4)})
    page = abrir_hoja()
    entrada(page, ana, 4).focus()

    page.keyboard.type("a")

    expect(page.locator("#estado-guardado")).to_have_text("1 cambio sin guardar")
    expect(page.locator("#sin-faltantes")).to_have_text("Sin notas faltantes")
    expect(page.locator("#cierre-area")).to_be_hidden()
    guardar(page)
    expect(page.locator("#cierre-area")).to_have_text("Matemática completa")


# --- Hoja accesible y sin desplazamiento horizontal de la página ---

SLOW_4G = {
    "offline": False,
    "downloadThroughput": 1.6 * 1024 * 1024 / 8 * 0.9,
    "uploadThroughput": 750 * 1024 / 8 * 0.9,
    "latency": 150 * 3.75,
}
PERSONAL_SOCIAL = "0006"


def sin_desplazamiento_horizontal(page):
    return page.evaluate(
        "document.documentElement.scrollWidth <= document.documentElement.clientWidth"
    )


@pytest.mark.parametrize("ancho", ANCHOS)
@pytest.mark.parametrize("tema", TEMAS)
def test_axe_con_notas_errores_filtro_y_dialogo(abrir_hoja, estudiantes, hoja_lista, ancho, tema):
    """Escenario "Axe en ambos temas": con notas, errores, panel o recuadro, filtro y diálogo."""
    ana, luis = estudiantes
    poner_nota(ana, competencia(MATEMATICA, 1), hoja_lista, "B")
    poner_nota(luis, competencia(MATEMATICA, 2), hoja_lista, "A")
    page = abrir_hoja(ancho=ancho, tema=tema)
    sufijo = f"{ancho}-{tema}"
    revisar_con_axe(page, f"hoja-notas-{sufijo}")
    assert sin_desplazamiento_horizontal(page)

    # Con errores: una C sin conclusión.
    if ancho >= 960:
        entrada(page, luis, 3).focus()
        page.keyboard.type("c")
        revisar_con_axe(page, f"hoja-notas-recuadro-{sufijo}")
        page.keyboard.press("Escape")
    else:
        boton_movil(page, luis, 3).click()
        page.locator('#panel-niveles [data-elegir="C"]').click()
        revisar_con_axe(page, f"hoja-notas-panel-{sufijo}")
        page.locator("#cerrar-panel").click()
    guardar(page)
    expect(page.locator("#mensaje-guardado")).to_contain_text("No se guardó nada")
    revisar_con_axe(page, f"hoja-notas-errores-{sufijo}")
    assert sin_desplazamiento_horizontal(page)

    # Con el filtro.
    faltantes(page).click()
    expect(page.locator("#titulo-area")).to_contain_text("Pendientes de registro")
    if ancho < 960:
        page.locator("#cerrar-panel").click()
    revisar_con_axe(page, f"hoja-notas-filtro-{sufijo}")

    # Con el diálogo de salida.
    page.get_by_role("link", name="Competencias").click()
    expect(page.locator("#confirmar-salida")).to_be_visible()
    revisar_con_axe(page, f"hoja-notas-dialogo-{sufijo}")


@pytest.mark.parametrize("ancho", ANCHOS)
@pytest.mark.parametrize("tema", TEMAS)
def test_axe_en_vacaciones(
    live_server, page, docente, clave, seccion_tutora, monkeypatch, ie, hoja_lista, ancho, tema
):
    """Escenario "Axe en ambos temas": en vacaciones."""
    fijar_hora_de_lima(monkeypatch, datetime.datetime(2027, 8, 1, 9, 0, tzinfo=LIMA))
    con_pantalla(page, ancho, tema)
    ingresar(page, live_server, docente, clave)
    page.wait_for_url(f"{live_server.url}/docente/")
    page.goto(url_hoja(live_server, seccion_tutora, area=MATEMATICA))
    expect(page.get_by_text("Hoy no hay un periodo vigente")).to_be_visible()
    revisar_con_axe(page, f"hoja-notas-vacaciones-{ancho}-{tema}")
    assert sin_desplazamiento_horizontal(page)


@pytest.mark.parametrize("ancho", ANCHOS)
@pytest.mark.parametrize("tema", TEMAS)
def test_axe_sin_periodos(
    live_server, page, docente, clave, seccion_tutora, monkeypatch, universo_ie, ancho, tema
):
    """Escenario "Axe en ambos temas": sin periodos."""
    fijar_hora_de_lima(monkeypatch, datetime.datetime(2027, 10, 30, 9, 0, tzinfo=LIMA))
    con_pantalla(page, ancho, tema)
    ingresar(page, live_server, docente, clave)
    page.wait_for_url(f"{live_server.url}/docente/")
    page.goto(url_hoja(live_server, seccion_tutora))
    expect(page.get_by_text("La dirección aún no configura los periodos")).to_be_visible()
    revisar_con_axe(page, f"hoja-notas-sin-periodos-{ancho}-{tema}")
    assert sin_desplazamiento_horizontal(page)


@pytest.mark.parametrize("ancho", [320, 360])
def test_personal_social_no_desplaza_la_pagina_y_la_tira_se_desplaza_sola(
    abrir_hoja, estudiantes, seccion_tutora, bimestres, ancho
):
    """Escenario "Sin desplazamiento de la página": 5 competencias a 320 y 360 px."""
    marcar(seccion_tutora, bimestres[2], ids_de(PERSONAL_SOCIAL))
    page = abrir_hoja(ancho=ancho, area=PERSONAL_SOCIAL)

    expect(page.locator(".notas-tabla tbody tr").first).to_be_visible()
    assert sin_desplazamiento_horizontal(page)
    tira = page.locator(".notas-tira")
    assert tira.evaluate("el => el.scrollWidth > el.clientWidth")
    assert tira.evaluate("el => getComputedStyle(el).overflowX") == "auto"


def test_las_areas_tactiles_miden_44_px(abrir_hoja, estudiantes):
    """Píldoras, celdas y niveles de 44 px en el celular."""
    ana, _ = estudiantes
    page = abrir_hoja(ancho=360)

    for pildora in page.locator("[data-area-pildora]").all():
        assert pildora.bounding_box()["height"] >= 44
    assert boton_movil(page, ana, 1).bounding_box()["height"] >= 44
    assert boton_movil(page, ana, 1).bounding_box()["width"] >= 43
    boton_movil(page, ana, 1).click()
    for nivel in page.locator("#panel-niveles button").all():
        assert nivel.bounding_box()["height"] >= 44


def test_el_lector_lee_estudiante_competencia_y_nivel(abrir_hoja, estudiantes, hoja_lista):
    """Escenario "Lector de pantalla en una celda"."""
    ana, _ = estudiantes
    poner_nota(ana, competencia(MATEMATICA, 1), hoja_lista, "A")
    page = abrir_hoja()

    expect(entrada(page, ana, 1)).to_have_attribute(
        "aria-label", re.compile(r"QUISPE, ANA, C1, A: Logro esperado")
    )
    expect(entrada(page, ana, 2)).to_have_attribute(
        "aria-label", re.compile(r"QUISPE, ANA, C2, Sin nivel")
    )


def test_la_hoja_mas_grande_con_slow_4g(
    live_server, page, docente, clave, seccion_tutora, monkeypatch, ie, bimestres, browser_name
):
    """La hoja más grande (Personal Social, 5 competencias, 30 estudiantes) con Slow 4G."""
    if browser_name != "chromium":
        pytest.skip("El perfil de red por CDP existe solo en Chromium.")
    marcar(seccion_tutora, bimestres[2], ids_de(PERSONAL_SOCIAL))
    crear_estudiantes(seccion_tutora, *[f"ESTUDIANTE{n:02d}, PRUEBA" for n in range(30)])
    fijar_hora_de_lima(monkeypatch, datetime.datetime(2027, 10, 30, 9, 0, tzinfo=LIMA))
    con_pantalla(page, 360, "light")
    ingresar(page, live_server, docente, clave)
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
    page.goto(url_hoja(live_server, seccion_tutora, area=PERSONAL_SOCIAL))
    expect(page.locator(".notas-celda-movil").first).to_be_visible()
    page.evaluate("document.fonts.ready")
    segundos = time.perf_counter() - inicio

    assert transferidos
    total = sum(transferidos)
    print(f"\nSlow 4G en la hoja: {total / 1024:.1f} KB, {segundos:.2f} s")
    assert total <= 2 * 1024 * 1024, f"{total} bytes"
    assert segundos <= 5, f"{segundos:.2f} s"
