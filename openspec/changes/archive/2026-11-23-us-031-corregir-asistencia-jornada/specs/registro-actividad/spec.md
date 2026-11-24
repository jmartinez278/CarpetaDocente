## MODIFIED Requirements

### Requirement: Cambios de asistencia
Cada cambio de estado de un estudiante en una jornada SHALL dejar una entrada ASISTENCIA_CAMBIADA con el identificador del estudiante, el estado anterior (vacío si no tenía), el estado nuevo, si cambió la nota de justificación y el origen (`toque` o `lote`). Si la jornada no es de hoy (fecha de Lima), el detalle suma `correccion: true`; de hoy, no lleva esa clave. La jornada nueva deja REGISTRO_ASISTENCIA y, la primera vez que todos sus estudiantes activos de ese día quedan marcados, JORNADA_COMPLETA.

#### Scenario: Primer toque del día
- **WHEN** la docente marca al primer estudiante del día
- **THEN** quedan REGISTRO_ASISTENCIA de la jornada y ASISTENCIA_CAMBIADA de ese estudiante con estado anterior vacío y origen `toque`

#### Scenario: Mismo estado otra vez
- **WHEN** llega de nuevo el mismo estado y la misma nota de un estudiante (un reintento)
- **THEN** no queda una entrada nueva

#### Scenario: Lote
- **WHEN** se guardan "los N restantes como Asistió"
- **THEN** quedan N entradas ASISTENCIA_CAMBIADA con origen `lote`, solo de los que no tenían estado

#### Scenario: Jornada completa
- **WHEN** la docente marca al último estudiante activo sin estado
- **THEN** queda una entrada JORNADA_COMPLETA; si luego cambia un estado, no queda otra

#### Scenario: Corrección de un día anterior
- **WHEN** la docente cambia a un estudiante de Faltó a Justificado en la jornada del lunes 16, siendo hoy jueves 19
- **THEN** la entrada ASISTENCIA_CAMBIADA lleva `correccion: true`, con el estado anterior Faltó y el nuevo Justificado

#### Scenario: Cambio de hoy
- **WHEN** la docente cambia un estado en la jornada de hoy
- **THEN** la entrada ASISTENCIA_CAMBIADA no lleva `correccion`

#### Scenario: Día anterior olvidado
- **WHEN** la docente marca por primera vez un día anterior sin jornada
- **THEN** quedan REGISTRO_ASISTENCIA de esa fecha y ASISTENCIA_CAMBIADA con `correccion: true`
