"""La plantilla de la hoja de notas (spec registro-notas; design de US-020, D9).

El servidor dibuja el marco (título, periodo, «Competencias», tira de áreas, avisos, diálogo de
salida, regiones del lector de pantalla y el ``json_script``); ``notas.js`` dibuja la rejilla (sus
pruebas son las de punta a punta). Aquí se revisa el HTML. El día se fija con el fixture ``hoy``.
"""

import html as html_lib
import re

import pytest
from django.urls import reverse

from notas.tests.conftest import (
    AGO_1,
    ARTE,
    COMUNICACION,
    EDUCACION_FISICA,
    INGLES,
    MAR_2,
    MATEMATICA,
    crear_estudiantes,
    ids_de,
    marcar,
)

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def hoy(hoy):
    return hoy


@pytest.fixture
def matematica(seccion_tutora, ie, bimestres):
    """Ana Quispe y Matemática y Comunicación marcadas en B2 y B3."""
    crear_estudiantes(seccion_tutora, "QUISPE, ANA")
    for periodo in bimestres[1:3]:
        marcar(seccion_tutora, periodo, ids_de(MATEMATICA, COMUNICACION))
    return bimestres[2]


def pagina(cliente, seccion, **parametros):
    respuesta = cliente.get(reverse("notas:hoja", args=[seccion.pk]), parametros)
    assert respuesta.status_code == 200
    return respuesta.content.decode()


def texto(fragmento):
    """El texto visible de un fragmento HTML, con los espacios normalizados."""
    return " ".join(html_lib.unescape(re.sub(r"<[^>]+>", " ", fragmento)).split())


def pildoras(html):
    return re.findall(r"<button [^>]*data-area-pildora=.*?</button>", html, re.DOTALL)


def periodo_visible(html):
    return texto(re.search(r'<p class="notas-periodo".*?</p>', html, re.DOTALL).group(0))


# --- Cabecera y periodo ---


def test_la_hoja_dibuja_su_titulo_y_el_periodo(cliente, seccion_tutora, matematica):
    html = pagina(cliente, seccion_tutora)

    assert html.count("<h1") == 1
    assert "Notas · 2.º A" in texto(re.search(r"<h1.*?</h1>", html, re.DOTALL).group(0))
    assert periodo_visible(html) == "B3 · Vigente"


def test_el_boton_competencias_lleva_el_periodo_y_el_area(cliente, seccion_tutora, matematica):
    html = pagina(cliente, seccion_tutora, periodo="2", area=COMUNICACION)

    enlace = re.search(r"<a [^>]*data-ir-competencias[^>]*>.*?</a>", html, re.DOTALL).group(0)
    base = reverse("competencias:pantalla", args=[seccion_tutora.pk])
    assert f'href="{base}?periodo=2&amp;area={COMUNICACION}"' in enlace
    assert "Competencias" in texto(enlace)


def test_el_periodo_anterior_dice_anterior_y_avisa(cliente, seccion_tutora, matematica):
    html = pagina(cliente, seccion_tutora, periodo="2")

    assert periodo_visible(html) == "B2 · Anterior"
    assert "Estás revisando un bimestre anterior" in html
    assert "Puedes corregirlo mientras el año esté abierto." in html


def test_el_vigente_no_lleva_aviso_de_periodo(cliente, seccion_tutora, matematica):
    html = pagina(cliente, seccion_tutora)

    assert "Estás revisando un bimestre anterior" not in html
    assert "Hoy no hay un periodo vigente" not in html


def test_en_vacaciones_avisa_y_abre_el_ultimo_anterior(cliente, seccion_tutora, matematica, hoy):
    hoy["valor"] = AGO_1

    html = pagina(cliente, seccion_tutora)

    assert "Hoy no hay un periodo vigente" in html
    assert periodo_visible(html) == "B2 · Anterior"
    assert 'id="guardar"' in html


# --- Tira de áreas ---


def test_la_tira_va_en_orden_siagie_con_el_area_inicial_presionada(
    cliente, seccion_tutora, matematica
):
    html = pagina(cliente, seccion_tutora)

    botones = pildoras(html)
    nombres = [texto(b) for b in botones]
    assert len(botones) == 10
    assert nombres[0].startswith("Arte y Cultura")
    assert nombres[6].startswith("Matemática")
    presionados = [b for b in botones if 'aria-pressed="true"' in b]
    assert len(presionados) == 1
    assert f'data-area-pildora="{COMUNICACION}"' in presionados[0]
    assert all('type="button"' in b for b in botones)


def test_el_area_pedida_abre_presionada(cliente, seccion_tutora, matematica):
    html = pagina(cliente, seccion_tutora, area=MATEMATICA)

    presionados = [b for b in pildoras(html) if 'aria-pressed="true"' in b]
    assert len(presionados) == 1
    assert f'data-area-pildora="{MATEMATICA}"' in presionados[0]


