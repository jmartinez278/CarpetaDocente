# Verificación: US-018 – Cargar sesiones del repositorio inicial

## A2 (`/codex:adversarial-review --base main`)

Corregidos en `28c9164`, con prueba de regresión (`test_migraciones_us018.py`):

- **high** · `grado_hasta` NOT NULL rompía los envíos del código anterior entre `migrate` y la publicación: `repositorio/0004` lo deja nulable, los CHECK pasan el nulo y se lee como `grado`.
- **medium** · revertir `actividad/0007` fallaba tras cargar y eliminar una referencia (el CHECK de 0006 rechaza `SESION_REFERENCIA_*`): sus pasos de CHECK van en `SoloAdelante` y la base conserva el CHECK ampliado. D1 y Migration Plan corregidos.

## Escenarios sin prueba automática

- Vista previa de Vercel con las migraciones `0003`, `0004` y `actividad/0007` en Neon, y carga y eliminación de una referencia ficticia desde el panel (tarea 4.1): pendiente, depende de la vista previa de la rama final.
- Vuelta atrás completa de `repositorio/0003` y `0004` con una referencia cargada: no se prueba; se acepta que falla y que se borran antes a mano (design, Migration Plan). Solo se prueba la de `actividad`.
- `copiar_grado` de `repositorio/0003`: sin prueba propia (ver Minor).

## Minor para la descripción del PR

- `repositorio/0003`: `copiar_grado` no tiene prueba propia (la 0002 sí). Arreglo propuesto: una prueba que llame a `copiar_grado(apps, None)` sobre una fila propia y compruebe `grado_hasta == grado`; hoy `ck_sesion_un_grado` impide armar esa fila incoherente, así que la copia se comprobó a mano sobre la base local (3 sesiones, todas con `grado_hasta = grado`).
- Mientras las tres SESION_REFERENCIA_* sigan en `RESERVADAS`, no se cumple el escenario «Cada operación tiene su prueba» de registro-actividad. Lo cierra la tarea 2.1, y `test_solo_quedan_reservadas_las_de_material_de_referencia` obliga a hacerlo.

- `uv run pytest -m e2e --browser chromium` (sin xdist): 594 pasaron y 2 dieron error de teardown en `repositorio/tests/test_sesiones_e2e.py` (`test_subir_otra_abre_un_formulario_nuevo` y `test_recargar_despues_del_exito_no_muestra_el_mensaje_ni_envia_otra`): `RuntimeError: Database access not allowed` en `close_old_connections` al cerrarse una respuesta, con «Broken pipe» en el log. Son de US-011/012/016, no de US-018. Corriendo el archivo solo, pasan los 34. Causa probable: carrera entre el servidor de la prueba y el teardown. No investigado; a la deuda de e2e en paralelo.
- `grado_hasta` queda nulable: pasar a NOT NULL es una migración posterior, ya sin el código anterior en servicio (deuda de la historia siguiente).

## DoD 1 a 9

1. Cobertura ≥ 80 %: 98,62 % local (`verificar.py --completo`). Sonar way: pendiente del PR.
2. Análisis estático: Ruff y formato en verde; A2 con 2 hallazgos corregidos. CodeQL y SonarQube Cloud: pendiente del PR.
3. Aprobación de otra integrante: pendiente del PR.
4. Vista previa de Vercel: pendiente del PR (ver escenarios sin prueba).
5. Escenarios y e2e: `-m e2e` completo, 594 en verde y 2 errores de teardown de US-011/012/016 (ver Minor), antes de `28c9164`. GitHub Actions: pendiente del PR.
6. Reglas de negocio: referencia sin autora, rango de grados, CHECK de coherencia, borrado solo con `operacion_al_borrar` y RN-015 sin contenido en el registro; con pruebas de servicios.
7. Accesibilidad: pantallas de la parte C con axe en las pruebas e2e; vistas por Marco según las tareas.
8. Sin datos reales: fixtures y referencias de prueba ficticias.
9. Documentación: README sin cambios. Deuda en «Minor para la descripción del PR».
