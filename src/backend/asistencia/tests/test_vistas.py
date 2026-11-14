"""Vistas de la asistencia de hoy (spec asistencia-jornada; design de US-030, D3 y D10).

Rutas y acceso (la docente de la sección; otra docente, año CERRADO o inexistente, 403 con registro
desde US-004; otro rol, sin sesión y HTMX), CSRF, las respuestas sin cuerpo de los guardados (204,
400, 404 y 409) y el HTML que dibuja el
servidor (D10). El día se fija parcheando ``timezone.localdate``.
"""

import datetime
import re

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from actividad.tests.intentos import es_sin_permiso, intentos, motivos
from asistencia.models import Asistencia, Jornada
from institucion.models import AnioEscolar, Estudiante, Seccion

pytestmark = pytest.mark.django_db

HTMX = {"HTTP_HX_REQUEST": "true"}
MIERCOLES = datetime.date(2026, 10, 28)
SABADO = datetime.date(2026, 10, 31)
# La de Django, antes de que el fixture de abajo la reemplace.
LOCALDATE = timezone.localdate


@pytest.fixture(autouse=True)
def hoy_miercoles(monkeypatch):
    """Hoy es el miércoles 28 de octubre en Lima, sin tocar el reloj del sistema."""
    dia = {"valor": MIERCOLES}
    monkeypatch.setattr(timezone, "localdate", lambda *args, **kwargs: dia["valor"])
    return dia


@pytest.fixture
def seccion_docente(seccion, docente):
    seccion.docente = docente
    seccion.save()
    return seccion


@pytest.fixture
def entrar(client):
    def entrar_como(usuario):
        client.force_login(usuario)
        return client

    return entrar_como


@pytest.fixture
def cliente(entrar, docente, seccion_docente):
    return entrar(docente)


def url_hoy(seccion):
    return reverse("asistencia:hoy", args=[seccion.pk])


def url_marcar(seccion, estudiante, fecha=MIERCOLES):
    return reverse("asistencia:marcar", args=[seccion.pk, fecha, estudiante.pk])


def url_restantes(seccion, fecha=MIERCOLES):
    return reverse("asistencia:restantes", args=[seccion.pk, fecha])


# --- Rutas (D10) ---


def test_las_tres_rutas_estan_bajo_la_seccion(seccion_docente, estudiante):
    base = f"/docente/secciones/{seccion_docente.pk}/asistencia/"

    assert url_hoy(seccion_docente) == base
    assert url_marcar(seccion_docente, estudiante) == (
        f"{base}2026-10-28/estudiantes/{estudiante.pk}/"
    )
    assert url_restantes(seccion_docente) == f"{base}2026-10-28/restantes/"


@pytest.mark.parametrize("fecha", ["2026-13-01", "2026-02-30", "28-10-2026", "hoy"])
def test_una_fecha_mal_escrita_no_es_una_ruta(cliente, seccion_docente, estudiante, fecha):
    base = f"/docente/secciones/{seccion_docente.pk}/asistencia/"

    respuesta = cliente.post(f"{base}{fecha}/estudiantes/{estudiante.pk}/", {"estado": "ASISTIO"})

    assert respuesta.status_code == 404
    assert not Jornada.objects.exists()


# --- Acceso (spec "Acceso solo a la asistencia de su sección") ---


def test_la_docente_de_la_seccion_abre_la_asistencia(cliente, seccion_docente):
    assert cliente.get(url_hoy(seccion_docente)).status_code == 200


def test_abrir_la_asistencia_no_crea_la_jornada(cliente, seccion_docente, estudiante):
    cliente.get(url_hoy(seccion_docente))

    assert not Jornada.objects.exists()


@pytest.mark.parametrize("cabeceras", [{}, HTMX])
def test_otra_docente_recibe_403_y_no_guarda(
    entrar, otra_docente, seccion_docente, estudiante, cabeceras
):
    cliente = entrar(otra_docente)
    url_m = url_marcar(seccion_docente, estudiante)
    url_r = url_restantes(seccion_docente)

    hoy = cliente.get(url_hoy(seccion_docente), **cabeceras)
    marcar = cliente.post(url_m, {"estado": "ASISTIO"}, **cabeceras)
    restantes = cliente.post(url_r, {"estudiante": [estudiante.pk]}, **cabeceras)

    assert all(es_sin_permiso(r) for r in (hoy, marcar, restantes))
    assert not Jornada.objects.exists()
    seccion = str(seccion_docente.pk)
    assert intentos() == [
        (seccion, url_hoy(seccion_docente), "ajena"),
        (seccion, url_m, "ajena"),
        (seccion, url_r, "ajena"),
    ]


