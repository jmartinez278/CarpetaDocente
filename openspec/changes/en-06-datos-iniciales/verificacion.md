# Verificación: EN-06 – Catálogo curricular y datos ficticios

## Evidencia por parte

### Grupo 1, parte A: modelos y migraciones (1.1 a 1.3)

- 1.1: `catalogo/tests/test_modelos.py` falló primero (`ImportError` de `Area`) y luego pasó (9 pruebas). `makemigrations --check` no da cambios. `sqlmigrate catalogo 0001` muestra `uq_competencia`, `uq_institucion_area` y el `UNIQUE` de `codigo_siagie` y de `nombre` en `area`.
- 1.2: `catalogo/tests/test_migracion_catalogo.py` falló primero (no existía `0002_catalogo_siagie`) y luego pasó (13 pruebas). En la base local, `migrate catalogo zero` y `migrate` funcionan, y quedan 11 áreas, 30 competencias y 11 filas de `institucion_area` para la institución local.
- 1.3: el revisor no encontró Critical ni Important. `verificar.py --antes-del-commit` PASA (cobertura 98,31 %, 978 pruebas).

### Grupo 1, parte B: áreas de cada institución y panel (1.4 a 1.6)

- 1.4: `catalogo/tests/test_servicios.py` falló primero (`ImportError` de `servicios`; luego, con `asegurar_areas` y sin la señal, 3 de 4 fallaron porque la institución nacía sin filas) y pasó con la señal (4 pruebas). Con la señal activa, `catalogo` (26) y la suite completa (982) pasan, también `test_modelos.py` (Minor 5).
- 1.5: `catalogo/tests/test_admin.py` falló primero (18 de 20; las dos de «otro rol» ya pasaban por `IngresoPanelView`) y luego pasó (20 pruebas). `uv run pytest --cov`: 1002 pruebas, cobertura 98,51 %.
- 1.6: el revisor no encontró Critical; su único Important era esta evidencia.

## Minor para la descripción del PR

- La prueba con `MigrationExecutor` (`test_migracion_catalogo.py`) vuelve a `catalogo 0001` y solo reaplica `catalogo 0002`. Cuando una migración de otra app dependa de `catalogo` (US-027, US-028, US-020), conviene terminar la prueba migrando a `executor.loader.graph.leaf_nodes()`.
- La fixture `catalogo` reproduce solo la carga de `0002`. Si una migración futura corrige un texto, la fixture tiene que aplicar también esa corrección, porque si no crea la competencia vieja como nueva.
- Las pruebas comparan unos 7 de los 30 textos de competencias, que es lo que pide la tarea. Comparar la lista completa detectaría un cambio accidental en `0002`.
- No hay prueba de `RESTRICT` en `InstitucionArea.area`: la tarea 1.1 solo lo pide para `Competencia.area`.
- En `test_modelos.py`, que las pruebas no dependan de la señal de la parte B se basa en el orden de los argumentos `(institucion, area)`.
- En `conftest.py`, `from django.apps import apps` va dentro de la fixture y no arriba (estilo).
- «Campos fijos» se prueba solo en la ficha del área, como pide el spec; que `area` y `nombre` de la competencia, e `institucion` y `area` de la fila, sean de solo lectura no tiene prueba.
- «Otro rol» se prueba solo con `/admin/catalogo/area/`; las otras dos listas las cubre el mismo `IngresoPanelView`.
- `test_sin_accion_eliminar_en_lote` no revisa el código de la respuesta del POST, solo que el objeto siga existiendo.
- `ignore_conflicts=True` en `asegurar_areas` callaría también otro conflicto de unicidad de `institucion_area`; hoy solo existe `uq_institucion_area`.
