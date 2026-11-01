"""Acceso a la hoja de notas (spec registro-notas, "Acceso a la hoja de notas"; design D8).

Las dos rutas usan ``SeccionDocenteMixin``, como las competencias: otra docente, un año CERRADO o
una sección inexistente es 403 con registro (US-004) en GET y POST antes de llegar al servicio;
otro rol y sin sesión, ``RolRequeridoMixin``. Ningún caso de error guarda notas. El día se fija con
el fixture ``hoy`` (30 de octubre).
"""

import datetime
import json

import pytest
from django.urls import reverse

from actividad.tests.intentos import es_sin_permiso, intentos, motivos
from institucion.models import AnioEscolar, Periodo, Seccion
from notas.models import Calificacion
from notas.tests.conftest import MATEMATICA, competencia, crear_estudiantes, ids_de, marcar

pytestmark = pytest.mark.django_db

HTMX = {"HTTP_HX_REQUEST": "true"}


@pytest.fixture(autouse=True)
def hoy(hoy):
    return hoy


@pytest.fixture
def entrar(client):
    def entrar_como(usuario):
        client.force_login(usuario)
        return client

    return entrar_como


@pytest.fixture
def hoja_lista(seccion_tutora, bimestres):
    """Matemática marcada en el bimestre 3, con la estudiante ficticia Ana Quispe."""
    marcar(seccion_tutora, bimestres[2], ids_de(MATEMATICA))
    (ana,) = crear_estudiantes(seccion_tutora, "QUISPE, ANA")
    return ana


def url_hoja(seccion):
    return reverse("notas:hoja", args=[seccion.pk])


def url_guardar(seccion, numero=3, area=MATEMATICA):
    return reverse("notas:guardar", args=[seccion.pk, numero, area])


def guardar(cliente, seccion, estudiante_id=1, numero=3, **extra):
    cuerpo = {
        "celdas": [
            {
                "estudiante": estudiante_id,
                "competencia": competencia(MATEMATICA, 1).pk,
                "nivel": "A",
                "conclusion": "",
                "base": None,
            }
        ]
    }
    return cliente.post(
        url_guardar(seccion, numero),
        json.dumps(cuerpo),
        content_type="application/json",
        **extra,
    )


# --- Rutas (D8) ---


def test_las_dos_rutas_estan_bajo_la_seccion(seccion_tutora):
    base = f"/docente/secciones/{seccion_tutora.pk}/notas/"

    assert url_hoja(seccion_tutora) == base
    assert url_guardar(seccion_tutora, 3, MATEMATICA) == f"{base}3/{MATEMATICA}/"


def test_la_hoja_no_acepta_post_ni_el_guardado_get(entrar, docente, seccion_tutora, bimestres):
    cliente = entrar(docente)

    assert cliente.post(url_hoja(seccion_tutora)).status_code == 405
    assert cliente.get(url_guardar(seccion_tutora)).status_code == 405


# --- Acceso ---


def test_la_docente_de_la_seccion_abre_su_hoja(entrar, docente, seccion_tutora, hoja_lista):
    assert entrar(docente).get(url_hoja(seccion_tutora)).status_code == 200


def test_la_docente_de_la_seccion_guarda_su_hoja(entrar, docente, seccion_tutora, hoja_lista):
    respuesta = guardar(entrar(docente), seccion_tutora, hoja_lista.pk)

    assert respuesta.status_code == 200
    assert Calificacion.objects.get().nivel == "A"


def test_abrir_la_hoja_no_guarda_notas(entrar, docente, seccion_tutora, hoja_lista):
    entrar(docente).get(url_hoja(seccion_tutora))

    assert not Calificacion.objects.exists()


