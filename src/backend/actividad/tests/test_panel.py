"""Registro de actividad en el panel: solo lectura, solo el Administrador y filtros (D8, D11)."""

from datetime import UTC, datetime

import pytest
from django.db import transaction
from django.urls import reverse

from actividad.models import Operacion, RegistroActividad
from actividad.servicios import registrar
from actividad.tests.conftest import entrar

pytestmark = pytest.mark.django_db

URL_LISTA = "admin:actividad_registroactividad_changelist"
URL_FICHA = "admin:actividad_registroactividad_change"
URL_ALTA = "admin:actividad_registroactividad_add"
URL_BORRAR = "admin:actividad_registroactividad_delete"


def entrada(usuario, operacion, fecha_hora, **campos):
    """Crea una entrada con ``registrar`` y le fija la fecha (``default``, no ``auto_now``)."""
    with transaction.atomic():
        creada = registrar(usuario, operacion, **campos)
    RegistroActividad.objects.filter(pk=creada.pk).update(fecha_hora=fecha_hora)
    creada.refresh_from_db()
    return creada


@pytest.fixture
def una_entrada(docente):
    return entrada(
        docente,
        Operacion.REGISTRO_ASISTENCIA,
        datetime(2026, 10, 26, 3, 30, 15, tzinfo=UTC),
        entidad="jornada",
        entidad_id=7,
        detalle={"seccion": 3, "fecha": "2026-10-25"},
    )


@pytest.fixture
def panel(client, administrador):
    entrar(client, administrador)
    return client


def campos_de(entrada_guardada):
    return RegistroActividad.objects.values().get(pk=entrada_guardada.pk)


# --- Administrador: ve, pero no cambia nada -------------------------------------------------


def test_el_administrador_ve_la_lista_sin_agregar_ni_acciones(panel, una_entrada):
    respuesta = panel.get(reverse(URL_LISTA))

    assert respuesta.status_code == 200
    assert list(respuesta.context["cl"].result_list) == [una_entrada]
    assert not respuesta.context["has_add_permission"]
    assert respuesta.context["action_form"] is None
    assert reverse(URL_ALTA) not in respuesta.content.decode()


def test_la_lista_muestra_la_hora_de_lima(panel, una_entrada):
    respuesta = panel.get(reverse(URL_LISTA))

    # 03:30:15 UTC del 26-10 son las 22:30:15 del 25-10 en Lima.
    assert "25-10-2026 22:30:15" in respuesta.content.decode()


def test_la_ficha_se_ve_sin_campos_editables_ni_botones(panel, una_entrada):
    respuesta = panel.get(reverse(URL_FICHA, args=[una_entrada.pk]))

    assert respuesta.status_code == 200
    assert respuesta.context["adminform"].form.fields == {}
    html = respuesta.content.decode()
    for boton in ('name="_save"', 'name="_continue"', 'name="_addanother"'):
        assert boton not in html
    assert reverse(URL_BORRAR, args=[una_entrada.pk]) not in html


def test_post_a_agregar_responde_403_y_no_crea_nada(panel, docente):
    respuesta = panel.post(
        reverse(URL_ALTA), {"usuario": docente.pk, "operacion": Operacion.INICIO_SESION}
    )

    assert respuesta.status_code == 403
    assert RegistroActividad.objects.count() == 0


def test_post_a_la_ficha_responde_403_y_la_entrada_queda_igual(panel, una_entrada):
    antes = campos_de(una_entrada)

    respuesta = panel.post(
        reverse(URL_FICHA, args=[una_entrada.pk]),
        {"operacion": Operacion.INICIO_SESION, "entidad": "otra", "_save": "Guardar"},
    )

    assert respuesta.status_code == 403
    assert campos_de(una_entrada) == antes


def test_post_a_borrar_responde_403_y_la_entrada_sigue(panel, una_entrada):
    respuesta = panel.post(reverse(URL_BORRAR, args=[una_entrada.pk]), {"post": "yes"})

    assert respuesta.status_code == 403
    assert RegistroActividad.objects.filter(pk=una_entrada.pk).exists()


def test_borrar_en_lote_desde_la_lista_no_borra(panel, una_entrada):
    respuesta = panel.post(
        reverse(URL_LISTA),
        {"action": "delete_selected", "_selected_action": [una_entrada.pk], "post": "yes"},
    )

    assert respuesta.status_code in (200, 302, 403)
    assert RegistroActividad.objects.filter(pk=una_entrada.pk).exists()


# --- Ruta Infeliz: docente y dirección no entran -----------------------------------------


def rutas_del_registro(una_entrada):
    return {
        "lista": reverse(URL_LISTA),
        "ficha": reverse(URL_FICHA, args=[una_entrada.pk]),
    }


