"""Periodos en la ficha del año y organización en la de la institución (design de US-028, D5)."""

import datetime

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from actividad.models import Operacion, RegistroActividad
from institucion import servicios
from institucion.models import MENSAJE_CRUCE, AnioEscolar, Institucion, Periodo

pytestmark = pytest.mark.django_db

BIMESTRES = [
    ("2027-03-16", "2027-05-15"),
    ("2027-05-25", "2027-07-24"),
    ("2027-08-10", "2027-10-09"),
    ("2027-10-19", "2027-12-18"),
]
VACIAS = [("", "")] * 4


@pytest.fixture
def anio(anio_abierto):
    """Año 2027 ABIERTO de una institución organizada en bimestres, sin periodos."""
    institucion = anio_abierto.institucion
    institucion.organizacion_periodos = Institucion.OrganizacionPeriodos.BIMESTRE
    institucion.save()
    return anio_abierto


@pytest.fixture
def anio_con_periodos(anio):
    for numero, (inicio, fin) in enumerate(BIMESTRES, start=1):
        Periodo.objects.create(
            anio_escolar=anio,
            numero=numero,
            fecha_inicio=datetime.date.fromisoformat(inicio),
            fecha_fin=datetime.date.fromisoformat(fin),
        )
    return anio


def url_anio(anio):
    return reverse("admin:institucion_anioescolar_change", args=[anio.pk])


def url_institucion(institucion):
    return reverse("admin:institucion_institucion_change", args=[institucion.pk])


def formset(respuesta):
    """El formset de periodos de la ficha, o ``None`` si la ficha no lo tiene."""
    formsets = respuesta.context["inline_admin_formsets"]
    return formsets[0].formset if formsets else None


def datos_anio(anio, filas, estado=None, **extra):
    """POST de la ficha del año con ``filas`` (inicio, fin) en el formset ``periodos``."""
    guardados = list(anio.periodos.all())
    datos = {
        "institucion": anio.institucion_id,
        "anio": anio.anio,
        "estado": estado or anio.estado,
        "periodos-TOTAL_FORMS": len(filas),
        "periodos-INITIAL_FORMS": len(guardados),
        "periodos-MIN_NUM_FORMS": 0,
        "periodos-MAX_NUM_FORMS": len(filas),
    }
    for indice, (inicio, fin) in enumerate(filas):
        datos[f"periodos-{indice}-anio_escolar"] = anio.pk
        datos[f"periodos-{indice}-fecha_inicio"] = inicio
        datos[f"periodos-{indice}-fecha_fin"] = fin
        if indice < len(guardados):
            datos[f"periodos-{indice}-id"] = guardados[indice].pk
    datos.update(extra)
    return datos


def fechas(anio):
    return [(p.fecha_inicio.isoformat(), p.fecha_fin.isoformat()) for p in anio.periodos.all()]


def operaciones_de_periodos():
    return list(
        RegistroActividad.objects.filter(
            operacion__in=[Operacion.PERIODOS_CONFIGURADOS, Operacion.PERIODO_EDITADO]
        ).values_list("operacion", flat=True)
    )


# --- Qué muestra la ficha ---


@pytest.mark.parametrize(
    ("organizacion", "cantidad"),
    [
        (Institucion.OrganizacionPeriodos.BIMESTRE, 4),
        (Institucion.OrganizacionPeriodos.TRIMESTRE, 3),
    ],
)
def test_la_ficha_muestra_una_fila_por_periodo_numerada_y_sin_borrar(
    admin_client, anio, organizacion, cantidad
):
    anio.institucion.organizacion_periodos = organizacion
    anio.institucion.save()

    periodos = formset(admin_client.get(url_anio(anio)))

    assert [form.instance.numero for form in periodos.forms] == list(range(1, cantidad + 1))
    assert not periodos.can_delete


def test_al_crear_un_anio_no_hay_filas_de_periodos(admin_client, anio):
    respuesta = admin_client.get(reverse("admin:institucion_anioescolar_add"))

    assert formset(respuesta) is None


def test_sin_organizacion_la_ficha_avisa_con_el_enlace_y_sin_filas(admin_client, anio_abierto):
    respuesta = admin_client.get(url_anio(anio_abierto))

    assert formset(respuesta) is None
    contenido = respuesta.content.decode()
    assert servicios.SIN_ORGANIZACION in contenido
    assert url_institucion(anio_abierto.institucion) in contenido


# --- Guardar ---


def test_guardar_las_4_filas_crea_los_periodos_y_lo_registra(admin_client, admin_user, anio):
    respuesta = admin_client.post(url_anio(anio), datos_anio(anio, BIMESTRES))

    assert respuesta.status_code == 302
    assert list(anio.periodos.values_list("numero", flat=True)) == [1, 2, 3, 4]
    assert fechas(anio) == BIMESTRES
    entrada = RegistroActividad.objects.get(operacion=Operacion.PERIODOS_CONFIGURADOS)
    assert entrada.usuario == admin_user
    assert entrada.detalle == {"periodos": 4}


