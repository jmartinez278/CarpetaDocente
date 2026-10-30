"""Comando ``cargar_demo``: llena 1.º A a 2.º D con datos ficticios (EN-06, D6 a D8)."""

import os

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from institucion import demo
from institucion.models import Institucion


class Command(BaseCommand):
    help = (
        "Carga las 8 primeras secciones del año ABIERTO con una docente demo, estudiantes "
        "ficticios y 10 días de asistencia. La contraseña de las cuentas va en DEMO_CLAVE."
    )

    def add_arguments(self, parser):
        parser.add_argument("--institucion", type=int, required=True, help="Id de la institución")
        parser.add_argument(
            "--estudiantes", type=int, default=25, help="Estudiantes por sección, de 1 a 60"
        )
        parser.add_argument(
            "--confirmar", action="store_true", help="Obligatorio fuera del modo de desarrollo"
        )

    def handle(self, *args, **options):
        try:
            institucion = Institucion.objects.get(pk=options["institucion"])
        except Institucion.DoesNotExist:
            raise CommandError(f"No existe la institución {options['institucion']}.") from None
        datos = (
            institucion,
            options["estudiantes"],
            timezone.localdate(),
            os.environ.get("DEMO_CLAVE", ""),
        )
        try:
            if not settings.DEBUG and not options["confirmar"]:
                plan = demo.planear_demo(*datos)
                self.stdout.write(f"Se cargaría: {plan.texto()}")
                raise CommandError("Fuera del modo de desarrollo hace falta --confirmar.")
            resumen = demo.cargar_demo(*datos)
        except ValidationError as error:
            raise CommandError(" ".join(error.messages)) from None
        self.stdout.write(f"Demostración cargada. {resumen.texto()}")
