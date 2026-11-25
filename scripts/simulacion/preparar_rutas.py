"""Base propia de la simulación (G2): institución simulada, sim01 en 3.º A y su limpieza.

Todo ocurre en la institución «I.E. Simulada (datos simulados)». La institución 1 y la demo no se
tocan. La base (institución, año ABIERTO 2026, 4 bimestres, áreas y 24 secciones) se arma una sola
vez y G3 la reutiliza; ``quitar`` limpia solo lo de la simulación y la deja armada.

Guardas: solo con DEBUG (base local), y se niega si la institución simulada tiene datos que no son
de la simulación (cuentas que no son ``simNN``, secciones con otra docente o estudiantes sin una
docente ``simNN``).

Uso (con la base local arriba y la clave en la variable de entorno SIM_CLAVE):

    uv run python scripts/simulacion/preparar_rutas.py preparar
    uv run python scripts/simulacion/preparar_rutas.py quitar
"""

# ruff: noqa: E402  (Django se configura antes de importar los modelos, también al correr suelto)

import argparse
import os
import random
import re
import sys
from pathlib import Path

import django
from django.apps import apps

RAIZ = Path(__file__).resolve().parents[2]


def _preparar_django() -> None:
    if apps.ready:
        return
    backend = str(RAIZ / "src" / "backend")
    if backend not in sys.path:
        sys.path.insert(0, backend)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()


_preparar_django()

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction

from cuentas.models import Usuario
from institucion import demo, servicios
from institucion.models import AnioEscolar, Estudiante, Institucion, Periodo, Seccion
from notas import servicios as notas
from repositorio import servicios as repositorio
from repositorio.models import Sesion, SesionVista

NOMBRE_INSTITUCION = "I.E. Simulada (datos simulados)"
ANIO = 2026
DOCENTE = "sim01"
GRADO, SECCION = 3, "A"
ESTUDIANTES = 30
CUENTA_SIM = re.compile(r"^sim\d{2}$")


class BaseNoSegura(Exception):
    """La operación se niega: no es la base local o hay datos que no son de la simulación."""


def _exigir_local() -> None:
    if not settings.DEBUG:
        raise BaseNoSegura("Solo con DEBUG (base local): la simulación nunca corre en producción.")


def _exigir_clave(clave: str) -> None:
    if not clave:
        raise BaseNoSegura("Falta la variable SIM_CLAVE con la contraseña de sim01.")


def _institucion() -> Institucion | None:
    return Institucion.objects.filter(nombre=NOMBRE_INSTITUCION).first()


def _es_sim(cuenta: Usuario | None) -> bool:
    return cuenta is not None and bool(CUENTA_SIM.match(cuenta.username))


def _revisar_ajenos(institucion: Institucion) -> None:
    """Se niega si la institución simulada tiene algo que no es de la simulación."""
    ajenos = []
    for cuenta in Usuario.objects.filter(institucion=institucion):
        if not CUENTA_SIM.match(cuenta.username):
            ajenos.append(f"la cuenta {cuenta.username}")
    secciones = Seccion.objects.filter(anio_escolar__institucion=institucion).select_related(
        "docente"
    )
    for seccion in secciones:
        texto = servicios.texto_seccion_corto(seccion)
        if seccion.docente is not None and not _es_sim(seccion.docente):
            ajenos.append(f"la docente de {texto}")
        elif seccion.docente is None and seccion.estudiantes.exists():
            ajenos.append(f"los estudiantes de {texto}")
    if ajenos:
        raise BaseNoSegura(
            "La institución simulada tiene datos que no son de la simulación: "
            + ", ".join(ajenos)
            + ". No se toca nada."
        )


def preparar_base() -> Institucion:
    """Arma la base una sola vez: institución, año ABIERTO 2026, 4 bimestres, áreas y secciones."""
    _exigir_local()
    with transaction.atomic():
        institucion = _institucion()
        if institucion is None:
            # La señal de catálogo le da sus áreas al crearla (catalogo/signals.py).
            institucion = Institucion.objects.create(
                nombre=NOMBRE_INSTITUCION,
                organizacion_periodos=Institucion.OrganizacionPeriodos.BIMESTRE,
            )
        else:
            _revisar_ajenos(institucion)
        anio, _, _ = servicios.cargar_secciones(institucion, ANIO)
        if not anio.periodos.exists():
            servicios.guardar_periodos(anio, demo.bimestres_ejemplo(ANIO))
    return institucion


