## MODIFIED Requirements

### Requirement: Portada del docente
La portada del docente SHALL saludar al docente por su nombre y mostrar las tarjetas de las tres dimensiones en este orden, que es también el orden de lectura: Asistencia, Sesiones y Notas, cada una con su título corto, su frase de acción y su miniatura esquemática, sin el subtítulo formal de la dimensión y sin ningún dato que pueda leerse como un registro del docente. Las frases son "Marca la asistencia de cada día.", "Envía tu sesión a la dirección y compártela con tus colegas." y "Registra tus notas por competencia para el SIAGIE.". En la computadora, Asistencia es la tarjeta principal y Sesiones y Notas van a su lado; en el celular, las tres se apilan en el mismo orden, sin carrusel. Desde US-005, bajo el saludo y fuera del encabezado principal, una línea SHALL mostrar las secciones del docente en el año escolar ABIERTO de su institución, con el formato "2.º grado, sección A" (º ordinal), separadas por " · " y ordenadas por grado y nombre. Sin sección en el año ABIERTO, la línea dice "Tu sección aparecerá cuando el administrador la asigne." Las tarjetas no cambian. Desde US-006, si la docente tiene una sola sección en el año ABIERTO, junto a esa línea (que sigue siendo texto, sin estilo de enlace) va el enlace "Ver estudiantes" con la flecha de acción, de 44 px de alto como mínimo, que abre la lista de la sección; y mientras la sección no tenga estudiantes, debajo aparece el aviso "Tu sección aún no tiene estudiantes" / "Agrégalos para poder tomar asistencia", que desaparece en cuanto la sección tiene estudiantes, también sin recargar la página. Con varias secciones, o sin sección, no hay enlace ni aviso. Desde US-030, el saludo depende de la hora de Lima: "Buenos días" hasta las 11:59, "Buenas tardes" de 12:00 a 18:59 y "Buenas noches" desde las 19:00; y la línea de la sección empieza con la fecha de hoy ("Miércoles 28 de octubre · 2.º grado, sección A"). Con una sola sección, en un día de lunes a viernes, con estudiantes activos y la jornada de hoy sin completar, la tarjeta Asistencia lleva la píldora "Hoy: pendiente", sin enlace propio y descrita en el enlace de la tarjeta; con la jornada completa, el fin de semana o sin estudiantes, no está.

#### Scenario: Portada al entrar
- **WHEN** un docente entra al sistema a las 9:00 de Lima
- **THEN** ve "Buenos días," con su nombre y las tres tarjetas en el orden Asistencia, Sesiones y Notas, con sus frases "Marca la asistencia de cada día.", "Envía tu sesión a la dirección y compártela con tus colegas." y "Registra tus notas por competencia para el SIAGIE.", y ninguna muestra "Planificación de sesiones de aprendizaje", "Registro y control de notas" ni "Control de asistencia"

#### Scenario: Orden de lectura
- **WHEN** el lector de pantalla o el teclado recorren la portada
- **THEN** llegan a las tarjetas en el orden Asistencia, Sesiones y Notas, el mismo que se ve

#### Scenario: Tarjetas en el celular
- **WHEN** la portada se abre a 360 px
- **THEN** las tres tarjetas se ven apiladas en el orden Asistencia, Sesiones y Notas, sin chips, sin puntos y sin desplazamiento horizontal

#### Scenario: Tarjetas en la computadora
- **WHEN** la portada se abre a 1280 px
- **THEN** Asistencia ocupa la columna principal y Sesiones y Notas van a su lado, una sobre otra

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

### Requirement: Accesibilidad en ambos temas
Cada pantalla nueva MUST pasar la revisión automática de accesibilidad (WCAG 2.1, niveles A y AA) sin infracciones críticas ni graves, en tema claro y en tema oscuro, a 360 px y a 1280 px (RNF-008, DoD 7). El contraste de texto queda incluido en la revisión.

#### Scenario: Revisión de cada pantalla
- **WHEN** se ejecuta la revisión automática sobre el inicio de sesión con el marco del rebrand (normal, con error, con campos vacíos, «Ingresando…» y con el aviso de inactividad), la portada del docente con el marco del rebrand (con una sección, con varias, sin sección, con la sección sin estudiantes, con «Hoy: pendiente», con una tarjeta «Próximamente» mostrando su aviso, con el menú de la cuenta abierto y con el diálogo de Estudiantes abierto), el inicio de la dirección (con el menú cerrado y abierto) y «sin permiso» (con el ☰ y el menú de la cuenta cerrados, con el ☰ abierto y con el menú de la cuenta abierto), en ambos temas y en ambos anchos
- **THEN** no hay infracciones críticas ni graves

### Requirement: Sin desplazamiento horizontal
Ninguna pantalla nueva SHALL desplazarse en horizontal entre 320 px y 1280 px de ancho, en ningún tema (RNF-005).

#### Scenario: Pantallas a 320 px
- **WHEN** cada pantalla nueva se abre a 320 px y a 360 px, en ambos temas
- **THEN** el ancho del documento no supera el de la ventana

#### Scenario: Portada sin desplazamiento interno
- **WHEN** la portada se abre a 320 px y a 360 px, en ambos temas, con «Hoy: pendiente» y con el aviso de la sección sin estudiantes
- **THEN** ni el documento ni ningún contenedor de las tarjetas se desplaza en horizontal

## REMOVED Requirements

### Requirement: Carrusel de dimensiones en el celular
**Reason**: DESIGN.md 1.1 (Layout «Portada») apila las tarjetas hasta 899 px y compacta las secundarias hasta 699 px; con tres tarjetas apiladas, el carrusel, sus chips y sus puntos ya no hacen falta (decisiones.md de `rebrand-portada`, punto 9).
**Migration**: En el celular las tarjetas se leen en vertical, en el orden Asistencia, Sesiones y Notas (requisito «Portada del docente», escenario «Tarjetas en el celular»). Los enlaces `#c-<clave>` siguen llevando a cada tarjeta; `data-carrusel` y los chips desaparecen.
