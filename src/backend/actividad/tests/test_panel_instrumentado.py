"""Escrituras del panel en el registro de actividad (design de US-008, D4 y D5).

Escenarios "Operación del panel", "Desactivar una cuenta", "Asignar y liberar una sección" y
"Ningún camino del panel escribe sin registrar" del spec registro-actividad. Todo pasa por las
pantallas del panel, con el Administrador ficticio.
"""

import pytest
from django.contrib import admin
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.contrib.admin.models import ADDITION, CHANGE, LogEntry
from django.contrib.auth.models import Group
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone

from actividad.admin import RegistroActividadAdmin
from actividad.models import Operacion, RegistroActividad
from actividad.panel import RegistraEnPanel
from actividad.tests.conftest import entrar
from catalogo.models import Area, Competencia, InstitucionArea
from cuentas.models import Usuario
from institucion.models import AnioEscolar, Institucion, Seccion

pytestmark = pytest.mark.django_db

CLAVE_NUEVA = "Clave-Ficticia-Nueva-2026"


@pytest.fixture
def panel(client, administrador):
    return entrar(client, administrador)


def entradas(operacion=None):
    consulta = RegistroActividad.objects.order_by("id")
    if operacion:
        consulta = consulta.filter(operacion=operacion)
    return list(consulta)


def una(operacion):
    (entrada,) = entradas(operacion)
    return entrada


def url(modelo, vista, *argumentos):
    return reverse(f"admin:{modelo}_{vista}", args=argumentos)


# --- Cuentas ---


def datos_cuenta(usuario, **cambios):
    datos = {
        "first_name": usuario.first_name,
        "last_name": usuario.last_name,
        "email": usuario.email,
        "rol": usuario.rol,
        "institucion": usuario.institucion_id,
        "is_active": "on",
        "last_login_0": "",
        "last_login_1": "",
    }
    # Como la ficha la muestra (hora de Lima), con los campos ocultos ``initial-`` que Django
    # agrega porque ``date_joined`` tiene un ``default`` invocable.
    fecha = timezone.localtime(usuario.date_joined)
    for prefijo in ("", "initial-"):
        datos[f"{prefijo}date_joined_0"] = fecha.strftime("%d/%m/%Y")
        datos[f"{prefijo}date_joined_1"] = fecha.strftime("%H:%M:%S")
    datos.update(cambios)
    return {clave: valor for clave, valor in datos.items() if valor is not None}


def test_alta_de_cuenta_deja_cuenta_creada(panel, administrador, institucion):
    panel.post(
        url("cuentas_usuario", "add"),
        {
            "first_name": "Juana",
            "last_name": "Pérez",
            "username": "jperez",
            "rol": Usuario.Rol.DOCENTE,
            "institucion": institucion.pk,
            "password1": CLAVE_NUEVA,
            "password2": CLAVE_NUEVA,
        },
    )

    nueva = Usuario.objects.get(username="jperez")
    entrada = una(Operacion.CUENTA_CREADA)
    assert entrada.usuario == administrador
    assert (entrada.entidad, entrada.entidad_id) == ("usuario", str(nueva.pk))
    assert entrada.detalle == {}


def test_editar_cuenta_deja_los_nombres_de_los_campos_sin_valores(panel, administrador, docente):
    respuesta = panel.post(
        url("cuentas_usuario", "change", docente.pk),
        datos_cuenta(docente, first_name="Anita", email="anita@ficticio.test"),
    )

    assert respuesta.status_code == 302
    entrada = una(Operacion.CUENTA_EDITADA)
    assert entrada.usuario == administrador
    assert (entrada.entidad, entrada.entidad_id) == ("usuario", str(docente.pk))
    assert sorted(entrada.detalle["campos"]) == ["email", "first_name"]
    assert "Anita" not in str(entrada.detalle)
    assert "anita@ficticio.test" not in str(entrada.detalle)


def test_guardar_la_cuenta_sin_cambios_no_deja_entrada(panel, docente):
    panel.post(url("cuentas_usuario", "change", docente.pk), datos_cuenta(docente))

    assert entradas() == []


def test_desmarcar_activo_deja_cuenta_desactivada(panel, docente):
    panel.post(url("cuentas_usuario", "change", docente.pk), datos_cuenta(docente, is_active=None))

    docente.refresh_from_db()
    assert not docente.is_active
    entrada = una(Operacion.CUENTA_DESACTIVADA)
    assert (entrada.entidad, entrada.entidad_id) == ("usuario", str(docente.pk))
    assert entradas(Operacion.CUENTA_EDITADA) == []


def test_desactivar_y_cambiar_otro_campo_deja_dos_entradas(panel, docente):
    panel.post(
        url("cuentas_usuario", "change", docente.pk),
        datos_cuenta(docente, is_active=None, first_name="Anita"),
    )

    assert una(Operacion.CUENTA_DESACTIVADA).entidad_id == str(docente.pk)
    assert una(Operacion.CUENTA_EDITADA).detalle == {"campos": ["first_name"]}


