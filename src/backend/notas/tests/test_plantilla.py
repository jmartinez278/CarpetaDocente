"""La plantilla de las competencias (spec competencias-periodo; design de US-029, D9).

El servidor dibuja la lista completa con el estado del periodo que abre; ``competencias.js`` agrega
el marcado y el guardado (sus pruebas son las de punta a punta). Aquí se revisa el HTML.
"""

import re

import pytest
from django.urls import reverse

from catalogo.models import Competencia
from notas.models import CompetenciaPeriodo
from notas.tests.conftest import (
    AGO_1,
    ARTE,
    COMUNICACION,
    EDUCACION_FISICA,
    INGLES,
    MAR_2,
    MATEMATICA,
    NOV_20,
    con_notas,
    ids_de,
)

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def hoy(hoy):
    """Todas las pruebas de la plantilla corren el 30 de octubre (fixture de conftest)."""
    return hoy


def pagina(cliente, seccion, **parametros):
    respuesta = cliente.get(reverse("competencias:pantalla", args=[seccion.pk]), parametros)
    assert respuesta.status_code == 200
    return respuesta.content.decode()


def area(html, codigo):
    """El bloque HTML de un área por su código SIAGIE."""
    encontrado = re.search(
        rf'<section class="comp-area[^"]*" data-area="{codigo}".*?</section>', html, re.DOTALL
    )
    assert encontrado, f"el área {codigo} está en la página"
    return encontrado.group(0)


def fila(html, competencia):
    """La fila de una competencia por su id."""
    encontrado = re.search(
        rf'<li class="comp-fila[^"]*" data-competencia-fila="{competencia}".*?</li>',
        html,
        re.DOTALL,
    )
    assert encontrado, f"la competencia {competencia} está en la página"
    return encontrado.group(0)


def boton_de_periodo(html, numero):
    encontrado = re.search(rf'<button [^>]*data-periodo="{numero}".*?</button>', html, re.DOTALL)
    assert encontrado, f"el botón del periodo {numero} está en la página"
    return encontrado.group(0)


def texto(fragmento):
    """El texto visible y para el lector de un fragmento, con los espacios normalizados."""
    return " ".join(re.sub(r"<[^>]+>", "", fragmento).split())


def principal(html):
    """El contenido del único ``<main>`` (el del marco del rebrand)."""
    assert html.count("<main") == 1, "un solo <main>: el del marco"
    return re.search(r"<main\b.*?</main>", html, re.DOTALL).group(0)


def marcar(seccion, periodo, ids):
    CompetenciaPeriodo.objects.bulk_create(
        CompetenciaPeriodo(seccion=seccion, periodo=periodo, competencia_id=i) for i in ids
    )


# --- Áreas y competencias (spec "Competencias que ve la tutora") ---


def test_dibuja_las_10_areas_en_orden_siagie_con_sus_27_competencias(cliente, seccion_tutora, ie):
    html = pagina(cliente, seccion_tutora)

    nombres = re.findall(r'<h3 id="area-[^"]+">([^<]+)</h3>', html)
    assert nombres == [
        "Arte y Cultura",
        "Inglés como lengua extranjera",
        "Ciencia y Tecnología",
        "Comunicación",
        "Educación Física",
        "Educación Religiosa",
        "Matemática",
        "Personal Social",
        "Se desenvuelve en entornos virtuales generados por las TIC",
        "Gestiona su aprendizaje de manera autónoma",
    ]
    assert len(re.findall(r'<input type="checkbox"', html)) == 27


def test_cada_competencia_tiene_su_casilla_con_etiqueta(cliente, seccion_tutora, ie):
    html = pagina(cliente, seccion_tutora)

    for competencia in ids_de(MATEMATICA):
        texto = fila(html, competencia)
        assert f'<label for="c-{competencia}">' in texto
        assert f'id="c-{competencia}"' in texto
        assert f'data-competencia="{competencia}"' in texto
        # La casilla va dentro de la etiqueta: la fila entera es pulsable.
        assert re.search(r'<label [^>]*>.*<input type="checkbox".*</label>', texto, re.DOTALL)


def test_cada_area_marcable_lleva_su_contador(cliente, seccion_tutora, ie):
    marcar(seccion_tutora, seccion_tutora.anio_escolar.periodos.get(numero=3), ids_de(ARTE))
    html = pagina(cliente, seccion_tutora)

    arte = ids_de(ARTE)
    contador = re.search(
        r'<span class="comp-cuenta" data-cuenta[^>]*>([^<]*)</span>', area(html, ARTE)
    )
    assert contador.group(1) == f"{len(arte)}/{len(arte)}"
    assert f'aria-label="{len(arte)} de {len(arte)} seleccionadas"' in area(html, ARTE)


