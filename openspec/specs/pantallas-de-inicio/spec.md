# pantallas-de-inicio Specification

## Purpose
Define lo que ve cada rol al entrar: la pantalla de inicio de sesión, la portada del docente con las tres dimensiones y el inicio de la dirección, sobre el marco visual común de DESIGN.md, en tema claro y oscuro, accesible y liviano para datos móviles.

## Requirements

### Requirement: Pantalla de inicio de sesión
La pantalla de inicio de sesión SHALL mostrar, en este orden, el nombre "I.E. Virgen del Carmen", "Huayucachi", "Sesiones · Notas · Asistencia", el formulario con Usuario, Contraseña, el botón "Ingresar" y la ayuda "Si olvidaste tu contraseña, pide al administrador que la restablezca.", y al final el pie "CarpetaDocente · 2026". No muestra logo ni escudo, ni enlaces a funciones que no existen. Desde US-003 el campo Usuario lleva debajo la pista de una línea "Ejemplo: jperez (inicial y apellido)", asociada al campo para el lector de pantalla. Desde el rebrand, tras un ingreso rechazado el mensaje de error MUST recibir el foco al cargar la página y el lector de pantalla MUST anunciarlo una sola vez.

#### Scenario: Contenido de la pantalla
- **WHEN** alguien sin sesión abre `/ingresar/`
- **THEN** ve el nombre de la I.E., el lugar, las tres dimensiones, el formulario con su ayuda y el pie, sin escudo, sin menú y sin un enlace para recuperar la contraseña

#### Scenario: Pista del campo Usuario
- **WHEN** alguien sin sesión abre `/ingresar/`
- **THEN** bajo el campo Usuario ve "Ejemplo: jperez (inicial y apellido)" en una línea, y el lector de pantalla la anuncia como descripción del campo, también cuando el campo muestra un error

#### Scenario: Mensaje de error sobre el formulario
- **WHEN** un ingreso es rechazado
- **THEN** el mensaje aparece sobre la tarjeta del formulario, con ícono, la primera línea destacada y la segunda en el color del texto, recibe el foco al cargar la página y el lector de pantalla lo anuncia una sola vez

#### Scenario: Error y teclado
- **WHEN** un ingreso es rechazado y el usuario pulsa Tab desde el mensaje enfocado
- **THEN** el foco pasa al campo Usuario, que conserva lo escrito

### Requirement: Mostrar la contraseña
El campo de contraseña SHALL tener un botón "Mostrar contraseña" que alterna entre ver y ocultar lo escrito e informa su estado al lector de pantalla. Sin JavaScript, el botón no aparece y el campo funciona como siempre. Al enviar el formulario, la contraseña vuelve a ocultarse.

#### Scenario: Ver la contraseña
- **WHEN** el usuario toca "Mostrar contraseña"
- **THEN** la contraseña se ve en texto y el botón queda marcado como presionado; al tocarlo otra vez, se oculta

#### Scenario: Sin JavaScript
- **WHEN** la página se abre sin JavaScript
- **THEN** el botón no aparece y el formulario se puede enviar igual

### Requirement: Estado de envío
Mientras se envía el formulario, el botón SHALL decir "Ingresando…" con un fondo distinto del normal y los dos campos MUST quedar de solo lectura, para que el cambio no dependa solo del texto y no se envíe dos veces.

#### Scenario: Envío en curso
- **WHEN** el usuario toca "Ingresar" con los dos campos llenos
- **THEN** el botón cambia a "Ingresando…" con el fondo de envío y los campos quedan de solo lectura hasta que llega la respuesta

