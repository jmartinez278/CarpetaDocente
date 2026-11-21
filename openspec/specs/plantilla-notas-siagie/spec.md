# plantilla-notas-siagie Specification

## Purpose

Permite a la dirección completar la plantilla de notas del SIAGIE de una sección con las notas registradas en CarpetaDocente, sin volver a digitarlas, y devolver el archivo completado junto con un resumen del llenado.

## Requirements

### Requirement: Solo la dirección completa la plantilla
Subir y completar la plantilla de notas del SIAGIE SHALL estar reservado al rol Dirección, sobre las secciones, el año y los periodos de su institución. La docente y el Administrador van a su pantalla de inicio; sin sesión, al ingreso.

#### Scenario: Otro rol
- **WHEN** una docente o el Administrador envía una plantilla a la ruta de llenado
- **THEN** va a su pantalla de inicio, no se procesa nada y no queda entrada PLANTILLA_SIAGIE_COMPLETADA

#### Scenario: Sin sesión
- **WHEN** alguien sin sesión envía una plantilla
- **THEN** va al ingreso y no se procesa nada

#### Scenario: Sección de otra institución
- **WHEN** llega, con una petición armada a mano, la elección de una sección de otra institución, de otro año o de otro grado que el de la plantilla
- **THEN** el servidor no guarda la equivalencia ni completa nada y responde «La sección elegida no es válida. Elige una de la lista.»

### Requirement: Diálogo «Sube la plantilla del SIAGIE»
«Subir plantilla», en el inicio de la dirección, SHALL abrir un diálogo con el título «Sube la plantilla del SIAGIE», la ayuda «Sube una plantilla de notas en Excel (.xlsx) por sección.», el campo «Archivo» y los botones «Completar plantilla» (deshabilitado hasta elegir un archivo) y «Cancelar»: en el celular, una hoja que sube desde abajo; en la PC, una ventana centrada. No se cierra tocando afuera ni mientras procesa; se cierra con «Cancelar» o con Esc. Cada apertura es un formulario nuevo.

#### Scenario: Abrir el diálogo
- **WHEN** la dirección toca «Subir plantilla»
- **THEN** se abre el diálogo con el foco en su título, el resto de la pantalla queda inerte y «Completar plantilla» está deshabilitado

#### Scenario: Elegir el archivo
- **WHEN** elige «RegNotas_2_TRIUNFADORES_B3.xlsx»
- **THEN** el campo muestra el nombre y «Excel (.xlsx)», el botón del campo dice «Cambiar» y «Completar plantilla» se habilita

#### Scenario: Cancelar
- **WHEN** toca «Cancelar» o Esc sin estar procesando
- **THEN** el diálogo se cierra sin enviar nada y el foco vuelve a «Subir plantilla»

### Requirement: Procesando
Mientras el archivo sube y se completa, el diálogo SHALL mostrar «Procesando la plantilla…» con una barra de avance anunciada al lector de pantalla y bloquear el campo, «Completar plantilla» y «Cancelar». Si la red se corta o el servidor no responde, el diálogo SHALL mostrar «Se cortó la conexión. Tu archivo sigue aquí: revisa tu conexión e inténtalo de nuevo.», desbloquearse y conservar el archivo elegido.

#### Scenario: Procesando
- **WHEN** la dirección toca «Completar plantilla»
- **THEN** ve «Procesando la plantilla…» y no puede cambiar el archivo, volver a enviar ni cancelar

#### Scenario: Se corta la red
- **WHEN** la red se corta mientras sube y la dirección vuelve a tocar «Completar plantilla» con la red de vuelta
- **THEN** se envía el mismo archivo sin volver a elegirlo

#### Scenario: En tiempo
- **WHEN** la dirección completa la plantilla de una sección de 30 estudiantes con el perfil Slow 4G
- **THEN** el resumen está listo en 5 s o menos, contando la subida (RNF-003)

### Requirement: Archivo que no corresponde a la plantilla
El servidor MUST reconocer la plantilla por su contenido y no por su nombre: un .xlsx de hasta 3 MB con la hoja «Parametros», cuyo código modular y anexo son los de la institución de la dirección, cuyo año académico es un año escolar de la institución y cuyo periodo (por ejemplo «B3») es un periodo de ese año con la organización de la institución, con un grado de PRIMERO a SEXTO en texto, y cuyas hojas de área llevan un código y números de competencia que el catálogo tiene. Si algo de eso no se cumple, no procesa nada y el campo SHALL mostrar «El archivo no corresponde a la plantilla de notas del SIAGIE», la ayuda «Elige el Excel que descargaste en «Periodo por Excel».» y la ruta «En el SIAGIE, ve a Evaluación → Registro de calificaciones → Periodo por Excel.», con el foco en el mensaje y el nombre del archivo a la vista.