def test_el_contador_cuenta_solo_las_marcadas_del_periodo_que_abre(
    cliente, seccion_tutora, ie, bimestres
):
    una = sorted(ids_de(MATEMATICA))[0]
    marcar(seccion_tutora, bimestres[2], [una, *sorted(ids_de(COMUNICACION))])

    html = pagina(cliente, seccion_tutora)

    total = len(ids_de(MATEMATICA))
    assert f">1/{total}</span>" in area(html, MATEMATICA)
    assert f'<input type="checkbox" id="c-{una}"' in fila(html, una)
    assert " checked" in fila(html, una)
    otra = sorted(ids_de(MATEMATICA))[1]
    assert " checked" not in fila(html, otra)


def test_cada_competencia_lleva_su_codigo_y_su_nombre_completo(cliente, seccion_tutora, ie):
    html = pagina(cliente, seccion_tutora)

    codigos = re.findall(r'<span class="comp-n">(C\d+)</span>', area(html, MATEMATICA))
    assert codigos == [f"C{n}" for n in range(1, len(ids_de(MATEMATICA)) + 1)]
    nombre = Competencia.objects.get(pk=min(ids_de(MATEMATICA))).nombre
    assert nombre in fila(html, min(ids_de(MATEMATICA)))


def test_sin_marcas_abre_con_todo_marcado(cliente, seccion_tutora, ie):
    html = pagina(cliente, seccion_tutora)

    for competencia in ie:
        assert " checked" in fila(html, competencia)


def test_las_transversales_dicen_competencia_transversal(cliente, seccion_tutora, ie):
    html = pagina(cliente, seccion_tutora)

    assert html.count('<p class="comp-sub">Competencia transversal</p>') == 2


# --- Áreas a cargo del docente de curso ---


def test_un_area_a_cargo_va_atenuada_con_su_aviso_y_casillas_deshabilitadas(
    cliente, seccion_tutora, ie
):
    html = pagina(cliente, seccion_tutora)

    for codigo in (EDUCACION_FISICA, INGLES):
        bloque = area(html, codigo)
        assert "comp-area--curso" in bloque
        assert "A cargo del docente de curso" in bloque
        assert "comp-cuenta" not in bloque
        casillas = re.findall(r'<input type="checkbox"[^>]*>', bloque)
        assert casillas
        assert all(" disabled" in c and " checked" not in c for c in casillas)
        assert all(f'aria-describedby="curso-{codigo}"' in c for c in casillas)
        assert f'<p class="comp-sub" id="curso-{codigo}">' in bloque


def test_un_area_de_la_tutora_no_dice_a_cargo(cliente, seccion_tutora, ie):
    bloque = area(pagina(cliente, seccion_tutora), MATEMATICA)

    assert "comp-area--curso" not in bloque
    assert "A cargo del docente de curso" not in bloque
    assert not re.search(r'<input type="checkbox"[^>]* disabled', bloque)


# --- Periodos (spec "Periodos que se marcan") ---


def test_los_botones_de_periodo_dicen_romano_estado_y_guardan_las_fechas_para_el_lector(
    cliente, seccion_tutora, ie
):
    html = pagina(cliente, seccion_tutora)

    assert 'role="group" aria-label="Bimestres de 2027"' in html
    textos = {
        1: ("I", "Anterior", "del 9 de marzo al 15 de mayo"),
        2: ("II", "Anterior", "del 25 de mayo al 24 de julio"),
        3: ("III", "Vigente", "del 10 de agosto al 30 de octubre"),
        4: ("IV", "Futuro", "del 8 de noviembre al 18 de diciembre"),
    }
    for numero, (romano, estado, fechas) in textos.items():
        boton = boton_de_periodo(html, numero)
        assert f"<strong>{romano}</strong>" in boton
        assert f"<span data-estado-periodo>{estado}</span>" in boton
        assert texto(boton) == f"{romano} bimestre, {estado}, {fechas}"
        # Las fechas solo van en el sr-only: a la vista, el botón dice el romano y el estado.
        assert f'<span class="sr-only">, {fechas}</span>' in boton
        assert "aria-label" not in boton