### Requirement: Portada del docente
La portada del docente SHALL saludar al docente por su nombre y mostrar las tarjetas de las tres dimensiones en este orden, que es también el orden de lectura: Asistencia, Sesiones y Notas, cada una con su título corto, su frase de acción y su miniatura esquemática, sin el subtítulo formal de la dimensión y sin ningún dato que pueda leerse como un registro del docente, salvo el avance de hoy en la miniatura de Asistencia. Las frases son "Marca la asistencia de cada día.", "Envía tu sesión a la dirección y compártela con tus colegas." y "Registra tus notas por competencia para el SIAGIE.". En la computadora, Asistencia es la tarjeta principal y Sesiones y Notas van a su lado; en el celular, las tres se apilan en el mismo orden, sin carrusel. Desde US-005, bajo el saludo y fuera del encabezado principal, una línea SHALL mostrar las secciones del docente en el año escolar ABIERTO de su institución, con el formato "2.º grado, sección A" (º ordinal), separadas por " · " y ordenadas por grado y nombre. Sin sección en el año ABIERTO, la línea dice "Tu sección aparecerá cuando el administrador la asigne." Las tarjetas no cambian. Desde US-006, si la docente tiene una sola sección en el año ABIERTO, junto a esa línea (que sigue siendo texto, sin estilo de enlace) va el enlace "Ver estudiantes" con la flecha de acción, de 44 px de alto como mínimo, que abre la lista de la sección; y mientras la sección no tenga estudiantes, debajo aparece el aviso "Tu sección aún no tiene estudiantes" / "Agrégalos para poder tomar asistencia", que desaparece en cuanto la sección tiene estudiantes, también sin recargar la página. Con varias secciones, o sin sección, no hay enlace ni aviso. Desde US-030, el saludo depende de la hora de Lima: "Buenos días" hasta las 11:59, "Buenas tardes" de 12:00 a 18:59 y "Buenas noches" desde las 19:00. Con una sola sección, en un día de lunes a viernes, con estudiantes activos y la jornada de hoy sin completar, la tarjeta Asistencia lleva la píldora "Hoy: pendiente", sin enlace propio y descrita en el enlace de la tarjeta; con la jornada completa, el fin de semana o sin estudiantes, no está. Desde US-040, la fecha de hoy ya no va en la línea de la sección: va en la miniatura de Asistencia, un calendario con el día de la semana, el día del mes y el mes, y el lector de pantalla la lee completa una vez («Lunes 23 de noviembre»). Con una sola sección con estudiantes activos en un día de lunes a viernes, la miniatura dice además «N de M estudiantes marcados» con una barra de avance; un sábado o domingo dice «Día sin clases»; con la sección sin estudiantes, «Sin estudiantes»; sin sección única, «Registro no disponible».

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
- **THEN** bajo el saludo ve "2.º grado, sección A", sin la fecha, y esa línea no forma parte del encabezado principal

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

#### Scenario: Asistencia de hoy pendiente
- **WHEN** un miércoles la sección de la docente tiene 25 estudiantes activos y solo 18 marcados hoy, o ninguno
- **THEN** la tarjeta Asistencia muestra "Hoy: pendiente", que no es un enlace aparte, y el lector de pantalla lo lee con el enlace de la tarjeta

#### Scenario: Asistencia de hoy completa
- **WHEN** los 25 estudiantes activos tienen estado hoy
- **THEN** la tarjeta Asistencia no muestra "Hoy: pendiente"

#### Scenario: Fin de semana o sección sin estudiantes
- **WHEN** es sábado, o la sección no tiene estudiantes
- **THEN** la tarjeta Asistencia no muestra "Hoy: pendiente"

#### Scenario: Calendario de Asistencia con avance
- **WHEN** el lunes 23 de noviembre la sección única de la docente tiene 25 estudiantes activos y 18 marcados hoy
- **THEN** la miniatura de Asistencia muestra «Lunes», «23» y «noviembre», «18 de 25 estudiantes marcados» y la barra de avance, y el lector de pantalla lee «Lunes 23 de noviembre» una sola vez

#### Scenario: Calendario sin registro
- **WHEN** es sábado, o la sección no tiene estudiantes, o la docente no tiene sección única
- **THEN** la miniatura muestra la fecha con «Día sin clases», «Sin estudiantes» o «Registro no disponible», sin barra

