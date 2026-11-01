# Spec Delta

## MODIFIED Requirements

### Requirement: Acceso a las competencias de su sección
La pantalla de competencias de una sección SHALL abrirse solo para la docente de esa sección en el año ABIERTO. La sección de otra docente o de un año CERRADO responde como página inexistente; otro rol va a su pantalla de inicio y una visita sin sesión va al ingreso. Las mismas reglas valen para cada guardado. Desde US-020 se llega desde la hoja de notas, con el botón «Competencias».

#### Scenario: Sección de otra docente
- **WHEN** una docente abre o guarda las competencias de una sección que no es suya
- **THEN** recibe "página no encontrada" y no se guarda nada

#### Scenario: Sección de un año cerrado
- **WHEN** la docente abre o guarda las competencias de su sección de un año CERRADO
- **THEN** recibe "página no encontrada" y no se guarda nada

#### Scenario: Otro rol
- **WHEN** un usuario de la dirección abre las competencias de una sección
- **THEN** llega a su propia pantalla de inicio

#### Scenario: Sin sesión
- **WHEN** alguien sin sesión abre las competencias de una sección
- **THEN** llega al ingreso y no ve ninguna competencia

#### Scenario: Portada sin cambios
- **WHEN** la docente abre su portada
- **THEN** no hay un enlace directo a las competencias: la tarjeta Notas lleva a la hoja de notas, y desde ella se llega a las competencias

#### Scenario: Desde la hoja de notas
- **WHEN** la tutora, en la hoja de notas del bimestre 2, pulsa «Competencias»
- **THEN** llega a las competencias del bimestre 2

### Requirement: No desmarcar una competencia con notas
Una competencia que ya tiene notas registradas en el periodo SHALL quedar marcada, con su motivo junto a ella. Si la tutora intenta desmarcarla, la marca no cambia y se muestra «La competencia tiene notas registradas en este periodo». Un guardado que la quita no guarda nada. Tiene notas si al menos un estudiante de la sección tiene una nota de esa competencia en el periodo.

#### Scenario: Caso de error
- **WHEN** la tutora intenta desmarcar una competencia que ya tiene notas registradas en el bimestre
- **THEN** la competencia sigue marcada y se muestra el mensaje "La competencia tiene notas registradas en este periodo"

#### Scenario: Guardado que la quita
- **WHEN** llega un guardado del bimestre sin una competencia que tiene notas en él
- **THEN** no se guarda nada del envío

#### Scenario: Una sola nota basta
- **WHEN** la tutora guardó en la hoja de notas una sola «A» de C1 de Matemática en el bimestre 3 y abre las competencias del bimestre 3
- **THEN** C1 de Matemática aparece marcada y bloqueada con su motivo

#### Scenario: Notas de otro periodo
- **WHEN** C1 de Matemática tiene notas en el bimestre 2 y ninguna en el 3
- **THEN** la tutora puede desmarcarla en el bimestre 3

### Requirement: Competencias obligatorias en el último periodo
En el periodo de número mayor del año ABIERTO, las competencias que la tutora puede marcar y que no tienen ninguna nota de la sección en ningún periodo del año SHALL aparecer marcadas y bloqueadas, con «Debe tener nivel al cerrar el año», y se guardan con las demás aunque el envío no las traiga (RN-005). No cuentan como un cambio de la tutora. Las áreas del docente de curso quedan fuera.

#### Scenario: Flujo alternativo válido
- **WHEN** la tutora abre el bimestre 4 y 5 de sus competencias no tienen notas en los bimestres 1 a 3
- **THEN** esas 5 aparecen marcadas y bloqueadas con «Debe tener nivel al cerrar el año», para que todas terminen el año con un nivel de logro

#### Scenario: Marcada antes, sin notas
- **WHEN** una competencia se marcó en el bimestre 2 pero nunca se registró una nota suya, y la tutora abre el bimestre 4
- **THEN** esa competencia aparece marcada y bloqueada con «Debe tener nivel al cerrar el año»

#### Scenario: Guardado sin las obligatorias
- **WHEN** llega un guardado del bimestre 4 que no trae esas 5 competencias
- **THEN** las 5 quedan guardadas junto con las del envío

#### Scenario: Otro periodo
- **WHEN** la tutora abre el bimestre 3
- **THEN** ninguna competencia aparece bloqueada por el cierre del año

## ADDED Requirements

### Requirement: Ir a las notas del periodo
La pantalla de competencias SHALL ofrecer «Registrar notas de B*n*» (o T*n*), que abre la hoja de notas del periodo visible y del área de la que vino la tutora. Si llega desde la hoja porque el periodo no tiene competencias guardadas, muestra arriba «B*n* aún no tiene competencias confirmadas» / «Confirma las que trabajaste para empezar a registrar los niveles de logro.». Con cambios sin guardar, el enlace abre «¿Salir sin guardar?».

#### Scenario: Volver a las notas
- **WHEN** la tutora, que vino desde la hoja de Matemática, elige el bimestre 2 en Competencias y pulsa «Registrar notas de B2»
- **THEN** ve la hoja de Matemática del bimestre 2

#### Scenario: Llega sin competencias confirmadas
- **WHEN** la hoja de notas la lleva a Competencias porque el bimestre 3 no tiene competencias guardadas
- **THEN** ve «B3 aún no tiene competencias confirmadas» y, tras guardar, «Registrar notas de B3» abre la hoja del bimestre 3

#### Scenario: Con cambios sin guardar
- **WHEN** la tutora desmarcó una competencia sin guardar y pulsa «Registrar notas de B3»
- **THEN** ve «¿Salir sin guardar?» antes de salir
