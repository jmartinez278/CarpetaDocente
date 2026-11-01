"""Acceso a la pantalla de competencias (spec competencias-periodo, "Acceso a las competencias de su
sección"; design de US-029, D8).

Las dos rutas usan ``SeccionDocenteMixin``, como la asistencia: otra docente o un año CERRADO es 404
en GET y POST antes de llegar al servicio; otro rol y sin sesión, ``RolRequeridoMixin``. El día se
fija parcheando ``timezone.localdate``.
"""

import datetime
import re

import pytest
from django.urls import reverse
from django.utils import timezone

from institucion.models import AnioEscolar, Periodo, Seccion
from notas.models import CompetenciaPeriodo
from notas.tests.conftest import OCT_30, ids_de

pytestmark = pytest.mark.django_db

HTMX = {"HTTP_HX_REQUEST": "true"}


@pytest.fixture(autouse=True)
def hoy_30_de_octubre(monkeypatch):
    monkeypatch.setattr(timezone, "localdate", lambda *args, **kwargs: OCT_30)


@pytest.fixture
def entrar(client):
    def entrar_como(usuario):
        client.force_login(usuario)
        return client

    return entrar_como


def url_pantalla(seccion):
    return reverse("competencias:pantalla", args=[seccion.pk])


def url_guardar(seccion, numero=3):
    return reverse("competencias:guardar", args=[seccion.pk, numero])


def guardar(cliente, seccion, numero=3, **extra):
    return cliente.post(
        url_guardar(seccion, numero), {"competencia": sorted(ids_de("063"))}, **extra
    )


# --- Rutas (D8) ---


def test_las_dos_rutas_estan_bajo_la_seccion(seccion_tutora):
    base = f"/docente/secciones/{seccion_tutora.pk}/competencias/"

    assert url_pantalla(seccion_tutora) == base
    assert url_guardar(seccion_tutora, 3) == f"{base}3/"


def test_la_pantalla_no_acepta_post_ni_el_guardado_get(entrar, docente, seccion_tutora, bimestres):
    cliente = entrar(docente)

    assert cliente.post(url_pantalla(seccion_tutora)).status_code == 405
    assert cliente.get(url_guardar(seccion_tutora)).status_code == 405


# --- Acceso ---


def test_la_docente_de_la_seccion_abre_sus_competencias(entrar, docente, seccion_tutora, bimestres):
    assert entrar(docente).get(url_pantalla(seccion_tutora)).status_code == 200


def test_abrir_la_pantalla_no_guarda_marcas(entrar, docente, seccion_tutora, bimestres):
    entrar(docente).get(url_pantalla(seccion_tutora))

    assert not CompetenciaPeriodo.objects.exists()


def test_otra_docente_recibe_404_y_no_guarda(entrar, otra_docente, seccion_tutora, bimestres):
    """Escenario "Sección de otra docente"."""
    cliente = entrar(otra_docente)

    assert cliente.get(url_pantalla(seccion_tutora)).status_code == 404
    assert guardar(cliente, seccion_tutora).status_code == 404
    assert not CompetenciaPeriodo.objects.exists()


def test_la_seccion_de_un_anio_cerrado_da_404_y_no_guarda(entrar, docente, institucion):
    """Escenario "Sección de un año cerrado"."""
    anio = AnioEscolar.objects.create(institucion=institucion, anio=2026, estado="CERRADO")
    cerrada = Seccion.objects.create(anio_escolar=anio, grado=2, nombre="A", docente=docente)
    Periodo.objects.create(
        anio_escolar=anio,
        numero=1,
        fecha_inicio=datetime.date(2026, 3, 9),
        fecha_fin=datetime.date(2026, 5, 15),
    )
    cliente = entrar(docente)

    assert cliente.get(url_pantalla(cerrada)).status_code == 404
    assert guardar(cliente, cerrada, numero=1).status_code == 404
    assert not CompetenciaPeriodo.objects.exists()


def test_una_seccion_que_no_existe_da_404(entrar, docente, seccion_tutora):
    cliente = entrar(docente)

    assert cliente.get(reverse("competencias:pantalla", args=[99999])).status_code == 404


def test_la_direccion_llega_a_su_pantalla(entrar, direccion, seccion_tutora, bimestres):
    """Escenario "Otro rol"."""
    cliente = entrar(direccion)

    assert cliente.get(url_pantalla(seccion_tutora)).url == "/direccion/"
    assert guardar(cliente, seccion_tutora).url == "/direccion/"
    assert not CompetenciaPeriodo.objects.exists()


def test_sin_sesion_va_a_ingresar_con_next(client, seccion_tutora):
    """Escenario "Sin sesión"."""
    respuesta = client.get(url_pantalla(seccion_tutora))

    assert respuesta.status_code == 302
    assert respuesta.url == f"/ingresar/?next={url_pantalla(seccion_tutora)}"


def test_sin_sesion_un_guardado_con_htmx_recibe_hx_redirect(client, seccion_tutora, bimestres):
    respuesta = guardar(client, seccion_tutora, **HTMX)

    assert respuesta.status_code == 200
    assert respuesta["HX-Redirect"] == "/ingresar/?next=/docente/"
    assert not CompetenciaPeriodo.objects.exists()


def test_con_la_sesion_vencida_un_guardado_con_htmx_recibe_hx_redirect(
    entrar, docente, seccion_tutora, bimestres
):
    cliente = entrar(docente)
    sesion = cliente.session
    sesion["ultima_actividad"] = 0
    sesion.save()

    respuesta = guardar(cliente, seccion_tutora, **HTMX)

    assert respuesta.status_code == 200
    assert respuesta["HX-Redirect"] == "/ingresar/?next=/docente/"
    assert not CompetenciaPeriodo.objects.exists()


# --- Portada sin cambios ---


def test_la_portada_lleva_a_la_hoja_y_no_a_las_competencias(
    entrar, docente, seccion_tutora, bimestres
):
    """Escenario "Portada sin cambios" (desde US-020): la tarjeta Notas lleva a la hoja."""
    html = entrar(docente).get(reverse("docente:portada")).content.decode()

    tarjetas = re.findall(r"<article\b.*?</article>", html, re.DOTALL)
    assert f'href="/docente/secciones/{seccion_tutora.pk}/notas/"' in tarjetas[1]
    assert "/competencias/" not in html
