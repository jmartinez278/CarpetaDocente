"""La plantilla de Sesiones (spec envio-sesiones; design de US-010, US-014 y EN-03, D8 y D9).

El servidor dibuja la pantalla, el popup «Subir una sesión» y el de los términos; ``sesiones.js``
los abre, valida y envía (sus pruebas son las de punta a punta). Aquí se revisa el HTML.
"""

import re
import uuid
from pathlib import Path

import pytest

from institucion.models import Seccion
from repositorio.models import TIPO_DOCX
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


def principal(html):
    """El contenido del único ``<main>`` (el del marco del rebrand)."""
    assert html.count("<main") == 1, "un solo <main>: el del marco"
    return re.search(r"<main\b.*?</main>", html, re.DOTALL).group(0)


def menu_navegacion(html):
    """El diálogo del ☰ (el primero de la página, antes del <main>)."""
    return re.search(
        r'<dialog\b[^>]*aria-labelledby="navegacion-titulo".*?</dialog>', html, re.DOTALL
    ).group(0)


def test_la_pantalla_carga_solo_la_hoja_del_rebrand(cliente):
    html = pagina(cliente)

    assert "dist/app.css" in html
    assert "dist/rebrand.css" not in html


def test_la_barra_dice_sesiones_y_el_menu_marca_sesiones_como_la_actual(cliente):
    """Escenarios «Primera visita» (barra) y «Ubicación actual en Sesiones» (US-011, D3)."""
    html = pagina(cliente)

    assert re.search(r'<span class="bar-title">Sesiones</span>', html)
    menu = menu_navegacion(html)
    sesiones = re.search(r"<li\b(?:(?!</li>).)*Sesiones(?:(?!</li>).)*</li>", menu, re.DOTALL)
    assert sesiones and "Próximamente" not in sesiones.group(0)
    assert 'href="/docente/sesiones/"' in sesiones.group(0)
    assert menu.count("aria-current") == 1 and "aria-current" in sesiones.group(0)


def test_la_cabecera_tiene_titulo_y_boton_sin_subtitulo_ni_icono_de_titulo_ni_franjas(cliente):
    """Escenarios «Primera visita», «Cabecera sin ícono ni franjas» y «Botón en el celular»."""
    contenido = principal(pagina(cliente))

    assert "<h1>Sesiones</h1>" in contenido
    assert "franjas-cabecera" not in contenido
    assert "Planificación de sesiones de aprendizaje" not in contenido
    boton = elemento(contenido, r"button[^>]*data-abrir-subir")
    assert 'type="button"' in boton
    assert "btn--primary" in boton
    assert 'aria-label="Subir una sesión"' in boton
    cuerpo = re.search(r"<button[^>]*data-abrir-subir[^>]*>(.*?)</button>", contenido, re.DOTALL)
    interior = cuerpo.group(1)
    assert '<span class="subir-largo">Subir una sesión</span>' in interior
    assert '<span class="subir-corto" aria-hidden="true">Subir</span>' in interior
    assert "<svg" in interior and interior.index("<svg") < interior.index("subir-largo")


def test_la_marca_de_sesiones_va_dentro_del_main_del_marco(cliente):
    contenido = principal(pagina(cliente))

    assert re.search(r'<main id="contenido"', contenido)
    assert 'data-dimension="sesiones"' in contenido


def test_el_estado_vacio_y_la_region_del_resultado(cliente):
    contenido = principal(pagina(cliente))

    vacio = re.search(r'<div class="empty">.*?</div>', contenido, re.DOTALL)
    assert vacio, "el estado vacío del rebrand"
    assert "Aquí verás las sesiones que envíes y su estado." in vacio.group(0)
    assert 'aria-hidden="true"' in vacio.group(0)
    region = elemento(contenido, r"section[^>]*data-resultado")
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
    assert 'class="dialog dialog--hoja"' in apertura
    assert " open" not in apertura
    assert 'aria-labelledby="subir-titulo"' in apertura
    assert 'aria-describedby="subir-descripcion"' in apertura
    assert re.search(
        r'<h2[^>]*id="subir-titulo"[^>]*tabindex="-1"[^>]*>Subir una sesión</h2>', subir
    )
    assert re.search(r'id="subir-descripcion"[^>]*>Se enviará a la dirección\.</p>', subir)


