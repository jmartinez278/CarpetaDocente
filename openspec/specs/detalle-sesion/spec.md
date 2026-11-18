# detalle-sesion Specification

## Purpose
Define la página de una sesión de aprendizaje para el rol Docente: quién puede verla, cómo se descarga o se abre su archivo, y lo que solo su autora puede hacer con ella: compartirla, dejar de compartirla y eliminarla (US-012, US-016).

## Requirements

### Requirement: Quién ve una sesión
La página de una sesión, su descarga y su vista MUST estar disponibles solo para su autora y, si está compartida, para cualquier Docente de la misma institución. En cualquier otro caso (eliminada, inexistente, ajena no compartida o de otra institución) el sistema SHALL mostrar «La sesión ya no está disponible» con «Volver a Sesiones», con la misma respuesta en todos, sin revelar cuál es el caso ni ningún dato de la sesión.

#### Scenario: Compartida de una colega
- **WHEN** una docente abre la página de una sesión compartida por una colega de su institución
- **THEN** ve la página de la sesión

#### Scenario: Propia sin compartir
- **WHEN** la autora abre la página de su sesión no compartida
- **THEN** ve la página de la sesión

#### Scenario: Ajena sin compartir
- **WHEN** una docente abre la dirección de una sesión no compartida de una colega
- **THEN** ve «La sesión ya no está disponible», sin el título ni la autora, igual que con una dirección que nunca existió

#### Scenario: Otra institución
- **WHEN** una docente abre la dirección de una sesión compartida en otra institución
- **THEN** ve «La sesión ya no está disponible»

#### Scenario: Dejó de compartirse
- **WHEN** una colega tenía abierta la lista del repositorio, la autora deja de compartir la sesión y la colega toca su tarjeta
- **THEN** la colega ve «La sesión ya no está disponible»

#### Scenario: Otro rol o sin sesión
- **WHEN** la dirección, el Administrador o una visita sin sesión abren la página, la descarga o la vista de una sesión
- **THEN** el sistema los lleva a su inicio o al ingreso y no entrega la página ni el archivo

### Requirement: Página de la sesión
La página SHALL mostrar las migas hacia Sesiones, «Sesión de aprendizaje · PDF» (o «Word»), el título, los chips de grado y área y, si lo está, «Compartida»; la autora, la fecha de envío, el formato y el tamaño del archivo; el propósito, si lo tiene; y la «Vista previa del texto» con la nota «Texto sin formato. Descarga el archivo para verlo tal como es.». Sin texto transcrito, en su lugar dice que la vista previa no está disponible y que puede descargar el archivo.

#### Scenario: Sesión con texto
- **WHEN** la docente abre «Leemos un cuento sobre la amistad», PDF de 142 KB, enviada el 5 de noviembre de 2026 por Bruno García Alarcón
- **THEN** ve «Sesión de aprendizaje · PDF», el título, «1.º grado», «Comunicación», «Bruno García Alarcón», «5 de noviembre de 2026», «PDF», «142 KB», el propósito y el texto transcrito, sin formato y con sus saltos de línea

#### Scenario: Sin propósito ni texto
- **WHEN** la sesión no tiene propósito y su archivo es un PDF escaneado
- **THEN** la página no muestra el bloque «Propósito» y, en la vista previa, dice que no está disponible y que puede descargar el archivo

#### Scenario: Migas
- **WHEN** la docente abre una sesión propia y luego una ajena
- **THEN** las migas de la propia llevan a «Mis sesiones» y las de la ajena a «Repositorio»

#### Scenario: Texto con marcas de HTML
- **WHEN** el título, el propósito o el texto transcrito contienen «<script>» u otras marcas
- **THEN** la página las muestra como texto y no las ejecuta

### Requirement: Descargar el archivo
«Descargar» SHALL ser un enlace del aplicativo que revisa el permiso en cada petición y entrega el archivo original, con su nombre original, como descarga. Si la sesión no está disponible para quien la pide, MUST NOT entregar el archivo y muestra «La sesión ya no está disponible».

#### Scenario: Camino ideal (sesión de otro docente)
- **GIVEN** una sesión publicada por otro docente
- **WHEN** el docente elige descargarla
- **THEN** el sistema entrega el archivo original para que lo adapte en su procesador de textos

#### Scenario: Flujo alternativo válido (sesión propia)
- **GIVEN** una sesión propia
- **WHEN** su autor elige descargarla
- **THEN** el sistema entrega el archivo, por ejemplo para subirlo al canal que indique la UGEL

#### Scenario: Caso de error (sesión eliminada)
- **GIVEN** una sesión que su autor eliminó del repositorio
- **WHEN** un docente intenta descargarla mediante un enlace guardado
- **THEN** el sistema no entrega el archivo y muestra el mensaje "La sesión ya no está disponible"

