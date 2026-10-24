"""Pruebas del ingreso y de las redirecciones (spec inicio-sesion; design.md de US-001, D2 y D3).

Una prueba por escenario, con el cliente de Django y cuentas ficticias.
"""

import re

import pytest
from django.contrib.auth import SESSION_KEY

from cuentas import servicios
from cuentas.models import Usuario

pytestmark = pytest.mark.django_db

INGRESAR = "/ingresar/"
LINEA_1 = "Usuario o contraseña incorrectos, o cuenta inactiva"
LINEA_2 = "Revisa tus datos. Si el problema sigue, pide ayuda al administrador."
CLAVE_INCORRECTA = "no-es-la-clave"
# Más saltos que estos indicarían un ciclo: el más largo es /admin/ → /admin/login/ → destino.
SALTOS_MAXIMOS = 3

_ALERTA = re.compile(r'<[^>]*role="alert".*?</div>', re.DOTALL)
_TOKEN = re.compile(r'name="csrfmiddlewaretoken" value="[^"]*"')


def ingresar(client, usuario, contrasena, **extra):
    return client.post(INGRESAR, {"username": usuario, "password": contrasena, **extra})


def con_sesion(client, usuario):
    client.force_login(usuario)
    return client


def alerta(respuesta):
    encontrada = _ALERTA.search(respuesta.content.decode())
    assert encontrada, "la respuesta no tiene el mensaje con role=alert"
    return encontrada.group(0)


def pagina_sin_variables(respuesta, usuario):
    """HTML de la respuesta sin el token CSRF ni el usuario escrito, que cambian en cada caso."""
    html = _TOKEN.sub("", respuesta.content.decode())
    return html.replace(usuario, "{usuario}")


def sesion_iniciada(client):
    return SESSION_KEY in client.session


# --- Inicio de sesión único ---


@pytest.mark.parametrize(
    ("fixture", "destino"),
    [("docente", "/docente/"), ("direccion", "/direccion/"), ("administrador", "/admin/")],
)
def test_cada_rol_llega_a_su_pantalla(client, request, clave, fixture, destino):
    usuario = request.getfixturevalue(fixture)

    respuesta = ingresar(client, usuario.username, clave)

    assert respuesta.status_code == 302
    assert respuesta.url == destino
    assert client.get(destino).status_code == 200


def test_la_pantalla_de_ingreso_responde(client):
    respuesta = client.get(INGRESAR)

    assert respuesta.status_code == 200
    assert 'name="username"' in respuesta.content.decode()


# --- Mensaje genérico ante un ingreso rechazado ---


@pytest.fixture
def rechazos(client, clave, docente, crear_usuario):
    """Respuesta de cada rechazo: clave incorrecta, usuario inexistente, inactiva y bloqueada."""
    crear_usuario("inactiva.ficticia", Usuario.Rol.DOCENTE, is_active=False)
    bloqueada = crear_usuario("bloqueada.ficticia", Usuario.Rol.DOCENTE)
    for _ in range(servicios.INTENTOS_MAXIMOS):
        servicios.intentar_ingreso(bloqueada, CLAVE_INCORRECTA)

    casos = {
        "contraseña incorrecta": ("ana.quispe", CLAVE_INCORRECTA),
        "usuario inexistente": ("nadie.ficticio", CLAVE_INCORRECTA),
        "cuenta inactiva": ("inactiva.ficticia", clave),
        "cuenta bloqueada": ("bloqueada.ficticia", clave),
    }
    return {
        caso: (usuario, ingresar(client, usuario, contrasena))
        for caso, (usuario, contrasena) in casos.items()
    }


def test_los_cuatro_rechazos_dan_el_mismo_mensaje_en_dos_lineas(rechazos, client):
    mensajes = {caso: alerta(respuesta) for caso, (_, respuesta) in rechazos.items()}

    assert len(set(mensajes.values())) == 1
    mensaje = mensajes["contraseña incorrecta"]
    assert LINEA_1 in mensaje
    assert LINEA_2 in mensaje
    assert all(respuesta.status_code == 200 for _, respuesta in rechazos.values())
    assert not sesion_iniciada(client)


def test_la_pagina_no_distingue_un_rechazo_de_otro(rechazos):
    paginas = {pagina_sin_variables(respuesta, usuario) for usuario, respuesta in rechazos.values()}

    assert len(paginas) == 1
    assert LINEA_1 in paginas.pop()


def test_conserva_el_usuario_pero_no_la_contrasena(client, docente):
    html = ingresar(client, "ana.quispe", CLAVE_INCORRECTA).content.decode()

    assert 'value="ana.quispe"' in html
    assert CLAVE_INCORRECTA not in html


@pytest.mark.parametrize(
    ("usuario", "contrasena", "errores"),
    [
        ("", "", {"username": ["Ingresa tu usuario."], "password": ["Ingresa tu contraseña."]}),
        ("ana.quispe", "", {"password": ["Ingresa tu contraseña."]}),
        ("", CLAVE_INCORRECTA, {"username": ["Ingresa tu usuario."]}),
    ],
    ids=["los dos vacíos", "contraseña vacía", "usuario vacío"],
)
def test_campos_vacios_muestran_su_mensaje_sin_contar_un_intento(
    client, docente, usuario, contrasena, errores
):
    respuesta = ingresar(client, usuario, contrasena)

    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors == errores
    html = respuesta.content.decode()
    assert all(mensaje in html for lista in errores.values() for mensaje in lista)
    assert LINEA_1 not in html
    docente.refresh_from_db()
    assert docente.intentos_fallidos == 0


