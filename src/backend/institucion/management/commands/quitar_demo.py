"""Comando ``quitar_demo``: libera las secciones demo y desactiva sus cuentas (EN-06, D9)."""

from django.core.management.base import BaseCommand, CommandError

from institucion import demo


class Command(BaseCommand):
    help = (
        "Borra estudiantes, jornadas y asistencia de las secciones demo, las deja sin docente "
        "y desactiva las cuentas demo. Se ejecuta antes de cargar las listas del piloto."
    )

    def add_arguments(self, parser):
        parser.add_argument("--confirmar", action="store_true", help="Sin él, no borra nada")

    def handle(self, *args, **options):
        if not options["confirmar"]:
            plan = demo.conteos_demo()
            raise CommandError(f"Se borraría: {plan.texto()} Repite con --confirmar.")
        self.stdout.write(demo.quitar_demo().texto())
