"""Borradores de la hoja de notas en el dispositivo (spec registro-notas; design de US-020, D10).

``notas-borrador.js`` guarda en ``localStorage`` los cambios sin guardar de cada hoja, por cuenta,
sección, periodo y área, solo con identificadores, niveles, conclusiones y fechas; ``notas.js``
los recupera y ``menu.js`` los borra al cerrar sesión. El 30 de octubre de 2027 es el bimestre 3
vigente. Necesita el CSS compilado y Chromium:
``DJANGO_ALLOW_ASYNC_UNSAFE=true uv run pytest -m e2e --browser chromium src/backend/notas``.
"""

import json
import re

import pytest
from playwright.sync_api import expect

from cuentas.tests.e2e import con_pantalla, envejecer_sesion, ingresar
from institucion.models import Estudiante
from notas.tests.conftest import COMUNICACION, CONCLUSION, MATEMATICA, competencia, poner_nota
from notas.tests.e2e import boton_movil, entrada, estado, guardar, notas_en_la_base, url_hoja

pytestmark = [pytest.mark.e2e, pytest.mark.django_db(transaction=True)]


@pytest.fixture(autouse=True)
def _catalogo_cargado(catalogo):
    """El catálogo debe estar antes de crear la institución, que copia sus áreas."""


FECHA = re.compile(r"Cambios sin guardar del \d{2}/\d{2}/\d{4}, \d{2}:\d{2}")


def llave_borrador(docente, seccion, numero=3, area=MATEMATICA):
    """La clave del borrador de un área en ``localStorage`` (D10)."""
    return f"cd:notas:v1:u{docente.pk}:s{seccion.pk}:p{numero}:a{area}"


def almacenamiento(page):
    """Todo lo que la página dejó en ``localStorage``."""
    return page.evaluate("() => Object.fromEntries(Object.entries(localStorage))")


def borradores_de(page, docente):
    prefijo = f"cd:notas:v1:u{docente.pk}:"
    return [clave for clave in almacenamiento(page) if clave.startswith(prefijo)]


def aceptar_salidas(page):
    """Acepta el aviso del navegador al recargar o salir con cambios sin guardar."""
    page.on("dialog", lambda dialogo: dialogo.accept())


@pytest.fixture
def otro_navegador(browser, live_server, docente, clave, seccion_tutora):
    """Abre la hoja de la misma tutora en otro navegador (otro dispositivo), con su sesión."""
    contextos = []

    def abrir(ancho=1280):
        contexto = browser.new_context()
        contextos.append(contexto)
        pagina = contexto.new_page()
        con_pantalla(pagina, ancho, "light")
        ingresar(pagina, live_server, docente, clave)
        pagina.wait_for_url(f"{live_server.url}/docente/")
        pagina.goto(url_hoja(live_server, seccion_tutora, area=MATEMATICA))
        expect(pagina.locator(".notas-tabla")).to_be_visible()
        return pagina

    yield abrir
    for contexto in contextos:
        contexto.close()


def otra_pestana(page, live_server, seccion):
    """La misma hoja en otra pestaña del mismo navegador."""
    pagina = page.context.new_page()
    con_pantalla(pagina, 1280, "light")
    pagina.goto(url_hoja(live_server, seccion, area=MATEMATICA))
    expect(pagina.locator(".notas-tabla")).to_be_visible()
    return pagina


def escribir(page, estudiante, orden, nivel, conclusion=None):
    entrada(page, estudiante, orden).focus()
    page.keyboard.type(nivel.lower()[0])
    if nivel == "AD":
        page.keyboard.type("d")
    if conclusion is not None:
        page.locator("#conclusion-pc").fill(conclusion)
        page.locator("#listo-nota").click()


# --- Borradores en el dispositivo ---


