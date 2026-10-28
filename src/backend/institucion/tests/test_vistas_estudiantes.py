"""Pruebas de las vistas de la lista de estudiantes (spec estudiantes-seccion; design de US-006).

Acceso (D4), una respuesta para el diálogo y para la página completa (D5) y la lista vacía.
"""

import re
from html import unescape
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


# --- Pegar lista y Revisar lista (spec "Pegar lista" y "Errores de la lista pegada") ---

LISTA_VALIDA = "\n".join(
    f"APELLIDO{numero:02d} FICTICIO, NOMBRE{numero:02d}" for numero in range(1, 4)
)


def url_pegar(seccion):
    return reverse("estudiantes:pegar", args=[seccion.pk])


def textarea(html):
    """Contenido del cuadro de texto, sin el salto de línea inicial que el HTML descarta."""
    contenido = re.search(r'<textarea[^>]*name="lista"[^>]*>(.*?)</textarea>', html, re.S).group(1)
    return unescape(contenido.removeprefix("\n"))


def formularios(html):
    return re.findall(r"<form\b.*?</form>", html, re.S)


@pytest.mark.parametrize("cabeceras", [{}, HTMX])
def test_pegar_lista_muestra_el_cuadro_vacio_con_su_ayuda(
    entrar, docente, seccion_docente, cabeceras
):
    html = entrar(docente).get(url_pegar(seccion_docente), **cabeceras).content.decode()

    assert "Pegar lista" in html
    assert re.search(r'<label[^>]*for="lista-pegada"[^>]*>Apellidos y nombres</label>', html)
    assert textarea(html) == ""
    assert "aria-invalid" not in html
    assert "Una línea por estudiante. La coma separa apellidos y nombres. Máximo 60 líneas." in html
    assert re.search(r'<button[^>]*type="submit"[^>]*>\s*Importar\s*</button>', html)
    assert f'href="{url_lista(seccion_docente)}"' in html.split("Importar")[1]


def test_en_el_dialogo_el_foco_va_al_cuadro_de_texto(entrar, docente, seccion_docente):
    html = entrar(docente).get(url_pegar(seccion_docente), **HTMX).content.decode()

    assert re.findall(r"<[a-z0-9]+\b[^>]*data-foco[^>]*>", html) == [
        re.search(r"<textarea[^>]*>", html).group(0)
    ]


@pytest.mark.parametrize("cabeceras", [{}, HTMX])
def test_cada_formulario_lleva_su_token_csrf_y_envia_con_htmx(
    entrar, docente, seccion_docente, cabeceras
):
    html = entrar(docente).get(url_pegar(seccion_docente), **cabeceras).content.decode()

    encontrados = formularios(html)
    pegar = [f for f in encontrados if 'name="lista"' in f]
    assert len(pegar) == 1
    for formulario in pegar:
        assert 'name="csrfmiddlewaretoken"' in formulario
        assert 'method="post"' in formulario
        assert f'hx-post="{url_pegar(seccion_docente)}"' in formulario


def test_importar_una_lista_valida_redirige_con_303_y_guarda(entrar, docente, seccion_docente):
    respuesta = entrar(docente).post(url_pegar(seccion_docente), {"lista": LISTA_VALIDA})

    assert respuesta.status_code == 303
    assert respuesta["Location"] == url_lista(seccion_docente)
    assert seccion_docente.estudiantes.count() == 3


@pytest.mark.parametrize("cabeceras", [{}, HTMX])
def test_el_aviso_de_exito_se_ve_una_sola_vez(entrar, docente, seccion_docente, cabeceras):
    cliente = entrar(docente)

    respuesta = cliente.post(
        url_pegar(seccion_docente), {"lista": LISTA_VALIDA}, follow=True, **cabeceras
    )
    html = respuesta.content.decode()

    assert respuesta.redirect_chain == [(url_lista(seccion_docente), 303)]
    assert "3 estudiantes importados" in html
    assert "Revisa los nombres; puedes corregirlos con Editar" in html
    assert (
        "3 estudiantes importados" not in cliente.get(url_lista(seccion_docente)).content.decode()
    )


def test_un_estudiante_importado_va_en_singular(entrar, docente, seccion_docente):
    respuesta = entrar(docente).post(
        url_pegar(seccion_docente), {"lista": "QUISPE MAMANI, ANA"}, follow=True
    )

    html = respuesta.content.decode()
    assert "1 estudiante importado" in html
    assert "1 estudiante<" in html