### Requirement: Disponibilidad de cada dimensión
Cada dimensión SHALL tener una bandera de disponibilidad que activa la historia que construye su pantalla. Una dimensión no disponible se muestra como "Próximamente" y nunca se oculta; una disponible enlaza a su pantalla. Ninguna tarjeta MUST enlazar a una página que no existe. Al cerrar US-001, las tres están en "Próximamente". Desde US-030, Asistencia está disponible y su tarjeta enlaza a la asistencia de hoy de la sección, con la misma regla que "Ver estudiantes": solo si la docente tiene una sola sección en el año ABIERTO. Sin esa sección única, la tarjeta Asistencia se muestra como "Próximamente". Desde US-020, Notas está disponible con la misma regla y su tarjeta enlaza a la hoja de notas de la sección, que abre en el periodo vigente. Desde US-011, Sesiones está disponible y su tarjeta enlaza a la pantalla Sesiones, tenga o no sección la docente.

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
- **THEN** la tarjeta Asistencia dice "Registrar asistencia" y lleva a la asistencia de hoy de esa sección

#### Scenario: Asistencia sin sección única
- **WHEN** una docente sin sección, o con dos, abre la portada
- **THEN** la tarjeta Asistencia se muestra como "Próximamente" y no contiene un enlace

#### Scenario: Notas con una sección
- **WHEN** una docente con una sola sección en el año ABIERTO abre la portada y toca la tarjeta Notas
- **THEN** la tarjeta dice "Registrar notas" y lleva a la hoja de notas de esa sección en el periodo vigente, o a Competencias si ese periodo no tiene competencias guardadas

#### Scenario: Notas sin sección única
- **WHEN** una docente sin sección, o con dos, abre la portada
- **THEN** la tarjeta Notas se muestra como "Próximamente" y no contiene un enlace

#### Scenario: Sesiones con o sin sección
- **WHEN** una docente con una sección, con dos o sin sección abre la portada
- **THEN** la tarjeta Sesiones dice "Ver sesiones" y lleva a la pantalla Sesiones

### Requirement: Inicio de la dirección
La portada de la dirección SHALL saludar al usuario por su nombre, según la hora de Lima como la del docente, con la línea «Dirección · <romano> bimestre vigente, hasta el <fin>» (sin bimestre vigente: «Dirección · <nombre de la I.E.>»), y mostrar, en este orden:
- la banda café «Consolidados», enlazada entera a Consolidados, con «Revisa cómo van las notas, la asistencia y las sesiones de las <N> secciones.», la pastilla «N secciones por revisar» (las atrasadas del bimestre vigente, spec `consolidados-direccion`; «1 sección por revisar»; sin pastilla con 0) y una miniatura de papel con la fecha de hoy y un mapa de las secciones por grado, que marca las atrasadas y las que no tienen docente o estudiantes. Sin bimestres configurados dice «Aún no hay bimestres configurados. Los consolidados aparecerán cuando el administrador configure los bimestres de <año>.», sin pastilla y con la miniatura solo de la fecha; antes del primer bimestre, «Hoy no hay un bimestre vigente», sin pastilla;
- la tarjeta Entregas, con «Al cierre del bimestre, revisa quién entregó sus notas y habilita correcciones.» y «Próximamente», sin enlace (US-042);
- el bloque «Al cierre del bimestre», con «Cuando una sección tenga sus notas completas, pásalas a la plantilla.» y el botón «Completar plantilla del SIAGIE», que abre el diálogo de subida de la plantilla (spec `plantilla-notas-siagie`).

#### Scenario: Inicio de la dirección en el Sprint 1
- **WHEN** un usuario de la dirección entra al sistema a las 9:00 de Lima el lunes 23 de noviembre, en el IV bimestre que termina el 18 de diciembre, con 13 secciones atrasadas
- **THEN** ve «Buenos días,» con su nombre, «Dirección · IV bimestre vigente, hasta el 18 de diciembre», la banda «Consolidados» con «13 secciones por revisar», la tarjeta Entregas con «Próximamente» y el botón «Completar plantilla del SIAGIE»

#### Scenario: La banda lleva a Consolidados
- **WHEN** la dirección toca cualquier parte de la banda «Consolidados»
- **THEN** llega a Consolidados en el bimestre vigente

#### Scenario: Acceso a la plantilla del SIAGIE
- **WHEN** la dirección toca «Completar plantilla del SIAGIE»
- **THEN** se abre el diálogo de subida de la plantilla

