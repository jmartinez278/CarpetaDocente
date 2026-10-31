# Spec Delta

## MODIFIED Requirements

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
| Periodos | PERIODOS_CONFIGURADOS, PERIODO_EDITADO | No |
| Secciones | SECCION_CREADA, SECCION_EDITADA, SECCION_ASIGNADA, SECCION_LIBERADA | No |
| Estudiantes | ESTUDIANTES_IMPORTADOS, ESTUDIANTE_AGREGADO, ESTUDIANTE_EDITADO, ESTUDIANTE_QUITADO, LISTA_VACIADA | No |
| Asistencia | REGISTRO_ASISTENCIA, ASISTENCIA_CAMBIADA, JORNADA_COMPLETA | Sí |
| Notas | COMPETENCIAS_MARCADAS | No |
| Catálogo y piloto | CATALOGO_EDITADO, DEMO_CARGADA, DEMO_QUITADA, SECCION_DESCARTADA | No |
| Permisos | INTENTO_SIN_PERMISO (reservada para US-004) | No |
| Registro | REGISTRO_EXPORTADO | No |

#### Scenario: Operación fuera del catálogo
- **WHEN** se intenta guardar una entrada con una operación que no está en el catálogo
- **THEN** el sistema la rechaza y no guarda la entrada ni la operación

#### Scenario: Cada operación tiene su prueba
- **WHEN** corre la suite de pruebas
- **THEN** cada operación del catálogo, salvo la reservada, la genera al menos una prueba que hace la operación real

## ADDED Requirements

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
