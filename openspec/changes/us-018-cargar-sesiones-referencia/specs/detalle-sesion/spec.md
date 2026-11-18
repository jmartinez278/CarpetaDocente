# Spec Delta

## MODIFIED Requirements

### Requirement: Quién ve una sesión
La página de una sesión, su descarga y su vista MUST estar disponibles solo para su autora y, si está compartida o es material de referencia, para cualquier Docente de la misma institución. En cualquier otro caso (eliminada, inexistente, ajena no compartida o de otra institución) el sistema SHALL mostrar «La sesión ya no está disponible» con «Volver a Sesiones», con la misma respuesta en todos, sin revelar cuál es el caso ni ningún dato de la sesión.

#### Scenario: Compartida de una colega
- **WHEN** una docente abre la página de una sesión compartida por una colega de su institución
- **THEN** ve la página de la sesión

#### Scenario: Propia sin compartir
- **WHEN** la autora abre la página de su sesión no compartida
- **THEN** ve la página de la sesión

#### Scenario: Ajena sin compartir
- **WHEN** una docente abre la dirección de una sesión no compartida de una colega
- **THEN** ve «La sesión ya no está disponible», sin el título ni la autora, igual que con una dirección que nunca existió

#### Scenario: Otra institución
- **WHEN** una docente abre la dirección de una sesión compartida en otra institución
- **THEN** ve «La sesión ya no está disponible»

#### Scenario: Dejó de compartirse
- **WHEN** una colega tenía abierta la lista del repositorio, la autora deja de compartir la sesión y la colega toca su tarjeta
- **THEN** la colega ve «La sesión ya no está disponible»

#### Scenario: Otro rol o sin sesión
- **WHEN** la dirección, el Administrador o una visita sin sesión abren la página, la descarga o la vista de una sesión
- **THEN** el sistema los lleva a su inicio o al ingreso y no entrega la página ni el archivo

#### Scenario: Material de referencia
- **WHEN** una docente abre la página de una sesión de referencia de su institución, o la de otra institución
- **THEN** ve la página y puede descargarla en el primer caso, y «La sesión ya no está disponible» en el segundo

## ADDED Requirements

### Requirement: Página del material de referencia
La página de una sesión de referencia SHALL mostrar lo mismo que la de una sesión ajena, con estos cambios: el chip de grado con su rango, el chip «Material de referencia» en lugar de «Compartida», la fecha como «Fecha de carga», sin la fila «Autora», y la tarjeta «Material de referencia» con la fuente y el permiso de uso. MUST NOT mostrar la tarjeta «Tu sesión» ni acciones de autora.

#### Scenario: Fuente y permiso
- **WHEN** una docente abre una sesión de referencia de 3.º a 5.º con fuente «Equipo del proyecto» y permiso «Elaborada por el equipo; uso libre en la I.E.»
- **THEN** ve «3.º–5.º grado», el área, «Material de referencia», «Fecha de carga», y en la tarjeta «Material de referencia» la fuente y el permiso de uso, como texto

#### Scenario: Sin acciones
- **WHEN** una docente abre una sesión de referencia
- **THEN** ve «Descargar» (y «Ver» si es PDF), las migas al «Repositorio», y no ve «Tu sesión», «Compartir», «Dejar de compartir» ni «Eliminar»

### Requirement: Una docente no cambia el material de referencia
Si una docente envía, con una petición armada a mano, eliminar, compartir o dejar de compartir una sesión de referencia de su institución, el sistema SHALL responder «Solo el autor puede eliminar esta sesión», dejar INTENTO_SIN_PERMISO y conservar la sesión y su archivo sin cambios.

#### Scenario: Eliminar el material de referencia
- **WHEN** una docente envía la petición de eliminar una sesión de referencia de su institución
- **THEN** ve «Solo el autor puede eliminar esta sesión», queda una entrada INTENTO_SIN_PERMISO y la sesión sigue en el repositorio con su archivo

#### Scenario: Dejar de compartir el material de referencia
- **WHEN** una docente envía la petición de dejar de compartir una sesión de referencia
- **THEN** la sesión sigue en el repositorio y queda una entrada INTENTO_SIN_PERMISO
