"""La plantilla de la hoja de notas (spec registro-notas; design de US-020, D9; rebrand-us-020).

El servidor dibuja el marco (encabezado, selector de periodo, tira de áreas con «Competencias»,
avisos, barra de guardar, diálogos, regiones del lector de pantalla y el ``json_script``);
``notas.js`` dibuja la rejilla (sus pruebas son las de punta a punta). Aquí se revisa el HTML. El
día se fija con el fixture ``hoy``.
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


def principal(html):
    """El contenido del único ``<main>`` (el del marco del rebrand)."""
    assert html.count("<main") == 1, "un solo <main>: el del marco"
    return re.search(r"<main\b.*?</main>", html, re.DOTALL).group(0)


def pildoras(html):
    return re.findall(r"<button [^>]*data-area-pildora=.*?</button>", html, re.DOTALL)


def selector(html):
    return re.search(r"<nav [^>]*data-selector-periodo.*?</nav>", html, re.DOTALL).group(0)


def periodos_del_selector(html):
    """Cada periodo del selector, un ``<li>``: un enlace si se elige, un ``<span>`` si es futuro."""
    items = re.findall(r"<li>(.*?)</li>", selector(html), re.DOTALL)
    return [item.strip() for item in items]


def sin_sr_only(fragmento):
    return re.sub(r'<span class="sr-only">.*?</span>', "", fragmento, flags=re.DOTALL)


def periodo_visible(html):
    """El texto visible del periodo marcado (las fechas van en ``sr-only``)."""
    actuales = [p for p in periodos_del_selector(html) if 'aria-current="page"' in p]
    assert len(actuales) == 1
    return texto(sin_sr_only(actuales[0]))


def dialogo(html, ident):
    return re.search(rf'<dialog [^>]*id="{ident}".*?</dialog>', html, re.DOTALL).group(0)


# --- Marco y encabezado (rebrand-us-020, D5) ---


def test_la_hoja_va_en_el_marco_del_rebrand(cliente, seccion_tutora, matematica):
    html = pagina(cliente, seccion_tutora)

    hojas = re.findall(r'<link rel="stylesheet" href="([^"]+)"', html)
    assert len(hojas) == 1 and hojas[0].endswith("dist/rebrand.css")
    assert "dist/app.css" not in html
    scripts = re.findall(r'<script src="([^"]+)"', principal(html))
    assert scripts == ["/static/js/notas.js"]
    assert 'data-dimension="notas"' in principal(html)
    assert '<span class="bar-title">Notas</span>' in html
    actuales = re.findall(r'<a [^>]*aria-current="page"[^>]*>.*?</a>', html, re.DOTALL)
    assert [texto(a) for a in actuales if "data-periodo" not in a] == ["Notas"]
    assert "<title>Notas · 2.º A · CarpetaDocente</title>" in html


def test_el_encabezado_lleva_la_seccion_y_el_titulo(cliente, seccion_tutora, matematica):
    contenido = principal(pagina(cliente, seccion_tutora))

    assert contenido.count("<h1") == 1
    assert "<h1>Registrar notas</h1>" in contenido
    assert '<p class="small">2.º grado, sección A · 2027</p>' in contenido


# --- Selector de periodo (delta «Periodo de la hoja»; D1) ---


def test_el_selector_marca_el_vigente(cliente, seccion_tutora, matematica):
    html = pagina(cliente, seccion_tutora)

    assert periodo_visible(html) == "III Vigente"
    assert 'aria-label="Bimestres de 2027"' in selector(html)


def test_cada_periodo_editable_es_un_enlace_a_su_hoja_en_el_area_inicial(
    cliente, seccion_tutora, matematica
):
    html = pagina(cliente, seccion_tutora, area=MATEMATICA)

    base = reverse("notas:hoja", args=[seccion_tutora.pk])
    periodos = periodos_del_selector(html)
    assert len(periodos) == 4
    for numero, enlace in enumerate(periodos[:3], start=1):
        assert enlace.startswith("<a ")
        assert f'data-periodo="{numero}"' in enlace
        assert f'href="{base}?periodo={numero}&amp;area={MATEMATICA}"' in enlace
    assert 'aria-current="page"' in periodos[2]
    assert all('aria-current="page"' not in p for p in periodos[:2])


def test_las_fechas_van_solo_en_el_nombre_accesible(cliente, seccion_tutora, matematica):
    tercero = periodos_del_selector(pagina(cliente, seccion_tutora))[2]

    assert "<strong>III</strong>" in tercero
    assert "Vigente" in texto(sin_sr_only(tercero))
    ocultos = " ".join(re.findall(r'<span class="sr-only">(.*?)</span>', tercero))
    assert "10 de agosto" in ocultos and "30 de octubre" in ocultos
    assert "agosto" not in sin_sr_only(tercero)


def test_el_futuro_no_se_elige(cliente, seccion_tutora, matematica):
    cuarto = periodos_del_selector(pagina(cliente, seccion_tutora))[3]

    assert cuarto.startswith("<span ")
    assert 'aria-disabled="true"' in cuarto
    assert "href" not in cuarto
    assert texto(sin_sr_only(cuarto)) == "IV Futuro"


def test_el_periodo_anterior_dice_anterior_y_avisa(cliente, seccion_tutora, matematica):
    html = pagina(cliente, seccion_tutora, periodo="2")

    assert periodo_visible(html) == "II Anterior"
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
    assert periodo_visible(html) == "II Anterior"
    assert 'id="guardar"' in html


# --- Tira de áreas (delta «Áreas de la hoja») ---


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
            assert "hn-pildora--curso" in boton
            assert 'aria-description="A cargo del docente de curso"' in boton
            vistas += 1
        elif f'data-area-pildora="{MATEMATICA}"' in boton:
            assert "hn-pildora--curso" not in boton
            assert "aria-description" not in boton
    assert vistas == 2


def test_la_tira_vive_en_su_propio_contenedor_y_competencias_queda_fuera(
    cliente, seccion_tutora, matematica
):
    """Escenario «Área activa a la vista»: el acceso a Competencias queda fijo fuera del tramo que
    se desplaza."""
    html = pagina(cliente, seccion_tutora)

    nav = re.search(r'<nav [^>]*aria-label="Áreas del bimestre".*?</nav>', html, re.DOTALL)
    tira = re.search(r"<div [^>]*data-tira[^>]*>.*?</div>", nav.group(0), re.DOTALL).group(0)
    assert "data-area-pildora" in tira
    assert "data-ir-competencias" not in tira
    assert "data-ir-competencias" in nav.group(0)


def test_el_acceso_a_competencias_lleva_el_periodo_y_el_area(cliente, seccion_tutora, matematica):
    html = pagina(cliente, seccion_tutora, periodo="2", area=COMUNICACION)

    enlace = re.search(r"<a [^>]*data-ir-competencias[^>]*>.*?</a>", html, re.DOTALL).group(0)
    base = reverse("competencias:pantalla", args=[seccion_tutora.pk])
    assert f'href="{base}?periodo=2&amp;area={COMUNICACION}"' in enlace
    assert texto(enlace) == "Competencias"
    assert "M11 6h9" in enlace or "<svg" in enlace


def test_la_tira_trae_las_10_areas_tambien_las_sin_competencias(
    cliente, seccion_tutora, matematica
):
    html = pagina(cliente, seccion_tutora)

    assert f'data-area-pildora="{ARTE}"' in html


# --- Estructura de la hoja (D5): los ganchos que lee notas.js ---


IDS_DE_NOTAS_JS = (
    "hoja",
    "titulo-area",
    "detalle-hoja",
    "ver-todos",
    "rellenar-movil",
    "ayuda-teclas",
    "borrador",
    "mensaje-guardado",
    "superficie-hoja",
    "barra-guardar",
    "cierre-area",
    "estado-guardado",
    "separador-estado",
    "faltantes",
    "sin-faltantes",
    "no-validos",
    "texto-no-validos",
    "alcance",
    "faltantes-ayuda",
    "conteo-vivo",
    "guardar",
    "pie-hoja",
    "lista-niveles",
    "panel-editor",
    "panel-posicion",
    "panel-estudiante",
    "cerrar-panel",
    "panel-competencia",
    "panel-niveles",
    "panel-conclusion",
    "conclusion-movil",
    "contador-movil",
    "ayuda-conclusion",
    "panel-rechazo",
    "siguiente",
    "confirmar-relleno",
    "titulo-relleno",
    "texto-relleno",
    "columna-relleno",
    "elegir-columna",
    "aplicar-relleno",
    "cancelar-relleno",
    "confirmar-salida",
    "titulo-salida",
    "texto-salida",
    "areas-pendientes",
    "aviso-borradores",
    "seguir-editando",
    "salir-sin-guardar",
    "competencia-detalle",
    "nota-editor",
    "nota-titulo",
    "nota-contexto",
    "cerrar-nota",
    "conclusion-pc",
    "ayuda-nota",
    "contador-nota",
    "listo-nota",
)


def test_siguen_los_id_y_data_que_lee_notas_js(cliente, seccion_tutora, matematica):
    html = pagina(cliente, seccion_tutora)

    for ident in IDS_DE_NOTAS_JS:
        assert html.count(f'id="{ident}"') == 1, ident
    for gancho in (
        "data-trabajo",
        "data-tira",
        "data-superficie",
        "data-borrador",
        "data-rango",
        "data-panel-borrador",
        "data-ir-competencias",
        "data-areas-pendientes",
        "data-iconos",
        "data-anuncio",
        "data-alerta",
    ):
        assert gancho in html, gancho


def test_la_barra_de_guardar_queda_fuera_de_la_hoja(cliente, seccion_tutora, matematica):
    html = pagina(cliente, seccion_tutora)

    hoja = re.search(r'<section id="hoja".*?</section>', html, re.DOTALL).group(0)
    assert 'id="barra-guardar"' not in hoja
    assert re.search(r'<button[^>]*id="guardar"[^>]*>Guardar</button>', html)
    assert 'aria-disabled="true"' in re.search(r'<button[^>]*id="guardar"[^>]*>', html).group(0)
    assert re.search(r'<p[^>]*id="conteo-vivo"[^>]*aria-live="polite"', html)


def test_la_leyenda_va_bajo_la_hoja(cliente, seccion_tutora, matematica):
    html = pagina(cliente, seccion_tutora)

    assert html.index('<section id="hoja"') < html.index('id="pie-hoja"')
    pie = re.search(r'<div [^>]*id="pie-hoja".*?</div>', html, re.DOTALL).group(0)
    assert "B y C llevan conclusión, de 10 a 500 caracteres." in texto(pie)
    assert "Cambio sin guardar" in texto(pie)


def test_rellenar_vacias_es_un_solo_boton_en_todos_los_anchos(cliente, seccion_tutora, matematica):
    boton = re.search(r'<button [^>]*id="rellenar-movil"[^>]*>', pagina(cliente, seccion_tutora))

    assert "solo-celular" not in boton.group(0)
    assert "btn--secondary" in boton.group(0)


def test_el_dialogo_de_relleno_es_el_del_rebrand(cliente, seccion_tutora, matematica):
    relleno = dialogo(pagina(cliente, seccion_tutora), "confirmar-relleno")

    assert 'class="dialog dialog--chico"' in relleno
    assert 'aria-labelledby="titulo-relleno"' in relleno
    assert 'aria-describedby="texto-relleno"' in relleno
    assert re.search(r'<h2 id="titulo-relleno"[^>]*>Rellenar vacías</h2>', relleno)
    assert relleno.index('id="aplicar-relleno"') < relleno.index('id="cancelar-relleno"')
    assert re.search(r'<button[^>]*id="cancelar-relleno"[^>]*autofocus', relleno)
    assert relleno.count('type="radio"') == 2
    assert 'value="AD"' in relleno and 'value="A" checked' in relleno


def test_el_dialogo_de_salida(cliente, seccion_tutora, matematica):
    salida = dialogo(pagina(cliente, seccion_tutora), "confirmar-salida")

    assert 'class="dialog dialog--chico"' in salida
    assert "¿Salir sin guardar?" in salida
    assert re.search(r"<button[^>]*autofocus[^>]*>Seguir editando</button>", salida)
    assert salida.index("Seguir editando") < salida.index("Salir sin guardar</button>")
    assert 'aria-labelledby="titulo-salida"' in salida
    assert 'aria-describedby="texto-salida"' in salida
    assert "data-areas-pendientes" in salida
    assert "Los borradores quedan en este dispositivo." in salida


def test_el_panel_del_celular_el_recuadro_y_la_lista(cliente, seccion_tutora, matematica):
    html = pagina(cliente, seccion_tutora)

    assert re.search(r'<dialog [^>]*id="panel-editor"', html)
    assert 'id="nota-editor"' in html and 'id="conclusion-pc"' in html
    assert 'role="listbox"' in html and 'id="lista-niveles"' in html
    assert re.search(r'<div id="competencia-detalle"[^>]*role="tooltip"', html)
    assert re.search(r'<div id="nota-previa"[^>]*role="tooltip"[^>]*hidden', html)


def test_las_regiones_del_lector_de_pantalla_y_el_noscript(cliente, seccion_tutora, matematica):
    html = pagina(cliente, seccion_tutora)

    assert re.search(r'<div[^>]*role="status"[^>]*data-anuncio', html)
    assert re.search(r'<div[^>]*role="alert"[^>]*data-alerta', html)
    noscript = re.search(r"<noscript>.*?</noscript>", html, re.DOTALL).group(0)
    assert 'class="message message--aviso"' in noscript
    assert "Activa JavaScript para registrar las notas." in noscript


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
    assert "data-selector-periodo" not in html
    assert 'id="guardar"' not in html
    assert "data-tira" not in html
    assert "datos-notas" not in html
    assert "notas.js" not in html
    assert "Activa JavaScript" not in html


def test_antes_del_primer_periodo_sin_hoja(cliente, seccion_tutora, ie, hoy):
    hoy["valor"] = MAR_2

    html = pagina(cliente, seccion_tutora)

    assert "Hoy no hay un periodo vigente" in html
    assert "El I bimestre empieza el 9 de marzo." in html
    assert 'class="message message--aviso"' in html
    assert 'id="guardar"' not in html
    assert "data-tira" not in html
