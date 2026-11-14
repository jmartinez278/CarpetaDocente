## MODIFIED Requirements

### Requirement: Periodo de la hoja
La hoja SHALL abrir en el periodo vigente, o en el periodo pedido si ya empezó; sin vigente, en el último periodo ya pasado. Arriba, un selector muestra cada periodo del año en romanos («I»–«IV», o «I»–«III» con trimestres) con su estado («Anterior», «Vigente», «Futuro») y marca el visible. Elegir otro periodo abre su hoja en la misma área, sin preguntar, y los cambios sin guardar de cada periodo siguen en el dispositivo; si el dispositivo no puede conservarlos, elegir otro periodo con cambios sin guardar abre «¿Salir sin guardar?» como cualquier salida. Un periodo futuro no se elige, no se abre ni se guarda. El acceso a Competencias abre las competencias del periodo visible. Los periodos se nombran en romanos en toda la hoja («IV bimestre», «Matemática · IV bimestre»).

#### Scenario: Abre en el vigente
- **WHEN** la tutora abre la hoja el 30 de octubre, con el bimestre 3 del 10 de agosto al 30 de octubre
- **THEN** el selector marca «III» con «Vigente» y ve las notas del bimestre 3

#### Scenario: Periodo anterior pedido
- **WHEN** la tutora vuelve desde Competencias con «Registrar notas del II bimestre»
- **THEN** el selector marca «II» con «Anterior» y ve las notas del bimestre 2

#### Scenario: Periodo futuro pedido
- **WHEN** la tutora pide el bimestre 4 antes de su fecha de inicio
- **THEN** ve el bimestre vigente

#### Scenario: Periodo futuro en el selector
- **WHEN** la tutora abre la hoja el 30 de octubre, con el bimestre 4 aún por empezar
- **THEN** «IV» aparece con «Futuro» y no se puede elegir

#### Scenario: Elegir otro periodo
- **WHEN** la tutora, en la hoja de Matemática del bimestre 3, elige «II» en el selector
- **THEN** ve la hoja de Matemática del bimestre 2, sin el diálogo «¿Salir sin guardar?»

#### Scenario: Cambiar de periodo conserva el borrador
- **WHEN** la tutora escribe una nota en Matemática del bimestre 3, elige «II» y luego vuelve a «III»
- **THEN** su nota del bimestre 3 sigue en la hoja como cambio sin guardar

#### Scenario: Cambiar de periodo sin almacenamiento
- **WHEN** el navegador no permite guardar en el dispositivo y la tutora, con una nota sin guardar en Matemática del bimestre 3, elige «II»
- **THEN** ve «¿Salir sin guardar?» con «Matemática · III bimestre», y con «Seguir editando» sigue en el bimestre 3 con su nota

#### Scenario: Guardado de un periodo futuro
- **WHEN** llega un guardado para el bimestre 4 antes de su fecha de inicio
- **THEN** no se guarda nada

### Requirement: Sin periodo vigente
Sin periodos configurados, la hoja SHALL decir «La dirección aún no configura los periodos», sin áreas ni «Guardar». Antes del primer periodo dice «Hoy no hay un periodo vigente» y la fecha en que empieza el primero, sin hoja. En un hueco entre periodos dice «Hoy no hay un periodo vigente» y abre el último periodo ya pasado, que se puede editar.

#### Scenario: Sin periodos
- **WHEN** el año ABIERTO no tiene periodos y la tutora abre la hoja
- **THEN** ve «La dirección aún no configura los periodos» y ningún botón «Guardar»

#### Scenario: Vacaciones
- **WHEN** la tutora abre la hoja el 1 de agosto, entre el bimestre 2 y el 3
- **THEN** ve «Hoy no hay un periodo vigente», el selector marca «II» con «Anterior» y ve las notas del bimestre 2, que puede corregir

#### Scenario: Antes del primer periodo
- **WHEN** la tutora abre la hoja el 2 de marzo y el bimestre 1 empieza el 9 de marzo
- **THEN** ve «Hoy no hay un periodo vigente» con «El I bimestre empieza el 9 de marzo.» y ninguna hoja

### Requirement: Periodo sin competencias marcadas
Si la sección no tiene guardada ninguna competencia que la tutora marca en el periodo, la hoja SHALL llevarla a Competencias de ese periodo, con el aviso «<romano> aún no tiene competencias confirmadas» / «Confirma las que trabajaste para empezar a registrar los niveles de logro.».

#### Scenario: Bimestre sin marcas
- **WHEN** la tutora abre la hoja del bimestre 3 y ninguna competencia del bimestre 3 está guardada
- **THEN** llega a Competencias en el bimestre 3 con «III aún no tiene competencias confirmadas»

