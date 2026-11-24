## MODIFIED Requirements

### Requirement: Listas solo del rol Docente
«Mis sesiones» y «Repositorio» MUST ser solo del rol Docente, tenga o no sección asignada. La dirección y el Administrador van a su pantalla de inicio y una visita sin sesión, al ingreso. Desde US-040, la dirección ve las sesiones de su institución (RN-019) solo desde la pestaña Sesiones del detalle de una sección (spec `consolidados-direccion`), no en estas listas.

#### Scenario: Docente sin sección
- **WHEN** una docente sin sección en el año ABIERTO abre el repositorio
- **THEN** ve las sesiones compartidas de su institución

#### Scenario: Otro rol o sin sesión
- **WHEN** la dirección, el Administrador o una visita sin sesión piden «Mis sesiones» o el repositorio, con o sin filtros
- **THEN** el sistema los lleva a su inicio o al ingreso y no muestra ninguna sesión