def test_con_errores_responde_200_con_el_formulario_y_no_guarda(entrar, docente, seccion_docente):
    texto = "AGUILAR FLORES, LUCIANA\n, MATEO\nCRUZ HUAMÁN, SEBASTIÁN\ncruz  huamán, sebastián"

    respuesta = entrar(docente).post(url_pegar(seccion_docente), {"lista": texto}, **HTMX)

    html = respuesta.content.decode()
    assert respuesta.status_code == 200
    assert seccion_docente.estudiantes.count() == 0
    assert "Revisar lista" in html
    assert "No se guardó ningún estudiante" in html
    assert "Línea 2: faltan los apellidos" in html
    assert "Líneas 3 y 4: el mismo estudiante" in html
    assert "Escribe apellidos y nombres separados por una coma." in html
    assert "localizar-linea" not in html
    assert html.index("Línea 2") < html.index("Líneas 3 y 4")
    assert re.search(r'<div[^>]*class="mensaje mensaje--error"[^>]*role="alert"', html)
    assert len(formularios(html)) == 1
    assert 'name="csrfmiddlewaretoken"' in formularios(html)[0]


def test_con_errores_el_texto_vuelve_intacto_con_aria_invalid(entrar, docente, seccion_docente):
    texto = (
        "\n\n  AGUILAR FLORES , LUCIANA  \r\nCONDORI MAMANI DANIELA\n<b>ROJAS</b> & CÍA, ANA\n\n"
    )

    html = entrar(docente).post(url_pegar(seccion_docente), {"lista": texto}).content.decode()

    assert textarea(html) == texto
    assert re.search(r'<textarea[^>]*aria-invalid="true"', html)
    assert "<b>ROJAS</b>" not in html
    assert "Línea 4: falta la coma entre apellidos y nombres" in html


def test_en_revisar_lista_el_foco_va_al_titulo_de_la_vista(entrar, docente, seccion_docente):
    html = (
        entrar(docente)
        .post(url_pegar(seccion_docente), {"lista": "SIN COMA"}, **HTMX)
        .content.decode()
    )

    con_foco = re.findall(r"<[a-z0-9]+\b[^>]*data-foco[^>]*>", html)
    assert len(con_foco) == 1
    assert re.match(r'<h3[^>]*class="vista-titulo"[^>]*tabindex="-1"', con_foco[0])


def test_la_vista_lleva_h2_como_pagina_completa(entrar, docente, seccion_docente):
    html = entrar(docente).get(url_pegar(seccion_docente)).content.decode()

    assert re.search(r'<h2[^>]*class="vista-titulo"[^>]*>Pegar lista</h2>', html)


def test_el_texto_vacio_pide_pegar_al_menos_uno(entrar, docente, seccion_docente):
    html = entrar(docente).post(url_pegar(seccion_docente), {"lista": "\n  \n"}).content.decode()

    assert "Pega al menos un estudiante" in html
    assert seccion_docente.estudiantes.count() == 0


# --- Pegar lista solo con la sección vacía ---


@pytest.fixture
def con_un_estudiante(seccion_docente):
    return Estudiante.objects.create(seccion=seccion_docente, apellidos="QUISPE", nombres="ANA")


@pytest.mark.parametrize("cabeceras", [{}, HTMX])
def test_la_lista_con_estudiantes_no_ofrece_pegar_lista(
    entrar, docente, seccion_docente, con_un_estudiante, cabeceras
):
    html = entrar(docente).get(url_lista(seccion_docente), **cabeceras).content.decode()

    assert "Pegar lista" not in html
    assert url_pegar(seccion_docente) not in html


@pytest.mark.parametrize("cabeceras", [{}, HTMX])
def test_pegar_con_estudiantes_muestra_el_aviso_sin_el_cuadro(
    entrar, docente, seccion_docente, con_un_estudiante, cabeceras
):
    html = entrar(docente).get(url_pegar(seccion_docente), **cabeceras).content.decode()

    assert "Tu sección ya tiene estudiantes" in html
    assert "Agrega a los que falten con Agregar estudiante." in html
    assert "<textarea" not in html
    assert "Importar" not in html


