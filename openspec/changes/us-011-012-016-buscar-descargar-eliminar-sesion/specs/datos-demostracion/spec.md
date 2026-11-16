# Spec Delta

## ADDED Requirements

### Requirement: Sesiones de ejemplo
Cargar la demostración SHALL crear sesiones de aprendizaje de las cuentas demo, con archivos PDF y Word válidos y texto ficticio, repartidas en varios grados y áreas y en varios días: la mayoría compartidas, al menos una sin compartir y al menos un PDF sin texto. Volver a cargar MUST NOT duplicarlas. No dejan entradas SESION_ENVIADA ni cuentan en los indicadores.

#### Scenario: Demostración cargada
- **WHEN** se carga la demostración y una docente demo abre el repositorio
- **THEN** ve sesiones compartidas de varios grados y áreas, en PDF y en Word, con las primeras líneas de su texto, y puede buscarlas por una palabra de su texto

#### Scenario: Archivos válidos
- **WHEN** una docente demo descarga una sesión de ejemplo en PDF y otra en Word
- **THEN** los dos archivos se abren en su programa y no contienen datos reales

#### Scenario: Volver a cargar
- **WHEN** se carga la demostración otra vez
- **THEN** hay las mismas sesiones de ejemplo, sin duplicados ni archivos de más

#### Scenario: Indicadores
- **WHEN** el Administrador abre «Indicadores por semana» con la demostración cargada
- **THEN** las sesiones de ejemplo no cuentan en «sesiones cargadas»

### Requirement: Sesiones al quitar la demostración
Quitar la demostración SHALL eliminar todas las sesiones cuya autora es una cuenta demo, con sus archivos, con la misma regla de borrado que usa la docente al eliminar, y las vistas que las cuentas demo dejaron en sesiones reales. Las sesiones de cuentas reales MUST NOT cambiar.

#### Scenario: Quitar la demostración con sesiones
- **WHEN** se quita la demostración con la confirmación
- **THEN** no queda ninguna sesión de una cuenta demo ni su archivo en el almacenamiento, y el resumen del comando dice cuántas sesiones borró

#### Scenario: Sesión que una docente demo envió a mano
- **WHEN** una cuenta demo envió una sesión desde la pantalla y luego se quita la demostración
- **THEN** esa sesión y su archivo también se eliminan

#### Scenario: Sesiones reales intactas
- **WHEN** una docente real tiene una sesión compartida que una cuenta demo abrió, y se quita la demostración
- **THEN** la sesión y su archivo siguen, y su total de colegas que la vieron ya no cuenta a la cuenta demo