def test_el_borrador_vuelve_al_recargar_y_descartar_lo_borra(
    abrir_hoja, estudiantes, docente, seccion_tutora
):
    """Escenarios "Volver con un borrador" (al recargar) y "Descartar"."""
    ana, _ = estudiantes
    page = abrir_hoja()
    escribir(page, ana, 1, "A")
    llave = llave_borrador(docente, seccion_tutora)
    assert llave in almacenamiento(page)

    aceptar_salidas(page)
    page.reload()

    expect(entrada(page, ana, 1)).to_have_value("A")
    expect(estado(page)).to_have_text("1 cambio sin guardar")
    borrador = page.locator("#borrador")
    expect(borrador).to_contain_text(FECHA)
    expect(borrador).to_contain_text("Conservados en este dispositivo.")
    expect(borrador.get_by_role("button", name="Guardar")).to_be_visible()

    borrador.get_by_role("button", name="Descartar").click()

    expect(entrada(page, ana, 1)).to_have_value("")
    expect(borrador).to_be_hidden()
    expect(estado(page)).to_have_text("Sin cambios")
    assert llave not in almacenamiento(page)
    assert notas_en_la_base() == {}


def test_el_borrador_sobrevive_a_cerrar_el_navegador_y_su_guardar_guarda(
    abrir_hoja, estudiantes, browser, live_server, docente, clave, seccion_tutora
):
    """Escenario "Volver con un borrador" tras cerrar el navegador, sin la cookie de sesión."""
    ana, _ = estudiantes
    page = abrir_hoja()
    escribir(page, ana, 1, "B", CONCLUSION)
    origenes = page.context.storage_state()["origins"]
    page.context.close()

    contexto = browser.new_context(storage_state={"cookies": [], "origins": origenes})
    nueva = contexto.new_page()
    con_pantalla(nueva, 1280, "light")
    ingresar(nueva, live_server, docente, clave)
    nueva.wait_for_url(f"{live_server.url}/docente/")
    nueva.goto(url_hoja(live_server, seccion_tutora, area=MATEMATICA))

    expect(entrada(nueva, ana, 1)).to_have_value("B")
    expect(nueva.locator("#borrador")).to_contain_text(FECHA)
    nueva.locator("#borrador").get_by_role("button", name="Guardar").click()

    expect(nueva.locator("#mensaje-guardado")).to_contain_text("Matemática guardada")
    expect(nueva.locator("#borrador")).to_be_hidden()
    assert notas_en_la_base() == {(ana.pk, competencia(MATEMATICA, 1).pk): ("B", CONCLUSION)}
    assert borradores_de(nueva, docente) == []
    contexto.close()


def test_el_dispositivo_guarda_solo_identificadores_niveles_conclusiones_y_fechas(
    abrir_hoja, estudiantes, docente, seccion_tutora, hoja_lista
):
    """Escenario "Sin nombres en el dispositivo"."""
    ana, luis = estudiantes
    c1, c2 = competencia(MATEMATICA, 1), competencia(MATEMATICA, 2)
    poner_nota(luis, c2, hoja_lista, "A")
    page = abrir_hoja()
    escribir(page, ana, 1, "B", CONCLUSION)
    escribir(page, luis, 2, "AD")

    guardados = almacenamiento(page)
    llave = llave_borrador(docente, seccion_tutora)
    assert [clave for clave in guardados if clave.startswith("cd:notas:")] == [llave]
    valor = json.loads(guardados[llave])
    assert set(valor) == {"v", "fecha", "rev", "celdas"}
    assert valor["v"] == 1
    assert valor["celdas"] == {
        f"{ana.pk}-{c1.pk}": {"nivel": "B", "conclusion": CONCLUSION, "base": None},
        f"{luis.pk}-{c2.pk}": {
            "nivel": "AD",
            "conclusion": "",
            "base": {"nivel": "A", "conclusion": ""},
        },
    }
    texto = json.dumps(guardados, ensure_ascii=False)
    for nombre in ("QUISPE", "ANA", "ROJAS", "LUIS", "Matemática", c1.nombre):
        assert nombre not in texto


