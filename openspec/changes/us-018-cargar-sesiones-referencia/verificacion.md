# Verificación: US-018 – Cargar sesiones del repositorio inicial

Se completa en la tarea 4.2 (DoD 1 a 9, carga en la vista previa y escenarios sin prueba).

## Minor de la revisión

### Parte A (revisor)

- `repositorio/0003`: `copiar_grado` no tiene prueba propia (la 0002 sí). Arreglo propuesto: una prueba que llame a `copiar_grado(apps, None)` sobre una fila propia y compruebe `grado_hasta == grado`; hoy `ck_sesion_un_grado` impide armar esa fila incoherente, así que la copia se comprobó a mano sobre la base local (3 sesiones, todas con `grado_hasta = grado`).
- Mientras las tres SESION_REFERENCIA_* sigan en `RESERVADAS`, no se cumple el escenario «Cada operación tiene su prueba» de registro-actividad. Lo cierra la tarea 2.1, y `test_solo_quedan_reservadas_las_de_material_de_referencia` obliga a hacerlo.
