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
| Permisos | INTENTO_SIN_PERMISO (reservada para US-004) | No |
| Registro | REGISTRO_EXPORTADO | No |

#### Scenario: Operación fuera del catálogo
- **WHEN** se intenta guardar una entrada con una operación que no está en el catálogo
- **THEN** el sistema la rechaza y no guarda la entrada ni la operación

#### Scenario: Cada operación tiene su prueba
- **WHEN** corre la suite de pruebas
- **THEN** cada operación del catálogo, salvo la reservada, la genera al menos una prueba que hace la operación real

## ADDED Requirements

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
