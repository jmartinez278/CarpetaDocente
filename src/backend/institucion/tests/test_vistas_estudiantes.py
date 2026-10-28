"""Pruebas de las vistas de la lista de estudiantes (spec estudiantes-seccion; design de US-006).

Acceso (D4), una respuesta para el diálogo y para la página completa (D5) y la lista vacía.
"""

import re
from urllib.parse import quote

import pytest
from django.urls import reverse

from institucion.models import AnioEscolar, Estudiante, Seccion

pytestmark = pytest.mark.django_db

HTMX = {"HTTP_HX_REQUEST": "true"}


@pytest.fixture
def seccion_docente(seccion, docente):
    seccion.docente = docente
    seccion.save()
    return seccion


def url_lista(seccion):
    return reverse("estudiantes:lista", args=[seccion.pk])


@pytest.fixture
def entrar(client):
    def entrar_como(usuario):
        client.force_login(usuario)
        return client

    return entrar_como


# --- Rutas (D4) ---


def test_la_lista_esta_bajo_la_seccion(seccion_docente):
    assert url_lista(seccion_docente) == f"/docente/secciones/{seccion_docente.pk}/estudiantes/"


@pytest.mark.parametrize(
    ("nombre", "argumentos", "ruta"),
    [
        ("agregar", [], "agregar/"),
        ("pegar", [], "pegar/"),
        ("editar", [7], "7/editar/"),
        ("quitar", [7], "7/quitar/"),
        ("vaciar", [], "vaciar/"),
    ],
)
def test_las_demas_rutas_estan_registradas(seccion_docente, nombre, argumentos, ruta):
    url = reverse(f"estudiantes:{nombre}", args=[seccion_docente.pk, *argumentos])

    assert url == f"{url_lista(seccion_docente)}{ruta}"


# --- Acceso: solo a sus secciones ---


def test_la_docente_de_la_seccion_ve_la_lista(entrar, docente, seccion_docente):
    respuesta = entrar(docente).get(url_lista(seccion_docente))

    assert respuesta.status_code == 200


def test_otra_docente_recibe_404_y_no_ve_nombres(entrar, otra_docente, seccion_docente):
    Estudiante.objects.create(seccion=seccion_docente, apellidos="QUISPE", nombres="ANA")

    respuesta = entrar(otra_docente).get(url_lista(seccion_docente))

    assert respuesta.status_code == 404
    assert "QUISPE" not in respuesta.content.decode()


def test_una_seccion_del_anio_cerrado_da_404(entrar, docente, institucion):
    cerrado = AnioEscolar.objects.create(institucion=institucion, anio=2026, estado="CERRADO")
    vieja = Seccion.objects.create(anio_escolar=cerrado, grado=2, nombre="A", docente=docente)

    assert entrar(docente).get(url_lista(vieja)).status_code == 404


def test_una_seccion_que_no_existe_da_404(entrar, docente):
    assert entrar(docente).get("/docente/secciones/999999/estudiantes/").status_code == 404


def test_la_direccion_llega_a_su_pantalla(entrar, direccion, seccion_docente):
    respuesta = entrar(direccion).get(url_lista(seccion_docente))

    assert respuesta.status_code == 302
    assert respuesta["Location"] == "/direccion/"


def test_sin_sesion_va_a_ingresar_con_next(client, seccion_docente):
    url = url_lista(seccion_docente)

    respuesta = client.get(url)

    assert respuesta.status_code == 302
    assert respuesta["Location"] == f"/ingresar/?next={quote(url)}"


# --- Una respuesta para el diálogo y para la página completa (D5) ---


def test_con_htmx_responde_el_parcial_sin_marco(entrar, docente, seccion_docente):
    html = entrar(docente).get(url_lista(seccion_docente), **HTMX).content.decode()

    assert "<html" not in html
    assert "<h1" not in html
    assert re.search(r'<h2[^>]*id="modal-titulo"[^>]*>\s*Estudiantes de 2\.º A\s*</h2>', html)


def test_con_htmx_lleva_el_aviso_de_la_portada_fuera_de_banda(entrar, docente, seccion_docente):
    html = entrar(docente).get(url_lista(seccion_docente), **HTMX).content.decode()

    aviso = re.search(r'<div[^>]*id="aviso-portada"[^>]*hx-swap-oob="true"[^>]*>', html)
    assert aviso, "falta el aviso fuera de banda"
    assert "Tu sección aún no tiene estudiantes" in html[aviso.start() :]


