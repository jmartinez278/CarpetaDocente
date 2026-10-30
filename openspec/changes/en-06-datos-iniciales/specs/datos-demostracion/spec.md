# Spec Delta

## Purpose

Datos ficticios para mostrar y probar el aplicativo sin datos reales de estudiantes (RN-018): secciones de demostración que el equipo carga y retira con un comando, y el descarte de lo cargado en una sección del piloto.

## ADDED Requirements

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
