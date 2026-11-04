"""La plantilla de Sesiones (spec envio-sesiones; design de US-010, US-014 y EN-03, D8 y D9).

El servidor dibuja la pantalla, el popup «Subir una sesión» y el de los términos; ``sesiones.js``
los abre, valida y envía (sus pruebas son las de punta a punta). Aquí se revisa el HTML.
"""

import re
import uuid

import pytest

from institucion.models import Seccion
from repositorio.tests.archivos import pdf

pytestmark = pytest.mark.django_db

URL_INICIO = "/docente/sesiones/"
URL_ENVIAR = "/docente/sesiones/enviar/"

# Doc 09 §4, literal.
TERMINOS = [
    "Al publicar esta sesión en el repositorio, declaro que:",
    "Soy autor(a) de la sesión o cuento con permiso para compartirla.",
    "Autorizo que los docentes y la dirección de la institución la vean, la descarguen y la"
    " adapten.",
    "El archivo no contiene datos personales de estudiantes, como nombres o notas.",
    "Puedo retirarla del repositorio en cualquier momento eliminándola.",
]


@pytest.fixture
def cliente(client, docente):
    client.force_login(docente)
    return client


@pytest.fixture
def seccion_docente(seccion, docente):
    seccion.docente = docente
    seccion.save()
    return seccion


def pagina(cliente):
    respuesta = cliente.get(URL_INICIO)
    assert respuesta.status_code == 200
    return respuesta.content.decode()


def elemento(html, patron):
    """La primera etiqueta de apertura que cumple ``patron`` (regex sobre la etiqueta)."""
    encontrado = re.search(rf"<{patron}[^>]*>", html)
    assert encontrado, f"la página tiene <{patron}>"
    return encontrado.group(0)


def bloque(html, etiqueta, ident):
    """El HTML completo de ``<etiqueta id="ident">…</etiqueta>``."""
    encontrado = re.search(rf'<{etiqueta}[^>]*id="{ident}".*?</{etiqueta}>', html, re.DOTALL)
    assert encontrado, f"la página tiene <{etiqueta} id={ident}>"
    return encontrado.group(0)


def describe(etiqueta):
    encontrado = re.search(r'aria-describedby="([^"]*)"', etiqueta)
    return encontrado.group(1).split() if encontrado else []


# --- Pantalla ---


def test_la_cabecera_tiene_el_titulo_las_franjas_de_sesiones_y_el_boton(cliente):
    html = pagina(cliente)

    assert 'data-dimension="sesiones"' in html
    assert 'class="franjas-cabecera"' in html
    assert "Planificación de sesiones de aprendizaje" in html
    boton = elemento(html, r"button[^>]*data-abrir-subir")
    assert 'type="button"' in boton
    assert "Subir una sesión</button>" in html


def test_el_estado_vacio_y_la_region_del_resultado(cliente):
    html = pagina(cliente)

    assert "Aquí verás las sesiones que envíes y su estado." in html
    region = elemento(html, r"section[^>]*data-resultado")
    assert 'role="status"' in region


def test_sin_javascript_un_noscript_lo_dice(cliente):
    html = pagina(cliente)

    assert re.search(
        r"<noscript>.*Para subir una sesión necesitas activar JavaScript\..*</noscript>",
        html,
        re.DOTALL,
    )


def test_la_pantalla_carga_sesiones_js(cliente):
    assert re.search(r'<script src="[^"]*js/sesiones\.js" defer>', pagina(cliente))


# --- Popup «Subir una sesión» ---


def test_el_popup_tiene_su_titulo_y_su_descripcion(cliente):
    subir = bloque(pagina(cliente), "dialog", "subir")

    apertura = elemento(subir, 'dialog[^>]*id="subir"')
    assert 'aria-labelledby="subir-titulo"' in apertura
    assert 'aria-describedby="subir-descripcion"' in apertura
    assert re.search(
        r'<h2[^>]*id="subir-titulo"[^>]*tabindex="-1"[^>]*>Subir una sesión</h2>', subir
    )
    assert re.search(r'id="subir-descripcion"[^>]*>Se enviará a la dirección\.</p>', subir)


def test_el_cuerpo_del_popup_se_alcanza_con_el_teclado(cliente):
    subir = bloque(pagina(cliente), "dialog", "subir")

    cuerpo = elemento(subir, r'div class="modal-cuerpo"')
    assert 'tabindex="0"' in cuerpo
    assert 'role="region"' in cuerpo


