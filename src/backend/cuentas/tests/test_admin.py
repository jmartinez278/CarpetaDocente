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
        "username": "jperez",
        "first_name": "Juana",
        "last_name": "Pérez",
        "password1": CLAVE_FICTICIA,
        "password2": CLAVE_FICTICIA,
        "rol": Usuario.Rol.DOCENTE,
    }
    datos.update(cambios)
    return datos


def errores_del_alta(respuesta):
    assert respuesta.status_code == 200
    return respuesta.context["adminform"].form.errors


def test_formulario_de_alta_incluye_rol_e_institucion(admin_client):
    respuesta = admin_client.get(reverse(URL_ALTA))

    assert respuesta.status_code == 200
    campos = respuesta.context["adminform"].form.fields
    assert "rol" in campos
    assert "institucion" in campos


def test_alta_desde_el_panel_crea_docente_activo_y_muestra_cuenta_creada(admin_client, institucion):
    respuesta = admin_client.post(
        reverse(URL_ALTA), datos_alta(institucion=institucion.pk), follow=True
    )

    usuario = Usuario.objects.get(username="jperez")
    assert usuario.rol == Usuario.Rol.DOCENTE
    assert usuario.institucion == institucion
    assert (usuario.first_name, usuario.last_name) == ("Juana", "Pérez")
    assert usuario.check_password(CLAVE_FICTICIA)
    assert usuario.is_active
    assert not usuario.is_staff
    assert not usuario.is_superuser
    assert mensajes(respuesta) == ["Cuenta creada"]


@pytest.mark.parametrize(
    "campo", ["first_name", "last_name", "institucion", "password1", "password2"]
)
def test_alta_con_un_obligatorio_vacio_no_crea_la_cuenta(admin_client, institucion, campo):
    datos = datos_alta(institucion=institucion.pk)
    datos[campo] = ""

    respuesta = admin_client.post(reverse(URL_ALTA), datos)

    assert campo in errores_del_alta(respuesta)
    assert not Usuario.objects.filter(username="jperez").exists()


def test_alta_de_docente_sin_institucion_senala_el_campo(admin_client):
    respuesta = admin_client.post(reverse(URL_ALTA), datos_alta())

    assert "institucion" in errores_del_alta(respuesta)
    assert not Usuario.objects.filter(username="jperez").exists()


def test_el_alta_no_ofrece_crear_la_cuenta_sin_contrasena(admin_client):
    respuesta = admin_client.get(reverse(URL_ALTA))

    campos = respuesta.context["adminform"].form.fields
    assert "usable_password" not in campos
    assert campos["password1"].required
    assert campos["password2"].required


def test_el_alta_rechaza_el_rol_administrador(admin_client, institucion):
    respuesta = admin_client.post(
        reverse(URL_ALTA),
        datos_alta(institucion=institucion.pk, rol=Usuario.Rol.ADMINISTRADOR),
    )

    assert "rol" in errores_del_alta(respuesta)
    assert not Usuario.objects.filter(username="jperez").exists()


@pytest.mark.parametrize("repetido", ["jperez", "JPerez"])
def test_usuario_repetido_dice_que_ya_existe_y_propone_el_siguiente(
    admin_client, crear_usuario, institucion, repetido
):
    crear_usuario("jperez", Usuario.Rol.DOCENTE)
    crear_usuario("jperez2", Usuario.Rol.DOCENTE)

    respuesta = admin_client.post(
        reverse(URL_ALTA), datos_alta(username=repetido, institucion=institucion.pk)
    )

    errores = errores_del_alta(respuesta)["username"]
    assert errores[0] == "El usuario ya existe"
    assert "Prueba con jperez3." in errores
    assert Usuario.objects.filter(username__iexact="jperez").count() == 1


def test_la_sugerencia_parte_de_los_nombres_con_tilde_y_enie(
    admin_client, crear_usuario, institucion
):
    crear_usuario("nnunez", Usuario.Rol.DOCENTE)

    respuesta = admin_client.post(
        reverse(URL_ALTA),
        datos_alta(
            username="nnunez",
            first_name="Ñahui Rosa",
            last_name="Núñez Ávila",
            institucion=institucion.pk,
        ),
    )

    assert "Prueba con nnunez2." in errores_del_alta(respuesta)["username"]


