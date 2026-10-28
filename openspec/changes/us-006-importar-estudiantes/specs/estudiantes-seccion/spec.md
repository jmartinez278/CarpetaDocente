# Spec Delta

## Purpose

Lista de estudiantes de cada sección: la docente de aula la carga pegando las filas de su hoja de cálculo o uno por uno, y la corrige, para registrar después la asistencia y las notas sin volver a escribir los nombres.

## ADDED Requirements

### Requirement: Estudiantes de una sección
Cada estudiante SHALL pertenecer a una sección y guardar solo sus apellidos y sus nombres (RN-015), de hasta 120 caracteres cada uno, en mayúsculas (conservando tildes y Ñ) y sin espacios al inicio, al final ni repetidos. Una sección MUST NOT tener dos estudiantes con los mismos apellidos y nombres, y la base de datos lo impide.

#### Scenario: Nombre guardado en mayúsculas
- **WHEN** la docente guarda "  quispe   mamani " y "ana lucía"
- **THEN** el estudiante queda como "QUISPE MAMANI, ANA LUCÍA"

#### Scenario: Homónimo exacto en la misma sección
- **WHEN** se intenta guardar un estudiante con los mismos apellidos y nombres que otro de la sección, por cualquier vía
- **THEN** no se guarda

#### Scenario: Mismo nombre en otra sección
- **WHEN** dos secciones tienen un estudiante "QUISPE MAMANI, ANA"
- **THEN** ambos se guardan

### Requirement: Acceso solo a sus secciones
Solo la docente de aula de una sección del año escolar ABIERTO SHALL ver y cambiar su lista. Otra docente recibe "no encontrada" (404); otro rol va a su pantalla de inicio; sin sesión, a `/ingresar/`. Un estudiante solo se alcanza a través de su propia sección.

#### Scenario: Sección de otra docente
- **WHEN** una docente abre la lista o edita un estudiante de una sección que no es suya
- **THEN** recibe 404 y no ve ningún nombre

#### Scenario: Sección de un año cerrado
- **WHEN** la docente abre la lista de su sección de un año CERRADO
- **THEN** recibe 404

#### Scenario: Otro rol
- **WHEN** una cuenta de la dirección abre la dirección de la lista
- **THEN** llega a `/direccion/`

### Requirement: Diálogo de la lista
"Ver estudiantes" SHALL abrir un único diálogo "Estudiantes de 2.º A", con el número de estudiantes en la cabecera, donde se cambia de vista sin abrir otro diálogo encima. Las vistas secundarias tienen "Volver a la lista". Esc y "Cerrar" lo cierran y el foco vuelve a "Ver estudiantes". Cada vista tiene su dirección: sin JavaScript, el enlace abre esa vista como página completa y todo funciona igual.

#### Scenario: Abrir la lista
- **WHEN** la docente toca "Ver estudiantes" en la portada
- **THEN** se abre el diálogo "Estudiantes de 2.º A" sobre la portada, con "25 estudiantes" (o el número que tenga) bajo el título, sin cambiar la dirección de la página

#### Scenario: Cerrar el diálogo
- **WHEN** la docente presiona Esc o toca "Cerrar"
- **THEN** el diálogo se cierra y el foco vuelve a "Ver estudiantes"

#### Scenario: Sin JavaScript
- **WHEN** la docente sigue "Ver estudiantes" sin JavaScript
- **THEN** ve la lista como página completa, y agregar, pegar, editar, quitar y vaciar funcionan con envíos normales

### Requirement: Lista de la sección
La lista SHALL mostrar a los estudiantes ordenados por apellidos y nombres, con su número de orden, el nombre completo "APELLIDOS, NOMBRES" sin recortar y un enlace "Editar" por fila. "Agregar estudiante" va arriba y "Vaciar lista", al final. Sin estudiantes, la vista dice "Tu sección aún no tiene estudiantes." y ofrece "Agregar uno por uno" (principal) y "Pegar lista".

#### Scenario: Lista vacía
- **WHEN** la docente abre una sección sin estudiantes
- **THEN** ve "Tu sección aún no tiene estudiantes.", el botón principal "Agregar uno por uno" y el secundario "Pegar lista"

#### Scenario: Orden y número
- **WHEN** la sección tiene a "RAMOS HUAMÁN, VALENTÍN" y a "AGUILAR FLORES, LUCIANA"
- **THEN** la lista los muestra como 1 "AGUILAR FLORES, LUCIANA" y 2 "RAMOS HUAMÁN, VALENTÍN"