def test_editar_dos_periodos_los_corrige_sin_cambiar_su_id(admin_client, anio_con_periodos):
    ids = list(anio_con_periodos.periodos.values_list("id", flat=True))
    filas = [("2027-03-16", "2027-05-10"), ("2027-05-11", "2027-07-24"), *BIMESTRES[2:]]

    respuesta = admin_client.post(url_anio(anio_con_periodos), datos_anio(anio_con_periodos, filas))

    assert respuesta.status_code == 302
    assert fechas(anio_con_periodos) == filas
    assert list(anio_con_periodos.periodos.values_list("id", flat=True)) == ids
    assert operaciones_de_periodos() == [Operacion.PERIODO_EDITADO] * 2


@pytest.mark.parametrize(
    ("filas", "fila", "mensaje"),
    [
        (
            [("2027-05-15", "2027-03-16"), *BIMESTRES[1:]],
            1,
            servicios.FIN_ANTES_DEL_INICIO,
        ),
        (
            [*BIMESTRES[:3], ("2027-10-19", "2028-01-05")],
            4,
            servicios.mensaje_fuera_del_anio(2027),
        ),
        (
            [BIMESTRES[0], ("2027-05-15", "2027-07-24"), *BIMESTRES[2:]],
            2,
            MENSAJE_CRUCE,
        ),
        (
            [("2027-06-01", "2027-07-31"), ("2027-03-16", "2027-05-15"), *BIMESTRES[2:]],
            2,
            servicios.mensaje_orden(2),
        ),
        ([*BIMESTRES[:3], ("", "")], None, servicios.mensaje_incompletas(4)),
        ([*BIMESTRES[:3], ("2027-10-19", "")], None, servicios.mensaje_incompletas(4)),
    ],
    ids=["fin-antes", "fuera-del-anio", "cruce", "orden", "falta-una", "falta-un-fin"],
)
def test_cada_regla_muestra_su_mensaje_en_la_ficha_y_no_guarda_nada(
    admin_client, anio, filas, fila, mensaje
):
    respuesta = admin_client.post(url_anio(anio), datos_anio(anio, filas))

    assert respuesta.status_code == 200
    periodos = formset(respuesta)
    if fila is None:
        assert mensaje in periodos.non_form_errors()
    else:
        assert mensaje in periodos.forms[fila - 1].non_field_errors()
    assert mensaje in respuesta.content.decode()
    assert not Periodo.objects.exists()
    assert not operaciones_de_periodos()


def test_vaciar_las_filas_de_un_anio_con_periodos_se_rechaza(admin_client, anio_con_periodos):
    respuesta = admin_client.post(
        url_anio(anio_con_periodos), datos_anio(anio_con_periodos, VACIAS)
    )

    assert respuesta.status_code == 200
    assert servicios.mensaje_incompletas(4) in formset(respuesta).non_form_errors()
    assert fechas(anio_con_periodos) == BIMESTRES


def test_editar_el_estado_con_las_filas_vacias_guarda_el_anio_sin_periodos(admin_client, anio):
    respuesta = admin_client.post(url_anio(anio), datos_anio(anio, VACIAS, estado="CERRADO"))

    assert respuesta.status_code == 302
    anio.refresh_from_db()
    assert anio.estado == AnioEscolar.Estado.CERRADO
    assert not Periodo.objects.exists()


def test_cerrar_un_anio_con_periodos_sin_tocarlos_lo_cierra(admin_client, anio_con_periodos):
    respuesta = admin_client.post(
        url_anio(anio_con_periodos), datos_anio(anio_con_periodos, BIMESTRES, estado="CERRADO")
    )

    assert respuesta.status_code == 302
    anio_con_periodos.refresh_from_db()
    assert anio_con_periodos.estado == AnioEscolar.Estado.CERRADO
    assert fechas(anio_con_periodos) == BIMESTRES


def test_un_post_con_delete_no_borra_periodos(admin_client, anio_con_periodos):
    datos = datos_anio(anio_con_periodos, BIMESTRES, **{"periodos-0-DELETE": "on"})

    admin_client.post(url_anio(anio_con_periodos), datos)

    assert anio_con_periodos.periodos.count() == 4


def test_un_cruce_que_llega_al_guardado_muestra_el_mensaje_sin_500(admin_client, anio, monkeypatch):
    def cruce(*args, **kwargs):
        raise ValidationError(MENSAJE_CRUCE)

    monkeypatch.setattr(servicios, "guardar_periodos", cruce)

    respuesta = admin_client.post(url_anio(anio), datos_anio(anio, BIMESTRES))

    assert respuesta.status_code == 200
    assert MENSAJE_CRUCE in formset(respuesta).non_form_errors()
    assert not Periodo.objects.exists()
    assert not RegistroActividad.objects.filter(operacion=Operacion.ANIO_EDITADO).exists()


