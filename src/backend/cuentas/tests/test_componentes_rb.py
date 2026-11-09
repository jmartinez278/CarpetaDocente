"""Componentes del rebrand: botón, campo y mensaje (rebrand-base, D8; decisión 11).

Se pintan con ``render_to_string`` y se revisa el HTML: elemento, clases del prototipo y
atributos de accesibilidad. Cómo se ven está en ``rebrand/componentes.css``.
"""

import re

import pytest
from django import forms
from django.template.loader import render_to_string


def boton(**contexto):
    return render_to_string("rb/boton.html", contexto).strip()


def campo(**contexto):
    return render_to_string("rb/campo.html", contexto).strip()


def mensaje(**contexto):
    return render_to_string("rb/mensaje.html", contexto).strip()


def clases(html, etiqueta):
    encontrado = re.search(rf'<{etiqueta}\b[^>]*class="([^"]*)"', html)
    assert encontrado, f"no hay <{etiqueta}> con clase"
    return encontrado.group(1).split()


# --- Botón ---


def test_boton_con_href_es_un_enlace():
    html = boton(texto="Volver a tu inicio", href="/docente/", variante="principal")

    assert html.startswith("<a ")
    assert 'href="/docente/"' in html
    assert "Volver a tu inicio" in html
    assert "<button" not in html
    assert "type=" not in html


def test_boton_sin_href_es_un_boton_de_tipo_button():
    html = boton(texto="Guardar")

    assert html.startswith("<button ")
    assert 'type="button"' in html
    assert "href=" not in html


def test_boton_puede_ser_de_envio():
    assert 'type="submit"' in boton(texto="Guardar", tipo="submit")


@pytest.mark.parametrize(
    ("variante", "clase"),
    [("principal", "btn--primary"), ("secundario", "btn--secondary"), ("texto", "btn--text")],
)
def test_boton_variantes(variante, clase):
    html = boton(texto="Hacer", variante=variante)

    assert clases(html, "button")[:2] == ["btn", clase]


def test_boton_sin_variante_es_secundario():
    assert "btn--secondary" in clases(boton(texto="Hacer"), "button")


def test_boton_con_icono_decorativo():
    html = boton(texto="Siguiente", icono="arrow-right")

    svg = re.search(r"<svg\b[^>]*>", html).group(0)
    assert 'aria-hidden="true"' in svg
    assert 'focusable="false"' in svg
    # El nombre accesible es el texto, no el ícono.
    assert "aria-label" not in html
    assert "Siguiente" in html


def test_boton_sin_icono_no_trae_svg():
    assert "<svg" not in boton(texto="Hacer")


def test_boton_suma_clases_propias():
    assert "btn--ancho" in clases(boton(texto="Hacer", clase="btn--ancho"), "button")


# --- Campo ---


class Formulario(forms.Form):
    nombre = forms.CharField(label="Nombre de la sesión")


def campo_de(datos=None, **contexto):
    formulario = Formulario(datos) if datos is not None else Formulario()
    if datos is not None:
        formulario.is_valid()
    return campo(campo=formulario["nombre"], **contexto)


def test_campo_etiqueta_asociada_al_control():
    html = campo_de()

    assert '<label for="id_nombre"' in html
    assert "Nombre de la sesión</label>" in html
    assert 'id="id_nombre"' in html
    assert 'name="nombre"' in html
    assert "placeholder" not in html


def test_campo_sin_ayuda_ni_error_no_trae_describedby_ni_invalid():
    html = campo_de()

    assert "aria-describedby" not in html
    assert "aria-invalid" not in html


def test_campo_con_ayuda_en_describedby():
    html = campo_de(ayuda="De 3 a 120 caracteres.")

    assert 'aria-describedby="id_nombre_ayuda"' in html
    assert re.search(r'id="id_nombre_ayuda"[^>]*>De 3 a 120 caracteres\.<', html)
    assert "aria-invalid" not in html


def test_campo_con_error_en_describedby_e_invalid():
    html = campo_de(datos={})

    assert 'aria-invalid="true"' in html
    assert 'aria-describedby="id_nombre_error"' in html
    assert re.search(r'id="id_nombre_error"', html)
    assert "Este campo es obligatorio." in html


def test_campo_con_ayuda_y_error_los_nombra_a_los_dos():
    html = campo_de(datos={}, ayuda="De 3 a 120 caracteres.")

    assert 'aria-describedby="id_nombre_ayuda id_nombre_error"' in html


def test_campo_conserva_el_valor():
    html = campo_de(datos={"nombre": "Fracciones"})

    assert 'value="Fracciones"' in html
    assert "aria-invalid" not in html


def test_campo_clases_del_prototipo():
    html = campo_de()

    assert "field" in clases(html, "div")
    assert "input" in clases(html, "input")


# --- Mensaje ---


@pytest.mark.parametrize(
    ("tipo", "clase"),
    [("aviso", "message--aviso"), ("error", "message--error"), ("exito", "message--exito")],
)
def test_mensaje_tipos(tipo, clase):
    html = mensaje(tipo=tipo, titulo="Título", texto="Texto")

    assert clases(html, "div")[:2] == ["message", clase]


def test_mensaje_titulo_texto_e_icono_decorativo():
    html = mensaje(tipo="aviso", titulo="Revisa la fecha", texto="La sesión es de mañana.")

    assert "Revisa la fecha" in html
    assert "<p>La sesión es de mañana.</p>" in html
    svg = re.search(r"<svg\b[^>]*>", html).group(0)
    assert 'aria-hidden="true"' in svg


def test_mensaje_sin_alerta_no_trae_role():
    assert "role=" not in mensaje(tipo="error", titulo="Título", texto="Texto")


def test_mensaje_con_alerta_trae_role_alert():
    html = mensaje(tipo="error", titulo="Título", texto="Texto", alerta=True)

    assert re.match(r'<div\b[^>]*role="alert"', html)


def test_mensaje_titulo_como_encabezado_si_se_pide():
    html = mensaje(tipo="error", titulo="No tienes permiso", texto="Texto", nivel=1)

    assert re.search(r"<h1\b[^>]*>No tienes permiso</h1>", html)


def test_mensaje_titulo_sin_nivel_no_es_encabezado():
    html = mensaje(tipo="aviso", titulo="Título", texto="Texto")

    assert not re.search(r"<h\d", html)
    assert "Título" in html
