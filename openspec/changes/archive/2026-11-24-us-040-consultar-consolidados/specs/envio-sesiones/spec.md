## MODIFIED Requirements

### Requirement: Solo el rol Docente
La pantalla Sesiones y el envío MUST ser solo del rol Docente, tenga o no sección asignada. La dirección y el Administrador van a su pantalla de inicio y una visita sin sesión, al ingreso; ninguno de ellos guarda una sesión. Desde US-040, una sesión enviada queda visible para la dirección de su institución, compartida o no (RN-019), en Consolidados (spec `consolidados-direccion`).

#### Scenario: Docente sin sección
- **WHEN** una docente sin sección en el año ABIERTO abre Sesiones y envía una sesión válida
- **THEN** la sesión se guarda

#### Scenario: Otro rol
- **WHEN** la dirección o el Administrador abren Sesiones o envían el formulario
- **THEN** el sistema los lleva a su pantalla de inicio y no guarda ninguna sesión ni archivo

#### Scenario: Sin sesión
- **WHEN** una visita sin sesión abre Sesiones o envía el formulario
- **THEN** el sistema la lleva al ingreso y no guarda nada; si el envío venía del popup, la lleva con la página completa

#### Scenario: Visible para la dirección
- **WHEN** una docente envía una sesión de 2.º grado sin compartirla en el repositorio
- **THEN** la dirección de su institución la ve en la pestaña Sesiones de las secciones de 2.º grado de esa docente
