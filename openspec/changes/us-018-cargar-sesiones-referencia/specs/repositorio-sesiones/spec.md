# Spec Delta

## MODIFIED Requirements

### Requirement: Repositorio de la institución
«Repositorio» SHALL listar solo las sesiones compartidas de la institución de la docente, incluidas las suyas y el material de referencia de su institución, de la más reciente a la más antigua, con el título de resultados («8 sesiones compartidas»; con filtros, «3 sesiones»). La lista muestra 20 y «Ver más» agrega las siguientes. Una sesión no compartida o de otra institución MUST NOT aparecer.

#### Scenario: Compartidas de la institución
- **WHEN** en la institución hay 3 sesiones compartidas (una de la docente) y 2 no compartidas de colegas
- **THEN** la docente ve las 3 compartidas y el título «3 sesiones compartidas»

#### Scenario: Otra institución
- **WHEN** otra institución tiene sesiones compartidas
- **THEN** no aparecen ni cuentan en el repositorio de la docente

#### Scenario: Una sola
- **WHEN** hay una sola sesión compartida
- **THEN** el título dice «1 sesión compartida»

#### Scenario: Repositorio vacío
- **WHEN** nadie de la institución ha compartido una sesión
- **THEN** la docente ve «Comparte una de tus sesiones», con un enlace que lleva a «Mis sesiones»

#### Scenario: Con material de referencia
- **WHEN** en la institución hay 2 sesiones compartidas por docentes y 3 de referencia, y otra institución tiene 1 de referencia
- **THEN** la docente ve las 5 de su institución, el título «5 sesiones compartidas» y la pestaña «Repositorio 5»

## ADDED Requirements

### Requirement: Material de referencia en las listas
Una sesión de referencia SHALL mostrarse en el repositorio con la misma tarjeta, pero con «Material de referencia» en el lugar de la autora y sus grados como rango («3.º–5.º grado»). El filtro de grado MUST encontrarla con cualquier grado de su rango, y el conteo por área la cuenta una vez. No aparece en «Mis sesiones» de nadie.

#### Scenario: Tarjeta
- **WHEN** se lista «Contamos y agrupamos objetos», de 3.º a 5.º grado, Matemática, cargada el 10 de noviembre
- **THEN** la tarjeta muestra el título, «3.º–5.º grado · Matemática» y «Material de referencia · 10 nov», sin el nombre de una persona

#### Scenario: Un solo grado
- **WHEN** la sesión de referencia es solo de 2.º grado
- **THEN** la tarjeta dice «2.º grado · …», como la de una docente

#### Scenario: Filtrar por un grado del rango
- **WHEN** la docente filtra por 4.º grado
- **THEN** ve la sesión de referencia de 3.º a 5.º, y no la ve si filtra por 6.º

#### Scenario: Conteo por área
- **WHEN** hay una sesión de referencia de Matemática de 3.º a 5.º y ningún filtro de grado
- **THEN** Matemática suma 1, no 3

#### Scenario: No está en Mis sesiones
- **WHEN** la docente abre «Mis sesiones»
- **THEN** no ve ninguna sesión de referencia y su contador no las cuenta