#### Scenario: Otro Excel
- **WHEN** la dirección sube «Listado_2do.xlsx», un Excel sin la hoja «Parametros»
- **THEN** ve «El archivo no corresponde a la plantilla de notas del SIAGIE» con la ayuda y la ruta, el campo conserva «Listado_2do.xlsx» y puede elegir otro archivo en el mismo diálogo

#### Scenario: Otro tipo con nombre de Excel
- **WHEN** sube un PDF renombrado como «notas.xlsx», un archivo vacío o uno de más de 3 MB
- **THEN** el servidor no lo procesa; con más de 3 MB el campo dice «El archivo supera los 3 MB. Elige uno más pequeño.» y en los otros casos, el mensaje de la plantilla

#### Scenario: La completada no cabe en la respuesta
- **WHEN** la plantilla completada pasa de 3 MB
- **THEN** el campo dice «La plantilla completada supera los 3 MB y no se puede descargar. No se guardó ningún cambio.», sin la ayuda del SIAGIE, y no quedan ni la equivalencia nueva ni la entrada en el registro

#### Scenario: Plantilla de otra institución
- **WHEN** sube una plantilla con otro código modular, u otro anexo
- **THEN** ve el mensaje de la plantilla y no se completa nada

#### Scenario: Año o periodo que no existen
- **WHEN** sube una plantilla del año 2025, que la institución no tiene, o del periodo «B5»
- **THEN** ve el mensaje de la plantilla

#### Scenario: Institución por trimestres
- **WHEN** la institución trabaja por trimestres y la plantilla dice «B3»
- **THEN** ve el mensaje de la plantilla

#### Scenario: Área o competencia desconocida
- **WHEN** la plantilla trae la hoja «0099-OTRA» o, en «063-MATE», la competencia «05»
- **THEN** ve el mensaje de la plantilla y no se completa ninguna hoja

#### Scenario: Envío que salta el navegador
- **WHEN** llega al servidor un archivo dañado o comprimido para ocupar mucho más al abrirse
- **THEN** el servidor no lo procesa y responde el mensaje de la plantilla

### Requirement: Sección de la plantilla
La sección SHALL encontrarse por el grado y el nombre de la sección de la plantilla, sin distinguir mayúsculas, tildes ni espacios, entre las secciones de ese grado del año de la plantilla; o por la equivalencia guardada antes para esa sección del SIAGIE (su código y su nombre). Si no hay una sola coincidencia, el diálogo SHALL cambiar a «Elige la sección», con la tarjeta «Sección en la plantilla del SIAGIE» y «2.º TRIUNFADORES · Tercer bimestre 2026», el grupo «Sección de tu I.E.» con una opción por cada sección de ese grado (2.º A, 2.º B…), sin ninguna marcada, la ayuda «Guardaremos esta equivalencia para las próximas plantillas de 2.º TRIUNFADORES.» y los botones «Guardar y completar» (deshabilitado hasta elegir) y «Cancelar».

#### Scenario: El nombre coincide
- **WHEN** la plantilla dice «SEGUNDO» y «A» y la I.E. tiene 2.º A
- **THEN** se completa con 2.º A sin preguntar y no se guarda equivalencia

#### Scenario: El nombre no coincide
- **WHEN** la plantilla dice «SEGUNDO» y «TRIUNFADORES» y la I.E. tiene 2.º A, B, C y D
- **THEN** el diálogo pide elegir entre las cuatro, con el foco en su título

#### Scenario: Guardar y completar
- **WHEN** la dirección elige 2.º B y toca «Guardar y completar»
- **THEN** sin volver a elegir el archivo, se guarda la equivalencia de TRIUNFADORES con 2.º B y se completa la plantilla en el mismo paso

#### Scenario: La siguiente plantilla
- **WHEN** después sube otra plantilla de 2.º TRIUNFADORES de ese año, de cualquier periodo
- **THEN** se completa con 2.º B sin preguntar

#### Scenario: Cancelar la elección
- **WHEN** toca «Cancelar» en «Elige la sección»
- **THEN** el diálogo se cierra sin guardar la equivalencia ni completar nada

#### Scenario: Sin secciones del grado
- **WHEN** la institución no tiene secciones de 2.º en el año de la plantilla
- **THEN** el campo dice «Tu I.E. no tiene secciones de 2.º grado en 2026.» y no se completa nada

#### Scenario: Una sección ya tiene equivalencia
- **WHEN** la dirección elige para 2.º TRIUNFADORES la sección 2.º B, que ya es la equivalencia de 2.º CAMPEONES
- **THEN** 2.º B no aparece entre las opciones; si llega a mano, se responde «La sección elegida no es válida. Elige una de la lista.»