def test_el_formulario_envia_a_la_ruta_con_el_token_y_el_id_oculto(cliente):
    subir = bloque(pagina(cliente), "dialog", "subir")

    formulario = elemento(subir, 'form[^>]*id="formulario-sesion"')
    assert f'action="{URL_ENVIAR}"' in formulario
    assert 'enctype="multipart/form-data"' in formulario
    assert "novalidate" in formulario
    assert 'name="csrfmiddlewaretoken"' in subir
    oculto = elemento(subir, r'input[^>]*name="id"')
    assert 'type="hidden"' in oculto
    assert "value=" not in oculto, "el id lo genera el navegador al abrir (D5)"


@pytest.mark.parametrize(
    ("campo", "ayuda"),
    [
        ("archivo", "PDF o Word (.docx) · Hasta 4 MB"),
        ("grado", "Elige el grado de esta sesión."),
        ("area", None),
        ("titulo", None),
        ("proposito", None),
    ],
)
def test_cada_campo_tiene_su_ayuda_y_su_error_asociados(cliente, campo, ayuda):
    subir = bloque(pagina(cliente), "dialog", "subir")

    control = elemento(subir, rf'(?:input|select|textarea)[^>]*id="{campo}"')
    assert f'name="{campo}"' in control
    assert re.search(rf'<label[^>]*for="{campo}"', subir), "el campo tiene su etiqueta"
    asociados = describe(control)
    assert f"{campo}-error" in asociados
    assert re.search(rf'<p class="campo__error"[^>]*id="{campo}-error"[^>]*hidden', subir)
    if ayuda:
        assert f"{campo}-ayuda" in asociados
        assert re.search(rf'id="{campo}-ayuda"[^>]*>{re.escape(ayuda)}</p>', subir)


def test_el_archivo_acepta_pdf_y_docx_y_dice_que_aun_no_se_elige(cliente):
    subir = bloque(pagina(cliente), "dialog", "subir")

    archivo = elemento(subir, r'input[^>]*id="archivo"')
    assert 'type="file"' in archivo
    assert 'accept=".pdf,.docx' in archivo
    assert "Aún no has elegido un archivo" in subir


def test_titulo_y_proposito_con_su_tope(cliente):
    subir = bloque(pagina(cliente), "dialog", "subir")

    assert 'maxlength="200"' in elemento(subir, r'input[^>]*id="titulo"')
    assert 'maxlength="1000"' in elemento(subir, r'textarea[^>]*id="proposito"')
    assert re.search(r'for="proposito"[^>]*>Propósito <span class="opcional">\(opcional\)', subir)


def test_las_areas_son_las_de_la_institucion_con_una_opcion_vacia(cliente, comunicacion):
    subir = bloque(pagina(cliente), "dialog", "subir")

    area = bloque(subir, "select", "area")
    assert '<option value="">Elige el área</option>' in area
    assert f'<option value="{comunicacion.pk}">Comunicación</option>' in area


def test_la_casilla_de_compartir_desmarcada_con_su_ayuda(cliente):
    subir = bloque(pagina(cliente), "dialog", "subir")

    casilla = elemento(subir, r'input[^>]*id="compartir"')
    assert 'type="checkbox"' in casilla
    assert "checked" not in casilla
    assert "compartir-ayuda" in describe(casilla)
    assert "Compartir también en el repositorio" in subir
    assert re.search(
        r'id="compartir-ayuda"[^>]*>Tus colegas podrán verla, descargarla y adaptarla\.</p>', subir
    )


def test_el_aviso_de_corte_de_red_esta_oculto(cliente):
    subir = bloque(pagina(cliente), "dialog", "subir")

    aviso = re.search(r'<div class="mensaje mensaje--error"[^>]*data-error-red[^>]*>', subir)
    assert aviso and "hidden" in aviso.group(0)
    assert "Se cortó la conexión" in subir
    assert (
        "Tus datos y tu archivo siguen aquí. Revisa tu conexión e intenta enviar de nuevo." in subir
    )


def test_el_pie_tiene_el_avance_y_los_botones_en_su_orden(cliente):
    subir = bloque(pagina(cliente), "dialog", "subir")

    barra = elemento(subir, "progress")
    assert 'max="100"' in barra
    assert "aria-label=" in barra
    acciones = re.search(r'<div class="acciones-modal">(.*?)</div>', subir, re.DOTALL).group(1)
    enviar = acciones.index("Enviar a la dirección")
    cancelar = acciones.index("Cancelar")
    assert enviar < cancelar, "en el celular «Enviar» va arriba; en la PC, el CSS lo invierte"
    assert 'form="formulario-sesion"' in elemento(acciones, r'button[^>]*type="submit"')