def _lista(azar: random.Random, cantidad: int) -> str:
    """Estudiantes ficticios «APELLIDOS, NOMBRES», sin repetir; los mismos con la misma semilla."""
    estudiantes = set()
    while len(estudiantes) < cantidad:
        apellidos = f"{azar.choice(demo.APELLIDOS)} {azar.choice(demo.APELLIDOS)}"
        estudiantes.add((apellidos, azar.choice(demo.NOMBRES)))
    return "\n".join(f"{apellidos}, {nombres}" for apellidos, nombres in sorted(estudiantes))


def _cuenta(institucion: Institucion, clave: str) -> Usuario:
    """La docente sim01: nueva (normal, no demo) o la existente reactivada con la clave."""
    otra = Usuario.objects.filter(username=DOCENTE).exclude(institucion=institucion).first()
    if otra is not None:
        raise BaseNoSegura(f"{DOCENTE} ya existe en otra institución: no se reutiliza.")
    cuenta = Usuario.objects.filter(username=DOCENTE).first()
    if cuenta is None:
        return Usuario.objects.create_user(
            username=DOCENTE,
            password=clave,
            rol=Usuario.Rol.DOCENTE,
            institucion=institucion,
            es_demo=False,
            first_name="Docente",
            last_name="Simulada",
        )
    cuenta.is_active = True
    cuenta.debe_cambiar_password = False
    cuenta.set_password(clave)
    cuenta.save()
    return cuenta


def preparar_docente(institucion: Institucion, clave: str, hoy) -> Seccion:
    """sim01 en 3.º A, con 30 estudiantes ficticios y sin asistencia ni notas previas."""
    _exigir_local()
    _exigir_clave(clave)
    with transaction.atomic():
        _revisar_ajenos(institucion)
        anio = AnioEscolar.objects.get(institucion=institucion, anio=ANIO)
        seccion = Seccion.objects.select_for_update(of=("self",)).get(
            anio_escolar=anio, grado=GRADO, nombre=SECCION
        )
        cuenta = _cuenta(institucion, clave)
        seccion.docente = cuenta
        seccion.save()
        if not Estudiante.objects.filter(seccion=seccion).exists():
            azar = random.Random(f"sim-{GRADO}{SECCION}")  # noqa: S311
            _, errores = servicios.importar_lista_sin_registro(seccion, _lista(azar, ESTUDIANTES))
            if errores:
                raise ValidationError([error.titulo for error in errores])
        empezados = Periodo.objects.filter(anio_escolar=anio, fecha_inicio__lte=hoy)
        notas.marcar_todo_sin_registro(seccion, list(empezados))
    return Seccion.objects.get(pk=seccion.pk)


def quitar() -> int:
    """Limpia lo de la simulación en su institución y deja la base armada.

    Borra estudiantes, asistencia, marcas y notas de las secciones con docente ``simNN``, y las
    sesiones que enviaron esas cuentas. Libera las secciones y desactiva las cuentas. Devuelve
    cuántos estudiantes borró.
    """
    _exigir_local()
    institucion = _institucion()
    if institucion is None:
        return 0
    with transaction.atomic():
        _revisar_ajenos(institucion)
        secciones = Seccion.objects.filter(
            anio_escolar__institucion=institucion,
            anio_escolar__estado=AnioEscolar.Estado.ABIERTO,
            docente__isnull=False,
        ).select_related("docente")
        borrados = 0
        for seccion in secciones:
            borrados += demo.descartar_seccion(seccion).estudiantes
            seccion.docente = None
            seccion.save()
        # Las sesiones que enviaron las cuentas de la simulación, con sus archivos y vistas.
        repositorio.borrar_sesiones(Sesion.objects.filter(autor__institucion=institucion))
        SesionVista.objects.filter(usuario__institucion=institucion).delete()
        for cuenta in Usuario.objects.filter(institucion=institucion):
            cuenta.is_active = False
            cuenta.save()
    return borrados


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Base propia de la simulación (datos simulados).")
    parser.add_argument("orden", choices=["preparar", "quitar"])
    orden = parser.parse_args(argv).orden
    try:
        if orden == "preparar":
            clave = os.environ.get("SIM_CLAVE", "")
            _exigir_local()
            _exigir_clave(clave)
            institucion = preparar_base()
            seccion = preparar_docente(institucion, clave, _hoy())
            print(
                f"Base «{institucion.nombre}» (id {institucion.pk}) lista. {DOCENTE} en "
                f"{servicios.texto_seccion_corto(seccion)} con {seccion.estudiantes.count()} "
                "estudiantes."
            )
        else:
            print(f"Estudiantes borrados: {quitar()}. La base queda armada.")
    except (BaseNoSegura, ValidationError) as error:
        print(" ".join(getattr(error, "messages", [str(error)])))
        return 1
    return 0


def _hoy():
    from django.utils import timezone

    return timezone.localdate()


if __name__ == "__main__":
    sys.exit(main())