@pytest.mark.parametrize("usuario", ["J.Pérez", "j perez", "JPerez", "jperez1", "jpeñez"])
def test_formato_invalido_explica_el_ejemplo(admin_client, institucion, usuario):
    respuesta = admin_client.post(
        reverse(URL_ALTA), datos_alta(username=usuario, institucion=institucion.pk)
    )

    errores = errores_del_alta(respuesta)["username"]
    assert any("jperez" in error for error in errores)
    assert not Usuario.objects.filter(username=usuario).exists()


def test_usuario_con_numero_se_acepta(admin_client, crear_usuario, institucion):
    crear_usuario("jperez", Usuario.Rol.DOCENTE)

    respuesta = admin_client.post(
        reverse(URL_ALTA), datos_alta(username="jperez2", institucion=institucion.pk)
    )

    assert respuesta.status_code == 302
    assert Usuario.objects.filter(username="jperez2").exists()


def test_el_usuario_explica_el_formato(admin_client):
    respuesta = admin_client.get(reverse(URL_ALTA))

    ayuda = respuesta.context["adminform"].form.fields["username"].help_text
    assert "jperez" in ayuda
    assert "jperez2" in ayuda


# --- Edición de cuentas (spec gestion-cuentas; design.md de US-003, D4) ---

CAMPOS_OCULTOS = {
    "is_staff",
    "is_superuser",
    "groups",
    "user_permissions",
    "debe_cambiar_password",
}


def url_edicion(usuario):
    return reverse("admin:cuentas_usuario_change", args=[usuario.pk])


def campos_visibles(respuesta):
    """Campos del formulario más los de solo lectura, que son lo que ve el Administrador."""
    formulario = respuesta.context["adminform"]
    return set(formulario.form.fields) | set(formulario.readonly_fields)


def test_la_edicion_no_muestra_privilegios_ni_cambio_obligatorio(admin_client, docente):
    respuesta = admin_client.get(url_edicion(docente))

    assert respuesta.status_code == 200
    assert not CAMPOS_OCULTOS & campos_visibles(respuesta)


def test_la_edicion_permite_cambiar_nombres_rol_institucion_y_activo(admin_client, docente):
    campos = admin_client.get(url_edicion(docente)).context["adminform"].form.fields

    assert {"first_name", "last_name", "rol", "institucion", "is_active"} <= set(campos)


def test_el_usuario_es_de_solo_lectura_en_la_edicion(admin_client, docente):
    respuesta = admin_client.get(url_edicion(docente))

    assert "username" not in respuesta.context["adminform"].form.fields
    assert "username" in respuesta.context["adminform"].readonly_fields


def test_el_rol_de_un_administrador_es_de_solo_lectura(admin_client, administrador):
    respuesta = admin_client.get(url_edicion(administrador))

    assert "rol" not in respuesta.context["adminform"].form.fields
    assert "rol" in respuesta.context["adminform"].readonly_fields


def test_el_rol_de_un_docente_se_puede_cambiar(admin_client, docente):
    respuesta = admin_client.get(url_edicion(docente))

    assert "rol" in respuesta.context["adminform"].form.fields


def test_el_rol_de_la_edicion_ofrece_solo_docente_y_direccion(admin_client, docente):
    campo = admin_client.get(url_edicion(docente)).context["adminform"].form.fields["rol"]

    assert {valor for valor, _ in campo.choices if valor} == {"DOCENTE", "DIRECCION"}


def test_la_edicion_rechaza_asignar_el_rol_administrador(admin_client, docente):
    datos = datos_edicion(docente, rol=Usuario.Rol.ADMINISTRADOR)

    respuesta = admin_client.post(url_edicion(docente), datos)

    assert respuesta.status_code == 200
    assert "rol" in respuesta.context["adminform"].form.errors
    docente.refresh_from_db()
    assert docente.rol == Usuario.Rol.DOCENTE


def datos_edicion(usuario, **cambios):
    datos = {
        "first_name": usuario.first_name,
        "last_name": usuario.last_name,
        "email": usuario.email,
        "rol": usuario.rol,
        "institucion": usuario.institucion_id,
        "is_active": "on",
        "last_login_0": "",
        "last_login_1": "",
        "date_joined_0": usuario.date_joined.strftime("%Y-%m-%d"),
        "date_joined_1": usuario.date_joined.strftime("%H:%M:%S"),
    }
    datos.update(cambios)
    return datos


