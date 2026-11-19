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

## ADDED Requirements

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
