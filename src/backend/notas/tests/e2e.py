"""Utilidades de las pruebas e2e de la hoja de notas (test_hoja_e2e y test_borradores_e2e).

Las fixtures que abren la hoja (``estudiantes``, ``hoja_lista``, ``abrir_hoja``) están en
``conftest.py``.
"""

from zoneinfo import ZoneInfo

from notas.models import Calificacion
from notas.tests.conftest import MATEMATICA, competencia

LIMA = ZoneInfo("America/Lima")


def url_hoja(live_server, seccion, **parametros):
    consulta = "&".join(f"{k}={v}" for k, v in parametros.items())
    base = f"{live_server.url}/docente/secciones/{seccion.pk}/notas/"
    return f"{base}?{consulta}" if consulta else base


def entrada(page, estudiante, orden):
    """La celda de teclado de la competencia ``orden`` (1…n) de Matemática."""
    comp = competencia(MATEMATICA, orden)
    return page.locator(f'.notas-nivel[data-est="{estudiante.pk}"][data-comp="{comp.pk}"]')


def boton_movil(page, estudiante, orden):
    comp = competencia(MATEMATICA, orden)
    return page.locator(f'.notas-celda-movil[data-est="{estudiante.pk}"][data-comp="{comp.pk}"]')


def estado(page):
    return page.locator("#estado-guardado")


def guardar(page):
    page.locator("#guardar").click()


def notas_en_la_base():
    return {
        (c.estudiante_id, c.competencia_id): (c.nivel, c.conclusion_descriptiva)
        for c in Calificacion.objects.all()
    }