def test_el_envio_a_una_seccion_con_estudiantes_no_guarda_nada(
    entrar, docente, seccion_docente, con_un_estudiante
):
    respuesta = entrar(docente).post(url_pegar(seccion_docente), {"lista": LISTA_VALIDA}, **HTMX)

    html = respuesta.content.decode()
    assert respuesta.status_code == 200
    assert seccion_docente.estudiantes.count() == 1
    assert "Tu sección ya tiene estudiantes" in html
    assert "<textarea" not in html


@pytest.fixture
def lista_de_tres(seccion_docente):
    for apellidos, nombres in [
        ("RAMOS HUAMÁN", "VALENTÍN"),
        ("ÑAUPA ROJAS", "LUIS"),
        ("ÁLVAREZ SOTO", "ANA LUCÍA"),
    ]:
        Estudiante.objects.create(seccion=seccion_docente, apellidos=apellidos, nombres=nombres)
    return list(seccion_docente.estudiantes.all())


def filas(html):
    return re.findall(r'<li class="estudiante">(.*?)</li>', html, re.S)


@pytest.mark.parametrize("cabeceras", [{}, HTMX])
def test_la_lista_numera_en_orden_con_el_nombre_completo_y_editar(
    entrar, docente, seccion_docente, lista_de_tres, cabeceras
):
    html = entrar(docente).get(url_lista(seccion_docente), **cabeceras).content.decode()

    encontradas = filas(html)
    assert len(encontradas) == 3
    esperado = ["ÁLVAREZ SOTO, ANA LUCÍA", "ÑAUPA ROJAS, LUIS", "RAMOS HUAMÁN, VALENTÍN"]
    for numero, (fila, nombre) in enumerate(zip(encontradas, esperado, strict=True), start=1):
        assert re.search(rf'class="estudiante__numero"[^>]*>{numero}</span>', fila)
        assert f'<span class="estudiante__nombre">{nombre}</span>' in fila
        editar = re.search(r'<a[^>]*class="editar-fila"[^>]*>Editar</a>', fila).group(0)
        assert f'aria-label="Editar a {nombre}"' in editar
    assert "…" not in html


def test_editar_lleva_a_la_ruta_del_estudiante(entrar, docente, seccion_docente, lista_de_tres):
    html = entrar(docente).get(url_lista(seccion_docente), **HTMX).content.decode()

    for estudiante in lista_de_tres:
        destino = reverse("estudiantes:editar", args=[seccion_docente.pk, estudiante.pk])
        assert re.search(rf'<a[^>]*href="{destino}"[^>]*hx-get="{destino}"', html)


@pytest.mark.parametrize("cabeceras", [{}, HTMX])
def test_agregar_va_arriba_y_vaciar_al_final(
    entrar, docente, seccion_docente, lista_de_tres, cabeceras
):
    html = entrar(docente).get(url_lista(seccion_docente), **cabeceras).content.decode()
    agregar = reverse("estudiantes:agregar", args=[seccion_docente.pk])
    vaciar = reverse("estudiantes:vaciar", args=[seccion_docente.pk])

    cabecera = re.search(r'<header class="modal-cabecera">.*?</header>', html, re.S).group(0)
    assert re.search(
        rf'<a[^>]*class="boton-principal"[^>]*href="{agregar}"[^>]*>Agregar estudiante</a>',
        cabecera,
    )
    final = re.search(r'<div class="fin-lista">(.*?)</div>', html, re.S)
    assert final, "falta el final de la lista"
    assert html.index("</ol>") < final.start()
    assert re.search(
        rf'<a[^>]*class="accion-peligro"[^>]*href="{vaciar}"[^>]*>Vaciar lista</a>',
        final.group(1),
    )


def test_el_aviso_de_exito_es_un_estado_que_no_se_va_solo(entrar, docente, seccion_docente):
    html = (
        entrar(docente)
        .post(url_pegar(seccion_docente), {"lista": LISTA_VALIDA}, follow=True, **HTMX)
        .content.decode()
    )

    aviso = re.search(r'<div class="mensaje mensaje--exito"[^>]*>', html).group(0)
    assert 'role="status"' in aviso
    assert "data-ocultar" not in aviso
    assert html.index("3 estudiantes importados") < html.index('<ol class="estudiantes"')