@pytest.mark.parametrize("rol", ["docente", "direccion"])
@pytest.mark.parametrize("ruta", ["lista", "ficha"])
def test_docente_y_direccion_no_entran_al_registro(client, request, una_entrada, rol, ruta):
    entrar(client, request.getfixturevalue(rol))
    antes = campos_de(una_entrada)

    respuesta = client.get(rutas_del_registro(una_entrada)[ruta])

    assert respuesta.status_code in (302, 403)
    if respuesta.status_code == 302:
        assert respuesta.url.startswith(reverse("admin:login"))
    assert campos_de(una_entrada) == antes


@pytest.mark.parametrize("rol", ["docente", "direccion"])
def test_docente_y_direccion_no_borran_ni_cambian_por_post(client, request, una_entrada, rol):
    entrar(client, request.getfixturevalue(rol))
    antes = campos_de(una_entrada)

    client.post(reverse(URL_FICHA, args=[una_entrada.pk]), {"operacion": "INICIO_SESION"})
    client.post(reverse(URL_BORRAR, args=[una_entrada.pk]), {"post": "yes"})

    assert campos_de(una_entrada) == antes


@pytest.mark.parametrize("rol", ["docente", "direccion"])
@pytest.mark.parametrize(
    ("metodo", "nombre"),
    [
        ("post", "admin:actividad_registroactividad_exportar"),
        ("get", "admin:actividad_registroactividad_indicadores"),
    ],
)
def test_docente_y_direccion_no_entran_a_exportar_ni_a_indicadores(
    client, request, una_entrada, rol, metodo, nombre
):
    entrar(client, request.getfixturevalue(rol))

    respuesta = getattr(client, metodo)(reverse(nombre))

    assert respuesta.status_code in (302, 403)
    if respuesta.status_code == 302:
        assert respuesta.url.startswith(reverse("admin:login"))
    assert list(RegistroActividad.objects.all()) == [una_entrada]


# --- Filtrar (escenario "Filtrar") -------------------------------------------------------


@pytest.fixture
def entradas_para_filtrar(docente, otra_docente):
    """La "semana pasada" es la del lunes 19 al domingo 25 de octubre de 2026 (hora de Lima)."""
    dentro = datetime(2026, 10, 21, 15, 0, tzinfo=UTC)
    return {
        "cumple": entrada(docente, Operacion.ASISTENCIA_CAMBIADA, dentro),
        # Domingo 25 a las 23:30 de Lima (04:30 UTC del lunes 26): aún dentro.
        "domingo_noche": entrada(
            docente, Operacion.ASISTENCIA_CAMBIADA, datetime(2026, 10, 26, 4, 30, tzinfo=UTC)
        ),
        "otra_docente": entrada(otra_docente, Operacion.ASISTENCIA_CAMBIADA, dentro),
        "otra_operacion": entrada(docente, Operacion.INICIO_SESION, dentro),
        # Lunes 26 a las 00:30 de Lima: ya fuera.
        "fuera_de_rango": entrada(
            docente, Operacion.ASISTENCIA_CAMBIADA, datetime(2026, 10, 26, 5, 30, tzinfo=UTC)
        ),
        "antes_de_rango": entrada(
            docente, Operacion.ASISTENCIA_CAMBIADA, datetime(2026, 10, 19, 4, 59, tzinfo=UTC)
        ),
    }


def test_filtrar_por_usuario_operacion_y_rango_de_fechas(panel, docente, entradas_para_filtrar):
    respuesta = panel.get(
        reverse(URL_LISTA),
        {
            "usuario__id__exact": docente.pk,
            "operacion__exact": Operacion.ASISTENCIA_CAMBIADA,
            "fecha_hora__desde": "2026-10-19",
            "fecha_hora__hasta": "2026-10-25",
        },
    )

    assert respuesta.status_code == 200
    esperadas = [entradas_para_filtrar["domingo_noche"], entradas_para_filtrar["cumple"]]
    assert list(respuesta.context["cl"].result_list) == esperadas


def test_el_rango_de_fechas_tiene_sus_campos_con_etiqueta(panel, entradas_para_filtrar):
    respuesta = panel.get(reverse(URL_LISTA))

    html = respuesta.content.decode()
    for campo in ("fecha_hora__desde", "fecha_hora__hasta"):
        assert f'name="{campo}"' in html
        assert f'for="id_{campo}"' in html


def test_solo_desde_filtra_hacia_adelante(panel, entradas_para_filtrar):
    respuesta = panel.get(reverse(URL_LISTA), {"fecha_hora__desde": "2026-10-26"})

    assert list(respuesta.context["cl"].result_list) == [entradas_para_filtrar["fuera_de_rango"]]


def test_una_fecha_invalida_no_rompe_la_lista(panel, entradas_para_filtrar):
    respuesta = panel.get(reverse(URL_LISTA), {"fecha_hora__desde": "no-es-fecha"})

    assert respuesta.status_code in (200, 302)
