"""Vistas de la dirección: la portada (US-040, D9; spec pantallas-de-inicio, «Inicio de la
dirección»).

Comprueban el HTML que sale del servidor, sin JavaScript. El día es el lunes 22 de noviembre de
2027, en el IV bimestre (del 8 de noviembre al 18 de diciembre), salvo donde la prueba lo cambia.
"""

import datetime
import re
import uuid
from urllib.parse import urlencode

import pytest
from django.urls import reverse
from django.utils import timezone

from actividad.models import Operacion, RegistroActividad
from asistencia.models import Asistencia, Jornada
from asistencia.servicios import dias_de_clase
from catalogo.models import Area
from cuentas.models import Usuario
from direccion.tests.conftest import HOY, completar_asistencia, crear_seccion
from institucion.models import AnioEscolar, Estudiante, Periodo
from notas.models import Calificacion
from notas.tests.conftest import (
    COMUNICACION,
    MATEMATICA,
    competencia,
    crear_estudiantes,
    ids_de,
    marcar,
    poner_nota,
)
from repositorio.models import TIPO_DOCX, SesionVista

pytestmark = pytest.mark.django_db

INICIO = "/direccion/"
CONSOLIDADOS = "/direccion/consolidados/"
IE = "I.E. Ficticia N.° 1"
LIMA = datetime.timezone(datetime.timedelta(hours=-5))
# El jueves 18 de noviembre de 2027, 10:00 de Lima: dentro del IV bimestre.
ENVIADA = datetime.datetime(2027, 11, 18, 10, 0, tzinfo=LIMA)


@pytest.fixture
def fijar_dia(monkeypatch):
    """Fija el día y la hora de Lima sin tocar el reloj (por defecto, ``HOY`` a las 9:00)."""
    ahora = {"valor": datetime.datetime(HOY.year, HOY.month, HOY.day, 9, 0)}
    original = timezone.localtime

    def localtime(value=None, timezone=None):
        return original(value, timezone) if value is not None else ahora["valor"]

    monkeypatch.setattr(timezone, "localtime", localtime)
    monkeypatch.setattr(timezone, "localdate", lambda *args, **kwargs: ahora["valor"].date())

    def fijar(dia=HOY, hora=9):
        ahora["valor"] = datetime.datetime(dia.year, dia.month, dia.day, hora, 0)

    return fijar


@pytest.fixture(autouse=True)
def reloj(fijar_dia):
    fijar_dia()


@pytest.fixture
def portada(client, direccion):
    """El HTML de la portada de la dirección."""

    def abrir():
        client.force_login(direccion)
        respuesta = client.get(INICIO)
        assert respuesta.status_code == 200
        return respuesta.content.decode()

    return abrir


