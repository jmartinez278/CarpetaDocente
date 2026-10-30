# Spec Delta

## MODIFIED Requirements

### Requirement: Portada del docente
La portada del docente SHALL saludar al docente por su nombre y mostrar las tarjetas de las tres dimensiones en este orden: Sesiones, Notas y Asistencia, cada una con su título corto, su subtítulo formal y su miniatura esquemática, sin ningún dato que pueda leerse como un registro del docente. Desde US-005, bajo el saludo y fuera del encabezado principal, una línea SHALL mostrar las secciones del docente en el año escolar ABIERTO de su institución, con el formato "2.º grado, sección A" (º ordinal), separadas por " · " y ordenadas por grado y nombre. Sin sección en el año ABIERTO, la línea dice "Tu sección aparecerá cuando el administrador la asigne." Las tarjetas no cambian. Desde US-006, si la docente tiene una sola sección en el año ABIERTO, junto a esa línea (que sigue siendo texto, sin estilo de enlace) va el enlace "Ver estudiantes" con la flecha de acción, de 44 px de alto como mínimo, que abre la lista de la sección; y mientras la sección no tenga estudiantes, debajo aparece el aviso "Tu sección aún no tiene estudiantes" / "Agrégalos para poder tomar asistencia", que desaparece en cuanto la sección tiene estudiantes, también sin recargar la página. Con varias secciones, o sin sección, no hay enlace ni aviso. Desde US-030, el saludo depende de la hora de Lima: "Buenos días" hasta las 11:59, "Buenas tardes" de 12:00 a 18:59 y "Buenas noches" desde las 19:00; y la línea de la sección empieza con la fecha de hoy ("Miércoles 28 de octubre · 2.º grado, sección A"). Con una sola sección, en un día de lunes a viernes, con estudiantes activos y la jornada de hoy sin completar, la tarjeta Asistencia lleva la píldora "Hoy: pendiente", sin enlace propio y descrita en el enlace de la tarjeta; con la jornada completa, el fin de semana o sin estudiantes, no está.

#### Scenario: Portada al entrar
- **WHEN** un docente entra al sistema a las 9:00 de Lima
- **THEN** ve "Buenos días," con su nombre y las tres tarjetas en orden, con sus subtítulos "Planificación de sesiones de aprendizaje", "Registro y control de notas" y "Control de asistencia"

#### Scenario: Saludo según la hora
- **WHEN** el docente abre la portada a las 12:00 y luego a las 19:00 de Lima
- **THEN** ve "Buenas tardes," y luego "Buenas noches,"

#### Scenario: Docente con una sección
- **WHEN** una docente con "2.º grado, sección A" en el año ABIERTO entra al sistema un miércoles 28 de octubre
- **THEN** bajo el saludo ve "Miércoles 28 de octubre · 2.º grado, sección A", y esa línea no forma parte del encabezado principal

#### Scenario: Docente con varias secciones
- **WHEN** una docente tiene "3.º grado, sección B" y "2.º grado, sección A" en el año ABIERTO
- **THEN** ve, después de la fecha, "2.º grado, sección A · 3.º grado, sección B"

#### Scenario: Docente sin sección
- **WHEN** una docente sin sección en el año ABIERTO entra al sistema
- **THEN** bajo el saludo ve, después de la fecha, "Tu sección aparecerá cuando el administrador la asigne."

#### Scenario: Sección de un año cerrado
- **WHEN** la única sección de la docente pertenece a un año CERRADO
- **THEN** ve, después de la fecha, "Tu sección aparecerá cuando el administrador la asigne."

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

#### Scenario: Asistencia de hoy pendiente
- **WHEN** un miércoles la sección de la docente tiene 25 estudiantes activos y solo 18 marcados hoy, o ninguno
- **THEN** la tarjeta Asistencia muestra "Hoy: pendiente", que no es un enlace aparte, y el lector de pantalla lo lee con el enlace de la tarjeta

#### Scenario: Asistencia de hoy completa
- **WHEN** los 25 estudiantes activos tienen estado hoy
- **THEN** la tarjeta Asistencia no muestra "Hoy: pendiente"

#### Scenario: Fin de semana o sección sin estudiantes
- **WHEN** es sábado, o la sección no tiene estudiantes
- **THEN** la tarjeta Asistencia no muestra "Hoy: pendiente"

### Requirement: Disponibilidad de cada dimensión
Cada dimensión SHALL tener una bandera de disponibilidad que activa la historia que construye su pantalla. Una dimensión no disponible se muestra como "Próximamente" y nunca se oculta; una disponible enlaza a su pantalla. Ninguna tarjeta MUST enlazar a una página que no existe. Al cerrar US-001, las tres están en "Próximamente". Desde US-030, Asistencia está disponible y su tarjeta enlaza a la asistencia de hoy de la sección, con la misma regla que "Ver estudiantes": solo si la docente tiene una sola sección en el año ABIERTO. Sin esa sección única, la tarjeta Asistencia se muestra como "Próximamente".

#### Scenario: Tres dimensiones en "Próximamente"
- **WHEN** un docente abre la portada al cerrar US-001
- **THEN** las tres tarjetas muestran la insignia "Próximamente" y ninguna contiene un enlace

#### Scenario: Toque en una tarjeta "Próximamente"
- **WHEN** el docente toca una tarjeta "Próximamente"
- **THEN** la página no cambia de dirección y la tarjeta muestra "Llegará en una próxima versión." durante unos segundos, en un aviso que anuncia el lector de pantalla y que no mueve el resto de la tarjeta

#### Scenario: Dimensión activada por su historia
- **WHEN** la historia de una dimensión activa su bandera
- **THEN** su tarjeta pasa a disponible, con el verbo de su acción ("Ver sesiones", "Registrar notas" o "Registrar asistencia") y un enlace a su pantalla, y toda la tarjeta responde al toque

#### Scenario: Bandera activa sin pantalla
- **WHEN** se activa la bandera de una dimensión cuya pantalla no existe
- **THEN** las pruebas automáticas fallan antes de que el cambio pueda fusionarse

#### Scenario: Asistencia con una sección
- **WHEN** una docente con una sola sección en el año ABIERTO abre la portada
- **THEN** la tarjeta Asistencia dice "Registrar asistencia" y lleva a la asistencia de hoy de esa sección; Sesiones y Notas siguen en "Próximamente"

#### Scenario: Asistencia sin sección única
- **WHEN** una docente sin sección, o con dos, abre la portada
- **THEN** la tarjeta Asistencia se muestra como "Próximamente" y no contiene un enlace
