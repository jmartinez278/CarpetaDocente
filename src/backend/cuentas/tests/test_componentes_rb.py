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


def test_mensaje_sin_texto_solo_trae_el_titulo():
    html = mensaje(tipo="aviso", titulo="Activa JavaScript.")

    assert re.findall(r"<p\b[^>]*>", html) == ['<p class="message-titulo">']


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


# --- Botón con datos (rebrand-us-010, D1) ---


def test_boton_con_datos_pone_el_atributo_data():
    html = boton(texto="Subir una sesión", datos="abrir-subir")

    assert re.match(r"<button\b[^>]*\sdata-abrir-subir(\s|>|=)", html)


def test_boton_con_datos_tambien_en_el_enlace():
    html = boton(texto="Ir", href="/x/", datos="ir")

    assert re.match(r"<a\b[^>]*\sdata-ir(\s|>|=)", html)


def test_boton_sin_datos_no_trae_atributos_data():
    assert "data-" not in boton(texto="Hacer")
    assert "data-" not in boton(texto="Ir", href="/x/")


# --- Botón con formulario (rebrand-us-006, D5; E-05) ---


def test_boton_con_formulario_pone_el_atributo_form():
    html = boton(texto="Importar", tipo="submit", formulario="form-x", variante="principal")

    assert re.match(r'<button\b[^>]*\stype="submit" form="form-x">', html)


def test_boton_sin_formulario_no_cambia():
    assert boton(texto="Guardar", tipo="submit", variante="principal") == (
        '<button class="btn btn--primary" type="submit">Guardar</button>'
    )


def test_boton_con_href_ignora_formulario():
    html = boton(texto="Ir", href="/x/", formulario="form-x")

    assert html == '<a class="btn btn--secondary" href="/x/">Ir</a>'


# --- Diálogo (rebrand-us-010, D3) ---


def dialogo(**contexto):
    base = {
        "id": "subir",
        "titulo": "Subir una sesión",
        "titulo_id": "subir-titulo",
        "variante": "hoja",
        "cuerpo": "rb/mensaje.html",
        "pie": "rb/boton.html",
        "tipo": "aviso",
        "texto": "Texto del cuerpo",
        "datos": "pie-marca",
    }
    base.update(contexto)
    return render_to_string("rb/dialogo.html", base).strip()


def etiqueta_apertura(html, etiqueta):
    encontrado = re.search(rf"<{etiqueta}\b[^>]*>", html)
    assert encontrado, f"no hay <{etiqueta}>"
    return encontrado.group(0)


@pytest.mark.parametrize(
    ("variante", "clase"), [("hoja", "dialog--hoja"), ("chico", "dialog--chico")]
)
def test_dialogo_variantes(variante, clase):
    html = dialogo(variante=variante)

    assert html.startswith("<dialog ")
    assert clases(html, "dialog")[:2] == ["dialog", clase]
    assert 'id="subir"' in etiqueta_apertura(html, "dialog")


def test_dialogo_nombrado_por_su_titulo():
    html = dialogo()

    assert 'aria-labelledby="subir-titulo"' in etiqueta_apertura(html, "dialog")
    titulo = etiqueta_apertura(html, "h2")
    assert 'id="subir-titulo"' in titulo
    assert 'tabindex="-1"' in titulo
    assert "Subir una sesión</h2>" in html


def test_dialogo_sin_descripcion_no_trae_describedby():
    assert "aria-describedby" not in dialogo()


def test_dialogo_con_descripcion_en_describedby():
    html = dialogo(descripcion="Tu envío llega a la dirección.", descripcion_id="subir-desc")

    assert 'aria-describedby="subir-desc"' in etiqueta_apertura(html, "dialog")
    assert re.search(r'id="subir-desc"[^>]*>Tu envío llega a la dirección\.<', html)


def test_dialogo_descrito_por_el_cuerpo_sin_parrafo_en_la_cabecera():
    html = dialogo(descrito_por="texto-salida")

    assert 'aria-describedby="texto-salida"' in etiqueta_apertura(html, "dialog")
    assert '<p class="small"' not in html


