"""Vistas de Sesiones (spec envio-sesiones; design de US-010, US-014 y EN-03, D7).

Rutas, acceso solo del rol Docente (con o sin sección; la dirección y el Administrador van a su
inicio sin registro de intento; sin sesión, al ingreso; con ``HX-Request``, ``HX-Redirect``), la
primera visita y las respuestas del envío: 201 con el fragmento, 400 con los errores en JSON y el
mismo 201 si se repite el ``id``.
"""

import json
import re
import uuid

import pytest
from django.core.files.storage import storages
from django.test import Client
from django.urls import reverse

from actividad.models import Operacion, RegistroActividad
from actividad.tests.intentos import intentos
from catalogo.models import Area, InstitucionArea
from repositorio.models import Sesion
from repositorio.tests.archivos import docx, pdf, pdf_bytes, subido
from repositorio.tests.conftest import COMUNICACION, MATEMATICA

pytestmark = pytest.mark.django_db

HTMX = {"HTTP_HX_REQUEST": "true"}
URL_INICIO = "/docente/sesiones/"
URL_ENVIAR = "/docente/sesiones/enviar/"
# 1,2 MB como los cuenta filesizeformat (base 1024).
UN_COMA_DOS_MB = 1258291


@pytest.fixture
def entrar(client):
    def entrar_como(usuario):
        client.force_login(usuario)
        return client

    return entrar_como


@pytest.fixture
def cliente(entrar, docente):
    return entrar(docente)


@pytest.fixture
def seccion_docente(seccion, docente):
    seccion.docente = docente
    seccion.save()
    return seccion


@pytest.fixture
def formulario(comunicacion):
    """Lo que manda el popup: «Leemos un cuento», 2.º grado, Comunicación, con un PDF de 1,2 MB."""

    def armar(**cambios):
        valores = {
            "id": str(uuid.uuid4()),
            "grado": "2",
            "area": str(comunicacion.pk),
            "titulo": "Leemos un cuento",
            "proposito": "",
            "archivo": pdf(tamano=UN_COMA_DOS_MB),
            **cambios,
        }
        return {clave: valor for clave, valor in valores.items() if valor is not None}

    return armar


def nada_guardado():
    almacen = storages["sesiones"]
    assert not Sesion.objects.exists()
    assert not RegistroActividad.objects.filter(operacion=Operacion.SESION_ENVIADA).exists()
    assert not almacen.exists("sesiones") or almacen.listdir("sesiones") == ([], [])


def errores(respuesta):
    assert respuesta.status_code == 400
    assert respuesta["Content-Type"] == "application/json"
    cuerpo = json.loads(respuesta.content)
    assert list(cuerpo) == ["errores"]
    return cuerpo["errores"]


# --- Rutas (D7) ---


def test_las_dos_rutas_estan_bajo_docente_sesiones():
    assert reverse("sesiones:inicio") == URL_INICIO
    assert reverse("sesiones:enviar") == URL_ENVIAR


def test_enviar_solo_acepta_post(cliente):
    assert cliente.get(URL_ENVIAR).status_code == 405


def test_un_envio_sin_token_csrf_se_rechaza(docente, formulario):
    cliente = Client(enforce_csrf_checks=True)
    cliente.force_login(docente)

    assert cliente.post(URL_ENVIAR, formulario(), **HTMX).status_code == 403
    nada_guardado()


# --- Solo el rol Docente ---


def test_la_docente_con_seccion_abre_sesiones_y_envia(cliente, seccion_docente, formulario):
    assert cliente.get(URL_INICIO).status_code == 200

    assert cliente.post(URL_ENVIAR, formulario(), **HTMX).status_code == 201
    assert Sesion.objects.count() == 1


def test_la_docente_sin_seccion_abre_sesiones_y_envia(cliente, formulario):
    # Escenario «Docente sin sección»: Sesiones no es una ruta de sección.
    assert cliente.get(URL_INICIO).status_code == 200

    assert cliente.post(URL_ENVIAR, formulario(), **HTMX).status_code == 201
    assert Sesion.objects.count() == 1


