# Spec Delta

## MODIFIED Requirements

### Requirement: Jornadas registradas
La columna "jornadas registradas" SHALL contar las entradas REGISTRO_ASISTENCIA de la semana. La columna "secciones con notas" SHALL contar las secciones distintas con al menos una entrada NOTAS_GUARDADAS de una cuenta real en la semana. "Sesiones cargadas" muestra "—" hasta que US-010 registre su operación.

#### Scenario: Columnas aún sin datos
- **WHEN** el Administrador abre la página
- **THEN** la columna "sesiones cargadas" dice "—" en cada fila

#### Scenario: Secciones con notas
- **WHEN** en una semana una docente guarda notas de Matemática y de Comunicación de su sección, y otra docente guarda notas de la suya
- **THEN** la fila de esa semana dice 2 en "secciones con notas"

#### Scenario: Semana sin notas
- **WHEN** en una semana nadie guarda notas
- **THEN** la fila dice 0 en "secciones con notas"

#### Scenario: Notas de la demostración
- **WHEN** una cuenta demo guarda notas en la semana
- **THEN** esa sección no cuenta en "secciones con notas"
