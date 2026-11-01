# Spec Delta

## ADDED Requirements

### Requirement: Notas al quitar o descartar
Quitar la demostración y descartar una sección SHALL borrar, en la misma transacción y antes que los estudiantes, las notas de esas secciones, y decir cuántas borró. La carga de la demostración no crea notas.

#### Scenario: Quitar la demostración con notas
- **WHEN** una cuenta demo guardó notas en su sección y se quita la demostración
- **THEN** la sección demo queda sin notas ni estudiantes, el comando cuenta las notas borradas, y las notas de las demás secciones no cambian

#### Scenario: Descartar una sección con notas
- **WHEN** se descarta 3.° A, que tiene 40 notas en el bimestre 2
- **THEN** 3.° A queda sin notas ni estudiantes y el comando dice que borró 40 notas

#### Scenario: Cargar la demostración
- **WHEN** se carga la demostración
- **THEN** ninguna sección demo tiene notas
