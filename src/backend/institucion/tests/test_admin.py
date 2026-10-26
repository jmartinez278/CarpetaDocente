"""Pruebas del panel de administración de institucion (documento 10; spec asignacion-secciones)."""

import pytest
from django.urls import reverse

from cuentas.models import Usuario
from institucion.models import AnioEscolar, Seccion

pytestmark = pytest.mark.django_db

OCUPADA = "La sección ya tiene un docente asignado"
ABIERTO = "La institución ya tiene un año escolar abierto."


def test_panel_lista_instituciones(admin_client):
    respuesta = admin_client.get(reverse("admin:institucion_institucion_changelist"))

    assert respuesta.status_code == 200


def formulario(respuesta):
    return respuesta.context["adminform"].form


def acciones_de(lista):
    """Acciones de la lista; sin ninguna, Django no arma el formulario de acciones."""
    form = lista.context["action_form"]
    return [] if form is None else [valor for valor, _ in form.fields["action"].choices]


# --- Año escolar ---


def test_alta_de_anio_escolar_guarda_institucion_anio_y_estado(admin_client, institucion):
    campos = formulario(admin_client.get(reverse("admin:institucion_anioescolar_add"))).fields
    respuesta = admin_client.post(
        reverse("admin:institucion_anioescolar_add"),
        {"institucion": institucion.pk, "anio": 2027, "estado": "ABIERTO"},
    )

    assert set(campos) == {"institucion", "anio", "estado"}
    assert respuesta.status_code == 302
    assert AnioEscolar.objects.get().anio == 2027


def test_segundo_anio_abierto_muestra_el_mensaje_y_no_se_guarda(admin_client, anio_abierto):
    respuesta = admin_client.post(
        reverse("admin:institucion_anioescolar_add"),
        {"institucion": anio_abierto.institucion.pk, "anio": 2028, "estado": "ABIERTO"},
    )

    assert respuesta.status_code == 200
    assert ABIERTO in formulario(respuesta).non_field_errors()
    assert AnioEscolar.objects.count() == 1


def test_la_ficha_del_anio_cambia_el_estado(admin_client, anio_abierto):
    respuesta = admin_client.post(
        reverse("admin:institucion_anioescolar_change", args=[anio_abierto.pk]),
        {"institucion": anio_abierto.institucion.pk, "anio": 2027, "estado": "CERRADO"},
    )

    assert respuesta.status_code == 302
    anio_abierto.refresh_from_db()
    assert anio_abierto.estado == AnioEscolar.Estado.CERRADO


# --- Sección: alta y ficha ---


def url_ficha(seccion):
    return reverse("admin:institucion_seccion_change", args=[seccion.pk])


def datos_ficha(seccion, **cambios):
    datos = {"grado": seccion.grado, "nombre": seccion.nombre, "docente": ""}
    datos.update(cambios)
    return datos


def test_el_alta_de_seccion_no_tiene_el_campo_docente(admin_client):
    respuesta = admin_client.get(reverse("admin:institucion_seccion_add"))

    assert set(formulario(respuesta).fields) == {"anio_escolar", "grado", "nombre"}


def test_el_alta_de_seccion_la_crea_sin_docente(admin_client, anio_abierto):
    respuesta = admin_client.post(
        reverse("admin:institucion_seccion_add"),
        {"anio_escolar": anio_abierto.pk, "grado": 1, "nombre": "A"},
    )

    assert respuesta.status_code == 302
    assert Seccion.objects.get().docente is None


def test_la_ficha_tiene_el_docente_de_aula_y_el_anio_de_solo_lectura(admin_client, seccion):
    form = formulario(admin_client.get(url_ficha(seccion)))

    assert set(form.fields) == {"grado", "nombre", "docente"}
    assert form.fields["docente"].label == "Docente de aula"


def test_la_lista_del_docente_muestra_solo_docentes_activas_de_la_institucion(
    admin_client, seccion, docente, otra_docente, direccion, crear_usuario, otra_institucion
):
    crear_usuario("pflores", is_active=False)
    crear_usuario("cvargas", institucion=otra_institucion)

    campo = formulario(admin_client.get(url_ficha(seccion))).fields["docente"]

    assert set(campo.queryset) == {docente, otra_docente}


def test_asignar_una_docente_en_la_ficha_la_guarda(admin_client, seccion, docente):
    respuesta = admin_client.post(url_ficha(seccion), datos_ficha(seccion, docente=docente.pk))

    assert respuesta.status_code == 302
    seccion.refresh_from_db()
    assert seccion.docente == docente


