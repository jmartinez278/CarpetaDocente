# Verificación: US-008 – Registrar la actividad de los usuarios

Rama `feature/US-008-registrar-actividad`. Pruebas en `src/backend/actividad/tests/`. Abreviaturas: `mod` = `test_modelos.py`, `reg` = `test_registrar.py`. La tabla crece con cada parte; la tarea 3.2 la completa con los dos specs y la DoD 1 a 9.

## Escenarios de `registro-actividad` (parte 1A)

| Escenario | Prueba |
| --- | --- |
| Operación fuera del catálogo | `mod::test_operacion_fuera_del_catalogo_la_rechaza_la_base` (base); `reg::test_operacion_fuera_del_catalogo_lanza_value_error_sin_guardar` (servicio) |
| La operación falla | `reg::test_la_operacion_falla_y_no_queda_entrada` |
| El registro falla | `reg::test_el_registro_falla_y_la_operacion_no_se_guarda` |
| Desde el código | `mod::test_guardar_de_nuevo_una_entrada_existente_lanza_permission_denied`, `test_borrar_una_entrada_lanza_permission_denied` |
| Detalle sin datos personales (mecanismo) | `reg::test_clave_de_detalle_no_permitida_lanza_value_error_sin_guardar`; el recorrido de las entradas reales llega con la tarea 2.6 |

Además: usuario vacío (`mod::test_usuario_vacio_se_permite`, `test_borrar_el_usuario_deja_la_entrada_con_usuario_vacio`, `reg::test_usuario_anonimo_queda_vacio`), orden (`mod::test_orden_de_la_mas_reciente_a_la_mas_antigua`), marcas del catálogo (`mod::test_solo_las_operaciones_de_asistencia_cuentan_para_kpi_01`, `test_solo_intento_sin_permiso_esta_reservada`) y `registrar` fuera de una transacción (`reg::test_fuera_de_una_transaccion_lanza_runtime_error`).

Las pruebas de "falla" usan savepoints y no `transaction=True`: una transacción real vacía la base y rompe las pruebas con `serialized_rollback` de `institucion`.

## Minor para la descripción del PR

Parte 1A (revisión de la parte):

- `reg::test_fuera_de_una_transaccion_lanza_runtime_error` simula la ausencia de transacción con `monkeypatch` de `connection.in_atomic_block`; no la prueba contra una conexión real sin transacción.
- Sin prueba de un detalle con claves permitidas que se guarda tal cual, salvo el de REGISTRO_ASISTENCIA, ni de `detalle` que no sea un diccionario.
- `entidad` y `entidad_id` no se validan contra su `max_length` (60 y 40): un valor largo da un `DataError` de PostgreSQL que revierte la operación, coherente con el spec pero con un mensaje poco claro. Improbable con `db_table` e ids.
- `bulk_update`, `QuerySet.update()` y `delete()` no pasan por `save()` ni `delete()` del modelo; el bloqueo en la base es EN-04 (ya en la deuda).
- `DETALLE_PERMITIDO` deja sin claves a las operaciones sin detalle y a las tres de demostración; las claves de estas se agregan en la tarea 2.4.
