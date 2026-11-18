# Spec Delta

## MODIFIED Requirements

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
