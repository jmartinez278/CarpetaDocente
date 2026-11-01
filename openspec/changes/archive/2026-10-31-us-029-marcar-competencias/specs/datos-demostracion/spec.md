# Spec Delta

## ADDED Requirements

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