#### Scenario: Sin bimestres en la portada
- **WHEN** el año ABIERTO no tiene periodos
- **THEN** la línea dice «Dirección · <nombre de la I.E.>» y la banda dice «Aún no hay bimestres configurados…», sin pastilla, con la miniatura solo de la fecha, y sigue llevando a Consolidados

#### Scenario: Todas al día
- **WHEN** ninguna sección está atrasada en el bimestre vigente
- **THEN** la banda no muestra la pastilla

#### Scenario: Entregas próximamente
- **WHEN** la dirección toca la tarjeta Entregas
- **THEN** la página no cambia de dirección

### Requirement: Marco común
Las pantallas con sesión de los roles SHALL compartir una barra superior y un pie. En las pantallas interiores de la docente y de la dirección, la barra queda fija arriba y lleva, en este orden, el ☰, el título de la pantalla y, a la derecha, el botón de tema y el menú de la cuenta (spec `cierre-sesion`). La portada del docente y la portada de la dirección llevan en la barra solo el botón de tema y el menú de la cuenta, sin ☰. El nombre de la I.E. no va en la barra. El pie muestra "CarpetaDocente · 2026" a la izquierda e "I.E. Virgen del Carmen" a la derecha, alineados con los bordes del contenido.

#### Scenario: Barra de una pantalla interior
- **WHEN** una docente abre una pantalla interior, por ejemplo «sin permiso»
- **THEN** ve en la barra el ☰, el título de la pantalla («Sin permiso»), el botón de tema y el menú de la cuenta a la derecha, sin el nombre de la I.E., y la barra sigue visible al desplazar la página

#### Scenario: Barra de un interior de la dirección
- **WHEN** la dirección abre Consolidados
- **THEN** ve en la barra el ☰, «Consolidados», el botón de tema y el menú de la cuenta, y no hay un enlace de regreso sobre el título

#### Scenario: Barra y pie
- **WHEN** un docente abre su portada o un usuario de la dirección abre la suya
- **THEN** la barra lleva solo el botón de tema y el menú de la cuenta a la derecha, sin ☰ ni nombre de la I.E., y el pie va al final

#### Scenario: Pie
- **WHEN** un usuario con sesión llega al final de una pantalla con el marco común, a 1280 px y a 360 px
- **THEN** ve "CarpetaDocente · 2026" a la izquierda e "I.E. Virgen del Carmen" a la derecha, los dos alineados con los bordes del contenido y sin desplazamiento horizontal

### Requirement: Navegación de la docente
El ☰ de las pantallas interiores de la docente SHALL abrir un panel lateral, sobre la barra, con Inicio, Sesiones, Asistencia y Notas, en ese orden, y marcar la pantalla actual. Inicio enlaza a la portada; los otros tres siguen la disponibilidad de su tarjeta de la portada, y lo no disponible se ve como "Próximamente", sin enlace, y nunca se oculta. El ☰ MUST funcionar con teclado; sin JavaScript MUST llevar a la portada. Abierto, MUST NOT causar desplazamiento horizontal.

#### Scenario: Abrir el ☰
- **WHEN** una docente con una sola sección en el año ABIERTO toca el ☰ en «sin permiso»
- **THEN** ve un panel que cubre la barra, con "Cerrar navegación" y con Inicio, Sesiones, Asistencia y Notas, en ese orden; Inicio lleva a la portada, Sesiones a la pantalla Sesiones, Asistencia a la asistencia de hoy de su sección y Notas a la hoja de notas de su sección, igual que las tarjetas de la portada

#### Scenario: Destino no disponible
- **WHEN** la docente no tiene sección única en el año ABIERTO y abre el ☰
- **THEN** Asistencia y Notas se ven con "Próximamente", sin enlace, y siguen en la lista; Sesiones sí enlaza a su pantalla

#### Scenario: Ubicación actual
- **WHEN** la docente abre el ☰ desde la hoja de notas de su sección
- **THEN** Notas está marcada como la pantalla actual, a la vista y para el lector de pantalla, y ningún otro destino lo está; desde «sin permiso», ninguno está marcado

