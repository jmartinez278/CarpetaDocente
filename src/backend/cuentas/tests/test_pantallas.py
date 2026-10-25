"""Pantallas de US-001 (spec pantallas-de-inicio; design.md de US-001, D5 a D8).

Comprueba el contenido y la estructura de ``/ingresar/``, de la portada del docente y del
inicio de la dirección. El aspecto (tokens, temas, anchos) se revisa en el navegador y con
axe en los grupos 6 y 8.
"""

import re
from dataclasses import replace

import pytest

from cuentas import dimensiones
from cuentas.models import Usuario

pytestmark = pytest.mark.django_db

INGRESAR = "/ingresar/"
LINEA_1 = "Usuario o contraseña incorrectos, o cuenta inactiva"
LINEA_2 = "Revisa tus datos. Si el problema sigue, pide ayuda al administrador."
AYUDA = "Si olvidaste tu contraseña, pide al administrador que la restablezca."
CLAVE_INCORRECTA = "no-es-la-clave"

# Orden de arriba abajo que fija el spec "Pantalla de inicio de sesión".
TEXTOS_EN_ORDEN = [
    "I.E. Virgen del Carmen",
    "Huayucachi",
    "Sesiones · Notas · Asistencia",
    "Usuario",
    "Contraseña",
    "Ingresar",
    AYUDA,
    "CarpetaDocente · 2026",
]


@pytest.fixture
def pagina(client):
    return client.get(INGRESAR).content.decode()


@pytest.fixture
def pagina_rechazada(client, docente):
    respuesta = client.post(INGRESAR, {"username": "ana.quispe", "password": CLAVE_INCORRECTA})
    return respuesta.content.decode()


@pytest.fixture
def pagina_con_campos_vacios(client):
    return client.post(INGRESAR, {"username": "", "password": ""}).content.decode()


def etiqueta(html, patron):
    """Primera etiqueta de apertura que contiene ``patron`` (para revisar sus atributos)."""
    encontrada = re.search(rf"<[a-z0-9]+\b[^>]*{patron}[^>]*>", html, re.DOTALL)
    assert encontrada, f"no hay una etiqueta con {patron}"
    return encontrada.group(0)


# --- Contenido y orden ---


def test_los_textos_aparecen_en_el_orden_del_spec(pagina):
    cuerpo = pagina[pagina.index("<body") :]
    desde = 0
    for texto in TEXTOS_EN_ORDEN:
        posicion = cuerpo.find(texto, desde)
        assert posicion >= 0, f"«{texto}» no aparece después del texto anterior"
        desde = posicion + len(texto)


def test_el_titulo_de_la_pagina_y_el_idioma(pagina):
    assert "<title>Ingresar · I.E. Virgen del Carmen</title>" in pagina
    assert '<html lang="es-PE"' in pagina
    assert '<meta name="color-scheme" content="light dark">' in pagina


def test_el_nombre_de_la_ie_es_el_unico_h1(pagina):
    assert re.findall(r"<h1\b[^>]*>(.*?)</h1>", pagina, re.DOTALL) == ["I.E. Virgen del Carmen"]


def test_sin_escudo_ni_menu_ni_enlaces(pagina):
    assert "<img" not in pagina
    assert "<nav" not in pagina
    assert 'class="barra' not in pagina
    assert "<a " not in pagina, "no hay enlaces: ni de recuperación ni a funciones que no existen"


def test_usuario_y_contrasena_tienen_etiqueta_y_autocompletado(pagina):
    assert '<label class="campo__etiqueta" for="id_username">Usuario</label>' in pagina
    assert '<label class="campo__etiqueta" for="id_password">Contraseña</label>' in pagina
    usuario = etiqueta(pagina, 'name="username"')
    assert 'id="id_username"' in usuario
    assert 'autocomplete="username"' in usuario
    clave = etiqueta(pagina, 'name="password"')
    assert 'id="id_password"' in clave
    assert 'type="password"' in clave
    assert 'autocomplete="current-password"' in clave


def test_el_formulario_envia_por_post_con_token_y_next(client):
    html = client.get(f"{INGRESAR}?next=/docente/").content.decode()

    assert re.search(r'<form\b[^>]*method="post"', html)
    assert 'name="csrfmiddlewaretoken"' in html
    assert 'name="next" value="/docente/"' in html