def test_otra_cuenta_en_el_mismo_navegador_no_ve_el_borrador(
    abrir_hoja, estudiantes, live_server, docente, otra_docente, clave, seccion_tutora
):
    """Escenario "Otra cuenta en el mismo navegador": la sección pasa a otra docente."""
    ana, _ = estudiantes
    page = abrir_hoja()
    escribir(page, ana, 1, "A")
    envejecer_sesion(page, 61)
    seccion_tutora.docente = None  # La sección cambia de docente en dos pasos (RF-005).
    seccion_tutora.save()
    seccion_tutora.docente = otra_docente
    seccion_tutora.save()

    aceptar_salidas(page)
    page.goto(url_hoja(live_server, seccion_tutora, area=MATEMATICA))
    page.wait_for_url(re.compile(r"/ingresar/"))
    ingresar(page, live_server, otra_docente, clave)
    page.wait_for_url(f"{live_server.url}/docente/")
    page.goto(url_hoja(live_server, seccion_tutora, area=MATEMATICA))

    expect(entrada(page, ana, 1)).to_have_value("")
    expect(page.locator("#borrador")).to_be_hidden()
    expect(estado(page)).to_have_text("Sin cambios")
    assert llave_borrador(docente, seccion_tutora) in almacenamiento(page)


def test_sin_almacenamiento_la_hoja_guarda_igual(abrir_hoja, estudiantes, page):
    """Requisito "Borradores en el dispositivo": sin almacenamiento la hoja funciona igual."""
    page.add_init_script(
        "Object.defineProperty(window, 'localStorage', { configurable: true, get() {"
        " throw new DOMException('Bloqueado', 'SecurityError'); } });"
    )
    ana, _ = estudiantes
    page = abrir_hoja()
    escribir(page, ana, 1, "A")
    expect(estado(page)).to_have_text("1 cambio sin guardar")

    guardar(page)

    expect(page.locator("#mensaje-guardado")).to_contain_text("Matemática guardada")
    assert notas_en_la_base() == {(ana.pk, competencia(MATEMATICA, 1).pk): ("A", "")}


def test_un_estudiante_que_ya_no_es_activo_sale_del_borrador_con_aviso(
    abrir_hoja, estudiantes, docente, seccion_tutora
):
    """Design D10: las celdas que ya no se podrían guardar se descartan y la hoja lo dice."""
    ana, luis = estudiantes
    page = abrir_hoja()
    escribir(page, ana, 1, "A")
    escribir(page, luis, 1, "A")
    Estudiante.objects.filter(pk=ana.pk).update(estado=Estudiante.Estado.TRASLADADO)

    aceptar_salidas(page)
    page.reload()

    borrador = page.locator("#borrador")
    expect(borrador).to_contain_text("1 cambio del borrador ya no se puede guardar")
    expect(borrador).to_contain_text("el estudiante ya no está activo")
    expect(entrada(page, ana, 1)).to_have_count(0)
    expect(entrada(page, luis, 1)).to_have_value("A")
    expect(estado(page)).to_have_text("1 cambio sin guardar")
    celdas = json.loads(almacenamiento(page)[llave_borrador(docente, seccion_tutora)])["celdas"]
    assert list(celdas) == [f"{luis.pk}-{competencia(MATEMATICA, 1).pk}"]


# --- Cerrar sesión borra los borradores ---


def test_cerrar_sesion_desde_la_portada_borra_los_borradores_de_la_cuenta(
    abrir_hoja, estudiantes, live_server, docente
):
    """Escenario "Cerrar sesión desde la portada": solo se borran los de esa cuenta."""
    ana, _ = estudiantes
    page = abrir_hoja()
    escribir(page, ana, 1, "A")
    ajena = "cd:notas:v1:u999999:s1:p3:a063"
    page.evaluate(
        f"() => {{ localStorage.setItem('{ajena}', '{{}}'); localStorage.setItem('otra', 'x'); }}"
    )
    assert borradores_de(page, docente)

    aceptar_salidas(page)
    page.goto(f"{live_server.url}/docente/")
    page.get_by_label("Menú de la cuenta").click()
    page.get_by_role("button", name="Cerrar sesión").click()
    page.wait_for_url(re.compile(r"/ingresar/"))

    assert borradores_de(page, docente) == []
    guardados = almacenamiento(page)
    assert ajena in guardados
    assert "otra" in guardados


