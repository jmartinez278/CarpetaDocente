"""Pruebas del modelo Sesion (spec envio-sesiones, «Coherencia en la base»; design D1)."""

import uuid

import pytest
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.utils import timezone

from repositorio.models import TAMANO_MAXIMO, Sesion

pytestmark = pytest.mark.django_db

PDF = "application/pdf"
DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
DOC = "application/msword"


@pytest.fixture
def crear_sesion(institucion, docente, comunicacion):
    """Guarda una sesión válida (PROPIA, ENVIADA, no compartida) con los cambios de ``campos``."""

    def crear(**campos):
        id_ = campos.pop("id", None) or uuid.uuid4()
        valores = {
            "id": id_,
            "institucion": institucion,
            "autor": docente,
            "subido_por": docente,
            "grado": 2,
            "area": comunicacion,
            "titulo": "Leemos un cuento",
            "origen": Sesion.Origen.PROPIA,
            "estado": Sesion.Estado.ENVIADA,
            "compartida": False,
            "archivo_clave": f"sesiones/{id_}.pdf",
            "archivo_nombre": "leemos-un-cuento.pdf",
            "tipo_mime": PDF,
            "tamano_bytes": 1_258_291,
            **campos,
        }
        with transaction.atomic():
            return Sesion.objects.create(**valores)

    return crear


def test_la_tabla_es_sesion():
    assert Sesion._meta.db_table == "sesion"


def test_una_sesion_valida_se_guarda_con_su_proposito_vacio(crear_sesion):
    sesion = crear_sesion()

    sesion.refresh_from_db()
    assert sesion.proposito == ""
    assert sesion.terminos_aceptados_en is None
    assert sesion.creado_en is not None


@pytest.mark.parametrize(
    ("campos", "restriccion"),
    [
        ({"grado": 0}, "ck_sesion_grado"),
        ({"grado": 7}, "ck_sesion_grado"),
        ({"origen": "ADAPTADA"}, "ck_sesion_origen"),
        ({"estado": "OBSERVADA"}, "ck_sesion_estado"),
        ({"tipo_mime": DOC}, "ck_sesion_tipo_mime"),
        ({"tamano_bytes": 0}, "ck_sesion_tamano"),
        ({"tamano_bytes": TAMANO_MAXIMO + 1}, "ck_sesion_tamano"),
        ({"titulo": ""}, "ck_sesion_titulo"),
        ({"compartida": True}, "ck_sesion_terminos"),
        ({"terminos_aceptados_en": timezone.now()}, "ck_sesion_terminos"),
    ],
    ids=[
        "grado-0",
        "grado-7",
        "origen",
        "estado",
        "doc",
        "tamano-0",
        "tamano-4194305",
        "titulo-vacio",
        "compartida-sin-fecha",
        "no-compartida-con-fecha",
    ],
)
def test_la_base_rechaza_una_sesion_incoherente(crear_sesion, campos, restriccion):
    with pytest.raises(IntegrityError, match=restriccion):
        crear_sesion(**campos)

    assert not Sesion.objects.exists()


def test_justo_4_mb_se_guarda(crear_sesion):
    assert TAMANO_MAXIMO == 4_194_304

    crear_sesion(tamano_bytes=TAMANO_MAXIMO)

    assert Sesion.objects.get().tamano_bytes == 4_194_304


def test_docx_y_compartida_con_fecha_se_guardan(crear_sesion):
    crear_sesion(tipo_mime=DOCX, compartida=True, terminos_aceptados_en=timezone.now())

    assert Sesion.objects.get().compartida


def test_la_misma_clave_de_archivo_dos_veces_la_rechaza_la_base(crear_sesion):
    primera = crear_sesion()

    with pytest.raises(IntegrityError, match="uq_sesion_archivo_clave"):
        crear_sesion(archivo_clave=primera.archivo_clave)


def test_borrar_la_autora_con_sesiones_falla(crear_sesion, docente):
    sesion = crear_sesion()

    with pytest.raises(ProtectedError) as error, transaction.atomic():
        docente.delete()

    assert sesion in error.value.protected_objects
    assert Sesion.objects.filter(pk=sesion.pk).exists()


def test_borrar_quien_la_subio_falla(crear_sesion, docente, otra_docente):
    sesion = crear_sesion(subido_por=otra_docente)

    with pytest.raises(ProtectedError) as error, transaction.atomic():
        otra_docente.delete()

    assert sesion in error.value.protected_objects


def test_borrar_el_area_con_sesiones_falla(crear_sesion, comunicacion):
    sesion = crear_sesion()

    with pytest.raises(ProtectedError) as error, transaction.atomic():
        comunicacion.delete()

    assert sesion in error.value.protected_objects


def test_borrar_la_institucion_con_sesiones_falla(crear_sesion, institucion):
    sesion = crear_sesion()

    with pytest.raises(ProtectedError) as error, transaction.atomic():
        institucion.delete()

    assert sesion in error.value.protected_objects
