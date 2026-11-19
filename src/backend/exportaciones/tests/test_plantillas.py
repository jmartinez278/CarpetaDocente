"""Textos y marcado de las pantallas de completar la plantilla del SIAGIE (US-024/025, D10).

Specs «Diálogo “Sube la plantilla del SIAGIE”», «Sección de la plantilla» (el paso «Elige la
sección»), «Resumen del llenado» y «Corregir la equivalencia». Se renderizan las plantillas con un
contexto armado a mano, sin base de datos: las reglas de negocio ya las prueban
``test_servicios_*`` y ``test_vistas``. Todos los nombres son ficticios.
"""

import re
from pathlib import Path
from types import SimpleNamespace

import pytest
from django.template.loader import render_to_string

RAIZ = Path(__file__).resolve().parents[2]
PLANTILLAS = RAIZ / "templates"
ARCHIVOS_DE_LA_PANTALLA = [
    "exportaciones/_dialogo.html",
    "exportaciones/_dialogo_cuerpo.html",
    "exportaciones/_dialogo_pie.html",
    "exportaciones/_seccion.html",
    "exportaciones/_resumen.html",
    "exportaciones/_equivalencia_borrada.html",
]

NOMBRE_LARGO = "DEL BOSQUE DE TIZA Y DE LOS MAPAS DEL AULA DE PAPEL, ELUNIA MARISOL"


def texto(html):
    """El texto visible, sin etiquetas y con los espacios colapsados."""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()


def etiqueta(html, nombre, atributo):
    """El elemento ``<nombre ...>`` que lleva ``atributo`` (cadena o expresión regular)."""
    encontrada = re.search(rf"<(?:{nombre})\b[^>]*{atributo}[^>]*>", html)
    assert encontrada, f"no hay <{nombre}> con {atributo}"
    return encontrada.group(0)


# --- Diálogo «Sube la plantilla del SIAGIE» ---


@pytest.fixture
def dialogo(rf):
    return render_to_string("exportaciones/_dialogo.html", request=rf.get("/direccion/"))


def test_el_dialogo_tiene_su_titulo_y_su_ayuda(dialogo):
    assert re.search(r"<h2\b[^>]*>Sube la plantilla del SIAGIE</h2>", dialogo)
    assert "Sube una plantilla de notas en Excel (.xlsx) por sección." in texto(dialogo)
    # El título recibe el foco al abrir (por eso tabindex="-1") y nombra al diálogo.
    assert 'tabindex="-1"' in etiqueta(dialogo, "h2", 'id="plantilla-titulo"')
    abierto = etiqueta(dialogo, "dialog", "plantilla-siagie")
    assert 'aria-labelledby="plantilla-titulo"' in abierto
    assert "dialog--hoja" in abierto


def test_el_campo_archivo_solo_acepta_excel_y_trae_la_ruta_del_siagie(dialogo):
    entrada = etiqueta(dialogo, "input", 'type="file"')
    assert 'name="archivo"' in entrada
    assert ".xlsx" in entrada
    assert re.search(r'<label\b[^>]*for="archivo"[^>]*>\s*Archivo\s*</label>', dialogo)
    assert "Aún no has elegido un archivo" in texto(dialogo)
    assert "En el SIAGIE, ve a Evaluación → Registro de calificaciones → Periodo por Excel" in (
        texto(dialogo)
    )


def test_completar_plantilla_empieza_deshabilitado_y_cancelar_no_envia(dialogo):
    completar = etiqueta(dialogo, "button", "data-enviar")
    assert "disabled" in completar
    assert 'type="submit"' in completar
    assert re.search(r"<button\b[^>]*data-enviar[^>]*>\s*Completar plantilla\s*</button>", dialogo)
    cancelar = etiqueta(dialogo, "button", "data-cancelar")
    assert 'type="button"' in cancelar
    assert re.search(r"<button\b[^>]*data-cancelar[^>]*>\s*Cancelar\s*</button>", dialogo)


def test_el_error_del_archivo_nace_oculto_y_se_anuncia(dialogo):
    error = etiqueta(dialogo, "div", 'id="archivo-error"')
    assert "hidden" in error
    assert 'role="alert"' in error
    assert 'tabindex="-1"' in error
    entrada = etiqueta(dialogo, "input", 'type="file"')
    assert "archivo-error" in entrada


def test_el_avance_nace_oculto_y_se_anuncia_al_lector(dialogo):
    avance = etiqueta(dialogo, "div", "data-progreso")
    assert "hidden" in avance
    assert 'role="status"' in etiqueta(dialogo, "p", "data-progreso-texto")
    assert "Procesando la plantilla…" in texto(dialogo)
    assert "aria-label" in etiqueta(dialogo, "progress", "data-barra")


def test_el_corte_de_red_tiene_su_mensaje_y_nace_oculto(dialogo):
    corte = etiqueta(dialogo, "div", "data-error-red")
    assert "hidden" in corte
    assert (
        "Se cortó la conexión. Tu archivo sigue aquí: "
        "revisa tu conexión e inténtalo de nuevo." in texto(dialogo)
    )