### Requirement: Pegar lista
La docente SHALL pegar en un cuadro de texto una línea por estudiante con el formato "APELLIDOS, NOMBRES". Las líneas en blanco se ignoran, pero cuentan para numerar las líneas tal como se ven en el cuadro. Si todas las líneas son válidas, se guardan todos y la lista muestra "N estudiantes importados" / "Revisa los nombres; puedes corregirlos con Editar", sin que el aviso desaparezca solo.

#### Scenario: Camino ideal
- **WHEN** una docente con una sección asignada y sin estudiantes pega las filas copiadas de una hoja de cálculo, 25 líneas con apellidos y nombres completos, y toca "Importar"
- **THEN** el sistema registra los 25 estudiantes en la sección y muestra "25 estudiantes importados", y la cabecera dice "25 estudiantes"

#### Scenario: Líneas en blanco
- **WHEN** el texto tiene 25 estudiantes y líneas en blanco entre ellos y al final
- **THEN** se importan los 25 y ninguna línea en blanco da error

### Requirement: Pegar lista solo con la sección vacía
Pegar lista SHALL estar disponible solo mientras la sección no tiene estudiantes. Con al menos un estudiante, la lista MUST NOT ofrecer "Pegar lista", la dirección de Pegar lista muestra "Tu sección ya tiene estudiantes" / "Agrega a los que falten con Agregar estudiante." sin el cuadro de texto, y un envío de texto pegado no guarda nada. Los estudiantes que falten se agregan uno por uno.

#### Scenario: Lista con estudiantes
- **WHEN** la docente abre la lista de una sección con estudiantes
- **THEN** ve "Agregar estudiante" y no ve "Pegar lista"

#### Scenario: Dirección de Pegar lista con estudiantes
- **WHEN** la docente abre la dirección de Pegar lista de una sección con estudiantes
- **THEN** ve "Tu sección ya tiene estudiantes" / "Agrega a los que falten con Agregar estudiante.", sin el cuadro de texto

#### Scenario: Envío a una sección con estudiantes
- **WHEN** llega un texto pegado para una sección que ya tiene estudiantes (por ejemplo, desde otra pestaña abierta antes)
- **THEN** no se guarda ningún estudiante y se muestra el mismo aviso

### Requirement: Errores de la lista pegada
Si alguna línea tiene error, el sistema SHALL NOT guardar ningún estudiante, conservar el texto pegado y mostrar "No se guardó ningún estudiante", con cada error por número de línea, su motivo y cómo corregirlo. Motivos: tabulaciones (más de una columna), sin coma, más de una coma, apellidos o nombres vacíos, más de 120 caracteres, estudiante repetido en el texto y más de 60 estudiantes. Una línea muestra un solo motivo.

#### Scenario: Caso de error
- **WHEN** el texto pegado tiene una línea sin apellidos y dos líneas con el mismo estudiante, y la docente toca "Importar"
- **THEN** el sistema no importa ninguna línea y muestra cada línea con error y su motivo, para que la docente las corrija, con el texto pegado intacto

#### Scenario: Línea con tabulaciones
- **WHEN** la línea 3 es "ALVARADO ROJAS⇥MARÍA FERNANDA⇥2.º A" (⇥ = tabulación), con o sin coma
- **THEN** se muestra "Línea 3: pega solo la columna de apellidos y nombres"

#### Scenario: Falta la coma
- **WHEN** la línea 7 es "CONDORI MAMANI DANIELA"
- **THEN** se muestra "Línea 7: falta la coma entre apellidos y nombres"

#### Scenario: Estudiante repetido
- **WHEN** las líneas 4 y 12 tienen el mismo estudiante, aunque con distintas mayúsculas o espacios
- **THEN** se muestra "Líneas 4 y 12: el mismo estudiante", con la sugerencia de escribir el segundo nombre completo si son personas distintas

#### Scenario: Campo demasiado largo
- **WHEN** los apellidos de la línea 15 tienen 121 caracteres
- **THEN** se muestra "Línea 15: los apellidos tienen más de 120 caracteres"

#### Scenario: Más de 60 estudiantes
- **WHEN** el texto tiene 61 líneas con texto
- **THEN** se muestra que la lista tiene 61 líneas y el máximo es 60, sin errores por línea, y no se guarda nada

#### Scenario: Texto vacío
- **WHEN** la docente toca "Importar" con el cuadro vacío o solo con líneas en blanco
- **THEN** no se guarda nada y se le pide pegar al menos un estudiante

### Requirement: Agregar un estudiante
La docente SHALL agregar un estudiante con los campos Apellidos y Nombres, obligatorios y de hasta 120 caracteres. "Guardar y agregar otro" guarda, deja la vista con los campos vacíos y el foco en Apellidos, muestra "Estudiante agregado" y actualiza el número de la cabecera. Un homónimo exacto se rechaza con la sugerencia del segundo nombre completo.