def test_el_cierre_por_inactividad_conserva_el_borrador(
    abrir_hoja, estudiantes, live_server, docente, clave, seccion_tutora
):
    """Escenario "Cierre por inactividad"."""
    ana, _ = estudiantes
    page = abrir_hoja()
    escribir(page, ana, 1, "A")
    envejecer_sesion(page, 61)

    aceptar_salidas(page)
    page.goto(url_hoja(live_server, seccion_tutora, area=MATEMATICA))
    page.wait_for_url(re.compile(r"/ingresar/"))
    ingresar(page, live_server, docente, clave)
    page.wait_for_url(f"{live_server.url}/docente/")
    page.goto(url_hoja(live_server, seccion_tutora, area=MATEMATICA))

    expect(entrada(page, ana, 1)).to_have_value("A")
    expect(page.locator("#borrador")).to_contain_text(FECHA)


# --- Nota cambiada desde otro dispositivo (D7 en el cliente) ---


def test_un_borrador_mas_antiguo_que_la_nota_avisa_y_guardar_guarda_lo_que_muestra(
    abrir_hoja, otro_navegador, estudiantes, hoja_lista
):
    """Escenarios "Borrador más antiguo que la nota" y "Nada cambió en otro lado"."""
    ana, luis = estudiantes
    comp = competencia(MATEMATICA, 1)
    poner_nota(ana, comp, hoja_lista, "A")
    laptop = abrir_hoja()
    escribir(laptop, ana, 1, "B", CONCLUSION)
    escribir(laptop, luis, 1, "A")

    celular = otro_navegador(ancho=360)
    boton_movil(celular, ana, 1).click()
    celular.locator('#panel-niveles [data-elegir="AD"]').click()
    celular.locator("#cerrar-panel").click()
    guardar(celular)
    expect(celular.locator("#mensaje-guardado")).to_contain_text("Matemática guardada")

    aceptar_salidas(laptop)
    laptop.reload()

    expect(entrada(laptop, ana, 1)).to_have_value("B")
    expect(entrada(laptop, ana, 1)).to_have_attribute(
        "aria-label", re.compile("Ahora guardada: AD")
    )
    expect(entrada(laptop, luis, 1)).not_to_have_attribute(
        "aria-label", re.compile("Ahora guardada")
    )
    aviso = laptop.locator("#mensaje-guardado")
    expect(aviso).to_contain_text("1 nota cambió en otro dispositivo")
    expect(aviso).to_contain_text("Ana · C1: AD")

    guardar(laptop)

    expect(aviso).to_contain_text("Matemática guardada")
    assert notas_en_la_base()[(ana.pk, comp.pk)] == ("B", CONCLUSION)
    assert notas_en_la_base()[(luis.pk, comp.pk)] == ("A", "")


def test_una_nota_cambiada_en_otro_navegador_detiene_el_guardado(
    abrir_hoja, otro_navegador, estudiantes, hoja_lista
):
    """Escenario "Cambio al guardar", con dos navegadores de la misma cuenta."""
    ana, _ = estudiantes
    comp = competencia(MATEMATICA, 1)
    poner_nota(ana, comp, hoja_lista, "A")
    laptop = abrir_hoja()
    escribir(laptop, ana, 1, "AD")

    celular = otro_navegador()
    escribir(celular, ana, 1, "C", CONCLUSION)
    guardar(celular)
    expect(celular.locator("#mensaje-guardado")).to_contain_text("Matemática guardada")

    guardar(laptop)

    expect(laptop.locator("#mensaje-guardado")).to_contain_text(
        "1 nota cambió en otro dispositivo. Revisa las celdas marcadas y vuelve a guardar."
    )
    expect(entrada(laptop, ana, 1)).to_have_attribute("aria-label", re.compile("Ahora guardada: C"))
    assert notas_en_la_base() == {(ana.pk, comp.pk): ("C", CONCLUSION)}

    guardar(laptop)

    expect(laptop.locator("#mensaje-guardado")).to_contain_text("Matemática guardada")
    assert notas_en_la_base() == {(ana.pk, comp.pk): ("AD", "")}


