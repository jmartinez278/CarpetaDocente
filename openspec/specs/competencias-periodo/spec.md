# competencias-periodo Specification

## Purpose
Marcas de las competencias que la tutora desarrolló con su sección en cada periodo, para que el registro de notas le pida solo esas y para que todas terminen el año con un nivel de logro (RF-029, RN-005).

## Requirements

### Requirement: Acceso a las competencias de su sección
La pantalla de competencias de una sección SHALL abrirse solo para la docente de esa sección en el año ABIERTO. La sección de otra docente o de un año CERRADO responde como página inexistente; otro rol va a su pantalla de inicio y una visita sin sesión va al ingreso. Las mismas reglas valen para cada guardado. No hay tarjeta ni enlace que lleve a la pantalla: se llega por su dirección hasta que US-020 la enlace.

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
- **THEN** la tarjeta Notas sigue en "Próximamente" y no hay enlace a las competencias

### Requirement: Competencias que ve la tutora
La pantalla SHALL mostrar, agrupadas por área y en el orden del SIAGIE, las competencias activas de las áreas que la institución trabaja, transversales incluidas (RN-008). Un área a cargo del docente de curso se muestra atenuada con «A cargo del docente de curso»: sus casillas están vacías y deshabilitadas, y no entra en los totales. Las áreas que la institución no trabaja y las competencias inactivas no aparecen.

#### Scenario: Catálogo de la I.E.
- **WHEN** la tutora abre las competencias en una institución que trabaja todas las áreas salvo Castellano como segunda lengua, con Educación Física e Inglés a cargo del docente de curso
- **THEN** ve 10 áreas en el orden del SIAGIE con 27 competencias, de las que puede marcar 21; Educación Física e Inglés dicen «A cargo del docente de curso»

#### Scenario: Competencia inactiva
- **WHEN** el Administrador desactiva una competencia de Matemática
- **THEN** la pantalla muestra 3 competencias de Matemática

#### Scenario: Área a cargo del docente de curso
- **WHEN** la tutora intenta marcar una competencia de Educación Física
- **THEN** la casilla no cambia y no se guarda ninguna marca de Educación Física

### Requirement: Solo la tutora marca sus áreas
Solo la docente de la sección SHALL marcar o desmarcar, y solo en las áreas que no están a cargo del docente de curso. Un guardado que trae una competencia fuera de ese conjunto no guarda nada. Guardar no crea ni borra marcas de competencias que la tutora no puede marcar (áreas del docente de curso o competencias que se desactivaron después de marcarse).

#### Scenario: Competencia de otra área en el guardado
- **WHEN** llega un guardado que incluye una competencia de Inglés, a cargo del docente de curso
- **THEN** no se guarda nada y la respuesta dice que el conjunto no es válido

#### Scenario: Marca que la tutora no ve
- **WHEN** una competencia de Matemática se marcó en el bimestre 2, luego se desactivó, y la tutora guarda el bimestre 2
- **THEN** la marca de esa competencia sigue guardada

### Requirement: Periodos que se marcan
Mientras el año esté ABIERTO, la tutora SHALL poder marcar el periodo vigente y los anteriores; los futuros se ven deshabilitados y un guardado para un periodo futuro no se guarda. La pantalla abre en el periodo vigente. Cada periodo muestra su nombre corto (B1 a B4, o T1 a T3), si es vigente, anterior o futuro, y sus fechas. La fecha de hoy es la de Lima.

#### Scenario: Abre en el vigente
- **WHEN** la tutora abre las competencias el 30 de octubre, con el bimestre 3 del 10 de agosto al 30 de octubre
- **THEN** la pantalla muestra el bimestre 3 como vigente, el 1 y el 2 como anteriores y el 4 como futuro y deshabilitado

#### Scenario: Corregir un periodo anterior
- **WHEN** la tutora elige el bimestre 1, desmarca una competencia y guarda
- **THEN** la marca del bimestre 1 se borra y las del bimestre 3 no cambian