def test_las_fechas_del_periodo_quedan_ocultas_para_el_js(cliente, seccion_tutora, ie):
    html = pagina(cliente, seccion_tutora)

    assert re.search(r"<span[^>]* data-fecha-periodo[^>]* hidden[^>]*>", html)
    assert "Puedes volver a los bimestres anteriores." not in html
    assert 'id="titulo-periodos"' not in html


def test_el_vigente_va_presionado_y_los_demas_no(cliente, seccion_tutora, ie):
    html = pagina(cliente, seccion_tutora)

    presionados = [n for n in (1, 2, 3, 4) if 'aria-pressed="true"' in boton_de_periodo(html, n)]
    assert presionados == [3]
    assert all('aria-pressed="false"' in boton_de_periodo(html, n) for n in (1, 2, 4))


def test_el_futuro_va_deshabilitado_y_los_que_empezaron_no(cliente, seccion_tutora, ie):
    html = pagina(cliente, seccion_tutora)

    assert " disabled" in boton_de_periodo(html, 4)
    assert all(" disabled" not in boton_de_periodo(html, n) for n in (1, 2, 3))


def test_el_periodo_pedido_abre_presionado(cliente, seccion_tutora, ie):
    html = pagina(cliente, seccion_tutora, periodo="1")

    assert 'aria-pressed="true"' in boton_de_periodo(html, 1)
    assert 'aria-pressed="false"' in boton_de_periodo(html, 3)


def test_con_trimestres_los_botones_dicen_romanos(cliente, institucion, seccion_tutora, ie):
    institucion.organizacion_periodos = institucion.OrganizacionPeriodos.TRIMESTRE
    institucion.save()

    html = pagina(cliente, seccion_tutora)

    assert "<strong>I</strong>" in boton_de_periodo(html, 1)
    assert texto(boton_de_periodo(html, 3)).startswith("III trimestre, Vigente")
    assert 'aria-label="Trimestres de 2027"' in html
    assert "<h1>Competencias del trimestre</h1>" in html
    assert "Desmarca las que no desarrollaste en este trimestre." in html


# --- Bloqueos con su motivo en la fila ---


def test_una_competencia_con_notas_va_marcada_bloqueada_con_su_motivo(
    cliente, seccion_tutora, bimestres, ie
):
    elegida = min(ie)
    con_notas(seccion_tutora, bimestres[2], [elegida])

    html = pagina(cliente, seccion_tutora)

    texto = fila(html, elegida)
    assert 'aria-disabled="true"' in texto and " checked" in texto
    assert "comp-fila--notas" in texto
    assert "La competencia tiene notas registradas en este periodo" in texto
    assert '<span class="motivo">' in texto and "<svg" in texto
    otra = fila(html, max(ie))
    assert "aria-disabled" not in otra
    assert "La competencia tiene notas" not in otra


def test_las_obligatorias_del_ultimo_periodo_dicen_su_motivo(
    cliente, seccion_tutora, bimestres, ie, hoy
):
    faltan = sorted(ie)[:5]
    for periodo in bimestres[:3]:
        marcar(seccion_tutora, periodo, ie - set(faltan))
        con_notas(seccion_tutora, periodo, ie - set(faltan))
    hoy["valor"] = NOV_20

    html = pagina(cliente, seccion_tutora)

    for competencia in faltan:
        texto = fila(html, competencia)
        assert 'aria-disabled="true"' in texto and " checked" in texto
        assert "comp-fila--anual" in texto
        assert "Debe tener nivel al cerrar el año" in texto
    assert html.count("Debe tener nivel al cerrar el año") == 5


def test_en_otro_periodo_ninguna_competencia_va_bloqueada(cliente, seccion_tutora, ie):
    html = pagina(cliente, seccion_tutora)

    assert "aria-disabled" not in "".join(fila(html, c) for c in ie)
    assert "Debe tener nivel" not in html


# --- Panel, guardado y avisos ---