def test_otra_docente_no_puede_pegar_en_la_seccion(entrar, otra_docente, seccion_docente):
    respuesta = entrar(otra_docente).post(url_pegar(seccion_docente), {"lista": LISTA_VALIDA})

    assert respuesta.status_code == 404
    assert seccion_docente.estudiantes.count() == 0


# --- Agregar y Editar (spec "Agregar un estudiante" y "Editar un estudiante") ---

AYUDA_HOMONIMO = "Si son personas distintas, escribe el segundo nombre completo."


def url_agregar(seccion):
    return reverse("estudiantes:agregar", args=[seccion.pk])


def url_editar(seccion, estudiante):
    return reverse("estudiantes:editar", args=[seccion.pk, estudiante.pk])


def url_quitar(seccion, estudiante):
    return reverse("estudiantes:quitar", args=[seccion.pk, estudiante.pk])


def entrada(html, nombre):
    return re.search(rf'<input[^>]*name="{nombre}"[^>]*>', html).group(0)


def formulario_estudiante(html):
    """El formulario de Agregar o Editar (la página completa tiene además el de "Salir")."""
    return [f for f in formularios(html) if 'name="apellidos"' in f]


def con_foco(html):
    return re.findall(r"<[a-z0-9]+\b[^>]*data-foco[^>]*>", html)


def aviso_portada(html):
    return re.search(r'<div[^>]*id="aviso-portada"[^>]*hx-swap-oob="true"[^>]*>.*', html, re.S)


@pytest.fixture
def ana_lucia(seccion_docente):
    return Estudiante.objects.create(
        seccion=seccion_docente, apellidos="QUISPE MAMANI", nombres="ANA LUCIA"
    )


@pytest.mark.parametrize("cabeceras", [{}, HTMX])
def test_agregar_tiene_dos_campos_obligatorios_de_120(entrar, docente, seccion_docente, cabeceras):
    html = entrar(docente).get(url_agregar(seccion_docente), **cabeceras).content.decode()

    assert "Agregar estudiante" in html
    for nombre, etiqueta in [("apellidos", "Apellidos"), ("nombres", "Nombres")]:
        control = entrada(html, nombre)
        assert "required" in control
        assert 'maxlength="120"' in control
        assert "value=" not in control
        assert re.search(rf'<label[^>]*for="agregar-{nombre}"[^>]*>{etiqueta}</label>', html)
    assert "Los nombres se guardan en mayúsculas." in html
    assert re.search(
        r'<button[^>]*type="submit"[^>]*form="form-estudiante"[^>]*>\s*Guardar y agregar otro',
        html,
    )
    assert f'href="{url_lista(seccion_docente)}"' in html.split("Guardar y agregar otro")[1]
    formulario = formulario_estudiante(html)
    assert len(formulario) == 1
    assert 'name="csrfmiddlewaretoken"' in formulario[0]
    assert f'hx-post="{url_agregar(seccion_docente)}"' in formulario[0]


@pytest.mark.parametrize("vista", ["agregar", "editar"])
def test_los_campos_del_estudiante_no_se_autocompletan(
    entrar, docente, seccion_docente, ana_lucia, vista
):
    # SonarQube (Web:S6840): family-name y given-name autocompletarían el nombre de la docente,
    # no el del estudiante (esos valores describen a quien usa el navegador).
    url = (
        url_agregar(seccion_docente)
        if vista == "agregar"
        else url_editar(seccion_docente, ana_lucia)
    )

    html = entrar(docente).get(url).content.decode()

    for nombre in ("apellidos", "nombres"):
        assert 'autocomplete="off"' in entrada(html, nombre)


def test_en_agregar_el_foco_va_a_apellidos(entrar, docente, seccion_docente):
    html = entrar(docente).get(url_agregar(seccion_docente), **HTMX).content.decode()

    assert con_foco(html) == [entrada(html, "apellidos")]


def test_guardar_y_agregar_otro_redirige_a_agregar_con_303(entrar, docente, seccion_docente):
    datos = {"apellidos": "  quispe   mamani ", "nombres": "ana lucía"}

    respuesta = entrar(docente).post(url_agregar(seccion_docente), datos)

    assert respuesta.status_code == 303
    assert respuesta["Location"] == url_agregar(seccion_docente)
    estudiante = seccion_docente.estudiantes.get()
    assert (estudiante.apellidos, estudiante.nombres) == ("QUISPE MAMANI", "ANA LUCÍA")


