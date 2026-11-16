"""Vistas de Sesiones (spec envio-sesiones; design de US-010, US-014 y EN-03, D7).

Rutas, acceso solo del rol Docente (con o sin sección; la dirección y el Administrador van a su
inicio sin registro de intento; sin sesión, al ingreso; con ``HX-Request``, ``HX-Redirect``), la
primera visita y las respuestas del envío: 201 con el fragmento, 400 con los errores en JSON y el
mismo 201 si se repite el ``id``.
"""

import json
import re
import uuid
from datetime import timedelta

import pytest
from django.core.files.storage import storages
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from actividad.models import Operacion, RegistroActividad
from actividad.tests.intentos import intentos
from catalogo.models import Area, InstitucionArea
from repositorio.models import TIPO_DOCX, Sesion, SesionVista
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
    assert "Planificación de sesiones de aprendizaje" not in html
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


# --- Listas, página y entrega del archivo (design de US-011, D5 a D7 y D10) -----------------

URL_REPOSITORIO = "/docente/sesiones/repositorio/"
NO_DISPONIBLE = "La sesión ya no está disponible"
_CSRF = re.compile(r'name="csrfmiddlewaretoken" value="[^"]*"')
NOMBRE_RFC5987 = "Sesi%C3%B3n%203%20%E2%80%93%20cuento%20%C3%B1and%C3%BA.pdf"


def entradas():
    """Las entradas del registro, sin el INICIO_SESION que deja ``force_login``."""
    return list(RegistroActividad.objects.exclude(operacion=Operacion.INICIO_SESION))


def url_de(sesion_o_id, sufijo=""):
    id_sesion = getattr(sesion_o_id, "pk", sesion_o_id)
    return f"/docente/sesiones/{id_sesion}/{sufijo}"


def texto_de(respuesta):
    return respuesta.content.decode()


def sin_csrf(respuesta):
    """El cuerpo sin el token de la cuenta: cambia en cada respuesta."""
    return _CSRF.sub("", texto_de(respuesta))


def test_las_rutas_nuevas_estan_bajo_docente_sesiones():
    id_sesion = uuid.uuid4()

    assert reverse("sesiones:repositorio") == URL_REPOSITORIO
    assert reverse("sesiones:detalle", args=[id_sesion]) == url_de(id_sesion)
    assert reverse("sesiones:descargar", args=[id_sesion]) == url_de(id_sesion, "descargar/")
    assert reverse("sesiones:ver", args=[id_sesion]) == url_de(id_sesion, "ver/")


def test_un_id_que_no_es_uuid_no_llega_a_la_vista(cliente):
    assert cliente.get("/docente/sesiones/123/").status_code == 404


def _rutas_get(sesion):
    return [
        URL_INICIO,
        f"{URL_REPOSITORIO}?q=cuento&grado=2",
        url_de(sesion),
        url_de(sesion, "descargar/"),
        url_de(sesion, "ver/"),
    ]


@pytest.mark.parametrize(
    ("rol", "inicio"), [("direccion", "/direccion/"), ("administrador", "/admin/")]
)
def test_otro_rol_va_a_su_inicio_en_las_cinco_rutas(
    request, entrar, con_archivo, otra_docente, rol, inicio
):
    # Escenarios «Otro rol o sin sesión» de las listas y de la página.
    sesion = con_archivo(otra_docente, compartida=True, titulo="Secreta de la colega")
    cliente = entrar(request.getfixturevalue(rol))

    for ruta in _rutas_get(sesion):
        respuesta = cliente.get(ruta)
        assert (respuesta.status_code, respuesta.url) == (302, inicio), ruta
        con_htmx = cliente.get(ruta, **HTMX)
        assert con_htmx["HX-Redirect"] == inicio, ruta
        assert "Secreta" not in texto_de(con_htmx)
    assert not entradas()


def test_sin_sesion_las_cinco_rutas_van_al_ingreso(client, con_archivo, otra_docente):
    sesion = con_archivo(otra_docente, compartida=True)

    for ruta in _rutas_get(sesion):
        respuesta = client.get(ruta)
        assert respuesta.status_code == 302, ruta
        assert respuesta.url.startswith("/ingresar/?next="), ruta
        assert client.get(ruta, **HTMX)["HX-Redirect"] == "/ingresar/?next=/docente/"
    assert not entradas()


# --- Listas ---