def test_una_seccion_del_anio_cerrado_da_403_y_no_guarda(
    entrar, docente, institucion, hoy_miercoles
):
    anio = AnioEscolar.objects.create(institucion=institucion, anio=2026, estado="CERRADO")
    cerrada = Seccion.objects.create(anio_escolar=anio, grado=2, nombre="A", docente=docente)
    (estudiante,) = [Estudiante.objects.create(seccion=cerrada, apellidos="ROJAS", nombres="LUIS")]
    cliente = entrar(docente)

    assert es_sin_permiso(cliente.get(url_hoy(cerrada)))
    assert es_sin_permiso(cliente.post(url_marcar(cerrada, estudiante), {"estado": "ASISTIO"}))
    assert es_sin_permiso(cliente.post(url_restantes(cerrada), {"estudiante": [estudiante.pk]}))
    assert not Jornada.objects.exists()
    assert motivos() == ["anio_cerrado"] * 3


def test_una_seccion_que_no_existe_da_403_y_no_guarda(entrar, docente):
    cliente = entrar(docente)
    base = "/docente/secciones/999999/asistencia/"

    assert es_sin_permiso(cliente.get(base))
    assert es_sin_permiso(cliente.post(f"{base}2026-10-28/estudiantes/1/", {"estado": "ASISTIO"}))
    assert es_sin_permiso(cliente.post(f"{base}2026-10-28/restantes/", {"estudiante": [1]}))
    assert not Jornada.objects.exists()
    assert motivos() == ["inexistente"] * 3


def test_la_direccion_llega_a_su_pantalla(entrar, direccion, seccion_docente, estudiante):
    cliente = entrar(direccion)

    assert cliente.get(url_hoy(seccion_docente)).url == "/direccion/"
    marcar = cliente.post(url_marcar(seccion_docente, estudiante), {"estado": "ASISTIO"})
    assert marcar.url == "/direccion/"
    assert not Jornada.objects.exists()


def test_sin_sesion_va_a_ingresar_con_next(client, seccion_docente):
    respuesta = client.get(url_hoy(seccion_docente))

    assert respuesta.status_code == 302
    assert respuesta.url == f"/ingresar/?next={url_hoy(seccion_docente)}"


def test_sin_sesion_un_guardado_con_htmx_recibe_hx_redirect(client, seccion_docente, estudiante):
    respuesta = client.post(url_marcar(seccion_docente, estudiante), {"estado": "ASISTIO"}, **HTMX)

    assert respuesta.status_code == 200
    assert respuesta["HX-Redirect"] == "/ingresar/?next=/docente/"
    assert not Jornada.objects.exists()


def test_con_la_sesion_vencida_un_guardado_con_htmx_recibe_hx_redirect(
    cliente, seccion_docente, estudiante
):
    sesion = cliente.session
    sesion["ultima_actividad"] = 0
    sesion.save()

    respuesta = cliente.post(url_marcar(seccion_docente, estudiante), {"estado": "ASISTIO"}, **HTMX)

    assert respuesta.status_code == 200
    assert respuesta["HX-Redirect"] == "/ingresar/?next=/docente/"
    assert not Jornada.objects.exists()


def test_un_guardado_sin_token_csrf_se_rechaza(docente, seccion_docente, estudiante):
    cliente = Client(enforce_csrf_checks=True)
    cliente.force_login(docente)

    respuesta = cliente.post(url_marcar(seccion_docente, estudiante), {"estado": "ASISTIO"})

    assert respuesta.status_code == 403
    assert not Jornada.objects.exists()


# --- Guardar una fila (D3) ---


def test_un_guardado_correcto_responde_204_sin_cuerpo(cliente, seccion_docente, estudiante):
    respuesta = cliente.post(url_marcar(seccion_docente, estudiante), {"estado": "FALTO"})

    assert respuesta.status_code == 204
    assert respuesta.content == b""
    asistencia = Asistencia.objects.get()
    assert (asistencia.estudiante, asistencia.estado) == (estudiante, "FALTO")
    assert asistencia.jornada.registrado_por.username == "aquispe"


def test_el_guardado_lleva_la_nota_de_justificacion(cliente, seccion_docente, estudiante):
    datos = {"estado": "JUSTIFICADO", "nota": "Constancia entregada a la docente"}

    assert cliente.post(url_marcar(seccion_docente, estudiante), datos).status_code == 204
    assert Asistencia.objects.get().nota_justificacion == "Constancia entregada a la docente"


def test_el_mismo_guardado_dos_veces_deja_una_fila(cliente, seccion_docente, estudiante):
    for _ in range(2):
        cliente.post(url_marcar(seccion_docente, estudiante), {"estado": "ASISTIO"})

    assert Jornada.objects.count() == 1
    assert Asistencia.objects.count() == 1


