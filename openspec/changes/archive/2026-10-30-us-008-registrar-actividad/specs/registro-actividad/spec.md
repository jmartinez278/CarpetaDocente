## ADDED Requirements

### Requirement: Entrada de actividad
Cada entrada del registro de actividad SHALL guardar el usuario que hizo la operación (vacío si la hizo un comando de consola), la fecha y hora, la operación, la entidad afectada, su identificador y un detalle opcional. La entrada se guarda en la misma transacción que la operación: si una falla, no queda ninguna de las dos.

#### Scenario: Camino ideal (registro de asistencia)
- **GIVEN** un docente con la sesión iniciada
- **WHEN** registra la asistencia de una jornada
- **THEN** el sistema guarda una entrada de actividad con su usuario, la fecha, la hora y la operación "registro de asistencia" (`REGISTRO_ASISTENCIA`), con la entidad jornada y su identificador

#### Scenario: La operación falla
- **WHEN** una operación que se registra no llega a guardarse (por ejemplo, un toque de asistencia sobre un estudiante de otra sección)
- **THEN** no queda ninguna entrada de actividad de esa operación

#### Scenario: El registro falla
- **WHEN** la entrada de actividad no puede guardarse
- **THEN** la operación tampoco se guarda

#### Scenario: Comando de consola
- **WHEN** el Administrador corre `cargar_demo`, `quitar_demo`, `descartar_seccion` o `cargar_secciones`
- **THEN** queda la entrada de su operación con el usuario vacío

### Requirement: Catálogo cerrado de operaciones
La operación de una entrada MUST ser una del catálogo; cada operación del catálogo dice si cuenta para KPI-01.

#### Scenario: Catálogo de esta historia
- **WHEN** se consulta el catálogo
- **THEN** tiene estas operaciones, y solo las de asistencia cuentan para KPI-01:

| Grupo | Operaciones | Cuenta para KPI-01 |
|---|---|---|
| Sesión | INICIO_SESION, CIERRE_SESION | No |
| Cuentas | CUENTA_CREADA, CUENTA_EDITADA, CUENTA_DESACTIVADA | No |
| Institución y año | INSTITUCION_CREADA, INSTITUCION_EDITADA, ANIO_CREADO, ANIO_EDITADO | No |
| Secciones | SECCION_CREADA, SECCION_EDITADA, SECCION_ASIGNADA, SECCION_LIBERADA | No |
| Estudiantes | ESTUDIANTES_IMPORTADOS, ESTUDIANTE_AGREGADO, ESTUDIANTE_EDITADO, ESTUDIANTE_QUITADO, LISTA_VACIADA | No |
| Asistencia | REGISTRO_ASISTENCIA, ASISTENCIA_CAMBIADA, JORNADA_COMPLETA | Sí |
| Catálogo y piloto | CATALOGO_EDITADO, DEMO_CARGADA, DEMO_QUITADA, SECCION_DESCARTADA | No |
| Permisos | INTENTO_SIN_PERMISO (reservada para US-004) | No |
| Registro | REGISTRO_EXPORTADO | No |

#### Scenario: Operación fuera del catálogo
- **WHEN** se intenta guardar una entrada con una operación que no está en el catálogo
- **THEN** el sistema la rechaza y no guarda la entrada ni la operación

#### Scenario: Cada operación tiene su prueba
- **WHEN** corre la suite de pruebas
- **THEN** cada operación del catálogo, salvo la reservada, la genera al menos una prueba que hace la operación real

### Requirement: Toda escritura queda registrada
Toda operación que crea, modifica o elimina datos MUST registrarse con una operación del catálogo, sea desde las pantallas, desde el panel de administración o desde un comando de consola. La historia que introduce una operación nueva agrega su operación al catálogo. Ver o consultar no se registra. Iniciar y cerrar sesión sí se registran (para atender incidencias), pero no cuentan para KPI-01.

#### Scenario: Una lectura no deja entrada
- **WHEN** una docente abre la portada, la lista de estudiantes o la asistencia de hoy sin cambiar nada
- **THEN** no queda ninguna entrada de actividad

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

