# Verificación: US-029 – Marcar las competencias desarrolladas en el periodo

## Minor para la descripción del PR

### Parte A: `CompetenciaPeriodo`, `a_cargo_docente_curso` y migraciones

- `catalogo/tests/test_admin.py`, `test_otro_rol_no_cambia_a_cargo_del_docente_de_curso`: buscar `a_cargo_docente_curso` en el cuerpo del 302 no prueba nada; lo que cubre el escenario es que no hay cambio ni CATALOGO_EDITADO.
- `catalogo/0003`: `AddField` sin `db_default`. Mientras Vercel migra Neon, el despliegue anterior no manda la columna: crear una institución en esa ventana falla. Con `db_default=False` no pasaría.
- `notas/models.py`, `CompetenciaPeriodo.__str__`: hace tres consultas. Si llega a un panel o a una lista, usar `select_related`.