#### Scenario: Nombre original
- **WHEN** la docente descarga una sesión cuyo archivo se subió como «Sesión 3 – cuento ñandú.docx»
- **THEN** el archivo se guarda con ese nombre, con sus tildes y su ñ

#### Scenario: Enlace guardado de una sesión que dejó de compartirse
- **WHEN** una colega usa el enlace de descarga del aplicativo de una sesión que su autora dejó de compartir
- **THEN** el sistema no entrega el archivo y muestra «La sesión ya no está disponible»

### Requirement: Ver el PDF
Las sesiones en PDF SHALL tener además «Ver», que abre el archivo en una pestaña nueva del navegador, con el mismo permiso que «Descargar». Las sesiones en Word solo tienen «Descargar»; pedir la vista de una MUST NOT entregar el archivo.

#### Scenario: PDF
- **WHEN** la docente toca «Ver» en una sesión en PDF
- **THEN** el PDF se abre en una pestaña nueva, sin descargarse, y la página de la sesión sigue abierta

#### Scenario: Word
- **WHEN** la docente abre una sesión en Word
- **THEN** ve «Descargar» y no ve «Ver»

#### Scenario: Vista de un Word por su dirección
- **WHEN** alguien pide la dirección de la vista de una sesión en Word
- **THEN** el sistema no entrega el archivo

### Requirement: Colegas que la vieron
El sistema SHALL contar las personas distintas que abrieron la página de una sesión, sin contar a su autora, y mostrar el total solo a la autora, en la página y en «Mis sesiones» («La vieron 3 colegas», «La vio 1 colega»); con 0 no se muestra. MUST NOT mostrarse quiénes fueron, ni las descargas.

#### Scenario: Primera visita de una colega
- **WHEN** una colega abre por primera vez la página de una sesión compartida
- **THEN** el total de esa sesión sube en 1

#### Scenario: La misma colega otra vez
- **WHEN** esa colega vuelve a abrir la página, hoy u otro día
- **THEN** el total no cambia

#### Scenario: La autora
- **WHEN** la autora abre la página de su sesión
- **THEN** el total no cambia y, si es 3, ve «La vieron 3 colegas», sin nombres

#### Scenario: Nadie la vio
- **WHEN** ninguna colega ha abierto la sesión
- **THEN** la autora no ve ningún texto de vistas, ni en la página ni en «Mis sesiones»

#### Scenario: Una colega no ve el total
- **WHEN** una colega abre la página de una sesión ajena
- **THEN** no ve cuántas personas la vieron

### Requirement: Tarjeta «Tu sesión»
En una sesión propia, la página SHALL mostrar la tarjeta «Tu sesión» con el estado real de la sesión («Compartida con tus colegas y enviada a la dirección.» o «Enviada a la dirección. Solo tú y la dirección la ven.»), «Dejar de compartir» o «Compartir», y «Eliminar» con la nota «También se retira de la dirección.». En una sesión ajena MUST NOT aparecer la tarjeta ni esas acciones.

#### Scenario: Propia compartida
- **WHEN** la autora abre su sesión compartida
- **THEN** ve «Tu sesión», «Compartida con tus colegas y enviada a la dirección.», «Dejar de compartir» y «Eliminar»

#### Scenario: Propia sin compartir
- **WHEN** la autora abre su sesión no compartida
- **THEN** ve «Enviada a la dirección. Solo tú y la dirección la ven.», «Compartir» y «Eliminar», y la página no lleva el chip «Compartida»

#### Scenario: Ajena
- **WHEN** una colega abre la sesión
- **THEN** no ve «Tu sesión», «Compartir», «Dejar de compartir» ni «Eliminar»

### Requirement: Dejar de compartir
«Dejar de compartir» SHALL sacar la sesión del repositorio sin pedir confirmación: sigue enviada a la dirección, solo la ve su autora y conserva la fecha en que aceptó los términos. Solo la autora puede hacerlo.

#### Scenario: Dejar de compartir
- **WHEN** la autora toca «Dejar de compartir»
- **THEN** la página dice «Dejaste de compartir la sesión», muestra «Compartir», ya no lleva el chip «Compartida» y la sesión deja de aparecer en el repositorio

#### Scenario: Ya no estaba compartida
- **WHEN** llega la petición de dejar de compartir una sesión propia que ya no está compartida (dos pestañas)
- **THEN** la sesión queda igual y no se registra otra operación

#### Scenario: Sesión ajena
- **WHEN** una docente envía, con una petición armada a mano, dejar de compartir una sesión de una colega
- **THEN** la sesión sigue compartida

### Requirement: Compartir después
«Compartir» SHALL abrir los términos de publicación («Antes de compartir», con el texto del doc 09 §4, «Acepto y comparto» y «Volver»). Solo al aceptar, la sesión queda compartida, con la fecha y la hora de esta aceptación, y aparece en el repositorio. Solo la autora puede hacerlo.