def test_el_cuerpo_del_popup_se_alcanza_con_el_teclado(cliente):
    subir = bloque(pagina(cliente), "dialog", "subir")

    cuerpo = elemento(subir, r"div[^>]*data-cuerpo")
    assert 'tabindex="0"' in cuerpo
    assert 'role="region"' in cuerpo
    assert 'aria-labelledby="subir-titulo"' in cuerpo


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
    assert re.search(rf'<p class="field-error"[^>]*id="{campo}-error"[^>]*hidden', subir)
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
    assert re.search(r'for="proposito"[^>]*>Propósito <span class="muted">\(opcional\)', subir)


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

    aviso = elemento(subir, r'div class="message message--error"[^>]*data-error-red')
    assert "hidden" in aviso
    assert 'role="alert"' in aviso
    assert "Se cortó la conexión" in subir
    assert (
        "Tus datos y tu archivo siguen aquí. Revisa tu conexión e intenta enviar de nuevo." in subir
    )


def test_el_pie_tiene_el_avance_y_los_botones_en_su_orden(cliente):
    subir = bloque(pagina(cliente), "dialog", "subir")

    barra = elemento(subir, "progress")
    assert 'max="100"' in barra
    assert "aria-label=" in barra
    acciones = re.search(r'<div class="dialog-pie">(.*?)</dialog>', subir, re.DOTALL).group(1)
    enviar = acciones.index("Enviar a la dirección")
    cancelar = acciones.index("Cancelar")
    assert enviar < cancelar, "en el celular «Enviar» va arriba; en la PC, el CSS lo invierte"
    assert 'form="formulario-sesion"' in elemento(acciones, r'button[^>]*type="submit"')


def test_el_pie_tiene_un_solo_boton_enviar_principal_con_sus_ganchos(cliente):
    """Caracterización del pie al pasar a ``rb/boton.html`` (rebrand-cierre, decisión 6)."""
    subir = bloque(pagina(cliente), "dialog", "subir")
    acciones = re.search(r'<div class="dialog-pie">(.*?)</dialog>', subir, re.DOTALL).group(1)

    botones = re.findall(r"<button\b[^>]*>[^<]*Enviar a la dirección", acciones)
    assert len(botones) == 1
    boton = botones[0]
    assert re.search(r'class="btn btn--primary"', boton)
    assert 'type="submit"' in boton
    assert 'form="formulario-sesion"' in boton
    assert "data-enviar" in boton


def test_el_error_general_tiene_su_primer_parrafo_vacio(cliente):
    """sesiones.js escribe el error general en el primer <p> de [data-error-general]."""
    subir = bloque(pagina(cliente), "dialog", "subir")

    general = re.search(r"<div[^>]*data-error-general[^>]*>(.*?)</div></div>", subir, re.DOTALL)
    assert general and 'role="alert"' in general.group(0) and "hidden" in general.group(0)
    primero = re.search(r"<p\b[^>]*>(.*?)</p>", general.group(1), re.DOTALL)
    assert primero.group(1) == ""


@pytest.mark.parametrize("dialogo", ["subir", "terminos"])
def test_los_popups_no_llevan_boton_de_cerrar(cliente, dialogo):
    """Se cierran con «Cancelar», «Volver» o Esc (rebrand-us-010, D2)."""
    html = bloque(pagina(cliente), "dialog", dialogo)

    assert "data-cerrar" not in html
    assert "Cerrar" not in html
    assert "✕" not in html


def test_la_pagina_conserva_los_ganchos_de_sesiones_js(cliente):
    """decisiones.md, «Se conserva»: los data-* que usa sesiones.js."""
    html = pagina(cliente)

    for gancho in (
        "abrir-subir", "aceptar", "archivo-accion", "archivo-control", "archivo-detalle",
        "archivo-nombre", "barra", "campos", "cancelar", "cuerpo", "dimension", "enviar",
        "error-general", "error-red", "progreso", "progreso-texto", "resultado", "volver",
    ):  # fmt: skip
        assert re.search(rf"\sdata-{gancho}[\s=>]", html), f"falta data-{gancho}"


def test_hay_una_region_aria_live_para_el_avance(cliente):
    region = elemento(pagina(cliente), r'div[^>]*id="anuncio"')

    assert 'aria-live="polite"' in region
    assert "sr-only" in region


# --- Términos (4a) ---


