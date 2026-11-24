"""Vistas de la dirección: la portada (US-040, D9; spec pantallas-de-inicio, «Inicio de la
dirección»).

Comprueban el HTML que sale del servidor, sin JavaScript. El día es el lunes 22 de noviembre de
2027, en el IV bimestre (del 8 de noviembre al 18 de diciembre), salvo donde la prueba lo cambia.
"""

import datetime
import re

import pytest
from django.utils import timezone

from direccion.tests.conftest import HOY, completar_asistencia, crear_seccion

pytestmark = pytest.mark.django_db

INICIO = "/direccion/"
CONSOLIDADOS = "/direccion/consolidados/"
IE = "I.E. Ficticia N.° 1"


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
