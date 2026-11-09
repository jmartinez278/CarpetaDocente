## MODIFIED Requirements

### Requirement: Marco común
Las pantallas con sesión de los roles SHALL compartir una barra superior y un pie. En las pantallas interiores de la docente, la barra queda fija arriba y lleva, en este orden, el ☰, el título de la pantalla y, a la derecha, el menú de la cuenta (spec `cierre-sesion`). La portada del docente y el inicio de la dirección llevan en la barra solo el menú de la cuenta, sin ☰. El nombre de la I.E. no va en la barra. El pie muestra "CarpetaDocente · 2026" a la izquierda e "I.E. Virgen del Carmen" a la derecha, alineados con los bordes del contenido.

#### Scenario: Barra de una pantalla interior
- **WHEN** una docente abre una pantalla interior, por ejemplo «sin permiso»
- **THEN** ve en la barra el ☰, el título de la pantalla («Sin permiso») y el menú de la cuenta a la derecha, sin el nombre de la I.E., y la barra sigue visible al desplazar la página

#### Scenario: Barra y pie
- **WHEN** un docente abre su portada o un usuario de la dirección abre su inicio
- **THEN** la barra lleva solo el menú de la cuenta a la derecha, sin ☰ ni nombre de la I.E., y el pie va al final

#### Scenario: Pie
- **WHEN** un usuario con sesión llega al final de una pantalla con el marco común, a 1280 px y a 360 px
- **THEN** ve "CarpetaDocente · 2026" a la izquierda e "I.E. Virgen del Carmen" a la derecha, los dos alineados con los bordes del contenido y sin desplazamiento horizontal

### Requirement: Accesibilidad en ambos temas
Cada pantalla nueva MUST pasar la revisión automática de accesibilidad (WCAG 2.1, niveles A y AA) sin infracciones críticas ni graves, en tema claro y en tema oscuro, a 360 px y a 1280 px (RNF-008, DoD 7). El contraste de texto queda incluido en la revisión.

#### Scenario: Revisión de cada pantalla
- **WHEN** se ejecuta la revisión automática sobre el inicio de sesión (normal, con error, con campos vacíos y con el aviso de inactividad), la portada del docente y el inicio de la dirección (cada una con el menú cerrado y abierto) y «sin permiso» (con el ☰ y el menú de la cuenta cerrados, con el ☰ abierto y con el menú de la cuenta abierto), en ambos temas y en ambos anchos
- **THEN** no hay infracciones críticas ni graves

## ADDED Requirements

### Requirement: Navegación de la docente
El ☰ de las pantallas interiores de la docente SHALL abrir un panel lateral, sobre la barra, con Inicio, Sesiones, Asistencia y Notas, en ese orden, y marcar la pantalla actual. Inicio enlaza a la portada; los otros tres siguen la disponibilidad de su tarjeta de la portada, y lo no disponible se ve como "Próximamente", sin enlace, y nunca se oculta. El ☰ MUST funcionar con teclado; sin JavaScript MUST llevar a la portada. Abierto, MUST NOT causar desplazamiento horizontal.

#### Scenario: Abrir el ☰
- **WHEN** una docente con una sola sección en el año ABIERTO toca el ☰ en «sin permiso»
- **THEN** ve un panel que cubre la barra, con "Cerrar navegación" y con Inicio, Sesiones, Asistencia y Notas, en ese orden; Inicio lleva a la portada, Asistencia a la asistencia de hoy de su sección y Notas a la hoja de notas de su sección, igual que las tarjetas de la portada

#### Scenario: Destino no disponible
- **WHEN** la bandera de Sesiones está apagada, o la docente no tiene sección única en el año ABIERTO, y abre el ☰
- **THEN** Sesiones (y, sin sección única, también Asistencia y Notas) se ve con "Próximamente", sin enlace, y sigue en la lista

#### Scenario: Ubicación actual
- **WHEN** la docente abre el ☰ desde la hoja de notas de su sección
- **THEN** Notas está marcada como la pantalla actual, a la vista y para el lector de pantalla, y ningún otro destino lo está; desde «sin permiso», ninguno está marcado

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