def test_los_terminos_van_en_su_propio_popup_con_titulo_y_descripcion(cliente):
    terminos = bloque(pagina(cliente), "dialog", "terminos")

    apertura = elemento(terminos, 'dialog[^>]*id="terminos"')
    assert 'class="dialog dialog--chico"' in apertura
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
    cuerpo = elemento(terminos, r"div[^>]*data-cuerpo")
    assert 'tabindex="0"' in cuerpo and 'role="region"' in cuerpo
    pie = re.search(r'<div class="dialog-pie">(.*?)</dialog>', terminos, re.DOTALL).group(1)
    assert pie.index("Acepto y envío") < pie.index("Volver")


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
    assert 'class="message message--exito"' in html
    assert "btn--primary" in elemento(html, r"button[^>]*data-subir-otra")


# --- Pestañas, listas y página de la sesión (US-011, US-012 y US-016; tarea 5.2) ---

URL_REPOSITORIO = "/docente/sesiones/repositorio/"
BOTON_FILTRAR = r'<button [^>]*aria-controls="filtros"[^>]*>.*?</button>'


def repositorio(cliente, **consulta):
    respuesta = cliente.get(URL_REPOSITORIO, consulta)
    assert respuesta.status_code == 200
    return principal(respuesta.content.decode())


def detalle(cliente, sesion, estado=200):
    respuesta = cliente.get(f"{URL_INICIO}{sesion.pk}/")
    assert respuesta.status_code == estado
    return principal(respuesta.content.decode())