def test_el_panel_es_una_sola_tarjeta_con_el_total_del_periodo(cliente, seccion_tutora, ie):
    html = pagina(cliente, seccion_tutora)

    assert html.count("Tu selección") == 1
    assert "<strong data-conteo>21/21</strong>" in html
    assert "<span data-conteo-periodo>para el III bimestre</span>" in html
    # El total escrito es decorativo: el lector oye la copia sr-only.
    conteo = re.search(r'<p class="comp-conteo"[^>]*>', html).group(0)
    assert 'aria-hidden="true"' in conteo
    assert '<p class="sr-only" data-conteo-lector>21 de 21 para el III bimestre</p>' in html
    assert re.search(r'<progress[^>]*data-progreso[^>]*aria-hidden="true"[^>]*>', html)
    assert "Las áreas del docente de curso no se incluyen." in html
    assert "data-resumen-bloqueos" in html and "data-guardado" in html
    assert html.count('id="guardar"') == 1 and html.count('id="deshacer"') == 1
    assert "21 de 21 seleccionadas" not in html and "competencias para B3" not in html


def test_con_marcas_el_panel_cuenta_las_guardadas(cliente, seccion_tutora, bimestres, ie):
    marcar(seccion_tutora, bimestres[2], sorted(ie)[:18])

    html = pagina(cliente, seccion_tutora)

    assert "<strong data-conteo>18/21</strong>" in html
    assert "18 de 21 para el III bimestre" in html


def test_registrar_notas_del_periodo_va_fuera_de_la_tarjeta(cliente, seccion_tutora, ie):
    html = pagina(cliente, seccion_tutora)

    enlace = re.search(r"<a [^>]*data-registrar-notas[^>]*>.*?</a>", html, re.DOTALL).group(0)
    assert texto(enlace) == "Registrar notas del III bimestre"
    tarjeta = re.search(r'<section class="comp-resumen".*?</section>', html, re.DOTALL).group(0)
    assert "data-registrar-notas" not in tarjeta


def test_el_boton_guardar_y_deshacer(cliente, seccion_tutora, ie):
    html = pagina(cliente, seccion_tutora)

    assert re.search(r'<button[^>]*id="guardar"[^>]*>Guardar</button>', html)
    assert 'aria-disabled="true"' in re.search(r'<button[^>]*id="guardar"[^>]*>', html).group(0)
    assert "Guarda la selección de todas las áreas del" in html
    assert re.search(
        r'<button[^>]*id="deshacer"[^>]* hidden[^>]*>(<svg.*?</svg>\s*)?Deshacer cambios</button>',
        html,
        re.DOTALL,
    )


def test_la_capsula_de_areas_lleva_flechas_posicion_y_selector(cliente, seccion_tutora, ie):
    html = pagina(cliente, seccion_tutora)

    assert 'aria-label="Área anterior"' in html and 'aria-label="Área siguiente"' in html
    assert re.search(r"<span[^>]* data-posicion-area[^>]*>1 de 10</span>", html)
    selector = re.search(r'<select[^>]*id="area-elegida".*?</select>', html, re.DOTALL).group(0)
    assert len(re.findall(r"<option ", selector)) == 10
    assert "Arte y Cultura" in selector


def test_el_dialogo_de_salida(cliente, seccion_tutora, ie):
    html = pagina(cliente, seccion_tutora)

    dialogo = re.search(
        r'<dialog [^>]*id="confirmar-salida"[^>]*>.*?</dialog>', html, re.DOTALL
    ).group(0)
    assert 'id="confirmar-salida"' in dialogo
    assert 'aria-labelledby="titulo-salida"' in dialogo
    assert 'aria-describedby="texto-salida"' in dialogo
    assert re.search(r'<h2 id="titulo-salida"[^>]*>¿Salir sin guardar\?</h2>', dialogo)
    assert '<p class="small"' not in dialogo
    assert '<div id="texto-salida">' in dialogo
    assert "Tienes cambios pendientes en:" in dialogo
    assert re.search(r"<ul[^>]* data-pendientes[^>]*></ul>", dialogo)
    assert "Si sales, estos cambios se pierden." in dialogo
    seguir = re.search(r'<button[^>]*id="seguir-editando"[^>]*>', dialogo).group(0)
    assert "autofocus" in seguir and "btn--primary" in seguir
    assert dialogo.index('id="seguir-editando"') < dialogo.index('id="salir-sin-guardar"')
    assert "Salir sin guardar</button>" in dialogo


def test_las_regiones_del_lector_de_pantalla_y_el_noscript(cliente, seccion_tutora, ie):
    html = pagina(cliente, seccion_tutora)

    assert html.count('role="status"') == 1
    assert html.count('role="alert"') == 1
    noscript = re.search(r"<noscript>.*?</noscript>", html, re.DOTALL).group(0)
    assert "Activa JavaScript para guardar las competencias." in noscript
    assert 'class="message message--aviso"' in noscript