@pytest.mark.parametrize("cabeceras", [{}, HTMX])
def test_tras_agregar_los_campos_vuelven_vacios_con_el_aviso_una_vez(
    entrar, docente, seccion_docente, cabeceras
):
    cliente = entrar(docente)
    datos = {"apellidos": "QUISPE MAMANI", "nombres": "ANA"}

    respuesta = cliente.post(url_agregar(seccion_docente), datos, follow=True, **cabeceras)
    html = respuesta.content.decode()

    assert respuesta.redirect_chain == [(url_agregar(seccion_docente), 303)]
    assert re.search(r'<div class="mensaje mensaje--exito"[^>]*role="status"', html)
    assert "Estudiante agregado" in html
    assert "1 estudiante<" in html
    assert "value=" not in entrada(html, "apellidos")
    assert "Estudiante agregado" not in cliente.get(url_agregar(seccion_docente)).content.decode()


def test_con_htmx_agregar_quita_el_aviso_de_la_portada(entrar, docente, seccion_docente):
    datos = {"apellidos": "ROJAS", "nombres": "ANA"}

    html = (
        entrar(docente)
        .post(url_agregar(seccion_docente), datos, follow=True, **HTMX)
        .content.decode()
    )

    aviso = aviso_portada(html)
    assert aviso, "falta el aviso fuera de banda"
    assert "Tu sección aún no tiene estudiantes" not in aviso.group(0)


def test_un_campo_vacio_muestra_su_error_y_no_guarda(entrar, docente, seccion_docente):
    respuesta = entrar(docente).post(
        url_agregar(seccion_docente), {"apellidos": "QUISPE MAMANI", "nombres": "   "}, **HTMX
    )

    html = respuesta.content.decode()
    assert respuesta.status_code == 200
    assert seccion_docente.estudiantes.count() == 0
    nombres = entrada(html, "nombres")
    assert 'aria-invalid="true"' in nombres
    assert "agregar-nombres-error" in nombres
    assert re.search(
        r'<p class="campo__error" id="agregar-nombres-error">.*?<span>Escribe los nombres</span>',
        html,
        re.S,
    )
    assert 'value="QUISPE MAMANI"' in entrada(html, "apellidos")
    assert "aria-invalid" not in entrada(html, "apellidos")
    assert con_foco(html) == [nombres]


def test_mas_de_120_caracteres_muestra_su_error(entrar, docente, seccion_docente):
    datos = {"apellidos": "A" * 121, "nombres": "ANA"}

    html = entrar(docente).post(url_agregar(seccion_docente), datos).content.decode()

    assert "Usa un máximo de 120 caracteres." in html
    assert seccion_docente.estudiantes.count() == 0


@pytest.mark.parametrize("cabeceras", [{}, HTMX])
def test_el_homonimo_al_agregar_conserva_lo_escrito_y_sugiere_el_segundo_nombre(
    entrar, docente, seccion_docente, ana_lucia, cabeceras
):
    datos = {"apellidos": "quispe mamani", "nombres": "ana lucia"}

    respuesta = entrar(docente).post(url_agregar(seccion_docente), datos, **cabeceras)

    html = respuesta.content.decode()
    assert respuesta.status_code == 200
    assert seccion_docente.estudiantes.count() == 1
    error = re.search(
        r'<div class="mensaje mensaje--error" role="alert">.*?</div></div>', html, re.S
    )
    assert error, "falta el mensaje del homónimo"
    assert "Este estudiante ya está en la lista" in error.group(0)
    assert AYUDA_HOMONIMO in error.group(0)
    assert 'value="quispe mamani"' in entrada(html, "apellidos")
    assert 'value="ana lucia"' in entrada(html, "nombres")