def test_las_areas_a_cargo_van_atenuadas(cliente, seccion_tutora, matematica):
    html = pagina(cliente, seccion_tutora)

    vistas = 0
    for boton in pildoras(html):
        if INGLES in boton.split("data-area-pildora=")[1][:8] or (
            EDUCACION_FISICA in boton.split("data-area-pildora=")[1][:8]
        ):
            assert "notas-pildora--curso" in boton
            assert 'aria-description="A cargo del docente de curso"' in boton
            vistas += 1
        elif f'data-area-pildora="{MATEMATICA}"' in boton:
            assert "notas-pildora--curso" not in boton
            assert "aria-description" not in boton
    assert vistas == 2


def test_la_tira_vive_en_su_propio_contenedor(cliente, seccion_tutora, matematica):
    html = pagina(cliente, seccion_tutora)

    assert re.search(r'<div class="notas-tira"[^>]*>\s*<div[^>]*data-tira', html)
    assert 'aria-label="Áreas del bimestre"' in html


def test_la_tira_trae_las_10_areas_tambien_las_sin_competencias(
    cliente, seccion_tutora, matematica
):
    html = pagina(cliente, seccion_tutora)

    assert f'data-area-pildora="{ARTE}"' in html


# --- Estructura de la hoja ---


def test_el_marco_de_la_hoja_y_la_barra_de_guardar(cliente, seccion_tutora, matematica):
    html = pagina(cliente, seccion_tutora)

    assert re.search(r'<button[^>]*id="guardar"[^>]*>Guardar</button>', html)
    assert 'aria-disabled="true"' in re.search(r'<button[^>]*id="guardar"[^>]*>', html).group(0)
    assert "data-superficie" in html
    assert re.search(r'<p[^>]*id="conteo-vivo"[^>]*aria-live="polite"', html)
    assert "data-borrador" in html


def test_el_dialogo_de_salida(cliente, seccion_tutora, matematica):
    html = pagina(cliente, seccion_tutora)

    dialogo = re.search(r'<dialog [^>]*id="confirmar-salida".*?</dialog>', html, re.DOTALL).group(0)
    assert "¿Salir sin guardar?" in dialogo
    assert re.search(r"<button[^>]*autofocus[^>]*>Seguir editando</button>", dialogo)
    assert "Salir sin guardar</button>" in dialogo
    assert 'aria-labelledby="titulo-salida"' in dialogo
    assert "data-areas-pendientes" in dialogo


def test_el_panel_del_celular_el_recuadro_y_el_relleno(cliente, seccion_tutora, matematica):
    html = pagina(cliente, seccion_tutora)

    assert re.search(r'<dialog [^>]*id="panel-editor"', html)
    assert 'id="nota-editor"' in html and 'id="conclusion-pc"' in html
    assert re.search(r'<dialog [^>]*id="confirmar-relleno"', html)
    assert 'role="listbox"' in html and 'id="lista-niveles"' in html
    assert 'role="tooltip"' in html


def test_las_regiones_del_lector_de_pantalla_y_el_noscript(cliente, seccion_tutora, matematica):
    html = pagina(cliente, seccion_tutora)

    assert re.search(r'<div[^>]*role="status"[^>]*data-anuncio', html)
    assert re.search(r'<div[^>]*role="alert"[^>]*data-alerta', html)
    assert "<noscript>" in html
    assert "Activa JavaScript para registrar las notas." in html


def test_el_json_script_y_el_script_de_la_hoja(cliente, seccion_tutora, matematica):
    html = pagina(cliente, seccion_tutora)

    assert '<script id="datos-notas" type="application/json">' in html
    assert "js/notas.js" in html


def test_sin_estilos_en_linea_ni_colores_hex(cliente, seccion_tutora, matematica):
    html = pagina(cliente, seccion_tutora)

    assert "style=" not in html
    assert not re.search(r"#[0-9a-fA-F]{6}\b", html)


# --- Estados sin hoja ---


def test_sin_periodos_solo_el_aviso(cliente, seccion_tutora, universo_ie):
    html = pagina(cliente, seccion_tutora)

    assert "La dirección aún no configura los periodos" in html
    assert 'id="guardar"' not in html
    assert "data-tira" not in html
    assert "datos-notas" not in html
    assert "notas.js" not in html
    assert "Activa JavaScript" not in html


def test_antes_del_primer_periodo_sin_hoja(cliente, seccion_tutora, ie, hoy):
    hoy["valor"] = MAR_2

    html = pagina(cliente, seccion_tutora)

    assert "Hoy no hay un periodo vigente" in html
    assert "El bimestre 1 empieza el 9 de marzo." in html
    assert 'id="guardar"' not in html
    assert "data-tira" not in html