#### Scenario: Aceptar y compartir
- **WHEN** la autora toca «Compartir» y luego «Acepto y comparto»
- **THEN** la página dice «Sesión compartida en el repositorio», lleva el chip «Compartida» y la sesión aparece en el repositorio con la fecha de esta aceptación guardada

#### Scenario: Volver
- **WHEN** la autora toca «Volver» o Esc en los términos
- **THEN** los términos se cierran, el foco vuelve a «Compartir» y la sesión sigue sin compartir

#### Scenario: Compartir sin aceptar
- **WHEN** llega al servidor la petición de compartir sin la aceptación de los términos
- **THEN** la sesión sigue sin compartir y la respuesta dice «Para compartirla en el repositorio debes aceptar los términos.»

#### Scenario: Volver a compartir
- **WHEN** la autora comparte de nuevo una sesión que había dejado de compartir
- **THEN** debe aceptar otra vez los términos y la fecha guardada es la de la nueva aceptación

#### Scenario: Sesión ajena
- **WHEN** una docente envía, con una petición armada a mano, compartir una sesión no compartida de una colega
- **THEN** la sesión sigue sin compartir y la respuesta es «La sesión ya no está disponible»

### Requirement: Eliminar una sesión propia
«Eliminar» SHALL pedir confirmación en un diálogo chico («¿Eliminar esta sesión?», «También se retira de la dirección.», «Se eliminarán la sesión y su archivo para todos.», «Cancelar» y «Eliminar sesión»), con el foco inicial en «Cancelar». Al confirmar, el sistema elimina la sesión y su archivo para todos, también para la dirección, y lleva a «Mis sesiones» con el Mensaje «Sesión eliminada».

#### Scenario: Camino ideal (eliminar y confirmar)
- **GIVEN** una sesión propia
- **WHEN** el docente elige eliminarla y confirma la acción
- **THEN** el sistema la retira del repositorio y muestra el mensaje "Sesión eliminada"

#### Scenario: Flujo alternativo válido (cancelar)
- **GIVEN** un docente que elige eliminar una sesión
- **WHEN** cancela la confirmación
- **THEN** el sistema conserva la sesión sin cambios

#### Scenario: Después de eliminar
- **WHEN** la autora confirma la eliminación
- **THEN** la sesión ya no está en «Mis sesiones» ni en el repositorio, su página dice «La sesión ya no está disponible», su archivo ya no existe en el almacenamiento y el Mensaje llega al lector de pantalla

#### Scenario: Cancelar y foco
- **WHEN** la autora toca «Cancelar» o Esc en el diálogo
- **THEN** el diálogo se cierra y el foco vuelve a «Eliminar»

#### Scenario: Eliminar dos veces
- **WHEN** la autora confirma la eliminación en dos pestañas
- **THEN** la segunda ve «La sesión ya no está disponible» y no hay error

#### Scenario: Recargar después de eliminar
- **WHEN** la autora recarga «Mis sesiones» después de eliminar
- **THEN** ya no ve el Mensaje «Sesión eliminada»

### Requirement: Solo la autora elimina
Solo la autora MUST poder eliminar una sesión. Si otra docente lo intenta sobre una sesión que puede ver, el sistema SHALL responder «Solo el autor puede eliminar esta sesión» y conservarla con su archivo; sobre una que no puede ver, responde «La sesión ya no está disponible».

#### Scenario: Caso de error (sesión de otro docente)
- **GIVEN** una sesión de otro docente
- **WHEN** un docente intenta eliminarla
- **THEN** el sistema no lo permite y muestra el mensaje "Solo el autor puede eliminar esta sesión"

#### Scenario: Ajena y no compartida
- **WHEN** una docente envía, con una petición armada a mano, eliminar una sesión no compartida de una colega
- **THEN** la respuesta es «La sesión ya no está disponible» y la sesión y su archivo siguen

#### Scenario: Otro rol
- **WHEN** la dirección o el Administrador envían la petición de eliminar una sesión
- **THEN** el sistema los lleva a su inicio y la sesión sigue

### Requirement: Página accesible y sin desplazamiento horizontal
La página de la sesión, el diálogo de eliminar y los términos MUST NOT tener infracciones graves de axe en ambos temas ni desplazamiento horizontal a 360 px; cada control mide 44 px o más. El texto transcrito se ajusta al ancho de la página, aunque tenga líneas largas.

#### Scenario: Revisión de la página
- **WHEN** se revisan la página de una sesión propia, el diálogo de eliminar abierto y los términos abiertos, a 360 px en claro y oscuro
- **THEN** axe no reporta infracciones graves, la página no se desplaza en horizontal y cada control mide al menos 44 px

#### Scenario: Línea larga en el texto
- **WHEN** el texto transcrito tiene una línea de 300 caracteres sin espacios
- **THEN** la línea se parte y la página no se desplaza en horizontal