@pytest.mark.parametrize(
    "datos",
    [{"estado": "PRESENTE"}, {}, {"estado": "JUSTIFICADO", "nota": "x" * 101}],
    ids=["estado-desconocido", "sin-estado", "nota-de-101"],
)
def test_un_estado_o_una_nota_que_no_valen_responden_400(
    cliente, seccion_docente, estudiante, datos
):
    respuesta = cliente.post(url_marcar(seccion_docente, estudiante), datos)

    assert respuesta.status_code == 400
    assert respuesta.content == b""
    assert not Jornada.objects.exists()


@pytest.mark.parametrize("cabeceras", [{}, HTMX])
def test_un_estudiante_de_otra_seccion_responde_403(
    cliente, seccion_docente, anio_abierto, cabeceras
):
    otra = Seccion.objects.create(anio_escolar=anio_abierto, grado=3, nombre="B")
    ajeno = Estudiante.objects.create(seccion=otra, apellidos="ROJAS", nombres="LUIS")
    url = url_marcar(seccion_docente, ajeno)

    respuesta = cliente.post(url, {"estado": "ASISTIO"}, **cabeceras)

    assert es_sin_permiso(respuesta)
    assert not Jornada.objects.exists()
    assert intentos() == [(str(seccion_docente.pk), url, "estudiante")]


def test_un_estudiante_retirado_responde_404(cliente, seccion_docente, estudiante):
    estudiante.estado = Estudiante.Estado.RETIRADO
    estudiante.save()

    respuesta = cliente.post(url_marcar(seccion_docente, estudiante), {"estado": "ASISTIO"})

    assert respuesta.status_code == 404
    assert respuesta.content == b""
    assert intentos() == []


def test_un_guardado_de_otro_dia_responde_409(cliente, seccion_docente, estudiante):
    ayer = MIERCOLES - datetime.timedelta(days=1)

    respuesta = cliente.post(url_marcar(seccion_docente, estudiante, ayer), {"estado": "ASISTIO"})

    assert respuesta.status_code == 409
    assert respuesta.content == b""
    assert not Jornada.objects.exists()


def test_un_guardado_en_sabado_responde_409(cliente, seccion_docente, estudiante, hoy_miercoles):
    hoy_miercoles["valor"] = SABADO

    respuesta = cliente.post(url_marcar(seccion_docente, estudiante, SABADO), {"estado": "ASISTIO"})

    assert respuesta.status_code == 409
    assert not Jornada.objects.exists()


def test_marcar_solo_acepta_post(cliente, seccion_docente, estudiante):
    assert cliente.get(url_marcar(seccion_docente, estudiante)).status_code == 405


# --- Marcar los restantes (D5) ---


@pytest.fixture
def tres(seccion_docente):
    return [
        Estudiante.objects.create(seccion=seccion_docente, apellidos=apellidos, nombres="ANA")
        for apellidos in ("AGUILAR", "BRAVO", "CASAS")
    ]


def test_restantes_guarda_asistio_y_responde_204(cliente, seccion_docente, tres):
    ids = [e.pk for e in tres]

    respuesta = cliente.post(url_restantes(seccion_docente), {"estudiante": ids})

    assert respuesta.status_code == 204
    assert respuesta.content == b""
    assert sorted(Asistencia.objects.values_list("estado", flat=True)) == ["ASISTIO"] * 3


def test_restantes_con_un_id_ajeno_responde_404_sin_guardar(
    cliente, seccion_docente, tres, anio_abierto
):
    otra = Seccion.objects.create(anio_escolar=anio_abierto, grado=3, nombre="B")
    ajeno = Estudiante.objects.create(seccion=otra, apellidos="ROJAS", nombres="LUIS")

    respuesta = cliente.post(url_restantes(seccion_docente), {"estudiante": [tres[0].pk, ajeno.pk]})

    assert respuesta.status_code == 404
    assert not Asistencia.objects.exists()
    # D7 de US-004: un id ajeno en el cuerpo no es un intento sin permiso.
    assert intentos() == []


def test_restantes_con_un_id_que_no_es_numero_responde_400(cliente, seccion_docente, tres):
    respuesta = cliente.post(url_restantes(seccion_docente), {"estudiante": [tres[0].pk, "x"]})

    assert respuesta.status_code == 400
    assert not Asistencia.objects.exists()


def test_restantes_de_otro_dia_responde_409(cliente, seccion_docente, tres):
    ayer = MIERCOLES - datetime.timedelta(days=1)

    respuesta = cliente.post(url_restantes(seccion_docente, ayer), {"estudiante": [tres[0].pk]})

    assert respuesta.status_code == 409
    assert not Asistencia.objects.exists()


# --- Enlace del aviso de éxito de la lista de estudiantes (spec estudiantes-seccion) ---