#### Scenario: Guardado de un periodo futuro
- **WHEN** llega un guardado para el bimestre 4 antes de su fecha de inicio
- **THEN** no se guarda nada

### Requirement: Sin periodo para marcar
Sin periodos configurados, la pantalla SHALL decir «La dirección aún no configura los periodos», sin selector de periodos ni botón de guardar. En un hueco entre periodos, dice «Hoy no hay un periodo vigente» y ofrece los periodos ya pasados, sin ninguno elegido. Antes del primer periodo, dice «Hoy no hay un periodo vigente» y la fecha en que empieza el primero, sin periodos que elegir.

#### Scenario: Sin periodos
- **WHEN** el año ABIERTO no tiene periodos y la tutora abre las competencias
- **THEN** ve «La dirección aún no configura los periodos» y ningún botón de guardar

#### Scenario: Vacaciones
- **WHEN** la tutora abre las competencias el 1 de agosto, entre el bimestre 2 y el 3
- **THEN** ve «Hoy no hay un periodo vigente», puede elegir el bimestre 1 o el 2, y el 3 y el 4 están deshabilitados

#### Scenario: Antes del primer periodo
- **WHEN** la tutora abre las competencias el 2 de marzo y el bimestre 1 empieza el 9 de marzo
- **THEN** ve «Hoy no hay un periodo vigente» con la fecha de inicio del bimestre 1, y ningún periodo se puede elegir

### Requirement: Estado inicial del periodo
Si la sección no tiene marcas en un periodo, la pantalla SHALL abrirlo con todas las competencias que la tutora puede marcar ya marcadas, para que confirme o desmarque. Nada se guarda hasta que pulsa «Guardar». Si el periodo ya tiene marcas, muestra esas.

#### Scenario: Periodo sin marcas
- **WHEN** la tutora abre el bimestre 3, que no tiene marcas
- **THEN** ve las 21 competencias marcadas, el aviso de que no están guardadas, y en la base no hay marcas del bimestre 3

#### Scenario: Periodo con marcas
- **WHEN** la tutora abre el bimestre 2, que tiene 18 marcas guardadas
- **THEN** ve marcadas esas 18 y las otras 3 sin marcar

### Requirement: Guardar las competencias del periodo
«Guardar» SHALL guardar, en un solo envío y todo o nada, el conjunto completo de las competencias marcadas del periodo visible, con todas sus áreas: crea las marcas nuevas y borra las desmarcadas. Repetir el mismo envío no cambia nada. Un conjunto vacío no se guarda y se muestra «Marca al menos una competencia para guardar.». Si las competencias que la tutora puede marcar cambiaron desde que abrió la pantalla, no se guarda nada y se muestra «Las competencias enviadas no son válidas. Recarga la página.».

#### Scenario: Camino ideal
- **WHEN** la tutora, con el bimestre 3 vigente, deja marcadas solo las competencias de Matemática y de Comunicación que trabajó y pulsa «Guardar»
- **THEN** el bimestre 3 de su sección queda con esas 7 competencias como desarrolladas, que son las que el registro de notas le pedirá en ese periodo

#### Scenario: Guardar desde otra área en el celular
- **WHEN** la tutora desmarca una competencia de Arte y Cultura, pasa a Personal Social con la cápsula y pulsa «Guardar»
- **THEN** se guarda el conjunto de todas las áreas del bimestre, incluida la desmarca de Arte y Cultura

#### Scenario: Envío repetido
- **WHEN** el mismo guardado llega dos veces
- **THEN** las marcas son las mismas que tras el primero y no hay marcas repetidas

#### Scenario: Dos guardados a la vez
- **WHEN** dos pestañas de la tutora guardan el mismo bimestre con conjuntos distintos al mismo tiempo
- **THEN** queda guardado uno de los dos conjuntos completo, sin mezclarlos y sin error

