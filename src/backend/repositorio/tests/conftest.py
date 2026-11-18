"""Datos ficticios de las pruebas de repositorio: reutiliza los de institucion (DoD 8)."""

import uuid

import pytest
from django.core.files.base import ContentFile
from django.core.files.storage import storages
from django.utils import timezone

from catalogo.models import Area
from institucion.tests.conftest import *  # noqa: F403 - fixtures compartidas
from repositorio import servicios
from repositorio.models import TIPO_PDF, Sesion

# Códigos SIAGIE de las áreas que usan las pruebas (catalogo/0002).
COMUNICACION = "0005"
MATEMATICA = "063"


@pytest.fixture
def comunicacion(db):
    return Area.objects.get(codigo_siagie=COMUNICACION)


@pytest.fixture
def almacen_que_firma(settings):
    """El almacén ``sesiones`` pasa a ser un ``S3Storage`` que firma sin red (D7)."""
    from repositorio.tests.almacenes import AlmacenQueFirma

    AlmacenQueFirma.llamadas = []
    settings.STORAGES = {
        **settings.STORAGES,
        "sesiones": {"BACKEND": "repositorio.tests.almacenes.AlmacenQueFirma"},
    }
    return AlmacenQueFirma


@pytest.fixture
def matematica(db):
    return Area.objects.get(codigo_siagie=MATEMATICA)


@pytest.fixture
def crear_sesion(comunicacion):
    """Guarda una sesión ficticia sin pasar por el envío; ``creado_en`` se puede fijar."""

    def crear(autor, creado_en=None, **campos):
        id_sesion = uuid.uuid4()
        texto = campos.pop("texto", "")
        valores = {
            "id": id_sesion,
            # Sin autora (material de referencia), la institución va en ``campos``.
            "institucion_id": autor.institucion_id if autor else None,
            "autor": autor,
            "subido_por": autor,
            "grado": 2,
            "area": comunicacion,
            "titulo": "Leemos un cuento",
            "proposito": "",
            "origen": Sesion.Origen.PROPIA,
            "estado": Sesion.Estado.ENVIADA,
            "compartida": False,
            "archivo_clave": f"sesiones/{id_sesion}-0123456789abcdef.pdf",
            "archivo_nombre": "leemos-un-cuento.pdf",
            "tipo_mime": TIPO_PDF,
            "tamano_bytes": 1024,
            **campos,
        }
        valores.setdefault("grado_hasta", valores["grado"])
        if valores["compartida"]:
            valores.setdefault("terminos_aceptados_en", timezone.now())
        valores["texto"] = texto
        valores["texto_busqueda"] = servicios.texto_de_busqueda(
            valores["titulo"], valores["proposito"], texto
        )
        sesion = Sesion.objects.create(**valores)
        if creado_en is not None:
            Sesion.objects.filter(pk=sesion.pk).update(creado_en=creado_en)
            sesion.refresh_from_db()
        return sesion

    return crear


@pytest.fixture
def material_de_referencia(crear_sesion, administrador, institucion):
    """Una sesión de referencia ficticia de 3.º a 5.º, como la deja ``cargar_referencia`` (D1)."""

    def crear(institucion=institucion, creado_en=None, **campos):
        valores = {
            "institucion_id": institucion.pk,
            "subido_por": administrador,
            "titulo": "Contamos y agrupamos objetos",
            "grado": 3,
            "grado_hasta": 5,
            "origen": Sesion.Origen.REFERENCIA,
            "estado": "",
            "compartida": True,
            "terminos_aceptados_en": None,
            "fuente": "Equipo del proyecto",
            "permiso_uso": "Elaborada por el equipo; uso libre en la I.E.",
            **campos,
        }
        return crear_sesion(None, creado_en=creado_en, **valores)

    return crear


@pytest.fixture
def colega_de_otra(crear_usuario, otra_institucion):
    return crear_usuario("pflores", institucion=otra_institucion, first_name="Pía")


@pytest.fixture
def con_archivo(crear_sesion):
    """Una sesión con su archivo en el almacenamiento de la suite."""

    def crear(autor, contenido=b"%PDF-1.4 cuerpo", **campos):
        sesion = crear_sesion(autor, **campos)
        storages["sesiones"].save(sesion.archivo_clave, ContentFile(contenido))
        return sesion

    return crear
