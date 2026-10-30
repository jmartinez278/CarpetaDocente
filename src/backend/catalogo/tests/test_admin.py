"""Pruebas del catálogo en el panel de administración (spec catalogo-curricular; EN-06, D5)."""

import pytest
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.urls import reverse

from catalogo.models import Area, Competencia, InstitucionArea
from cuentas.models import Usuario
from institucion.models import Institucion

pytestmark = pytest.mark.django_db

MODELOS = ["area", "competencia", "institucionarea"]


@pytest.fixture
def institucion():
    return Institucion.objects.create(nombre="I.E. Ficticia N.° 1")


@pytest.fixture
def area():
    return Area.objects.get(codigo_siagie="0005")


@pytest.fixture
def competencia(area):
    return area.competencias.get(orden=1)


@pytest.fixture
def fila_castellano(institucion):
    return InstitucionArea.objects.get(institucion=institucion, area__codigo_siagie="0002")


def objeto_de(modelo, area, competencia, fila):
    return {"area": area, "competencia": competencia, "institucionarea": fila}[modelo]


@pytest.mark.parametrize("modelo", MODELOS)
def test_las_listas_abren(admin_client, institucion, modelo):
    respuesta = admin_client.get(reverse(f"admin:catalogo_{modelo}_changelist"))

    assert respuesta.status_code == 200
    assert respuesta.context["has_add_permission"] is False


@pytest.mark.parametrize("modelo", MODELOS)
def test_sin_url_de_agregar(admin_client, modelo):
    respuesta = admin_client.get(reverse(f"admin:catalogo_{modelo}_add"))

    assert respuesta.status_code == 403


@pytest.mark.parametrize("modelo", MODELOS)
def test_sin_url_de_borrado(admin_client, area, competencia, fila_castellano, modelo):
    objeto = objeto_de(modelo, area, competencia, fila_castellano)

    respuesta = admin_client.post(reverse(f"admin:catalogo_{modelo}_delete", args=[objeto.pk]))

    assert respuesta.status_code == 403
    assert type(objeto).objects.filter(pk=objeto.pk).exists()


@pytest.mark.parametrize("modelo", MODELOS)
def test_sin_accion_eliminar_en_lote(admin_client, area, competencia, fila_castellano, modelo):
    objeto = objeto_de(modelo, area, competencia, fila_castellano)
    url = reverse(f"admin:catalogo_{modelo}_changelist")

    assert b'value="delete_selected"' not in admin_client.get(url).content
    admin_client.post(
        url, {"action": "delete_selected", ACTION_CHECKBOX_NAME: [objeto.pk], "post": "yes"}
    )
    assert type(objeto).objects.filter(pk=objeto.pk).exists()


@pytest.mark.parametrize("modelo", MODELOS)
def test_la_ficha_no_tiene_boton_de_borrar(
    admin_client, area, competencia, fila_castellano, modelo
):
    objeto = objeto_de(modelo, area, competencia, fila_castellano)

    respuesta = admin_client.get(reverse(f"admin:catalogo_{modelo}_change", args=[objeto.pk]))

    assert respuesta.status_code == 200
    assert respuesta.context["has_delete_permission"] is False


def test_ficha_del_area_solo_edita_el_orden(admin_client, area):
    url = reverse("admin:catalogo_area_change", args=[area.pk])

    respuesta = admin_client.get(url)
    ficha = respuesta.context["adminform"]
    assert set(ficha.form.fields) == {"orden"}
    assert {"codigo_siagie", "nombre", "es_transversal", "admite_exoneracion"} <= set(
        ficha.readonly_fields
    )

    admin_client.post(
        url,
        {
            "orden": 20,
            "codigo_siagie": "9999",
            "nombre": "Otro nombre",
            "es_transversal": "on",
            "admite_exoneracion": "on",
        },
    )

    area.refresh_from_db()
    assert area.orden == 20
    assert (area.codigo_siagie, area.nombre) == ("0005", "Comunicación")
    assert (area.es_transversal, area.admite_exoneracion) == (False, False)


def test_desmarcar_activa_deja_la_competencia_inactiva_y_existente(admin_client, competencia):
    url = reverse("admin:catalogo_competencia_change", args=[competencia.pk])

    respuesta = admin_client.post(url, {"orden": competencia.orden})

    assert respuesta.status_code == 302
    competencia.refresh_from_db()
    assert competencia.activa is False
    assert Competencia.objects.filter(pk=competencia.pk).exists()


def test_se_trabaja_se_cambia_desde_la_lista(admin_client, fila_castellano):
    respuesta = admin_client.post(
        reverse("admin:catalogo_institucionarea_changelist"),
        {
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "1",
            "form-0-id": fila_castellano.pk,
            "form-0-se_trabaja": "on",
            "_save": "Guardar",
        },
    )

    assert respuesta.status_code == 302
    fila_castellano.refresh_from_db()
    assert fila_castellano.se_trabaja is True


@pytest.mark.parametrize(
    ("rol", "destino"),
    [(Usuario.Rol.DOCENTE, "/docente/"), (Usuario.Rol.DIRECCION, "/direccion/")],
)
def test_otro_rol_llega_a_su_inicio(client, institucion, rol, destino):
    client.force_login(
        Usuario.objects.create_user(username="cuentaficticia", rol=rol, institucion=institucion)
    )

    respuesta = client.get("/admin/catalogo/area/", follow=True)

    assert respuesta.redirect_chain[-1][0] == destino
    assert respuesta.status_code == 200
