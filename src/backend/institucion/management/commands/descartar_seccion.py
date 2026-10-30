"""Comando ``descartar_seccion``: borra lo cargado en una sección del piloto (EN-06, D9)."""

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from institucion import demo, servicios
from institucion.models import Seccion


class Command(BaseCommand):
    help = (
        "Borra estudiantes, jornadas y asistencia de una sección del año ABIERTO y conserva "
        "su docente. Hacer antes un respaldo de la base."
    )

    def add_arguments(self, parser):
        parser.add_argument("--seccion", type=int, required=True, help="Id de la sección")
        parser.add_argument("--confirmar", action="store_true", help="Sin él, no borra nada")

    def handle(self, *args, **options):
        try:
            seccion = Seccion.objects.get(pk=options["seccion"])
        except Seccion.DoesNotExist:
            raise CommandError(f"No existe la sección {options['seccion']}.") from None
        nombre = servicios.texto_seccion_corto(seccion)
        if not options["confirmar"]:
            plan = demo.conteos_seccion(seccion)
            raise CommandError(f"Se borraría de {nombre}: {plan.texto()}. Repite con --confirmar.")
        try:
            conteos = demo.descartar_seccion(seccion)
        except ValidationError as error:
            raise CommandError(" ".join(error.messages)) from None
        self.stdout.write(f"{nombre} descartada: {conteos.texto()} borrados.")
