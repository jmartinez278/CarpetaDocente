"""Almacenamiento de los archivos de las sesiones en la suite (spec almacenamiento-archivos, D2)."""

import uuid
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest
from django.core.files.base import ContentFile
from django.core.files.storage import InMemoryStorage, storages

from repositorio import servicios
from repositorio.models import TIPO_PDF, Sesion
from repositorio.tests.almacenes import ENDPOINT

RAIZ = Path(__file__).resolve().parents[4]


def test_en_las_pruebas_los_archivos_van_a_memoria():
    # Escenario «Pruebas»: ninguna prueba escribe en media/ ni se conecta a R2.
    assert isinstance(storages["sesiones"], InMemoryStorage)


def test_guardar_en_las_pruebas_no_crea_archivos_en_media():
    antes = set((RAIZ / "media").rglob("*")) if (RAIZ / "media").exists() else set()

    nombre = storages["sesiones"].save("sesiones/prueba.pdf", ContentFile(b"%PDF-1.4"))

    assert nombre == "sesiones/prueba.pdf"
    assert storages["sesiones"].exists(nombre)
    despues = set((RAIZ / "media").rglob("*")) if (RAIZ / "media").exists() else set()
    assert despues == antes


def test_git_ignora_los_archivos_de_la_laptop():
    # Escenario «Laptop»: lo que queda en media/sesiones/ no aparece en git status. Se lee
    # .gitignore y no se llama a git: verificar.py corre la suite en una copia del índice,
    # fuera del repositorio.
    reglas = (RAIZ / ".gitignore").read_text(encoding="utf-8").splitlines()

    assert "media/" in reglas


# --- Enlace firmado (spec almacenamiento-archivos; design de US-011, D7) ---


@pytest.mark.django_db
def test_con_un_almacen_que_firma_la_entrega_es_un_enlace_de_60_segundos(
    almacen_que_firma, docente, comunicacion
):
    # Escenario «Descarga en Vercel»: el enlace lleva la clave, 60 s y el nombre original.
    sesion = Sesion.objects.create(
        id=uuid.uuid4(),
        institucion_id=docente.institucion_id,
        autor=docente,
        subido_por=docente,
        grado=2,
        area=comunicacion,
        titulo="Leemos un cuento",
        origen=Sesion.Origen.PROPIA,
        estado=Sesion.Estado.ENVIADA,
        archivo_clave="sesiones/abc-0123456789abcdef.pdf",
        archivo_nombre="Sesión ñandú.pdf",
        tipo_mime=TIPO_PDF,
        tamano_bytes=10,
    )

    entrega = servicios.entregar_archivo(docente, sesion.pk, "ver")

    assert almacen_que_firma.llamadas == [
        {
            "name": "sesiones/abc-0123456789abcdef.pdf",
            "parameters": {
                "ResponseContentDisposition": (
                    "inline; filename*=utf-8''Sesi%C3%B3n%20%C3%B1and%C3%BA.pdf"
                ),
                "ResponseContentType": TIPO_PDF,
                "ResponseCacheControl": "no-store",
            },
            "expire": 60,
        }
    ]
    assert entrega.archivo is None
    consulta = parse_qs(urlsplit(entrega.url).query)
    assert entrega.url.startswith(ENDPOINT)
    assert consulta["X-Amz-Expires"] == ["60"]
    assert consulta["response-content-type"] == [TIPO_PDF]
    # Escenario «Respuesta sin caché»: la que trae el archivo es la de R2, no la del aplicativo.
    assert consulta["response-cache-control"] == ["no-store"]
    assert consulta["response-content-disposition"] == [
        "inline; filename*=utf-8''Sesi%C3%B3n%20%C3%B1and%C3%BA.pdf"
    ]