# --- Mensaje de error ---


def test_el_error_va_sobre_la_tarjeta_con_role_alert_y_dos_lineas(pagina_rechazada):
    alerta = re.search(r'<div[^>]*role="alert".*?</div>\s*</div>', pagina_rechazada, re.DOTALL)
    assert alerta, "no hay un mensaje con role=alert"
    lineas = re.findall(r"<p>(.*?)</p>", alerta.group(0), re.DOTALL)

    assert lineas == [LINEA_1, LINEA_2]
    assert alerta.start() < pagina_rechazada.index("<form")
    assert "<svg" in alerta.group(0)


def test_sin_rechazo_no_hay_mensaje(pagina):
    assert 'role="alert"' not in pagina


def test_el_error_conserva_el_usuario_y_no_la_contrasena(pagina_rechazada):
    assert 'value="ana.quispe"' in pagina_rechazada
    assert CLAVE_INCORRECTA not in pagina_rechazada


def test_campos_vacios_marcan_cada_campo_y_lo_enlazan_a_su_mensaje(pagina_con_campos_vacios):
    for campo, mensaje in [
        ("username", "Ingresa tu usuario."),
        ("password", "Ingresa tu contraseña."),
    ]:
        control = etiqueta(pagina_con_campos_vacios, f'name="{campo}"')
        assert 'aria-invalid="true"' in control
        assert f'aria-describedby="id_{campo}_error"' in control
        assert re.search(
            rf'<p class="campo__error" id="id_{campo}_error">.*?<span>{mensaje}</span>',
            pagina_con_campos_vacios,
            re.DOTALL,
        )
    assert 'role="alert"' not in pagina_con_campos_vacios


def test_sin_errores_los_campos_no_se_marcan_invalidos(pagina):
    assert "aria-invalid" not in pagina
    assert "aria-describedby" not in pagina


# --- Mostrar contraseña (sin JavaScript no aparece) ---


def test_el_boton_mostrar_contrasena_nace_oculto_y_sin_presionar(pagina):
    boton = etiqueta(pagina, "data-mostrar-clave")

    assert re.search(r"\bhidden\b", boton)
    assert 'aria-pressed="false"' in boton
    assert 'aria-label="Mostrar contraseña"' in boton
    assert 'aria-controls="id_password"' in boton
    assert 'type="button"' in boton


# --- Anuncio del envío (C8-01) ---


def test_el_anuncio_del_envio_es_una_region_status_vacia_oculta_y_fuera_del_formulario(pagina):
    region = re.search(r'<p\b[^>]*role="status"[^>]*>(.*?)</p>', pagina, re.DOTALL)
    assert region, "no hay una región role=status"

    assert region.group(1) == "", "la región nace vacía: el texto lo escribe ingresar.js al enviar"
    assert "data-estado-ingreso" in region.group(0)
    assert "sr-only" in region.group(0)
    assert region.start() > pagina.index("</form>"), "fuera del formulario que lleva aria-busy"
    assert "Ingresando" not in pagina


# --- Scripts (D6) ---


def test_carga_ingresar_js_pero_no_alpine_ni_htmx(pagina):
    scripts = re.findall(r"<script\b[^>]*>", pagina, re.IGNORECASE)

    assert len(scripts) == 1
    assert "js/ingresar.js" in scripts[0]
    assert "defer" in scripts[0]
    assert "alpine" not in pagina.lower()
    assert "htmx" not in pagina.lower()


# --- Marco común: barra sin menú y pie (portada y dirección) ---

PORTADA = "/docente/"
INICIO_DIRECCION = "/direccion/"
SUBTITULOS = [
    "Planificación de sesiones de aprendizaje",
    "Registro y control de notas",
    "Control de asistencia",
]
VACIO_DIRECCION = "Los consolidados de notas y asistencia estarán aquí en una próxima versión."


@pytest.fixture
def portada(client, docente):
    client.force_login(docente)
    return client.get(PORTADA).content.decode()


@pytest.fixture
def inicio_direccion(client, direccion):
    client.force_login(direccion)
    return client.get(INICIO_DIRECCION).content.decode()


