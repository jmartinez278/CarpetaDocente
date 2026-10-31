# Verificación: US-028 – Configurar los periodos del año escolar

## Minor del revisor

### Parte 1A: `btree_gist`, `Periodo` y migración

- `test_modelos_periodo.py`: `test_la_base_crea_la_extension_btree_gist` ya no puede fallar en la base de pruebas, porque `institucion/0005` crea la extensión antes. Sirvió para la comprobación previa al modelo (tarea 1.1); en Neon, la prueba es la vista previa de Vercel (tarea 1.3).
- `test_modelos_periodo.py`: el cruce se prueba con `SET CONSTRAINTS … IMMEDIATE` y no al confirmar (pytest-django revierte la transacción). Que no estalle en el `COMMIT` lo cubren las tareas 2.2 y 2.3.
- `models.py`, `Periodo.__str__`: hace una consulta por periodo para leer `anio_escolar`. Si el inline lo muestra por fila, usar `select_related`.

### Parte 2A: servicios, registro de actividad y periodo vigente

- Tarea 2.3: su texto pide que uno de los dos guardados reciba `MENSAJE_CRUCE`. Con el bloqueo de D4 y la escritura por número, el segundo espera y edita lo del primero (4 PERIODO_EDITADO); la prueba fija eso. Sin el bloqueo, el resultado es `IntegrityError` de `uq_periodo`. El cruce que solo ve la base lo cubre `test_cruce_que_solo_ve_la_base_da_el_mensaje_sin_guardar_nada`. También son nuevos: `validar_organizacion` y el rechazo de vaciar las filas de un año que ya tiene periodos.
- `guardar_periodos` bloquea primero la institución y después el año. Desde la ficha del año, `RegistraEnPanel` bloquea primero el año, así que el orden queda al revés y puede haber un deadlock con la demo. Se resuelve en la tarea 2.6.
- `test_concurrencia_periodos.py`: `segundo.join(1)` depende del tiempo y no comprueba que el segundo hilo esté esperando el bloqueo.

### Parte 2B: ficha del año y de la institución en el panel

- `AnioEscolarAdmin`: `institucion` sigue editable en la ficha. Mover a otra institución un año con periodos se salta la organización fija (D5); si además cambian las fechas, `validar_periodos` da `ValueError` (500). Solo pasa con más de una institución: deuda, o `institucion` de solo lectura cuando el año tiene periodos.
- `test_admin_periodos.py`: falta la prueba de un POST que cierra el año y cambia periodos a la vez (se rechaza con "El año escolar está cerrado…" y no guarda nada).
- `FormsetPeriodos.poner_error`: un `error_dict` del guardado con claves que no son números de fila daría 500; hoy `guardar_periodos` no lo produce.
