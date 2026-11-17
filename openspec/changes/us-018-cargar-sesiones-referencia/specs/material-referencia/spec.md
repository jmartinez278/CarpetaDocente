# Spec Delta

## Purpose

Permite que el Administrador cargue, edite y elimine desde el panel sesiones de referencia con su fuente y su permiso de uso, para que el repositorio de una institución tenga material desde el inicio (US-018, RF-018, RN-020).

## ADDED Requirements

### Requirement: Cargar una sesión de referencia
El panel SHALL permitir al Administrador cargar una sesión de referencia con institución, grado inicial y final, área, título, propósito opcional, fuente, permiso de uso y un archivo PDF o Word (.docx) de hasta 4 MB. Se guarda como «Material de referencia», sin autora, con el Administrador como quien la subió, y queda en el repositorio de esa institución desde que se guarda, sin términos de publicación.

#### Scenario: Camino ideal
- **GIVEN** una sesión cuyo uso está permitido
- **WHEN** el administrador la sube con grado, área, título, fuente y tipo de permiso
- **THEN** el sistema la guarda como "Material de referencia", visible para todos los docentes

#### Scenario: Flujo alternativo válido (equipo del proyecto)
- **GIVEN** una sesión elaborada por el propio equipo del proyecto
- **WHEN** el administrador la sube e indica como fuente "Equipo del proyecto"
- **THEN** el sistema la guarda como material de referencia

#### Scenario: Visible desde que se guarda
- **WHEN** el Administrador guarda una sesión de referencia de la institución A
- **THEN** las docentes de A la ven en el repositorio de inmediato, y las de otra institución no

### Requirement: Fuente y permiso de uso obligatorios
La fuente y el permiso de uso MUST ir en toda sesión de referencia, también cuando la fuente es «Equipo del proyecto»; cada uno tiene hasta 300 caracteres. Si falta alguno, o solo tiene espacios, el sistema SHALL NOT guardarla y muestra «Indique la fuente y el permiso de uso».

#### Scenario: Caso de error
- **GIVEN** una sesión de terceros
- **WHEN** el administrador intenta subirla sin indicar la fuente o el permiso de uso
- **THEN** el sistema no la guarda y muestra el mensaje "Indique la fuente y el permiso de uso"

#### Scenario: Solo espacios
- **WHEN** la fuente o el permiso de uso llegan solo con espacios
- **THEN** el sistema no la guarda, muestra «Indique la fuente y el permiso de uso» y no queda ningún archivo en el almacenamiento

#### Scenario: Coherencia en la base
- **WHEN** se intenta guardar una sesión de referencia sin fuente o sin permiso de uso, con autora, con fecha de términos o fuera del repositorio
- **THEN** la base de datos la rechaza

### Requirement: Varios grados
Una sesión de referencia SHALL guardar un rango de grados, de 1.º a 6.º, con el grado final igual o mayor que el inicial; un solo grado es un rango de uno. Las sesiones que envían las docentes MUST tener un solo grado.

#### Scenario: Multigrado
- **WHEN** el Administrador carga una sesión de 3.º a 5.º grado
- **THEN** se guarda con los tres grados

#### Scenario: Rango al revés
- **WHEN** el grado final es menor que el inicial
- **THEN** el sistema no la guarda y muestra «El grado final no puede ser menor que el inicial.»

#### Scenario: Una sesión de docente con varios grados
- **WHEN** se intenta guardar en la base una sesión propia de una docente con grado final distinto del inicial
- **THEN** la base de datos la rechaza

### Requirement: Datos y archivo válidos
La ficha SHALL validar los datos con las mismas reglas que el envío de una docente: título obligatorio de hasta 200 caracteres, propósito de hasta 1000, área que la institución elegida trabaja (RN-007) y archivo PDF o .docx de hasta 4 MB reconocido por su contenido, con los mensajes de cada campo. Con un dato inválido no se guarda nada, ni la fila ni el archivo.

#### Scenario: Área que la institución no trabaja
- **WHEN** el Administrador elige un área que la institución elegida no trabaja
- **THEN** el sistema no la guarda y el campo área dice «Elige un área de la lista.»

#### Scenario: Archivo que no es PDF ni Word
- **WHEN** el archivo es una imagen renombrada a .pdf
- **THEN** el sistema no la guarda y el campo archivo dice «Este archivo no es PDF ni Word (.docx). Elige otro archivo.»

#### Scenario: Sin archivo
- **WHEN** el Administrador guarda la ficha nueva sin archivo
- **THEN** el sistema no la guarda y el campo archivo dice «Elige un archivo PDF o Word (.docx).»