def test_el_aviso_de_importados_lleva_a_tomar_la_asistencia_de_hoy(cliente, seccion_docente):
    url_pegar = reverse("estudiantes:pegar", args=[seccion_docente.pk])

    html = cliente.post(url_pegar, {"lista": "QUISPE, ANA\nROJAS, LUIS"}, follow=True)
    html = html.content.decode()

    aviso = html[html.index("message--exito") : html.index('<ol class="estudiantes-lista"')]
    assert "2 estudiantes importados" in aviso
    enlace = (
        f'<a class="btn btn--text" href="{url_hoy(seccion_docente)}">Tomar la asistencia de hoy'
    )
    assert enlace in aviso
    assert "hx-get" not in aviso, "un enlace normal: también en el diálogo abre la página completa"


def test_sin_aviso_de_importados_no_hay_enlace_a_la_asistencia(cliente, seccion_docente):
    Estudiante.objects.create(seccion=seccion_docente, apellidos="QUISPE", nombres="ANA")

    html = cliente.get(reverse("estudiantes:lista", args=[seccion_docente.pk])).content.decode()

    assert "Tomar la asistencia de hoy" not in html


# --- HTML de la pantalla (spec asistencia-jornada; rebrand-us-030, D1 a D5) ---


def abrir(cliente, seccion):
    respuesta = cliente.get(url_hoy(seccion))
    assert respuesta.status_code == 200
    return respuesta.content.decode()


def principal(html):
    """El contenido del único ``<main>`` (el del marco del rebrand)."""
    assert html.count("<main") == 1, "un solo <main>: el del marco"
    return re.search(r"<main\b.*?</main>", html, re.DOTALL).group(0)


def botones(html, clase):
    """Las etiquetas de apertura de los botones con esa clase, en orden."""
    return re.findall(rf'<button[^>]*class="(?:[^"]* )?{clase}(?: [^"]*)?"[^>]*>', html)


def fila(html, estudiante):
    inicio = html.index(f'id="fila-{estudiante.pk}"')
    return html[inicio : html.index("</li>", inicio)]


def nombre(estudiante):
    return f"{estudiante.apellidos}, {estudiante.nombres}"


def tarjeta(html):
    """La tarjeta café «Tu jornada», hasta el aviso «Sin conexión» que la sigue (D1)."""
    inicio = html.index('class="tarjeta-jornada"')
    return html[inicio : html.index("data-sin-conexion", inicio)]


def texto(fragmento):
    return re.sub(r"<[^>]+>", "", fragmento)


@pytest.fixture
def lista(seccion_docente, veinticinco):
    return veinticinco


def poner(seccion, estudiantes, estado, nota=""):
    """Estados ya guardados hoy, sin pasar por la vista."""
    jornada, _ = Jornada.objects.get_or_create(
        seccion=seccion, fecha=MIERCOLES, defaults={"registrado_por": seccion.docente}
    )
    for estudiante in estudiantes:
        Asistencia.objects.create(
            jornada=jornada, estudiante=estudiante, estado=estado, nota_justificacion=nota
        )


LISTA = '<ol class="filas-asistencia"'


# 1.1 Marco y encabezado


def test_la_pantalla_va_en_el_marco_del_rebrand(cliente, seccion_docente, lista):
    html = abrir(cliente, seccion_docente)

    hojas = re.findall(r'<link rel="stylesheet" href="([^"]+)"', html)
    assert len(hojas) == 1
    assert hojas[0].endswith("dist/rebrand.css")
    assert "dist/app.css" not in html
    assert "js/asistencia.js" in html
    assert '<span class="bar-title">Asistencia</span>' in html
    actuales = re.findall(r'<a [^>]*aria-current="page"[^>]*>(.*?)</a>', html, re.DOTALL)
    assert [texto(a).strip() for a in actuales] == ["Asistencia"]
    assert 'data-dimension="asistencia"' in principal(html)


def test_la_cabecera_dice_la_seccion_el_titulo_y_la_fecha(cliente, seccion_docente, lista):
    html = abrir(cliente, seccion_docente)
    contenido = principal(html)

    assert "2.º grado, sección A · 2027" in contenido
    assert re.findall(r"<h1\b[^>]*>(.*?)</h1>", html, re.DOTALL) == ["Asistencia de hoy"]
    assert '<time datetime="2026-10-28">Miércoles 28 de octubre</time>' in contenido
    assert "Asistencia · 2.º A" not in contenido
    assert "<title>Asistencia · 2.º A · CarpetaDocente</title>" in html


def test_a_las_23_30_de_lima_es_el_dia_de_lima_y_no_el_de_utc(
    monkeypatch, cliente, seccion_docente, lista
):
    """Escenario "Fecha de Lima": en UTC ya es jueves 29 a las 4:30."""
    monkeypatch.setattr(timezone, "localdate", LOCALDATE)
    jueves_utc = datetime.datetime(2026, 10, 29, 4, 30, tzinfo=datetime.UTC)
    monkeypatch.setattr(timezone, "now", lambda: jueves_utc)

    html = abrir(cliente, seccion_docente)
    respuesta = cliente.post(url_marcar(seccion_docente, lista[0]), {"estado": "FALTO"})

    assert "Miércoles 28 de octubre" in html
    assert respuesta.status_code == 204
    assert Jornada.objects.get().fecha == MIERCOLES