def test_dialogo_sin_descrito_por_no_cambia():
    con_descripcion = dialogo(descripcion="Tu envío.", descripcion_id="d")

    assert 'aria-describedby="d"' in con_descripcion
    assert dialogo() == dialogo(descrito_por="")


def test_dialogo_cuerpo_alcanzable_con_teclado_y_con_nombre():
    html = dialogo()

    cuerpo = re.search(r'<div\b[^>]*class="[^"]*\bdialog-cuerpo\b[^"]*"[^>]*>', html).group(0)
    assert 'tabindex="0"' in cuerpo
    assert 'role="region"' in cuerpo
    assert 'aria-labelledby="subir-titulo"' in cuerpo
    assert "Texto del cuerpo" in html


def test_dialogo_data_cuerpo_solo_si_se_pide():
    assert "data-cuerpo" not in dialogo()
    assert "data-cuerpo" in dialogo(marca_cuerpo=True)


def test_dialogo_pie_despues_del_cuerpo():
    html = dialogo()

    assert html.index("Texto del cuerpo") < html.index("data-pie-marca")
    assert html.index("dialog-pie") < html.index("data-pie-marca")


def test_dialogo_cerrado_sin_x_ni_hex_ni_style():
    html = dialogo()

    assert "open" not in etiqueta_apertura(html, "dialog").split()
    assert not re.search(r"\bopen\b", etiqueta_apertura(html, "dialog"))
    assert "<svg" not in html.split("dialog-cuerpo")[0]  # cabecera sin ✕
    assert "style=" not in html
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b", html)


# --- Estado vacío (rebrand-us-010, D6) ---


def estado_vacio(**contexto):
    base = {"icono": "inbox", "texto": "Aquí verás las sesiones que envíes y su estado."}
    base.update(contexto)
    return render_to_string("rb/estado_vacio.html", base).strip()


def test_estado_vacio_trae_icono_decorativo_y_texto():
    html = estado_vacio()

    assert "empty" in clases(html, "div")
    assert 'aria-hidden="true"' in html
    assert html.index("<svg") < html.index("Aquí verás las sesiones")
    assert "Aquí verás las sesiones que envíes y su estado." in html


def test_estado_vacio_sin_accion_no_trae_enlace_ni_boton():
    html = estado_vacio()

    assert "<a " not in html
    assert "<button" not in html


def test_estado_vacio_con_href_trae_un_enlace():
    html = estado_vacio(accion="Ir a la portada", href="/inicio/")

    assert re.search(r'<a\b[^>]*href="/inicio/"[^>]*>Ir a la portada</a>', html)
    assert "<button" not in html


def test_estado_vacio_con_datos_trae_un_boton_con_el_atributo():
    html = estado_vacio(accion="Subir una sesión", datos="abrir-subir")

    assert re.search(r"<button\b[^>]*data-abrir-subir[^>]*>Subir una sesión</button>", html)
    assert "<a " not in html


def test_estado_vacio_con_titulo_lo_pinta_antes_del_texto():
    html = estado_vacio(
        titulo="Hoy no hay clases", texto="La asistencia se registra de lunes a viernes."
    )

    assert '<p class="empty-titulo">Hoy no hay clases</p><p>La asistencia' in html
    assert html.index("<svg") < html.index("Hoy no hay clases")


def test_estado_vacio_sin_titulo_no_cambia():
    icono = render_to_string("iconos/inbox.svg", {"clase": "empty-icono"})

    assert estado_vacio() == (
        f'<div class="empty">{icono}<p>Aquí verás las sesiones que envíes y su estado.</p></div>'
    )


def test_estado_vacio_sin_hex_ni_style():
    html = estado_vacio(accion="Subir", datos="x")

    assert "style=" not in html
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b", html)


# --- Ingreso del rebrand (rebrand-us-001, D3) ---


class FormularioIngreso(forms.Form):
    username = forms.CharField(label="Usuario")
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput)


def campo_de_ingreso(nombre, datos=None, **contexto):
    formulario = FormularioIngreso(datos)
    if datos is not None:
        formulario.is_valid()
    return campo(campo=formulario[nombre], **contexto)


