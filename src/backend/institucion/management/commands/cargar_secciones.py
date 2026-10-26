"""Comando ``cargar_secciones``: crea el año escolar y sus secciones (US-005, D5)."""

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from institucion import servicios
from institucion.models import Institucion


class Command(BaseCommand):
    help = "Crea el año escolar ABIERTO y sus secciones de 1.º a 6.º grado, A a D, sin docentes."

    def add_arguments(self, parser):
        parser.add_argument("--anio", type=int, required=True, help="Año escolar, por ejemplo 2027")
        parser.add_argument("--institucion", type=int, required=True, help="Id de la institución")

    def handle(self, *args, **options):
        anio = options["anio"]
        try:
            institucion = Institucion.objects.get(pk=options["institucion"])
        except Institucion.DoesNotExist:
            raise CommandError(f"No existe la institución {options['institucion']}.") from None
        try:
            _, anio_creado, creadas = servicios.cargar_secciones(institucion, anio)
        except ValidationError as error:
            raise CommandError(" ".join(error.messages)) from None
        if creadas == 0:
            self.stdout.write(f"No se creó nada: el año {anio} ya tiene sus 24 secciones.")
        elif anio_creado:
            self.stdout.write(f"Año {anio} creado. Secciones creadas: {creadas}.")
        else:
            self.stdout.write(f"Secciones creadas: {creadas}.")
