"""Almacenamiento de los archivos de las sesiones en la suite (spec almacenamiento-archivos, D2)."""

from pathlib import Path

from django.core.files.base import ContentFile
from django.core.files.storage import InMemoryStorage, storages

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
