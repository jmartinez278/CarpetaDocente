# Spec Delta

## MODIFIED Requirements

### Requirement: Acceso a las competencias de su sección
La pantalla de competencias de una sección SHALL abrirse solo para la docente de esa sección en el año ABIERTO. La sección de otra docente, inexistente o de un año CERRADO responde 403 con el mensaje de «sin permiso» y deja una entrada de intento (spec `acceso-secciones`); otro rol va a su pantalla de inicio y una visita sin sesión va al ingreso. Las mismas reglas valen para cada guardado; un guardado con 403 lleva la pestaña a la página de «sin permiso», no a «Tu sesión venció». Desde US-020 se llega desde la hoja de notas, con el botón «Competencias».

#### Scenario: Sección de otra docente
- **WHEN** una docente abre o guarda las competencias de una sección que no es suya
- **THEN** recibe 403 y no se guarda nada

#### Scenario: Sección de un año cerrado
- **WHEN** la docente abre o guarda las competencias de su sección de un año CERRADO
- **THEN** recibe 403 y no se guarda nada

#### Scenario: Otro rol
- **WHEN** un usuario de la dirección abre las competencias de una sección
- **THEN** llega a su propia pantalla de inicio

#### Scenario: Sin sesión
- **WHEN** alguien sin sesión abre las competencias de una sección
- **THEN** llega al ingreso y no ve ninguna competencia

#### Scenario: Portada sin cambios
- **WHEN** la docente abre su portada
- **THEN** no hay un enlace directo a las competencias: la tarjeta Notas lleva a la hoja de notas, y desde ella se llega a las competencias

#### Scenario: Desde la hoja de notas
- **WHEN** la tutora, en la hoja de notas del bimestre 2, pulsa «Competencias»
- **THEN** llega a las competencias del bimestre 2
