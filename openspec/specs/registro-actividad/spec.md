# registro-actividad Specification

## Purpose
Registro de actividad del sistema: cada operación que crea, modifica o elimina datos deja una entrada con su usuario, fecha y operación del catálogo, guardada en la misma transacción, como base de los indicadores de adopción y de la atención de incidencias.

## Requirements

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
- **THEN** tiene estas operaciones, y solo las de asistencia, NOTAS_GUARDADAS y SESION_ENVIADA cuentan para KPI-01:

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
| Notas | PLANTILLA_SIAGIE_COMPLETADA, EQUIVALENCIA_SECCION_BORRADA | No |
| Sesiones de aprendizaje | SESION_ENVIADA | Sí |
| Sesiones de aprendizaje | SESION_VISTA, SESION_DESCARGADA, SESION_COMPARTIDA, SESION_DESCOMPARTIDA, SESION_ELIMINADA | No |
| Material de referencia | SESION_REFERENCIA_CARGADA, SESION_REFERENCIA_EDITADA, SESION_REFERENCIA_ELIMINADA | No |
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
Toda operación que crea, modifica o elimina datos MUST registrarse con una operación del catálogo, sea desde las pantallas, desde el panel de administración o desde un comando de consola. La historia que introduce una operación nueva agrega su operación al catálogo. Ver o consultar no se registra, salvo tres casos: un intento sin permiso (la petición de una docente a una sección o un estudiante que no son suyos, o el intento de eliminar, compartir o dejar de compartir una sesión ajena, deja una entrada INTENTO_SIN_PERMISO; spec `acceso-secciones`), la primera vez que una docente abre la página de una sesión ajena (SESION_VISTA) y cada entrega del archivo de una sesión (SESION_DESCARGADA). Iniciar y cerrar sesión sí se registran (para atender incidencias), pero no cuentan para KPI-01.

#### Scenario: Una lectura no deja entrada
- **WHEN** una docente abre la portada, la lista de estudiantes, la asistencia de hoy, «Mis sesiones», el repositorio (con o sin búsqueda) o la página de una sesión propia, sin cambiar nada
- **THEN** no queda ninguna entrada de actividad

#### Scenario: Un intento sin permiso deja entrada
- **WHEN** una docente abre la lista de estudiantes de una sección de otra docente
- **THEN** queda una entrada INTENTO_SIN_PERMISO con su usuario, aunque no se cambió nada

#### Scenario: Intento sobre una sesión ajena
- **WHEN** una docente envía, con una petición armada a mano, eliminar, compartir o dejar de compartir una sesión de una colega
- **THEN** queda una entrada INTENTO_SIN_PERMISO con su usuario, la ruta y el motivo, y la sesión no cambia

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

### Requirement: Marcas de competencias
Cada guardado de las competencias de un periodo que cambia algo SHALL dejar una entrada COMPETENCIAS_MARCADAS con la docente, la sección, el número del periodo y los identificadores de las competencias agregadas y quitadas, en la misma transacción. Un guardado que no cambia nada no deja entrada. Las obligatorias del último periodo cuentan como agregadas.

#### Scenario: Primer guardado del periodo
- **WHEN** la tutora guarda por primera vez el bimestre 3 con 20 competencias
- **THEN** queda una entrada COMPETENCIAS_MARCADAS con su usuario, la sección, el periodo 3, las 20 como agregadas y ninguna quitada

#### Scenario: Corrección
- **WHEN** la tutora desmarca una competencia del bimestre 3 ya guardado y vuelve a guardar
- **THEN** queda una entrada con esa competencia como quitada y ninguna agregada

#### Scenario: Sin cambios
- **WHEN** la tutora guarda el bimestre sin haber cambiado nada
- **THEN** no queda una entrada nueva

### Requirement: Guardado de notas
Cada guardado de la hoja de notas de un área que crea o cambia alguna nota SHALL dejar una entrada NOTAS_GUARDADAS con la docente, la sección, el área, el número del periodo, cuántas notas se crearon y los pares (estudiante, competencia) de las notas cambiadas, sin niveles ni conclusiones (RN-015), en la misma transacción. Un guardado que no cambia nada no deja entrada.

#### Scenario: Primer guardado del área
- **WHEN** la tutora guarda por primera vez Matemática del bimestre 3 con 30 notas
- **THEN** queda una entrada NOTAS_GUARDADAS con su usuario, la sección, el área, el periodo 3, 30 creadas y ninguna cambiada

#### Scenario: Corrección
- **WHEN** la tutora cambia una nota de «B» a «A» y guarda
- **THEN** queda una entrada con 0 creadas y el par de ese estudiante y esa competencia como cambiado, sin «B» ni «A» en el detalle

#### Scenario: Solo cambia la conclusión
- **WHEN** la tutora corrige solo el texto de la conclusión de una «C» y guarda
- **THEN** la entrada lista ese par como cambiado, sin el texto

#### Scenario: Sin cambios
- **WHEN** la tutora guarda la hoja sin haber cambiado nada, o el mismo guardado llega dos veces
- **THEN** no queda una entrada nueva

### Requirement: Envío de sesiones
Cada sesión guardada SHALL dejar una entrada SESION_ENVIADA con la docente, la sesión como entidad (su UUID) y en el detalle solo si se compartió (`{"compartida": true}` o `false`), sin título, propósito ni nombre del archivo, en la misma transacción. Un envío repetido de la misma sesión no deja otra entrada.

#### Scenario: Sesión enviada sin compartir
- **WHEN** la docente envía una sesión sin compartir
- **THEN** queda una entrada SESION_ENVIADA con su usuario, la entidad `sesion`, el UUID de la sesión y el detalle `{"compartida": false}`

