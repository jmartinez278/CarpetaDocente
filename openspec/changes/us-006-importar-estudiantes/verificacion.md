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

Grupo 2, parte A (revisión de la parte, con las secciones de DESIGN.md que usa):

- Mientras no existan las partes B y C, "Agregar uno por uno" y "Pegar lista" abren rutas con `PendienteView` (404): no hacen nada al pulsarlas. Temporal: `PendienteView` (en `institucion/views.py` y `urls.py`) la reemplazan las partes B y C con sus vistas reales, y el catálogo de rutas suma entonces las cinco rutas restantes.
- CSS adelantado para B y C: `.mensaje--exito` y `.campo-ayuda` (aún sin uso).
- Si la petición del parcial falla (500 o red), HTMX no muestra nada en el diálogo.
- Con el diálogo abierto y la sesión vencida, la entrada de historial extra queda al ir a `/ingresar/` (inocuo: tras ingresar va a `/docente/`).
- El aviso de la portada (`role="status"`) cambia por `hx-swap-oob` mientras el diálogo deja la portada inerte: el lector de pantalla probablemente no lo anuncie hasta cerrar el diálogo.
- Para B y C: los POST del diálogo necesitan el token CSRF (`{% csrf_token %}` en cada formulario).

Grupo 2, parte B (revisión de la parte, con Mensaje, Campo de texto y Movimiento de DESIGN.md):

- En Revisar lista, el cuadro (`aria-invalid="true"`) no apunta a la lista de errores con `aria-describedby`: el lector los oye por el `role="alert"` y el foco en "Revisar lista", pero no al volver al cuadro.
- Los errores van arriba del cuadro y sin ícono por línea (como el boceto), no debajo del campo como pide Campo de texto: el mensaje de error de la vista sí lleva ícono.
- El aviso "N estudiantes importados" (`role="status"`) llega dentro del contenido nuevo; el foco va al título, así que el lector probablemente no lo anuncie solo.
- "Importar" no se desactiva mientras envía: un doble clic podría mandar un segundo POST, que encuentra la sección con estudiantes y muestra "Tu sección ya tiene estudiantes" en lugar del aviso de éxito (no se guarda nada de más).
- Las e2e de 2.4 y 2.5 se escribieron después de las pruebas de vistas ya en verde y pasaron al primer intento: no se las vio fallar.