### Requirement: Cambios de asistencia
Cada cambio de estado de un estudiante en una jornada SHALL dejar una entrada ASISTENCIA_CAMBIADA con el identificador del estudiante, el estado anterior (vacío si no tenía), el estado nuevo, si cambió la nota de justificación y el origen (`toque` o `lote`). La jornada nueva deja REGISTRO_ASISTENCIA y, la primera vez que todos sus estudiantes activos quedan marcados, JORNADA_COMPLETA.

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

### Requirement: Detalle sin datos personales
El detalle de una entrada MUST NOT incluir nombres de estudiantes, sus notas ni el texto de una nota de justificación (RN-015); solo identificadores, códigos, cantidades y nombres de campos.

#### Scenario: Estudiante editado
- **WHEN** la docente corrige el nombre de un estudiante
- **THEN** la entrada ESTUDIANTE_EDITADO tiene el identificador del estudiante y no su nombre anterior ni el nuevo

#### Scenario: Justificación
- **WHEN** la docente escribe una nota de justificación
- **THEN** la entrada ASISTENCIA_CAMBIADA dice que la nota cambió, sin su texto

### Requirement: Registro de solo lectura
El registro de actividad MUST ser de solo lectura para todos los roles, incluido el Administrador: nadie agrega, edita ni borra entradas desde el panel, y el sistema rechaza modificar o borrar una entrada guardada.

#### Scenario: Caso de error (docente o dirección)
- **GIVEN** un docente o un usuario de la dirección
- **WHEN** intenta modificar o borrar una entrada del registro de actividad
- **THEN** el sistema no lo permite, porque el registro de actividad es de solo lectura para todos los roles

#### Scenario: Administrador en el panel
- **WHEN** el Administrador abre una entrada del registro en el panel
- **THEN** la ve sin campos editables y sin los botones de agregar, guardar ni eliminar, y un POST a esas rutas no cambia nada

#### Scenario: Desde el código
- **WHEN** se intenta guardar de nuevo o borrar una entrada ya guardada
- **THEN** el sistema lo rechaza y la entrada queda igual

### Requirement: Consulta en el panel
El Administrador SHALL consultar el registro en el panel, de la más reciente a la más antigua, con fecha y hora de Lima, usuario, operación, entidad e identificador, y filtrarlo por usuario, operación y rango de fechas.

#### Scenario: Filtrar
- **WHEN** el Administrador filtra por una docente, la operación ASISTENCIA_CAMBIADA y la semana pasada
- **THEN** ve solo las entradas que cumplen los tres filtros

### Requirement: Exportar el registro
El Administrador SHALL descargar en CSV (UTF-8) el registro con los filtros que tiene puestos (doc 08). La descarga deja una entrada REGISTRO_EXPORTADO con los filtros usados y la cantidad de filas. Solo el Administrador puede exportar.

#### Scenario: Exportar lo filtrado
- **WHEN** el Administrador exporta con un filtro de operación puesto
- **THEN** descarga un CSV con una fila por entrada filtrada (fecha y hora de Lima, usuario, operación, entidad, identificador y detalle) y queda una entrada REGISTRO_EXPORTADO

#### Scenario: Celda que parece fórmula
- **WHEN** un valor del CSV empieza con `=`, `+`, `-` o `@`
- **THEN** el CSV lo guarda como texto, de modo que una hoja de cálculo no lo ejecuta

#### Scenario: Otro rol
- **WHEN** una docente o un usuario de la dirección pide la exportación
- **THEN** no la obtiene

### Requirement: Conservación
Las entradas MUST sobrevivir al borrado de lo que registran: su identificador no depende de la tabla afectada, y el cierre del año (US-009) no borra el registro. El plazo final de conservación lo fija US-009.

#### Scenario: Sección descartada
- **WHEN** se descarta una sección del piloto con sus jornadas
- **THEN** las entradas de asistencia de esa sección siguen en el registro