#### Scenario: Sesión compartida
- **WHEN** la docente envía una sesión y acepta compartirla
- **THEN** el detalle de la entrada es `{"compartida": true}`, sin el título ni el nombre del archivo

#### Scenario: Envío rechazado o repetido
- **WHEN** un envío no se guarda por un dato inválido, o llega otra vez una sesión ya guardada
- **THEN** no queda una entrada nueva

### Requirement: Operaciones sobre sesiones
Compartir, dejar de compartir y eliminar una sesión SHALL dejar, en la misma transacción, una entrada SESION_COMPARTIDA, SESION_DESCOMPARTIDA o SESION_ELIMINADA con la docente y la sesión como entidad (su UUID); la de eliminar lleva en el detalle solo si estaba compartida. Ningún detalle lleva el título, el propósito, el texto ni el nombre del archivo. Una petición que no cambia nada no deja entrada.

#### Scenario: Eliminar
- **WHEN** la autora elimina una sesión compartida
- **THEN** queda una entrada SESION_ELIMINADA con su usuario, la entidad `sesion`, el UUID y el detalle `{"compartida": true}`, y la entrada SESION_ENVIADA de esa sesión sigue en el registro

#### Scenario: Compartir y dejar de compartir
- **WHEN** la autora deja de compartir una sesión y luego la comparte otra vez
- **THEN** quedan una entrada SESION_DESCOMPARTIDA y una SESION_COMPARTIDA con el UUID de la sesión

#### Scenario: Sin cambio
- **WHEN** llega la petición de dejar de compartir una sesión que ya no está compartida, o de eliminar una que ya no existe
- **THEN** no queda una entrada nueva

### Requirement: Vistas y descargas de sesiones
La primera vez que una docente abre la página de una sesión ajena SHALL quedar una entrada SESION_VISTA con su usuario y el UUID de la sesión; las siguientes veces y las de la autora no dejan entrada. Cada entrega del archivo (Descargar o Ver), también a la autora, SHALL dejar una entrada SESION_DESCARGADA con el detalle `{"modo": "descargar"}` o `{"modo": "ver"}` y si la sesión es propia (`"propia": true` o `false`). Ninguna cuenta para KPI-01.

#### Scenario: Primera vista
- **WHEN** una colega abre por primera vez la página de una sesión compartida
- **THEN** queda una entrada SESION_VISTA con su usuario y el UUID de la sesión

#### Scenario: Vista repetida o de la autora
- **WHEN** la misma colega vuelve a abrir la página, o la abre la autora
- **THEN** no queda una entrada nueva

#### Scenario: Descarga
- **WHEN** una colega descarga una sesión y la autora la abre con «Ver»
- **THEN** quedan dos entradas SESION_DESCARGADA: `{"modo": "descargar", "propia": false}` y `{"modo": "ver", "propia": true}`

#### Scenario: Descarga rechazada
- **WHEN** alguien pide la descarga de una sesión que no está disponible para ella
- **THEN** no queda una entrada SESION_DESCARGADA

#### Scenario: Solo ver no activa
- **WHEN** una docente participante, en una semana, solo abre sesiones del repositorio y las descarga
- **THEN** no cuenta como activa en esa semana (KPI-01)

### Requirement: Plantilla del SIAGIE completada
Cada plantilla completada y devuelta SHALL dejar una entrada PLANTILLA_SIAGIE_COMPLETADA con el usuario de la dirección, la sección como entidad y, en el detalle, solo el número del periodo, el año, los cuatro conteos (encontrados, no encontrados, faltantes y reemplazadas) y si se guardó una equivalencia en ese paso, sin nombres de estudiantes, niveles, conclusiones, nombre del archivo ni nombre de la sección del SIAGIE (RN-015). Guardar la equivalencia y la entrada van en la misma transacción. Un archivo rechazado, una elección cancelada o un periodo sin notas no dejan entrada.

#### Scenario: Plantilla completada
- **WHEN** la dirección completa la plantilla del bimestre 3 de 2.º B con 26 encontrados, 2 no encontrados, 3 faltantes y 4 reemplazadas
- **THEN** queda una entrada PLANTILLA_SIAGIE_COMPLETADA con su usuario, la entidad `seccion`, el id de 2.º B y el detalle `{"periodo": 3, "anio": 2026, "encontrados": 26, "no_encontrados": 2, "faltantes": 3, "reemplazadas": 4, "equivalencia": false}`

#### Scenario: Con equivalencia nueva
- **WHEN** la dirección elige 2.º B para TRIUNFADORES y se completa la plantilla
- **THEN** el detalle dice `"equivalencia": true` y no lleva «TRIUNFADORES»

#### Scenario: Sin entrada
- **WHEN** el archivo no corresponde a la plantilla, la dirección cancela la elección de sección o el periodo no tiene notas
- **THEN** no queda entrada PLANTILLA_SIAGIE_COMPLETADA

### Requirement: Equivalencia de sección borrada
Borrar una equivalencia desde «¿No es esta sección?» SHALL dejar, en la misma transacción, una entrada EQUIVALENCIA_SECCION_BORRADA con el usuario de la dirección, la sección de la I.E. como entidad y, en el detalle, solo el año y el grado, sin el código ni el nombre de la sección del SIAGIE. Un borrado que no encuentra la equivalencia no deja entrada.

#### Scenario: Equivalencia borrada
- **WHEN** la dirección borra la equivalencia de TRIUNFADORES con 2.º B de 2026
- **THEN** queda una entrada EQUIVALENCIA_SECCION_BORRADA con su usuario, la entidad `seccion`, el id de 2.º B y el detalle `{"anio": 2026, "grado": 2}`

#### Scenario: Borrado repetido
- **WHEN** llega otra vez el borrado de la misma equivalencia
- **THEN** no queda una entrada nueva