# 1.2 Una sola tarjeta (D1)


def test_una_sola_tarjeta_cafe_con_la_jornada(cliente, seccion_docente, lista):
    poner(seccion_docente, lista[:18], "ASISTIO")

    html = principal(abrir(cliente, seccion_docente))
    caja = tarjeta(html)

    assert html.count('class="tarjeta-jornada"') == 1
    assert html.count("Tu jornada") == 1
    for viejo in ('class="controles"', "franja-jornada", "panel-jornada"):
        assert viejo not in html
    assert "data-guardado" in caja
    progreso = '<progress max="25" value="18" aria-label="Estudiantes marcados" data-progreso>'
    assert progreso in caja
    for estado in ("ASISTIO", "TARDE", "FALTO", "JUSTIFICADO"):
        assert f'data-total="{estado}"' in caja
    assert "data-cierre" in caja
    assert "data-resumen-completo" in caja
    assert caja.count("data-marcar-todos") == 1
    assert html.count("data-marcar-todos") == 2
    debajo = html.index("data-marcar-todos", html.index("data-sin-conexion"))
    assert debajo < html.index(LISTA), "el segundo, debajo de la tarjeta y antes de la lista"


def test_marcar_los_n_restantes_cuenta_los_sin_marcar(cliente, seccion_docente, lista):
    poner(seccion_docente, lista[:18], "ASISTIO")

    html = abrir(cliente, seccion_docente)

    assert html.count("Marcar los 7 restantes como Asistió") == 2
    marcar = re.findall(r"<button[^>]*data-marcar-todos[^>]*>", html)
    assert "btn--primary" in marcar[0]
    assert "btn--secondary" in marcar[1]
    assert all("hidden" not in b for b in marcar)


def test_con_un_sin_marcar_dice_el_restante(cliente, seccion_docente, lista):
    poner(seccion_docente, lista[:24], "ASISTIO")

    html = abrir(cliente, seccion_docente)

    assert "Marcar el restante como Asistió" in html
    assert "Marcar los 1 restantes" not in html


def test_los_totales_de_la_tarjeta_a_medio_marcar(cliente, seccion_docente, lista):
    poner(seccion_docente, lista[:14], "ASISTIO")
    poner(seccion_docente, [lista[14]], "TARDE")
    poner(seccion_docente, lista[15:17], "FALTO")
    poner(seccion_docente, [lista[17]], "JUSTIFICADO")

    caja = tarjeta(abrir(cliente, seccion_docente))

    for palabra, estado, total in [
        ("Asistió", "ASISTIO", 14),
        ("Tarde", "TARDE", 1),
        ("Faltó", "FALTO", 2),
        ("Justificado", "JUSTIFICADO", 1),
    ]:
        assert f'<dt>{palabra}</dt><dd data-total="{estado}">{total}</dd>' in caja


def test_la_jornada_completa_se_dibuja_con_el_cierre(cliente, seccion_docente, lista):
    poner(seccion_docente, lista[:21], "ASISTIO")
    poner(seccion_docente, [lista[21]], "TARDE")
    poner(seccion_docente, lista[22:24], "FALTO")
    poner(seccion_docente, [lista[24]], "JUSTIFICADO")

    html = abrir(cliente, seccion_docente)
    caja = tarjeta(html)

    assert "jornada-completa" in html
    assert "Jornada completa" in caja
    assert re.search(r"<p [^>]*data-cierre>.*?Asistencia de hoy completa</p>", caja, re.DOTALL)
    assert "Asistió: 21 · Tarde: 1 · Faltó: 2 · Justificado: 1" in caja
    assert re.search(r"<p [^>]*data-avance hidden>", caja)
    assert "restantes como Asistió" not in html
    assert "Marcar el restante" not in html
    assert "cierre-animado" not in html, "al abrirla ya completa, sin animación (D3)"


def test_sin_completar_no_hay_cierre(cliente, seccion_docente, lista):
    poner(seccion_docente, lista[:24], "ASISTIO")

    html = abrir(cliente, seccion_docente)

    assert "jornada-completa" not in html
    assert re.search(r"<p [^>]*data-cierre hidden>", html)
    assert re.search(r"<p [^>]*data-resumen-completo hidden>", html)
    assert f'"#fila-{lista[24].pk}"' in html
    assert ">1 sin marcar</a>" in html


# 1.3 Conteo visible y accesible (delta «Avance de la jornada», D2)


