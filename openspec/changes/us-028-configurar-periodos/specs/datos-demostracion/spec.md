# Spec Delta

## ADDED Requirements

### Requirement: Bimestres de ejemplo
La carga de la demostración SHALL crear, en la misma transacción, los 4 bimestres del año ABIERTO con fechas de ejemplo dentro del año, en orden y sin cruzarse, solo si la institución está organizada en bimestres y el año aún no tiene periodos. Si no, no toca los periodos y su resumen lo dice. Quitar la demostración no borra los periodos: viven en el año real y el Administrador los corrige.

#### Scenario: Año sin periodos
- **WHEN** se carga la demostración en una institución organizada en bimestres cuyo año ABIERTO no tiene periodos
- **THEN** el año queda con los bimestres 1 a 4, el resumen los nombra y queda una entrada PERIODOS_CONFIGURADOS con el usuario vacío

#### Scenario: Año con periodos
- **WHEN** el año ABIERTO ya tiene periodos y se carga la demostración
- **THEN** los periodos no cambian

#### Scenario: Organización vacía o en trimestres
- **WHEN** la institución no tiene organización de periodos, o está en trimestres, y se carga la demostración
- **THEN** se cargan las secciones demo, no se crea ningún periodo y el resumen dice que los periodos se configuran en el panel

#### Scenario: Volver a cargar sin periodos
- **WHEN** la demostración ya estaba cargada, el año no tiene periodos y la institución está en bimestres
- **THEN** solo se crean los 4 bimestres

#### Scenario: Quitar la demostración
- **WHEN** se quita la demostración
- **THEN** los periodos del año siguen como estaban
