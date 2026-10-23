"""Pantalla de inicio de sesión (spec pantallas-de-inicio; design.md de US-001, D5, D6 y D8).

Comprueba el contenido y la estructura de ``/ingresar/``. El aspecto (tokens, temas, anchos)
se revisa en el navegador y con axe en el grupo 8.
"""

import re

import pytest

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


# --- Scripts (D6) ---


def test_carga_ingresar_js_pero_no_alpine_ni_htmx(pagina):
    scripts = re.findall(r"<script\b[^>]*>", pagina)

    assert len(scripts) == 1
    assert "js/ingresar.js" in scripts[0]
    assert "defer" in scripts[0]
    assert "alpine" not in pagina.lower()
    assert "htmx" not in pagina.lower()
