# Spec Delta

## MODIFIED Requirements

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
| Sesiones de aprendizaje | SESION_ENVIADA | Sí |
| Sesiones de aprendizaje | SESION_VISTA, SESION_DESCARGADA, SESION_COMPARTIDA, SESION_DESCOMPARTIDA, SESION_ELIMINADA | No |
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

## ADDED Requirements

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
