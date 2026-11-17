# Verificación: US-018 – Cargar sesiones del repositorio inicial

Se completa en la tarea 4.2 (DoD 1 a 9, carga en la vista previa y escenarios sin prueba).

## Minor de la revisión

### Parte A (revisor)

- `repositorio/0003`: `copiar_grado` no tiene prueba propia (la 0002 sí). Arreglo propuesto: una prueba que llame a `copiar_grado(apps, None)` sobre una fila propia y compruebe `grado_hasta == grado`; hoy `ck_sesion_un_grado` impide armar esa fila incoherente, así que la copia se comprobó a mano sobre la base local (3 sesiones, todas con `grado_hasta = grado`).
- Mientras las tres SESION_REFERENCIA_* sigan en `RESERVADAS`, no se cumple el escenario «Cada operación tiene su prueba» de registro-actividad. Lo cierra la tarea 2.1, y `test_solo_quedan_reservadas_las_de_material_de_referencia` obliga a hacerlo.

### Suite e2e completa (parte D)

- `uv run pytest -m e2e --browser chromium` (sin xdist): 594 pasaron y 2 dieron error de teardown en `repositorio/tests/test_sesiones_e2e.py` (`test_subir_otra_abre_un_formulario_nuevo` y `test_recargar_despues_del_exito_no_muestra_el_mensaje_ni_envia_otra`): `RuntimeError: Database access not allowed` en `close_old_connections` al cerrarse una respuesta, con «Broken pipe» en el log. Son de US-011/012/016, no de US-018. Corriendo el archivo solo, pasan los 34. Causa probable: carrera entre el servidor de la prueba y el teardown. No investigado; a la deuda (ver [[deuda-e2e-xdist]]).