def test_mis_sesiones_lista_las_suyas_con_su_pestana_y_contadores(
    cliente, crear_sesion, docente, otra_docente
):
    crear_sesion(docente, titulo="Mi sesión compartida", compartida=True)
    crear_sesion(docente, titulo="Mi sesión sin compartir")
    crear_sesion(otra_docente, titulo="De la colega", compartida=True)

    respuesta = cliente.get(URL_INICIO)
    html = texto_de(respuesta)

    assert respuesta.status_code == 200
    assert "Mi sesión compartida" in html and "Mi sesión sin compartir" in html
    assert "De la colega" not in html
    assert respuesta.context["pestana"] == "mis_sesiones"
    assert respuesta.context["contadores"] == {"mis_sesiones": 2, "repositorio": 2}
    assert "HX-Request" in respuesta["Vary"]


def test_el_repositorio_lista_las_compartidas_de_su_institucion(
    cliente, crear_sesion, otra_docente, colega_de_otra
):
    crear_sesion(otra_docente, titulo="Compartida de la colega", compartida=True)
    crear_sesion(otra_docente, titulo="Sin compartir de la colega")
    crear_sesion(colega_de_otra, titulo="De otra institución", compartida=True)

    respuesta = cliente.get(URL_REPOSITORIO)
    html = texto_de(respuesta)

    assert respuesta.status_code == 200
    assert respuesta.context["pestana"] == "repositorio"
    assert "Compartida de la colega" in html
    assert "Sin compartir de la colega" not in html
    assert "De otra institución" not in html


def test_el_repositorio_aplica_los_filtros_de_la_direccion(
    cliente, crear_sesion, otra_docente, comunicacion, matematica
):
    # Escenario «Filtros en la dirección».
    crear_sesion(otra_docente, titulo="Tercero comunica agua", grado=3, compartida=True)
    crear_sesion(
        otra_docente, titulo="Tercero suma agua", grado=3, area=matematica, compartida=True
    )
    crear_sesion(otra_docente, titulo="Segundo comunica agua", compartida=True)

    respuesta = cliente.get(URL_REPOSITORIO, {"q": "AGUA", "grado": "3", "area": comunicacion.pk})
    pagina = respuesta.context["pagina"]

    assert [s.titulo for s in pagina.sesiones] == ["Tercero comunica agua"]
    assert (pagina.q, pagina.grado, pagina.area) == ("AGUA", 3, comunicacion)
    assert dict(respuesta.context["conteos"].areas)[matematica] == 1


@pytest.mark.parametrize(
    "consulta",
    [{"grado": "7"}, {"area": "abc"}, {"grado": "x", "area": "999999"}, {"q": "%_" * 80}],
)
def test_valores_que_no_existen_se_ignoran_sin_error(cliente, crear_sesion, otra_docente, consulta):
    # Escenarios «Valores que no existen» y «Búsqueda muy larga o con comodines».
    crear_sesion(otra_docente, compartida=True)

    assert cliente.get(URL_REPOSITORIO, consulta).status_code == 200


def test_la_docente_sin_seccion_abre_el_repositorio(cliente, crear_sesion, otra_docente):
    # Escenario «Docente sin sección».
    crear_sesion(otra_docente, titulo="Compartida", compartida=True)

    assert "Compartida" in texto_de(cliente.get(URL_REPOSITORIO))


@pytest.mark.parametrize("url", [URL_INICIO, URL_REPOSITORIO])
def test_con_hx_request_responde_solo_el_fragmento_con_vary(cliente, crear_sesion, docente, url):
    crear_sesion(docente, titulo="Fragmento", compartida=True)

    respuesta = cliente.get(url, **HTMX)
    html = texto_de(respuesta)

    assert respuesta.status_code == 200
    assert "<html" not in html and "<main" not in html
    assert "Fragmento" in html
    assert "HX-Request" in respuesta["Vary"]
    assert 'hx-swap-oob="true"' in html, "los contadores van fuera de banda"


@pytest.mark.parametrize("url", [URL_INICIO, URL_REPOSITORIO])
def test_pagina_2_devuelve_solo_las_tarjetas_siguientes(cliente, crear_sesion, docente, url):
    ahora = timezone.now()
    for indice in range(22):
        crear_sesion(
            docente,
            titulo=f"Tarjeta {indice:02}",
            compartida=True,
            creado_en=ahora - timedelta(minutes=indice),
        )

    respuesta = cliente.get(url, {"pagina": "2"}, **HTMX)
    html = texto_de(respuesta)

    assert respuesta.status_code == 200
    assert "Tarjeta 20" in html and "Tarjeta 21" in html
    assert "Tarjeta 19" not in html
    assert "hx-swap-oob" not in html
    assert "HX-Request" in respuesta["Vary"]


