# Spec Delta

## MODIFIED Requirements

### Requirement: Catálogo cerrado de operaciones
La operación de una entrada MUST ser una del catálogo; cada operación del catálogo dice si cuenta para KPI-01.

#### Scenario: Catálogo de esta historia
- **WHEN** se consulta el catálogo
- **THEN** tiene estas operaciones, y solo las de asistencia y NOTAS_GUARDADAS cuentan para KPI-01:

| Grupo | Operaciones | Cuenta para KPI-01 |
|---|---|---|
| Sesión | INICIO_SESION, CIERRE_SESION | No |
| Cuentas | CUENTA_CREADA, CUENTA_EDITADA, CUENTA_DESACTIVADA | No |
| Institución y año | INSTITUCION_CREADA, INSTITUCION_EDITADA, ANIO_CREADO, ANIO_EDITADO | No |
| Periodos | PERIODOS_CONFIGURADOS, PERIODO_EDITADO | No |
| Secciones | SECCION_CREADA, SECCION_EDITADA, SECCION_ASIGNADA, SECCION_LIBERADA | No |
| Estudiantes | ESTUDIANTES_IMPORTADOS, ESTUDIANTE_AGREGADO, ESTUDIANTE_EDITADO, ESTUDIANTE_QUITADO, LISTA_VACIADA | No |
| Asistencia | REGISTRO_ASISTENCIA, ASISTENCIA_CAMBIADA, JORNADA_COMPLETA | Sí |
| Notas | COMPETENCIAS_MARCADAS | No |
| Notas | NOTAS_GUARDADAS | Sí |
| Catálogo y piloto | CATALOGO_EDITADO, DEMO_CARGADA, DEMO_QUITADA, SECCION_DESCARTADA | No |
| Permisos | INTENTO_SIN_PERMISO | No |
| Registro | REGISTRO_EXPORTADO | No |

#### Scenario: Operación fuera del catálogo
- **WHEN** se intenta guardar una entrada con una operación que no está en el catálogo
- **THEN** el sistema la rechaza y no guarda la entrada ni la operación

#### Scenario: Cada operación tiene su prueba
- **WHEN** corre la suite de pruebas
- **THEN** cada operación del catálogo la genera al menos una prueba que hace la operación real; ninguna queda reservada

### Requirement: Toda escritura queda registrada
Toda operación que crea, modifica o elimina datos MUST registrarse con una operación del catálogo, sea desde las pantallas, desde el panel de administración o desde un comando de consola. La historia que introduce una operación nueva agrega su operación al catálogo. Ver o consultar no se registra, salvo un intento sin permiso: la petición de una docente a una sección o un estudiante que no son suyos deja una entrada INTENTO_SIN_PERMISO (spec `acceso-secciones`). Iniciar y cerrar sesión sí se registran (para atender incidencias), pero no cuentan para KPI-01.

#### Scenario: Una lectura no deja entrada
- **WHEN** una docente abre la portada, la lista de estudiantes o la asistencia de hoy sin cambiar nada
- **THEN** no queda ninguna entrada de actividad

#### Scenario: Un intento sin permiso deja entrada
- **WHEN** una docente abre la lista de estudiantes de una sección de otra docente
- **THEN** queda una entrada INTENTO_SIN_PERMISO con su usuario, aunque no se cambió nada

#### Scenario: Inicio y cierre de sesión
- **WHEN** una docente inicia sesión y luego la cierra con "Cerrar sesión"
- **THEN** quedan una entrada INICIO_SESION y una CIERRE_SESION con su usuario

#### Scenario: Cierre por inactividad
- **WHEN** la sesión se cierra por inactividad
- **THEN** queda una entrada CIERRE_SESION cuyo detalle dice que fue por inactividad

#### Scenario: Operación del panel
- **WHEN** el Administrador crea o edita una cuenta, una institución, un año escolar, una sección o el catálogo curricular desde el panel
- **THEN** queda una entrada con la operación que corresponde, su usuario y, en el detalle, los nombres de los campos que cambiaron (sin sus valores)

#### Scenario: Desactivar una cuenta
- **WHEN** el Administrador desmarca "activo" en la ficha de una cuenta
- **THEN** queda una entrada CUENTA_DESACTIVADA con esa cuenta

#### Scenario: Asignar y liberar una sección
- **WHEN** el Administrador elige un docente para una sección, cambia el docente o lo quita
- **THEN** queda una entrada SECCION_ASIGNADA (al elegir o cambiar) o SECCION_LIBERADA (al quitarlo), con los identificadores del docente anterior y del nuevo

#### Scenario: Ningún camino del panel escribe sin registrar
- **WHEN** se revisan los modelos que el panel deja crear, editar o borrar
- **THEN** cada uno registra su operación; el panel no permite borrar instituciones ni gestionar grupos

### Requirement: Detalle sin datos personales
El detalle de una entrada MUST NOT incluir nombres de estudiantes, sus notas ni el texto de una nota de justificación (RN-015); solo identificadores, códigos, cantidades y nombres de campos.

#### Scenario: Estudiante editado
- **WHEN** la docente corrige el nombre de un estudiante
- **THEN** la entrada ESTUDIANTE_EDITADO tiene el identificador del estudiante y no su nombre anterior ni el nuevo

#### Scenario: Justificación
- **WHEN** la docente escribe una nota de justificación
- **THEN** la entrada ASISTENCIA_CAMBIADA dice que la nota cambió, sin su texto

#### Scenario: Intento sin permiso
- **WHEN** una docente intenta abrir la hoja de notas de otra sección con una consulta en la dirección
- **THEN** la entrada INTENTO_SIN_PERMISO solo tiene la ruta sin la consulta y el motivo, sin nombres ni notas