@pytest.mark.parametrize("cabeceras", [{}, HTMX])
def test_editar_muestra_los_valores_y_la_salida_para_quitar(
    entrar, docente, seccion_docente, ana_lucia, cabeceras
):
    url = url_editar(seccion_docente, ana_lucia)

    html = entrar(docente).get(url, **cabeceras).content.decode()

    assert "Editar estudiante" in html
    assert 'value="QUISPE MAMANI"' in entrada(html, "apellidos")
    assert 'value="ANA LUCIA"' in entrada(html, "nombres")
    for nombre in ("apellidos", "nombres"):
        assert 'maxlength="120"' in entrada(html, nombre)
        assert "required" in entrada(html, nombre)
    assert html.count("Se guarda en mayúsculas. Máximo 120 caracteres.") == 2
    quitar = url_quitar(seccion_docente, ana_lucia)
    assert re.search(
        rf'<a[^>]*class="accion-peligro"[^>]*href="{quitar}"[^>]*hx-get="{quitar}"[^>]*>'
        r"Quitar estudiante</a>",
        html,
    )
    assert "Solo puedes quitarlo si no tiene asistencia ni notas." in html
    assert re.search(
        r'<button[^>]*type="submit"[^>]*form="form-estudiante"[^>]*>\s*Guardar cambios', html
    )
    formulario = formulario_estudiante(html)
    assert len(formulario) == 1
    assert 'name="csrfmiddlewaretoken"' in formulario[0]
    assert f'hx-post="{url}"' in formulario[0]


def test_en_editar_el_foco_va_a_apellidos(entrar, docente, seccion_docente, ana_lucia):
    html = entrar(docente).get(url_editar(seccion_docente, ana_lucia), **HTMX).content.decode()

    assert con_foco(html) == [entrada(html, "apellidos")]


def test_guardar_cambios_vuelve_a_la_lista_con_el_nombre_corregido(
    entrar, docente, seccion_docente, ana_lucia
):
    cliente = entrar(docente)
    datos = {"apellidos": "QUISPE MAMANI", "nombres": "ana lucía"}

    respuesta = cliente.post(url_editar(seccion_docente, ana_lucia), datos)

    assert respuesta.status_code == 303
    assert respuesta["Location"] == url_lista(seccion_docente)
    html = cliente.get(url_lista(seccion_docente)).content.decode()
    assert '<span class="estudiante__nombre">QUISPE MAMANI, ANA LUCÍA</span>' in html


def test_la_correccion_que_crea_un_homonimo_no_se_guarda(
    entrar, docente, seccion_docente, ana_lucia
):
    Estudiante.objects.create(seccion=seccion_docente, apellidos="QUISPE MAMANI", nombres="ANA")
    datos = {"apellidos": "Quispe Mamani", "nombres": "Ana"}

    respuesta = entrar(docente).post(url_editar(seccion_docente, ana_lucia), datos, **HTMX)

    html = respuesta.content.decode()
    assert respuesta.status_code == 200
    assert "Este estudiante ya está en la lista" in html
    assert AYUDA_HOMONIMO in html
    assert 'value="Quispe Mamani"' in entrada(html, "apellidos")
    ana_lucia.refresh_from_db()
    assert ana_lucia.nombres == "ANA LUCIA"


def test_editar_un_estudiante_quitado_mientras_se_enviaba_da_404_sin_recrearlo(
    entrar, docente, seccion_docente, ana_lucia, monkeypatch
):
    # Revisión A2: otra pestaña lo quita después de que la vista lo cargó y antes de guardar.
    from institucion import views

    validar = views.EstudianteForm.is_valid

    def quitado_entretanto(formulario):
        Estudiante.objects.filter(pk=ana_lucia.pk).delete()
        return validar(formulario)

    monkeypatch.setattr(views.EstudianteForm, "is_valid", quitado_entretanto)
    datos = {"apellidos": "QUISPE MAMANI", "nombres": "ana lucía"}

    respuesta = entrar(docente).post(url_editar(seccion_docente, ana_lucia), datos)

    assert respuesta.status_code == 404
    assert seccion_docente.estudiantes.count() == 0


@pytest.mark.parametrize("ruta", ["editar", "quitar"])
@pytest.mark.parametrize("metodo", ["get", "post"])
def test_un_estudiante_de_otra_seccion_da_404(
    entrar, docente, seccion_docente, anio_abierto, otra_docente, ruta, metodo
):
    otra = Seccion.objects.create(
        anio_escolar=anio_abierto, grado=3, nombre="B", docente=otra_docente
    )
    ajeno = Estudiante.objects.create(seccion=otra, apellidos="ROJAS", nombres="LUIS")
    url = reverse(f"estudiantes:{ruta}", args=[seccion_docente.pk, ajeno.pk])

    respuesta = getattr(entrar(docente), metodo)(url, {"apellidos": "X", "nombres": "Y"})

    assert respuesta.status_code == 404
    assert "ROJAS" not in respuesta.content.decode()
    ajeno.refresh_from_db()
    assert ajeno.apellidos == "ROJAS"


