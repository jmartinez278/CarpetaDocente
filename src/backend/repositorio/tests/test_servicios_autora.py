"""Lo que solo la autora hace con su sesión: eliminar, compartir y dejar de compartir.

Specs detalle-sesion («Eliminar una sesión propia», «Solo la autora elimina», «Dejar de
compartir», «Compartir después»), almacenamiento-archivos («El archivo se borra con su sesión»)
y registro-actividad («Operaciones sobre sesiones»); design de US-011, D8.

El borrado del archivo corre al confirmar la transacción: las pruebas que lo miran usan
``django_capture_on_commit_callbacks(execute=True)``.
"""

import logging
import uuid

import pytest
from django.core.exceptions import ValidationError
from django.core.files.storage import storages
from django.db import DatabaseError
from django.utils import timezone

from actividad.models import Operacion, RegistroActividad
from actividad.tests.intentos import intentos
from repositorio import servicios
from repositorio.models import Sesion, SesionVista

pytestmark = pytest.mark.django_db

RUTA = "/docente/sesiones/x/eliminar/"


def entradas(operacion):
    return list(RegistroActividad.objects.filter(operacion=operacion).order_by("pk"))


def existe(sesion):
    return Sesion.objects.filter(pk=sesion.pk).exists()


def tiene_archivo(sesion):
    return storages["sesiones"].exists(sesion.archivo_clave)


# --- Eliminar una sesión propia ---------------------------------------------------------------


def test_eliminar_borra_la_sesion_su_archivo_y_deja_sesion_eliminada(
    con_archivo, docente, django_capture_on_commit_callbacks
):
    sesion = con_archivo(docente, compartida=True)

    with django_capture_on_commit_callbacks(execute=True):
        servicios.eliminar_sesion(docente, sesion.pk, RUTA)

    assert not existe(sesion)
    assert not tiene_archivo(sesion)
    [entrada] = entradas(Operacion.SESION_ELIMINADA)
    assert entrada.usuario == docente
    assert entrada.entidad == "sesion"
    assert entrada.entidad_id == str(sesion.pk)
    assert entrada.detalle == {"compartida": True}


def test_la_entrada_de_eliminar_dice_si_no_estaba_compartida(con_archivo, docente):
    sesion = con_archivo(docente, compartida=False)

    servicios.eliminar_sesion(docente, sesion.pk, RUTA)

    [entrada] = entradas(Operacion.SESION_ELIMINADA)
    assert entrada.detalle == {"compartida": False}


def test_eliminar_conserva_la_entrada_sesion_enviada(con_archivo, docente):
    sesion = con_archivo(docente)
    servicios.registrar(docente, Operacion.SESION_ENVIADA, entidad="sesion", entidad_id=sesion.pk)

    servicios.eliminar_sesion(docente, sesion.pk, RUTA)

    assert [e.entidad_id for e in entradas(Operacion.SESION_ENVIADA)] == [str(sesion.pk)]


def test_eliminar_borra_las_vistas_de_la_sesion(con_archivo, docente, otra_docente):
    sesion = con_archivo(docente, compartida=True)
    servicios.registrar_vista(otra_docente, sesion)

    servicios.eliminar_sesion(docente, sesion.pk, RUTA)

    assert not SesionVista.objects.exists()


def test_eliminar_no_toca_otras_sesiones_ni_sus_archivos(
    con_archivo, docente, django_capture_on_commit_callbacks
):
    sesion, otra = con_archivo(docente), con_archivo(docente)

    with django_capture_on_commit_callbacks(execute=True):
        servicios.eliminar_sesion(docente, sesion.pk, RUTA)

    assert existe(otra)
    assert tiene_archivo(otra)


def test_eliminar_dos_veces_la_segunda_no_esta_disponible_y_no_deja_entrada(con_archivo, docente):
    sesion = con_archivo(docente)
    servicios.eliminar_sesion(docente, sesion.pk, RUTA)

    with pytest.raises(servicios.SesionNoDisponible):
        servicios.eliminar_sesion(docente, sesion.pk, RUTA)

    assert len(entradas(Operacion.SESION_ELIMINADA)) == 1
    assert not intentos()


@pytest.mark.parametrize("id_sesion", [uuid.uuid4(), "no-es-un-uuid"])
def test_eliminar_una_que_nunca_existio_no_deja_entrada(docente, id_sesion):
    with pytest.raises(servicios.SesionNoDisponible):
        servicios.eliminar_sesion(docente, id_sesion, RUTA)

    assert not RegistroActividad.objects.exists()


# --- Solo la autora elimina -------------------------------------------------------------------


def test_eliminar_una_ajena_visible_es_solo_la_autora_y_deja_intento(
    con_archivo, docente, otra_docente
):
    sesion = con_archivo(otra_docente, compartida=True)

    with pytest.raises(servicios.SoloLaAutora):
        servicios.eliminar_sesion(docente, sesion.pk, RUTA)

    assert existe(sesion)
    assert tiene_archivo(sesion)
    assert intentos() == [(str(sesion.pk), RUTA, servicios.SESION_AJENA)]
    assert not entradas(Operacion.SESION_ELIMINADA)


