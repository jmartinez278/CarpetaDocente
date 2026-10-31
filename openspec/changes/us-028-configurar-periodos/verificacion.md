# Verificación: US-028 – Configurar los periodos del año escolar

## Minor del revisor

### Parte 1A: `btree_gist`, `Periodo` y migración

- `test_modelos_periodo.py`: `test_la_base_crea_la_extension_btree_gist` ya no puede fallar en la base de pruebas, porque `institucion/0005` crea la extensión antes. Sirvió para la comprobación previa al modelo (tarea 1.1); en Neon, la prueba es la vista previa de Vercel (tarea 1.3).
- `test_modelos_periodo.py`: el cruce se prueba con `SET CONSTRAINTS … IMMEDIATE` y no al confirmar (pytest-django revierte la transacción). Que no estalle en el `COMMIT` lo cubren las tareas 2.2 y 2.3.
- `models.py`, `Periodo.__str__`: hace una consulta por periodo para leer `anio_escolar`. Si el inline lo muestra por fila, usar `select_related`.