#### Scenario: Flujo alternativo válido
- **WHEN** una docente con la lista ya importada agrega a un estudiante que se incorporó después
- **THEN** el sistema registra al estudiante en la sección, muestra "Estudiante agregado" y la cabecera pasa de "25 estudiantes" a "26 estudiantes"

#### Scenario: Homónimo al agregar
- **WHEN** la docente agrega a un estudiante con los mismos apellidos y nombres que otro de su sección
- **THEN** no se guarda, el formulario conserva lo escrito y le sugiere escribir el segundo nombre completo si son personas distintas

#### Scenario: Campo vacío
- **WHEN** la docente deja vacíos los Nombres
- **THEN** no se guarda y el campo muestra su error

### Requirement: Editar un estudiante
La docente SHALL corregir los apellidos y nombres de un estudiante de su sección, con las mismas reglas que al agregar. "Guardar cambios" vuelve a la lista con el nombre corregido en su lugar del orden.

#### Scenario: Corregir un nombre
- **WHEN** la docente cambia "ANA LUCIA" por "ana lucía" y toca "Guardar cambios"
- **THEN** la lista muestra "QUISPE MAMANI, ANA LUCÍA"

#### Scenario: Corrección que crea un homónimo
- **WHEN** la corrección deja al estudiante igual a otro de la sección
- **THEN** no se guarda y se muestra la sugerencia del segundo nombre completo

### Requirement: Quitar y vaciar
Desde Editar, "Quitar estudiante" pide confirmación y lo elimina; "Vaciar lista" pide confirmación ("Se quitarán los 25 estudiantes.") y los elimina a todos. Ambos MUST hacerse solo si ningún estudiante afectado tiene asistencia ni notas; si no, no se elimina ninguno y se muestra el bloqueo con "Si es un error, pide ayuda al administrador".

#### Scenario: Quitar sin registros
- **WHEN** la docente confirma "Quitar estudiante" de un estudiante sin asistencia ni notas
- **THEN** el estudiante deja de estar en la lista y la cabecera baja en uno

#### Scenario: Vaciar sin registros
- **WHEN** la docente confirma "Vaciar lista" con 25 estudiantes sin registros
- **THEN** la sección queda sin estudiantes y se ve la lista vacía

#### Scenario: Vaciar con registros
- **WHEN** algún estudiante de la sección ya tiene asistencia o notas y la docente confirma "Vaciar lista"
- **THEN** no se quita ninguno y ve "No se puede vaciar: algunos estudiantes ya tienen registros" / "Si es un error, pide ayuda al administrador", solo con "Volver a la lista"

#### Scenario: Quitar con registros
- **WHEN** el estudiante ya tiene asistencia o notas y la docente confirma "Quitar estudiante"
- **THEN** no se quita y ve "No se puede quitar: el estudiante ya tiene registros" / "Si es un error, pide ayuda al administrador"

### Requirement: Sesión vencida con el diálogo abierto
Si la sesión venció (RN-025) o se cerró mientras el diálogo está abierto, la siguiente acción en el diálogo SHALL llevar la página completa a `/ingresar/`, con el aviso de inactividad cuando corresponda, y MUST NOT mostrar el formulario de ingreso dentro del diálogo.

#### Scenario: Acción tras 60 minutos sin actividad
- **WHEN** la docente toca "Importar" en el diálogo después de 60 minutos sin actividad
- **THEN** la página completa va a `/ingresar/` con el aviso de inactividad y no se guarda nada

### Requirement: Diálogo accesible y sin desplazamiento horizontal
Cada vista de la lista, en el diálogo y como página completa, MUST pasar la revisión automática de accesibilidad (WCAG 2.1, A y AA) sin infracciones críticas ni graves en ambos temas, a 360 px y a 1280 px, y MUST NOT desplazarse en horizontal entre 320 px y 1280 px (RNF-005, RNF-008). Los nombres largos bajan de línea sin "…". Cabecera y pie del diálogo quedan fijos y solo el cuerpo se desplaza.

#### Scenario: Revisión de cada vista
- **WHEN** se revisan la lista vacía, la lista, Pegar lista, Revisar lista, Agregar, Editar, Quitar, Vaciar y el bloqueo, en ambos temas y anchos
- **THEN** no hay infracciones críticas ni graves y el ancho del documento no supera el de la ventana

#### Scenario: Nombre largo a 320 px
- **WHEN** la lista tiene un estudiante de 120 caracteres en apellidos y en nombres y se ve a 320 px
- **THEN** el nombre se lee completo en varias líneas y la página no se desplaza en horizontal