@pytest.mark.parametrize("cabeceras", [{}, HTMX])
def test_otra_docente_recibe_403_y_no_guarda(
    entrar, otra_docente, seccion_tutora, hoja_lista, cabeceras
):
    """Escenario "Sección de otra docente" (y "Intento registrado" de acceso-secciones)."""
    cliente = entrar(otra_docente)

    assert es_sin_permiso(cliente.get(url_hoja(seccion_tutora), **cabeceras))
    assert es_sin_permiso(guardar(cliente, seccion_tutora, hoja_lista.pk, **cabeceras))
    assert not Calificacion.objects.exists()
    seccion = str(seccion_tutora.pk)
    assert intentos() == [
        (seccion, f"/docente/secciones/{seccion}/notas/", "ajena"),
        (seccion, url_guardar(seccion_tutora), "ajena"),
    ]


def test_la_seccion_de_un_anio_cerrado_da_403_y_no_guarda(entrar, docente, institucion):
    """Escenario "Sección de un año cerrado"."""
    anio = AnioEscolar.objects.create(institucion=institucion, anio=2026, estado="CERRADO")
    cerrada = Seccion.objects.create(anio_escolar=anio, grado=2, nombre="A", docente=docente)
    periodo = Periodo.objects.create(
        anio_escolar=anio,
        numero=1,
        fecha_inicio=datetime.date(2026, 3, 9),
        fecha_fin=datetime.date(2026, 5, 15),
    )
    marcar(cerrada, periodo, ids_de(MATEMATICA))
    (ana,) = crear_estudiantes(cerrada, "QUISPE, ANA")
    cliente = entrar(docente)

    assert es_sin_permiso(cliente.get(url_hoja(cerrada)))
    assert es_sin_permiso(guardar(cliente, cerrada, ana.pk, numero=1))
    assert not Calificacion.objects.exists()
    assert motivos() == ["anio_cerrado", "anio_cerrado"]


def test_una_seccion_que_no_existe_da_403(entrar, docente, seccion_tutora, hoja_lista):
    cliente = entrar(docente)

    assert es_sin_permiso(cliente.get(reverse("notas:hoja", args=[99999])))
    assert motivos() == ["inexistente"]


def test_la_consulta_no_va_en_la_ruta_registrada(entrar, otra_docente, seccion_tutora, hoja_lista):
    """Escenario "Intento sin permiso" de registro-actividad: solo la ruta, sin la consulta."""
    entrar(otra_docente).get(f"{url_hoja(seccion_tutora)}?area=QUISPE")

    assert intentos() == [(str(seccion_tutora.pk), url_hoja(seccion_tutora), "ajena")]


def test_la_direccion_llega_a_su_pantalla(entrar, direccion, seccion_tutora, hoja_lista):
    """Escenario "Otro rol"."""
    cliente = entrar(direccion)

    assert cliente.get(url_hoja(seccion_tutora)).url == "/direccion/"
    assert guardar(cliente, seccion_tutora, hoja_lista.pk).url == "/direccion/"
    assert not Calificacion.objects.exists()


def test_sin_sesion_va_a_ingresar_con_next(client, seccion_tutora):
    """Escenario "Sin sesión"."""
    respuesta = client.get(url_hoja(seccion_tutora))

    assert respuesta.status_code == 302
    assert respuesta.url == f"/ingresar/?next={url_hoja(seccion_tutora)}"


def test_sin_sesion_un_guardado_con_htmx_recibe_hx_redirect(client, seccion_tutora, hoja_lista):
    respuesta = guardar(client, seccion_tutora, hoja_lista.pk, **HTMX)

    assert respuesta.status_code == 200
    assert respuesta["HX-Redirect"] == "/ingresar/?next=/docente/"
    assert not Calificacion.objects.exists()


def test_con_la_sesion_vencida_un_guardado_con_htmx_recibe_hx_redirect(
    entrar, docente, seccion_tutora, hoja_lista
):
    """Escenario "Guardar con la sesión vencida" (servidor): no se guarda nada."""
    cliente = entrar(docente)
    sesion = cliente.session
    sesion["ultima_actividad"] = 0
    sesion.save()

    respuesta = guardar(cliente, seccion_tutora, hoja_lista.pk, **HTMX)

    assert respuesta.status_code == 200
    assert respuesta["HX-Redirect"] == "/ingresar/?next=/docente/"
    assert not Calificacion.objects.exists()
