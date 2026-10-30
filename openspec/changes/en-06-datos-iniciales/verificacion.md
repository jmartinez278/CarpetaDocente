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

### Grupo 2: datos de demostración (2.1 a 2.4)

- 2.1: `institucion/tests/test_demo.py` falló primero (22 de 22, con `demo.py` vacío) y luego pasó. Dos fallas eran de la prueba y no del código: el 1-1-2027 es viernes y entra entre los días hábiles, y `last_name` se guarda en tipo título.
- 2.2: las 8 pruebas de quitar y descartar fallaron primero (`AttributeError`) y luego pasaron.
- 2.3: `institucion/tests/test_comandos_demo.py` falló primero (12 de 12, comandos inexistentes) y luego pasó. `uv run pytest --cov`: 1044 pruebas, cobertura 98,48 %.
  - En la base local, el año abierto era 2027 y hoy es 30-10-2026, así que `cargar_demo` dio «0 días de asistencia». Con la opción que eligió el equipo, se cerró 2027 en local y se cargó 2026 (`cargar_secciones --anio 2026`).
  - Con eso, `quitar_demo --confirmar` y `cargar_demo` reactivaron las 8 cuentas. `demounoa` ingresa (302 a `/docente/`) y ve la portada de 1.° A con 10 jornadas del 16 al 29 de octubre, de lunes a viernes, con 25 estados cada una y la toma a las 8:00 de Lima. El README pasa la carga inicial de producción a 2026 (decisión del equipo).
- 2.4: el revisor no encontró Critical. Encontró dos Important:
  - Una recarga no ponía la clave vigente a las cuentas demo activas ni les quitaba el cambio de contraseña pendiente, aunque el design dice que la clave se rota con una nueva carga. Se corrigió con la prueba primero: `test_volver_a_cargar_pone_la_clave_nueva` y `test_cuenta_demo_activa_sin_seccion_queda_sin_cambio_pendiente` fallaron y luego pasaron.
  - Faltaba esta evidencia.
  - Después de las correcciones, la suite completa da 1046 pruebas y 98,48 % de cobertura.

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
- `descartar_seccion` sin `--confirmar` sobre un año CERRADO dice «Se borraría…», aunque con `--confirmar` se negaría; no hay prueba del año cerrado a nivel de comando.
- `quitar_demo` sin demo y sin `--confirmar`, y `cargar_demo` con la demo ya cargada fuera de desarrollo y sin `--confirmar`, imprimen un plan que se contradice («Se borraría: No hay demostración…», «Se cargaría: La demostración ya está cargada…»).
- Dos `cargar_demo` a la vez: `importar_lista` lanza `SeccionConEstudiantes`, que no se convierte en `CommandError` (traceback; la transacción revierte igual).
- `quitar_demo` cuenta lo que borra antes del `select_for_update`: con escrituras concurrentes, el resumen puede quedar desfasado.
- No se valida la fuerza de `DEMO_CLAVE` (`password_validation.validate_password`).
- El docstring de `demo.py` dice que cada función corre en una transacción; `planear_demo`, `conteos_*` y `secciones_demo` solo leen.
- El README no dice de dónde sacar el id de `--institucion` (panel o `shell`).