def test_caso_de_error_el_conteo_visible_y_el_accesible(cliente, seccion_docente, lista):
    """Escenario "Caso de error": 7 de 25 sin estado."""
    poner(seccion_docente, lista[:18], "ASISTIO")

    html = abrir(cliente, seccion_docente)
    caja = tarjeta(html)

    pc = '<span class="conteo__pc" aria-hidden="true"><strong data-marcados>18</strong>/25 marcados'
    movil = (
        '<span class="conteo__movil" aria-hidden="true"><span data-marcados>18</span>/25 ·</span>'
    )
    assert pc + "</span>" in caja
    assert movil in caja
    assert html.count("de 25 marcados") == 1
    assert '<span class="sr-only"><span data-marcados>18</span> de 25 marcados</span>' in caja
    enlaces = re.findall(r"<a [^>]*data-sin-marcar[^>]*>[^<]*</a>", caja)
    assert len(enlaces) == 2
    for enlace in enlaces:
        assert f'href="#fila-{lista[18].pk}"' in enlace
        assert enlace.endswith(">7 sin marcar</a>")
    assert "jornada-completa" not in html
    assert re.search(r"<p [^>]*data-cierre hidden>", caja)


def test_primera_vez_en_el_dia_todos_sin_marcar(cliente, seccion_docente, lista):
    html = abrir(cliente, seccion_docente)

    assert '<span class="sr-only"><span data-marcados>0</span> de 25 marcados</span>' in html
    assert "<strong data-marcados>0</strong>/25 marcados" in html
    assert ">25 sin marcar</a>" in html
    assert html.count("data-estudiante=") == 25
    assert html.count("data-etiqueta>Sin marcar</span>") == 25
    assert "Sin cambios" in html


# 1.4 Selector y cabecera de la hoja (D1, D4)


def test_el_selector_va_en_la_cabecera_de_la_hoja(cliente, seccion_docente, lista):
    html = principal(abrir(cliente, seccion_docente))

    hoja = html.index('class="hoja-asistencia"')
    selector = html.index('role="group" aria-label="Semana del 26 al 30 de octubre"')
    cabecera = html.index(
        '<div class="hoja-cabecera"><span>25 estudiantes activos</span><span>Hoy</span></div>'
    )
    assert hoja < selector < cabecera < html.index(LISTA)
    assert html.count("Solo puedes marcar hoy.") == 1
    assert selector < html.index("Solo puedes marcar hoy.") < cabecera
    assert html.index("data-sin-conexion") < hoja, "la tarjeta va antes de la hoja"


def test_el_selector_tiene_hoy_como_unico_dia_activo(cliente, seccion_docente, lista):
    html = abrir(cliente, seccion_docente)

    dias = botones(html, "dia")
    assert len(dias) == 5, "un solo selector"
    hoy = [d for d in dias if 'aria-current="date"' in d]
    assert len(hoy) == 1
    assert 'aria-label="Mié 28 de octubre, hoy"' in hoy[0]
    assert "aria-disabled" not in hoy[0]
    assert all('aria-disabled="true"' in d for d in dias if d not in hoy)
    assert 'aria-label="Lun 26 de octubre, no disponible"' in html
    assert 'aria-label="Vie 30 de octubre, no disponible"' in html
    flechas = botones(html, "flecha")
    assert len(flechas) == 2
    assert all('aria-disabled="true"' in f for f in flechas)
    assert 'aria-label="Semana anterior no disponible"' in html
    assert 'aria-label="Semana siguiente no disponible"' in html
    assert not re.search(r"<button[^>]* disabled[ >]", html), "aria-disabled, no disabled"


def test_la_semana_que_cruza_de_mes_lo_dice(cliente, seccion_docente, lista, hoy_miercoles):
    hoy_miercoles["valor"] = datetime.date(2026, 10, 1)

    html = abrir(cliente, seccion_docente)

    assert 'aria-label="Semana del 28 de septiembre al 2 de octubre"' in html
    assert 'aria-label="Jue 1 de octubre, hoy"' in html


# 1.5 Filas (D3)


def test_las_filas_van_en_orden_con_nombre_completo_y_su_circulo(cliente, seccion_docente, lista):
    html = abrir(cliente, seccion_docente)

    posiciones = [html.index(f'id="fila-{e.pk}"') for e in lista]
    assert posiciones == sorted(posiciones)
    primera = fila(html, lista[0])
    assert f'data-estudiante="{lista[0].pk}"' in primera
    assert 'data-estado=""' in primera
    assert '<span class="fila__numero" aria-hidden="true">01</span>' in primera
    nombre_html = '<span class="estudiante__nombre"><strong>AGUILAR FLORES,</strong> LUCIANA</span>'
    assert nombre_html in primera
    assert texto(nombre_html) == "AGUILAR FLORES, LUCIANA"
    assert primera.index(nombre_html) < primera.index("data-etiqueta>Sin marcar</span>")
    assert re.search(r"<button [^>]*data-marcar ", primera)
    assert 'aria-label="AGUILAR FLORES, LUCIANA: Sin marcar. Cambiar a Asistió"' in primera
    assert 'class="estado estado--sin-marcar"' in primera
    assert f'id="fallo-{lista[0].pk}" data-fallo hidden' in primera
    assert f'id="nota-{lista[0].pk}"' in primera
    assert '<span class="fila__numero" aria-hidden="true">25</span>' in fila(html, lista[24])


