"""Comando ``extraer_textos``: texto transcrito de las sesiones ya enviadas (US-011, D3)."""

from django.core.management.base import BaseCommand

from repositorio import servicios


class Command(BaseCommand):
    help = (
        "Extrae el texto del archivo de cada sesión que no lo tiene y lo guarda para la "
        "búsqueda. No toca las que ya tienen texto: se puede repetir. Se corre una vez "
        "después de desplegar US-011."
    )

    def handle(self, *args, **options):
        self.stdout.write(servicios.transcribir_pendientes().texto())
