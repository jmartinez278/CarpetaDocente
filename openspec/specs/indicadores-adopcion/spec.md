# indicadores-adopcion Specification

## Purpose
Página de indicadores por semana para el Administrador: docentes activos (KPI-01), jornadas registradas y demás actividad calculadas a partir del registro de actividad, excluyendo la demostración.

## Requirements

### Requirement: Indicadores por semana
El panel SHALL tener la página "Indicadores por semana", solo para el Administrador, con una fila por semana (de lunes a domingo, hora de Lima) dentro del rango elegido. Por defecto, el rango es el año escolar ABIERTO, del 1 de enero a hoy; un rango que corta una semana la muestra entera. Columnas: semana, docentes activos / participantes, jornadas registradas, sesiones cargadas y secciones con notas. Las semanas sin actividad se muestran con 0.

#### Scenario: Flujo alternativo válido (consultar un periodo)
- **GIVEN** el administrador
- **WHEN** consulta la actividad de un periodo
- **THEN** el sistema muestra, por semana, el número de docentes activos (con al menos un uso en la semana, KPI-01), de sesiones cargadas, de jornadas registradas y de secciones con notas registradas (KPIs del documento 03)

#### Scenario: Rango por defecto
- **WHEN** el Administrador abre la página sin elegir fechas
- **THEN** ve las semanas del año ABIERTO desde el 1 de enero hasta la semana de hoy

#### Scenario: Rango al revés
- **WHEN** elige un "desde" posterior al "hasta"
- **THEN** la página dice "La fecha de inicio debe ser anterior a la de fin" y no muestra filas

#### Scenario: Domingo por la noche
- **WHEN** una docente registra una jornada un domingo a las 23:30 hora de Lima
- **THEN** cuenta en la semana que termina ese domingo, no en la siguiente

#### Scenario: Otro rol
- **WHEN** una docente o un usuario de la dirección pide la página
- **THEN** no la ve

### Requirement: Docentes activos (KPI-01)
Participantes SHALL ser las cuentas Docente activas con al menos una sección en el año ABIERTO, contadas al día de la consulta. Un participante es activo en una semana si hizo al menos una operación que cuenta para KPI-01 en esa semana. La columna se muestra como "activos / participantes (porcentaje)", por ejemplo "3 / 5 (60 %)"; sin participantes, "0 / 0 (—)".

#### Scenario: Solo iniciar sesión
- **WHEN** una docente participante solo inicia y cierra sesión en una semana
- **THEN** no cuenta como activa en esa semana

#### Scenario: Registra asistencia
- **WHEN** una docente participante marca la asistencia el martes y el jueves de una semana
- **THEN** cuenta una vez como activa en esa semana

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

### Requirement: La demostración no cuenta
Las cuentas de demostración (marca de EN-06) y lo que hacen MUST quedar fuera de todo cálculo de la página: no son participantes, no son activas y sus jornadas no se cuentan.

#### Scenario: Demo cargada
- **GIVEN** la demostración cargada y una docente real que registra una jornada
- **WHEN** el Administrador abre la página
- **THEN** la semana muestra "1 / 1 (100 %)" y 1 jornada registrada, aunque las cuentas demo hayan marcado asistencia

### Requirement: Accesibilidad de la página
La página "Indicadores por semana" MUST pasar la revisión automática de accesibilidad (WCAG 2.1 A y AA) sin infracciones críticas ni graves, en ambos temas, a 360 y 1280 px; la tabla tiene encabezados de columna y el formulario de fechas, etiquetas.

#### Scenario: Revisión automática
- **WHEN** se revisa la página con axe-core en claro y oscuro, a 360 y 1280 px
- **THEN** no hay infracciones críticas ni graves
