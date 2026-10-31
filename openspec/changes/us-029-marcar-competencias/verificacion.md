# Verificación: US-029 – Marcar las competencias desarrolladas en el periodo

## Minor para la descripción del PR

### Parte A: `CompetenciaPeriodo`, `a_cargo_docente_curso` y migraciones

- `catalogo/tests/test_admin.py`, `test_otro_rol_no_cambia_a_cargo_del_docente_de_curso`: buscar `a_cargo_docente_curso` en el cuerpo del 302 no prueba nada; lo que cubre el escenario es que no hay cambio ni CATALOGO_EDITADO.
- `catalogo/0003`: `AddField` sin `db_default`. Mientras Vercel migra Neon, el despliegue anterior no manda la columna: crear una institución en esa ventana falla. Con `db_default=False` no pasaría.
- `notas/models.py`, `CompetenciaPeriodo.__str__`: hace tres consultas. Si llega a un panel o a una lista, usar `select_related`.

### Parte B: servicios de `notas`, actividad y demo

- `notas/servicios.py`, `marcar_todo_sin_registro`: no bloquea la sección. Si una docente demo guarda mientras corre la carga, choca con `uq_competencia_periodo` y se revierte toda la carga (se vuelve a correr).
- `notas/tests/test_servicios_guardar.py`, obligatorias del bimestre 4: revisa `cambios.agregadas`, pero no el `detalle` de COMPETENCIAS_MARCADAS («las obligatorias cuentan como agregadas»).
- Tarea 2.4, «competencia de otra institución»: el catálogo es global; se probó con Castellano (no se trabaja) y con un id que no existe. El aislamiento por institución lo cubre `test_un_area_de_otra_institucion_no_se_marca`.

### Parte C: vistas, rutas y permisos

- `notas/tests/test_vistas_acceso.py`, «Portada sin cambios»: supone que Notas es la segunda tarjeta; buscar el `<article>` con `id="ins-notas"`.

### A2 (Codex, adversarial)

- Corregido (alto): una competencia reactivada con la pantalla abierta perdía su marca al guardar. Ahora el POST lleva el universo que se mostró y, si cambió, responde 400 sin guardar (escenario «Catálogo cambiado al guardar», design D5).
- Deuda (medio), `static/js/competencias.js`, `pendiente()`: con B1={X,Y} y B4={Y} guardados, quitar X del B1 la vuelve obligatoria en el B4; `base()` y `borrador()` la suman, `cambios()` da 0 y «Guardar» queda deshabilitado, aunque X no tiene marca en ningún periodo del año. El servidor la agrega en el próximo guardado del B4. Arreglo propuesto: `pendiente()` verdadero si falta una obligatoria en `guardado`.
- Corregido (medio), `catalogo/0003`: `db_default=False` en el campo y en la migración (es el Minor de la parte A). Un INSERT sin la columna, como el de `main`, la deja en `False`.
