# datos-demostracion Specification

## Purpose
Datos ficticios para mostrar y probar el aplicativo sin datos reales de estudiantes (RN-018): secciones de demostración que el equipo carga y retira con un comando, y el descarte de lo cargado en una sección del piloto.

## Requirements

### Requirement: Cargar la demostración
Un comando del equipo SHALL llenar las 8 primeras secciones del año ABIERTO de una institución, en orden de grado y nombre (1.° A a 2.° D). Cada una recibe su cuenta de docente demo, 25 estudiantes ficticios (o el número que se indique, de 1 a 60) y la asistencia de los últimos 10 días de lunes a viernes anteriores a hoy y del mismo año escolar. Todo se carga o nada.

#### Scenario: Demostración cargada
- **WHEN** se ejecuta la carga de la demostración en una institución con su año ABIERTO y las 24 secciones vacías
- **THEN** 1.° A a 2.° D tienen cada una su docente demo, 25 estudiantes ACTIVOS y 10 jornadas con un estado para cada estudiante, y las otras 16 secciones siguen vacías

#### Scenario: Sin datos reales
- **WHEN** se revisan los estudiantes y las docentes cargados
- **THEN** todos los nombres salen de las listas ficticias del aplicativo

#### Scenario: Solo días de clase pasados
- **WHEN** la demostración se carga un lunes
- **THEN** ninguna jornada cae en sábado, domingo, hoy ni en una fecha futura, y no hay dos jornadas de la misma sección en la misma fecha

#### Scenario: Otro número de estudiantes
- **WHEN** se carga la demostración pidiendo 30 estudiantes
- **THEN** cada sección demo tiene 30

#### Scenario: Volver a cargar
- **WHEN** se ejecuta la carga sobre una demostración ya cargada
- **THEN** no se crea nada más

#### Scenario: Sin año abierto
- **WHEN** la institución no tiene un año ABIERTO
- **THEN** el comando termina con un error y no crea nada

### Requirement: La demostración no pisa secciones en uso
La carga SHALL negarse, sin crear nada, si alguna de las 8 secciones tiene una docente que no es una cuenta demo o tiene estudiantes sin una docente demo. Fuera del modo de desarrollo, SHALL pedir una confirmación explícita antes de escribir.

#### Scenario: Sección con docente real
- **WHEN** 2.° B tiene asignada una docente que no es demo y se ejecuta la carga
- **THEN** el comando termina con un error que nombra 2.° B y no se crea nada en ninguna sección

#### Scenario: Producción sin confirmar
- **WHEN** se ejecuta la carga fuera del modo de desarrollo sin la confirmación
- **THEN** el comando dice qué haría, termina con un error y no crea nada

### Requirement: Cuentas demo identificables
Las cuentas demo SHALL tener un usuario fijo de una lista conocida y una marca de cuenta demo que solo pone la carga, con rol Docente, la institución de la carga, y la contraseña que el equipo da por variable de entorno; no se les pide cambiarla. Sin esa variable, la carga no crea nada.

#### Scenario: Ingreso con una cuenta demo
- **WHEN** se ingresa con el usuario demo de 1.° A y la contraseña de la variable
- **THEN** se llega a la portada de 1.° A sin pasar por el cambio de contraseña

#### Scenario: Cuenta real con un usuario de la lista
- **WHEN** una Docente real de la institución, sin la marca demo, tiene el usuario demo de 1.° A y se ejecuta la carga
- **THEN** el comando termina con un error que nombra ese usuario, no crea nada y la contraseña de esa cuenta no cambia

#### Scenario: Sin contraseña configurada
- **WHEN** se ejecuta la carga sin la variable de la contraseña demo
- **THEN** el comando termina con un error y no crea nada

### Requirement: Quitar la demostración
Un comando del equipo SHALL borrar la asistencia, las jornadas y los estudiantes de las secciones cuya docente es una cuenta con la marca demo, dejarlas sin docente y desactivar esas cuentas, sin borrarlas (RN-023). Pide confirmación explícita y no toca otras secciones.

#### Scenario: Secciones liberadas
- **WHEN** se quita la demostración con la confirmación
- **THEN** 1.° A a 2.° D quedan sin docente, sin estudiantes y sin jornadas, y las cuentas demo existen pero están inactivas

#### Scenario: Otras secciones intactas
- **WHEN** 3.° A tiene una docente real con su lista y asistencia, y se quita la demostración
- **THEN** 3.° A no cambia

#### Scenario: Cuenta real con un usuario de la lista intacta
- **WHEN** 3.° A tiene como docente una cuenta real sin la marca demo cuyo usuario está en la lista demo, y se quita la demostración
- **THEN** 3.° A no cambia y esa cuenta sigue activa

#### Scenario: Carga y retiro a la vez
- **WHEN** se quita la demostración mientras una carga, primera o repetida, está en curso
- **THEN** al terminar las dos, o la demostración queda completa o queda quitada: ninguna cuenta demo queda activa sin su sección ni una sección demo queda con su cuenta inactiva

