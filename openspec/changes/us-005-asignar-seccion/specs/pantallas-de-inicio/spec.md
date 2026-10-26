# Spec Delta

## MODIFIED Requirements

### Requirement: Portada del docente
La portada del docente SHALL saludar al docente por su nombre y mostrar las tarjetas de las tres dimensiones en este orden: Sesiones, Notas y Asistencia, cada una con su título corto, su subtítulo formal y su miniatura esquemática, sin ningún dato que pueda leerse como un registro del docente. Desde US-005, bajo el saludo y fuera del encabezado principal, una línea SHALL mostrar las secciones del docente en el año escolar ABIERTO de su institución, con el formato "2.º grado, sección A" (º ordinal), separadas por " · " y ordenadas por grado y nombre. Sin sección en el año ABIERTO, la línea dice "Tu sección aparecerá cuando el administrador la asigne." Las tarjetas no cambian.

#### Scenario: Portada al entrar
- **WHEN** un docente entra al sistema
- **THEN** ve "Hola," con su nombre y las tres tarjetas en orden, con sus subtítulos "Planificación de sesiones de aprendizaje", "Registro y control de notas" y "Control de asistencia"

#### Scenario: Docente con una sección
- **WHEN** una docente con "2.º grado, sección A" en el año ABIERTO entra al sistema
- **THEN** bajo el saludo ve "2.º grado, sección A", y esa línea no forma parte del encabezado principal

#### Scenario: Docente con varias secciones
- **WHEN** una docente tiene "3.º grado, sección B" y "2.º grado, sección A" en el año ABIERTO
- **THEN** ve "2.º grado, sección A · 3.º grado, sección B"

#### Scenario: Docente sin sección
- **WHEN** una docente sin sección en el año ABIERTO entra al sistema
- **THEN** bajo el saludo ve "Tu sección aparecerá cuando el administrador la asigne."

#### Scenario: Sección de un año cerrado
- **WHEN** la única sección de la docente pertenece a un año CERRADO
- **THEN** ve "Tu sección aparecerá cuando el administrador la asigne."
