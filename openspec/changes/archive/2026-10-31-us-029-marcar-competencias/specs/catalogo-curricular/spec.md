# Spec Delta

## MODIFIED Requirements

### Requirement: Áreas que trabaja cada institución
Cada institución SHALL tener una fila por área que dice si la trabaja (RN-007), y nunca dos para la misma área. Las instituciones que existen al migrar y las que se crean después reciben las 11 filas: todas «se trabaja», salvo Castellano como segunda lengua, que aparece en el formato del SIAGIE pero no se llena. Desde US-029, cada fila dice además si el área está «a cargo del docente de curso» (al migrar y al crear la institución, no): la tutora no marca sus competencias.

#### Scenario: Institución existente al migrar
- **WHEN** se migra una base que ya tiene una institución
- **THEN** la institución tiene 11 áreas: 10 que se trabajan y Castellano como segunda lengua que no se trabaja, y ninguna a cargo del docente de curso

#### Scenario: Institución nueva
- **WHEN** el Administrador crea una institución
- **THEN** nace con las mismas 11 áreas y las mismas marcas

#### Scenario: Área repetida en la institución
- **WHEN** se intenta guardar una segunda fila de la misma área para la misma institución
- **THEN** no se guarda

### Requirement: Mantenimiento del catálogo en el panel
Solo el Administrador SHALL ver el catálogo en el panel de administración. Ahí cambia el orden de un área, el orden y la marca «activa» de una competencia, y las marcas «se trabaja» y «a cargo del docente de curso» de un área de su institución. El código, el nombre, las marcas de transversal y de exoneración no se editan, y nada del catálogo se agrega ni se borra desde el panel (RN-023).

#### Scenario: Desactivar una competencia
- **WHEN** el Administrador desmarca «activa» en una competencia y guarda
- **THEN** la competencia queda inactiva y sigue existiendo

#### Scenario: Área a cargo del docente de curso
- **WHEN** el Administrador marca «a cargo del docente de curso» en Educación Física de su institución, desde la lista o desde la ficha, y guarda
- **THEN** la marca queda guardada y queda una entrada CATALOGO_EDITADO con el nombre del campo

#### Scenario: Sin borrar
- **WHEN** el Administrador abre un área, una competencia o un área de su institución en el panel
- **THEN** no hay acción para borrarla, ni sola ni en lote

#### Scenario: Sin agregar
- **WHEN** el Administrador abre la lista de áreas, competencias o áreas de la institución
- **THEN** no hay botón para agregar

#### Scenario: Campos fijos
- **WHEN** el Administrador abre un área en el panel
- **THEN** el código, el nombre y las marcas de transversal y de exoneración se ven, pero no se pueden cambiar

#### Scenario: Otro rol
- **WHEN** una cuenta de Docente o de Dirección abre el catálogo en el panel
- **THEN** llega a su pantalla de inicio y no ve el catálogo
