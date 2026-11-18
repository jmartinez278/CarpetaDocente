"""Migraciones de US-018: despliegue con el código anterior y vuelta atrás (revisión A2)."""

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

from actividad.models import Operacion, RegistroActividad


def test_grado_hasta_nulo_pasa_los_check_como_el_codigo_anterior(crear_sesion, docente):
    sesion = crear_sesion(docente, grado_hasta=None)
    sesion.refresh_from_db()
    assert sesion.grado_hasta is None
    assert sesion.grados_texto == "2.º grado"


def test_el_filtro_de_grado_incluye_la_fila_sin_grado_final(crear_sesion, docente):
    from repositorio import servicios
    from repositorio.models import Sesion

    sesion = crear_sesion(docente, grado_hasta=None)
    assert sesion in servicios._del_grado(Sesion.objects.all(), 2)
    assert sesion not in servicios._del_grado(Sesion.objects.all(), 3)


@pytest.mark.django_db(transaction=True)
def test_revertir_actividad_con_entradas_de_referencia_no_falla(administrador):
    RegistroActividad.objects.create(
        usuario=administrador, operacion=Operacion.SESION_REFERENCIA_CARGADA
    )
    ejecutor = MigrationExecutor(connection)
    hojas = ejecutor.loader.graph.leaf_nodes()
    try:
        ejecutor.migrate([("actividad", "0006_operaciones_sobre_sesiones")])
    finally:
        MigrationExecutor(connection).migrate(hojas)