@pytest.mark.parametrize(
    ("estado", "palabra", "siguiente", "clase"),
    [
        ("ASISTIO", "Asistió", "Faltó", "estado--asistio"),
        ("FALTO", "Faltó", "Tarde", "estado--falto"),
        ("TARDE", "Tarde", "Justificado", "estado--tarde"),
        ("JUSTIFICADO", "Justificado", "Asistió", "estado--justificado"),
    ],
)
def test_un_estado_guardado_se_dibuja_en_palabras_y_en_el_circulo(
    cliente, seccion_docente, lista, estado, palabra, siguiente, clase
):
    poner(seccion_docente, [lista[2]], estado)

    html = fila(abrir(cliente, seccion_docente), lista[2])

    assert f"data-etiqueta>{palabra}</span>" in html
    assert f'aria-label="{nombre(lista[2])}: {palabra}. Cambiar a {siguiente}"' in html
    assert f'class="estado {clase}"' in html
    assert f'data-estado="{estado}"' in html


def test_la_nota_se_ve_solo_en_justificado(cliente, seccion_docente, lista):
    poner(seccion_docente, [lista[1]], "JUSTIFICADO", "Constancia entregada a la docente")
    poner(seccion_docente, [lista[2]], "FALTO")

    html = abrir(cliente, seccion_docente)

    justificado = fila(html, lista[1])
    assert re.search(r"<div [^>]*data-nota>", justificado)
    assert re.search(r"Nota de justificación <span [^>]*>\(opcional\)</span>", justificado)
    assert 'maxlength="100"' in justificado
    assert 'placeholder="Ej.: constancia entregada"' in justificado
    assert 'value="Constancia entregada a la docente"' in justificado
    assert f'aria-describedby="ayuda-nota-{lista[1].pk}"' in justificado
    assert "<span data-contador>33</span>/100" in justificado
    for otro in (lista[0], lista[2]):
        assert re.search(r"<div [^>]*data-nota hidden>", fila(html, otro))
        assert 'maxlength="100"' in fila(html, otro)


# 1.6 Leyenda


LEYENDA = ["Sin marcar", "Asistió", "Faltó", "Tarde", "Justificado"]
NOTA_LEYENDA = "Después de Justificado, sigue Asistió. Una marca guardada ya no queda Sin marcar."


def test_la_leyenda_lateral_tiene_los_cinco_estados(cliente, seccion_docente, lista):
    html = principal(abrir(cliente, seccion_docente))

    inicio = html.index('class="leyenda leyenda--lateral"')
    lateral = html[inicio : html.index("</div>", inicio)]
    assert "Cada toque cambia el estado" in lateral
    assert re.findall(r"<li>.*?<span>([^<]+)</span></li>", lateral, re.DOTALL) == LEYENDA
    assert lateral.count('class="estado ') == 5
    assert NOTA_LEYENDA in lateral
    assert inicio < html.index('class="hoja-asistencia"'), "en el lateral, bajo la tarjeta"


def test_la_leyenda_del_celular_es_plegable(cliente, seccion_docente, lista):
    html = principal(abrir(cliente, seccion_docente))

    inicio = html.index('<details class="leyenda leyenda--plegable">')
    plegable = html[inicio : html.index("</details>", inicio)]
    assert re.search(r"<summary>Un toque cambia el estado", plegable)
    assert re.findall(r"<li>.*?<span>([^<]+)</span></li>", plegable, re.DOTALL) == LEYENDA
    assert NOTA_LEYENDA in plegable
    assert html.index('class="hoja-asistencia"') < inicio < html.index(LISTA)


# 1.7 Inactivos, «Deshacer», anuncio y «Sin conexión» (D1, D5)


def test_los_no_activos_van_al_final_sin_circulo_y_sin_contar(cliente, seccion_docente, lista):
    retirado = Estudiante.objects.create(
        seccion=seccion_docente, apellidos="ESPINOZA VARGAS", nombres="RENATO", estado="RETIRADO"
    )
    Estudiante.objects.create(
        seccion=seccion_docente,
        apellidos="PAREDES QUISPE",
        nombres="VALENTINA",
        estado="TRASLADADO",
    )

    html = abrir(cliente, seccion_docente)

    assert html.count("data-estudiante=") == 25
    assert "<span data-marcados>0</span> de 25 marcados" in html
    inicio = html.index("data-fuera-registro")
    assert inicio > html.index(f'id="fila-{lista[24].pk}"')
    fuera = html[inicio:]
    assert "Fuera del registro de hoy" in fuera
    assert "No cuentan entre los 25 estudiantes." in fuera
    assert "ESPINOZA VARGAS, RENATO" in texto(fuera)
    assert re.search(r"<span [^>]*data-marca-fuera>RETIRADO</span>", fuera)
    assert re.search(r"<span [^>]*data-marca-fuera>TRASLADADO</span>", fuera)
    assert "ESPINOZA VARGAS, RENATO:" not in html, "sin círculo"
    assert f'id="fila-{retirado.pk}"' not in html


