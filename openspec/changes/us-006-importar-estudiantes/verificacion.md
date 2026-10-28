# Verificación: US-006

(Tabla escenario → prueba y DoD 1 a 9: tarea 3.2.)

## Minor para la descripción del PR

Grupo 1 (revisión del grupo, sin DESIGN.md):

- `importar_lista` y `agregar_estudiante` no comparten bloqueo: un agregar concurrente entre el `exists()` y el `bulk_create` podría dar un `IntegrityError` sin capturar. Ventana mínima (una docente por sección); sin prueba de carrera.
- `editar_estudiante` deja la instancia en memoria con los valores rechazados si falla: la vista del grupo 2 debe volver a cargar el estudiante.
- `_guardar_estudiante` traduce cualquier `IntegrityError` a "Este estudiante ya está en la lista" (engañoso si la sección se borra en paralelo; muy improbable).
- Condicional anidado en `_errores_de_filas` poco legible; `_clave_orden` repetida en el desempate de `estudiantes_ordenados`.
- Falta una prueba del máximo de 120 caracteres al editar (solo al agregar).
- El mensaje "Este estudiante ya está en la lista" está en `servicios.py` y en `Estudiante.Meta` (el ciclo de importación impide compartirlo).