def texto(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()


def bloque(html, patron):
    encontrado = re.search(patron, html, re.DOTALL)
    assert encontrado, f"no se halló {patron!r}"
    return encontrado.group(0)


def banda(html):
    return bloque(html, r'<article\b[^>]*aria-labelledby="t-con".*?</article>')


def entregas(html):
    return bloque(html, r'<article\b[^>]*aria-labelledby="t-ent".*?</article>')


def casillas(html):
    """Las clases de estado de las casillas del mapa de la miniatura, en orden."""
    return re.findall(r'<i class="dir-mapita__c dir-mapita__c--(\w+)"', html)


@pytest.fixture
def una_atrasada(anio_abierto, docente, bimestres):
    """Una sección con estudiantes y sin jornadas: atrasada en el IV bimestre."""
    return crear_seccion(anio_abierto, 2, "A", docente=docente, estudiantes=2)


@pytest.fixture
def una_al_dia(anio_abierto, docente, bimestres):
    seccion = crear_seccion(anio_abierto, 2, "B", docente=docente, estudiantes=2)
    completar_asistencia(seccion, bimestres[3], HOY - datetime.timedelta(days=1), docente)
    return seccion


# --- Saludo y línea de contexto ---


def test_saluda_con_el_nombre_en_el_mismo_h1(portada, bimestres):
    html = portada()

    h1 = bloque(html, r"<h1\b[^>]*>.*?</h1>")
    assert re.search(r'<span class="saludo">Buenos días,</span>', h1)
    assert re.search(r'<span class="docente">Luisa Huamán</span>', h1)
    assert html.count("<h1") == 1


@pytest.mark.parametrize(
    ("hora", "saludo"), [(11, "Buenos días"), (12, "Buenas tardes"), (19, "Buenas noches")]
)
def test_el_saludo_depende_de_la_hora_de_lima(portada, bimestres, fijar_dia, hora, saludo):
    fijar_dia(hora=hora)

    assert f'<span class="saludo">{saludo},</span>' in portada()


def test_la_linea_dice_el_bimestre_vigente_y_su_fin(portada, bimestres):
    """Escenario «Inicio de la dirección en el Sprint 1»."""
    contexto = bloque(portada(), r'<p class="dir-contexto">.*?</p>')

    assert texto(contexto) == "Dirección · IV bimestre vigente, hasta el 18 de diciembre"


@pytest.mark.parametrize(
    "dia", [datetime.date(2027, 3, 2), datetime.date(2027, 5, 20), datetime.date(2028, 1, 10)]
)
def test_sin_bimestre_vigente_la_linea_dice_la_ie(portada, bimestres, fijar_dia, dia):
    """Antes del primero, entre dos bimestres y después del último."""
    fijar_dia(dia)

    contexto = bloque(portada(), r'<p class="dir-contexto">.*?</p>')

    assert texto(contexto) == f"Dirección · {IE}"


# --- Banda «Consolidados» ---


def test_la_banda_lleva_a_consolidados_con_un_solo_enlace(portada, una_atrasada):
    """Escenario «La banda lleva a Consolidados»: el enlace del título se estira sobre la banda."""
    html = banda(portada())

    enlaces = re.findall(r"<a\b[^>]*>", html)
    assert len(enlaces) == 1
    assert f'href="{CONSOLIDADOS}"' in enlaces[0]
    assert re.search(r"<h2\b[^>]*>\s*<a\b[^>]*>Consolidados</a>\s*</h2>", html)
    assert 'aria-describedby="p-con"' in enlaces[0]
    assert "Ver consolidados" in texto(html)


def test_la_banda_cuenta_las_secciones_del_anio(portada, veinticuatro):
    frase = "Revisa cómo van las notas, la asistencia y las sesiones de las 24 secciones."

    assert frase in texto(banda(portada()))


def test_la_banda_con_una_sola_seccion_habla_de_la_seccion(portada, una_atrasada):
    frase = "Revisa cómo van las notas, la asistencia y las sesiones de la sección."

    assert frase in texto(banda(portada()))


def test_la_pastilla_cuenta_las_secciones_atrasadas_del_vigente(portada, veinticuatro):
    """Escenario «Inicio de la dirección en el Sprint 1»: 13 de las 22 con trabajo."""
    html = banda(portada())

    pastilla = bloque(html, r'<p class="dir-pendiente" id="p-con">.*?</p>')
    assert texto(pastilla) == "13 secciones por revisar"
    assert re.search(r'<svg\b[^>]*aria-hidden="true"', pastilla)


def test_la_pastilla_dice_una_seccion_en_singular(portada, una_atrasada, una_al_dia):
    pastilla = bloque(banda(portada()), r'<p class="dir-pendiente" id="p-con">.*?</p>')

    assert texto(pastilla) == "1 sección por revisar"


def test_con_todas_al_dia_no_hay_pastilla(portada, una_al_dia):
    """Escenario «Todas al día»."""
    html = banda(portada())

    assert "dir-pendiente" not in html
    assert "por revisar" not in html
    assert 'aria-describedby="p-con"' not in html


# --- Miniatura de la banda ---


def test_la_miniatura_trae_la_fecha_de_hoy(portada, una_atrasada):
    html = banda(portada())

    fecha = bloque(html, r"<time\b.*?</time>")
    assert 'datetime="2027-11-22"' in fecha
    assert re.search(r'<span class="sr-only">Hoy, lunes 22 de noviembre</span>', fecha)
    assert re.search(r'<span aria-hidden="true">Lunes</span>', fecha)
    assert re.search(r'<strong aria-hidden="true">22</strong>', fecha)
    assert re.search(r'<span aria-hidden="true">noviembre</span>', fecha)


def test_el_mapa_de_la_miniatura_tiene_una_casilla_por_seccion_con_su_estado(portada, veinticuatro):
    html = banda(portada())

    mapa = bloque(html, r'<div class="dir-mapita"[^>]*>.*?</div>')
    assert 'aria-hidden="true"' in re.match(r"<div[^>]*>", mapa).group(0)
    assert re.findall(r'<span class="dir-mapita__g">([^<]+)</span>', mapa) == [
        f"{grado}.º" for grado in range(1, 7)
    ]
    estados = casillas(mapa)
    assert len(estados) == 24
    assert estados.count("x") == 13, "atrasadas"
    assert estados.count("o") == 9, "al día"
    assert estados.count("s") == 2, "sin docente o sin estudiantes"
    # 4.º C (sin docente) y 6.º D (sin estudiantes) son las casillas 15 y 24 del mapa.
    assert [i for i, e in enumerate(estados, start=1) if e == "s"] == [15, 24]


def test_el_mapa_completa_con_casillas_vacias_los_grados_con_menos_secciones(
    portada, anio_abierto, docente, bimestres
):
    crear_seccion(anio_abierto, 1, "A", docente=docente, estudiantes=1)
    crear_seccion(anio_abierto, 1, "B", docente=docente, estudiantes=1)

    estados = casillas(banda(portada()))

    assert estados[:2] == ["x", "x"]
    assert len(estados) == 6 * 4, "siempre la rejilla de 6 × 4"
    assert estados[2:] == ["v"] * 22


# --- Sin vigente: sin bimestres, antes del primero, entre bimestres ---


def test_sin_bimestres_la_banda_lo_dice_y_no_hay_pastilla_ni_mapa(portada, una_atrasada, bimestres):
    bimestres[0].anio_escolar.periodos.all().delete()

    html = portada()
    frase = (
        "Aún no hay bimestres configurados. Los consolidados aparecerán cuando el administrador "
        "configure los bimestres de 2027."
    )

    assert frase in texto(banda(html))
    assert texto(bloque(html, r'<p class="dir-contexto">.*?</p>')) == f"Dirección · {IE}"
    assert "dir-pendiente" not in html
    assert "dir-mapita" not in html
    assert "dir-mini--solo-fecha" in html
    assert 'datetime="2027-11-22"' in html


def test_sin_bimestres_la_banda_sigue_llevando_a_consolidados(portada, anio_abierto):
    html = banda(portada())

    assert f'href="{CONSOLIDADOS}"' in html
    assert "Ver consolidados" in texto(html)


@pytest.mark.parametrize(
    "dia", [datetime.date(2027, 3, 2), datetime.date(2027, 5, 20), datetime.date(2028, 1, 10)]
)
def test_sin_bimestre_vigente_la_banda_lo_dice_sin_pastilla_ni_mapa(
    portada, una_atrasada, fijar_dia, dia
):
    """Escenario «Antes del primer bimestre» (y entre bimestres)."""
    fijar_dia(dia)
    html = portada()

    assert "Hoy no hay un bimestre vigente" in texto(banda(html))
    assert "dir-pendiente" not in html
    assert "dir-mapita" not in html
    assert f'href="{CONSOLIDADOS}"' in banda(html)


# --- Entregas y el cierre del bimestre ---


def test_entregas_es_una_tarjeta_sin_enlace_con_proximamente(portada, una_atrasada):
    """Escenario «Entregas próximamente»."""
    html = entregas(portada())

    assert "<a " not in html
    assert not re.search(r"<(a|button)\b", html)
    assert re.search(r"<h2\b[^>]*>Entregas</h2>", html)
    assert (
        "Al cierre del bimestre, revisa quién entregó sus notas y habilita correcciones."
        in texto(html)
    )
    assert re.search(r'<span class="dir-proxima">Próximamente</span>', html)


def test_el_cierre_trae_el_boton_que_abre_la_plantilla_del_siagie(portada, una_atrasada):
    """Escenario «Acceso a la plantilla del SIAGIE»."""
    seccion = bloque(portada(), r'<section\b[^>]*aria-labelledby="t-cierre".*?</section>')

    assert re.search(r"<h2\b[^>]*>Al cierre del bimestre</h2>", seccion)
    assert "Cuando una sección tenga sus notas completas, pásalas a la plantilla." in texto(seccion)
    boton = bloque(seccion, r"<button\b[^>]*>.*?</button>")
    assert 'type="button"' in boton
    assert "data-abrir-plantilla" in boton
    assert 'aria-haspopup="dialog"' in boton
    assert texto(boton) == "Completar plantilla del SIAGIE"


def test_el_dialogo_de_subida_va_en_la_pagina_y_cerrado(portada, una_atrasada):
    html = portada()

    dialogo = bloque(html, r'<dialog\b[^>]*id="plantilla-siagie"[^>]*>')
    assert "open" not in dialogo.split()
    assert "Sube la plantilla del SIAGIE" in html
    assert '<script src="/static/js/plantilla-siagie.js" defer></script>' in html


def test_el_orden_de_lectura_es_saludo_banda_entregas_y_cierre(portada, una_atrasada):
    html = portada()

    posiciones = [
        html.index('<span class="saludo">'),
        html.index('id="t-con"'),
        html.index('id="t-ent"'),
        html.index('id="t-cierre"'),
    ]
    assert posiciones == sorted(posiciones)


# --- Barra y marco ---


def test_la_barra_lleva_solo_el_tema_y_la_cuenta(portada, una_atrasada):
    """Escenario «Barra y pie»: sin ☰ ni título."""
    html = portada()

    cabecera = bloque(html, r"<header\b.*?</header>")
    assert "data-menu-navegacion" not in html
    assert "appbar--portada" in cabecera
    assert re.search(r'<span class="bar-title">\s*</span>', cabecera)
    assert cabecera.index("data-tema") < cabecera.index("data-menu-cuenta")
    assert 'aria-label="Cambiar a tema oscuro"' in cabecera


def test_la_portada_precarga_besley(portada, una_atrasada):
    html = portada()

    assert re.search(
        r'<link rel="preload" href="[^"]*besley-latin-600-normal\.woff2" as="font"'
        r' type="font/woff2" crossorigin>',
        html,
    )


def test_el_titulo_de_la_pagina(portada, una_atrasada):
    assert "<title>Inicio · CarpetaDocente</title>" in portada()


def test_la_portada_no_usa_colores_ni_estilos_en_linea(portada, veinticuatro):
    html = portada()

    assert not re.search(r"#[0-9A-Fa-f]{3,8}\b", re.sub(r'href="#[^"]*"', "", html))
    assert " style=" not in html


# --- Quién entra y cuántas consultas hace ---


def test_la_docente_no_ve_la_portada_de_la_direccion(client, docente):
    client.force_login(docente)

    respuesta = client.get(INICIO)

    assert (respuesta.status_code, respuesta.url) == (302, "/docente/")


def test_las_secciones_de_otra_institucion_no_cuentan(
    portada, una_al_dia, otra_institucion, crear_usuario
):
    from institucion.models import AnioEscolar

    ajena = crear_usuario("otra.docente", institucion=otra_institucion)
    anio = AnioEscolar.objects.create(institucion=otra_institucion, anio=2027)
    crear_seccion(anio, 3, "A", docente=ajena, estudiantes=2)

    html = banda(portada())

    assert "por revisar" not in html
    assert len(casillas(html)) == 24
    assert casillas(html).count("o") == 1


def test_la_portada_no_crece_en_consultas_con_24_secciones(
    client, direccion, veinticuatro, django_assert_max_num_queries
):
    client.force_login(direccion)

    with django_assert_max_num_queries(12):
        assert client.get(INICIO).status_code == 200


# --- Acceso a las secciones y a las sesiones de la dirección (D2 y D7; spec acceso-secciones) ---

RUTAS_DE_SECCION = ["direccion:notas", "direccion:asistencia", "direccion:sesiones"]
NO_DISPONIBLE = "La sesión ya no está disponible"


@pytest.fixture
def dos_a(anio_abierto, docente, bimestres):
    return crear_seccion(anio_abierto, 2, "A", docente=docente, estudiantes=2)


@pytest.fixture
def otra_direccion(crear_usuario, otra_institucion):
    return crear_usuario(
        "dir.otra", Usuario.Rol.DIRECCION, institucion=otra_institucion, first_name="Rita"
    )


@pytest.fixture
def entrar_como_direccion(client, direccion):
    client.force_login(direccion)
    return client


def entradas_de_lectura():
    """Lo que dejaría abrir o descargar una sesión (el ingreso de la prueba no cuenta)."""
    return RegistroActividad.objects.filter(
        operacion__in=[
            Operacion.SESION_VISTA,
            Operacion.SESION_DESCARGADA,
            Operacion.INTENTO_SIN_PERMISO,
        ]
    )


def ruta(nombre, objeto):
    return reverse(nombre, args=[objeto.pk])


@pytest.mark.parametrize("nombre", RUTAS_DE_SECCION)
def test_la_direccion_abre_las_secciones_de_su_institucion(entrar_como_direccion, dos_a, nombre):
    respuesta = entrar_como_direccion.get(ruta(nombre, dos_a))

    assert respuesta.status_code == 200


@pytest.mark.parametrize("nombre", RUTAS_DE_SECCION)
def test_la_direccion_de_otra_institucion_recibe_pagina_no_encontrada(
    client, otra_direccion, dos_a, nombre
):
    client.force_login(otra_direccion)

    respuesta = client.get(ruta(nombre, dos_a))

    assert respuesta.status_code == 404
    assert "2.º" not in respuesta.content.decode()


@pytest.mark.parametrize("nombre", RUTAS_DE_SECCION)
def test_una_seccion_de_un_anio_cerrado_o_inexistente_es_pagina_no_encontrada(
    entrar_como_direccion, institucion, docente, nombre
):
    anio = AnioEscolar.objects.create(
        institucion=institucion, anio=2026, estado=AnioEscolar.Estado.CERRADO
    )
    cerrada = crear_seccion(anio, 2, "A", docente=docente, estudiantes=1)

    assert entrar_como_direccion.get(ruta(nombre, cerrada)).status_code == 404
    assert entrar_como_direccion.get(reverse(nombre, args=[cerrada.pk + 1000])).status_code == 404


@pytest.mark.parametrize("nombre", ["direccion:consolidados", *RUTAS_DE_SECCION])
def test_las_rutas_de_la_direccion_solo_leen(entrar_como_direccion, dos_a, nombre):
    url = reverse(nombre, args=[dos_a.pk] if nombre in RUTAS_DE_SECCION else [])

    for metodo in ("post", "put", "patch", "delete"):
        assert getattr(entrar_como_direccion, metodo)(url).status_code == 405


def test_una_ruta_con_un_id_que_no_es_numerico_no_llega_a_la_vista(entrar_como_direccion):
    assert (
        entrar_como_direccion.get("/direccion/consolidados/secciones/abc/notas/").status_code == 404
    )


# --- Página de una sesión en la dirección ---


def pagina_de_la_sesion(cliente, sesion):
    respuesta = cliente.get(ruta("direccion:sesion", sesion))
    assert respuesta.status_code == 200
    return respuesta, respuesta.content.decode()


def test_la_direccion_abre_una_sesion_no_compartida_de_su_institucion(
    entrar_como_direccion, crear_sesion, docente
):
    """Escenario «Abrir y descargar desde Consolidados»: la página sin acciones de la autora."""
    sesion = crear_sesion(
        docente,
        titulo="Leemos un cuento",
        proposito="Que comenten.",
        texto="Inicio",
        compartida=False,
    )

    respuesta, html = pagina_de_la_sesion(entrar_como_direccion, sesion)
    plano = texto(html)

    assert "repositorio/_pagina_sesion.html" in [t.name for t in respuesta.templates]
    for dato in [
        "Leemos un cuento",
        "Que comenten.",
        "Inicio",
        "Comunicación",
        "Ana Quispe",
        "PDF",
    ]:
        assert dato in plano, dato
    assert "Sesión de aprendizaje · PDF" in plano
    assert re.search(rf'href="{ruta("direccion:descargar", sesion)}"', html)
    assert re.search(rf'href="{ruta("direccion:ver", sesion)}"[^>]*target="_blank"', html)
    for ausente in [
        "Eliminar",
        "Compartir",
        "Dejar de compartir",
        "Tu sesión",
        "Mis sesiones",
        "Repositorio",
        "colega",
        "/docente/sesiones/",
    ]:
        assert ausente not in plano and ausente not in html, ausente
    # El único <dialog> es el ☰ del marco: no están los de compartir y eliminar.
    assert "<dialog" not in bloque(html, r"<main[^>]*>.*?</main>")


def test_una_sesion_compartida_lleva_su_chip_para_la_direccion(
    entrar_como_direccion, crear_sesion, docente
):
    _, html = pagina_de_la_sesion(entrar_como_direccion, crear_sesion(docente, compartida=True))

    assert '<span class="chip">Compartida</span>' in html


def test_una_sesion_en_word_no_ofrece_ver(entrar_como_direccion, crear_sesion, docente):
    sesion = crear_sesion(docente, tipo_mime=TIPO_DOCX)

    _, html = pagina_de_la_sesion(entrar_como_direccion, sesion)

    assert "/descargar/" in html and "/ver/" not in html
    assert "Sesión de aprendizaje · Word" in texto(html)


def test_la_pagina_de_la_direccion_lleva_el_menu_de_la_direccion(
    entrar_como_direccion, crear_sesion, docente
):
    _, html = pagina_de_la_sesion(entrar_como_direccion, crear_sesion(docente))

    menu = bloque(html, r"<nav[^>]*>.*?</nav>")
    assert "Consolidados" in texto(menu) and 'aria-current="page"' in menu
    assert "Entregas" in texto(menu)


def test_abrir_la_pagina_no_cuenta_una_vista_ni_deja_entrada(
    entrar_como_direccion, crear_sesion, docente
):
    sesion = crear_sesion(docente, compartida=True)

    pagina_de_la_sesion(entrar_como_direccion, sesion)
    pagina_de_la_sesion(entrar_como_direccion, sesion)

    assert not SesionVista.objects.filter(sesion=sesion).exists()
    assert not entradas_de_lectura()


@pytest.mark.parametrize("caso", ["otra institución", "referencia", "inexistente"])
def test_una_sesion_que_la_direccion_no_ve_es_la_misma_pagina_con_volver_a_consolidados(
    entrar_como_direccion, crear_sesion, colega_de_otra, material_de_referencia, caso
):
    sesion = {
        "otra institución": lambda: crear_sesion(colega_de_otra, titulo="Secreta", compartida=True),
        "referencia": lambda: material_de_referencia(titulo="Secreta"),
    }.get(caso, lambda: None)()
    url = (
        ruta("direccion:sesion", sesion)
        if sesion
        else reverse("direccion:sesion", args=[uuid.uuid4()])
    )

    respuesta = entrar_como_direccion.get(url)
    html = respuesta.content.decode()

    assert respuesta.status_code == 404
    assert NO_DISPONIBLE in html and "Secreta" not in html
    assert "Volver a Consolidados" in html and "Volver a Sesiones" not in html
    assert f'href="{reverse("direccion:consolidados")}"' in html


def test_la_pagina_de_la_docente_sigue_diciendo_volver_a_sesiones(
    client, docente, crear_sesion, otra_docente
):
    client.force_login(docente)

    html = client.get(ruta("sesiones:detalle", crear_sesion(otra_docente))).content.decode()

    assert NO_DISPONIBLE in html and "Volver a Sesiones" in html
    assert "Volver a Consolidados" not in html


def test_un_id_que_no_es_uuid_no_llega_a_la_vista_de_la_sesion(entrar_como_direccion):
    assert entrar_como_direccion.get("/direccion/sesiones/no-es-un-uuid/").status_code == 404


# --- Descargar y ver en la dirección ---


def test_la_direccion_descarga_una_sesion_no_compartida_y_queda_la_entrada(
    entrar_como_direccion, con_archivo, docente, direccion
):
    """Escenario «Abrir y descargar desde Consolidados»."""
    sesion = con_archivo(docente, archivo_nombre="cuento.pdf")

    respuesta = entrar_como_direccion.get(ruta("direccion:descargar", sesion))

    assert respuesta.status_code == 200
    assert b"".join(respuesta.streaming_content) == b"%PDF-1.4 cuerpo"
    assert respuesta["Content-Disposition"] == 'attachment; filename="cuento.pdf"'
    assert "no-store" in respuesta["Cache-Control"]
    (entrada,) = RegistroActividad.objects.filter(operacion=Operacion.SESION_DESCARGADA)
    assert (entrada.usuario_id, entrada.entidad_id) == (direccion.pk, str(sesion.pk))
    assert entrada.detalle == {"modo": "descargar", "propia": False}


def test_la_direccion_ve_el_pdf_en_linea(entrar_como_direccion, con_archivo, docente):
    sesion = con_archivo(docente, archivo_nombre="cuento.pdf")

    respuesta = entrar_como_direccion.get(ruta("direccion:ver", sesion))

    assert respuesta.status_code == 200
    assert respuesta["Content-Disposition"].startswith("inline")


def test_ver_un_word_no_entrega_el_archivo(entrar_como_direccion, con_archivo, docente):
    sesion = con_archivo(docente, tipo_mime=TIPO_DOCX, archivo_nombre="a.docx")

    respuesta = entrar_como_direccion.get(ruta("direccion:ver", sesion))

    assert respuesta.status_code == 404
    assert not entradas_de_lectura()


@pytest.mark.parametrize("nombre", ["direccion:descargar", "direccion:ver"])
def test_la_direccion_no_recibe_el_archivo_de_otra_institucion(
    entrar_como_direccion, con_archivo, colega_de_otra, nombre
):
    sesion = con_archivo(colega_de_otra, compartida=True)

    respuesta = entrar_como_direccion.get(ruta(nombre, sesion))

    assert respuesta.status_code == 404
    assert NO_DISPONIBLE in respuesta.content.decode()
    assert "Volver a Consolidados" in respuesta.content.decode()
    assert not entradas_de_lectura()


# --- Otros roles ---


@pytest.mark.parametrize(
    "nombre", ["direccion:consolidados", "direccion:notas", "direccion:sesion", "direccion:ver"]
)
def test_una_docente_va_a_su_inicio_sin_ver_ni_registrar_nada(
    client, docente, dos_a, con_archivo, nombre
):
    sesion = con_archivo(docente)
    client.force_login(docente)
    args = {
        "direccion:consolidados": [],
        "direccion:notas": [dos_a.pk],
        "direccion:sesion": [sesion.pk],
        "direccion:ver": [sesion.pk],
    }[nombre]

    respuesta = client.get(reverse(nombre, args=args))

    assert respuesta.status_code == 302 and respuesta.url == reverse("docente:portada")
    assert not entradas_de_lectura()


# --- Consolidados: bimestre, mapa y resumen de la I.E. (D3, D4; spec consolidados-direccion) ---


@pytest.fixture
def consolidados(client, direccion):
    """El HTML de Consolidados (o de la ruta pedida) para la dirección."""

    def abrir(ruta=CONSOLIDADOS):
        client.force_login(direccion)
        respuesta = client.get(ruta)
        assert respuesta.status_code == 200
        return respuesta.content.decode()

    return abrir


def tira(html):
    return bloque(html, r'<nav class="hn-periodos[^"]*"[^>]*>.*?</nav>')


def periodos_de_la_tira(html):
    """``{romano: (enlace o None, estado, ¿actual?, fechas para el lector)}``."""
    resultado = {}
    for item in re.findall(r"<li>.*?</li>", tira(html), re.DOTALL):
        romano = re.search(r"<strong>(\w+)</strong>", item).group(1)
        enlace = re.search(r'href="([^"]*)"', item)
        estado = re.search(r'hn-periodo__estado">(\w+)<', item).group(1)
        fechas = re.search(r'sr-only">, (del [^<]*)<', item).group(1)
        resultado[romano] = (
            enlace.group(1).replace("&amp;", "&") if enlace else None,
            estado,
            'aria-current="page"' in item,
            fechas,
        )
    return resultado


def contexto_de(html):
    return texto(bloque(html, r'<p class="dir-contexto">.*?</p>'))


def mapa(html):
    return bloque(html, r'<section class="dir-mapa".*?</section>\s*</div>\s*</section>')


def celdas(html):
    """``{(grado, letra): bloque}`` de las celdas del mapa, enlaces o no."""
    resultado = {}
    for m in re.finditer(r'<(a|div) class="dir-celda[^"]*"[^>]*>.*?</\1>', html, re.DOTALL):
        letra, grado = re.search(
            r'dir-celda__letra">(\w)<span class="sr-only"> de (\d)\.º', m.group(0)
        ).groups()
        resultado[(int(grado), letra)] = m.group(0)
    return resultado


def resumen(html):
    return bloque(html, r'<aside class="cafe dir-resumen".*?</aside>')


def datos_del_resumen(html):
    return {
        texto(dt): texto(dd)
        for dt, dd in re.findall(r"<dt>(.*?)</dt>\s*<dd>(.*?)</dd>", resumen(html), re.DOTALL)
    }


def url_de_notas(seccion, periodo=4):
    return f"{reverse('direccion:notas', args=[seccion.pk])}?periodo={periodo}"


def test_consolidados_dice_el_bimestre_vigente_y_la_tira_marca_el_cuarto(consolidados, bimestres):
    """Escenario «Entra en el vigente»."""
    html = consolidados()

    assert re.search(r"<h1>Consolidados</h1>", html)
    assert contexto_de(html) == "IV bimestre vigente · hoy, lunes 22 de noviembre"
    assert 'aria-label="Bimestres de 2027"' in tira(html)
    periodos = periodos_de_la_tira(html)
    assert list(periodos) == ["I", "II", "III", "IV"]
    assert periodos["IV"][1:] == ("Vigente", True, "del 8 de noviembre al 18 de diciembre")
    assert [periodos[r][1] for r in ("I", "II", "III")] == ["Anterior"] * 3
    assert periodos["I"][3] == "del 9 de marzo al 15 de mayo"


def test_la_tira_enlaza_los_bimestres_anteriores_y_el_vigente_por_get(consolidados, bimestres):
    periodos = periodos_de_la_tira(consolidados())

    assert [periodos[r][0] for r in ("I", "II", "III", "IV")] == [
        f"{CONSOLIDADOS}?periodo={n}" for n in (1, 2, 3, 4)
    ]


def test_un_bimestre_anterior_abre_el_mismo_mapa_y_el_resumen_dice_terminado(
    consolidados, veinticuatro
):
    """Escenario «Bimestre anterior»."""
    html = consolidados(f"{CONSOLIDADOS}?periodo=2")

    assert contexto_de(html) == "II bimestre · terminó el 24 de julio"
    periodos = periodos_de_la_tira(html)
    assert periodos["II"][2] and not periodos["IV"][2]
    assert len(celdas(html)) == 24
    assert "Terminado" in texto(resumen(html))
    assert "24 de julio" in texto(resumen(html))
    assert "para el cierre" not in resumen(html)
    # Los enlaces del mapa conservan el bimestre que se está viendo.
    assert re.search(r'href="[^"]*/notas/\?periodo=2"', mapa(html))


def test_un_bimestre_futuro_no_se_elige_y_pedirlo_abre_el_vigente(
    consolidados, bimestres, fijar_dia
):
    """Escenario «Bimestre futuro pedido»: el 1 de abril solo el I está vigente."""
    fijar_dia(datetime.date(2027, 4, 1))

    html = consolidados(f"{CONSOLIDADOS}?periodo=4")

    periodos = periodos_de_la_tira(html)
    assert periodos["I"][1:3] == ("Vigente", True)
    assert periodos["IV"][:3] == (None, "Futuro", False)
    assert contexto_de(html).startswith("I bimestre vigente")
    assert 'aria-disabled="true"' in tira(html)


@pytest.mark.parametrize("pedido", ["", "?periodo=9", "?periodo=x", "?periodo="])
def test_un_periodo_que_no_vale_abre_el_vigente(consolidados, bimestres, pedido):
    html = consolidados(CONSOLIDADOS + pedido)

    assert periodos_de_la_tira(html)["IV"][2]


def test_entre_dos_bimestres_se_ve_el_ultimo_terminado(consolidados, bimestres, fijar_dia):
    fijar_dia(datetime.date(2027, 5, 20))

    html = consolidados()

    assert contexto_de(html) == "I bimestre · terminó el 15 de mayo"
    assert periodos_de_la_tira(html)["I"][2]


def test_sin_bimestres_consolidados_es_el_estado_vacio(consolidados, anio_abierto):
    """Escenario «Sin bimestres»."""
    html = consolidados()

    assert "Aún no hay bimestres configurados" in html
    assert (
        "Los consolidados aparecerán cuando el administrador configure los bimestres de 2027."
        in texto(html)
    )
    assert contexto_de(html) == f"Dirección · {IE}"
    for ausente in ("hn-periodos", "dir-mapa", "cafe", "dir-celda"):
        assert ausente not in html, ausente


def test_antes_del_primer_bimestre_dice_cuando_empieza_sin_mapa_ni_resumen(
    consolidados, una_atrasada, fijar_dia
):
    """Escenario «Antes del primer bimestre»."""
    fijar_dia(datetime.date(2027, 3, 2))

    html = consolidados()

    assert "Hoy no hay un bimestre vigente" in html
    assert "El I bimestre empieza el 9 de marzo." in texto(html)
    for ausente in ("dir-mapa", "cafe", "dir-celda"):
        assert ausente not in html, ausente
    assert {estado for _, estado, _, _ in periodos_de_la_tira(html).values()} == {"Futuro"}


def test_el_mapa_tiene_una_fila_por_grado_y_una_celda_por_seccion(consolidados, veinticuatro):
    html = consolidados()

    encabezado = bloque(html, r'<h2 class="dir-h2" id="c-mapa">.*?</h2>')
    assert texto(encabezado) == "Las 24 secciones"
    assert re.findall(r'<h3 class="dir-mapa__nombre">([^<]*)</h3>', html) == [
        f"{g}.º" for g in range(1, 7)
    ]
    assert list(celdas(html)) == [(g, n) for g in range(1, 7) for n in "ABCD"]
    assert len(re.findall(r'<ul class="dir-mapa__celdas" role="list">', html)) == 6
    assert 'aria-label="Primer grado"' in html and 'aria-label="Sexto grado"' in html


def test_la_leyenda_dice_los_tres_estados_con_texto(consolidados, veinticuatro):
    leyenda = texto(bloque(consolidados(), r'<ul class="dir-leyenda".*?</ul>'))

    assert leyenda == "Al día Atrasada Sin docente o sin estudiantes"


def test_una_celda_al_dia_dice_su_estado_en_texto_y_enlaza_a_notas(consolidados, veinticuatro):
    """Escenario «Sección al día» (RNF-005: el estado no depende del color)."""
    celda = celdas(consolidados())[(1, "A")]

    assert texto(celda) == "A de 1.º, Ana Quispe Al día"
    assert re.match(r'<a class="dir-celda dir-celda--al-dia" href="([^"]*)"', celda)
    assert url_de_notas(veinticuatro[0]) in celda
    assert re.search(r'<svg\b[^>]*aria-hidden="true"', celda)


def test_una_celda_atrasada_dice_los_dias_sin_completar(consolidados, veinticuatro):
    celda = celdas(consolidados())[(3, "B")]

    assert texto(celda) == "B de 3.º, Ana Quispe 10 días sin completar"
    assert "dir-celda--atrasada" in celda
    assert re.search(r'<svg\b[^>]*aria-hidden="true"', celda)


def test_una_celda_con_notas_y_dias_dice_las_dos_cosas_y_lleva_al_detalle(
    consolidados, anio_abierto, docente, bimestres
):
    """Escenarios «Celdas del mapa» y «Notas que faltan»: ocho celdas de Matemática sin nota."""
    seccion = crear_seccion(anio_abierto, 2, "C", docente=docente, estudiantes=2)
    ids = ids_de(MATEMATICA)
    marcar(seccion, bimestres[3], ids)
    completar_asistencia(seccion, bimestres[3], HOY - datetime.timedelta(days=4), docente)
    faltan = 2 * len(ids)

    celda = celdas(consolidados())[(2, "C")]

    assert texto(celda) == f"C de 2.º, Ana Quispe Faltan {faltan} notas 1 día sin completar"
    assert f'href="{url_de_notas(seccion)}"' in celda


def test_una_sola_nota_o_un_solo_dia_van_en_singular(
    consolidados, anio_abierto, docente, bimestres
):
    seccion = crear_seccion(anio_abierto, 3, "A", docente=docente, estudiantes=1)
    marcar(seccion, bimestres[3], [competencia(MATEMATICA, 1).pk])
    completar_asistencia(seccion, bimestres[3], HOY - datetime.timedelta(days=4), docente)

    celda = celdas(consolidados())[(3, "A")]

    assert texto(celda).endswith("Falta 1 nota 1 día sin completar")


def test_una_seccion_sin_docente_no_es_un_enlace(consolidados, veinticuatro):
    """Escenario «Sección sin docente»."""
    celda = celdas(consolidados())[(4, "C")]

    assert texto(celda) == "C de 4.º Sin docente"
    assert celda.startswith('<div class="dir-celda dir-celda--sin"')
    assert "href" not in celda


def test_una_seccion_sin_estudiantes_abre_en_sesiones(consolidados, veinticuatro):
    """Escenario «Sección sin estudiantes»."""
    celda = celdas(consolidados())[(6, "D")]

    assert texto(celda) == "D de 6.º, Ana Quispe Sin estudiantes"
    sesiones = reverse("direccion:sesiones", args=[veinticuatro[-1].pk])
    assert f'href="{sesiones}?periodo=4"' in celda
    assert "dir-celda--sin" in celda


def test_el_estado_de_cada_celda_esta_escrito(consolidados, veinticuatro):
    for celda in celdas(consolidados()).values():
        assert re.search(
            r"Al día|días? sin completar|Faltan? \d+ notas?|Sin docente|Sin estu", celda
        )


def test_el_resumen_cuenta_las_al_dia_sobre_las_que_tienen_trabajo(consolidados, veinticuatro):
    """Escenario «Resumen del vigente»: 9 de 22 y las dos secciones sin trabajo al pie."""
    html = consolidados()
    resumen_html = resumen(html)

    assert re.search(r'<h2 id="c-cafe">Resumen de la I\.E\.</h2>', resumen_html)
    assert "Faltan 26 días para el cierre" in texto(resumen_html)
    assert re.search(r"<strong>9 de 22</strong>\s*<span>secciones al día</span>", resumen_html)
    assert re.search(r'<progress class="cafe__barra" max="22" value="9" aria-hidden="true">', html)
    assert datos_del_resumen(html) == {
        "Notas que faltan": "0",
        "Días sin completar": "130",
        "Asistencia": "100,0 %",
        "Sesiones": "0",
    }
    assert (
        "Al día: sin notas que falten y sin días por completar. "
        "4.º C no tiene docente y 6.º D no tiene estudiantes." in texto(resumen_html)
    )


def test_el_resumen_suma_lo_mismo_que_las_celdas(consolidados, anio_abierto, docente, bimestres):
    """RNF-017: lo que dice el café es la suma de lo que dicen las celdas."""
    for nombre, estudiantes in (("A", 2), ("B", 3)):
        seccion = crear_seccion(anio_abierto, 2, nombre, docente=docente, estudiantes=estudiantes)
        marcar(seccion, bimestres[3], ids_de(MATEMATICA))
    html = consolidados()

    por_celda = sum(
        int(n) for c in celdas(html).values() for n in re.findall(r"Faltan (\d+) notas", texto(c))
    )

    assert por_celda == (2 + 3) * len(ids_de(MATEMATICA))
    assert datos_del_resumen(html)["Notas que faltan"] == str(por_celda)


def test_el_resumen_cuenta_las_sesiones_del_bimestre_sin_la_referencia(
    consolidados, bimestres, docente, crear_sesion, material_de_referencia, una_al_dia
):
    crear_sesion(docente, creado_en=ENVIADA)
    crear_sesion(docente, creado_en=ENVIADA)
    crear_sesion(docente, creado_en=ENVIADA - datetime.timedelta(days=200))
    material_de_referencia()

    assert datos_del_resumen(consolidados())["Sesiones"] == "2"


def test_consolidados_lleva_el_menu_de_la_direccion_y_consolidados_en_la_barra(
    consolidados, veinticuatro
):
    """Escenario «Navegación de la dirección»: con ☰ y el texto «Consolidados»."""
    html = consolidados()

    barra = bloque(html, r"<header\b.*?</header>")
    assert "data-menu-navegacion" in barra
    assert re.search(r'<span class="bar-title">Consolidados</span>', barra)
    assert "data-tema" in barra and "data-menu-cuenta" in barra
    menu = bloque(html, r'<nav aria-label="Navegación principal">.*?</nav>')
    assert re.search(r'<a href="/direccion/consolidados/" aria-current="page">', menu)


def test_consolidados_usa_solo_tokens_y_el_titulo_de_la_pagina(consolidados, veinticuatro):
    html = consolidados()

    assert "<title>Consolidados · CarpetaDocente</title>" in html
    assert not re.search(r"#[0-9A-Fa-f]{3,8}\b", re.sub(r'href="#[^"]*"', "", html))
    assert " style=" not in html


def test_consolidados_con_el_anio_sin_secciones_lo_dice(consolidados, bimestres):
    html = consolidados()

    assert "Aún no hay secciones" in html
    assert "dir-celda" not in html and "cafe" not in html


def test_las_secciones_de_otra_institucion_no_salen_en_el_mapa(
    consolidados, una_al_dia, otra_institucion, crear_usuario
):
    ajena = crear_usuario("otra.docente", institucion=otra_institucion)
    anio = AnioEscolar.objects.create(institucion=otra_institucion, anio=2027)
    crear_seccion(anio, 3, "A", docente=ajena, estudiantes=2)

    html = consolidados()

    assert list(celdas(html)) == [(2, "B")]
    assert "otra.docente" not in html


def test_consolidados_no_crece_en_consultas_con_24_secciones(
    client, direccion, veinticuatro, django_assert_max_num_queries
):
    client.force_login(direccion)

    with django_assert_max_num_queries(16):
        assert client.get(CONSOLIDADOS).status_code == 200


# --- Detalle de una sección y pestaña Notas (D2, D3; specs consolidados-direccion) ---


@pytest.fixture
def con_notas(anio_abierto, docente, bimestres, areas_a_cargo):
    """2.º A con tres estudiantes; Matemática y Comunicación marcadas en el IV bimestre.

    Matemática (4 competencias): AD 1, A 4, B 1, C 0 y faltan 6; Gabriel y Ana quedan pendientes.
    Comunicación está completa; Arte no tiene competencias marcadas.
    """
    seccion = crear_seccion(anio_abierto, 2, "A", docente=docente, estudiantes=0)
    luciana, gabriel, ana = crear_estudiantes(
        seccion, "AGUILAR FLORES, LUCIANA", "MEDINA CASTRO, GABRIEL", "QUISPE MAMANI, ANA LUCÍA"
    )
    cuarto = bimestres[3]
    marcar(seccion, cuarto, ids_de(MATEMATICA, COMUNICACION))
    for numero, nivel in enumerate(["A", "A", "AD", "A"], start=1):
        poner_nota(luciana, competencia(MATEMATICA, numero), cuarto, nivel)
    poner_nota(gabriel, competencia(MATEMATICA, 1), cuarto, "B")
    poner_nota(gabriel, competencia(MATEMATICA, 2), cuarto, "A")
    for estudiante in (luciana, gabriel, ana):
        for competencia_id in ids_de(COMUNICACION):
            poner_nota(estudiante, competencia_id, cuarto, "A")
    return seccion


def url_de(nombre, seccion, **consulta):
    url = reverse(nombre, args=[seccion.pk])
    return f"{url}?{urlencode(consulta)}" if consulta else url


@pytest.fixture
def detalle(client, direccion):
    """El HTML de una pestaña del detalle (200) o su respuesta."""

    def abrir(url):
        client.force_login(direccion)
        respuesta = client.get(url)
        assert respuesta.status_code == 200, respuesta.status_code
        return respuesta.content.decode()

    return abrir


def cabecera_del_detalle(html):
    return bloque(html, r'<header class="det-cabecera">.*?</header>')


def pestanas(html):
    return bloque(html, r'<nav class="det-pestanas".*?</nav>')


def cafe_del_detalle(html):
    return bloque(html, r'<section class="cafe det-cafe".*?</section>')


def filas_de_areas(html):
    """``{área: [textos de sus celdas]}`` de la tabla de notas por área."""
    tabla = bloque(html, r'<table class="con-tabla">.*?</table>')
    return {
        re.search(r"<th scope=\"row\">(.*?)</th>", fila, re.DOTALL).group(1).strip(): [
            texto(celda) for celda in re.findall(r"<td[^>]*>.*?</td>", fila, re.DOTALL)
        ]
        for fila in re.findall(r"<tr[^>]*>\s*<th scope=\"row\">.*?</tr>", tabla, re.DOTALL)
    }


def tira_de_areas(html):
    tira_ = bloque(html, r'<nav class="hn-tira det-tira".*?</nav>')
    return [
        (texto(a), 'aria-current="page"' in a, re.search(r'href="([^"]*)"', a).group(1))
        for a in re.findall(r"<a [^>]*>.*?</a>", tira_, re.DOTALL)
    ]


def hoja_de_notas(html):
    return bloque(html, r'<section class="hn-hoja det-hoja".*?</section>')


def celdas_de_la_hoja(html):
    return re.findall(r'<span class="sr-only">([^<]*, C\d: [^<]*)</span>', hoja_de_notas(html))


def test_el_detalle_dice_la_tutora_los_estudiantes_el_anio_y_el_titulo(detalle, con_notas):
    """Escenario «Flujo alternativo válido (US-040)»."""
    html = detalle(url_de("direccion:notas", con_notas))

    cabecera = cabecera_del_detalle(html)
    assert texto(bloque(cabecera, r'<p class="small">.*?</p>')) == (
        "Tutora: Ana Quispe · 3 estudiantes · 2027"
    )
    assert re.search(r"<h1>2\.º grado, sección A</h1>", cabecera)
    assert "<title>2.º grado, sección A · CarpetaDocente</title>" in html
    assert re.search(r'<span class="bar-title">Consolidados</span>', html)
    assert "data-menu-navegacion" in html


def test_una_sola_estudiante_va_en_singular(detalle, anio_abierto, docente, bimestres):
    seccion = crear_seccion(anio_abierto, 3, "A", docente=docente, estudiantes=1)

    html = detalle(url_de("direccion:sesiones", seccion))

    assert "Tutora: Ana Quispe · 1 estudiante · 2027" in texto(cabecera_del_detalle(html))


def test_la_tira_del_detalle_enlaza_la_misma_pestana_en_otro_bimestre(detalle, con_notas):
    html = detalle(url_de("direccion:notas", con_notas))

    periodos = periodos_de_la_tira(html)
    base = reverse("direccion:notas", args=[con_notas.pk])
    assert [periodos[r][0] for r in ("I", "II", "III", "IV")] == [
        f"{base}?periodo={n}" for n in (1, 2, 3, 4)
    ]
    assert periodos["IV"][1:3] == ("Vigente", True)


def test_las_pestanas_son_enlaces_y_marcan_la_activa(detalle, con_notas):
    html = detalle(url_de("direccion:notas", con_notas))

    nav = pestanas(html)
    assert 'aria-label="Consolidado de 2.º A"' in nav
    enlaces = re.findall(r'<a href="([^"]*)"( aria-current="page")?>([^<]*)</a>', nav)
    assert [(e[2], bool(e[1])) for e in enlaces] == [
        ("Notas", True),
        ("Asistencia", False),
        ("Sesiones", False),
    ]
    assert [e[0] for e in enlaces] == [
        f"{url_de(nombre, con_notas)}?periodo=4"
        for nombre in ("direccion:notas", "direccion:asistencia", "direccion:sesiones")
    ]


def test_el_detalle_no_trae_selector_de_seccion_ni_enlaces_de_volver(detalle, con_notas):
    html = detalle(url_de("direccion:notas", con_notas))

    assert "<select" not in html
    assert "Volver" not in html and "‹" not in html


def test_el_cafe_de_notas_dice_las_notas_que_faltan_y_las_registradas(detalle, con_notas):
    """Escenario «Notas registradas»: 3 estudiantes × (4 + 3) competencias, faltan 6."""
    html = detalle(url_de("direccion:notas", con_notas))
    total = 3 * len(ids_de(MATEMATICA, COMUNICACION))

    cafe = cafe_del_detalle(html)
    assert re.search(r'<h2 id="cafe-titulo">2\.º A · IV bimestre</h2>', cafe)
    assert "Vigente, hasta hoy lunes 22 de noviembre" in texto(cafe)
    assert re.search(r"<h3>Notas</h3>", cafe)
    assert re.search(r"<strong>6</strong>\s*<span>notas faltan</span>", cafe)
    assert re.search(
        rf'<progress class="cafe__barra" max="{total}" value="{total - 6}" aria-hidden="true">',
        cafe,
    )
    assert f"{total - 6} de {total} registradas" in texto(cafe)


def test_el_cafe_de_un_bimestre_anterior_dice_terminado(detalle, con_notas):
    html = detalle(url_de("direccion:notas", con_notas, periodo=2))

    assert "II bimestre" in texto(cafe_del_detalle(html))
    assert "Terminado · 24 de julio" in texto(cafe_del_detalle(html))
    assert "Notas" in texto(cafe_del_detalle(html))


def test_el_cafe_de_notas_dice_lo_mismo_que_la_celda_del_mapa(detalle, consolidados, con_notas):
    """Escenario «Mismos números en el mapa y en el detalle» (RNF-017)."""
    celda = texto(celdas(consolidados())[(2, "A")])
    cafe = texto(cafe_del_detalle(detalle(url_de("direccion:notas", con_notas))))

    assert "Faltan 6 notas" in celda
    assert "6 notas faltan" in cafe


def test_la_tabla_por_area_cuenta_los_niveles_y_las_que_faltan(detalle, con_notas):
    """Escenarios «Tabla por área» y «Área del docente de curso»."""
    html = detalle(url_de("direccion:notas", con_notas))
    filas = filas_de_areas(html)

    assert "Notas por área" in texto(html)
    assert "Solo competencias marcadas en el IV bimestre" in texto(html)
    assert filas["Matemática"] == ["1", "4", "1", "0", "6"]
    assert filas["Comunicación"][:4] == ["0", "9", "0", "0"]
    assert "Educación Física" not in filas, "área del docente de curso"
    assert "Inglés como lengua extranjera" not in filas, "área del docente de curso"
    orden = {area.nombre: area.orden for area in Area.objects.all()}
    assert "Arte y Cultura" in filas
    assert list(filas) == sorted(filas, key=orden.__getitem__), "en el orden del SIAGIE"


def test_un_area_sin_faltantes_dice_ninguna_con_texto_y_un_area_sin_marcas_lo_dice(
    detalle, con_notas
):
    """Escenario «Tabla por área»: «Ninguna» y «Sin competencias marcadas» (RNF-005)."""
    html = detalle(url_de("direccion:notas", con_notas))
    filas = filas_de_areas(html)

    assert filas["Comunicación"][4] == "Ninguna"
    assert filas["Arte y Cultura"] == ["Sin competencias marcadas"]
    tabla = bloque(html, r'<table class="con-tabla">.*?</table>')
    assert re.search(r'<caption class="sr-only">Notas de 2\.º A por área, IV bimestre', tabla)
    assert re.search(
        r'<td colspan="5" class="con-sin-marcar">Sin competencias marcadas</td>', tabla
    )
    assert 'class="con-faltan con-faltan--si">6</td>' in tabla


def test_la_suma_de_las_que_faltan_por_area_es_la_del_cafe(detalle, con_notas):
    html = detalle(url_de("direccion:notas", con_notas))

    faltan = sum(
        int(f[4]) for f in filas_de_areas(html).values() if len(f) == 5 and f[4] != "Ninguna"
    )

    assert faltan == 6


def test_la_tira_de_areas_abre_la_primera_con_marcas_y_marca_la_pedida(detalle, con_notas):
    por_defecto = tira_de_areas(detalle(url_de("direccion:notas", con_notas)))
    pedida = tira_de_areas(detalle(url_de("direccion:notas", con_notas, area=COMUNICACION)))
    invalida = tira_de_areas(detalle(url_de("direccion:notas", con_notas, area="9999")))

    nombres = [nombre for nombre, _, _ in por_defecto]
    assert "Educación Física" not in nombres
    assert [n for n, actual, _ in por_defecto if actual] == ["Comunicación"], "la primera marcada"
    assert [n for n, actual, _ in pedida if actual] == ["Comunicación"]
    assert por_defecto == invalida
    assert all(href.endswith("#hoja") and "periodo=4" in href for _, _, href in por_defecto)
    assert not any("filtro" in href for _, _, href in por_defecto)


def test_la_hoja_es_de_solo_lectura_sin_campos_ni_guardar(detalle, con_notas):
    """Escenarios «Hoja de notas en solo lectura» y «Solo lectura»."""
    html = detalle(url_de("direccion:notas", con_notas, area=MATEMATICA))
    hoja = hoja_de_notas(html)

    assert re.search(r'<h2 id="titulo-area">Matemática</h2>', hoja)
    assert "3 estudiantes · 4 competencias · Solo lectura" in texto(hoja)
    assert 'aria-readonly="true"' in hoja and 'role="grid"' in hoja
    for ausente in ("<input", "<button", "<textarea", "<select", "contenteditable"):
        assert ausente not in html.split("<main")[1], ausente
    principal = bloque(html, r"<main[^>]*>.*?</main>")
    for ausente in ("Guardar", "Rellenar", "borrador", "hn-barra"):
        assert ausente not in principal, ausente


def test_la_hoja_lista_a_los_estudiantes_activos_con_su_nivel_o_sin_nota(detalle, con_notas):
    html = detalle(url_de("direccion:notas", con_notas, area=MATEMATICA))

    assert celdas_de_la_hoja(html) == [
        "AGUILAR FLORES, LUCIANA, C1: A",
        "AGUILAR FLORES, LUCIANA, C2: A",
        "AGUILAR FLORES, LUCIANA, C3: AD",
        "AGUILAR FLORES, LUCIANA, C4: A",
        "MEDINA CASTRO, GABRIEL, C1: B",
        "MEDINA CASTRO, GABRIEL, C2: A",
        "MEDINA CASTRO, GABRIEL, C3: sin nota",
        "MEDINA CASTRO, GABRIEL, C4: sin nota",
        "QUISPE MAMANI, ANA LUCÍA, C1: sin nota",
        "QUISPE MAMANI, ANA LUCÍA, C2: sin nota",
        "QUISPE MAMANI, ANA LUCÍA, C3: sin nota",
        "QUISPE MAMANI, ANA LUCÍA, C4: sin nota",
    ]
    assert hoja_de_notas(html).count('aria-hidden="true">—</span>') == 2 * 6
    assert "— Nota que falta." in texto(html)
    assert re.findall(r'<span class="hn-numero" aria-hidden="true">(\d\d)</span>', html) == [
        "01",
        "02",
        "03",
    ]


def test_los_encabezados_de_las_competencias_dicen_su_texto(detalle, con_notas):
    html = detalle(url_de("direccion:notas", con_notas, area=MATEMATICA))

    cantidad = competencia(MATEMATICA, 1).nombre
    assert f"C1: {cantidad}" in html
    assert re.search(r'<th scope="col" class="hn-comp"', hoja_de_notas(html))


def test_un_estudiante_trasladado_no_sale_en_la_hoja(detalle, con_notas):
    crear_estudiantes(con_notas, "ZEGARRA, TOMÁS", estado=Estudiante.Estado.TRASLADADO)

    html = detalle(url_de("direccion:notas", con_notas, area=MATEMATICA))

    assert "ZEGARRA" not in html
    assert "Tutora: Ana Quispe · 3 estudiantes" in texto(html)


def test_el_filtro_dice_cuantos_estudiantes_estan_pendientes(detalle, con_notas):
    """Escenario «Pendientes del área»: Gabriel y Ana tienen alguna nota de Matemática sin poner."""
    html = detalle(url_de("direccion:notas", con_notas, area=MATEMATICA))

    filtro = bloque(html, r'<nav class="det-filtro".*?</nav>')
    assert 'aria-label="Estudiantes de la hoja"' in filtro
    enlaces = re.findall(r'<a href="([^"]*)"( aria-current="page")?>(.*?)</a>', filtro, re.DOTALL)
    assert [(texto(e[2]), bool(e[1])) for e in enlaces] == [
        ("Todos", True),
        ("Pendientes 2", False),
    ]
    assert "filtro=pendientes" in enlaces[1][0] and "area=063" in enlaces[1][0]
    assert "periodo=4" in enlaces[1][0] and "filtro" not in enlaces[0][0]


def test_pendientes_deja_solo_a_esos_estudiantes_y_cambia_el_titulo(detalle, con_notas):
    html = detalle(url_de("direccion:notas", con_notas, area=MATEMATICA, filtro="pendientes"))

    assert re.search(r'<h2 id="titulo-area">Pendientes · Matemática</h2>', html)
    assert "2 estudiantes con notas faltantes · Solo lectura" in texto(hoja_de_notas(html))
    nombres = {c.rsplit(", C", 1)[0] for c in celdas_de_la_hoja(html)}
    assert nombres == {"MEDINA CASTRO, GABRIEL", "QUISPE MAMANI, ANA LUCÍA"}
    assert re.findall(r'<span class="hn-numero" aria-hidden="true">(\d\d)</span>', html) == [
        "02",
        "03",
    ], "conservan su número de la lista"
    filtro = bloque(html, r'<nav class="det-filtro".*?</nav>')
    assert re.search(r'<a href="[^"]*" aria-current="page">Pendientes', filtro)
    assert "6 notas faltan" in texto(cafe_del_detalle(html)), "el café no cambia con el filtro"


def test_pendientes_de_un_area_completa_lo_dice(detalle, con_notas):
    html = detalle(url_de("direccion:notas", con_notas, area=COMUNICACION, filtro="pendientes"))

    assert "Pendientes · Comunicación" in html
    assert "Ningún estudiante tiene notas pendientes en Comunicación." in texto(html)
    assert celdas_de_la_hoja(html) == []


def test_un_area_sin_competencias_marcadas_no_trae_hoja(detalle, con_notas):
    html = detalle(url_de("direccion:notas", con_notas, area="0001"))

    assert "Arte y Cultura" in texto(hoja_de_notas(html))
    assert "Sin competencias marcadas en el IV bimestre." in texto(html)
    assert celdas_de_la_hoja(html) == [] and '<table class="hn-tabla"' not in html


def test_un_bimestre_sin_marcas_lo_dice_sin_hoja(detalle, con_notas):
    html = detalle(url_de("direccion:notas", con_notas, periodo=3))

    assert "Sin competencias marcadas en el III bimestre" in texto(html)
    assert "hn-hoja" not in html and "con-tabla" not in html
    cafe = texto(cafe_del_detalle(html))
    assert "0 notas faltan" in cafe and "Sin competencias marcadas" in cafe
    assert "registradas" not in cafe and "progress" not in cafe_del_detalle(html)


@pytest.mark.parametrize("nombre", ["direccion:notas", "direccion:asistencia"])
def test_una_seccion_sin_estudiantes_lleva_de_notas_y_asistencia_a_sesiones(
    entrar_como_direccion, anio_abierto, docente, bimestres, nombre
):
    """Escenario «Pestaña sin estudiantes pedida por su dirección»."""
    vacia = crear_seccion(anio_abierto, 6, "D", docente=docente, estudiantes=0)

    respuesta = entrar_como_direccion.get(url_de(nombre, vacia, periodo=3))

    assert respuesta.status_code == 302
    assert respuesta.url == url_de("direccion:sesiones", vacia, periodo=3)


def test_una_seccion_sin_docente_dice_que_no_hay_notas_que_mostrar(
    detalle, anio_abierto, bimestres
):
    sin_docente = crear_seccion(anio_abierto, 4, "C", docente=None, estudiantes=2)

    html = detalle(url_de("direccion:notas", sin_docente))

    assert "Tutora: sin docente · 2 estudiantes · 2027" in texto(cabecera_del_detalle(html))
    assert "Esta sección no tiene docente: no hay notas que mostrar." in texto(html)
    assert "hn-hoja" not in html


@pytest.mark.parametrize("dia", [datetime.date(2027, 3, 2)])
def test_el_detalle_sin_bimestre_que_mostrar_dice_cuando_empieza(
    detalle, con_notas, fijar_dia, dia
):
    fijar_dia(dia)

    html = detalle(url_de("direccion:notas", con_notas))

    assert "Hoy no hay un bimestre vigente" in html
    assert "El I bimestre empieza el 9 de marzo." in texto(html)
    assert "cafe" not in html and "con-tabla" not in html


def test_el_detalle_sin_bimestres_dice_que_no_estan_configurados(detalle, anio_abierto, docente):
    seccion = crear_seccion(anio_abierto, 2, "A", docente=docente, estudiantes=2)

    html = detalle(url_de("direccion:notas", seccion))

    assert "Aún no hay bimestres configurados" in html
    assert "hn-periodos" not in html


def test_el_detalle_usa_solo_tokens_y_no_cambia_nada(detalle, con_notas):
    html = detalle(url_de("direccion:notas", con_notas, area=MATEMATICA))

    assert not re.search(r"#[0-9A-Fa-f]{3,8}\b", re.sub(r'href="#[^"]*"', "", html))
    assert " style=" not in html.replace('style="--columnas', "")
    assert "<form" not in bloque(html, r"<main[^>]*>.*?</main>")


def test_la_pestana_notas_no_crece_en_consultas(
    client, direccion, con_notas, django_assert_max_num_queries
):
    client.force_login(direccion)

    with django_assert_max_num_queries(22):
        assert client.get(url_de("direccion:notas", con_notas, area=MATEMATICA)).status_code == 200


@pytest.mark.parametrize("nombre", ["post", "put", "delete"])
def test_los_guardados_de_la_direccion_no_guardan_nada(entrar_como_direccion, con_notas, nombre):
    """Escenario «Caso de error (US-040)»: el detalle solo lee y la hoja no se guarda."""
    antes = Calificacion.objects.count()
    url = url_de("direccion:notas", con_notas, area=MATEMATICA)

    respuesta = getattr(entrar_como_direccion, nombre)(url, {"nivel": "AD"})

    assert respuesta.status_code == 405
    assert Calificacion.objects.count() == antes


# --- Pestaña Asistencia (D5; spec consolidados-direccion, «Pestaña Asistencia») ---


def poner_marcas(seccion, estudiante, usuario, estados):
    """Una marca por día de clase del IV bimestre hasta hoy, con ``estados`` en orden; las
    jornadas se crean una sola vez por día."""
    dias = dias_de_clase(Periodo.objects.get(anio_escolar=seccion.anio_escolar, numero=4), HOY)
    for dia, estado in zip(dias, estados, strict=True):
        jornada, _ = Jornada.objects.get_or_create(
            seccion=seccion, fecha=dia, defaults={"registrado_por": usuario}
        )
        Asistencia.objects.create(jornada=jornada, estudiante=estudiante, estado=estado)


@pytest.fixture
def con_asistencia(anio_abierto, docente, bimestres):
    """2.º A con dos estudiantes y 11 días de clase (del 8 al 22 de noviembre) completos.

    Luciana: 8 Asistió, 0 Tarde, 2 Faltó, 1 Justificado (72,7 %); Gabriel: 11 Asistió (100,0 %).
    """
    seccion = crear_seccion(anio_abierto, 2, "A", docente=docente, estudiantes=0)
    luciana, gabriel = crear_estudiantes(
        seccion, "AGUILAR FLORES, LUCIANA", "MEDINA CASTRO, GABRIEL"
    )
    estado = Asistencia.Estado
    poner_marcas(
        seccion,
        luciana,
        docente,
        [estado.ASISTIO] * 8 + [estado.FALTO] * 2 + [estado.JUSTIFICADO],
    )
    poner_marcas(seccion, gabriel, docente, [estado.ASISTIO] * 11)
    return seccion


def tabla_de_asistencia(html):
    """``{nombre: [asistió, tarde, faltó, justificado, %]}`` de la tabla por estudiante."""
    tabla = bloque(html, r'<table class="det-tabla">.*?</table>')
    filas = {}
    for fila in re.findall(r"<tr>\s*<th scope=\"row\".*?</tr>", tabla, re.DOTALL):
        nombre = texto(bloque(fila, r'<th scope="row".*?</th>'))
        filas[nombre] = [
            texto(re.sub(r'<span class="(?:sr-only|estado)[^"]*"[^>]*>.*?</span>', "", celda))
            for celda in re.findall(r"<td.*?</td>", fila, re.DOTALL)
        ]
    return filas


def test_la_pestana_asistencia_dice_los_dias_de_clase_del_bimestre_hasta_hoy(
    detalle, con_asistencia
):
    """Escenario del boceto: «11 días de clase, del 8 al 22 de noviembre»."""
    html = detalle(url_de("direccion:asistencia", con_asistencia))

    assert re.search(r'<h2 id="asis-titulo">Totales por estudiante</h2>', html)
    assert "11 días de clase, del 8 al 22 de noviembre" in texto(html)
    assert re.search(r'<a href="[^"]*" aria-current="page">Asistencia</a>', pestanas(html))
    assert "Asistencia de 2.º A por estudiante, IV bimestre" in html


def test_cada_estudiante_activo_tiene_sus_totales_y_su_porcentaje(detalle, con_asistencia):
    """Escenario «Totales de un estudiante»: 8, 0, 2, 1 y «72,7 %»."""
    html = detalle(url_de("direccion:asistencia", con_asistencia))

    assert tabla_de_asistencia(html) == {
        "01 AGUILAR FLORES, LUCIANA": ["8", "0", "2", "1", "72,7 %"],
        "02 MEDINA CASTRO, GABRIEL": ["11", "0", "0", "0", "100,0 %"],
    }
    encabezados = re.findall(r'<th scope="col"[^>]*>([^<]*)</th>', html)
    assert encabezados == ["Apellidos y nombres", "Asistió", "Tarde", "Faltó", "Justif.", "%"]


def test_los_totales_dicen_el_estado_con_texto_para_el_lector(detalle, con_asistencia):
    html = detalle(url_de("direccion:asistencia", con_asistencia))

    fila = bloque(html, r"<tr>\s*<th scope=\"row\".*?</tr>")
    assert re.findall(r'<span class="sr-only">([^<]*)</span>', fila) == [
        "Asistió ",
        "Tarde ",
        "Faltó ",
        "Justificado ",
        "Asistencia ",
    ]
    assert fila.count('aria-hidden="true"') >= 4


def test_el_cafe_de_asistencia_dice_el_porcentaje_los_cuatro_totales_y_los_dias(
    detalle, con_asistencia
):
    """Escenario «Días completos»: 19 + 0 de 22 marcas = 86,4 %."""
    cafe = cafe_del_detalle(detalle(url_de("direccion:asistencia", con_asistencia)))

    assert re.search(r"<h3>Asistencia</h3>", cafe)
    assert "86,4 % de asistencia" in texto(cafe)
    totales = {
        texto(dt): texto(dd)
        for dt, dd in re.findall(r"<dt>(.*?)</dt>\s*<dd>(.*?)</dd>", cafe, re.DOTALL)
    }
    assert totales == {"Asistió": "19", "Tarde": "0", "Faltó": "2", "Justificado": "1"}
    assert "Todos los días completos" in texto(cafe)
    assert "sin completar" not in texto(cafe)


def test_el_cafe_cuenta_los_dias_sin_completar_como_la_celda_del_mapa(
    detalle, consolidados, con_asistencia
):
    """Escenarios «Día sin tomar» y «Mismos números en el mapa y en el detalle»: el martes 16
    y el jueves 18 faltan para Gabriel."""
    gabriel = con_asistencia.estudiantes.get(apellidos="MEDINA CASTRO")
    Asistencia.objects.filter(
        estudiante=gabriel,
        jornada__fecha__in=[datetime.date(2027, 11, 16), datetime.date(2027, 11, 18)],
    ).delete()

    celda = texto(celdas(consolidados())[(2, "A")])
    cafe = texto(cafe_del_detalle(detalle(url_de("direccion:asistencia", con_asistencia))))

    assert "2 días sin completar" in celda
    assert "2 días sin completar" in cafe
    assert "Todos los días completos" not in cafe


def test_hoy_sin_marcar_no_cuenta_como_dia_sin_completar(detalle, con_asistencia):
    Asistencia.objects.filter(jornada__fecha=HOY).delete()

    html = detalle(url_de("direccion:asistencia", con_asistencia))

    assert "Todos los días completos" in texto(cafe_del_detalle(html))
    assert "10 días de clase, del 8 al 19 de noviembre" not in texto(html)
    assert "11 días de clase, del 8 al 22 de noviembre" in texto(html), "hoy sí es día de clase"


def test_sin_marcas_el_porcentaje_es_una_raya(detalle, anio_abierto, docente, bimestres):
    seccion = crear_seccion(anio_abierto, 3, "A", docente=docente, estudiantes=1)

    html = detalle(url_de("direccion:asistencia", seccion))

    assert "— de asistencia" in texto(cafe_del_detalle(html))
    assert list(tabla_de_asistencia(html).values()) == [["0", "0", "0", "0", "—"]]
    assert "10 días sin completar" in texto(cafe_del_detalle(html))


def test_un_trasladado_sale_de_la_tabla_pero_sus_marcas_cuentan_en_la_seccion(
    detalle, con_asistencia
):
    """Deuda a US-033: los totales usan los activos de hoy (design, Risks)."""
    gabriel = con_asistencia.estudiantes.get(apellidos="MEDINA CASTRO")
    Estudiante.objects.filter(pk=gabriel.pk).update(estado=Estudiante.Estado.TRASLADADO)

    html = detalle(url_de("direccion:asistencia", con_asistencia))

    assert list(tabla_de_asistencia(html)) == ["01 AGUILAR FLORES, LUCIANA"]
    assert {"Asistió": "19"}.items() <= {
        texto(dt): texto(dd)
        for dt, dd in re.findall(
            r"<dt>(.*?)</dt>\s*<dd>(.*?)</dd>", cafe_del_detalle(html), re.DOTALL
        )
    }.items()


def test_un_bimestre_anterior_cuenta_hasta_su_ultimo_dia_de_clase(
    detalle, anio_abierto, docente, bimestres
):
    seccion = crear_seccion(anio_abierto, 2, "B", docente=docente, estudiantes=1)
    n = len(dias_de_clase(bimestres[1], bimestres[1].fecha_fin))

    html = detalle(url_de("direccion:asistencia", seccion, periodo=2))

    assert f"{n} días de clase, del 25 de mayo al 23 de julio" in texto(html)
    assert "Terminado · 24 de julio" in texto(cafe_del_detalle(html))


def test_la_asistencia_no_crece_en_consultas(
    client, direccion, con_asistencia, django_assert_max_num_queries
):
    client.force_login(direccion)

    with django_assert_max_num_queries(14):
        assert client.get(url_de("direccion:asistencia", con_asistencia)).status_code == 200


def test_la_pestana_de_asistencia_no_tiene_formularios_ni_campos(detalle, con_asistencia):
    html = detalle(url_de("direccion:asistencia", con_asistencia))
    principal = bloque(html, r"<main[^>]*>.*?</main>")

    for ausente in ("<form", "<input", "<button", "<select", "Marcar", "Guardar"):
        assert ausente not in principal, ausente