def test_otra_docente_no_puede_agregar_en_la_seccion(entrar, otra_docente, seccion_docente):
    datos = {"apellidos": "ROJAS", "nombres": "LUIS"}

    respuesta = entrar(otra_docente).post(url_agregar(seccion_docente), datos)

    assert respuesta.status_code == 404
    assert seccion_docente.estudiantes.count() == 0


def test_ya_no_hay_vistas_pendientes():
    from institucion import views

    assert not hasattr(views, "PendienteView")


# --- Quitar y vaciar (spec "Quitar y vaciar") ---

AYUDA_BLOQUEO = "Si es un error, pide ayuda al administrador"


def url_vaciar(seccion):
    return reverse("estudiantes:vaciar", args=[seccion.pk])


def formulario_de(html, accion):
    return [f for f in formularios(html) if f'action="{accion}"' in f]


def solo_volver_a_la_lista(html, seccion):
    pie = re.search(r'<footer class="modal-pie"[^>]*>(.*?)</footer>', html, re.S).group(1)
    assert re.findall(r"<(?:a|button)\b[^>]*>", pie) == [
        re.search(r'<a[^>]*class="volver-lista"[^>]*>', pie).group(0)
    ]
    assert f'href="{url_lista(seccion)}"' in pie


@pytest.mark.parametrize("cabeceras", [{}, HTMX])
def test_quitar_pide_confirmacion_con_el_nombre(
    entrar, docente, seccion_docente, ana_lucia, cabeceras
):
    url = url_quitar(seccion_docente, ana_lucia)

    html = entrar(docente).get(url, **cabeceras).content.decode()

    assert re.search(r'class="vista-titulo"[^>]*>Quitar estudiante<', html)
    assert '<p class="confirmacion-nombre">¿Quitar a QUISPE MAMANI, ANA LUCIA?</p>' in html
    assert "Solo se puede si no tiene asistencia ni notas" in html
    assert re.search(r'<button[^>]*form="form-quitar"[^>]*>\s*Quitar estudiante', html)
    formulario = formulario_de(html, url)
    assert len(formulario) == 1
    assert 'id="form-quitar"' in formulario[0]
    assert 'name="csrfmiddlewaretoken"' in formulario[0]
    assert f'hx-post="{url}"' in formulario[0]
    assert f'href="{url_lista(seccion_docente)}"' in html.split("form-quitar")[-1]


def test_en_quitar_el_foco_va_al_titulo_de_la_vista(entrar, docente, seccion_docente, ana_lucia):
    html = entrar(docente).get(url_quitar(seccion_docente, ana_lucia), **HTMX).content.decode()

    foco = con_foco(html)
    assert len(foco) == 1
    assert re.match(r'<h3[^>]*class="vista-titulo"[^>]*tabindex="-1"', foco[0])


def test_quitar_sin_registros_vuelve_a_la_lista_con_uno_menos(
    entrar, docente, seccion_docente, lista_de_tres
):
    cliente = entrar(docente)
    quitado = lista_de_tres[0]

    respuesta = cliente.post(url_quitar(seccion_docente, quitado))

    assert respuesta.status_code == 303
    assert respuesta["Location"] == url_lista(seccion_docente)
    assert not Estudiante.objects.filter(pk=quitado.pk).exists()
    assert "2 estudiantes" in cliente.get(url_lista(seccion_docente)).content.decode()


@pytest.mark.parametrize("cabeceras", [{}, HTMX])
def test_quitar_con_registros_muestra_el_bloqueo_y_no_quita(
    entrar, docente, seccion_docente, ana_lucia, borrado_con_registros, cabeceras
):
    respuesta = entrar(docente).post(url_quitar(seccion_docente, ana_lucia), **cabeceras)

    html = respuesta.content.decode()
    assert respuesta.status_code == 200
    assert Estudiante.objects.filter(pk=ana_lucia.pk).exists()
    alerta = re.search(
        r'<div class="mensaje mensaje--error" role="alert">.*?</div></div>', html, re.S
    )
    assert alerta, "falta el bloqueo"
    assert "No se puede quitar: el estudiante ya tiene registros" in alerta.group(0)
    assert AYUDA_BLOQUEO in alerta.group(0)
    assert not formulario_de(html, url_quitar(seccion_docente, ana_lucia))
    solo_volver_a_la_lista(html, seccion_docente)