def test_sin_htmx_pagina_2_es_la_pantalla_completa_con_esa_pagina(cliente, crear_sesion, docente):
    for indice in range(21):
        crear_sesion(docente, titulo=f"T{indice}")

    respuesta = cliente.get(URL_INICIO, {"pagina": "2"})

    assert "<html" in texto_de(respuesta)
    assert len(respuesta.context["pagina"].sesiones) == 1


# --- Página de la sesión ---


def test_la_pagina_de_una_sesion_propia_muestra_sus_datos_y_migas_a_mis_sesiones(
    cliente, crear_sesion, docente
):
    sesion = crear_sesion(
        docente,
        titulo="Leemos un cuento sobre la amistad",
        proposito="Que comenten el cuento.",
        texto="Inicio\nDesarrollo",
        compartida=True,
    )

    respuesta = cliente.get(url_de(sesion))
    html = texto_de(respuesta)

    assert respuesta.status_code == 200
    assert respuesta.templates[0].name == "repositorio/sesion.html"
    for dato in [
        "Leemos un cuento sobre la amistad",
        "Que comenten el cuento.",
        "Inicio\nDesarrollo",
        "Comunicación",
        "Ana Quispe",
    ]:
        assert dato in html, dato
    assert respuesta.context["propia"] is True
    assert respuesta.context["miga"] == ("Mis sesiones", URL_INICIO)
    assert f'href="{URL_INICIO}"' in html


def test_la_pagina_de_una_ajena_compartida_lleva_las_migas_al_repositorio(
    cliente, crear_sesion, otra_docente
):
    sesion = crear_sesion(otra_docente, titulo="De la colega", compartida=True)

    respuesta = cliente.get(url_de(sesion))

    assert respuesta.status_code == 200
    assert respuesta.context["propia"] is False
    assert respuesta.context["miga"] == ("Repositorio", URL_REPOSITORIO)
    assert f'href="{URL_REPOSITORIO}"' in texto_de(respuesta)


def test_abrir_una_ajena_cuenta_la_primera_vez(cliente, crear_sesion, docente, otra_docente):
    sesion = crear_sesion(otra_docente, compartida=True)

    cliente.get(url_de(sesion))
    cliente.get(url_de(sesion))

    assert SesionVista.objects.filter(sesion=sesion, usuario=docente).count() == 1
    assert RegistroActividad.objects.filter(operacion=Operacion.SESION_VISTA).count() == 1


def test_una_lectura_no_deja_entrada(cliente, crear_sesion, docente, otra_docente):
    # Escenario «Una lectura no deja entrada».
    propia = crear_sesion(docente, compartida=True)
    crear_sesion(otra_docente, compartida=True)

    cliente.get(URL_INICIO)
    cliente.get(URL_INICIO, **HTMX)
    cliente.get(URL_REPOSITORIO, {"q": "cuento", "grado": "2"})
    cliente.get(URL_REPOSITORIO, {"q": "cuento"}, **HTMX)
    cliente.get(url_de(propia))

    assert not entradas()


def test_titulo_proposito_y_texto_con_marcas_salen_escapados(cliente, crear_sesion, docente):
    # Escenario «Texto con marcas de HTML».
    marca = "<script>alert(1)</script>"
    sesion = crear_sesion(
        docente, titulo=f"T {marca}", proposito=f"P {marca}", texto=f"X {marca}", compartida=True
    )

    for url in [url_de(sesion), URL_INICIO, URL_REPOSITORIO]:
        html = texto_de(cliente.get(url))
        assert marca not in html, url
        assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html, url


def test_la_pagina_y_las_listas_no_traen_la_clave_ni_una_direccion_de_r2(
    cliente, almacen_que_firma, crear_sesion, docente
):
    # Escenario «La página no trae enlaces de R2».
    sesion = crear_sesion(docente, compartida=True)

    for url in [url_de(sesion), URL_INICIO, URL_REPOSITORIO]:
        html = texto_de(cliente.get(url))
        assert sesion.archivo_clave not in html, url
        assert "r2.cloudflarestorage" not in html and "X-Amz" not in html, url
    assert almacen_que_firma.llamadas == []
    assert f'href="{url_de(sesion, "descargar/")}"' in texto_de(cliente.get(url_de(sesion)))


