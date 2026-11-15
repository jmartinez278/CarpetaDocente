# Spec Delta

## Purpose

Permite que la docente envíe una sesión de aprendizaje a la dirección desde su celular o su PC y decida, con su consentimiento explícito, si además la comparte con sus colegas en el repositorio (US-010, US-014).

## ADDED Requirements

### Requirement: Pantalla Sesiones
La docente SHALL tener la pantalla Sesiones con la cabecera de la dimensión (ícono, título «Sesiones», franjas en el tinte de Sesiones y el subtítulo «Planificación de sesiones de aprendizaje»), el botón «Subir una sesión» y el estado vacío «Aquí verás las sesiones que envíes y su estado.», sin lista de sesiones. La tarjeta Sesiones de la portada sigue en «Próximamente».

#### Scenario: Primera visita
- **WHEN** una docente abre la pantalla Sesiones escribiendo su dirección
- **THEN** ve la cabecera, el botón «Subir una sesión» y el estado vacío, y ninguna lista

#### Scenario: Portada sin cambio
- **WHEN** la docente abre su portada
- **THEN** la tarjeta Sesiones sigue en «Próximamente», sin enlace a la pantalla

### Requirement: Solo el rol Docente
La pantalla Sesiones y el envío MUST ser solo del rol Docente, tenga o no sección asignada. La dirección y el Administrador van a su pantalla de inicio y una visita sin sesión, al ingreso; ninguno de ellos guarda una sesión.

#### Scenario: Docente sin sección
- **WHEN** una docente sin sección en el año ABIERTO abre Sesiones y envía una sesión válida
- **THEN** la sesión se guarda

#### Scenario: Otro rol
- **WHEN** la dirección o el Administrador abren Sesiones o envían el formulario
- **THEN** el sistema los lleva a su pantalla de inicio y no guarda ninguna sesión ni archivo

#### Scenario: Sin sesión
- **WHEN** una visita sin sesión abre Sesiones o envía el formulario
- **THEN** el sistema la lleva al ingreso y no guarda nada; si el envío venía del popup, la lleva con la página completa

### Requirement: Popup «Subir una sesión»
«Subir una sesión» SHALL abrir un popup con el título «Subir una sesión» y la ayuda «Se enviará a la dirección.»: en el celular, una hoja casi completa que sube desde abajo; en la PC, una ventana centrada de unos 480 px. No se cierra tocando afuera ni mientras sube; se cierra con «Cancelar» o con Esc. Cada apertura es un formulario nuevo.

#### Scenario: Abrir el popup
- **WHEN** la docente toca «Subir una sesión»
- **THEN** se abre el popup con el foco en su título, el resto de la pantalla queda inerte y la casilla de compartir está desmarcada

#### Scenario: Tocar afuera
- **WHEN** la docente toca fuera del popup
- **THEN** el popup sigue abierto con lo que escribió

#### Scenario: Cancelar
- **WHEN** la docente toca «Cancelar»
- **THEN** el popup se cierra sin guardar nada y el foco vuelve a «Subir una sesión»; al abrirlo otra vez, el formulario está vacío

#### Scenario: Orden de los botones
- **WHEN** la docente abre el popup en el celular y en la PC
- **THEN** en el celular «Enviar a la dirección» va arriba y «Cancelar» debajo; en la PC «Cancelar» va a la izquierda

### Requirement: Botón «atrás» con el popup abierto
El botón o gesto «atrás» del navegador SHALL cerrar solo el popup de arriba, sin salir de la pantalla y sin borrar lo escrito ni el archivo del popup que queda. Mientras sube, «atrás» no cierra nada.

#### Scenario: Atrás en el formulario
- **WHEN** la docente, con el formulario abierto, usa «atrás»
- **THEN** el popup se cierra y sigue en la pantalla Sesiones

#### Scenario: Atrás en los términos
- **WHEN** la docente, con los términos abiertos sobre el formulario, usa «atrás»
- **THEN** se cierran solo los términos y el formulario conserva sus campos, la casilla marcada y el archivo

#### Scenario: Atrás mientras sube
- **WHEN** la docente usa «atrás» mientras la sesión sube
- **THEN** el popup sigue abierto y la subida continúa

### Requirement: Campos del formulario
El formulario SHALL pedir el archivo, el grado (1.º a 6.º), el área, el título (hasta 200 caracteres) y el propósito (opcional, hasta 1000 caracteres), sin competencias. Las áreas son las que la institución de la docente trabaja, en el orden del SIAGIE. La ayuda del archivo dice «PDF o Word (.docx) · Hasta 4 MB».

#### Scenario: Áreas de la institución
- **WHEN** la docente abre el área
- **THEN** ve solo las áreas que su institución trabaja, en el orden del SIAGIE, y no las que no trabaja

