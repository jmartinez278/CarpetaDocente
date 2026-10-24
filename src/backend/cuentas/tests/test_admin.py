"""Pruebas del panel de administración de usuarios (rol Administrador): alta y desbloqueo."""

import pytest
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.messages import get_messages
from django.urls import reverse
from django.utils import timezone

from cuentas import servicios
from cuentas.admin import UsuarioAdmin
from cuentas.models import Usuario
from institucion.models import Institucion

pytestmark = pytest.mark.django_db

URL_ALTA = "admin:cuentas_usuario_add"
CLAVE_FICTICIA = "Clave-Ficticia-2026"


@pytest.fixture
def institucion():
    return Institucion.objects.create(nombre="I.E. Ficticia N.° 1")


def datos_alta(**cambios):
    datos = {
        "username": "docente_ficticio",
        "usable_password": "true",
        "password1": CLAVE_FICTICIA,
        "password2": CLAVE_FICTICIA,
        "rol": Usuario.Rol.DOCENTE,
    }
    datos.update(cambios)
    return datos


def test_formulario_de_alta_incluye_rol_e_institucion(admin_client):
    respuesta = admin_client.get(reverse(URL_ALTA))

    assert respuesta.status_code == 200
    campos = respuesta.context["adminform"].form.fields
    assert "rol" in campos
    assert "institucion" in campos


def test_alta_desde_el_panel_crea_docente(admin_client, institucion):
    respuesta = admin_client.post(reverse(URL_ALTA), datos_alta(institucion=institucion.pk))

    assert respuesta.status_code == 302
    usuario = Usuario.objects.get(username="docente_ficticio")
    assert usuario.rol == Usuario.Rol.DOCENTE
    assert usuario.institucion == institucion
    assert usuario.check_password(CLAVE_FICTICIA)


def test_alta_desde_el_panel_de_docente_sin_institucion_muestra_error(admin_client):
    respuesta = admin_client.post(reverse(URL_ALTA), datos_alta())

    assert respuesta.status_code == 200
    errores = respuesta.context["adminform"].form.non_field_errors()
    assert errores == ["Docente y Dirección deben pertenecer a una institución."]
    assert not Usuario.objects.filter(username="docente_ficticio").exists()


# --- Acción "Desbloquear cuenta" (RN-024; spec inicio-sesion; design.md de US-001, D4) ---

URL_LISTA = "admin:cuentas_usuario_changelist"
CLAVE_INCORRECTA = "no-es-la-clave"


def bloquear(usuario):
    for _ in range(servicios.INTENTOS_MAXIMOS):
        servicios.intentar_ingreso(usuario, CLAVE_INCORRECTA)


def desbloquear(client, *usuarios):
    return client.post(
        reverse(URL_LISTA),
        {"action": "desbloquear_cuenta", ACTION_CHECKBOX_NAME: [u.pk for u in usuarios]},
        follow=True,
    )


def mensajes(respuesta):
    return [str(m) for m in get_messages(respuesta.wsgi_request)]


def registros_de(usuario):
    return LogEntry.objects.filter(
        content_type=ContentType.objects.get_for_model(Usuario), object_id=str(usuario.pk)
    )


@pytest.fixture
def panel(client, administrador):
    client.force_login(administrador)
    return client


def test_desbloquea_la_cuenta_y_lo_registra_en_su_historial(panel, administrador, docente):
    bloquear(docente)
    antes = timezone.now()

    respuesta = desbloquear(panel, docente)

    docente.refresh_from_db()
    assert docente.bloqueado_hasta is None
    assert docente.intentos_fallidos == 0
    (registro,) = registros_de(docente)
    assert registro.action_flag == CHANGE
    assert registro.get_change_message() == "Cuenta desbloqueada."
    assert registro.user == administrador
    assert registro.action_time >= antes
    assert mensajes(respuesta) == ["Cuentas desbloqueadas: 1."]


def test_el_historial_del_panel_muestra_el_desbloqueo(panel, docente):
    bloquear(docente)
    desbloquear(panel, docente)

    historial = panel.get(reverse("admin:cuentas_usuario_history", args=[docente.pk]))

    assert "Cuenta desbloqueada." in historial.content.decode()


def test_una_cuenta_sin_bloqueo_no_cambia_ni_se_registra(panel, docente):
    respuesta = desbloquear(panel, docente)

    assert not registros_de(docente).exists()
    assert mensajes(respuesta) == ["Sin nada que desbloquear: 1."]


def test_sobre_varias_cuentas_el_mensaje_cuenta_cada_caso(panel, docente, direccion, crear_usuario):
    otra = crear_usuario("otra.docente", Usuario.Rol.DOCENTE)
    bloquear(docente)
    bloquear(otra)

    respuesta = desbloquear(panel, docente, direccion, otra)

    assert mensajes(respuesta) == ["Cuentas desbloqueadas: 2. Sin nada que desbloquear: 1."]
    assert not registros_de(direccion).exists()


def test_intentos_y_bloqueo_son_de_solo_lectura_en_el_formulario(panel, docente):
    respuesta = panel.get(reverse("admin:cuentas_usuario_change", args=[docente.pk]))

    campos = respuesta.context["adminform"].form.fields
    assert "intentos_fallidos" not in campos
    assert "bloqueado_hasta" not in campos
    assert {"intentos_fallidos", "bloqueado_hasta"} <= set(
        respuesta.context["adminform"].readonly_fields
    )


def test_la_lista_muestra_bloqueado_hasta(panel, docente):
    bloquear(docente)

    respuesta = panel.get(reverse(URL_LISTA))

    assert "bloqueado_hasta" in respuesta.context["cl"].list_display


def acciones_de(respuesta):
    formulario = respuesta.context["action_form"]
    return [] if formulario is None else [valor for valor, _ in formulario.fields["action"].choices]


@pytest.fixture
def panel_de_solo_lectura(client, crear_usuario):
    """Staff con solo ``view_usuario``: ve las cuentas, pero no las cambia."""
    visor = crear_usuario("visor.ficticio", Usuario.Rol.ADMINISTRADOR, is_staff=True)
    visor.user_permissions.add(Permission.objects.get(codename="view_usuario"))
    client.force_login(visor)
    return client


def test_sin_permiso_de_cambio_no_aparece_la_accion(panel_de_solo_lectura, docente):
    respuesta = panel_de_solo_lectura.get(reverse(URL_LISTA))

    assert respuesta.status_code == 200
    assert "desbloquear_cuenta" not in acciones_de(respuesta)


def test_sin_permiso_de_cambio_un_post_no_desbloquea(panel_de_solo_lectura, docente):
    bloquear(docente)

    desbloquear(panel_de_solo_lectura, docente)

    docente.refresh_from_db()
    assert servicios.esta_bloqueado(docente)
    assert not registros_de(docente).exists()


def test_si_el_historial_falla_el_desbloqueo_se_revierte(panel, docente, monkeypatch):
    bloquear(docente)

    def historial_caido(*args, **kwargs):
        raise RuntimeError("historial no disponible")

    monkeypatch.setattr(UsuarioAdmin, "log_change", historial_caido)

    with pytest.raises(RuntimeError):
        desbloquear(panel, docente)

    docente.refresh_from_db()
    assert servicios.esta_bloqueado(docente)


def test_despues_de_desbloquear_ingresar_acepta_la_contrasena(client, panel, docente, clave):
    bloquear(docente)
    desbloquear(panel, docente)
    panel.logout()

    respuesta = client.post("/ingresar/", {"username": "ana.quispe", "password": clave})

    assert respuesta.status_code == 302
    assert respuesta.url == "/docente/"
