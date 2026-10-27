#!/usr/bin/env python
"""Entrada de manage.py desde la raíz del repo (EN-02, D6).

Vercel detecta Django buscando manage.py en la raíz o en un subdirectorio inmediato;
el proyecto vive en src/backend/. Este archivo solo agrega esa carpeta a sys.path y
delega: cualquier comando de manage.py funciona igual desde aquí.
"""

import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent / "src" / "backend"


def main():
    """Run administrative tasks."""
    sys.path.insert(0, str(BACKEND_DIR))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
