# Spec Delta

## MODIFIED Requirements

### Requirement: Disponibilidad de cada dimensión
Cada dimensión SHALL tener una bandera de disponibilidad que activa la historia que construye su pantalla. Una dimensión no disponible se muestra como "Próximamente" y nunca se oculta; una disponible enlaza a su pantalla. Ninguna tarjeta MUST enlazar a una página que no existe. Al cerrar US-001, las tres están en "Próximamente". Desde US-030, Asistencia está disponible y su tarjeta enlaza a la asistencia de hoy de la sección, con la misma regla que "Ver estudiantes": solo si la docente tiene una sola sección en el año ABIERTO. Sin esa sección única, la tarjeta Asistencia se muestra como "Próximamente". Desde US-020, Notas está disponible con la misma regla y su tarjeta enlaza a la hoja de notas de la sección, que abre en el periodo vigente.

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
- **THEN** la tarjeta Asistencia dice "Registrar asistencia" y lleva a la asistencia de hoy de esa sección; Sesiones sigue en "Próximamente"

#### Scenario: Asistencia sin sección única
- **WHEN** una docente sin sección, o con dos, abre la portada
- **THEN** la tarjeta Asistencia se muestra como "Próximamente" y no contiene un enlace

#### Scenario: Notas con una sección
- **WHEN** una docente con una sola sección en el año ABIERTO abre la portada y toca la tarjeta Notas
- **THEN** la tarjeta dice "Registrar notas" y lleva a la hoja de notas de esa sección en el periodo vigente, o a Competencias si ese periodo no tiene competencias guardadas

#### Scenario: Notas sin sección única
- **WHEN** una docente sin sección, o con dos, abre la portada
- **THEN** la tarjeta Notas se muestra como "Próximamente" y no contiene un enlace