def test_seccion_ocupada_muestra_el_mensaje_y_no_guarda_nada(
    admin_client, seccion, docente, otra_docente
):
    seccion.docente = docente
    seccion.save()

    respuesta = admin_client.post(
        url_ficha(seccion), datos_ficha(seccion, nombre="B", docente=otra_docente.pk)
    )

    assert respuesta.status_code == 200
    assert formulario(respuesta).errors["docente"] == [OCUPADA]
    seccion.refresh_from_db()
    assert (seccion.nombre, seccion.docente) == ("A", docente)


def test_cambiar_a_una_seccion_repetida_muestra_un_error(admin_client, seccion):
    otra = Seccion.objects.create(anio_escolar=seccion.anio_escolar, grado=2, nombre="B")

    respuesta = admin_client.post(url_ficha(otra), datos_ficha(otra, nombre="A"))

    assert respuesta.status_code == 200
    assert formulario(respuesta).non_field_errors()
    otra.refresh_from_db()
    assert otra.nombre == "B"


# --- Docente asignada que se desactiva ---


@pytest.fixture
def seccion_con_docente_inactiva(seccion, docente):
    seccion.docente = docente
    seccion.save()
    Usuario.objects.filter(pk=docente.pk).update(is_active=False)
    return seccion


def test_la_ficha_muestra_a_la_docente_guardada_aunque_este_inactiva(
    admin_client, seccion_con_docente_inactiva, docente
):
    campo = formulario(admin_client.get(url_ficha(seccion_con_docente_inactiva))).fields["docente"]

    assert docente in campo.queryset


def test_la_ficha_con_docente_inactiva_se_guarda_sin_cambios(
    admin_client, seccion_con_docente_inactiva, docente
):
    seccion = seccion_con_docente_inactiva

    respuesta = admin_client.post(url_ficha(seccion), datos_ficha(seccion, docente=docente.pk))

    assert respuesta.status_code == 302
    seccion.refresh_from_db()
    assert seccion.docente == docente


def test_la_ficha_con_docente_inactiva_se_puede_vaciar(admin_client, seccion_con_docente_inactiva):
    seccion = seccion_con_docente_inactiva

    respuesta = admin_client.post(url_ficha(seccion), datos_ficha(seccion))

    assert respuesta.status_code == 302
    seccion.refresh_from_db()
    assert seccion.docente is None


def test_la_docente_inactiva_no_aparece_en_otras_secciones(
    admin_client, seccion_con_docente_inactiva, docente
):
    otra = Seccion.objects.create(
        anio_escolar=seccion_con_docente_inactiva.anio_escolar, grado=3, nombre="A"
    )

    campo = formulario(admin_client.get(url_ficha(otra))).fields["docente"]

    assert docente not in campo.queryset


# --- Sin eliminar y solo el Administrador ---


@pytest.mark.parametrize("modelo", ["anioescolar", "seccion"])
def test_el_panel_no_ofrece_eliminar(admin_client, seccion, modelo):
    objeto = seccion.anio_escolar if modelo == "anioescolar" else seccion
    lista = admin_client.get(reverse(f"admin:institucion_{modelo}_changelist"))
    ficha = admin_client.get(reverse(f"admin:institucion_{modelo}_change", args=[objeto.pk]))
    eliminar = admin_client.post(
        reverse(f"admin:institucion_{modelo}_delete", args=[objeto.pk]), {"post": "yes"}
    )

    assert lista.status_code == 200
    assert "delete_selected" not in acciones_de(lista)
    assert not ficha.context["has_delete_permission"]
    assert eliminar.status_code == 403
    assert Seccion.objects.filter(pk=seccion.pk).exists()


@pytest.mark.parametrize("fixture", ["docente", "direccion"])
@pytest.mark.parametrize(
    "ruta", ["admin:institucion_seccion_changelist", "admin:institucion_anioescolar_changelist"]
)
def test_docente_y_direccion_no_ven_las_secciones_ni_los_anios(client, request, fixture, ruta):
    client.force_login(request.getfixturevalue(fixture))

    respuesta = client.get(reverse(ruta), follow=True)

    destino = "/docente/" if fixture == "docente" else "/direccion/"
    assert respuesta.redirect_chain[-1][0] == destino