@pytest.mark.parametrize(
    ("rol", "inicio"), [("direccion", "/direccion/"), ("administrador", "/admin/")]
)
def test_otro_rol_va_a_su_inicio_sin_guardar_ni_registrar(request, entrar, formulario, rol, inicio):
    # Escenario «Otro rol» (decisión 11: sin registro de intento).
    cliente = entrar(request.getfixturevalue(rol))

    assert cliente.get(URL_INICIO).url == inicio
    assert cliente.post(URL_ENVIAR, formulario()).url == inicio
    con_htmx = cliente.post(URL_ENVIAR, formulario(), **HTMX)
    assert con_htmx["HX-Redirect"] == inicio
    nada_guardado()
    assert intentos() == []


def test_sin_sesion_va_a_ingresar_con_next(client, formulario):
    # Escenario «Sin sesión».
    assert client.get(URL_INICIO).url == f"/ingresar/?next={URL_INICIO}"
    assert client.post(URL_ENVIAR, formulario()).url == f"/ingresar/?next={URL_ENVIAR}"
    nada_guardado()


def test_sin_sesion_el_envio_del_popup_recibe_hx_redirect(client, formulario):
    respuesta = client.post(URL_ENVIAR, formulario(), **HTMX)

    assert respuesta.status_code == 200
    assert respuesta["HX-Redirect"] == "/ingresar/?next=/docente/"
    nada_guardado()


def test_con_la_sesion_vencida_el_envio_recibe_hx_redirect(cliente, formulario):
    sesion = cliente.session
    sesion["ultima_actividad"] = 0
    sesion.save()

    respuesta = cliente.post(URL_ENVIAR, formulario(), **HTMX)

    assert respuesta["HX-Redirect"] == "/ingresar/?next=/docente/"
    nada_guardado()


# --- Primera visita ---


def test_primera_visita_cabecera_boton_y_estado_vacio_sin_lista(cliente):
    respuesta = cliente.get(URL_INICIO)
    html = respuesta.content.decode()

    assert respuesta.templates[0].name == "repositorio/sesiones.html"
    assert "<h1" in html and "Sesiones</h1>" in html
    assert "Planificación de sesiones de aprendizaje" in html
    assert "franjas-cabecera" not in html
    assert "Subir una sesión" in html
    assert "Aquí verás las sesiones que envíes y su estado." in html
    assert "Sesión enviada a la dirección" not in html
    contenido = re.search(r"<main\b.*?</main>", html, re.DOTALL).group(0)
    assert "<ul" not in contenido and "<table" not in contenido, "sin lista de sesiones"


def test_el_contexto_trae_las_areas_que_trabaja_la_institucion(cliente, institucion, comunicacion):
    matematica = Area.objects.get(codigo_siagie=MATEMATICA)
    InstitucionArea.objects.filter(institucion=institucion).exclude(
        area__codigo_siagie__in=[COMUNICACION, MATEMATICA]
    ).update(se_trabaja=False)

    contexto = cliente.get(URL_INICIO).context

    assert contexto["areas"] == sorted([comunicacion, matematica], key=lambda area: area.orden)
    assert [valor for valor, _ in contexto["grados"]] == [1, 2, 3, 4, 5, 6]


def test_el_contexto_trae_el_grado_de_su_unica_seccion(cliente, seccion_docente):
    contexto = cliente.get(URL_INICIO).context

    assert contexto["grado"] == 2
    assert contexto["ayuda_grado"] == "Grado de tu sección: 2.º A. Puedes cambiarlo."


def test_sin_seccion_el_contexto_no_trae_grado(cliente):
    contexto = cliente.get(URL_INICIO).context

    assert contexto["grado"] is None
    assert contexto["ayuda_grado"] == "Elige el grado de esta sesión."


# --- Envío (D7) ---