def tarjetas(html):
    encontradas = re.findall(r"<article\b.*?</article>", html, re.DOTALL)
    assert len(encontradas) == 3, "la portada lleva tres tarjetas"
    return encontradas


def saludos(html):
    return re.findall(r"<h1\b[^>]*>(.*?)</h1>", html, re.DOTALL)


def barra(html):
    encontrada = re.search(r"<header\b.*?</header>", html, re.DOTALL)
    assert encontrada, "no hay barra superior"
    return encontrada.group(0)


@pytest.mark.parametrize("pantalla", ["portada", "inicio_direccion"])
def test_barra_con_el_nombre_de_la_ie_y_solo_el_menu_de_la_cuenta(pantalla, request):
    html = request.getfixturevalue(pantalla)
    cabecera = barra(html)

    assert "I.E. Virgen del Carmen" in cabecera
    # US-002: el menú de la cuenta es lo único interactivo; no hay navegación ni enlaces.
    for control in ("<nav", "<a "):
        assert control not in cabecera
    assert cabecera.count("<details") == 1
    assert html.index(cabecera) < html.index("<main")


@pytest.mark.parametrize("pantalla", ["portada", "inicio_direccion"])
def test_pie_al_final_y_titulo_de_la_pagina(pantalla, request):
    html = request.getfixturevalue(pantalla)
    pie = re.search(r"<footer\b.*?</footer>", html, re.DOTALL)

    assert pie and "CarpetaDocente · 2026" in pie.group(0)
    assert pie.start() > html.index("</main>")
    assert "<title>Inicio · CarpetaDocente</title>" in html


# --- Portada del docente ---


def test_la_portada_saluda_con_el_nombre_completo(portada):
    assert saludos(portada) == ["Hola, Ana Quispe"]


def test_sin_nombre_la_portada_saluda_con_el_usuario(client, crear_usuario):
    client.force_login(crear_usuario("docente.sin.nombre", Usuario.Rol.DOCENTE))

    assert saludos(client.get(PORTADA).content.decode()) == ["Hola, docente.sin.nombre"]


def test_la_portada_no_inventa_grado_ni_tratamiento(portada):
    """D8: sin "Prof." ni "3.° grado, sección A" hasta que exista el dato."""
    assert "Prof." not in portada
    assert "grado" not in portada


def test_tres_tarjetas_en_orden_con_subtitulo_e_insignia(portada):
    for tarjeta, titulo, subtitulo in zip(
        tarjetas(portada), ["Sesiones", "Notas", "Asistencia"], SUBTITULOS, strict=True
    ):
        assert re.search(rf"<h2\b[^>]*>.*?>{titulo}</button></h2>", tarjeta, re.DOTALL)
        assert f'<p class="dimension__subtitulo">{subtitulo}</p>' in tarjeta
        assert re.search(r'<p class="insignia" id="[^"]+">Próximamente</p>', tarjeta)
        assert "dimension--proxima" in tarjeta


def test_las_tarjetas_proximamente_son_botones_sin_enlace(portada):
    for tarjeta in tarjetas(portada):
        assert "href" not in tarjeta
        assert "<a " not in tarjeta
        boton = etiqueta(tarjeta, 'class="dimension__boton"')
        assert 'type="button"' in boton
        assert 'aria-disabled="true"' in boton
        insignia = re.search(r'<p class="insignia" id="([^"]+)"', tarjeta).group(1)
        assert f'aria-describedby="{insignia}"' in boton


def test_cada_tarjeta_proximamente_tiene_su_region_aria_live_vacia(portada):
    for tarjeta in tarjetas(portada):
        assert re.search(r'<p class="dimension__aviso" aria-live="polite"[^>]*></p>', tarjeta)


def test_la_miniatura_es_esquematica_y_oculta_al_lector(portada):
    for tarjeta, clave in zip(tarjetas(portada), ["sesiones", "notas", "asistencia"], strict=True):
        ficha = etiqueta(tarjeta, f'class="ficha ficha--{clave}"')
        assert 'aria-hidden="true"' in ficha