# --- No disponible ---


@pytest.fixture
def no_visibles(con_archivo, otra_docente, colega_de_otra):
    """Los cuatro casos de «no disponible»: inexistente, ajena sin compartir, de otra
    institución y una que dejó de compartirse."""
    dejo = con_archivo(otra_docente, titulo="Dejó de compartirse", compartida=True)
    Sesion.objects.filter(pk=dejo.pk).update(compartida=False)
    return {
        "inexistente": uuid.uuid4(),
        "ajena sin compartir": con_archivo(otra_docente, titulo="Privada de la colega").pk,
        "otra institución": con_archivo(colega_de_otra, titulo="Ajena", compartida=True).pk,
        "dejó de compartirse": dejo.pk,
    }


@pytest.mark.parametrize("sufijo", ["", "descargar/", "ver/"])
def test_no_disponible_responde_404_con_el_mismo_cuerpo_en_los_cuatro_casos(
    cliente, no_visibles, sufijo
):
    # Escenarios «Ajena sin compartir», «Otra institución», «Dejó de compartirse» y
    # «Caso de error (sesión eliminada)».
    respuestas = [cliente.get(url_de(id_sesion, sufijo)) for id_sesion in no_visibles.values()]

    assert {respuesta.status_code for respuesta in respuestas} == {404}
    cuerpos = {sin_csrf(respuesta) for respuesta in respuestas}
    assert len(cuerpos) == 1
    (cuerpo,) = cuerpos
    assert NO_DISPONIBLE in cuerpo and "Volver a Sesiones" in cuerpo
    for dato in ["Privada de la colega", "Ajena", "Dejó de compartirse", "Rosa", "Pía"]:
        assert dato not in cuerpo
    assert not entradas()
    assert not SesionVista.objects.exists()


# --- Descargar y ver ---


def test_la_descarga_local_entrega_el_archivo_con_su_nombre_tipo_y_sin_cache(
    cliente, con_archivo, otra_docente
):
    # Escenarios «Camino ideal (sesión de otro docente)», «Nombre original» y «Laptop y pruebas».
    sesion = con_archivo(
        otra_docente,
        contenido=b"%PDF-1.4 contenido",
        compartida=True,
        archivo_nombre="Sesión 3 – cuento ñandú.pdf",
    )

    respuesta = cliente.get(url_de(sesion, "descargar/"))

    assert respuesta.status_code == 200
    assert b"".join(respuesta.streaming_content) == b"%PDF-1.4 contenido"
    assert respuesta["Content-Type"] == "application/pdf"
    assert respuesta["Content-Disposition"] == f"attachment; filename*=utf-8''{NOMBRE_RFC5987}"
    assert "no-store" in respuesta["Cache-Control"]
    assert respuesta["X-Content-Type-Options"] == "nosniff"
    assert RegistroActividad.objects.filter(operacion=Operacion.SESION_DESCARGADA).count() == 1


def test_la_autora_descarga_su_word(cliente, con_archivo, docente):
    # Escenario «Flujo alternativo válido (sesión propia)».
    sesion = con_archivo(
        docente, contenido=b"PK docx", tipo_mime=TIPO_DOCX, archivo_nombre="a.docx"
    )

    respuesta = cliente.get(url_de(sesion, "descargar/"))

    assert respuesta.status_code == 200
    assert respuesta["Content-Type"] == TIPO_DOCX
    assert respuesta["Content-Disposition"] == 'attachment; filename="a.docx"'


def test_ver_un_pdf_lo_entrega_en_linea(cliente, con_archivo, docente):
    sesion = con_archivo(docente, archivo_nombre="cuento.pdf")

    respuesta = cliente.get(url_de(sesion, "ver/"))

    assert respuesta.status_code == 200
    assert respuesta["Content-Disposition"] == 'inline; filename="cuento.pdf"'
    assert "no-store" in respuesta["Cache-Control"]


def test_ver_un_word_no_entrega_el_archivo(cliente, con_archivo, docente):
    # Escenario «Vista de un Word por su dirección».
    sesion = con_archivo(docente, tipo_mime=TIPO_DOCX, archivo_nombre="a.docx")

    respuesta = cliente.get(url_de(sesion, "ver/"))

    assert respuesta.status_code == 404
    assert NO_DISPONIBLE in texto_de(respuesta)
    assert not entradas()