#### Scenario: Cuenta demo inactiva
- **WHEN** se intenta ingresar con una cuenta demo después de quitar la demostración
- **THEN** no se ingresa

#### Scenario: Volver a quitar
- **WHEN** se quita la demostración cuando ya no hay
- **THEN** no cambia nada y el comando lo dice

### Requirement: Descartar una sección del piloto
Un comando del equipo SHALL borrar la asistencia, las jornadas y los estudiantes de una sección indicada del año ABIERTO, con confirmación explícita, y dejar la sección con su docente. Es el camino para borrar una lista con registros, que «Vaciar lista» no permite.

#### Scenario: Sección descartada
- **WHEN** se descarta 3.° A, que tiene 28 estudiantes y 12 jornadas, con la confirmación
- **THEN** 3.° A queda sin estudiantes ni jornadas, con la misma docente, y el comando dice cuántos estudiantes, jornadas y estados borró

#### Scenario: Sin confirmar
- **WHEN** se descarta una sección sin la confirmación
- **THEN** el comando dice qué borraría, termina con un error y no borra nada

#### Scenario: Sección de un año cerrado
- **WHEN** se descarta una sección de un año CERRADO
- **THEN** el comando termina con un error y no borra nada

### Requirement: Bimestres de ejemplo
La carga de la demostración SHALL crear, en la misma transacción, los 4 bimestres del año ABIERTO con fechas de ejemplo dentro del año, en orden y sin cruzarse, solo si la institución está organizada en bimestres y el año aún no tiene periodos. Si no, no toca los periodos y su resumen lo dice. Quitar la demostración no borra los periodos: viven en el año real y el Administrador los corrige.

#### Scenario: Año sin periodos
- **WHEN** se carga la demostración en una institución organizada en bimestres cuyo año ABIERTO no tiene periodos
- **THEN** el año queda con los bimestres 1 a 4, el resumen los nombra y queda una entrada PERIODOS_CONFIGURADOS con el usuario vacío

#### Scenario: Año con periodos
- **WHEN** el año ABIERTO ya tiene periodos y se carga la demostración
- **THEN** los periodos no cambian

#### Scenario: Organización vacía o en trimestres
- **WHEN** la institución no tiene organización de periodos, o está en trimestres, y se carga la demostración
- **THEN** se cargan las secciones demo, no se crea ningún periodo y el resumen dice que los periodos se configuran en el panel

#### Scenario: Volver a cargar sin periodos
- **WHEN** la demostración ya estaba cargada, el año no tiene periodos y la institución está en bimestres
- **THEN** solo se crean los 4 bimestres

#### Scenario: Quitar la demostración
- **WHEN** se quita la demostración
- **THEN** los periodos del año siguen como estaban

### Requirement: Competencias marcadas de ejemplo
La carga de la demostración SHALL marcar, en la misma transacción, todas las competencias que la tutora puede marcar en los periodos ya empezados (los pasados y el vigente) de cada sección demo, solo en los periodos que la sección aún no tiene marcados. Quitar la demostración y descartar una sección borran las marcas de esas secciones. No cambia qué áreas están a cargo del docente de curso.

#### Scenario: Demostración con periodos
- **WHEN** se carga la demostración el 15 de octubre (entre el bimestre 3 y el 4) en un año con los 4 bimestres de ejemplo
- **THEN** cada sección demo tiene marcadas sus competencias en los bimestres 1, 2 y 3, y ninguna en el 4

#### Scenario: Sin periodos
- **WHEN** la institución está en trimestres sin periodos y se carga la demostración
- **THEN** no se crea ninguna marca

#### Scenario: Volver a cargar
- **WHEN** la demostración ya estaba cargada sin marcas y se vuelve a cargar
- **THEN** solo se crean las marcas de los periodos ya empezados

#### Scenario: Quitar la demostración
- **WHEN** se quita la demostración
- **THEN** las secciones demo quedan sin marcas, y las marcas de las demás secciones no cambian

#### Scenario: Descartar una sección
- **WHEN** se descarta 3.° A, que tiene marcas en el bimestre 2
- **THEN** 3.° A queda sin marcas y el comando lo cuenta en lo que borró

### Requirement: Notas al quitar o descartar
Quitar la demostración y descartar una sección SHALL borrar, en la misma transacción y antes que los estudiantes, las notas de esas secciones, y decir cuántas borró. La carga de la demostración no crea notas.

#### Scenario: Quitar la demostración con notas
- **WHEN** una cuenta demo guardó notas en su sección y se quita la demostración
- **THEN** la sección demo queda sin notas ni estudiantes, el comando cuenta las notas borradas, y las notas de las demás secciones no cambian

#### Scenario: Descartar una sección con notas
- **WHEN** se descarta 3.° A, que tiene 40 notas en el bimestre 2
- **THEN** 3.° A queda sin notas ni estudiantes y el comando dice que borró 40 notas

#### Scenario: Cargar la demostración
- **WHEN** se carga la demostración
- **THEN** ninguna sección demo tiene notas
