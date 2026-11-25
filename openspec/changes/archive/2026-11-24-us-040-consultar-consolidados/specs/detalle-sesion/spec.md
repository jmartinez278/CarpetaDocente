## ADDED Requirements

### Requirement: Sesión abierta por la dirección
La dirección SHALL abrir una sesión desde la pestaña Sesiones del detalle de una sección (spec `consolidados-direccion`) en su propia página, con el ☰ de la dirección: los mismos datos que la página de la docente (tipo, título, chips, «Compartida» si lo está, autora, fecha de envío, formato, tamaño, propósito y vista previa del texto), «Descargar» y, si es PDF, «Ver», con el mismo permiso que la página. Sin migas hacia Sesiones ni acciones de la autora (compartir, dejar de compartir, eliminar) ni el total de colegas que la vieron. La descarga y la vista dejan SESION_DESCARGADA como las de la docente. Una sesión que la dirección no puede ver muestra «La sesión ya no está disponible» con «Volver a Consolidados».

#### Scenario: Abrir y descargar desde Consolidados
- **WHEN** la dirección toca la tarjeta de una sesión no compartida de la tutora de 2.º A y luego «Descargar»
- **THEN** ve la página de la sesión, sin «Eliminar» ni «Compartir», y recibe el archivo original con su nombre

#### Scenario: Sesión de otra institución
- **WHEN** la dirección abre la dirección de una sesión de otra institución
- **THEN** ve «La sesión ya no está disponible» con «Volver a Consolidados» y no recibe el archivo

## MODIFIED Requirements

### Requirement: Quién ve una sesión
La página de una sesión, su descarga y su vista MUST estar disponibles solo para su autora y, si está compartida o es material de referencia, para cualquier Docente de la misma institución. Desde US-040, la dirección MUST ver, en su propia página (requisito «Sesión abierta por la dirección»), cualquier sesión enviada por una docente de su institución, compartida o no, y no el material de referencia (RN-019). En cualquier otro caso (eliminada, inexistente, ajena no compartida o de otra institución) el sistema SHALL mostrar «La sesión ya no está disponible», con «Volver a Sesiones» para la docente y «Volver a Consolidados» para la dirección, con la misma respuesta en todos, sin revelar cuál es el caso ni ningún dato de la sesión.

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
- **WHEN** la dirección, el Administrador o una visita sin sesión abren la página, la descarga o la vista de una sesión en las rutas de la docente
- **THEN** el sistema los lleva a su inicio o al ingreso y no entrega la página ni el archivo

#### Scenario: Material de referencia
- **WHEN** una docente abre la página de una sesión de referencia de su institución, o la de otra institución
- **THEN** ve la página y puede descargarla en el primer caso, y «La sesión ya no está disponible» en el segundo

#### Scenario: La dirección y una sesión no compartida
- **WHEN** la dirección abre en su página una sesión no compartida de una docente de su institución
- **THEN** ve la página y puede descargarla

#### Scenario: La dirección y el material de referencia
- **WHEN** la dirección abre en su página una sesión de referencia
- **THEN** ve «La sesión ya no está disponible»

#### Scenario: Docente en la página de la dirección
- **WHEN** una docente, el Administrador o una visita sin sesión abren la página, la descarga o la vista de una sesión en las rutas de la dirección
- **THEN** el sistema los lleva a su inicio o al ingreso y no entrega la página ni el archivo

### Requirement: Colegas que la vieron
El sistema SHALL contar las personas distintas que abrieron la página de una sesión, sin contar a su autora ni a la dirección, y mostrar el total solo a la autora, en la página y en «Mis sesiones» («La vieron 3 colegas», «La vio 1 colega»); con 0 no se muestra. MUST NOT mostrarse quiénes fueron, ni las descargas.

#### Scenario: Primera visita de una colega
- **WHEN** una colega abre por primera vez la página de una sesión compartida
- **THEN** el total de esa sesión sube en 1

#### Scenario: La misma colega otra vez
- **WHEN** esa colega vuelve a abrir la página, hoy u otro día
- **THEN** el total no cambia

#### Scenario: La autora
- **WHEN** la autora abre la página de su sesión
- **THEN** el total no cambia y, si es 3, ve «La vieron 3 colegas», sin nombres

#### Scenario: Nadie la vio
- **WHEN** ninguna colega ha abierto la sesión
- **THEN** la autora no ve ningún texto de vistas, ni en la página ni en «Mis sesiones»

#### Scenario: Una colega no ve el total
- **WHEN** una colega abre la página de una sesión ajena
- **THEN** no ve cuántas personas la vieron

#### Scenario: La dirección no cuenta
- **WHEN** la dirección abre la página de una sesión
- **THEN** el total de esa sesión no cambia