def test_con_un_almacen_que_firma_la_descarga_redirige_al_enlace(
    cliente, almacen_que_firma, crear_sesion, docente
):
    # Escenario «Descarga en Vercel».
    sesion = crear_sesion(docente)

    respuesta = cliente.get(url_de(sesion, "descargar/"))

    assert respuesta.status_code == 302
    assert respuesta.url.startswith("https://cuenta-ficticia.r2.cloudflarestorage.com/")
    assert "no-store" in respuesta["Cache-Control"]
    assert almacen_que_firma.llamadas[0]["expire"] == 60


# --- Escrituras de la autora (design de US-011, D8 y D10) ---

SOLO_EL_AUTOR = "Solo el autor puede eliminar esta sesión"
SIN_TERMINOS = "Para compartirla en el repositorio debes aceptar los términos."


def test_las_rutas_post_estan_bajo_docente_sesiones():
    id_sesion = uuid.uuid4()

    assert reverse("sesiones:eliminar", args=[id_sesion]) == url_de(id_sesion, "eliminar/")
    assert reverse("sesiones:compartir", args=[id_sesion]) == url_de(id_sesion, "compartir/")
    assert reverse("sesiones:dejar_de_compartir", args=[id_sesion]) == url_de(
        id_sesion, "dejar-de-compartir/"
    )


@pytest.mark.parametrize("sufijo", ["eliminar/", "compartir/", "dejar-de-compartir/"])
def test_las_escrituras_no_aceptan_get(cliente, crear_sesion, docente, sufijo):
    sesion = crear_sesion(docente, compartida=True)

    assert cliente.get(url_de(sesion, sufijo)).status_code == 405
    assert Sesion.objects.filter(pk=sesion.pk, compartida=True).exists()


def test_una_escritura_sin_token_csrf_se_rechaza(docente, crear_sesion):
    sesion = crear_sesion(docente)
    cliente = Client(enforce_csrf_checks=True)
    cliente.force_login(docente)

    assert cliente.post(url_de(sesion, "eliminar/")).status_code == 403
    assert Sesion.objects.filter(pk=sesion.pk).exists()


def test_eliminar_lleva_a_mis_sesiones_con_el_mensaje_que_no_vuelve_al_recargar(
    cliente, con_archivo, docente, django_capture_on_commit_callbacks
):
    sesion = con_archivo(docente, compartida=True)

    with django_capture_on_commit_callbacks(execute=True):
        respuesta = cliente.post(url_de(sesion, "eliminar/"))

    assert (respuesta.status_code, respuesta.url) == (303, URL_INICIO)
    assert not Sesion.objects.filter(pk=sesion.pk).exists()
    assert not storages["sesiones"].exists(sesion.archivo_clave)
    lista = texto_de(cliente.get(URL_INICIO))
    assert "Sesión eliminada" in lista
    assert 'role="status"' in lista
    assert "Sesión eliminada" not in texto_de(cliente.get(URL_INICIO))
    assert cliente.get(url_de(sesion)).status_code == 404


def test_eliminar_dos_veces_la_segunda_es_no_disponible(cliente, crear_sesion, docente):
    sesion = crear_sesion(docente)
    cliente.post(url_de(sesion, "eliminar/"))

    respuesta = cliente.post(url_de(sesion, "eliminar/"))

    assert respuesta.status_code == 404
    assert NO_DISPONIBLE in texto_de(respuesta)


def test_eliminar_una_ajena_visible_responde_403_solo_el_autor(cliente, crear_sesion, otra_docente):
    sesion = crear_sesion(otra_docente, compartida=True, titulo="De la colega")

    respuesta = cliente.post(url_de(sesion, "eliminar/"))

    assert respuesta.status_code == 403
    assert respuesta.templates[0].name == "repositorio/sesion.html"
    html = texto_de(respuesta)
    assert SOLO_EL_AUTOR in html
    assert "De la colega" in html
    assert Sesion.objects.filter(pk=sesion.pk).exists()
    assert intentos() == [(str(sesion.pk), url_de(sesion, "eliminar/"), "sesion_ajena")]
    # La respuesta de error no cuenta como vista.
    assert not SesionVista.objects.exists()


