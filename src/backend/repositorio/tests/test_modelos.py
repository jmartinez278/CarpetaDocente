"""Pruebas de los modelos Sesion y SesionVista.

Spec envio-sesiones, «Coherencia en la base» y «No compartida con fecha»; design de US-011,
US-012 y US-016, D1.
"""

import uuid
from importlib import import_module

import pytest
from django.apps import apps
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.utils import timezone

from repositorio.models import TAMANO_MAXIMO, Sesion, SesionVista

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


def test_no_compartida_con_fecha_se_guarda(crear_sesion):
    # Escenario «No compartida con fecha»: la que dejó de compartirse conserva su aceptación.
    aceptada = timezone.now()
    sesion = crear_sesion(compartida=True, terminos_aceptados_en=aceptada)

    with transaction.atomic():
        Sesion.objects.filter(pk=sesion.pk).update(compartida=False)

    sesion.refresh_from_db()
    assert not sesion.compartida
    assert sesion.terminos_aceptados_en == aceptada


def test_una_compartida_no_puede_perder_su_fecha(crear_sesion):
    sesion = crear_sesion(compartida=True, terminos_aceptados_en=timezone.now())

    with pytest.raises(IntegrityError, match="ck_sesion_terminos"), transaction.atomic():
        Sesion.objects.filter(pk=sesion.pk).update(terminos_aceptados_en=None)


def test_el_texto_y_el_texto_de_busqueda_nacen_vacios(crear_sesion):
    sesion = crear_sesion()

    sesion.refresh_from_db()
    assert sesion.texto == ""
    assert sesion.texto_busqueda == ""


def test_mis_sesiones_tiene_su_indice_por_autora_y_fecha():
    indices = {indice.name: indice.fields for indice in Sesion._meta.indexes}

    assert indices["idx_sesion_autor_fecha"] == ["autor", "-creado_en"]
    assert "idx_sesion_autor" not in indices


def test_la_migracion_llena_el_texto_de_busqueda_con_titulo_y_proposito(crear_sesion):
    # Las sesiones de antes de este cambio se encuentran por su título sin esperar al comando
    # ``extraer_textos`` (design D3).
    sesion = crear_sesion(
        titulo="Escribimos  RECOMENDACIONES", proposito="Que la niña cuide\nel Árbol"
    )
    con_texto = crear_sesion(titulo="Otra", texto_busqueda="ya normalizado")
    migracion = import_module("repositorio.migrations.0002_texto_vistas_y_terminos")

    migracion.llenar_texto_busqueda(apps, None)

    sesion.refresh_from_db()
    con_texto.refresh_from_db()
    assert sesion.texto_busqueda == "escribimos recomendaciones que la nina cuide el arbol"
    assert con_texto.texto_busqueda == "ya normalizado"


def test_la_tabla_de_vistas_es_sesion_vista():
    assert SesionVista._meta.db_table == "sesion_vista"


def test_una_vista_guarda_sesion_usuario_y_fecha(crear_sesion, otra_docente):
    sesion = crear_sesion()

    vista = SesionVista.objects.create(sesion=sesion, usuario=otra_docente)

    assert vista.creado_en is not None
    assert list(sesion.vistas.all()) == [vista]


def test_la_misma_vista_dos_veces_la_rechaza_la_base(crear_sesion, otra_docente):
    sesion = crear_sesion()
    SesionVista.objects.create(sesion=sesion, usuario=otra_docente)

    with pytest.raises(IntegrityError, match="uq_sesion_vista"), transaction.atomic():
        SesionVista.objects.create(sesion=sesion, usuario=otra_docente)

    assert sesion.vistas.count() == 1


def test_dos_docentes_ven_la_misma_sesion(crear_sesion, docente, otra_docente):
    sesion = crear_sesion()

    SesionVista.objects.create(sesion=sesion, usuario=docente)
    SesionVista.objects.create(sesion=sesion, usuario=otra_docente)

    assert sesion.vistas.count() == 2


def test_borrar_la_sesion_borra_sus_vistas(crear_sesion, otra_docente):
    sesion = crear_sesion()
    SesionVista.objects.create(sesion=sesion, usuario=otra_docente)

    sesion.delete()

    assert not SesionVista.objects.exists()


def test_borrar_la_cuenta_con_vistas_falla(crear_sesion, otra_docente):
    vista = SesionVista.objects.create(sesion=crear_sesion(), usuario=otra_docente)

    with pytest.raises(ProtectedError) as error, transaction.atomic():
        otra_docente.delete()

    assert vista in error.value.protected_objects
    assert SesionVista.objects.filter(pk=vista.pk).exists()