#### Scenario: Archivo elegido
- **WHEN** la docente elige «leemos-un-cuento.pdf» de 1,2 MB
- **THEN** el control muestra el nombre, «PDF · 1,2 MB» y la acción «Cambiar»

### Requirement: Grado por defecto
Con una sola sección en el año ABIERTO, el grado SHALL venir con el de esa sección y la ayuda «Grado de tu sección: 2.º A. Puedes cambiarlo.». Con varias o ninguna, viene sin elegir, con la ayuda «Elige el grado de esta sesión.». El grado se puede cambiar.

#### Scenario: Una sección
- **WHEN** una docente de 2.º A abre el formulario
- **THEN** el grado dice «2.º grado» y la ayuda «Grado de tu sección: 2.º A. Puedes cambiarlo.»

#### Scenario: Varias secciones o ninguna
- **WHEN** una docente con dos secciones, o sin sección, abre el formulario
- **THEN** el grado está sin elegir y la ayuda dice «Elige el grado de esta sesión.»

### Requirement: Archivo PDF o Word de hasta 4 MB
El archivo MUST ser PDF o Word (.docx), reconocido por su contenido y no solo por su extensión, y pesar de 1 byte a 4 MB (4 194 304 bytes). El navegador lo revisa al elegirlo y el servidor otra vez al recibirlo; un archivo rechazado no se guarda.

#### Scenario: Tipo no permitido
- **WHEN** la docente elige un archivo que no es PDF ni Word (.docx), aunque se llame «sesion.pdf»
- **THEN** el campo dice «Este archivo no es PDF ni Word (.docx). Elige otro archivo.» y no se envía

#### Scenario: Archivo de más de 4 MB
- **WHEN** la docente elige un archivo de 4 194 305 bytes
- **THEN** el campo dice «El archivo supera los 4 MB. Elige uno más pequeño.» y no se envía

#### Scenario: Justo 4 MB
- **WHEN** la docente envía un PDF de 4 194 304 bytes
- **THEN** la sesión se guarda

#### Scenario: Envío que salta el navegador
- **WHEN** llega al servidor un envío con un archivo de otro tipo, uno de más de 4 MB, uno vacío o un .doc
- **THEN** el servidor no guarda la sesión ni el archivo y responde el mismo mensaje del campo

### Requirement: Datos que faltan
Si falta el archivo, el grado, el área o el título, o un dato no es válido, la sesión MUST NOT guardarse y cada campo SHALL mostrar su motivo, por ejemplo «Falta indicar el área.» y «Falta indicar el título.». Lo escrito y el archivo siguen en el formulario.

#### Scenario: Área y título vacíos
- **WHEN** la docente toca «Enviar a la dirección» sin área ni título
- **THEN** ve «Falta indicar el área.» y «Falta indicar el título.» en sus campos, el foco va al primer campo con error y no se envía nada

#### Scenario: Sin archivo
- **WHEN** la docente envía sin elegir archivo
- **THEN** el campo dice «Elige un archivo PDF o Word (.docx).»

#### Scenario: Área ajena o grado fuera de rango
- **WHEN** llega al servidor un área que la institución no trabaja, un grado 7 o un título de 201 caracteres
- **THEN** el servidor no guarda nada y responde el motivo del campo

### Requirement: Compartir en el repositorio
El formulario SHALL tener la casilla «Compartir también en el repositorio», desmarcada, con la ayuda «Tus colegas podrán verla, descargarla y adaptarla.». Sin la casilla, «Enviar a la dirección» envía directo y la sesión queda privada: solo la ven la autora y la dirección.

#### Scenario: Enviar sin compartir
- **WHEN** la docente completa los datos y toca «Enviar a la dirección» sin marcar la casilla
- **THEN** la sesión se envía sin pedir términos, queda enviada a la dirección, no compartida y sin fecha de aceptación

### Requirement: Términos de publicación
Con la casilla marcada, «Enviar a la dirección» SHALL abrir, sobre el formulario, un popup chico y centrado «Antes de compartir», con la ayuda «Para compartirla en el repositorio debes aceptar los términos.», el texto completo del doc 09 §4 (la frase de entrada y sus cuatro puntos, literales), «Acepto y envío» y «Volver». Solo «Acepto y envío» envía.

#### Scenario: Aceptar y enviar
- **WHEN** la docente marca la casilla, toca «Enviar a la dirección» y luego «Acepto y envío»
- **THEN** la sesión se envía a la dirección, queda compartida y se guarda la fecha y la hora de la aceptación

#### Scenario: Volver
- **WHEN** la docente toca «Volver» o Esc en los términos
- **THEN** se cierran solo los términos, el foco vuelve a «Enviar a la dirección», no se envía nada y el formulario conserva sus datos, la casilla y el archivo

#### Scenario: Compartir sin aceptar
- **WHEN** llega al servidor un envío que pide compartir sin la aceptación de los términos
- **THEN** el servidor no guarda la sesión ni el archivo y responde «Para compartirla en el repositorio debes aceptar los términos.»