def test_reactivar_deja_cuenta_editada_con_is_active(panel, docente):
    docente.is_active = False
    docente.save()

    panel.post(url("cuentas_usuario", "change", docente.pk), datos_cuenta(docente))

    assert una(Operacion.CUENTA_EDITADA).detalle == {"campos": ["is_active"]}


def test_cambiar_la_contrasena_deja_cuenta_editada_con_password(panel, docente):
    respuesta = panel.post(
        reverse("admin:auth_user_password_change", args=[docente.pk]),
        {"password1": CLAVE_NUEVA, "password2": CLAVE_NUEVA, "usable_password": "true"},
    )

    assert respuesta.status_code == 302
    docente.refresh_from_db()
    assert docente.check_password(CLAVE_NUEVA)
    entrada = una(Operacion.CUENTA_EDITADA)
    assert entrada.detalle == {"campos": ["password"]}
    assert CLAVE_NUEVA not in str(entrada.detalle)


def test_desbloquear_deja_cuenta_editada_con_desbloqueo(panel, docente):
    docente.bloqueado_hasta = timezone.now() + timezone.timedelta(minutes=10)
    docente.save()

    panel.post(
        url("cuentas_usuario", "changelist"),
        {"action": "desbloquear_cuenta", ACTION_CHECKBOX_NAME: [docente.pk]},
    )

    entrada = una(Operacion.CUENTA_EDITADA)
    assert (entrada.entidad, entrada.entidad_id) == ("usuario", str(docente.pk))
    assert entrada.detalle == {"campos": ["desbloqueo"]}


# --- Institución y año escolar ---


def test_alta_de_institucion_deja_institucion_creada(panel, administrador):
    panel.post(url("institucion_institucion", "add"), {"nombre": "I.E. Ficticia N.° 7"})

    nueva = Institucion.objects.get(nombre="I.E. Ficticia N.° 7")
    entrada = una(Operacion.INSTITUCION_CREADA)
    assert entrada.usuario == administrador
    assert (entrada.entidad, entrada.entidad_id) == ("institucion", str(nueva.pk))


def test_editar_institucion_deja_institucion_editada(panel, institucion):
    panel.post(
        url("institucion_institucion", "change", institucion.pk),
        {"nombre": "I.E. Ficticia N.° 8"},
    )

    assert una(Operacion.INSTITUCION_EDITADA).detalle == {"campos": ["nombre"]}


def test_borrar_una_institucion_responde_403(panel, institucion):
    respuesta = panel.post(
        url("institucion_institucion", "delete", institucion.pk), {"post": "yes"}
    )

    assert respuesta.status_code == 403
    assert Institucion.objects.filter(pk=institucion.pk).exists()
    assert entradas() == []


def test_alta_de_anio_deja_anio_creado(panel, institucion):
    panel.post(
        url("institucion_anioescolar", "add"),
        {"institucion": institucion.pk, "anio": 2028, "estado": AnioEscolar.Estado.ABIERTO},
    )

    nuevo = AnioEscolar.objects.get(anio=2028)
    entrada = una(Operacion.ANIO_CREADO)
    assert (entrada.entidad, entrada.entidad_id) == ("anio_escolar", str(nuevo.pk))


def test_editar_anio_deja_anio_editado(panel, anio_abierto):
    panel.post(
        url("institucion_anioescolar", "change", anio_abierto.pk),
        {
            "institucion": anio_abierto.institucion_id,
            "anio": anio_abierto.anio,
            "estado": AnioEscolar.Estado.CERRADO,
        },
    )

    assert una(Operacion.ANIO_EDITADO).detalle == {"campos": ["estado"]}


# --- Secciones ---


def ficha_seccion(seccion, **cambios):
    datos = {"grado": seccion.grado, "nombre": seccion.nombre, "docente": seccion.docente_id or ""}
    datos.update(cambios)
    return datos


def test_alta_de_seccion_deja_seccion_creada(panel, anio_abierto):
    panel.post(
        url("institucion_seccion", "add"),
        {"anio_escolar": anio_abierto.pk, "grado": 4, "nombre": "B"},
    )

    nueva = Seccion.objects.get(grado=4, nombre="B")
    entrada = una(Operacion.SECCION_CREADA)
    assert (entrada.entidad, entrada.entidad_id) == ("seccion", str(nueva.pk))


def test_editar_seccion_deja_seccion_editada(panel, seccion):
    panel.post(url("institucion_seccion", "change", seccion.pk), ficha_seccion(seccion, nombre="C"))

    assert una(Operacion.SECCION_EDITADA).detalle == {"campos": ["nombre"]}
    assert entradas(Operacion.SECCION_ASIGNADA) == []


