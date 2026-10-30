# Spec Delta

## Purpose

Catálogo de áreas y competencias de primaria tal como aparecen en el registro de notas del SIAGIE, y las áreas que trabaja cada institución, para que las notas, los periodos y las sesiones usen siempre los mismos bloques que la docente ve en el SIAGIE.

## ADDED Requirements

### Requirement: Áreas del SIAGIE al migrar
Al migrar una base de datos, SHALL existir las 11 áreas del registro de notas del SIAGIE (Currículo Nacional 2017, primaria), cada una con su código, su nombre con mayúsculas normales y su orden. Las dos competencias transversales son bloques propios. Migrar otra vez no duplica ni cambia nada. El código y el nombre de un área no se repiten.

#### Scenario: Catálogo cargado
- **WHEN** se migra una base de datos vacía
- **THEN** existen 11 áreas, en este orden: 0001 Arte y Cultura, 0002 Castellano como segunda lengua, 0003 Inglés como lengua extranjera, 0004 Ciencia y Tecnología, 0005 Comunicación, 031 Educación Física, 035 Educación Religiosa, 063 Matemática, 067 Personal Social, 0006 Se desenvuelve en entornos virtuales generados por las TIC y 0007 Gestiona su aprendizaje de manera autónoma

#### Scenario: Exonerables y transversales
- **WHEN** se revisan las áreas cargadas
- **THEN** solo Educación Física y Educación Religiosa admiten exoneración, y solo los bloques 0006 y 0007 son transversales

#### Scenario: Área repetida
- **WHEN** se intenta guardar un área con un código o un nombre que ya existe, por cualquier vía
- **THEN** no se guarda

#### Scenario: Carga idempotente
- **WHEN** la carga del catálogo se repite sobre una base que ya lo tiene, incluso con un orden editado en el panel
- **THEN** siguen existiendo 11 áreas y 30 competencias, y el orden editado no cambia

### Requirement: Competencias de la leyenda del SIAGIE
Cada área SHALL tener las competencias de la leyenda de su hoja del registro de notas del SIAGIE, con el texto de la leyenda y su orden 01…n, todas activas. Dentro de un área, el nombre de una competencia no se repite.

#### Scenario: Competencias por área
- **WHEN** se migra una base de datos vacía
- **THEN** hay 30 competencias: Arte y Cultura 2, Castellano como segunda lengua 3, Inglés 3, Ciencia y Tecnología 3, Comunicación 3, Educación Física 3, Educación Religiosa 2, Matemática 4, Personal Social 5 y una en cada bloque transversal

#### Scenario: Orden del SIAGIE y no del Anexo 03
- **WHEN** se listan las competencias de Arte y Cultura en orden
- **THEN** la 01 es "Aprecia de manera crítica manifestaciones artístico-culturales" y la 02 es "Crea proyectos desde los lenguajes artísticos"

#### Scenario: Texto completo de la leyenda
- **WHEN** se lee la competencia 01 de Comunicación
- **THEN** dice "Se comunica oralmente en su lengua materna"

#### Scenario: Competencia repetida en el área
- **WHEN** se intenta guardar una segunda competencia con el mismo nombre en la misma área
- **THEN** no se guarda

### Requirement: Áreas que trabaja cada institución
Cada institución SHALL tener una fila por área que dice si la trabaja (RN-007), y nunca dos para la misma área. Las instituciones que existen al migrar y las que se crean después reciben las 11 filas: todas «se trabaja», salvo Castellano como segunda lengua, que aparece en el formato del SIAGIE pero no se llena.

#### Scenario: Institución existente al migrar
- **WHEN** se migra una base que ya tiene una institución
- **THEN** la institución tiene 11 áreas: 10 que se trabajan y Castellano como segunda lengua que no se trabaja

#### Scenario: Institución nueva
- **WHEN** el Administrador crea una institución
- **THEN** nace con las mismas 11 áreas y la misma marca

#### Scenario: Área repetida en la institución
- **WHEN** se intenta guardar una segunda fila de la misma área para la misma institución
- **THEN** no se guarda

### Requirement: Mantenimiento del catálogo en el panel
Solo el Administrador SHALL ver el catálogo en el panel de administración. Ahí cambia el orden de un área, el orden y la marca «activa» de una competencia, y la marca «se trabaja» de un área de su institución. El código, el nombre, las marcas de transversal y de exoneración no se editan, y nada del catálogo se agrega ni se borra desde el panel (RN-023).

#### Scenario: Desactivar una competencia
- **WHEN** el Administrador desmarca «activa» en una competencia y guarda
- **THEN** la competencia queda inactiva y sigue existiendo

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