def test_campo_con_mostrar_clave_envuelve_el_input_y_trae_el_ojo():
    html = campo_de_ingreso("password", mostrar_clave=True)

    assert re.search(r'<div class="input-grupo">\s*<input\b', html)
    ojo = etiqueta_apertura(html, "button")
    assert 'type="button"' in ojo
    assert "data-mostrar-clave" in ojo
    assert 'aria-controls="id_password"' in ojo
    assert 'aria-pressed="false"' in ojo
    assert 'aria-label="Mostrar contraseña"' in ojo
    assert re.search(r"\shidden(\s|>)", ojo)
    iconos = re.findall(r"<svg\b[^>]*>", html)
    assert len(iconos) == 2
    assert all('aria-hidden="true"' in icono for icono in iconos)


def test_campo_con_mostrar_clave_nunca_reescribe_la_contraseña():
    html = campo_de_ingreso("password", datos={"password": "secreta"}, mostrar_clave=True)

    assert "value=" not in etiqueta_apertura(html, "input")
    assert "secreta" not in html


def test_campo_con_variante_ingreso_lleva_field_ingreso():
    html = campo_de_ingreso("username", variante="ingreso")

    assert "field--ingreso" in clases(html, "div")


def test_campo_con_sin_correccion_apaga_mayusculas_y_corrector():
    html = campo_de_ingreso("username", sin_correccion=True)

    entrada = etiqueta_apertura(html, "input")
    assert 'autocapitalize="none"' in entrada
    assert 'spellcheck="false"' in entrada


def test_campo_sin_los_parametros_nuevos_queda_como_antes():
    html = campo_de()

    assert "input-grupo" not in html
    assert "<button" not in html
    assert "<svg" not in html
    assert "field--ingreso" not in html
    assert clases(html, "div") == ["field"]
    assert "autocapitalize" not in html
    assert "spellcheck" not in html


# --- Mensaje con ícono y foco (rebrand-us-001, D2 y D3) ---


def test_mensaje_con_icono_usa_ese_icono():
    from django.template.loader import render_to_string as pintar

    reloj = pintar("iconos/clock.svg", {"clase": None}).strip()
    alerta = pintar("iconos/circle-alert.svg", {"clase": None}).strip()
    html = mensaje(tipo="aviso", titulo="T", texto="X", icono="clock")

    assert reloj in html
    assert alerta not in html


def test_mensaje_sin_icono_conserva_el_de_hoy():
    from django.template.loader import render_to_string as pintar

    alerta = pintar("iconos/circle-alert.svg", {"clase": None}).strip()

    assert alerta in mensaje(tipo="error", titulo="T")


def test_mensaje_con_enfocar_trae_tabindex_y_autofocus_sin_role():
    html = mensaje(tipo="error", titulo="T", texto="X", enfocar=True, alerta=True)

    apertura = etiqueta_apertura(html, "div")
    assert 'tabindex="-1"' in apertura
    assert re.search(r"\sautofocus(\s|>)", apertura)
    assert "role=" not in html


def test_mensaje_sin_enfocar_no_trae_tabindex_ni_autofocus():
    html = mensaje(tipo="error", titulo="T", texto="X")

    assert "tabindex" not in html
    assert "autofocus" not in html


# --- Pie con solo la marca (rebrand-us-001, D3) ---


def pie(**contexto):
    return render_to_string("rb/pie.html", contexto).strip()


def test_pie_con_solo_marca_trae_un_texto_y_footer_marca():
    html = pie(solo_marca=True)

    assert "footer--marca" in clases(html, "footer")
    assert "CarpetaDocente · 2026" in html
    assert "I.E. Virgen del Carmen" not in html


def test_pie_sin_solo_marca_trae_los_dos_textos():
    html = pie()

    assert "CarpetaDocente · 2026" in html
    assert "I.E. Virgen del Carmen" in html
    assert "footer--marca" not in html


# --- Filtro partes_aviso (rebrand-us-001, D3) ---