### Requirement: Áreas de la hoja
La hoja SHALL mostrar en una tira, en el orden del SIAGIE, las áreas que la institución trabaja, y una hoja por área. La tira se desplaza en horizontal dentro de su propio contenedor, con píldoras de 44 px como mínimo; la página no se desplaza. El área activa queda dentro del tramo visible de la tira, y el acceso a Competencias queda fijo fuera del tramo que se desplaza. Abre en el área pedida o, si no, en la primera que la tutora marca con competencias marcadas en el periodo. Cambiar de área no pierde lo digitado.

#### Scenario: Cambiar de área
- **WHEN** la tutora escribe una nota en Matemática y toca la píldora Comunicación
- **THEN** ve la hoja de Comunicación, y al volver a Matemática su nota sigue allí sin guardar

#### Scenario: Área activa a la vista
- **WHEN** en un celular de 360 px la tutora abre la hoja en Personal Social, que en el orden del SIAGIE queda fuera del primer tramo de la tira
- **THEN** la píldora Personal Social se ve entera en la tira y el acceso a Competencias sigue a la vista

#### Scenario: Área con cambios sin guardar
- **WHEN** Matemática tiene cambios sin guardar y la tutora está en Comunicación
- **THEN** la píldora Matemática muestra un punto y el lector de pantalla la lee con «Cambios sin guardar»

#### Scenario: Área del docente de curso
- **WHEN** la tutora toca Inglés, a cargo del docente de curso
- **THEN** la píldora se ve atenuada y la hoja dice «Esta área la registra el docente de curso», sin celdas ni «Guardar»

#### Scenario: Área sin competencias marcadas
- **WHEN** la tutora abre Educación Religiosa y ninguna de sus competencias está marcada en el bimestre 3, aunque otras áreas sí
- **THEN** ve «No hay competencias marcadas» y el enlace «Ir a Competencias», sin celdas ni «Guardar»

### Requirement: Nivel en el celular
En el celular, tocar una celda SHALL abrir un panel inferior con el estudiante, la competencia, los niveles AD · A · B · C en botones de 44 px como mínimo, la conclusión si el nivel es B o C, y «Siguiente ↓», que pasa al estudiante siguiente de la misma competencia. «Siguiente ↓» avanza también si la celda queda en B o C sin una conclusión de 10 a 500 caracteres: esa celda queda señalada con «Falta conclusión» y el guardado sigue rechazándola.

#### Scenario: Panel de la celda
- **WHEN** en un celular de 360 px la tutora toca la celda C2 de un estudiante, elige «A» y pulsa «Siguiente ↓»
- **THEN** la celda dice «A» y el panel muestra al estudiante siguiente en C2

#### Scenario: Siguiente con una B sin conclusión
- **WHEN** en un celular de 360 px la tutora elige «B» para un estudiante en C1, no escribe la conclusión y pulsa «Siguiente ↓»
- **THEN** el panel muestra al estudiante siguiente en C1, y al volver a la hoja la celda del primero dice «B» con «Falta conclusión»

### Requirement: Conclusión en B y C
Un nivel B o C SHALL llevar una conclusión descriptiva de 10 a 500 caracteres; AD y A no la piden. En la PC, elegir B o C abre un recuadro junto a la celda, sin oscurecer la pantalla y entero dentro de la ventana: si no cabe a la derecha de la celda, se abre a su izquierda. «Listo», Escape o un clic fuera lo cierran, conservan lo escrito y devuelven el foco a la celda. Un icono junto a la celda (o Alt+Enter) abre la conclusión; al pasar el puntero o llevar el foco al icono se ve una vista previa de la conclusión, que sigue visible mientras el puntero o el foco estén en el icono o en ella, sin temporizador, y Escape la cierra. Si la conclusión falta o es corta, la celda lo señala. Al pasar a AD o A, la conclusión se borra al guardar.

#### Scenario: Camino ideal (US-021)
- **WHEN** la tutora registra el nivel «C» para un estudiante, escribe la conclusión descriptiva y guarda
- **THEN** el sistema guarda el nivel y la conclusión

#### Scenario: Conclusión en B
- **WHEN** la tutora elige «B» en una celda
- **THEN** se abre el recuadro «Rellena la conclusión» junto a la celda, con «De 10 a 500 caracteres.»

#### Scenario: Recuadro en la última columna
- **WHEN** en una PC de 1280 px la tutora elige «B» en un área con una sola competencia
- **THEN** el recuadro se ve entero dentro de la ventana, junto a la celda

#### Scenario: Vista previa de la conclusión
- **WHEN** en la PC la tutora lleva el foco al icono de una conclusión anotada
- **THEN** ve el comienzo de la conclusión, y al pulsar Escape la vista previa se cierra y el foco sigue en el icono