### Requirement: Estudiantes de la plantilla
Cada fila SHALL cruzarse por su columna «Nombres» («APELLIDOS, NOMBRES») con los apellidos y nombres de los estudiantes de la sección, de cualquier estado, sin distinguir mayúsculas, tildes ni espacios y sin parecidos. Las columnas «ID» y «Cód. Estudiante» no se leen (RN-015). Una fila sin coincidencia, o con dos estudiantes de la sección que coinciden, no se toca y su nombre va a «No encontrados».

#### Scenario: Coincide con tildes distintas
- **WHEN** la plantilla dice «PEREZ QUISPE, MARIA» y la sección tiene «PÉREZ QUISPE, MARÍA»
- **THEN** su fila se completa

#### Scenario: Estudiante que no está en la sección
- **WHEN** la plantilla trae «DE LA LOMA DE PAPEL, AMARANTA LUZ», que no está en la sección
- **THEN** su fila queda como venía en todas las hojas y su nombre aparece una vez en «No encontrados»

#### Scenario: Sin parecidos
- **WHEN** la plantilla dice «PEREZ QUISPE, MARIA» y la sección tiene «PÉREZ QUISPE, MARÍA ELENA»
- **THEN** no se completa la fila y va a «No encontrados»

#### Scenario: Estudiante trasladado con notas
- **WHEN** la plantilla trae a un estudiante trasladado que tiene notas en el periodo
- **THEN** su fila se completa con esas notas

### Requirement: Llenado de la plantilla
Cada hoja de área SHALL identificarse por el código de área de su nombre (por ejemplo «0005-COMU») y cada competencia por su número de la fila 1 («01», «02»…), que es la primera, segunda… competencia activa del área en el orden del catálogo, sin importar la posición de la columna. Solo se escriben las celdas «NL» y «Conclusión descriptiva de la competencia» de las filas encontradas: si CarpetaDocente tiene la nota del estudiante en esa competencia y periodo, escribe su nivel y su conclusión, aunque la celda tenga otro valor, y con AD o A la conclusión queda vacía; si no la tiene, no toca las celdas. Las celdas sin nota quedan vacías, sin «Pendiente». El resto del libro (Parametros, Generalidades, las validaciones, los nombres de las hojas y de los archivos) queda igual. Se completa aunque la docente no haya entregado sus notas.

#### Scenario: Camino ideal
- **WHEN** la sección 2.º B tiene las notas del bimestre 3 y la dirección sube su plantilla vacía
- **THEN** recibe el mismo archivo con el nivel de logro y la conclusión de cada estudiante en cada competencia

#### Scenario: Columna por número
- **WHEN** en la hoja «063-MATE» la competencia «03» está en las columnas H e I
- **THEN** en H e I se escriben las notas de «Resuelve problemas de forma, movimiento y localización»

#### Scenario: Celda con otro valor
- **WHEN** la celda NL de un estudiante dice «A» y CarpetaDocente tiene «B» con su conclusión
- **THEN** la celda queda en «B» con la conclusión y cuenta como reemplazada

#### Scenario: Nota que CarpetaDocente no tiene
- **WHEN** la celda NL de un estudiante dice «A» y CarpetaDocente no tiene su nota en esa competencia
- **THEN** la celda sigue en «A»

#### Scenario: Se abre en Excel y LibreOffice
- **WHEN** se abre la plantilla completada
- **THEN** abre en Excel y en LibreOffice sin reparaciones, con la hoja Parametros oculta y las listas «A, AD, B, C» de las celdas NL (RNF-006)

### Requirement: Sin notas en el periodo
Si la sección no tiene ninguna nota en el periodo de la plantilla, el sistema MUST NOT completar ni devolver el archivo, y el diálogo SHALL mostrar «No hay notas para completar en este periodo».

#### Scenario: Periodo sin notas
- **WHEN** la dirección sube la plantilla del bimestre 4 de 2.º B, que aún no tiene notas
- **THEN** ve «No hay notas para completar en este periodo» en el mismo diálogo, no recibe el archivo y no queda entrada PLANTILLA_SIAGIE_COMPLETADA

#### Scenario: Equivalencia de un periodo sin notas
- **WHEN** la dirección elige 2.º B para TRIUNFADORES con una plantilla de un periodo sin notas
- **THEN** ve el mismo mensaje y la equivalencia no se guarda

### Requirement: Resumen del llenado
Al completarse, la pantalla SHALL mostrar el resumen: «Inicio de dirección» para volver; el título «Plantilla completada», o «Plantilla completada con observaciones» si hay no encontrados o faltan notas; «Sección de la I.E. 2.º B · Bimestre 3 · 2026» y «Sección en el SIAGIE 2.º TRIUNFADORES»; «Resultado del llenado» con cuatro conteos, que se ven aunque sean cero: «N estudiantes encontrados», «N no encontrados», «Faltan N notas» y «N celdas reemplazadas»; si hay no encontrados, «Estudiantes no encontrados» con «Sus filas quedaron intactas en la plantilla.» y la lista de nombres como venían en la plantilla; y «Archivo de salida» con «Plantilla de notas del SIAGIE (.xlsx)», «Descargar plantilla» y «Subir otra plantilla». «Faltan N notas» son las notas faltantes de la sección en el periodo, con la misma regla que la hoja de notas de la docente.