#### Scenario: Ubicación actual en Sesiones
- **WHEN** la docente abre el ☰ desde «Mis sesiones», el repositorio o la página de una sesión
- **THEN** Sesiones está marcada como la pantalla actual y ningún otro destino lo está

#### Scenario: Teclado
- **WHEN** la docente abre el ☰ con el teclado, recorre el panel con Tab y pulsa Escape
- **THEN** mientras el panel está abierto Tab no llega a la página de atrás; con Escape el panel se cierra y el foco vuelve al ☰

#### Scenario: Cerrar con el ✕
- **WHEN** el panel del ☰ está abierto y la docente toca "Cerrar navegación"
- **THEN** el panel se cierra y el foco vuelve al ☰

#### Scenario: Toque fuera del panel
- **WHEN** el panel del ☰ está abierto y la docente toca fuera de él
- **THEN** el panel se cierra y el foco vuelve al ☰

#### Scenario: Sin JavaScript
- **WHEN** el navegador no ejecuta JavaScript
- **THEN** el ☰ lleva a la portada

#### Scenario: ☰ abierto a 320 px
- **WHEN** el panel del ☰ está abierto a 320 px y a 360 px, en ambos temas
- **THEN** el ancho del documento no supera el de la ventana y "Cerrar navegación" sigue visible

### Requirement: Navegación de la dirección
El ☰ de las pantallas interiores de la dirección SHALL abrir el mismo panel lateral que el de la docente, con Inicio, Consolidados y Entregas, en ese orden, y marcar la pantalla actual. Inicio enlaza a la portada de la dirección y Consolidados a Consolidados; Entregas se ve con «Próximamente», sin enlace, hasta US-042. No hay enlaces de regreso («‹ Inicio», «‹ Consolidados») sobre el título: se vuelve con el ☰. El ☰ MUST funcionar con teclado igual que el de la docente; sin JavaScript MUST llevar a la portada de la dirección.

#### Scenario: Abrir el ☰ de la dirección
- **WHEN** la dirección toca el ☰ en Consolidados
- **THEN** ve el panel con Inicio, Consolidados y Entregas, en ese orden; Inicio lleva a su portada, Consolidados está marcada como la pantalla actual y Entregas dice «Próximamente», sin enlace

#### Scenario: Ubicación actual en el detalle
- **WHEN** la dirección abre el ☰ desde el detalle de una sección o desde la página de una sesión
- **THEN** Consolidados está marcada como la pantalla actual y ningún otro destino lo está

#### Scenario: Sin JavaScript en la dirección
- **WHEN** el navegador no ejecuta JavaScript y la dirección toca el ☰
- **THEN** llega a su portada

### Requirement: Temas claro y oscuro
Cada pantalla SHALL usar los mismos tokens de DESIGN.md en sus valores claros u oscuros; el oscuro es Pizarra neutra (DESIGN.md 1.2). Desde US-040 (T-04), un botón de tema de solo ícono (luna en claro, sol en oscuro) va a la izquierda del menú de la cuenta en todas las barras con sesión y arriba a la derecha en el inicio de sesión; no va en el panel de administración. Su nombre accesible dice el tema al que cambia: «Cambiar a tema oscuro» o «Cambiar a tema claro». Sin elección, la pantalla sigue la preferencia del sistema operativo, también cuando cambia con la página abierta. Al tocar el botón, la elección se guarda en el dispositivo y se aplica antes de pintar en cada pantalla, sin un destello del otro tema, y llega a las demás pestañas abiertas. Sin JavaScript o sin almacenamiento en el dispositivo, la pantalla sigue la preferencia del sistema. Las plantillas MUST NOT escribir colores hexadecimales ni estilos en línea: solo usan las clases de los tokens.

#### Scenario: Preferencia oscura
- **WHEN** el sistema operativo prefiere el tema oscuro y el usuario no eligió un tema
- **THEN** las pantallas se ven con los valores oscuros de los tokens

#### Scenario: Elegir el tema
- **WHEN** con el sistema en claro el usuario toca «Cambiar a tema oscuro» y luego abre otra pantalla
- **THEN** las dos se ven en oscuro, la segunda sin pasar por el claro, y el botón pasa a llamarse «Cambiar a tema claro»

