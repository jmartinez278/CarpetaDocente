## MODIFIED Requirements

### Requirement: Periodos que se marcan
Mientras el año esté ABIERTO, la tutora SHALL poder marcar el periodo vigente y los anteriores; los futuros se ven deshabilitados y un guardado para un periodo futuro no se guarda. La pantalla abre en el periodo vigente. Cada periodo muestra su nombre en romanos (I a IV, o I a III) y, debajo, si es vigente, anterior o futuro. Sus fechas no se ven: van en el nombre accesible del botón, junto al nombre del periodo y su estado. Al elegir un periodo, el foco queda en su botón. La fecha de hoy es la de Lima.

#### Scenario: Abre en el vigente
- **WHEN** la tutora abre las competencias el 30 de octubre, con el bimestre 3 del 10 de agosto al 30 de octubre
- **THEN** la pantalla muestra el bimestre 3 como vigente, el 1 y el 2 como anteriores y el 4 como futuro y deshabilitado

#### Scenario: Nombres en romanos con las fechas para el lector
- **WHEN** la tutora abre las competencias con el bimestre 4 vigente, del 13 de octubre al 19 de diciembre
- **THEN** el selector muestra «I», «II», «III» e «IV» con su estado debajo, ninguna fecha a la vista, y el nombre accesible del botón del bimestre 4 es «IV bimestre, Vigente, del 13 de octubre al 19 de diciembre»

#### Scenario: Cambiar de periodo con el teclado
- **WHEN** la tutora llega con Tab al botón del bimestre 2 y pulsa Enter
- **THEN** la pantalla muestra el bimestre 2 y el foco sigue en su botón, no en el cuerpo de la página

#### Scenario: Corregir un periodo anterior
- **WHEN** la tutora elige el bimestre 1, desmarca una competencia y guarda
- **THEN** la marca del bimestre 1 se borra y las del bimestre 3 no cambian

#### Scenario: Guardado de un periodo futuro
- **WHEN** llega un guardado para el bimestre 4 antes de su fecha de inicio
- **THEN** no se guarda nada

### Requirement: Competencias obligatorias en el último periodo
En el periodo de número mayor del año ABIERTO, las competencias que la tutora puede marcar y que no tienen ninguna nota de la sección en ningún periodo del año SHALL aparecer marcadas y bloqueadas, con «Debe tener nivel al cerrar el año», y se guardan con las demás aunque el envío no las traiga (RN-005). No cuentan como un cambio de la tutora. Las áreas del docente de curso quedan fuera. En ese periodo, un aviso arriba de la lista dice «IV bimestre: último del año» (o «III trimestre: último del año») y «Las competencias que no marcaste en bimestres anteriores quedan marcadas: deben tener nivel al cerrar el año.».

#### Scenario: Flujo alternativo válido
- **WHEN** la tutora abre el bimestre 4 y 5 de sus competencias no tienen notas en los bimestres 1 a 3
- **THEN** esas 5 aparecen marcadas y bloqueadas con «Debe tener nivel al cerrar el año», para que todas terminen el año con un nivel de logro

#### Scenario: Aviso del último periodo
- **WHEN** la tutora abre el bimestre 4
- **THEN** ve el aviso «IV bimestre: último del año» con «Las competencias que no marcaste en bimestres anteriores quedan marcadas: deben tener nivel al cerrar el año.»

#### Scenario: Marcada antes, sin notas
- **WHEN** una competencia se marcó en el bimestre 2 pero nunca se registró una nota suya, y la tutora abre el bimestre 4
- **THEN** esa competencia aparece marcada y bloqueada con «Debe tener nivel al cerrar el año»

#### Scenario: Guardado sin las obligatorias
- **WHEN** llega un guardado del bimestre 4 que no trae esas 5 competencias
- **THEN** las 5 quedan guardadas junto con las del envío

#### Scenario: Otro periodo
- **WHEN** la tutora abre el bimestre 3
- **THEN** ninguna competencia aparece bloqueada por el cierre del año