#### Scenario: Datos incompletos con la casilla marcada
- **WHEN** la docente marca la casilla y toca «Enviar a la dirección» sin título
- **THEN** ve «Falta indicar el título.» y los términos no se abren

### Requirement: Subida con avance
Mientras sube, el popup SHALL mostrar una barra con el porcentaje («Subiendo… 45 %»), anunciada al lector de pantalla, y bloquear los campos, «Enviar a la dirección» y «Cancelar». El envío viaja en una sola petición con los datos, el archivo y, si comparte, la aceptación.

#### Scenario: Subiendo
- **WHEN** la docente envía una sesión de 4 MB con una conexión lenta
- **THEN** ve «Subiendo… N %» que avanza y no puede cambiar los campos, volver a enviar ni cancelar

#### Scenario: Recargar mientras sube
- **WHEN** la docente intenta recargar o cerrar la pestaña mientras sube
- **THEN** el navegador le pide confirmar la salida

### Requirement: Corte de red
Si la subida falla por la red o el servidor no responde, el popup SHALL mostrar «Se cortó la conexión» / «Tus datos y tu archivo siguen aquí. Revisa tu conexión e intenta enviar de nuevo.», desbloquear el formulario con lo escrito y el archivo, y cambiar el botón a «Reintentar envío». Si el navegador ya no conserva el archivo, el campo lo pide de nuevo.

#### Scenario: Se corta y reintenta
- **WHEN** la red se corta al 45 % y la docente toca «Reintentar envío» con la red de vuelta
- **THEN** la sesión se envía una sola vez con los mismos datos

#### Scenario: Se guardó pero no llegó la respuesta
- **WHEN** el servidor guardó la sesión, la respuesta no llegó y la docente reintenta
- **THEN** ve el mismo éxito y en el sistema queda una sola sesión, un solo archivo y una sola entrada de actividad

### Requirement: Envío exitoso
Al guardarse la sesión, el popup SHALL cerrarse y la pantalla Sesiones mostrar el Mensaje de éxito «Sesión enviada a la dirección» o «Sesión enviada a la dirección y compartida en el repositorio», con el título, el grado, el área, el nombre del archivo, su tipo y su tamaño (en el formato de `es-pe`), y el botón «Subir otra», que abre un formulario nuevo. El estado vacío sigue debajo.

#### Scenario: Éxito sin compartir
- **WHEN** la docente envía «Leemos un cuento», 2.º grado, Comunicación, con un PDF de 1,2 MB, sin compartir
- **THEN** el popup se cierra y la pantalla dice «Sesión enviada a la dirección», con «Leemos un cuento», «2.º grado», «Comunicación», «leemos-un-cuento.pdf» y «PDF · 1,2 MB», y el anuncio llega al lector de pantalla

#### Scenario: Éxito compartida
- **WHEN** la misma sesión se envía con la casilla marcada y los términos aceptados
- **THEN** la pantalla dice «Sesión enviada a la dirección y compartida en el repositorio»

#### Scenario: Recargar después del éxito
- **WHEN** la docente recarga la pantalla después del éxito
- **THEN** ve la pantalla sin el Mensaje y no se envía otra sesión

### Requirement: Sesión guardada
Cada envío válido SHALL guardar una sesión de la institución de la docente, con ella como autora y quien la subió, el grado, el área, el título, el propósito, origen PROPIA, estado ENVIADA, si se compartió, la fecha y hora de aceptación solo si se compartió, y del archivo su nombre original, su tipo y su tamaño.

#### Scenario: Datos guardados
- **WHEN** la docente envía una sesión sin compartir
- **THEN** la sesión queda con esos datos, estado ENVIADA, no compartida y sin fecha de aceptación

#### Scenario: Coherencia en la base
- **WHEN** se intenta guardar una sesión compartida sin fecha de aceptación, una no compartida con fecha, o una de más de 4 MB
- **THEN** la base de datos la rechaza

### Requirement: Pantalla accesible y sin desplazamiento horizontal
La pantalla Sesiones, el formulario, los términos, los errores, la subida y el éxito MUST NOT tener infracciones graves de axe en ambos temas, a 360 y 1280 px, ni desplazamiento horizontal; los objetivos táctiles miden 44 px o más. Cada error queda asociado a su campo y el teclado alcanza el cuerpo del popup.

#### Scenario: Estados del boceto
- **WHEN** se revisan los estados 1, 2, 3, 4a, 5, 6a, 6b, 7, 8, 9 y 10 del boceto en claro y oscuro, a 360 y 1280 px
- **THEN** axe no reporta infracciones graves, la página no se desplaza en horizontal y cada control mide al menos 44 px

#### Scenario: Pantalla baja
- **WHEN** el popup de los términos no cabe en la altura de la pantalla
- **THEN** su cuerpo se desplaza y «Acepto y envío» y «Volver» siguen a la vista