# --- Bloqueo temporal (escenario "Cuenta bloqueada" de US-001) ---


def test_cuenta_bloqueada_rechaza_la_contrasena_correcta_con_el_mismo_mensaje(
    client, docente, clave
):
    for _ in range(servicios.INTENTOS_MAXIMOS):
        rechazo = ingresar(client, "ana.quispe", CLAVE_INCORRECTA)
    mensaje_del_quinto = alerta(rechazo)

    respuesta = ingresar(client, "ana.quispe", clave)

    assert respuesta.status_code == 200
    assert alerta(respuesta) == mensaje_del_quinto
    assert "bloque" not in respuesta.content.decode().lower()
    assert not sesion_iniciada(client)
    docente.refresh_from_db()
    assert servicios.esta_bloqueado(docente)


# --- Parámetro next ---


def test_next_seguro_lleva_a_la_pagina_pedida(client, docente, clave):
    pedida = client.get("/docente/")
    assert pedida.url == "/ingresar/?next=/docente/"

    respuesta = ingresar(client, "ana.quispe", clave, next="/docente/")

    assert respuesta.url == "/docente/"


def test_next_externo_se_ignora(client, docente, clave):
    respuesta = ingresar(client, "ana.quispe", clave, next="https://sitio-ajeno.invalid/")

    assert respuesta.url == "/docente/"


def test_next_a_la_pantalla_de_otro_rol_termina_en_la_propia(client, direccion, clave):
    respuesta = client.post(
        INGRESAR,
        {"username": "rosa.huaman", "password": clave, "next": "/docente/"},
        follow=True,
    )

    assert respuesta.redirect_chain[-1][0] == "/direccion/"
    assert respuesta.status_code == 200


# --- Redirección de la ruta raíz y sesión ya iniciada ---


def test_ingresar_con_la_sesion_iniciada_lleva_a_su_pantalla(client, direccion):
    respuesta = con_sesion(client, direccion).get(INGRESAR)

    assert respuesta.status_code == 302
    assert respuesta.url == "/direccion/"


def test_ingresar_con_sesion_y_next_a_ingresar_no_falla(client, direccion):
    respuesta = con_sesion(client, direccion).get(INGRESAR, {"next": INGRESAR})

    assert respuesta.status_code == 302
    assert respuesta.url == "/direccion/"


def test_raiz_sin_sesion_lleva_a_ingresar(client):
    respuesta = client.get("/")

    assert respuesta.status_code == 302
    assert respuesta.url == INGRESAR


def test_raiz_con_sesion_lleva_a_su_pantalla(client, docente):
    respuesta = con_sesion(client, docente).get("/")

    assert respuesta.status_code == 302
    assert respuesta.url == "/docente/"


# --- Un solo punto de entrada: el panel ---


def test_login_del_panel_sin_sesion_lleva_a_ingresar_con_next(client):
    respuesta = client.get("/admin/login/", {"next": "/admin/"})

    assert respuesta.status_code == 302
    assert respuesta.url == "/ingresar/?next=/admin/"


def test_login_del_panel_sin_next_lleva_a_ingresar(client):
    respuesta = client.get("/admin/login/")

    assert respuesta.url == INGRESAR


def test_panel_sin_sesion_termina_en_ingresar_y_vuelve_al_panel(client, administrador, clave):
    respuesta = client.get("/admin/", follow=True)

    assert respuesta.redirect_chain[-1][0] == "/ingresar/?next=/admin/"
    assert len(respuesta.redirect_chain) <= SALTOS_MAXIMOS

    vuelta = ingresar(client, administrador.username, clave, next="/admin/")

    assert vuelta.url == "/admin/"
    assert client.get("/admin/").status_code == 200


def test_login_del_panel_con_sesion_de_administrador_lleva_al_panel(client, administrador):
    respuesta = con_sesion(client, administrador).get("/admin/login/", {"next": "/admin/cuentas/"})

    assert respuesta.status_code == 302
    assert respuesta.url == "/admin/cuentas/"


def test_login_del_panel_ignora_un_next_externo(client, administrador):
    respuesta = con_sesion(client, administrador).get(
        "/admin/login/", {"next": "https://sitio-ajeno.invalid/"}
    )

    assert respuesta.url == "/admin/"


def test_docente_en_el_panel_termina_en_su_portada_sin_ciclo(client, docente):
    respuesta = con_sesion(client, docente).get("/admin/", follow=True)

    assert respuesta.status_code == 200
    assert respuesta.redirect_chain[-1][0] == "/docente/"
    assert len(respuesta.redirect_chain) <= SALTOS_MAXIMOS


def test_administrador_sin_is_staff_recibe_403_sin_ciclo(client, crear_usuario, clave):
    """Cuenta creada a mano (create_superuser pone is_staff): el panel no la acepta."""
    crear_usuario("admin.sin.staff", Usuario.Rol.ADMINISTRADOR, is_staff=False)

    respuesta = client.post(
        INGRESAR, {"username": "admin.sin.staff", "password": clave}, follow=True
    )

    assert respuesta.status_code == 403
    assert len(respuesta.redirect_chain) <= SALTOS_MAXIMOS
