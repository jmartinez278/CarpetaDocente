# Spec Delta

## MODIFIED Requirements

### Requirement: Jornadas registradas
La columna "jornadas registradas" SHALL contar las entradas REGISTRO_ASISTENCIA de la semana. La columna "secciones con notas" SHALL contar las secciones distintas con al menos una entrada NOTAS_GUARDADAS de una cuenta real en la semana. La columna "sesiones cargadas" SHALL contar las entradas SESION_ENVIADA de cuentas reales en la semana, compartidas o no.

#### Scenario: Columnas aún sin datos
- **WHEN** el Administrador abre la página
- **THEN** ninguna columna dice "—": "sesiones cargadas" muestra un número en cada fila, 0 si no hubo envíos

#### Scenario: Sesiones cargadas
- **WHEN** en una semana una docente envía dos sesiones, una compartida y otra no, y otra docente envía una
- **THEN** la fila de esa semana dice 3 en "sesiones cargadas"

#### Scenario: Semana sin sesiones
- **WHEN** en una semana nadie envía sesiones
- **THEN** la fila dice 0 en "sesiones cargadas"

#### Scenario: Sesiones de la demostración
- **WHEN** una cuenta demo envía una sesión en la semana
- **THEN** no cuenta en "sesiones cargadas"

#### Scenario: Secciones con notas
- **WHEN** en una semana una docente guarda notas de Matemática y de Comunicación de su sección, y otra docente guarda notas de la suya
- **THEN** la fila de esa semana dice 2 en "secciones con notas"

#### Scenario: Semana sin notas
- **WHEN** en una semana nadie guarda notas
- **THEN** la fila dice 0 en "secciones con notas"

#### Scenario: Notas de la demostración
- **WHEN** una cuenta demo guarda notas en la semana
- **THEN** esa sección no cuenta en "secciones con notas"