def test_eliminar_una_ajena_no_compartida_responde_404_igual_que_inexistente(
    cliente, crear_sesion, otra_docente
):
    sesion = crear_sesion(otra_docente, compartida=False, titulo="Secreta de la colega")

    ajena = cliente.post(url_de(sesion, "eliminar/"))
    inexistente = cliente.post(url_de(uuid.uuid4(), "eliminar/"))

    assert ajena.status_code == inexistente.status_code == 404
    assert sin_csrf(ajena) == sin_csrf(inexistente)
    assert "Secreta" not in texto_de(ajena)
    assert Sesion.objects.filter(pk=sesion.pk).exists()


def test_dejar_de_compartir_vuelve_a_la_pagina_con_su_mensaje(cliente, crear_sesion, docente):
    sesion = crear_sesion(docente, compartida=True)

    respuesta = cliente.post(url_de(sesion, "dejar-de-compartir/"))

    assert (respuesta.status_code, respuesta.url) == (303, url_de(sesion))
    assert not Sesion.objects.get(pk=sesion.pk).compartida
    assert "Dejaste de compartir la sesión" in texto_de(cliente.get(url_de(sesion)))


def test_compartir_aceptando_vuelve_a_la_pagina_con_su_mensaje(cliente, crear_sesion, docente):
    sesion = crear_sesion(docente, compartida=False)

    respuesta = cliente.post(url_de(sesion, "compartir/"), {"acepta_terminos": "on"})

    assert (respuesta.status_code, respuesta.url) == (303, url_de(sesion))
    assert Sesion.objects.get(pk=sesion.pk).compartida
    assert "Sesión compartida en el repositorio" in texto_de(cliente.get(url_de(sesion)))


def test_compartir_sin_aceptar_responde_400_con_su_mensaje(cliente, crear_sesion, docente):
    sesion = crear_sesion(docente, compartida=False)

    respuesta = cliente.post(url_de(sesion, "compartir/"))

    assert respuesta.status_code == 400
    assert respuesta.templates[0].name == "repositorio/sesion.html"
    assert SIN_TERMINOS in texto_de(respuesta)
    assert not Sesion.objects.get(pk=sesion.pk).compartida
    assert not entradas()


def test_compartir_una_ajena_sin_compartir_responde_404(cliente, crear_sesion, otra_docente):
    sesion = crear_sesion(otra_docente, compartida=False)

    respuesta = cliente.post(url_de(sesion, "compartir/"), {"acepta_terminos": "on"})

    assert respuesta.status_code == 404
    assert NO_DISPONIBLE in texto_de(respuesta)
    assert not Sesion.objects.get(pk=sesion.pk).compartida


def test_dejar_de_compartir_una_ajena_responde_403_y_sigue_compartida(
    cliente, crear_sesion, otra_docente
):
    sesion = crear_sesion(otra_docente, compartida=True)

    respuesta = cliente.post(url_de(sesion, "dejar-de-compartir/"))

    assert respuesta.status_code == 403
    assert Sesion.objects.get(pk=sesion.pk).compartida


def _rutas_post(sesion):
    return [url_de(sesion, s) for s in ("eliminar/", "compartir/", "dejar-de-compartir/")]


@pytest.mark.parametrize(
    ("rol", "inicio"), [("direccion", "/direccion/"), ("administrador", "/admin/")]
)
def test_otro_rol_va_a_su_inicio_sin_cambiar_nada(
    request, entrar, crear_sesion, otra_docente, rol, inicio
):
    # Escenario «Otro rol» de «Solo la autora elimina».
    sesion = crear_sesion(otra_docente, compartida=True)
    cliente = entrar(request.getfixturevalue(rol))

    for ruta in _rutas_post(sesion):
        respuesta = cliente.post(ruta, {"acepta_terminos": "on"})
        assert (respuesta.status_code, respuesta.url) == (302, inicio), ruta
    assert Sesion.objects.filter(pk=sesion.pk, compartida=True).exists()
    assert not entradas()


def test_sin_sesion_las_escrituras_van_al_ingreso_sin_cambiar_nada(
    client, crear_sesion, otra_docente
):
    sesion = crear_sesion(otra_docente, compartida=True)

    for ruta in _rutas_post(sesion):
        respuesta = client.post(ruta, {"acepta_terminos": "on"})
        assert respuesta.status_code == 302, ruta
        assert respuesta.url.startswith("/ingresar/?next="), ruta
    assert Sesion.objects.filter(pk=sesion.pk, compartida=True).exists()
    assert not RegistroActividad.objects.exists()
