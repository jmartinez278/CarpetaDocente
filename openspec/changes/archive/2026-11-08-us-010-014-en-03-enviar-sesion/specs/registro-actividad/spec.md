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
| Catálogo y piloto | CATALOGO_EDITADO, DEMO_CARGADA, DEMO_QUITADA, SECCION_DESCARTADA | No |
| Permisos | INTENTO_SIN_PERMISO | No |
| Registro | REGISTRO_EXPORTADO | No |

#### Scenario: Operación fuera del catálogo
- **WHEN** se intenta guardar una entrada con una operación que no está en el catálogo
- **THEN** el sistema la rechaza y no guarda la entrada ni la operación

#### Scenario: Cada operación tiene su prueba
- **WHEN** corre la suite de pruebas
- **THEN** cada operación del catálogo la genera al menos una prueba que hace la operación real; ninguna queda reservada

## ADDED Requirements

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