def test_hay_una_region_aria_live_para_el_avance(cliente):
    region = elemento(pagina(cliente), r'div[^>]*id="anuncio"')

    assert 'aria-live="polite"' in region
    assert "sr-only" in region


# --- Términos (4a) ---


def test_los_terminos_van_en_su_propio_popup_con_titulo_y_descripcion(cliente):
    terminos = bloque(pagina(cliente), "dialog", "terminos")

    apertura = elemento(terminos, 'dialog[^>]*id="terminos"')
    assert 'aria-labelledby="terminos-titulo"' in apertura
    assert 'aria-describedby="terminos-descripcion"' in apertura
    assert re.search(
        r'<h2[^>]*id="terminos-titulo"[^>]*tabindex="-1"[^>]*>Antes de compartir</h2>', terminos
    )
    assert re.search(
        r'id="terminos-descripcion"[^>]*>Para compartirla en el repositorio debes aceptar los'
        r" términos\.</p>",
        terminos,
    )


def test_los_terminos_son_los_del_doc_09_literales_y_en_orden(cliente):
    terminos = bloque(pagina(cliente), "dialog", "terminos")
    texto = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", terminos))

    posiciones = [texto.index(frase) for frase in TERMINOS]
    assert posiciones == sorted(posiciones)
    assert len(re.findall(r"<li>", terminos)) == 4


def test_los_terminos_tienen_acepto_y_volver(cliente):
    terminos = bloque(pagina(cliente), "dialog", "terminos")

    assert re.search(r"<button[^>]*data-aceptar[^>]*>Acepto y envío</button>", terminos)
    assert re.search(r"<button[^>]*data-volver[^>]*>[\s\S]*?Volver</button>", terminos)
    cuerpo = elemento(terminos, r'div class="modal-cuerpo"')
    assert 'tabindex="0"' in cuerpo and 'role="region"' in cuerpo


# --- Grado por defecto ---


def test_con_una_seccion_el_grado_viene_elegido_con_su_ayuda(cliente, seccion_docente):
    subir = bloque(pagina(cliente), "dialog", "subir")

    grado = bloque(subir, "select", "grado")
    assert '<option value="2" selected>2.º grado</option>' in grado
    assert grado.count("selected") == 1
    assert "Grado de tu sección: 2.º A. Puedes cambiarlo." in subir


def test_con_varias_secciones_el_grado_viene_sin_elegir(cliente, seccion_docente, docente):
    Seccion.objects.create(
        anio_escolar=seccion_docente.anio_escolar, grado=3, nombre="B", docente=docente
    )
    subir = bloque(pagina(cliente), "dialog", "subir")

    grado = bloque(subir, "select", "grado")
    assert '<option value="" selected>Elige</option>' in grado
    assert grado.count("selected") == 1
    assert "Elige el grado de esta sesión." in subir


def test_sin_seccion_el_grado_viene_sin_elegir(cliente):
    subir = bloque(pagina(cliente), "dialog", "subir")

    grado = bloque(subir, "select", "grado")
    assert '<option value="" selected>Elige</option>' in grado
    assert [f"{n}.º grado" in grado for n in range(1, 7)] == [True] * 6


# --- Fragmento del éxito ---


@pytest.mark.parametrize(
    ("compartir", "mensaje"),
    [
        ({}, "Sesión enviada a la dirección</p>"),
        (
            {"compartir": "on", "acepta_terminos": "1"},
            "Sesión enviada a la dirección y compartida en el repositorio</p>",
        ),
    ],
)
def test_el_fragmento_del_exito_dice_el_mensaje_y_el_titulo_enfocable(
    cliente, comunicacion, compartir, mensaje
):
    datos = {
        "id": str(uuid.uuid4()),
        "grado": "2",
        "area": str(comunicacion.pk),
        "titulo": "Leemos un cuento",
        "archivo": pdf(),
        **compartir,
    }
    html = cliente.post(URL_ENVIAR, datos).content.decode()

    assert mensaje in html
    assert re.search(r'<h2[^>]*tabindex="-1"[^>]*>Leemos un cuento</h2>', html)
    assert re.search(r"<button[^>]*data-subir-otra[^>]*>Subir otra</button>", html)
