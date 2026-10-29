"""Vistas de la asistencia de hoy (spec asistencia-jornada; design de US-030, D3 y D10).

Rutas y acceso (la docente de la sección, otra docente, año CERRADO, otro rol, sin sesión y HTMX),
CSRF y las respuestas sin cuerpo de los guardados: 204, 400, 404 y 409. El día se fija parcheando
``timezone.localdate``; el HTML de la pantalla se prueba en la parte B.
"""

import datetime

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from asistencia.models import Asistencia, Jornada
from institucion.models import AnioEscolar, Estudiante, Seccion

pytestmark = pytest.mark.django_db

HTMX = {"HTTP_HX_REQUEST": "true"}
MIERCOLES = datetime.date(2026, 10, 28)
SABADO = datetime.date(2026, 10, 31)


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


def test_otra_docente_recibe_404_y_no_guarda(entrar, otra_docente, seccion_docente, estudiante):
    cliente = entrar(otra_docente)

    assert cliente.get(url_hoy(seccion_docente)).status_code == 404
    marcar = cliente.post(url_marcar(seccion_docente, estudiante), {"estado": "ASISTIO"})
    restantes = cliente.post(url_restantes(seccion_docente), {"estudiante": [estudiante.pk]})

    assert (marcar.status_code, restantes.status_code) == (404, 404)
    assert not Jornada.objects.exists()


def test_una_seccion_del_anio_cerrado_da_404(entrar, docente, institucion):
    anio = AnioEscolar.objects.create(institucion=institucion, anio=2026, estado="CERRADO")
    cerrada = Seccion.objects.create(anio_escolar=anio, grado=2, nombre="A", docente=docente)

    assert entrar(docente).get(url_hoy(cerrada)).status_code == 404


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


def test_un_estudiante_de_otra_seccion_responde_404(cliente, seccion_docente, anio_abierto):
    otra = Seccion.objects.create(anio_escolar=anio_abierto, grado=3, nombre="B")
    ajeno = Estudiante.objects.create(seccion=otra, apellidos="ROJAS", nombres="LUIS")

    respuesta = cliente.post(url_marcar(seccion_docente, ajeno), {"estado": "ASISTIO"})

    assert respuesta.status_code == 404
    assert not Jornada.objects.exists()


def test_un_estudiante_retirado_responde_404(cliente, seccion_docente, estudiante):
    estudiante.estado = Estudiante.Estado.RETIRADO
    estudiante.save()

    respuesta = cliente.post(url_marcar(seccion_docente, estudiante), {"estado": "ASISTIO"})

    assert respuesta.status_code == 404
    assert respuesta.content == b""


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

    aviso = html[html.index("mensaje--exito") : html.index('<ol class="estudiantes"')]
    assert "2 estudiantes importados" in aviso
    enlace = (
        f'<a class="mensaje-enlace" href="{url_hoy(seccion_docente)}">Tomar la asistencia de hoy'
    )
    assert enlace in aviso
    assert "hx-get" not in aviso, "un enlace normal: también en el diálogo abre la página completa"


def test_sin_aviso_de_importados_no_hay_enlace_a_la_asistencia(cliente, seccion_docente):
    Estudiante.objects.create(seccion=seccion_docente, apellidos="QUISPE", nombres="ANA")

    html = cliente.get(reverse("estudiantes:lista", args=[seccion_docente.pk])).content.decode()

    assert "Tomar la asistencia de hoy" not in html