#### Scenario: Cambio del sistema sin elección
- **WHEN** el usuario no eligió un tema y el sistema operativo pasa de claro a oscuro con la página abierta
- **THEN** la página pasa a oscuro y el nombre del botón cambia con ella

#### Scenario: Otra pestaña
- **WHEN** el usuario elige el oscuro en una pestaña y tiene otra abierta del aplicativo
- **THEN** la otra pestaña pasa a oscuro sin recargarse

#### Scenario: Lugar del botón
- **WHEN** alguien abre el inicio de sesión, la portada de un rol, una pantalla interior o el panel de administración
- **THEN** el botón está arriba a la derecha en el inicio de sesión, a la izquierda del menú de la cuenta en la portada y en el interior, y no está en el panel de administración

#### Scenario: Plantillas sin colores escritos
- **WHEN** se revisan las plantillas del proyecto
- **THEN** ninguna contiene un color hexadecimal ni un atributo de estilo en línea

### Requirement: Accesibilidad en ambos temas
Cada pantalla nueva MUST pasar la revisión automática de accesibilidad (WCAG 2.1, niveles A y AA) sin infracciones críticas ni graves, en tema claro y en tema oscuro (RNF-008, DoD 7). El contraste de texto queda incluido en la revisión. Desde US-040, al cambiar el oscuro a Pizarra neutra, la revisión en oscuro se repite en todas las pantallas existentes, no solo en las nuevas.

#### Scenario: Revisión de cada pantalla
- **WHEN** se ejecuta la revisión automática sobre el inicio de sesión con el marco del rebrand (normal, con error, con campos vacíos, «Ingresando…» y con el aviso de inactividad), la portada del docente con el marco del rebrand (con una sección, con varias, sin sección, con la sección sin estudiantes, con «Hoy: pendiente», con una tarjeta «Próximamente» mostrando su aviso, con el menú de la cuenta abierto y con el diálogo de Estudiantes abierto), el inicio de la dirección con el marco del rebrand (con el menú de la cuenta cerrado y abierto) y «sin permiso» (con el ☰ y el menú de la cuenta cerrados, con el ☰ abierto y con el menú de la cuenta abierto), en ambos temas y en ambos anchos
- **THEN** no hay infracciones críticas ni graves

#### Scenario: Pantallas de US-040
- **WHEN** se ejecuta la revisión automática sobre la portada de la dirección (con bimestres y sin bimestres), con el ☰ de la dirección abierto, y sobre la portada del docente con el calendario de Asistencia, en ambos temas a 360 px
- **THEN** no hay infracciones críticas ni graves

#### Scenario: Pizarra neutra en las pantallas existentes
- **WHEN** corre la suite completa de pruebas en navegador con el oscuro de Pizarra neutra
- **THEN** ninguna revisión de accesibilidad en oscuro de las pantallas existentes tiene infracciones críticas ni graves

### Requirement: Sin desplazamiento horizontal
Ninguna pantalla nueva SHALL desplazarse en horizontal entre 320 px y 1280 px de ancho, en ningún tema (RNF-005).

#### Scenario: Pantallas a 320 px
- **WHEN** cada pantalla nueva se abre a 320 px y a 360 px, en ambos temas
- **THEN** el ancho del documento no supera el de la ventana

#### Scenario: Portada sin desplazamiento interno
- **WHEN** la portada se abre a 320 px y a 360 px, en ambos temas, con «Hoy: pendiente» y con el aviso de la sección sin estudiantes
- **THEN** ni el documento ni ningún contenedor de las tarjetas se desplaza en horizontal

### Requirement: Carga en conexión lenta
La pantalla de inicio de sesión MUST transferir 2 MB o menos y quedar usable en 5 segundos o menos con el perfil Slow 4G de Chrome DevTools y sin caché (RNF-002).

#### Scenario: Primera visita con Slow 4G
- **WHEN** un navegador sin caché, con el perfil Slow 4G, abre `/ingresar/`
- **THEN** se transfieren 2 MB o menos y el botón "Ingresar" está visible y habilitado, con la página cargada, en 5 segundos o menos