def test_la_pagina_lleva_su_titulo_y_los_datos_de_los_periodos(cliente, seccion_tutora, ie):
    html = pagina(cliente, seccion_tutora)

    assert html.count("<h1") == 1
    assert "<title>Competencias · 2.º A · CarpetaDocente</title>" in html
    assert '<script id="datos-competencias" type="application/json">' in html
    assert "js/competencias.js" in html


def test_la_pantalla_va_en_el_marco_del_rebrand(cliente, seccion_tutora, ie):
    html = pagina(cliente, seccion_tutora)

    hojas = re.findall(r'<link rel="stylesheet" href="([^"]+)"', html)
    assert len(hojas) == 1 and hojas[0].endswith("dist/rebrand.css")
    assert "dist/app.css" not in html
    assert "js/competencias.js" in html
    assert 'data-dimension="notas"' in principal(html)
    assert '<span class="bar-title">Notas</span>' in html
    actuales = re.findall(r'<a [^>]*aria-current="page"[^>]*>(.*?)</a>', html, re.DOTALL)
    assert [texto(a) for a in actuales] == ["Notas"]


def test_el_encabezado_lleva_la_vuelta_a_la_hoja_la_seccion_y_el_titulo(
    cliente, seccion_tutora, ie
):
    html = pagina(cliente, seccion_tutora, periodo="2", area=MATEMATICA)

    contenido = principal(html)
    volver = re.search(r'<nav class="breadcrumb"[^>]*>.*?</nav>', contenido, re.DOTALL).group(0)
    assert f'href="{reverse("notas:hoja", args=[seccion_tutora.pk])}"' in volver
    assert "?" not in re.search(r'href="([^"]+)"', volver).group(1)
    assert texto(volver) == "Registrar notas"
    assert '<p class="small">2.º grado, sección A · 2027</p>' in contenido
    assert "<h1>Competencias del bimestre</h1>" in contenido


def test_las_instrucciones_de_celular_y_de_pc(cliente, seccion_tutora, ie):
    html = pagina(cliente, seccion_tutora)

    instruccion = re.search(r"<p[^>]* data-instruccion[^>]*>.*?</p>", html, re.DOTALL).group(0)
    assert (
        "Confirma qué competencias trabajaste. Desmarca las que no desarrollaste en este bimestre."
        in instruccion
    )
    assert "Desmarca las que no trabajaste." in instruccion


def test_sin_estilos_en_linea_ni_colores_hex(cliente, seccion_tutora, ie):
    html = pagina(cliente, seccion_tutora)

    assert "style=" not in html
    assert not re.search(r"#[0-9a-fA-F]{6}\b", html)


# --- Estados vacíos ---


def test_sin_periodos_solo_el_estado_vacio(cliente, seccion_tutora, universo_ie):
    html = pagina(cliente, seccion_tutora)

    vacio = re.search(r'<div class="empty">.*?</div>', html, re.DOTALL).group(0)
    assert "La dirección aún no configura los periodos" in vacio
    assert "Cuando estén listos, podrás confirmar las competencias de tu sección." in vacio
    assert "data-periodo=" not in html
    assert 'id="guardar"' not in html
    assert "Guardar" not in html.replace("Guarda la selección", "")
    assert "Desmarca" not in html
    assert "comp-area" not in html
    assert "Activa JavaScript" not in html


def test_en_vacaciones_el_aviso_y_los_periodos_pasados_sin_ninguno_elegido(
    cliente, seccion_tutora, ie, hoy
):
    hoy["valor"] = AGO_1

    html = pagina(cliente, seccion_tutora)

    aviso = re.search(r"<div[^>]* data-aviso[^>]*>.*?</div></div>", html, re.DOTALL).group(0)
    assert 'class="message message--aviso"' in aviso
    assert "Hoy no hay un periodo vigente" in aviso
    assert "Elige uno de los bimestres ya pasados para revisar sus competencias." in aviso
    assert [" disabled" in boton_de_periodo(html, n) for n in (1, 2, 3, 4)] == [
        False,
        False,
        True,
        True,
    ]
    assert 'aria-pressed="true"' not in html
    vacio = re.search(r"<div[^>]* data-vacio[^>]*>.*?</div>", html, re.DOTALL).group(0)
    assert "Elige un bimestre anterior" in vacio
    assert "Puedes revisar y corregir las competencias del I y II bimestre." in vacio
    trabajo = re.search(r"<div[^>]* data-trabajo[^>]*>", html).group(0)
    assert " hidden" in trabajo
    assert re.search(r"<p[^>]* data-instruccion[^>]* hidden", html)