def test_el_formulario_lleva_el_csrf_de_la_sesion(dialogo):
    formulario = re.search(r"<form\b.*?</form>", dialogo, re.DOTALL).group(0)
    assert 'name="csrfmiddlewaretoken"' in formulario
    assert 'enctype="multipart/form-data"' in formulario
    assert 'action="/direccion/plantilla-siagie/"' in formulario


# --- Paso «Elige la sección» ---


class Opcion(SimpleNamespace):
    pass


@pytest.fixture
def seccion_html():
    opciones = [Opcion(pk=pk, grado=2, nombre=nombre) for pk, nombre in enumerate("ABCD", start=11)]
    return render_to_string(
        "exportaciones/_seccion.html",
        {
            "grado": 2,
            "nombre_siagie": "TRIUNFADORES",
            "periodo_texto": "Tercer bimestre 2026",
            "opciones": opciones,
        },
    )


def test_el_paso_de_la_seccion_se_anuncia_y_lleva_su_titulo(seccion_html):
    assert 'data-paso="seccion"' in etiqueta(seccion_html, "form|div", "data-paso")
    titulo = etiqueta(seccion_html, "h2", 'id="plantilla-seccion-titulo"')
    assert 'tabindex="-1"' in titulo
    assert re.search(r"<h2\b[^>]*>Elige la sección</h2>", seccion_html)


def test_la_tarjeta_muestra_la_seccion_y_el_periodo_de_la_plantilla(seccion_html):
    assert "Sección en la plantilla del SIAGIE" in texto(seccion_html)
    assert "2.º TRIUNFADORES · Tercer bimestre 2026" in texto(seccion_html)


def test_una_opcion_por_seccion_y_ninguna_marcada(seccion_html):
    radios = re.findall(r'<input\b[^>]*type="radio"[^>]*>', seccion_html)
    assert [re.search(r'value="(\d+)"', r).group(1) for r in radios] == ["11", "12", "13", "14"]
    assert all('name="seccion"' in r for r in radios)
    assert not any("checked" in r for r in radios)
    for nombre in ("2.º A", "2.º B", "2.º C", "2.º D"):
        assert nombre in texto(seccion_html)
    assert re.search(r"<legend\b[^>]*>Sección de tu I\.E\.</legend>", seccion_html)


def test_la_ayuda_dice_para_que_se_guarda_la_equivalencia(seccion_html):
    assert (
        "Guardaremos esta equivalencia para las próximas plantillas de 2.º TRIUNFADORES."
        in texto(seccion_html)
    )


def test_guardar_y_completar_empieza_deshabilitado_junto_a_cancelar(seccion_html):
    guardar = etiqueta(seccion_html, "button", "data-enviar")
    assert "disabled" in guardar
    assert 'type="submit"' in guardar
    assert re.search(
        r"<button\b[^>]*data-enviar[^>]*>\s*Guardar y completar\s*</button>", seccion_html
    )
    assert re.search(r"<button\b[^>]*data-cancelar[^>]*>\s*Cancelar\s*</button>", seccion_html)


def test_el_paso_de_la_seccion_trae_su_error_y_su_avance_ocultos(seccion_html):
    assert "hidden" in etiqueta(seccion_html, "div", "data-error-paso")
    assert "hidden" in etiqueta(seccion_html, "div", "data-progreso")


# --- Resumen del llenado ---


def resumen(**cambios):
    datos = {
        "titulo": "Plantilla completada con observaciones",
        "seccion": SimpleNamespace(grado=2, nombre="B"),
        "grado_siagie": 2,
        "nombre_siagie": "TRIUNFADORES",
        "encontrados": 26,
        "no_encontrados": ["DE LA LOMA DE PAPEL, AMARANTA LUZ", NOMBRE_LARGO],
        "faltantes": 3,
        "reemplazadas": 4,
        "equivalencia_id": 7,
    }
    datos.update(cambios)
    return SimpleNamespace(**datos)


def pintar(rf, **cambios):
    return render_to_string(
        "exportaciones/_resumen.html",
        {
            "resumen": resumen(**cambios),
            "archivo_base64": "UEsDBA==",
            "nombre_archivo": "RegNotas_2_TRIUNFADORES_B3.xlsx",
            "periodo_texto": "Bimestre 3 · 2026",
        },
        request=rf.get("/direccion/"),
    )


def conteos(html):
    """El texto de cada uno de los cuatro conteos de «Resultado del llenado», en su orden."""
    lista = re.search(r'<ul class="resumen-metricas"[^>]*>(.*?)</ul>', html, re.DOTALL)
    assert lista, "no hay lista de conteos"
    return [texto(li) for li in re.findall(r"<li>(.*?)</li>", lista.group(1), re.DOTALL)]