#### Scenario: Nivel A sin conclusión
- **WHEN** la tutora elige «A» en una celda
- **THEN** no se abre ningún recuadro y la celda queda con «A»

#### Scenario: De B a A
- **WHEN** una nota guardada en «B» con su conclusión pasa a «A» y la tutora guarda
- **THEN** queda guardada «A» sin conclusión

#### Scenario: Conclusión de un trasladado
- **WHEN** la tutora abre la conclusión de un estudiante trasladado
- **THEN** la lee sin poder editarla

### Requirement: Rellenar vacías
La hoja del área SHALL ofrecer un solo «Rellenar vacías», en todos los anchos, con la elección de la competencia, solo con AD o A, y una confirmación que dice cuántas celdas se rellenarán. Rellena solo las celdas vacías de estudiantes activos en esa competencia y queda como borrador hasta guardar.

#### Scenario: Rellenar con A
- **WHEN** la tutora pulsa «Rellenar vacías», elige C1, que tiene 3 celdas vacías y 5 llenas, elige «A» y confirma
- **THEN** las 3 vacías dicen «A», las 5 llenas no cambian y nada se guarda hasta pulsar «Guardar»

#### Scenario: Solo AD o A
- **WHEN** la tutora abre «Rellenar vacías»
- **THEN** solo puede elegir AD o A

#### Scenario: Elegir la competencia
- **WHEN** en una PC de 1280 px la tutora pulsa «Rellenar vacías» en Matemática
- **THEN** puede elegir entre C1, C2, C3 y C4, y la confirmación cuenta las celdas vacías de la elegida

### Requirement: Salir sin guardar
Con cambios sin guardar en alguna hoja, salir de la pantalla por un enlace o botón del aplicativo SHALL abrir «¿Salir sin guardar?», que nombra las áreas pendientes con su periodo («Matemática · III bimestre») y dice que quedan en el dispositivo, con «Seguir editando» (con el foco) y «Salir sin guardar». Si la salida es «Cerrar sesión», dice que se borrarán. Recargar o cerrar la pestaña muestra el aviso del navegador. Cambiar de área o de periodo no pregunta.

#### Scenario: Salir con cambios
- **WHEN** la tutora tiene cambios sin guardar en Matemática y Comunicación del bimestre 3 y toca «Competencias»
- **THEN** ve «¿Salir sin guardar?» con «Matemática · III bimestre» y «Comunicación · III bimestre», y el foco en «Seguir editando»

#### Scenario: Salir sin guardar
- **WHEN** en el diálogo pulsa «Salir sin guardar»
- **THEN** sale sin guardar, sin otro aviso del navegador, y el borrador sigue en el dispositivo

#### Scenario: Cerrar sesión con cambios
- **WHEN** la tutora con cambios sin guardar elige «Cerrar sesión»
- **THEN** el diálogo dice que los borradores se borrarán de este dispositivo

#### Scenario: Recargar con cambios
- **WHEN** la tutora recarga la página con cambios sin guardar
- **THEN** el navegador muestra su aviso de salida

### Requirement: Hoja accesible y sin desplazamiento horizontal de la página
La hoja SHALL no tener infracciones graves de axe-core en ambos temas ni desplazar la página en horizontal desde 320 px; sigue el patrón de rejilla para teclado y lector de pantalla, con áreas táctiles de 44 px en el celular. Cuando las competencias no caben a lo ancho, sus columnas se desplazan en horizontal dentro de la hoja: la columna del nombre queda fija y legible, la cabecera C1…Cn sigue a las columnas y una señal en el borde indica que hay más. La página tiene un solo desplazamiento vertical y la cabecera de la hoja queda a la vista al bajar. Funciona en Slow 4G con la hoja más grande.

#### Scenario: Axe en ambos temas
- **WHEN** se analiza con axe-core, en claro y oscuro, la hoja con notas y su panel, el rechazo al guardar y los diálogos a 360 px, y el recuadro y la vista previa de la conclusión a 1280 px
- **THEN** no hay infracciones graves

#### Scenario: Sin desplazamiento de la página
- **WHEN** la hoja de Personal Social, con 5 competencias, se abre a 320 y 360 px
- **THEN** la página no se desplaza en horizontal

#### Scenario: Columnas que no caben
- **WHEN** la hoja de Personal Social, con 5 competencias, se abre a 360 px y la tutora desplaza las columnas hasta C5
- **THEN** ve C5 y su cabecera alineadas, el nombre del estudiante sigue a la vista en su columna y la página no se desplazó

#### Scenario: Lector de pantalla en una celda
- **WHEN** la tutora llega con el teclado a una celda
- **THEN** el lector de pantalla lee el estudiante, la competencia y el nivel