def test_solo_el_autor_tiene_el_mensaje_de_la_spec():
    assert str(servicios.SoloLaAutora()) == "Solo el autor puede eliminar esta sesión"


def test_eliminar_una_ajena_no_compartida_no_esta_disponible_y_deja_intento(
    con_archivo, docente, otra_docente
):
    sesion = con_archivo(otra_docente, compartida=False)

    with pytest.raises(servicios.SesionNoDisponible):
        servicios.eliminar_sesion(docente, sesion.pk, RUTA)

    assert existe(sesion)
    assert tiene_archivo(sesion)
    assert intentos() == [(str(sesion.pk), RUTA, servicios.SESION_NO_VISIBLE)]


def test_eliminar_una_de_otra_institucion_no_esta_disponible_y_deja_intento(
    con_archivo, docente, colega_de_otra
):
    sesion = con_archivo(colega_de_otra, compartida=True)

    with pytest.raises(servicios.SesionNoDisponible):
        servicios.eliminar_sesion(docente, sesion.pk, RUTA)

    assert existe(sesion)
    assert intentos() == [(str(sesion.pk), RUTA, servicios.SESION_NO_VISIBLE)]


# --- El archivo se borra con su sesión --------------------------------------------------------


def test_si_falla_la_base_la_sesion_y_su_archivo_siguen_sin_entrada(
    con_archivo, docente, monkeypatch, django_capture_on_commit_callbacks
):
    sesion = con_archivo(docente)

    def fallar(*args, **kwargs):
        raise DatabaseError("la base se cayó")

    monkeypatch.setattr(servicios, "registrar", fallar)
    with django_capture_on_commit_callbacks(execute=True), pytest.raises(DatabaseError):
        servicios.eliminar_sesion(docente, sesion.pk, RUTA)

    assert existe(sesion)
    assert tiene_archivo(sesion)
    assert not RegistroActividad.objects.exists()


def test_si_falla_el_almacen_la_sesion_queda_eliminada_y_el_log_nombra_la_clave(
    con_archivo, docente, monkeypatch, caplog, django_capture_on_commit_callbacks
):
    sesion = con_archivo(docente, titulo="Título que no va al log")

    def fallar(nombre):
        raise OSError("R2 no responde")

    monkeypatch.setattr(storages["sesiones"], "delete", fallar)
    with (
        caplog.at_level(logging.ERROR, logger="repositorio.servicios"),
        django_capture_on_commit_callbacks(execute=True),
    ):
        servicios.eliminar_sesion(docente, sesion.pk, RUTA)

    assert not existe(sesion)
    assert len(entradas(Operacion.SESION_ELIMINADA)) == 1
    assert sesion.archivo_clave in caplog.text
    assert "Título que no va al log" not in caplog.text
    assert docente.username not in caplog.text


def test_el_archivo_no_se_borra_antes_de_confirmar(con_archivo, docente):
    sesion = con_archivo(docente)

    # Sin ejecutar los on_commit: la transacción de la prueba no se confirma.
    servicios.eliminar_sesion(docente, sesion.pk, RUTA)

    assert tiene_archivo(sesion)


# --- Dejar de compartir -----------------------------------------------------------------------


def test_dejar_de_compartir_la_saca_del_repositorio_y_conserva_la_fecha(crear_sesion, docente):
    aceptados = timezone.now() - timezone.timedelta(days=3)
    sesion = crear_sesion(docente, compartida=True, terminos_aceptados_en=aceptados)

    servicios.dejar_de_compartir(docente, sesion.pk, RUTA)

    sesion.refresh_from_db()
    assert sesion.compartida is False
    assert sesion.terminos_aceptados_en == aceptados
    [entrada] = entradas(Operacion.SESION_DESCOMPARTIDA)
    assert (entrada.usuario, entrada.entidad, entrada.entidad_id) == (
        docente,
        "sesion",
        str(sesion.pk),
    )
    assert entrada.detalle == {}


def test_dejar_de_compartir_una_que_ya_no_lo_esta_no_deja_entrada(crear_sesion, docente):
    sesion = crear_sesion(docente, compartida=False)

    servicios.dejar_de_compartir(docente, sesion.pk, RUTA)

    sesion.refresh_from_db()
    assert sesion.compartida is False
    assert not RegistroActividad.objects.exists()


def test_dejar_de_compartir_una_ajena_la_deja_compartida_y_deja_intento(
    crear_sesion, docente, otra_docente
):
    sesion = crear_sesion(otra_docente, compartida=True)

    with pytest.raises(servicios.SoloLaAutora):
        servicios.dejar_de_compartir(docente, sesion.pk, RUTA)

    sesion.refresh_from_db()
    assert sesion.compartida is True
    assert intentos() == [(str(sesion.pk), RUTA, servicios.SESION_AJENA)]
    assert not entradas(Operacion.SESION_DESCOMPARTIDA)