# --- Dos pestañas de la misma hoja (D11) ---


def test_lo_que_cambia_en_una_pestana_aparece_en_la_otra(
    abrir_hoja, estudiantes, live_server, seccion_tutora
):
    """Escenario "Cambio en otra pestaña"."""
    ana, _ = estudiantes
    uno = abrir_hoja()
    dos = otra_pestana(uno, live_server, seccion_tutora)

    escribir(uno, ana, 1, "A")

    expect(entrada(dos, ana, 1)).to_have_value("A")
    expect(estado(dos)).to_have_text("1 cambio sin guardar")
    expect(dos.locator("#mensaje-guardado")).to_contain_text(
        "Se sumó 1 cambio hecho en otra pestaña"
    )
    expect(dos.locator(f'[data-area-pildora="{MATEMATICA}"]')).to_contain_text(
        "Cambios sin guardar"
    )


def test_la_misma_celda_en_las_dos_pestanas_conserva_lo_de_cada_una_y_avisa(
    abrir_hoja, estudiantes, live_server, seccion_tutora
):
    """Escenario "Misma celda en las dos"."""
    _, luis = estudiantes
    uno = abrir_hoja()
    dos = otra_pestana(uno, live_server, seccion_tutora)
    escribir(uno, luis, 2, "A")
    expect(entrada(dos, luis, 2)).to_have_value("A")

    escribir(dos, luis, 2, "AD")

    choque = "Una celda se editó en ambas; quedó lo escrito aquí: Luis · C2."
    expect(dos.locator("#mensaje-guardado")).to_contain_text(choque)
    expect(uno.locator("#mensaje-guardado")).to_contain_text(choque)
    expect(entrada(uno, luis, 2)).to_have_value("A")
    expect(entrada(dos, luis, 2)).to_have_value("AD")


# --- Salir sin guardar (D11) ---


def test_salir_con_cambios_nombra_las_areas_de_todos_los_periodos_y_conserva_el_borrador(
    abrir_hoja, estudiantes, docente, seccion_tutora
):
    """Escenarios "Salir con cambios" y "Salir sin guardar", con un borrador de B2 guardado."""
    ana, _ = estudiantes
    page = abrir_hoja()
    de_b2 = llave_borrador(docente, seccion_tutora, numero=2)
    celda = f"{ana.pk}-{competencia(MATEMATICA, 1).pk}"
    valor = {"v": 1, "fecha": "2027-07-20T10:00:00Z", "rev": "x-1", "celdas": {}}
    valor["celdas"][celda] = {"nivel": "A", "conclusion": "", "base": None}
    page.evaluate(
        "([clave, valor]) => localStorage.setItem(clave, valor)", [de_b2, json.dumps(valor)]
    )
    escribir(page, ana, 1, "A")
    page.locator(f'[data-area-pildora="{COMUNICACION}"]').click()
    page.locator(".notas-nivel").first.focus()
    page.keyboard.type("a")
    avisos = []
    page.on("dialog", lambda dialogo: (avisos.append(dialogo.type), dialogo.dismiss()))

    page.get_by_role("link", name="Competencias").click()

    dialogo = page.locator("#confirmar-salida")
    expect(dialogo).to_be_visible()
    pendientes = page.locator("#areas-pendientes li")
    expect(pendientes).to_have_count(3)
    for texto in ("Matemática · B3", "Comunicación · B3", "Matemática · B2"):
        expect(pendientes.filter(has_text=texto)).to_have_count(1)
    expect(page.locator("#seguir-editando")).to_be_focused()
    expect(dialogo).to_contain_text("Los borradores quedan en este dispositivo.")

    page.locator("#salir-sin-guardar").click()

    page.wait_for_url(re.compile(r"/competencias/"))
    assert avisos == []
    guardados = almacenamiento(page)
    assert llave_borrador(docente, seccion_tutora) in guardados
    assert llave_borrador(docente, seccion_tutora, area=COMUNICACION) in guardados
    assert de_b2 in guardados