### Requirement: Marcado en el celular y en la PC
Hasta 899 px la pantalla SHALL mostrar un área a la vez, con una cápsula de flechas anterior y siguiente, la posición («1 de 10») y un selector para ir a cualquier área; las flechas no dan la vuelta. «Guardar» queda fijo abajo, con el estado del guardado y el total del periodo («IV · 20 de 21 en total»), en lugar del panel lateral. Desde 900 px muestra la lista completa y el panel lateral «Tu selección», con el total escrito «20/21 para el IV bimestre» (el lector oye «20 de 21») y el guardado. Nunca se ven los dos a la vez.

#### Scenario: Cápsula de áreas
- **WHEN** en un celular de 360 px la tutora toca la flecha siguiente desde Arte y Cultura
- **THEN** ve la siguiente área del orden del SIAGIE, la posición pasa a «2 de 10» y sus marcas de Arte y Cultura se conservan

#### Scenario: Extremo de la cápsula
- **WHEN** la tutora está en la última área
- **THEN** la flecha siguiente está deshabilitada

#### Scenario: Total en el celular
- **WHEN** en un celular de 360 px la tutora tiene 20 de 21 competencias marcadas en el bimestre 4
- **THEN** la barra fija de abajo dice «IV · 20 de 21 en total» junto a «Guardar», y el panel «Tu selección» no se ve

#### Scenario: PC
- **WHEN** la tutora abre la pantalla a 1280 px con 20 de 21 competencias marcadas en el bimestre 4
- **THEN** ve todas las áreas en una lista y el panel «Tu selección» con «20/21 para el IV bimestre» y «Guardar», sin la barra fija de abajo

#### Scenario: Corte en 900 px
- **WHEN** la tutora abre la pantalla a 900 px y luego a 899 px
- **THEN** a 900 px ve la lista completa con el panel, y a 899 px un área a la vez con la cápsula

### Requirement: Competencias accesibles y sin desplazamiento horizontal
La pantalla, con el marco del rebrand, SHALL no tener infracciones graves de axe-core en su estado principal ni con «¿Salir sin guardar?» abierto, en ambos temas, a 360 px, ni desplazamiento horizontal desde 320 px. Cada fila de competencia es pulsable entera, con al menos 44 px de alto; una competencia bloqueada recibe el foco y explica su motivo al intentar cambiarla. La pantalla funciona en Slow 4G (RNF-002).

#### Scenario: Axe en ambos temas
- **WHEN** se analiza con axe-core, a 360 px y en tema claro y oscuro, la pantalla con el marco del rebrand en su estado principal y con «¿Salir sin guardar?» abierto
- **THEN** no hay infracciones graves

#### Scenario: Teclado en una competencia bloqueada
- **WHEN** la tutora llega con Tab a una competencia obligatoria y pulsa Espacio
- **THEN** la marca no cambia y se anuncia «Debe tener nivel al cerrar el año»

#### Scenario: Sin desplazamiento horizontal
- **WHEN** la pantalla se abre a 320 y 360 px
- **THEN** la página no se desplaza horizontalmente

### Requirement: Ir a las notas del periodo
La pantalla de competencias SHALL ofrecer «Registrar notas del IV bimestre» (con el periodo visible, o «del III trimestre»), que abre la hoja de notas del periodo visible y del área de la que vino la tutora. Si llega desde la hoja porque el periodo no tiene competencias guardadas, muestra arriba «IV aún no tiene competencias confirmadas» / «Confirma las que trabajaste para empezar a registrar los niveles de logro.». Con cambios sin guardar, el enlace abre «¿Salir sin guardar?».

#### Scenario: Volver a las notas
- **WHEN** la tutora, que vino desde la hoja de Matemática, elige el bimestre 2 en Competencias y pulsa «Registrar notas del II bimestre»
- **THEN** ve la hoja de Matemática del bimestre 2

#### Scenario: Llega sin competencias confirmadas
- **WHEN** la hoja de notas la lleva a Competencias porque el bimestre 3 no tiene competencias guardadas
- **THEN** ve «III aún no tiene competencias confirmadas» y, tras guardar, «Registrar notas del III bimestre» abre la hoja del bimestre 3

#### Scenario: Con cambios sin guardar
- **WHEN** la tutora desmarcó una competencia sin guardar y pulsa «Registrar notas del III bimestre»
- **THEN** ve «¿Salir sin guardar?» antes de salir