def texto_plano(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()


def tarjetas_de(html):
    return re.findall(r'<li class="sesion-tarjeta">.*?</li>', html, re.DOTALL)


def pestanas(html):
    nav = re.search(r'<nav\b[^>]*id="pestanas".*?</nav>', html, re.DOTALL)
    assert nav, "la pantalla tiene las pestañas"
    return nav.group(0)


def colega(n):
    from cuentas.models import Usuario
    from institucion.models import Institucion

    return Usuario.objects.create_user(
        username=f"colega{n}",
        password="x",  # noqa: S106 - cuenta ficticia de la prueba
        rol=Usuario.Rol.DOCENTE,
        institucion=Institucion.objects.get(),
    )


def test_las_pestanas_son_enlaces_de_un_tablist_con_sus_contadores(
    cliente, crear_sesion, docente, otra_docente
):
    """Escenarios «Contadores» y «Cambiar de pestaña»."""
    crear_sesion(docente)
    crear_sesion(docente, compartida=True)
    crear_sesion(otra_docente, compartida=True)

    nav = pestanas(principal(pagina(cliente)))

    assert 'role="tablist"' in nav
    mis, repo = re.findall(r'<a\b[^>]*role="tab"[^>]*>.*?</a>', nav, re.DOTALL)
    assert 'href="/docente/sesiones/"' in mis and 'aria-selected="true"' in mis
    assert texto_plano(mis) == "Mis sesiones 2"
    assert 'href="/docente/sesiones/repositorio/"' in repo and 'aria-selected="false"' in repo
    assert texto_plano(repo) == "Repositorio 2"
    assert 'id="pestana-mis_sesiones"' in mis and 'id="pestana-repositorio"' in repo


def test_en_el_repositorio_la_pestana_actual_es_la_del_repositorio(cliente):
    html = repositorio(cliente)

    mis, repo = re.findall(r'<a\b[^>]*role="tab"[^>]*>', pestanas(html))
    assert 'aria-selected="false"' in mis and 'aria-selected="true"' in repo
    assert 'role="tabpanel"' in html


def test_solo_la_pestana_actual_entra_al_orden_del_tabulador(cliente):
    """Pestañas con flechas: tabindex=-1 en la que no es la actual (patrón de tablist)."""
    mis, repo = re.findall(r'<a\b[^>]*role="tab"[^>]*>', pestanas(principal(pagina(cliente))))

    assert 'tabindex="-1"' not in mis
    assert 'tabindex="-1"' in repo


def test_la_tarjeta_es_un_solo_enlace_con_la_hoja_dibujada_oculta_al_lector(
    cliente, crear_sesion, docente
):
    """Escenarios «Con texto» y «Nombre accesible»."""
    crear_sesion(
        docente,
        titulo="Leemos un cuento sobre la amistad",
        texto="SESIÓN DE APRENDIZAJE\nI. DATOS INFORMATIVOS",
    )

    tarjeta = tarjetas_de(principal(pagina(cliente)))[0]

    assert tarjeta.count("<a ") == 1 and "<button" not in tarjeta
    assert "aria-label" not in tarjeta, "el nombre sale del contenido visible (axe)"
    assert (
        '<span class="sr-only">Abrir </span>'
        '<span class="sesion-titulo">Leemos un cuento sobre la amistad</span>'
    ) in tarjeta
    hoja = re.search(
        r'<span class="sesion-hoja"[^>]*aria-hidden="true">.*?</span></span>', tarjeta, re.DOTALL
    )
    assert hoja and "I. DATOS INFORMATIVOS" in hoja.group(0)
    assert re.search(r'<span class="sesion-tipo"[^>]*>PDF</span>', tarjeta)
    assert "2.º grado · Comunicación" in texto_plano(tarjeta)
    assert "descargar" not in tarjeta.lower()


def test_la_etiqueta_de_una_sesion_en_word_dice_word(cliente, crear_sesion, docente):
    crear_sesion(docente, titulo="Pdf")
    crear_sesion(docente, titulo="Word", tipo_mime=TIPO_DOCX)

    html = principal(pagina(cliente))
    etiquetas = re.findall(r'<span class="sesion-tipo"[^>]*>([^<]*)</span>', html)

    assert sorted(etiquetas) == ["PDF", "Word"]


def test_sin_texto_la_hoja_muestra_un_icono_y_el_area_con_su_etiqueta(
    cliente, crear_sesion, docente
):
    """Escenario «Sin texto» (PDF escaneado)."""
    crear_sesion(docente, texto="")

    tarjeta = tarjetas_de(principal(pagina(cliente)))[0]

    hoja = re.search(
        r'<span class="sesion-hoja sesion-hoja--sin-texto"[^>]*>.*?</span></span>',
        tarjeta,
        re.DOTALL,
    )
    assert hoja and "<svg" in hoja.group(0) and "Comunicación" in hoja.group(0)
    assert ">PDF<" in tarjeta


def test_en_mis_sesiones_los_chips_y_las_vistas(cliente, crear_sesion, docente, otra_docente):
    """Escenarios «Chips» y «Colegas que la vieron»: nada con 0, singular con 1."""
    crear_sesion(docente, titulo="Ninguna", compartida=True)
    una = crear_sesion(docente, titulo="Una")
    tres = crear_sesion(docente, titulo="Tres", compartida=True)
    una.vistas.create(usuario=otra_docente)
    for n in range(3):
        tres.vistas.create(usuario=colega(n))

    por_titulo = {
        re.search(r'class="sesion-titulo">([^<]*)<', t).group(1): texto_plano(t)
        for t in tarjetas_de(principal(pagina(cliente)))
    }

    assert por_titulo["Ninguna"].endswith("Enviada Compartida")
    assert "colega" not in por_titulo["Ninguna"]
    assert "Compartida" not in por_titulo["Una"] and "Enviada" in por_titulo["Una"]
    assert "La vio 1 colega" in por_titulo["Una"]
    assert "La vieron 3 colegas" in por_titulo["Tres"]


def test_en_el_repositorio_la_tarjeta_no_lleva_chips_ni_vistas(cliente, crear_sesion, otra_docente):
    crear_sesion(otra_docente, compartida=True).vistas.create(usuario=colega(1))

    tarjeta = tarjetas_de(repositorio(cliente))[0]

    assert "Enviada" not in tarjeta and "colega" not in tarjeta


def test_los_grupos_de_mis_sesiones_marcan_su_dia(cliente, crear_sesion, docente):
    crear_sesion(docente)

    html = principal(pagina(cliente))

    assert '<section class="sesiones-dia" data-dia="Hoy"><h2>Hoy</h2>' in html


def test_sin_envios_el_estado_vacio_y_el_contador_en_cero(cliente):
    """Escenario «Sin envíos»."""
    html = principal(pagina(cliente))

    assert "Aquí verás las sesiones que envíes y su estado." in html
    assert texto_plano(pestanas(html)).startswith("Mis sesiones 0")


@pytest.mark.parametrize(
    ("cantidad", "titulo"),
    [(1, "1 sesión compartida"), (3, "3 sesiones compartidas")],
)
def test_el_titulo_de_resultados_en_singular_y_plural(
    cliente, crear_sesion, otra_docente, cantidad, titulo
):
    """Escenarios «Compartidas de la institución» y «Una sola»."""
    for n in range(cantidad):
        crear_sesion(otra_docente, titulo=f"S{n}", compartida=True)

    html = repositorio(cliente)

    abre = re.search(r'<h2 [^>]*id="resultados-titulo"[^>]*>', html).group(0)
    assert f"{titulo}</h2>" in html[html.index(abre) :]
    assert "aria-live" not in abre, "el total lo anuncia la región #anuncio"


def test_con_filtros_el_titulo_no_dice_compartidas(cliente, crear_sesion, otra_docente):
    crear_sesion(otra_docente, titulo="Agua uno", compartida=True)
    crear_sesion(otra_docente, titulo="Agua dos", compartida=True)

    html = repositorio(cliente, q="agua")

    assert re.search(r'id="resultados-titulo"[^>]*>2 sesiones</h2>', html)


def test_sin_filtros_no_hay_grupo_de_filtros_activos(cliente, crear_sesion, otra_docente):
    """Escenario «Sin filtros»."""
    crear_sesion(otra_docente, compartida=True)

    html = repositorio(cliente)

    assert 'aria-label="Filtros activos"' not in html
    assert 'id="filtros-activos"' in html, "la zona fuera de banda existe"


def test_con_filtros_hay_un_grupo_con_un_boton_por_filtro(
    cliente, crear_sesion, otra_docente, comunicacion
):
    """Escenarios «Un filtro activo» y «Quitar uno»."""
    crear_sesion(otra_docente, grado=3, titulo="Agua", compartida=True)

    html = repositorio(cliente, q="agua", grado="3", area=comunicacion.pk)

    grupo = re.search(r'<div role="group" aria-label="Filtros activos">.*?</div>', html, re.DOTALL)
    assert grupo
    quitar = re.findall(
        r'<a [^>]*aria-label="(Quitar filtro [^"]*)"[^>]*href="([^"]*)"', grupo.group(0)
    )
    assert [t for t, _ in quitar] == [
        "Quitar filtro «agua»",
        "Quitar filtro 3.º grado",
        "Quitar filtro Comunicación",
    ]
    sin_grado = dict(quitar)["Quitar filtro 3.º grado"]
    assert "q=agua" in sin_grado and "grado" not in sin_grado and "area=" in sin_grado


def test_el_grado_elegido_se_quita_al_tocarlo_de_nuevo(cliente, crear_sesion, otra_docente):
    """Escenario «Quitar un grado»."""
    crear_sesion(otra_docente, grado=3, compartida=True)

    html = repositorio(cliente, grado="3", q="x")
    tres = re.search(r'<a [^>]*aria-current="true"[^>]*data-grado[^>]*>3\.º</a>', html)

    assert tres and "grado" not in re.search(r'href="([^"]*)"', tres.group(0)).group(1)
    otro = re.search(r'<a [^>]*href="([^"]*)"[^>]*data-grado[^>]*>4\.º</a>', html)
    assert "grado=4" in otro.group(1) and "q=x" in otro.group(1)


def test_las_areas_traen_su_conteo_y_la_de_cero_no_se_puede_elegir(
    cliente, crear_sesion, otra_docente, matematica
):
    """Escenario «Conteo por área»."""
    crear_sesion(otra_docente, compartida=True)
    crear_sesion(otra_docente, compartida=True)
    crear_sesion(otra_docente, area=matematica, compartida=True)

    html = repositorio(cliente)
    filtros = re.search(r'<dialog\b[^>]*id="filtros".*?</dialog>', html, re.DOTALL).group(0)
    areas = {
        re.sub(r"\s+\d+$", "", texto_plano(m)): m
        for m in re.findall(r"<a [^>]*data-area[^>]*>.*?</a>", filtros, re.DOTALL)
    }

    assert texto_plano(areas["Todas las áreas"]).endswith(" 3")
    assert texto_plano(areas["Comunicación"]).endswith(" 2")
    assert texto_plano(areas["Matemática"]).endswith(" 1")
    vacias = [m for m in areas.values() if texto_plano(m).endswith(" 0")]
    assert vacias, "el catálogo de pruebas trae áreas sin sesiones"
    for vacia in vacias:
        assert 'aria-disabled="true"' in vacia and "href=" not in vacia


def test_el_panel_de_filtros_es_un_dialogo_con_su_titulo_y_su_cierre(cliente):
    """Escenario «Filtros en el celular»: un solo marcado; «Filtrar» junto al buscador."""
    html = repositorio(cliente)

    assert html.count('id="filtros"') == 1
    dialogo = re.search(r'<dialog\b[^>]*id="filtros"[^>]*>.*?</dialog>', html, re.DOTALL).group(0)
    assert 'aria-labelledby="filtros-titulo"' in dialogo
    assert re.search(r'<h2 id="filtros-titulo"[^>]*>Filtros</h2>', dialogo)
    assert re.search(r'<button [^>]*aria-label="Cerrar filtros"[^>]*data-cerrar-filtros', dialogo)
    assert "Borrar todo" in dialogo
    boton = re.search(BOTON_FILTRAR, html, re.DOTALL)
    assert boton and texto_plano(boton.group(0)).startswith("Filtrar")


def test_filtrar_indica_cuantos_filtros_hay_puestos(cliente, comunicacion):
    sin = re.search(BOTON_FILTRAR, repositorio(cliente), re.DOTALL)
    con = re.search(BOTON_FILTRAR, repositorio(cliente, grado="3", area=comunicacion.pk), re.DOTALL)

    assert texto_plano(sin.group(0)) == "Filtrar"
    assert texto_plano(con.group(0)) == "Filtrar 2"


def test_el_buscador_es_un_formulario_get_con_su_etiqueta_y_su_borrado(cliente):
    """Escenarios «Mientras escribe» y «Borrar la búsqueda»."""
    html = repositorio(cliente, q="agua")

    form = re.search(r'<form\b[^>]*role="search"[^>]*>.*?</form>', html, re.DOTALL).group(0)
    assert 'method="get"' in form and 'action="/docente/sesiones/repositorio/"' in form
    assert re.search(
        r'<label [^>]*for="buscar"[^>]*>Buscar sesiones por título, propósito o texto', form
    )
    campo = re.search(r'<input [^>]*id="buscar"[^>]*>', form).group(0)
    assert 'type="search"' in campo and 'name="q"' in campo and 'value="agua"' in campo
    assert 'maxlength="100"' in campo
    assert re.search(r'<button [^>]*aria-label="Borrar búsqueda"', form)
    assert 'hx-trigger="input changed delay:400ms, submit"' in form
    assert 'hx-sync="this:replace"' in form
    vacio = re.search(r'<button [^>]*aria-label="Borrar búsqueda"[^>]*>', repositorio(cliente))
    assert " hidden" in vacio.group(0)


def test_la_busqueda_conserva_el_grado_y_el_area_en_campos_ocultos(cliente, comunicacion):
    html = repositorio(cliente, grado="3", area=comunicacion.pk)

    ocultos = re.search(r'<span id="campos-ocultos"[^>]*>(.*?)</span>', html, re.DOTALL).group(1)
    assert 'name="grado" value="3"' in ocultos
    assert f'name="area" value="{comunicacion.pk}"' in ocultos


def test_sin_coincidencias_dice_el_mensaje_y_borra_filtros(cliente, crear_sesion, otra_docente):
    """Escenarios «Caso de error (sin coincidencias)» y «Borrar filtros»."""
    crear_sesion(otra_docente, compartida=True)

    html = repositorio(cliente, q="inexistente")

    assert "No se encontraron sesiones con esos filtros" in html
    assert re.search(r'<a [^>]*href="/docente/sesiones/repositorio/"[^>]*>Borrar filtros</a>', html)
    assert not tarjetas_de(html)


def test_repositorio_vacio_lleva_a_mis_sesiones(cliente):
    """Escenario «Repositorio vacío»."""
    html = repositorio(cliente)

    assert "Comparte una de tus sesiones" in html
    assert re.search(r'<a [^>]*href="/docente/sesiones/"[^>]*>Ir a Mis sesiones</a>', html)


def test_ver_mas_conserva_la_busqueda_y_los_filtros(cliente, crear_sesion, otra_docente):
    for n in range(21):
        crear_sesion(otra_docente, titulo=f"Agua {n}", grado=3, compartida=True)

    html = repositorio(cliente, q="agua", grado="3")

    mas = re.search(r'<a [^>]*class="btn btn--secondary sesiones-mas"[^>]*>', html).group(0)
    assert "q=agua" in mas and "grado=3" in mas and "pagina=2" in mas
    assert 'hx-swap="outerHTML"' in mas and 'hx-target="this"' in mas


# --- Página de la sesión ---


def test_la_pagina_muestra_migas_formato_titulo_chips_y_ficha(cliente, crear_sesion, otra_docente):
    """Escenario «Sesión con texto»."""
    sesion = crear_sesion(
        otra_docente,
        titulo="Leemos un cuento sobre la amistad",
        grado=1,
        compartida=True,
        proposito="Reconocer a los personajes.",
        tamano_bytes=142 * 1024,
        texto="SESIÓN\nLínea dos",
    )

    html = detalle(cliente, sesion)
    plano = texto_plano(html)

    assert '<nav class="migas" aria-label="Migas"><a href="/docente/sesiones/repositorio/">' in html
    assert "Sesión de aprendizaje · PDF" in plano
    assert "<h1>Leemos un cuento sobre la amistad</h1>" in html
    for esperado in ("1.º grado", "Comunicación", "Compartida", "Rosa Mamani", "142 KB", "PDF"):
        assert esperado in plano, esperado
    assert "Propósito Reconocer a los personajes." in plano
    assert "Vista previa del texto" in plano
    assert "Texto sin formato. Descarga el archivo para verlo tal como es." in plano
    assert '<pre class="sesion-texto">SESIÓN\nLínea dos</pre>' in html


def test_sin_proposito_ni_texto_dice_que_no_hay_vista_previa(cliente, crear_sesion, docente):
    """Escenario «Sin propósito ni texto»."""
    html = detalle(cliente, crear_sesion(docente, proposito="", texto=""))

    assert "Propósito" not in texto_plano(html)
    assert "La vista previa no está disponible. Puedes descargar el archivo." in texto_plano(html)
    assert "<pre" not in html


def test_la_pagina_propia_lleva_las_migas_a_mis_sesiones(cliente, crear_sesion, docente):
    """Escenario «Migas»."""
    html = detalle(cliente, crear_sesion(docente))

    migas = re.search(r'<nav class="migas".*?</nav>', html, re.DOTALL).group(0)
    assert 'href="/docente/sesiones/"' in migas and "Mis sesiones" in texto_plano(migas)


def test_descargar_y_ver_son_enlaces_del_aplicativo_y_ver_solo_en_pdf(
    cliente, crear_sesion, docente, otra_docente
):
    """Escenarios «PDF» y «Word» de «Ver el PDF»."""
    en_pdf_ = crear_sesion(docente, titulo="Pdf")
    word = crear_sesion(otra_docente, titulo="Word", tipo_mime=TIPO_DOCX, compartida=True)

    en_pdf = detalle(cliente, en_pdf_)
    en_word = detalle(cliente, word)

    assert re.search(rf'<a [^>]*href="/docente/sesiones/{en_pdf_.pk}/descargar/"[^>]*>', en_pdf)
    ver = re.search(rf'<a [^>]*href="/docente/sesiones/{en_pdf_.pk}/ver/"[^>]*>', en_pdf).group(0)
    assert 'target="_blank"' in ver and 'rel="noopener"' in ver
    assert "/descargar/" in en_word and "/ver/" not in en_word
    assert "Sesión de aprendizaje · Word" in texto_plano(en_word)


def test_tu_sesion_propia_compartida(cliente, crear_sesion, docente):
    """Escenario «Propia compartida»."""
    sesion = crear_sesion(docente, compartida=True)

    html = detalle(cliente, sesion)
    tuya = re.search(r'<aside class="sesion-tuya"[^>]*>.*?</aside>', html, re.DOTALL).group(0)

    assert 'aria-labelledby="tu-sesion"' in tuya
    plano = texto_plano(tuya)
    assert "Tu sesión" in plano
    assert "Compartida con tus colegas y enviada a la dirección." in plano
    assert f'action="/docente/sesiones/{sesion.pk}/dejar-de-compartir/"' in tuya
    assert "Dejar de compartir" in plano and "Eliminar" in plano
    assert "También se retira de la dirección." in plano
    assert 'name="csrfmiddlewaretoken"' in tuya


def test_tu_sesion_propia_sin_compartir_ofrece_compartir_con_los_terminos(
    cliente, crear_sesion, docente
):
    """Escenarios «Propia sin compartir», «Aceptar y compartir» y «Volver»."""
    sesion = crear_sesion(docente)

    html = detalle(cliente, sesion)
    tuya = re.search(r'<aside class="sesion-tuya".*?</aside>', html, re.DOTALL).group(0)

    plano = texto_plano(tuya)
    assert "Enviada a la dirección. Solo tú y la dirección la ven." in plano
    assert "Compartir" in plano and "Dejar de compartir" not in plano
    assert '<span class="chip">Compartida</span>' not in html
    terminos = re.search(r'<dialog\b[^>]*id="terminos-compartir".*?</dialog>', html, re.DOTALL)
    terminos = terminos.group(0)
    assert "Antes de compartir" in terminos
    for linea in TERMINOS:
        assert linea in terminos
    assert re.search(
        r'<button [^>]*type="submit"[^>]*name="acepta_terminos"[^>]*value="1"[^>]*>'
        r"Acepto y comparto</button>",
        terminos,
    )
    assert re.search(r"<button [^>]*data-volver[^>]*>.*Volver</button>", terminos, re.DOTALL)
    form = re.search(r'<form [^>]*id="form-compartir"[^>]*>', terminos).group(0)
    assert f'action="/docente/sesiones/{sesion.pk}/compartir/"' in form
    assert 'method="post"' in form


def test_el_dialogo_de_eliminar_tiene_su_texto_y_cancelar_primero(cliente, crear_sesion, docente):
    """El diálogo de «Eliminar una sesión propia» y «Cancelar y foco»."""
    sesion = crear_sesion(docente)

    html = detalle(cliente, sesion)
    dialogo = re.search(r'<dialog\b[^>]*id="eliminar".*?</dialog>', html, re.DOTALL).group(0)

    assert "dialog--chico" in dialogo
    plano = texto_plano(dialogo)
    assert "¿Eliminar esta sesión?" in plano
    assert "También se retira de la dirección." in plano
    assert "Se eliminarán la sesión y su archivo para todos." in plano
    assert dialogo.index("Cancelar") < dialogo.index("Eliminar sesión")
    cancelar = re.search(r"<button [^>]*data-cancelar[^>]*>", dialogo).group(0)
    assert "autofocus" in cancelar
    assert f'action="/docente/sesiones/{sesion.pk}/eliminar/"' in dialogo
    assert re.search(r'<button [^>]*type="submit"[^>]*>Eliminar sesión</button>', dialogo)


def test_en_una_ajena_no_hay_tarjeta_ni_acciones_ni_vistas(
    cliente, crear_sesion, otra_docente, docente
):
    """Escenarios «Ajena» y «Una colega no ve el total»."""
    sesion = crear_sesion(otra_docente, compartida=True)
    sesion.vistas.create(usuario=docente)
    sesion.vistas.create(usuario=colega(1))

    html = detalle(cliente, sesion)
    plano = re.sub(r"Compartida", "", texto_plano(html))

    assert "Tu sesión" not in plano
    for accion in ("Dejar de compartir", "Compartir", "Eliminar", "colega"):
        assert accion not in plano, accion
    assert "<dialog" not in html and "/eliminar/" not in html and "/compartir/" not in html


def test_la_autora_ve_cuantas_colegas_la_vieron_en_su_tarjeta(cliente, crear_sesion, docente):
    """Escenario «La autora»."""
    sesion = crear_sesion(docente, compartida=True)
    for n in range(3):
        sesion.vistas.create(usuario=colega(n))

    tuya = re.search(r'<aside class="sesion-tuya".*?</aside>', detalle(cliente, sesion), re.DOTALL)

    assert "La vieron 3 colegas" in texto_plano(tuya.group(0))
    assert "colega0" not in tuya.group(0)


def test_texto_con_marcas_sale_escapado_en_la_pagina_y_en_la_tarjeta(
    cliente, crear_sesion, docente
):
    """Escenario «Texto con marcas de HTML»."""
    sesion = crear_sesion(
        docente, titulo="<script>alert(1)</script>", texto="<img src=x onerror=alert(2)>"
    )

    en_pagina = detalle(cliente, sesion)
    en_lista = principal(pagina(cliente))

    for html in (en_pagina, en_lista):
        assert "<script>alert" not in html and "<img src=x" not in html
    assert "&lt;img src=x onerror=alert(2)&gt;" in en_pagina


def test_el_texto_va_en_un_pre_que_parte_las_lineas_largas(cliente, crear_sesion, docente):
    html = detalle(cliente, crear_sesion(docente, texto="x" * 300))

    assert f'<pre class="sesion-texto">{"x" * 300}</pre>' in html


def test_el_mensaje_de_exito_se_anuncia_sin_interrumpir(cliente, crear_sesion, docente):
    """«Dejaste de compartir la sesión»: role=status (rb/mensaje.html con estado)."""
    sesion = crear_sesion(docente, compartida=True)

    respuesta = cliente.post(f"{URL_INICIO}{sesion.pk}/dejar-de-compartir/", follow=True)
    html = respuesta.content.decode()

    assert '<div class="message message--exito" role="status">' in html
    assert "Dejaste de compartir la sesión" in html


# --- Reglas de plantillas ---


def test_ninguna_plantilla_de_repositorio_lleva_style_ni_colores_hex():
    carpeta = Path(__file__).resolve().parents[2] / "templates" / "repositorio"
    for ruta in carpeta.glob("*.html"):
        contenido = ruta.read_text(encoding="utf-8")
        assert " style=" not in contenido, ruta.name
        assert not re.search(r"(?<![&\w])#[0-9a-fA-F]{3,8}\b", contenido), ruta.name