### Requirement: Texto para la búsqueda
Al cargar una sesión de referencia, el sistema SHALL transcribir el texto de su archivo con las mismas reglas que el envío de una docente, para que la búsqueda del repositorio la encuentre por su título, su propósito o su texto. Si no se puede extraer, se guarda igual, sin texto.

#### Scenario: Palabra del archivo
- **WHEN** el Administrador carga un .docx cuyo cuerpo dice «Formamos equipos multigrado»
- **THEN** una docente de esa institución la encuentra al buscar «multigrado»

#### Scenario: PDF escaneado
- **WHEN** el archivo es un PDF sin capa de texto
- **THEN** la sesión se guarda sin texto y sin error

### Requirement: Editar una sesión de referencia
Solo el Administrador SHALL editar una sesión de referencia, en el panel: grados, área, título, propósito, fuente y permiso de uso, con las mismas reglas que al cargarla. El archivo y la institución no se cambian; para cambiar el archivo se elimina y se carga de nuevo. La búsqueda refleja el título y el propósito nuevos.

#### Scenario: Cambiar el título
- **WHEN** el Administrador cambia el título de una sesión de referencia
- **THEN** el repositorio la muestra con el título nuevo y la búsqueda la encuentra por él

#### Scenario: Borrar la fuente al editar
- **WHEN** el Administrador deja la fuente vacía y guarda
- **THEN** el sistema no guarda el cambio y muestra «Indique la fuente y el permiso de uso»

### Requirement: Eliminar una sesión de referencia
Solo el Administrador SHALL eliminar una sesión de referencia, desde su ficha del panel y con la confirmación del panel; se eliminan la sesión, su archivo y sus vistas. El panel MUST NOT ofrecer el borrado masivo de sesiones de referencia.

#### Scenario: Eliminar
- **WHEN** el Administrador elimina una sesión de referencia y confirma
- **THEN** la sesión deja de estar en el repositorio, su página dice «La sesión ya no está disponible» y su archivo ya no existe en el almacenamiento

#### Scenario: Sin borrado masivo
- **WHEN** el Administrador abre la lista de sesiones de referencia
- **THEN** la lista no ofrece la acción de eliminar las seleccionadas

### Requirement: Solo las sesiones de referencia en el panel
El panel SHALL mostrar al Administrador solo las sesiones de referencia. Las sesiones que envían las docentes MUST NOT verse, editarse ni eliminarse desde el panel.

#### Scenario: Sesión de una docente
- **WHEN** el Administrador abre la lista de sesiones de referencia, o la ficha con el identificador de una sesión enviada por una docente
- **THEN** la sesión de la docente no aparece en la lista y su ficha no se abre

#### Scenario: Otro rol
- **WHEN** una docente o la dirección piden la lista o la ficha de las sesiones de referencia del panel
- **THEN** el sistema no les muestra el panel

### Requirement: Registro de la carga
Cargar, editar y eliminar una sesión de referencia SHALL dejar, en la misma transacción, una entrada SESION_REFERENCIA_CARGADA, SESION_REFERENCIA_EDITADA o SESION_REFERENCIA_ELIMINADA con el Administrador y la sesión como entidad (su UUID); la de editar lleva los nombres de los campos que cambiaron, sin sus valores. Ningún detalle lleva el título, la fuente, el permiso de uso, el texto ni el nombre del archivo. Guardar sin cambios no deja entrada.

#### Scenario: Cargar
- **WHEN** el Administrador carga una sesión de referencia
- **THEN** queda una entrada SESION_REFERENCIA_CARGADA con su usuario, la entidad `sesion` y el UUID, y ninguna SESION_ENVIADA

#### Scenario: Editar
- **WHEN** el Administrador cambia el título y la fuente
- **THEN** queda una entrada SESION_REFERENCIA_EDITADA con `{"campos": [...]}` que nombra esos dos campos, sin sus valores

#### Scenario: Eliminar
- **WHEN** el Administrador elimina una sesión de referencia
- **THEN** queda una entrada SESION_REFERENCIA_ELIMINADA con su UUID

### Requirement: No cuenta en los indicadores
Una sesión de referencia MUST NOT contar en «sesiones cargadas» ni en KPI-01. Las vistas y descargas que las docentes hagan de ella SHALL registrarse como las de cualquier sesión del repositorio.

#### Scenario: Sesiones cargadas
- **WHEN** el Administrador carga 5 sesiones de referencia en una semana sin envíos de docentes
- **THEN** la fila de esa semana dice 0 en «sesiones cargadas» y los docentes activos no cambian

#### Scenario: Una docente la descarga
- **WHEN** una docente abre por primera vez una sesión de referencia y la descarga
- **THEN** quedan una entrada SESION_VISTA y una SESION_DESCARGADA con `"propia": false`