#### Scenario: Conjunto vacío
- **WHEN** la tutora desmarca todas las competencias y pulsa «Guardar»
- **THEN** no se guarda nada y ve «Marca al menos una competencia para guardar.»

#### Scenario: Catálogo cambiado al guardar
- **WHEN** el Administrador reactiva una competencia que estaba marcada en el bimestre 2 mientras la tutora tiene la pantalla abierta sin ella, y la tutora desmarca otra y pulsa «Guardar»
- **THEN** no se guarda nada, la marca de la competencia reactivada sigue y ve «Las competencias enviadas no son válidas. Recarga la página.»

### Requirement: No desmarcar una competencia con notas
Una competencia que ya tiene notas registradas en el periodo SHALL quedar marcada, con su motivo junto a ella. Si la tutora intenta desmarcarla, la marca no cambia y se muestra «La competencia tiene notas registradas en este periodo». Un guardado que la quita no guarda nada.

#### Scenario: Caso de error
- **WHEN** la tutora intenta desmarcar una competencia que ya tiene notas registradas en el bimestre
- **THEN** la competencia sigue marcada y se muestra el mensaje "La competencia tiene notas registradas en este periodo"

#### Scenario: Guardado que la quita
- **WHEN** llega un guardado del bimestre sin una competencia que tiene notas en él
- **THEN** no se guarda nada del envío

### Requirement: Competencias obligatorias en el último periodo
En el periodo de número mayor del año ABIERTO, las competencias que la tutora puede marcar y que no se marcaron en ningún periodo anterior SHALL aparecer marcadas y bloqueadas, con «Debe tener nivel al cerrar el año», y se guardan con las demás aunque el envío no las traiga (RN-005). No cuentan como un cambio de la tutora. Las áreas del docente de curso quedan fuera.

#### Scenario: Flujo alternativo válido
- **WHEN** la tutora abre el bimestre 4 y 5 de sus competencias no se marcaron en los bimestres 1 a 3
- **THEN** esas 5 aparecen marcadas y bloqueadas con «Debe tener nivel al cerrar el año», para que todas terminen el año con un nivel de logro

#### Scenario: Guardado sin las obligatorias
- **WHEN** llega un guardado del bimestre 4 que no trae esas 5 competencias
- **THEN** las 5 quedan guardadas junto con las del envío

#### Scenario: Otro periodo
- **WHEN** la tutora abre el bimestre 3
- **THEN** ninguna competencia aparece bloqueada por el cierre del año

### Requirement: Marcado en el celular y en la PC
En el celular la pantalla SHALL mostrar un área a la vez, con una cápsula de flechas anterior y siguiente, la posición («1 de 10») y un selector para ir a cualquier área; las flechas no dan la vuelta. «Guardar» queda fijo abajo con el total del periodo («B3 · 20 de 21 en total»). Desde 960 px muestra la lista completa y el panel lateral «Tu selección» con el total y el guardado.

#### Scenario: Cápsula de áreas
- **WHEN** en un celular de 360 px la tutora toca la flecha siguiente desde Arte y Cultura
- **THEN** ve la siguiente área del orden del SIAGIE, la posición pasa a «2 de 10» y sus marcas de Arte y Cultura se conservan

#### Scenario: Extremo de la cápsula
- **WHEN** la tutora está en la última área
- **THEN** la flecha siguiente está deshabilitada

#### Scenario: PC
- **WHEN** la tutora abre la pantalla a 1280 px
- **THEN** ve todas las áreas en una lista y el panel «Tu selección» con el total y «Guardar»

### Requirement: Borradores por periodo
Los cambios sin guardar de cada periodo SHALL conservarse durante la visita al cambiar de área o de periodo, sin interrumpir. El botón de un periodo con cambios sin guardar lo dice. «Deshacer cambios» devuelve el periodo visible a lo guardado (o a todo marcado, si no tiene marcas), sin contar las competencias obligatorias como cambio.