def test_un_envio_valido_responde_201_con_el_fragmento_y_su_resumen(cliente, formulario):
    respuesta = cliente.post(URL_ENVIAR, formulario(), **HTMX)
    html = respuesta.content.decode()

    assert respuesta.status_code == 201
    assert respuesta.templates[0].name == "repositorio/_enviada.html"
    assert "Sesión enviada a la dirección" in html
    assert "compartida en el repositorio" not in html
    assert "Leemos un cuento" in html
    assert "2.º grado" in html
    assert "Comunicación" in html
    assert "leemos-un-cuento.pdf" in html
    # filesizeformat separa con un espacio de no separación, en el formato de es-pe.
    assert "PDF · 1,2\xa0MB" in html
    assert "Subir otra" in html
    assert "<html" not in html


def test_un_envio_compartido_lo_dice_en_el_fragmento(cliente, formulario):
    respuesta = cliente.post(URL_ENVIAR, formulario(compartir="on", acepta_terminos="1"), **HTMX)

    assert respuesta.status_code == 201
    assert "Sesión enviada a la dirección y compartida en el repositorio" in (
        respuesta.content.decode()
    )


def test_un_docx_se_resume_como_word(cliente, formulario):
    respuesta = cliente.post(URL_ENVIAR, formulario(archivo=docx()), **HTMX)

    assert respuesta.status_code == 201
    assert "leemos-un-cuento.docx" in respuesta.content.decode()
    assert "Word · " in respuesta.content.decode()


def test_datos_que_faltan_responden_400_con_un_mensaje_por_campo(cliente, formulario):
    respuesta = cliente.post(URL_ENVIAR, formulario(area="", titulo="", archivo=None), **HTMX)

    assert errores(respuesta) == {
        "area": "Falta indicar el área.",
        "titulo": "Falta indicar el título.",
        "archivo": "Elige un archivo PDF o Word (.docx).",
    }
    nada_guardado()


def test_un_archivo_disfrazado_responde_400_con_el_mensaje_del_campo(cliente, formulario):
    falso = subido("sesion.pdf", b"MZ\x90\x00 ejecutable", "application/pdf")

    respuesta = cliente.post(URL_ENVIAR, formulario(archivo=falso), **HTMX)

    assert errores(respuesta) == {
        "archivo": "Este archivo no es PDF ni Word (.docx). Elige otro archivo."
    }
    nada_guardado()


def test_compartir_sin_aceptar_responde_400(cliente, formulario):
    respuesta = cliente.post(URL_ENVIAR, formulario(compartir="on"), **HTMX)

    assert errores(respuesta) == {
        "compartir": "Para compartirla en el repositorio debes aceptar los términos."
    }
    nada_guardado()


def test_un_id_mal_formado_responde_el_error_general(cliente, formulario):
    respuesta = cliente.post(URL_ENVIAR, formulario(id="no-es-un-uuid"), **HTMX)

    assert errores(respuesta) == {
        "general": "No se pudo enviar. Recarga la página e intenta de nuevo."
    }
    nada_guardado()


def test_el_400_no_lleva_el_texto_de_una_excepcion(cliente, formulario):
    respuesta = cliente.post(URL_ENVIAR, formulario(grado="7", titulo="x" * 201), **HTMX)
    texto = respuesta.content.decode()

    assert errores(respuesta) == {
        "grado": "Elige un grado de la lista.",
        "titulo": "El título puede tener hasta 200 caracteres.",
    }
    assert "ValidationError" not in texto and "Traceback" not in texto


def test_el_mismo_id_otra_vez_responde_el_mismo_201_con_una_sola_sesion(cliente, formulario):
    # Escenario «Se guardó pero no llegó la respuesta» (D5).
    primero = formulario()
    repetido = {**primero, "archivo": subido("leemos-un-cuento.pdf", pdf_bytes(UN_COMA_DOS_MB))}

    uno = cliente.post(URL_ENVIAR, primero, **HTMX)
    dos = cliente.post(URL_ENVIAR, repetido, **HTMX)

    assert uno.status_code == dos.status_code == 201
    assert uno.content == dos.content
    assert Sesion.objects.count() == 1
    assert RegistroActividad.objects.filter(operacion=Operacion.SESION_ENVIADA).count() == 1