def test_sin_htmx_responde_la_pagina_completa_con_h1(entrar, docente, seccion_docente):
    html = entrar(docente).get(url_lista(seccion_docente)).content.decode()

    assert html.lstrip().lower().startswith("<!doctype html>")
    assert re.findall(r"<h1\b[^>]*>(.*?)</h1>", html, re.DOTALL) == ["Estudiantes de 2.º A"]
    assert "<h2" not in html.split("<main")[1]
    assert "hx-swap-oob" not in html


def test_la_pagina_completa_no_tiene_cerrar_y_vuelve_a_la_portada(entrar, docente, seccion_docente):
    html = entrar(docente).get(url_lista(seccion_docente)).content.decode()

    assert "data-cerrar" not in html
    assert 'href="/docente/"' in html
    assert "<title>Estudiantes de 2.º A · CarpetaDocente</title>" in html


# --- Lista vacía (spec "Lista vacía") ---


@pytest.mark.parametrize("cabeceras", [{}, HTMX])
def test_lista_vacia_con_sus_dos_acciones(entrar, docente, seccion_docente, cabeceras):
    html = entrar(docente).get(url_lista(seccion_docente), **cabeceras).content.decode()

    assert "Tu sección aún no tiene estudiantes." in html
    assert "0 estudiantes" in html
    principal = re.search(r'<a[^>]*class="[^"]*boton-principal[^"]*"[^>]*>(.*?)</a>', html, re.S)
    assert principal and principal.group(1).strip() == "Agregar uno por uno"
    secundario = re.search(r'<a[^>]*class="[^"]*boton-secundario[^"]*"[^>]*>(.*?)</a>', html, re.S)
    assert secundario and secundario.group(1).strip() == "Pegar lista"


def test_las_acciones_de_la_lista_vacia_son_enlaces_reales_con_hx_get(
    entrar, docente, seccion_docente
):
    html = entrar(docente).get(url_lista(seccion_docente), **HTMX).content.decode()
    agregar = reverse("estudiantes:agregar", args=[seccion_docente.pk])
    pegar = reverse("estudiantes:pegar", args=[seccion_docente.pk])

    for destino in (agregar, pegar):
        assert re.search(rf'<a[^>]*href="{destino}"[^>]*hx-get="{destino}"', html)


def test_en_el_dialogo_el_titulo_recibe_el_foco_y_hay_cerrar(entrar, docente, seccion_docente):
    html = entrar(docente).get(url_lista(seccion_docente), **HTMX).content.decode()

    titulo = re.search(r'<h2[^>]*id="modal-titulo"[^>]*>', html).group(0)
    assert "data-foco" in titulo
    assert 'tabindex="-1"' in titulo
    assert re.search(r"<button[^>]*data-cerrar[^>]*>", html)


def test_las_plantillas_no_llevan_colores_hexadecimales_ni_style():
    from pathlib import Path

    from django.conf import settings

    carpeta = Path(settings.BASE_DIR) / "templates" / "institucion" / "estudiantes"
    archivos = list(carpeta.glob("*.html"))
    assert archivos, "faltan las plantillas de la lista"
    for archivo in archivos:
        texto = archivo.read_text(encoding="utf-8")
        assert not re.search(r"#[0-9a-fA-F]{3,8}\b", texto), archivo.name
        assert "style=" not in texto, archivo.name


# --- Lista con estudiantes (el diseño completo es de la parte B) ---


@pytest.mark.parametrize("cabeceras", [{}, HTMX])
def test_la_lista_con_estudiantes_responde_200_ordenada_y_con_la_cantidad(
    entrar, docente, seccion_docente, cabeceras
):
    for apellidos, nombres in [("RAMOS HUAMÁN", "VALENTÍN"), ("AGUILAR FLORES", "LUCIANA")]:
        Estudiante.objects.create(seccion=seccion_docente, apellidos=apellidos, nombres=nombres)

    respuesta = entrar(docente).get(url_lista(seccion_docente), **cabeceras)

    html = respuesta.content.decode()
    assert respuesta.status_code == 200
    assert "2 estudiantes" in html
    assert html.index("AGUILAR FLORES, LUCIANA") < html.index("RAMOS HUAMÁN, VALENTÍN")
    assert "Tu sección aún no tiene estudiantes." not in html