#### Scenario: Cambiar de periodo con cambios
- **WHEN** la tutora desmarca una competencia en el bimestre 3, pasa al 2 y vuelve al 3
- **THEN** la competencia sigue desmarcada y el botón del bimestre 3 dice que tiene cambios sin guardar

#### Scenario: Deshacer en el último periodo
- **WHEN** la tutora abre el bimestre 4 con competencias obligatorias y no cambia nada
- **THEN** no aparece «Deshacer cambios»

### Requirement: Salir sin guardar
Con cambios sin guardar en algún periodo, salir de la pantalla por un enlace o botón del aplicativo SHALL abrir el diálogo «¿Salir sin guardar?», que nombra los periodos pendientes, con «Seguir editando» (con el foco) y «Salir sin guardar». Escape o «Seguir editando» conservan los cambios. Recargar o cerrar la pestaña muestra el aviso del navegador. Sin cambios pendientes, no hay pregunta.

#### Scenario: Salir con cambios
- **WHEN** la tutora tiene cambios sin guardar en el bimestre 2 y el 3 y toca un enlace que sale de la pantalla
- **THEN** ve «¿Salir sin guardar?» con los bimestres 2 y 3, y el foco está en «Seguir editando»

#### Scenario: Salir sin guardar
- **WHEN** en el diálogo pulsa «Salir sin guardar»
- **THEN** sale sin guardar nada y sin otro aviso del navegador

#### Scenario: Recargar con cambios
- **WHEN** la tutora recarga la página con cambios sin guardar
- **THEN** el navegador muestra su aviso de salida

### Requirement: Estado del guardado
La pantalla SHALL decir si el periodo visible está sin guardar, con cambios, guardando o guardado, y anunciar el guardado al lector de pantalla. Si el guardado falla, muestra junto a «Guardar» «No se pudo guardar» y «Tus cambios siguen aquí. Reintenta.», y conserva el borrador; un guardado posterior quita el aviso. Si la sesión venció, lo dice y ofrece volver a ingresar.

#### Scenario: Guardado
- **WHEN** la tutora pulsa «Guardar» y el guardado termina
- **THEN** la pantalla dice que el bimestre está guardado y el lector de pantalla lo anuncia

#### Scenario: Falla la red
- **WHEN** la tutora pulsa «Guardar» sin conexión
- **THEN** ve «No se pudo guardar» y «Tus cambios siguen aquí. Reintenta.» junto a «Guardar», y sus marcas no cambian en pantalla

#### Scenario: Sesión vencida
- **WHEN** la sesión venció y la tutora pulsa «Guardar»
- **THEN** no se guarda nada y la pantalla le dice que vuelva a ingresar

### Requirement: Competencias accesibles y sin desplazamiento horizontal
La pantalla SHALL no tener infracciones graves de axe-core en ambos temas, a 360 y a 1280 px, ni desplazamiento horizontal desde 320 px. Cada fila de competencia es pulsable entera, con al menos 44 px de alto; una competencia bloqueada recibe el foco y explica su motivo al intentar cambiarla. La pantalla funciona en Slow 4G (RNF-002).

#### Scenario: Axe en ambos temas
- **WHEN** se analiza la pantalla con axe-core en tema claro y oscuro, a 360 y 1280 px, con marcas, con bloqueos, sin periodos y en vacaciones
- **THEN** no hay infracciones graves

#### Scenario: Teclado en una competencia bloqueada
- **WHEN** la tutora llega con Tab a una competencia obligatoria y pulsa Espacio
- **THEN** la marca no cambia y se anuncia «Debe tener nivel al cerrar el año»

#### Scenario: Sin desplazamiento horizontal
- **WHEN** la pantalla se abre a 320 y 360 px
- **THEN** la página no se desplaza horizontalmente