def test_chips_accesos_y_carrusel_tus_accesos(portada):
    nav = re.search(r'<nav class="chips" aria-label="Accesos">.*?</nav>', portada, re.DOTALL)
    assert nav, "no hay una fila de chips llamada Accesos"
    chips = re.findall(r'<a class="chip" href="#([^"]+)"[^>]*>(.*?)</a>', nav.group(0), re.DOTALL)

    assert [destino for destino, _ in chips] == ["c-sesiones", "c-notas", "c-asistencia"]
    for _, texto in chips:
        assert '<span class="sr-only">: ver tarjeta</span>' in texto
    carrusel = etiqueta(portada, 'aria-label="Tus accesos"')
    assert 'role="region"' in carrusel
    assert 'tabindex="0"' in carrusel
    assert [re.search(r'id="([^"]+)"', t).group(1) for t in tarjetas(portada)] == [
        "c-sesiones",
        "c-notas",
        "c-asistencia",
    ]


def test_los_puntos_son_tres_y_decorativos(portada):
    puntos = re.search(r'<div class="puntos" aria-hidden="true">.*?</div>', portada, re.DOTALL)

    assert puntos
    assert puntos.group(0).count('class="punto"') == 3


def test_sin_ninguna_disponible_la_tarjeta_inicial_es_sesiones(portada):
    iniciales = [t for t in tarjetas(portada) if "carrusel__item--inicial" in t]

    assert len(iniciales) == 1
    assert 'id="c-sesiones"' in iniciales[0]


def test_la_portada_carga_portada_js_antes_de_alpine(portada):
    scripts = re.findall(r"<script\b[^>]*>", portada, re.IGNORECASE)

    # menu.js es el del menú de la cuenta (US-002) y no depende de Alpine.
    assert len(scripts) == 3
    assert "js/portada.js" in scripts[0]
    assert "dist/vendor/alpine.min.js" in scripts[1]
    assert "js/menu.js" in scripts[2]
    assert all("defer" in script for script in scripts)
    assert "htmx" not in portada.lower()


def test_una_dimension_disponible_enlaza_a_su_pantalla(client, docente, monkeypatch):
    """Escenario "Dimensión activada por su historia", con una ruta que existe en vez de la suya."""
    sesiones, notas, asistencia = dimensiones.DIMENSIONES
    activa = replace(asistencia, disponible=True, url_name="docente:portada")
    monkeypatch.setattr(dimensiones, "DIMENSIONES", (sesiones, notas, activa))
    client.force_login(docente)

    html = client.get(PORTADA).content.decode()
    tarjeta = tarjetas(html)[2]

    enlace = etiqueta(tarjeta, 'class="dimension__enlace"')
    assert 'href="/docente/"' in enlace
    assert 'aria-describedby="acc-asistencia"' in enlace
    assert '<p class="dimension__accion" id="acc-asistencia">Registrar asistencia' in tarjeta
    assert "Próximamente" not in tarjeta
    assert "dimension--proxima" not in tarjeta
    assert "aria-live" not in tarjeta
    assert "carrusel__item--inicial" in tarjeta
    assert len(re.findall(r'<a class="dimension__enlace"', html)) == 1


# --- Inicio de la dirección ---


def test_la_direccion_saluda_y_muestra_el_estado_vacio(inicio_direccion):
    assert saludos(inicio_direccion) == ["Hola, Rosa Huamán"]
    assert re.search(r'<p class="[^"]*">Dirección</p>', inicio_direccion)
    seccion = re.search(r"<section\b.*?</section>", inicio_direccion, re.DOTALL)
    assert seccion, "no hay sección de consolidados"
    assert re.search(r"<h2\b[^>]*>Consolidados</h2>", seccion.group(0))
    assert VACIO_DIRECCION in seccion.group(0)
    assert "<svg" in seccion.group(0)


def test_la_direccion_no_muestra_tablas_ni_tarjetas_ni_scripts(inicio_direccion):
    assert "<table" not in inicio_direccion
    assert "<article" not in inicio_direccion
    # El único script es el del menú de la cuenta (D5): la dirección no carga Alpine ni portada.js.
    assert re.findall(r'<script src="([^"]+)"', inicio_direccion) == ["/static/js/menu.js"]


