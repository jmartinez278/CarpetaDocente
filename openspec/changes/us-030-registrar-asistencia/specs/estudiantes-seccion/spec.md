# Spec Delta

## MODIFIED Requirements

### Requirement: Estudiantes de una sección
Cada estudiante SHALL pertenecer a una sección y guardar solo sus apellidos y sus nombres (RN-015), de hasta 120 caracteres cada uno, en mayúsculas (conservando tildes y Ñ) y sin espacios al inicio, al final ni repetidos. Una sección MUST NOT tener dos estudiantes con los mismos apellidos y nombres, y la base de datos lo impide. Desde US-030, cada estudiante está en uno de tres estados, ACTIVO, TRASLADADO o RETIRADO, con la fecha de su último cambio (RN-027); un estudiante nuevo, importado o agregado, empieza ACTIVO y sin fecha de cambio. La base de datos solo admite esos tres estados.

#### Scenario: Nombre guardado en mayúsculas
- **WHEN** la docente guarda "  quispe   mamani " y "ana lucía"
- **THEN** el estudiante queda como "QUISPE MAMANI, ANA LUCÍA"

#### Scenario: Homónimo exacto en la misma sección
- **WHEN** se intenta guardar un estudiante con los mismos apellidos y nombres que otro de la sección, por cualquier vía
- **THEN** no se guarda

#### Scenario: Mismo nombre en otra sección
- **WHEN** dos secciones tienen un estudiante "QUISPE MAMANI, ANA"
- **THEN** ambos se guardan

#### Scenario: Estudiante nuevo
- **WHEN** la docente importa o agrega un estudiante
- **THEN** queda ACTIVO, sin fecha de cambio de estado

#### Scenario: Estado desconocido
- **WHEN** se intenta guardar un estudiante con un estado distinto de ACTIVO, TRASLADADO o RETIRADO, por cualquier vía
- **THEN** no se guarda

### Requirement: Pegar lista
La docente SHALL pegar en un cuadro de texto una línea por estudiante con el formato "APELLIDOS, NOMBRES". Las líneas en blanco se ignoran, pero cuentan para numerar las líneas tal como se ven en el cuadro. Si todas las líneas son válidas, se guardan todos y la lista muestra "N estudiantes importados" / "Revisa los nombres; puedes corregirlos con Editar", sin que el aviso desaparezca solo. Desde US-030, el aviso lleva además el enlace "Tomar la asistencia de hoy", de 44 px de alto como mínimo, que abre la asistencia de hoy de la sección.

#### Scenario: Camino ideal
- **WHEN** una docente con una sección asignada y sin estudiantes pega las filas copiadas de una hoja de cálculo, 25 líneas con apellidos y nombres completos, y toca "Importar"
- **THEN** el sistema registra los 25 estudiantes en la sección y muestra "25 estudiantes importados", y la cabecera dice "25 estudiantes"

#### Scenario: Líneas en blanco
- **WHEN** el texto tiene 25 estudiantes y líneas en blanco entre ellos y al final
- **THEN** se importan los 25 y ninguna línea en blanco da error

#### Scenario: Paso siguiente tras importar
- **WHEN** la docente importa la lista y toca "Tomar la asistencia de hoy" en el aviso
- **THEN** se abre la asistencia de hoy de su sección, como página completa