def test_elegir_docente_deja_seccion_asignada(panel, seccion, docente):
    panel.post(
        url("institucion_seccion", "change", seccion.pk), ficha_seccion(seccion, docente=docente.pk)
    )

    entrada = una(Operacion.SECCION_ASIGNADA)
    assert (entrada.entidad, entrada.entidad_id) == ("seccion", str(seccion.pk))
    assert entrada.detalle == {"docente_anterior": None, "docente_nuevo": docente.pk}
    assert entradas(Operacion.SECCION_EDITADA) == []


def test_cambiar_docente_en_dos_pasos_deja_liberada_y_asignada(
    panel, seccion, docente, otra_docente
):
    """El cambio de docente se hace vaciando la sección y eligiendo otro (US-005, D3)."""
    seccion.docente = docente
    seccion.save()
    ficha = url("institucion_seccion", "change", seccion.pk)

    panel.post(ficha, ficha_seccion(seccion, docente=""))
    panel.post(ficha, ficha_seccion(seccion, docente=otra_docente.pk))

    assert una(Operacion.SECCION_LIBERADA).detalle == {
        "docente_anterior": docente.pk,
        "docente_nuevo": None,
    }
    assert una(Operacion.SECCION_ASIGNADA).detalle == {
        "docente_anterior": None,
        "docente_nuevo": otra_docente.pk,
    }


def test_quitar_docente_deja_seccion_liberada(panel, seccion, docente):
    seccion.docente = docente
    seccion.save()

    panel.post(url("institucion_seccion", "change", seccion.pk), ficha_seccion(seccion, docente=""))

    assert una(Operacion.SECCION_LIBERADA).detalle == {
        "docente_anterior": docente.pk,
        "docente_nuevo": None,
    }


def test_cambiar_nombre_y_docente_deja_dos_entradas(panel, seccion, docente):
    panel.post(
        url("institucion_seccion", "change", seccion.pk),
        ficha_seccion(seccion, nombre="D", docente=docente.pk),
    )

    assert una(Operacion.SECCION_EDITADA).detalle == {"campos": ["nombre"]}
    assert una(Operacion.SECCION_ASIGNADA).detalle["docente_nuevo"] == docente.pk


# --- Catálogo curricular ---


def test_editar_un_area_desde_la_ficha_deja_catalogo_editado(panel):
    area = Area.objects.get(codigo_siagie="0005")

    panel.post(url("catalogo_area", "change", area.pk), {"orden": area.orden + 10})

    entrada = una(Operacion.CATALOGO_EDITADO)
    assert (entrada.entidad, entrada.entidad_id) == (Area._meta.db_table, str(area.pk))
    assert entrada.detalle == {"campos": ["orden"]}


def test_desactivar_una_competencia_deja_catalogo_editado(panel):
    competencia = Competencia.objects.filter(activa=True).first()

    panel.post(url("catalogo_competencia", "change", competencia.pk), {"orden": competencia.orden})

    assert una(Operacion.CATALOGO_EDITADO).detalle == {"campos": ["activa"]}


def test_editar_desde_list_editable_deja_catalogo_editado(panel, institucion):
    fila = InstitucionArea.objects.filter(institucion=institucion).first()

    panel.post(
        url("catalogo_institucionarea", "changelist"),
        {
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "1",
            "form-0-id": fila.pk,
            **({} if fila.se_trabaja else {"form-0-se_trabaja": "on"}),
            "_save": "Guardar",
        },
    )

    entrada = una(Operacion.CATALOGO_EDITADO)
    assert (entrada.entidad, entrada.entidad_id) == (
        InstitucionArea._meta.db_table,
        str(fila.pk),
    )
    assert entrada.detalle == {"campos": ["se_trabaja"]}


# --- El historial de Django sigue y ningún camino escribe sin registrar ---


def test_el_historial_de_django_sigue_apareciendo(panel, institucion):
    panel.post(url("institucion_institucion", "add"), {"nombre": "I.E. Ficticia N.° 9"})
    panel.post(
        url("institucion_institucion", "change", institucion.pk),
        {"nombre": "I.E. Ficticia N.° 10"},
    )

    banderas = set(LogEntry.objects.values_list("action_flag", flat=True))
    assert banderas == {ADDITION, CHANGE}


def test_grupos_fuera_del_panel(panel):
    assert not admin.site.is_registered(Group)
    assert panel.get("/admin/auth/group/").status_code == 404


def test_cada_model_admin_que_escribe_usa_la_mezcla(administrador):
    peticion = RequestFactory().get("/admin/")
    peticion.user = administrador

    for modelo, model_admin in admin.site._registry.items():
        if isinstance(model_admin, RegistroActividadAdmin):
            continue
        escribe = model_admin.has_add_permission(peticion) or model_admin.has_change_permission(
            peticion
        )
        if escribe:
            assert isinstance(model_admin, RegistraEnPanel), modelo
        assert not model_admin.has_delete_permission(peticion), modelo
