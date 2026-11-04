# Spec Delta

## MODIFIED Requirements

### Requirement: Acceso solo a la asistencia de su sección
La asistencia de una sección SHALL abrirse solo para la docente de esa sección en el año ABIERTO. La sección de otra docente, inexistente o de un año CERRADO responde 403 con el mensaje de «sin permiso» y deja una entrada de intento (spec `acceso-secciones`); otro rol va a su pantalla de inicio y una visita sin sesión va al ingreso, sin mostrar la lista. Las mismas reglas valen para cada guardado. Un guardado con 403 lleva la pestaña a la página de «sin permiso» sin guardar marcas pendientes en el dispositivo.

#### Scenario: Sección de otra docente
- **WHEN** una docente abre o guarda la asistencia de una sección que no es suya
- **THEN** recibe 403 y no se guarda nada

#### Scenario: Sección de un año cerrado
- **WHEN** la docente abre la asistencia de su sección de un año CERRADO
- **THEN** recibe 403

#### Scenario: Otro rol
- **WHEN** un usuario de la dirección abre la asistencia de una sección
- **THEN** llega a su propia pantalla de inicio

#### Scenario: Estudiante de otra sección
- **WHEN** llega el guardado de un estudiante, con el estudiante en la ruta, que no es de la sección
- **THEN** no se guarda nada y la respuesta es 403

#### Scenario: Estudiante de la sección que ya no está activo
- **WHEN** llega el guardado de un estudiante de la sección que está trasladado o retirado
- **THEN** no se guarda nada y la respuesta es "página no encontrada", sin entrada de intento

#### Scenario: Restantes con un id ajeno
- **WHEN** «Marcar los restantes» envía un id que no es activo de la sección
- **THEN** no se guarda ninguno y la respuesta es "página no encontrada", sin entrada de intento
