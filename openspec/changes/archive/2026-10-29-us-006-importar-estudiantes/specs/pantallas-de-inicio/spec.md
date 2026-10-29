# Spec Delta

## MODIFIED Requirements

### Requirement: Portada del docente
La portada del docente SHALL saludar al docente por su nombre y mostrar las tarjetas de las tres dimensiones en este orden: Sesiones, Notas y Asistencia, cada una con su título corto, su subtítulo formal y su miniatura esquemática, sin ningún dato que pueda leerse como un registro del docente. Desde US-005, bajo el saludo y fuera del encabezado principal, una línea SHALL mostrar las secciones del docente en el año escolar ABIERTO de su institución, con el formato "2.º grado, sección A" (º ordinal), separadas por " · " y ordenadas por grado y nombre. Sin sección en el año ABIERTO, la línea dice "Tu sección aparecerá cuando el administrador la asigne." Las tarjetas no cambian. Desde US-006, si la docente tiene una sola sección en el año ABIERTO, junto a esa línea (que sigue siendo texto, sin estilo de enlace) va el enlace "Ver estudiantes" con la flecha de acción, de 44 px de alto como mínimo, que abre la lista de la sección; y mientras la sección no tenga estudiantes, debajo aparece el aviso "Tu sección aún no tiene estudiantes" / "Agrégalos para poder tomar asistencia", que desaparece en cuanto la sección tiene estudiantes, también sin recargar la página. Con varias secciones, o sin sección, no hay enlace ni aviso.

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

#### Scenario: Enlace a la lista con una sección
- **WHEN** una docente con una sola sección en el año ABIERTO entra al sistema
- **THEN** junto a "2.º grado, sección A" ve "Ver estudiantes", que abre la lista de esa sección

#### Scenario: Sin enlace con varias secciones
- **WHEN** una docente tiene dos secciones en el año ABIERTO
- **THEN** no ve "Ver estudiantes" ni el aviso de la sección sin estudiantes

#### Scenario: Sin enlace sin sección
- **WHEN** una docente sin sección en el año ABIERTO entra al sistema
- **THEN** no ve "Ver estudiantes" ni el aviso de la sección sin estudiantes

#### Scenario: Sección sin estudiantes
- **WHEN** la única sección de la docente no tiene estudiantes
- **THEN** bajo la línea de la sección ve el aviso "Tu sección aún no tiene estudiantes" / "Agrégalos para poder tomar asistencia"

#### Scenario: El aviso desaparece al cargar la lista
- **WHEN** la docente importa o agrega estudiantes desde el diálogo y lo cierra
- **THEN** la portada ya no muestra el aviso, sin haberse recargado