def test_el_resumen_con_observaciones_trae_su_cabecera(rf):
    html = pintar(rf)

    assert re.search(r"<h1\b[^>]*>Plantilla completada con observaciones</h1>", html)
    assert 'tabindex="-1"' in etiqueta(html, "h1", "")
    assert 'data-paso="resumen"' in html
    assert re.search(r'<a\b[^>]*href="/direccion/"[^>]*>.*?Inicio de dirección', html, re.DOTALL)
    assert "Sección de la I.E. 2.º B · Bimestre 3 · 2026" in texto(html)
    assert "Sección en el SIAGIE 2.º TRIUNFADORES" in texto(html)


def test_los_cuatro_conteos_con_observaciones(rf):
    html = pintar(rf)

    assert re.search(r"<h2\b[^>]*>Resultado del llenado</h2>", html)
    assert conteos(html) == [
        "26 estudiantes encontrados",
        "2 no encontrados",
        "Faltan 3 notas",
        "4 celdas reemplazadas",
    ]


def test_la_lista_de_no_encontrados_con_su_aviso(rf):
    html = pintar(rf)

    assert re.search(r"<h3\b[^>]*>.*?Estudiantes no encontrados</h3>", html, re.DOTALL)
    assert "Sus filas quedaron intactas en la plantilla." in texto(html)
    nombres = re.findall(r"<li>([^<]+)</li>", html)
    assert "DE LA LOMA DE PAPEL, AMARANTA LUZ" in nombres
    assert NOMBRE_LARGO in nombres


def test_el_resumen_sin_observaciones_muestra_los_conteos_en_cero_y_sin_lista(rf):
    html = pintar(
        rf,
        titulo="Plantilla completada",
        encontrados=28,
        no_encontrados=[],
        faltantes=0,
        reemplazadas=0,
    )

    assert re.search(r"<h1\b[^>]*>Plantilla completada</h1>", html)
    assert conteos(html) == [
        "28 estudiantes encontrados",
        "0 no encontrados",
        "Faltan 0 notas",
        "0 celdas reemplazadas",
    ]
    assert "Estudiantes no encontrados" not in html
    assert "Sus filas quedaron intactas" not in html
    assert '<ul class="lista-nombres"' not in html


def test_el_archivo_de_salida_descarga_con_el_nombre_original(rf):
    html = pintar(rf)

    assert re.search(r"<h2\b[^>]*>Archivo de salida</h2>", html)
    assert "Plantilla de notas del SIAGIE (.xlsx)" in texto(html)
    descarga = etiqueta(html, "a", "data-archivo=")
    assert 'data-archivo="UEsDBA=="' in descarga
    assert 'download="RegNotas_2_TRIUNFADORES_B3.xlsx"' in descarga
    assert "Descargar plantilla" in texto(html)
    otra = etiqueta(html, "button", "data-subir-otra")
    assert 'type="button"' in otra
    assert "Subir otra plantilla" in texto(html)


def test_no_es_esta_seccion_solo_aparece_con_equivalencia(rf):
    con = pintar(rf, equivalencia_id=7)
    sin = pintar(rf, equivalencia_id=None)

    assert "¿No es esta sección?" in texto(con)
    formulario = etiqueta(con, "form", "data-borrar-equivalencia")
    assert 'action="/direccion/plantilla-siagie/equivalencias/7/borrar/"' in formulario
    assert 'method="post"' in formulario
    assert "csrfmiddlewaretoken" in con
    assert "¿No es esta sección?" not in texto(sin)
    assert "data-borrar-equivalencia" not in sin


def test_los_nombres_no_encontrados_se_escapan(rf):
    html = pintar(rf, no_encontrados=["<img src=x onerror=alert(1)>, X"])

    assert "&lt;img src=x onerror=alert(1)&gt;, X" in html
    assert "<img src=x" not in html


# --- Panel tras corregir la equivalencia ---


def test_el_panel_corregido_ofrece_subir_otra_vez_sin_descarga(rf):
    html = render_to_string(
        "exportaciones/_equivalencia_borrada.html", {"grado": 2, "nombre_siagie": "TRIUNFADORES"}
    )

    assert (
        "Quitamos la equivalencia. "
        "La próxima plantilla de 2.º TRIUNFADORES te pedirá elegir la sección." in texto(html)
    )
    assert "data-panel-archivo" in html
    assert re.search(
        r"<button\b[^>]*data-subir-otra[^>]*>\s*Subir plantilla otra vez\s*</button>", html
    )
    assert "Descargar plantilla" not in html


# --- Reglas de plantillas: sin estilos en línea ni colores hex ---


@pytest.mark.parametrize("nombre", ARCHIVOS_DE_LA_PANTALLA + ["direccion/inicio.html"])
def test_las_plantillas_no_llevan_style_ni_colores_hex(nombre):
    fuente = (PLANTILLAS / nombre).read_text(encoding="utf-8")

    assert "style=" not in fuente
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b(?![\w-])", re.sub(r'href="#[^"]*"', "", fuente))
