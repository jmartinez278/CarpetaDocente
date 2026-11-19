# Spec Delta

## MODIFIED Requirements

### Requirement: Entidad Institución
El sistema SHALL guardar instituciones educativas con nombre obligatorio, código modular opcional y único, anexo (un número de 0 a 9, 0 por defecto), organización de periodos opcional limitada a BIMESTRE o TRIMESTRE, y fecha de creación automática (documento 11, sección 3.1). El código modular y el anexo son los que reconocen la plantilla de notas del SIAGIE de la institución (spec `plantilla-notas-siagie`); el Administrador los edita en el panel.

#### Scenario: Institución válida
- **WHEN** se registra una institución solo con su nombre
- **THEN** queda guardada con su fecha de creación, anexo 0 y sin código modular ni organización de periodos

#### Scenario: Código modular repetido
- **WHEN** se registra una segunda institución con el mismo código modular que otra existente
- **THEN** la base de datos rechaza el registro

#### Scenario: Organización de periodos no permitida
- **WHEN** se intenta guardar una institución con una organización de periodos distinta de BIMESTRE o TRIMESTRE
- **THEN** la base de datos rechaza el registro

#### Scenario: Anexo fuera de rango
- **WHEN** se intenta guardar una institución con anexo 10
- **THEN** la base de datos rechaza el registro
