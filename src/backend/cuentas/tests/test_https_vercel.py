"""HTTPS, hosts y cookies seguras en la nube (spec despliegue, EN-02 D5).

Las pruebas aplican con ``settings`` los mismos valores que ``config.settings`` fija
cuando corre en Vercel (``config/tests/test_settings.py`` prueba que los fija) y
revisan cómo responde Django con ellos.
"""

import pytest

HOST = "carpeta-docente-abc123-equipo.vercel.app"
PROXY_HTTPS = {"x-forwarded-proto": "https", "host": HOST}


@pytest.fixture
def modo_nube(settings):
    settings.ALLOWED_HOSTS = [HOST]
    settings.CSRF_TRUSTED_ORIGINS = [f"https://{HOST}"]
    settings.SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    settings.SECURE_SSL_REDIRECT = True
    settings.SESSION_COOKIE_SECURE = True
    settings.CSRF_COOKIE_SECURE = True


def test_fuera_de_vercel_la_pantalla_de_ingreso_no_redirige_a_https(client):
    respuesta = client.get("/ingresar/")

    assert respuesta.status_code == 200


def test_peticion_detras_del_proxy_con_https_no_se_redirige(client, modo_nube):
    respuesta = client.get("/ingresar/", headers=PROXY_HTTPS)

    assert respuesta.status_code == 200


def test_peticion_sin_la_cabecera_del_proxy_se_redirige_a_https(client, modo_nube):
    respuesta = client.get("/ingresar/", headers={"host": HOST})

    assert respuesta.status_code == 301
    assert respuesta["Location"] == f"https://{HOST}/ingresar/"


def test_host_ajeno_recibe_400(client, modo_nube):
    respuesta = client.get("/ingresar/", headers={**PROXY_HTTPS, "host": "ajeno.example.com"})

    assert respuesta.status_code == 400


def test_el_ingreso_deja_las_cookies_con_secure(client, modo_nube, docente, clave):
    respuesta = client.post(
        "/ingresar/",
        {"username": docente.username, "password": clave},
        headers=PROXY_HTTPS,
    )

    assert respuesta.status_code == 302
    assert respuesta.cookies["sessionid"]["secure"]
    assert respuesta.cookies["csrftoken"]["secure"]