# --- Menú de la cuenta (spec cierre-sesion, "Menú de la cuenta"; design.md de US-002, D5) ---


def menu(html):
    encontrado = re.search(r"<details\b[^>]*data-menu-cuenta[^>]*>.*?</details>", html, re.DOTALL)
    assert encontrado, "la barra no tiene el menú de la cuenta"
    return encontrado.group(0)


@pytest.mark.parametrize(
    ("ruta", "nombre"), [("/docente/", "Ana Quispe"), ("/direccion/", "Rosa Huamán")]
)
def test_la_barra_lleva_el_menu_con_el_nombre_y_cerrar_sesion(
    client, docente, direccion, ruta, nombre
):
    client.force_login(docente if ruta == "/docente/" else direccion)
    html = client.get(ruta).content.decode()

    assert menu(html) in barra(html)
    assert re.search(r"<summary\b[^>]*aria-label=\"Menú de la cuenta\"", menu(html))
    assert nombre in menu(html)
    formulario = re.search(r"<form\b[^>]*>.*?</form>", menu(html), re.DOTALL).group(0)
    assert re.search(r'<form\b[^>]*method="post"', formulario)
    assert 'action="/salir/"' in formulario
    assert 'name="csrfmiddlewaretoken"' in formulario
    assert re.search(r"<button\b[^>]*>.*?Cerrar sesión.*?</button>", formulario, re.DOTALL)


def test_el_menu_muestra_el_usuario_si_no_tiene_nombre(client, crear_usuario):
    sin_nombre = crear_usuario("sin.nombre", Usuario.Rol.DOCENTE)
    client.force_login(sin_nombre)

    html = client.get("/docente/").content.decode()

    assert "sin.nombre" in menu(html)


def test_el_menu_carga_menu_js_y_los_iconos_de_la_cuenta(client, docente):
    client.force_login(docente)
    html = client.get("/docente/").content.decode()

    assert '<script src="/static/js/menu.js" defer>' in html
    assert menu(html).count("<svg") == 2


def test_ingresar_no_lleva_menu(pagina):
    assert "data-menu-cuenta" not in pagina


# --- Aviso de inactividad (spec cierre-sesion, "Aviso de cierre por inactividad"; D4) ---

AVISO_1 = "Tu sesión se cerró por inactividad."
AVISO_2 = "Pasaron 60 minutos sin uso. Ingresa de nuevo para continuar."


def aviso(html):
    encontrado = re.search(r"<div\b[^>]*mensaje--aviso[^>]*>.*?</div>\s*</div>", html, re.DOTALL)
    return encontrado.group(0) if encontrado else None


@pytest.fixture
def pagina_por_inactividad(client, docente):
    client.force_login(docente)
    sesion = client.session
    sesion["ultima_actividad"] = 0
    sesion.save()
    return client.get("/docente/", follow=True).content.decode()


def test_el_aviso_va_sobre_el_formulario_con_icono_y_dos_lineas(pagina_por_inactividad):
    html = pagina_por_inactividad

    caja = aviso(html)
    assert caja, "no hay aviso de inactividad"
    assert re.findall(r"<p>(.*?)</p>", caja, re.DOTALL) == [AVISO_1, AVISO_2]
    assert "<svg" in caja
    assert 'role="status"' in etiqueta(caja, "mensaje--aviso")
    assert 'role="alert"' not in caja
    assert html.index("mensaje--aviso") < html.index("<form")


def test_el_aviso_no_se_repite_al_recargar(client, pagina_por_inactividad):
    assert aviso(pagina_por_inactividad)

    assert aviso(client.get(INGRESAR).content.decode()) is None


def test_sin_inactividad_no_hay_aviso(pagina, client, docente, clave):
    assert aviso(pagina) is None

    client.post(INGRESAR, {"username": "ana.quispe", "password": clave})
    client.post("/salir/")
    assert aviso(client.get(INGRESAR).content.decode()) is None


def test_un_envio_tras_la_inactividad_muestra_el_aviso(client, docente):
    client.force_login(docente)
    sesion = client.session
    sesion["ultima_actividad"] = 0
    sesion.save()

    html = client.post("/salir/", follow=True).content.decode()

    assert aviso(html)