@pytest.mark.parametrize("cabeceras", [{}, HTMX])
def test_vaciar_pide_confirmacion_con_la_cantidad(
    entrar, docente, seccion_docente, lista_de_tres, cabeceras
):
    html = entrar(docente).get(url_vaciar(seccion_docente), **cabeceras).content.decode()

    assert re.search(r'class="vista-titulo"[^>]*>Vaciar lista<', html)
    aviso = re.search(
        r'<div class="mensaje mensaje--aviso" role="status">.*?</div></div>', html, re.S
    )
    assert aviso, "falta la confirmación"
    assert "Se quitarán los 3 estudiantes." in aviso.group(0)
    assert "Solo se puede si ninguno tiene asistencia ni notas" in aviso.group(0)
    assert re.search(r'<button[^>]*form="form-vaciar"[^>]*>\s*Vaciar lista', html)
    formulario = formulario_de(html, url_vaciar(seccion_docente))
    assert len(formulario) == 1
    assert 'name="csrfmiddlewaretoken"' in formulario[0]
    assert f'hx-post="{url_vaciar(seccion_docente)}"' in formulario[0]


def test_vaciar_con_un_estudiante_va_en_singular(entrar, docente, seccion_docente, ana_lucia):
    html = entrar(docente).get(url_vaciar(seccion_docente)).content.decode()

    assert "Se quitará 1 estudiante." in html


def test_vaciar_una_lista_vacia_vuelve_a_la_lista(entrar, docente, seccion_docente):
    respuesta = entrar(docente).get(url_vaciar(seccion_docente))

    assert respuesta.status_code == 303
    assert respuesta["Location"] == url_lista(seccion_docente)


def test_vaciar_sin_registros_deja_la_lista_vacia_y_el_aviso_de_la_portada(
    entrar, docente, seccion_docente, lista_de_tres
):
    respuesta = entrar(docente).post(url_vaciar(seccion_docente), follow=True, **HTMX)

    html = respuesta.content.decode()
    assert respuesta.redirect_chain == [(url_lista(seccion_docente), 303)]
    assert seccion_docente.estudiantes.count() == 0
    assert "Tu sección aún no tiene estudiantes." in html
    aviso = aviso_portada(html)
    assert aviso and "Tu sección aún no tiene estudiantes" in aviso.group(0)


@pytest.mark.parametrize("cabeceras", [{}, HTMX])
def test_vaciar_con_registros_muestra_el_bloqueo_y_no_quita_ninguno(
    entrar, docente, seccion_docente, lista_de_tres, borrado_con_registros, cabeceras
):
    respuesta = entrar(docente).post(url_vaciar(seccion_docente), **cabeceras)

    html = respuesta.content.decode()
    assert respuesta.status_code == 200
    assert seccion_docente.estudiantes.count() == 3
    alerta = re.search(
        r'<div class="mensaje mensaje--error" role="alert">.*?</div></div>', html, re.S
    )
    assert alerta, "falta el bloqueo"
    assert "No se puede vaciar: algunos estudiantes ya tienen registros" in alerta.group(0)
    assert AYUDA_BLOQUEO in alerta.group(0)
    assert not formulario_de(html, url_vaciar(seccion_docente))
    solo_volver_a_la_lista(html, seccion_docente)


def test_en_el_bloqueo_el_foco_va_al_titulo_de_la_vista(
    entrar, docente, seccion_docente, lista_de_tres, borrado_con_registros
):
    html = entrar(docente).post(url_vaciar(seccion_docente), **HTMX).content.decode()

    foco = con_foco(html)
    assert len(foco) == 1
    assert re.match(r'<h3[^>]*class="vista-titulo"[^>]*tabindex="-1"', foco[0])


def test_otra_docente_no_puede_vaciar_la_seccion(
    entrar, otra_docente, seccion_docente, lista_de_tres
):
    respuesta = entrar(otra_docente).post(url_vaciar(seccion_docente))

    assert respuesta.status_code == 404
    assert seccion_docente.estudiantes.count() == 3