def test_en_vacaciones_la_lista_viene_sin_marcas(cliente, seccion_tutora, ie, hoy):
    hoy["valor"] = AGO_1

    html = pagina(cliente, seccion_tutora)

    assert not any(" checked" in fila(html, c) for c in ie)


def test_antes_del_primer_periodo_el_aviso_con_la_fecha_y_nada_que_elegir(
    cliente, seccion_tutora, ie, hoy
):
    hoy["valor"] = MAR_2

    html = pagina(cliente, seccion_tutora)

    assert "Hoy no hay un periodo vigente" in html
    assert "El I bimestre empieza el 9 de marzo." in html
    assert all(" disabled" in boton_de_periodo(html, n) for n in (1, 2, 3, 4))
    assert 'id="guardar"' not in html
    assert "data-trabajo" not in html
    assert "Desmarca" not in html
    assert "Puedes revisar y corregir" not in html
    assert 'class="message message--aviso"' in html


# --- Vuelta a las notas (design de US-029 / US-020, D15) ---


def test_registrar_notas_lleva_el_periodo_y_el_area(cliente, seccion_tutora, ie):
    html = pagina(cliente, seccion_tutora, area=MATEMATICA)

    enlace = re.search(r"<a [^>]*data-registrar-notas[^>]*>.*?</a>", html, re.DOTALL).group(0)
    base = reverse("notas:hoja", args=[seccion_tutora.pk])
    assert f'href="{base}?periodo=3&amp;area={MATEMATICA}"' in enlace
    assert texto(enlace) == "Registrar notas del III bimestre"
    assert " hidden" not in enlace


def test_registrar_notas_sin_area_pedida_usa_la_primera(cliente, seccion_tutora, ie):
    html = pagina(cliente, seccion_tutora)

    enlace = re.search(r"<a [^>]*data-registrar-notas[^>]*>", html).group(0)
    assert f"area={ARTE}" in enlace


def test_el_periodo_pedido_cambia_el_enlace_de_notas(cliente, seccion_tutora, ie):
    html = pagina(cliente, seccion_tutora, periodo="2")

    enlace = re.search(r"<a [^>]*data-registrar-notas[^>]*>.*?</a>", html, re.DOTALL).group(0)
    assert "periodo=2" in enlace
    assert texto(enlace) == "Registrar notas del II bimestre"


def test_en_vacaciones_el_enlace_de_notas_va_oculto_hasta_elegir(cliente, seccion_tutora, ie, hoy):
    hoy["valor"] = AGO_1

    html = pagina(cliente, seccion_tutora)

    assert re.search(r"<a [^>]*data-registrar-notas[^>]* hidden", html)


def test_con_desde_notas_avisa_que_el_bimestre_no_tiene_competencias(cliente, seccion_tutora, ie):
    html = pagina(cliente, seccion_tutora, desde="notas", periodo="3", area=MATEMATICA)

    aviso = re.search(r"<div[^>]* data-aviso-sin-marcas[^>]*>.*?</div></div>", html, re.DOTALL)
    assert "III aún no tiene competencias confirmadas" in aviso.group(0)
    assert "B3" not in html
    assert "Confirma las que trabajaste para empezar a registrar los niveles de logro." in html


def test_sin_desde_notas_no_hay_aviso_de_confirmar(cliente, seccion_tutora, ie):
    html = pagina(cliente, seccion_tutora, periodo="3")

    assert "aún no tiene competencias confirmadas" not in html


def test_la_nota_del_periodo_nace_oculta_con_el_mensaje_del_rebrand(cliente, seccion_tutora, ie):
    html = pagina(cliente, seccion_tutora)

    nota = re.search(r"<div[^>]* data-nota-periodo[^>]*>", html).group(0)
    assert " hidden" in nota and "message message--aviso" in nota


def test_el_area_pedida_va_en_los_datos(cliente, seccion_tutora, ie):
    html = pagina(cliente, seccion_tutora, area=MATEMATICA)

    assert f'"area_inicial": "{MATEMATICA}"' in html


def test_un_area_pedida_que_no_existe_se_ignora(cliente, seccion_tutora, ie):
    html = pagina(cliente, seccion_tutora, area="xxxx")

    assert f'"area_inicial": "{ARTE}"' in html