def test_cerrar_sesion_con_cambios_dice_que_los_borradores_se_borraran(
    abrir_hoja, estudiantes, docente
):
    """Escenario "Cerrar sesión con cambios"."""
    ana, _ = estudiantes
    page = abrir_hoja()
    escribir(page, ana, 1, "A")

    page.get_by_label("Menú de la cuenta").click()
    page.get_by_role("button", name="Cerrar sesión").click()

    expect(page.locator("#confirmar-salida")).to_be_visible()
    expect(page.locator("#aviso-borradores")).to_have_text(
        "Los borradores se borrarán de este dispositivo al cerrar sesión."
    )
    assert borradores_de(page, docente)

    page.locator("#salir-sin-guardar").click()

    page.wait_for_url(re.compile(r"/ingresar/"))
    assert borradores_de(page, docente) == []


def test_cerrar_sesion_desde_competencias_con_marcas_sin_guardar_borra_los_borradores(
    abrir_hoja, estudiantes, docente
):
    """Escenario "Cerrar sesión desde la portada" en otra pantalla que detiene la salida: «desde
    cualquier pantalla», también si Competencias pregunta antes por sus marcas sin guardar."""
    ana, _ = estudiantes
    page = abrir_hoja()
    escribir(page, ana, 1, "A")
    page.get_by_role("link", name="Competencias").click()
    page.locator("#salir-sin-guardar").click()
    page.wait_for_url(re.compile(r"/competencias/"))
    page.locator(f'label[for="c-{competencia(MATEMATICA, 1).pk}"]').click()
    assert borradores_de(page, docente)

    page.get_by_label("Menú de la cuenta").click()
    page.get_by_role("button", name="Cerrar sesión").click()
    page.get_by_role("button", name="Salir sin guardar").click()

    page.wait_for_url(re.compile(r"/ingresar/"))
    assert borradores_de(page, docente) == []


def test_seguir_editando_tras_cerrar_sesion_conserva_el_borrador(abrir_hoja, estudiantes, docente):
    """Escenario "Cerrar sesión con cambios": «Seguir editando» no cierra sesión ni borra nada."""
    ana, _ = estudiantes
    page = abrir_hoja()
    escribir(page, ana, 1, "A")
    page.get_by_label("Menú de la cuenta").click()
    page.get_by_role("button", name="Cerrar sesión").click()

    page.locator("#seguir-editando").click()

    expect(page.locator("#confirmar-salida")).to_be_hidden()
    expect(page.locator(".notas-tabla")).to_be_visible()
    assert borradores_de(page, docente)
    page.get_by_role("link", name="Competencias").click()
    expect(page.locator("#aviso-borradores")).to_contain_text(
        "Los borradores quedan en este dispositivo."
    )


def test_recargar_con_cambios_muestra_el_aviso_del_navegador(abrir_hoja, estudiantes):
    """Escenario "Recargar con cambios"."""
    ana, _ = estudiantes
    page = abrir_hoja()
    escribir(page, ana, 1, "A")
    avisos = []
    page.on("dialog", lambda dialogo: (avisos.append(dialogo.type), dialogo.accept()))

    page.reload()

    expect(entrada(page, ana, 1)).to_have_value("A")
    assert avisos == ["beforeunload"]


# --- Revisión adversarial (A2) ---