def test_corregir_los_apellidos_conserva_usuario_y_contrasena(admin_client, docente, clave):
    respuesta = admin_client.post(
        url_edicion(docente), datos_edicion(docente, last_name="Quispe Mamani")
    )

    assert respuesta.status_code == 302
    docente.refresh_from_db()
    assert docente.last_name == "Quispe Mamani"
    assert docente.username == "ana.quispe"
    assert docente.check_password(clave)
    assert not docente.is_staff
    assert not docente.is_superuser


def test_un_post_no_puede_dar_privilegios_en_la_edicion(admin_client, docente):
    datos = datos_edicion(docente, is_staff="on", is_superuser="on", username="otro")

    admin_client.post(url_edicion(docente), datos)

    docente.refresh_from_db()
    assert not docente.is_staff
    assert not docente.is_superuser
    assert docente.username == "ana.quispe"


def test_la_lista_no_filtra_por_acceso_al_panel(admin_client):
    respuesta = admin_client.get(reverse("admin:cuentas_usuario_changelist"))

    assert "is_staff" not in {
        filtro.field_path
        for filtro in respuesta.context["cl"].filter_specs
        if hasattr(filtro, "field_path")
    }


# --- Desactivar sin eliminar y acceso al panel (spec gestion-cuentas; design.md de US-003, D5) ---


def url_eliminacion(usuario):
    return reverse("admin:cuentas_usuario_delete", args=[usuario.pk])


def test_el_panel_no_ofrece_eliminar_cuentas(admin_client, docente):
    lista = admin_client.get(reverse(URL_LISTA))
    edicion = admin_client.get(url_edicion(docente))

    assert "delete_selected" not in acciones_de(lista)
    assert not edicion.context["has_delete_permission"]
    assert url_eliminacion(docente) not in edicion.content.decode()


def test_una_peticion_directa_de_eliminacion_se_rechaza(admin_client, docente):
    respuesta = admin_client.post(url_eliminacion(docente), {"post": "yes"})

    assert respuesta.status_code == 403
    assert Usuario.objects.filter(pk=docente.pk).exists()


def test_la_accion_de_eliminar_varias_se_rechaza(admin_client, docente):
    admin_client.post(
        reverse(URL_LISTA),
        {"action": "delete_selected", ACTION_CHECKBOX_NAME: [docente.pk], "post": "yes"},
    )

    assert Usuario.objects.filter(pk=docente.pk).exists()


def test_una_cuenta_desactivada_no_ingresa_y_sigue_en_la_lista(
    client, admin_client, docente, clave
):
    admin_client.post(url_edicion(docente), datos_edicion(docente, is_active=""))

    docente.refresh_from_db()
    assert not docente.is_active
    respuesta = client.post("/ingresar/", {"username": "ana.quispe", "password": clave})
    assert respuesta.status_code == 200
    assert "Usuario o contraseña incorrectos, o cuenta inactiva" in respuesta.content.decode()
    lista = admin_client.get(reverse(URL_LISTA))
    assert docente in lista.context["cl"].result_list
    assert {"is_active"} <= set(lista.context["cl"].list_display)


def test_la_sesion_abierta_de_una_cuenta_desactivada_lleva_a_ingresar(
    client, admin_client, docente
):
    client.force_login(docente)
    assert client.get("/docente/").status_code == 200

    admin_client.post(url_edicion(docente), datos_edicion(docente, is_active=""))

    respuesta = client.get("/docente/")
    assert respuesta.status_code == 302
    assert respuesta.url == "/ingresar/?next=/docente/"


def test_la_cuenta_creada_en_el_panel_no_entra_al_panel(admin_client, client, institucion):
    admin_client.post(reverse(URL_ALTA), datos_alta(institucion=institucion.pk))

    respuesta = client.post("/ingresar/", {"username": "jperez", "password": CLAVE_FICTICIA})
    assert respuesta.status_code == 302
    assert respuesta.url == "/docente/"
    destino = client.get("/admin/", follow=True)
    assert destino.redirect_chain[-1][0] == "/docente/"
    assert destino.status_code == 200


@pytest.mark.parametrize("fixture", ["docente", "direccion"])
@pytest.mark.parametrize("ruta", ["admin:cuentas_usuario_changelist", URL_ALTA])
def test_docente_y_direccion_no_ven_la_gestion_de_cuentas(client, request, fixture, ruta):
    usuario = request.getfixturevalue(fixture)
    client.force_login(usuario)

    respuesta = client.get(reverse(ruta), follow=True)

    destino = "/docente/" if fixture == "docente" else "/direccion/"
    assert respuesta.redirect_chain[-1][0] == destino
    assert respuesta.status_code == 200


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