# --- Compartir después ------------------------------------------------------------------------


def test_compartir_aceptando_guarda_la_fecha_de_esta_aceptacion(crear_sesion, docente):
    sesion = crear_sesion(docente, compartida=False)
    antes = timezone.now()

    servicios.compartir_sesion(docente, sesion.pk, True, RUTA)

    sesion.refresh_from_db()
    assert sesion.compartida is True
    assert sesion.terminos_aceptados_en >= antes
    [entrada] = entradas(Operacion.SESION_COMPARTIDA)
    assert (entrada.usuario, entrada.entidad_id, entrada.detalle) == (
        docente,
        str(sesion.pk),
        {},
    )


def test_volver_a_compartir_guarda_la_fecha_nueva(crear_sesion, docente):
    vieja = timezone.now() - timezone.timedelta(days=10)
    sesion = crear_sesion(docente, compartida=True, terminos_aceptados_en=vieja)
    servicios.dejar_de_compartir(docente, sesion.pk, RUTA)

    servicios.compartir_sesion(docente, sesion.pk, True, RUTA)

    sesion.refresh_from_db()
    assert sesion.compartida is True
    assert sesion.terminos_aceptados_en > vieja
    assert [e.operacion for e in RegistroActividad.objects.order_by("pk")] == [
        Operacion.SESION_DESCOMPARTIDA,
        Operacion.SESION_COMPARTIDA,
    ]


def test_compartir_sin_aceptar_la_deja_sin_compartir(crear_sesion, docente):
    sesion = crear_sesion(docente, compartida=False)

    with pytest.raises(ValidationError) as error:
        servicios.compartir_sesion(docente, sesion.pk, False, RUTA)

    assert error.value.messages == [servicios.SIN_TERMINOS]
    sesion.refresh_from_db()
    assert sesion.compartida is False
    assert sesion.terminos_aceptados_en is None
    assert not RegistroActividad.objects.exists()


def test_compartir_una_ya_compartida_no_cambia_la_fecha_ni_deja_entrada(crear_sesion, docente):
    aceptados = timezone.now() - timezone.timedelta(days=2)
    sesion = crear_sesion(docente, compartida=True, terminos_aceptados_en=aceptados)

    servicios.compartir_sesion(docente, sesion.pk, True, RUTA)

    sesion.refresh_from_db()
    assert sesion.terminos_aceptados_en == aceptados
    assert not RegistroActividad.objects.exists()


def test_compartir_una_ajena_sin_compartir_no_esta_disponible_y_deja_intento(
    crear_sesion, docente, otra_docente
):
    sesion = crear_sesion(otra_docente, compartida=False)

    with pytest.raises(servicios.SesionNoDisponible):
        servicios.compartir_sesion(docente, sesion.pk, True, RUTA)

    sesion.refresh_from_db()
    assert sesion.compartida is False
    assert intentos() == [(str(sesion.pk), RUTA, servicios.SESION_NO_VISIBLE)]


def test_compartir_una_ajena_compartida_es_solo_la_autora(crear_sesion, docente, otra_docente):
    sesion = crear_sesion(otra_docente, compartida=True)

    with pytest.raises(servicios.SoloLaAutora):
        servicios.compartir_sesion(docente, sesion.pk, True, RUTA)

    assert intentos() == [(str(sesion.pk), RUTA, servicios.SESION_AJENA)]
    assert not entradas(Operacion.SESION_COMPARTIDA)


# --- Operaciones sobre sesiones: ningún detalle con datos de la sesión -------------------------


def test_ninguna_entrada_lleva_titulo_proposito_texto_ni_nombre_de_archivo(crear_sesion, docente):
    sesion = crear_sesion(
        docente,
        compartida=True,
        titulo="Cuento de Ana",
        proposito="Propósito privado",
        texto="Texto privado",
        archivo_nombre="ana.pdf",
    )

    servicios.dejar_de_compartir(docente, sesion.pk, RUTA)
    servicios.compartir_sesion(docente, sesion.pk, True, RUTA)
    servicios.eliminar_sesion(docente, sesion.pk, RUTA)

    for entrada in RegistroActividad.objects.all():
        detalle = str(entrada.detalle)
        for dato in ("Cuento de Ana", "Propósito privado", "Texto privado", "ana.pdf"):
            assert dato not in detalle


def test_la_ruta_larga_se_guarda_igual_en_el_intento(crear_sesion, docente, otra_docente):
    sesion = crear_sesion(otra_docente, compartida=True)
    ruta = f"/docente/sesiones/{sesion.pk}/eliminar/"

    with pytest.raises(servicios.SoloLaAutora):
        servicios.eliminar_sesion(docente, sesion.pk, ruta)

    assert intentos() == [(str(sesion.pk), ruta, servicios.SESION_AJENA)]