def test_partes_aviso_parte_titulo_y_detalle():
    from cuentas.templatetags.marco import partes_aviso

    assert partes_aviso("Tu sesión se cerró.\n\nVuelve a ingresar.") == (
        "Tu sesión se cerró.",
        "Vuelve a ingresar.",
    )


def test_partes_aviso_sin_detalle_deja_el_texto_vacio():
    from cuentas.templatetags.marco import partes_aviso

    assert partes_aviso("Solo título") == ("Solo título", "")


# --- Campo y mensaje para Estudiantes (rebrand-us-006, D6) ---


class FormularioEstudiante(forms.Form):
    apellidos = forms.CharField(label="Apellidos", max_length=120)
    nombres = forms.CharField(label="Nombres")


def campo_de_estudiante(nombre, datos=None, **contexto):
    formulario = FormularioEstudiante(datos)
    if datos is not None:
        formulario.is_valid()
    return campo(campo=formulario[nombre], **contexto)


def test_campo_pinta_maxlength_desde_el_campo_de_django():
    entrada = etiqueta_apertura(campo_de_estudiante("apellidos"), "input")

    assert 'maxlength="120"' in entrada


def test_campo_sin_max_length_no_pinta_maxlength():
    entrada = etiqueta_apertura(campo_de_estudiante("nombres"), "input")

    assert "maxlength" not in entrada


def test_campo_con_autocapitalize_pinta_el_valor_y_apaga_el_corrector():
    html = campo_de_estudiante("apellidos", autocapitalize="characters")
    entrada = etiqueta_apertura(html, "input")

    assert 'autocapitalize="characters"' in entrada
    assert 'spellcheck="false"' in entrada


def test_campo_con_descrito_por_lo_suma_a_la_ayuda_y_al_error():
    html = campo_de_estudiante(
        "apellidos", datos={"apellidos": ""}, ayuda="Ayuda", descrito_por="ayuda-x"
    )

    entrada = etiqueta_apertura(html, "input")
    descrito = re.search(r'aria-describedby="([^"]*)"', entrada).group(1).split()
    assert descrito == ["id_apellidos_ayuda", "id_apellidos_error", "ayuda-x"]


def test_campo_con_descrito_por_solo_lo_nombra():
    entrada = etiqueta_apertura(campo_de_estudiante("apellidos", descrito_por="ayuda-x"), "input")

    assert 'aria-describedby="ayuda-x"' in entrada


def test_campo_con_foco_marca_solo_el_campo_indicado():
    con_foco = etiqueta_apertura(campo_de_estudiante("apellidos", foco="apellidos"), "input")
    sin_foco = etiqueta_apertura(campo_de_estudiante("nombres", foco="apellidos"), "input")

    assert re.search(r"\sdata-foco(\s|>|=)", con_foco)
    assert "data-foco" not in sin_foco


def test_campo_sin_foco_no_trae_data_foco():
    assert "data-foco" not in campo_de_estudiante("apellidos")


def test_campo_del_ingreso_no_cambia_con_los_parametros_nuevos():
    html = campo_de_ingreso("username", variante="ingreso", sin_correccion=True)

    entrada = etiqueta_apertura(html, "input")
    assert "maxlength" not in entrada
    assert "data-foco" not in entrada
    assert "aria-describedby" not in entrada
    assert entrada.count("autocapitalize") == 1


def test_mensaje_con_estado_trae_role_status():
    apertura = etiqueta_apertura(mensaje(tipo="aviso", titulo="T", estado=True), "div")

    assert 'role="status"' in apertura


def test_mensaje_con_alerta_o_enfocar_ignora_estado():
    alerta = mensaje(tipo="error", titulo="T", alerta=True, estado=True)
    enfocado = mensaje(tipo="error", titulo="T", enfocar=True, estado=True)
    con_alerta = etiqueta_apertura(alerta, "div")
    con_foco = etiqueta_apertura(enfocado, "div")

    assert 'role="alert"' in con_alerta
    assert "status" not in con_alerta
    assert "role=" not in con_foco


def test_mensaje_sin_estado_ni_alerta_no_trae_role():
    assert "role=" not in mensaje(tipo="aviso", titulo="T")
