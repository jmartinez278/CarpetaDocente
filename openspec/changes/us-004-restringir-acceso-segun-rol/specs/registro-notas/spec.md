# Spec Delta

## MODIFIED Requirements

### Requirement: Acceso a la hoja de notas
La hoja de notas de una sección SHALL abrirse solo para la docente de esa sección en el año ABIERTO. La sección de otra docente, inexistente o de un año CERRADO responde 403 con el mensaje de «sin permiso» y deja una entrada de intento (spec `acceso-secciones`); otro rol va a su pantalla de inicio y una visita sin sesión va al ingreso. Las mismas reglas valen para cada guardado, que además no guarda nada; un guardado con 403 lleva la pestaña a la página de «sin permiso», no a «Tu sesión venció», y no deja borrador de esa sección. Las áreas que no son de la tutora siguen en gris, sin 403.

#### Scenario: Sección de otra docente
- **WHEN** una docente abre o guarda la hoja de notas de una sección que no es suya
- **THEN** recibe 403 y no se guarda ninguna nota

#### Scenario: Sección de un año cerrado
- **WHEN** la docente abre o guarda la hoja de notas de su sección de un año CERRADO
- **THEN** recibe 403 y no se guarda ninguna nota

#### Scenario: Otro rol
- **WHEN** un usuario de la dirección abre la hoja de notas de una sección
- **THEN** llega a su propia pantalla de inicio

#### Scenario: Sin sesión
- **WHEN** alguien sin sesión abre la hoja de notas de una sección
- **THEN** llega al ingreso y no ve ninguna nota