#### Scenario: Con observaciones
- **WHEN** se completa una plantilla con 26 estudiantes encontrados, 2 no encontrados, 3 notas faltantes y 4 celdas reemplazadas
- **THEN** el título es «Plantilla completada con observaciones», se ven los cuatro conteos y la lista con los 2 nombres

#### Scenario: Sin observaciones
- **WHEN** se completa una plantilla con los 28 estudiantes encontrados y sin faltantes ni reemplazos
- **THEN** el título es «Plantilla completada», se ven «28», «0», «Faltan 0» y «0», y no hay lista de nombres

#### Scenario: Descargar
- **WHEN** la dirección toca «Descargar plantilla»
- **THEN** descarga el .xlsx completado con el mismo nombre que tenía el archivo subido

#### Scenario: Subir otra
- **WHEN** toca «Subir otra plantilla»
- **THEN** se abre el diálogo de subida vacío

#### Scenario: Recargar el resumen
- **WHEN** la dirección recarga la pantalla del resumen
- **THEN** ve el inicio de la dirección, sin el resumen ni el archivo, y no se completa otra vez

### Requirement: Corregir la equivalencia
Cuando la sección del resumen salió de una equivalencia guardada (en ese llenado o antes), el resumen SHALL mostrar, junto a la sección de la I.E., el enlace «¿No es esta sección?». Al tocarlo se borra esa equivalencia, queda una entrada EQUIVALENCIA_SECCION_BORRADA y el panel «Archivo de salida» cambia a «Quitamos la equivalencia. La próxima plantilla de 2.º TRIUNFADORES te pedirá elegir la sección.» con «Subir plantilla otra vez», sin «Descargar plantilla». Si la sección salió del nombre, el enlace no aparece. Solo la dirección de la institución de la sección borra su equivalencia.

#### Scenario: Borrar una equivalencia equivocada
- **WHEN** la plantilla de 2.º TRIUNFADORES se completó con 2.º B por su equivalencia y la dirección toca «¿No es esta sección?»
- **THEN** la equivalencia se borra, el panel del archivo muestra el aviso con «Subir plantilla otra vez» y ya no ofrece la descarga

#### Scenario: La siguiente plantilla vuelve a preguntar
- **WHEN** después sube otra plantilla de 2.º TRIUNFADORES
- **THEN** el diálogo pide elegir la sección, con 2.º B entre las opciones

#### Scenario: Sección por su nombre
- **WHEN** la sección del resumen salió porque el nombre de la plantilla coincide con el de la I.E.
- **THEN** el resumen no muestra «¿No es esta sección?»

#### Scenario: Equivalencia de otra institución o ya borrada
- **WHEN** llega, con una petición armada a mano, el borrado de una equivalencia de otra institución, o de una que ya no existe
- **THEN** no se borra nada, no queda entrada y la respuesta dice «Esta equivalencia ya no existe.»

#### Scenario: Otro rol
- **WHEN** una docente o el Administrador pide el borrado
- **THEN** va a su pantalla de inicio y la equivalencia sigue

### Requirement: El archivo no se guarda
Ni la plantilla subida ni la completada MUST guardarse en la base de datos, en el almacén de archivos ni en el registro (Ley 29733): se procesan durante la petición y se devuelven en la misma respuesta (al guardar el libro, openpyxl escribe cada hoja en un archivo temporal del servidor y lo borra al terminar; en Vercel, `/tmp` es efímero). De la plantilla solo se guarda la equivalencia de la sección (el código y el nombre de la sección del SIAGIE).

#### Scenario: Después del llenado
- **WHEN** la dirección completa una plantilla
- **THEN** no queda ningún archivo en el almacén ni nombres de estudiantes de la plantilla en la base de datos ni en el registro

### Requirement: Pantalla accesible y sin desplazamiento horizontal
El diálogo de subida, el de elegir la sección y el resumen SHALL pasar axe sin infracciones en los temas claro y oscuro y no desplazarse en horizontal a 360 px.

#### Scenario: Accesibilidad
- **WHEN** se revisan con axe el diálogo de subida con el error, el de elegir la sección y el resumen con observaciones, en ambos temas
- **THEN** no hay infracciones

#### Scenario: 360 px
- **WHEN** se abre el resumen con un nombre no encontrado de 60 caracteres a 360 px
- **THEN** la página no se desplaza en horizontal