def test_tras_una_respuesta_perdida_volver_al_valor_anterior_sigue_siendo_un_cambio(
    abrir_hoja, estudiantes, hoja_lista
):
    """«Guardado sin conexión» con resultado incierto: el servidor guardó AD pero la respuesta no
    llegó. Volver a elegir A no puede dar «Sin cambios»: guardar debe dejar A en la base (D7 avisa
    que ahora está AD y el segundo guardado deja lo que muestra la hoja)."""
    ana, _ = estudiantes
    comp = competencia(MATEMATICA, 1)
    poner_nota(ana, comp, hoja_lista, "A")
    page = abrir_hoja()

    def perder_respuesta(ruta):
        if ruta.request.method != "POST":
            ruta.fallback()
            return
        ruta.fetch()
        ruta.abort()

    ruta_guardar = re.compile(r"/notas/\d+/\w+/$")
    page.route(ruta_guardar, perder_respuesta)
    escribir(page, ana, 1, "AD")
    guardar(page)
    expect(page.locator("#guardar")).to_have_text("Reintentar")
    assert notas_en_la_base() == {(ana.pk, comp.pk): ("AD", "")}
    page.unroute(ruta_guardar)

    escribir(page, ana, 1, "A")

    expect(estado(page)).to_have_text("1 cambio sin guardar")
    guardar(page)
    expect(entrada(page, ana, 1)).to_have_attribute("aria-label", re.compile("Ahora guardada: AD"))
    guardar(page)
    expect(page.locator("#mensaje-guardado")).to_contain_text("Matemática guardada")
    assert notas_en_la_base() == {(ana.pk, comp.pk): ("A", "")}


def test_un_cambio_de_otra_pestana_con_otra_base_avisa_la_nota_cambiada(
    abrir_hoja, estudiantes, hoja_lista, live_server, seccion_tutora
):
    """«Dos pestañas» con «Nota cambiada desde otro dispositivo»: la pestaña uno abrió A, otro
    dispositivo guardó AD y la pestaña dos abrió AD. Lo que edita la uno llega a la dos con su
    base A: la dos marca la celda como en «Borrador más antiguo que la nota» (D7)."""
    ana, _ = estudiantes
    comp = competencia(MATEMATICA, 1)
    nota = poner_nota(ana, comp, hoja_lista, "A")
    uno = abrir_hoja()
    nota.nivel = "AD"
    nota.save()
    dos = otra_pestana(uno, live_server, seccion_tutora)
    expect(entrada(dos, ana, 1)).to_have_value("AD")

    escribir(uno, ana, 1, "C", CONCLUSION)

    expect(entrada(dos, ana, 1)).to_have_value("C")
    expect(entrada(dos, ana, 1)).to_have_attribute("aria-label", re.compile("Ahora guardada: AD"))
    expect(dos.locator("#mensaje-guardado")).to_contain_text("1 nota cambió en otro dispositivo")
    expect(dos.locator("#mensaje-guardado")).to_contain_text("Ana · C1: AD")


def test_cerrar_sesion_en_otra_pestana_impide_volver_a_escribir_borradores(
    abrir_hoja, estudiantes, docente, live_server, seccion_tutora
):
    """«Cerrar sesión borra los borradores» con otra pestaña abierta: la que sigue abierta borra
    los cambios de su memoria y ya no escribe en el dispositivo (D10)."""
    ana, luis = estudiantes
    uno = abrir_hoja()
    dos = otra_pestana(uno, live_server, seccion_tutora)
    escribir(uno, ana, 1, "A")
    expect(entrada(dos, ana, 1)).to_have_value("A")

    uno.get_by_label("Menú de la cuenta").click()
    uno.get_by_role("button", name="Cerrar sesión").click()
    uno.locator("#salir-sin-guardar").click()
    uno.wait_for_url(re.compile(r"/ingresar/"))

    expect(dos.locator("#mensaje-guardado")).to_contain_text("Cerraste sesión en otra pestaña")
    expect(entrada(dos, ana, 1)).to_have_value("")
    escribir(dos, luis, 1, "A")
    expect(entrada(dos, luis, 1)).to_have_value("A")
    assert borradores_de(dos, docente) == []