# --- Año cerrado ---


def test_anio_cerrado_muestra_los_periodos_de_solo_lectura(admin_client, anio_con_periodos):
    anio_con_periodos.estado = AnioEscolar.Estado.CERRADO
    anio_con_periodos.save()

    inline = admin_client.get(url_anio(anio_con_periodos)).context["inline_admin_formsets"][0]

    assert not inline.has_change_permission
    assert not inline.has_add_permission


def test_anio_cerrado_sin_periodos_no_tiene_filas_para_llenar(admin_client, anio):
    anio.estado = AnioEscolar.Estado.CERRADO
    anio.save()

    assert formset(admin_client.get(url_anio(anio))).forms == []


def test_anio_cerrado_un_post_que_cambia_las_fechas_no_las_cambia(admin_client, anio_con_periodos):
    anio_con_periodos.estado = AnioEscolar.Estado.CERRADO
    anio_con_periodos.save()
    filas = [("2027-03-01", "2027-05-10"), *BIMESTRES[1:]]

    admin_client.post(url_anio(anio_con_periodos), datos_anio(anio_con_periodos, filas))

    assert fechas(anio_con_periodos) == BIMESTRES
    assert not operaciones_de_periodos()


def test_con_periodos_la_institucion_del_anio_es_de_solo_lectura(admin_client, anio_con_periodos):
    respuesta = admin_client.get(url_anio(anio_con_periodos))

    assert "institucion" not in respuesta.context["adminform"].form.fields


def test_con_periodos_un_post_que_cambia_la_institucion_no_la_cambia(
    admin_client, anio_con_periodos
):
    otra = Institucion.objects.create(nombre="Otra I.E. ficticia")
    original = anio_con_periodos.institucion_id

    admin_client.post(
        url_anio(anio_con_periodos),
        datos_anio(anio_con_periodos, BIMESTRES, institucion=otra.pk),
    )

    anio_con_periodos.refresh_from_db()
    assert anio_con_periodos.institucion_id == original


def test_sin_periodos_la_institucion_del_anio_sigue_editable(admin_client, anio):
    respuesta = admin_client.get(url_anio(anio))

    assert "institucion" in respuesta.context["adminform"].form.fields


def test_cada_fecha_de_la_ficha_tiene_su_etiqueta_para_el_lector_de_pantalla(admin_client, anio):
    respuesta = admin_client.get(url_anio(anio))

    html = respuesta.content.decode()
    assert 'aria-label="Periodo 1: fecha de inicio"' in html
    assert 'aria-label="Periodo 4: fecha de fin"' in html


# --- Organización de la institución ---


def test_con_periodos_la_organizacion_es_de_solo_lectura(admin_client, anio_con_periodos):
    institucion = anio_con_periodos.institucion

    respuesta = admin_client.get(url_institucion(institucion))

    assert "organizacion_periodos" not in respuesta.context["adminform"].form.fields


def test_con_periodos_un_post_que_cambia_la_organizacion_no_la_cambia(
    admin_client, anio_con_periodos
):
    institucion = anio_con_periodos.institucion

    admin_client.post(
        url_institucion(institucion),
        {"nombre": institucion.nombre, "codigo_modular": "", "organizacion_periodos": "TRIMESTRE"},
    )

    institucion.refresh_from_db()
    assert institucion.organizacion_periodos == Institucion.OrganizacionPeriodos.BIMESTRE


def test_sin_periodos_la_organizacion_cambia(admin_client, anio):
    institucion = anio.institucion

    respuesta = admin_client.post(
        url_institucion(institucion),
        {"nombre": institucion.nombre, "codigo_modular": "", "organizacion_periodos": "TRIMESTRE"},
    )

    assert respuesta.status_code == 302
    institucion.refresh_from_db()
    assert institucion.organizacion_periodos == Institucion.OrganizacionPeriodos.TRIMESTRE


def test_el_formulario_de_la_institucion_rechaza_cambiar_la_organizacion_con_periodos(
    anio_con_periodos,
):
    """Si la ficha se abrió antes de que hubiera periodos, el campo llega editable."""
    from institucion.admin import FormularioInstitucion

    institucion = anio_con_periodos.institucion
    form = FormularioInstitucion(
        {"nombre": institucion.nombre, "codigo_modular": "", "organizacion_periodos": "TRIMESTRE"},
        instance=institucion,
    )

    assert not form.is_valid()
    assert form.errors["organizacion_periodos"] == [servicios.ORGANIZACION_FIJA]


# --- Solo el Administrador ---


@pytest.mark.parametrize("fixture", ["docente", "direccion"])
def test_docente_y_direccion_no_ven_la_ficha_ni_cambian_periodos(client, request, fixture, anio):
    client.force_login(request.getfixturevalue(fixture))

    ficha = client.get(url_anio(anio))
    client.post(url_anio(anio), datos_anio(anio, BIMESTRES))

    assert ficha.status_code == 302
    assert not Periodo.objects.exists()