def test_sin_no_activos_no_hay_seccion_fuera_del_registro(cliente, seccion_docente, lista):
    assert "Fuera del registro de hoy" not in abrir(cliente, seccion_docente)


def test_sin_javascript_lo_dice_y_la_pantalla_carga_su_script(cliente, seccion_docente, lista):
    html = abrir(cliente, seccion_docente)

    assert "<noscript>" in html
    assert "Activa JavaScript para registrar la asistencia." in html
    assert "js/asistencia.js" in html
    assert 'id="anuncio" class="sr-only" role="status" aria-live="polite"' in html
    barra = re.search(r"<div [^>]*data-barra-deshacer hidden>.*?</div>", html, re.DOTALL)
    assert "data-deshacer-mensaje" in barra.group(0)
    deshacer = 'data-deshacer>Deshacer <span data-segundos aria-hidden="true">(5)</span></button>'
    assert deshacer in barra.group(0)


def test_sin_conexion_va_justo_despues_de_la_tarjeta(cliente, seccion_docente, lista):
    html = principal(abrir(cliente, seccion_docente))

    envoltorio = re.search(
        r"<div [^>]*data-sin-conexion hidden>(.*?)</div></div>\s*</div>", html, re.DOTALL
    )
    assert envoltorio
    aviso = envoltorio.group(1)
    assert 'class="message message--error"' in aviso
    assert "Sin conexión" in aviso
    assert "Tus marcas se guardarán cuando vuelva la señal. No cierres esta pantalla." in aviso
    assert html.count("data-sin-conexion") == 1
    assert html.index('class="tarjeta-jornada"') < envoltorio.start()
    assert envoltorio.start() < html.index("data-marcar-todos", envoltorio.start())


def test_la_pantalla_lleva_las_rutas_de_guardado(cliente, seccion_docente, lista):
    html = abrir(cliente, seccion_docente)

    assert f'data-url-restantes="{url_restantes(seccion_docente)}"' in html
    # La de cada fila la arma el JS con el id del estudiante; aquí, con el marcador 0.
    plantilla = reverse("asistencia:marcar", args=[seccion_docente.pk, MIERCOLES, 0])
    assert f'data-url-marcar="{plantilla}"' in html
    assert 'data-fecha="2026-10-28"' in html
    assert f'data-seccion="{seccion_docente.pk}"' in html


# 1.8 Fin de semana y sección sin estudiantes (D5)


def vacio(contenido):
    return re.search(r'<div class="empty">.*?</div>', contenido, re.DOTALL).group(0)


def test_el_sabado_no_hay_clases(cliente, seccion_docente, lista, hoy_miercoles):
    hoy_miercoles["valor"] = SABADO

    html = abrir(cliente, seccion_docente)
    contenido = principal(html)

    caja = vacio(contenido)
    assert caja.index("Hoy no hay clases") < caja.index(
        "La asistencia se registra de lunes a viernes."
    )
    assert "Sábado 31 de octubre" in contenido
    assert "data-estudiante=" not in html
    assert "restantes como Asistió" not in html
    assert "tarjeta-jornada" not in html
    assert 'aria-current="date"' not in html
    assert len(botones(html, "dia")) == 5
    assert 'aria-label="Semana del 26 al 30 de octubre"' in html
    assert "asistencia.js" not in html
    assert not Jornada.objects.exists()


def test_sin_estudiantes_un_vacio_lleva_a_la_lista(cliente, seccion_docente):
    html = abrir(cliente, seccion_docente)

    caja = vacio(principal(html))
    assert caja.index("Tu sección aún no tiene estudiantes") < caja.index(
        "Agrégalos para poder tomar asistencia."
    )
    url_lista = reverse("estudiantes:lista", args=[seccion_docente.pk])
    assert re.search(rf'<a [^>]*href="{url_lista}">Ver estudiantes</a>', caja)
    assert "data-estudiante=" not in html
    assert "tarjeta-jornada" not in html
    assert "asistencia.js" not in html
    assert not Jornada.objects.exists()


def test_solo_con_retirados_es_una_seccion_sin_estudiantes(cliente, seccion_docente):
    Estudiante.objects.create(
        seccion=seccion_docente, apellidos="ESPINOZA", nombres="RENATO", estado="RETIRADO"
    )

    assert "Tu sección aún no tiene estudiantes" in abrir(cliente, seccion_docente)
