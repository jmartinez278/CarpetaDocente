# repositorio-sesiones Specification

## Purpose
Permite que la docente encuentre las sesiones que envió («Mis sesiones») y busque, por palabra, grado y área, las que sus colegas compartieron en el repositorio de su institución (US-011).

## Requirements

### Requirement: Pestañas de Sesiones
La pantalla Sesiones SHALL tener, bajo la cabecera, las pestañas «Mis sesiones» y «Repositorio», cada una con su contador y con su propia dirección; la pantalla abre en «Mis sesiones». Las pestañas MUST manejarse con el teclado y el foco no se pierde al cambiar de pestaña.

#### Scenario: Contadores
- **WHEN** una docente con 2 sesiones enviadas abre Sesiones en una institución con 8 sesiones compartidas
- **THEN** ve «Mis sesiones 2» y «Repositorio 8», con «Mis sesiones» marcada como la pestaña actual

#### Scenario: Cambiar de pestaña
- **WHEN** la docente toca «Repositorio»
- **THEN** ve la lista del repositorio, la dirección cambia a la del repositorio y «atrás» vuelve a «Mis sesiones»

#### Scenario: Teclado
- **WHEN** la docente, con el foco en una pestaña, pulsa la flecha derecha o izquierda
- **THEN** el foco y la selección pasan a la otra pestaña y se muestra su lista

#### Scenario: Abrir el repositorio por su dirección
- **WHEN** la docente abre la dirección del repositorio, con o sin filtros en ella
- **THEN** ve «Repositorio» como pestaña actual, con esos filtros aplicados

### Requirement: Mis sesiones
«Mis sesiones» SHALL listar todas las sesiones que la docente envió, compartidas o no, de la más reciente a la más antigua, agrupadas por día de envío en hora de Lima («Hoy», «Ayer», «lun 2 nov»). Cada tarjeta lleva el chip «Enviada» y, si corresponde, «Compartida». La lista muestra 20 y «Ver más» agrega las siguientes.

#### Scenario: Agrupadas por día
- **WHEN** la docente envió dos sesiones hoy, una ayer y una el lunes 2 de noviembre
- **THEN** ve los grupos «Hoy» (2), «Ayer» (1) y «lun 2 nov» (1), en ese orden, y dentro de cada grupo la más reciente primero

#### Scenario: Chips
- **WHEN** una de sus sesiones está compartida y otra no
- **THEN** la primera lleva «Enviada» y «Compartida», y la segunda solo «Enviada»

#### Scenario: Solo las suyas
- **WHEN** una colega de la misma institución envió sesiones, compartidas o no
- **THEN** ninguna aparece en «Mis sesiones» de la docente

#### Scenario: Ver más
- **WHEN** la docente tiene 25 sesiones y toca «Ver más»
- **THEN** ve las 25, sin repetir ninguna, las nuevas quedan en su grupo de día y «Ver más» desaparece

#### Scenario: Sin envíos
- **WHEN** una docente que no ha enviado ninguna sesión abre «Mis sesiones»
- **THEN** ve el estado vacío «Aquí verás las sesiones que envíes y su estado.» y el contador en 0

### Requirement: Repositorio de la institución
«Repositorio» SHALL listar solo las sesiones compartidas de la institución de la docente, incluidas las suyas y el material de referencia de su institución, de la más reciente a la más antigua, con el título de resultados («8 sesiones compartidas»; con filtros, «3 sesiones»). La lista muestra 20 y «Ver más» agrega las siguientes. Una sesión no compartida o de otra institución MUST NOT aparecer.

#### Scenario: Compartidas de la institución
- **WHEN** en la institución hay 3 sesiones compartidas (una de la docente) y 2 no compartidas de colegas
- **THEN** la docente ve las 3 compartidas y el título «3 sesiones compartidas»

#### Scenario: Otra institución
- **WHEN** otra institución tiene sesiones compartidas
- **THEN** no aparecen ni cuentan en el repositorio de la docente

#### Scenario: Una sola
- **WHEN** hay una sola sesión compartida
- **THEN** el título dice «1 sesión compartida»

#### Scenario: Repositorio vacío
- **WHEN** nadie de la institución ha compartido una sesión
- **THEN** la docente ve «Comparte una de tus sesiones», con un enlace que lleva a «Mis sesiones»

#### Scenario: Con material de referencia
- **WHEN** en la institución hay 2 sesiones compartidas por docentes y 3 de referencia, y otra institución tiene 1 de referencia
- **THEN** la docente ve las 5 de su institución, el título «5 sesiones compartidas» y la pestaña «Repositorio 5»

### Requirement: Tarjeta de sesión
Cada sesión de una lista SHALL mostrarse como una tarjeta con una página dibujada con las primeras líneas de su texto y la etiqueta «PDF» o «Word», el título, «grado · área», la autora y la fecha de envío. Toda la tarjeta es un solo enlace a la página de la sesión; no tiene botón de descarga. La página dibujada es decorativa para el lector de pantalla y no usa un color por área.

#### Scenario: Con texto
- **WHEN** se lista «Leemos un cuento sobre la amistad», 1.º grado, Comunicación, PDF, de Bruno García Alarcón, enviada el 5 de noviembre
- **THEN** la tarjeta muestra las primeras líneas de su texto, «PDF», el título, «1.º grado · Comunicación» y «Bruno García Alarcón · 5 nov», y tocar cualquier parte abre su página

#### Scenario: Sin texto
- **WHEN** la sesión es un PDF escaneado, sin texto
- **THEN** la página dibujada muestra un ícono de documento y el área, con su etiqueta «PDF»

#### Scenario: Nombre accesible
- **WHEN** un lector de pantalla llega a la tarjeta
- **THEN** anuncia un solo enlace, «Abrir Leemos un cuento sobre la amistad», y no lee las líneas de la página dibujada

### Requirement: Búsqueda por palabra
El repositorio SHALL buscar las palabras que la docente escribe en el título, el propósito y el texto transcrito de cada sesión, sin distinguir tildes ni mayúsculas. Con varias palabras, la sesión debe contenerlas todas, en cualquier orden y en cualquiera de esos tres lugares. La lista se actualiza mientras escribe, sin recargar la página ni quitarle el foco, y también al enviar el formulario.

#### Scenario: Flujo alternativo válido (palabra clave)
- **GIVEN** un docente que busca la palabra "fracciones"
- **WHEN** no aplica ningún otro filtro
- **THEN** el sistema lista las sesiones del repositorio cuyo título o datos contienen esa palabra

#### Scenario: Tildes y mayúsculas
- **WHEN** la docente busca «RECOMENDACION» y hay una sesión titulada «Escribimos recomendaciones para cuidar el agua» y otra cuyo propósito dice «una recomendación»
- **THEN** ve las dos

#### Scenario: Palabra que solo está en el archivo
- **WHEN** la docente busca «lista de cotejo» y esas palabras solo están en el texto transcrito de una sesión
- **THEN** ve esa sesión

#### Scenario: Varias palabras
- **WHEN** la docente busca «agua escuela»
- **THEN** ve solo las sesiones que contienen las dos palabras

#### Scenario: Mientras escribe
- **WHEN** la docente escribe «fracc» en el buscador
- **THEN** la lista y el título de resultados se actualizan, el foco sigue en el buscador con lo escrito y el nuevo total se anuncia al lector de pantalla

#### Scenario: Borrar la búsqueda
- **WHEN** la docente toca «Borrar búsqueda»
- **THEN** el buscador queda vacío, con el foco, y la lista vuelve a mostrar lo que dejan los demás filtros

#### Scenario: Búsqueda muy larga o con comodines
- **WHEN** llega una búsqueda de más de 100 caracteres o con «%» o «_»
- **THEN** el sistema responde sin error: usa los primeros 100 caracteres y trata esos signos como texto

### Requirement: Filtros de grado y área
El repositorio SHALL filtrar por un grado (1.º a 6.º) y por un área de las que la institución trabaja, en el orden del SIAGIE; se combinan entre sí y con la búsqueda, y se aplican al tocar. Cada área muestra cuántas sesiones tiene con la búsqueda y el grado vigentes; las de 0 se ven atenuadas y no se pueden elegir. «Borrar todo» quita la búsqueda y los filtros.

#### Scenario: Camino ideal (grado y área)
- **GIVEN** un repositorio con sesiones de varios grados y áreas
- **WHEN** el docente filtra por "3.° grado" y "Comunicación"
- **THEN** el sistema lista solo las sesiones del repositorio que cumplen ambos filtros

#### Scenario: Conteo por área
- **WHEN** hay 3 sesiones compartidas de Comunicación, 2 de Matemática y ninguna de Arte y Cultura
- **THEN** «Todas las áreas» dice 5, Comunicación 3, Matemática 2 y Arte y Cultura 0, atenuada y sin poder elegirse

#### Scenario: Quitar un grado
- **WHEN** la docente toca otra vez el grado que tenía elegido
- **THEN** el filtro de grado se quita y la lista se actualiza

#### Scenario: Filtros en la dirección
- **WHEN** la docente filtra por 3.º grado y Comunicación y recarga la página
- **THEN** ve la misma lista con los mismos filtros marcados

#### Scenario: Valores que no existen
- **WHEN** llega un grado 7, un área que la institución no trabaja o un valor que no es un número
- **THEN** ese filtro se ignora y el sistema responde sin error

### Requirement: Filtros activos
Con una búsqueda o un filtro puesto, el repositorio SHALL mostrar los filtros activos como un grupo con el nombre accesible «Filtros activos», cada uno con su botón para quitarlo. Sin filtros, el grupo no existe en la página.

#### Scenario: Un filtro activo
- **WHEN** la docente filtra por 3.º grado y busca «agua»
- **THEN** ve «3.º grado» y «agua» como filtros activos, cada uno con «Quitar filtro …», dentro de un grupo llamado «Filtros activos»

#### Scenario: Quitar uno
- **WHEN** la docente quita «3.º grado» de los filtros activos
- **THEN** la lista se actualiza solo con la búsqueda «agua» y el grado deja de estar marcado

#### Scenario: Sin filtros
- **WHEN** no hay búsqueda ni filtros
- **THEN** la página no tiene el grupo «Filtros activos»

### Requirement: Filtros en el celular
Hasta 699 px, los filtros SHALL estar en un panel que abre el botón «Filtrar», junto al buscador; el botón indica cuántos filtros hay puestos. En la PC van en una barra a la izquierda de los resultados. El panel se cierra con su botón «Cerrar filtros», con Esc o tocando fuera, y el foco vuelve a «Filtrar».

#### Scenario: Abrir y filtrar
- **WHEN** la docente, a 360 px, toca «Filtrar» y elige «3.º»
- **THEN** el panel se abre con el foco dentro, la lista de atrás se actualiza al tocar y, al cerrar el panel, «Filtrar» muestra 1

#### Scenario: Cerrar
- **WHEN** la docente pulsa Esc o toca «Cerrar filtros»
- **THEN** el panel se cierra y el foco vuelve a «Filtrar»

#### Scenario: PC
- **WHEN** la docente abre el repositorio a 1280 px
- **THEN** ve los filtros a la izquierda de los resultados y no ve el botón «Filtrar»

### Requirement: Sin coincidencias
Si ninguna sesión compartida cumple la búsqueda y los filtros, el repositorio SHALL mostrar «No se encontraron sesiones con esos filtros» y el botón «Borrar filtros», que los quita todos.

#### Scenario: Caso de error (sin coincidencias)
- **GIVEN** una búsqueda sin coincidencias
- **WHEN** el docente aplica los filtros
- **THEN** el sistema muestra el mensaje "No se encontraron sesiones con esos filtros"

#### Scenario: Borrar filtros
- **WHEN** la docente toca «Borrar filtros»
- **THEN** el buscador y los filtros quedan vacíos y ve todas las sesiones compartidas

### Requirement: Texto transcrito
Al enviar una sesión, el sistema SHALL extraer el texto de su archivo (.docx o PDF con capa de texto) y guardarlo con la sesión, recortado a 100 000 caracteres; de un PDF se leen como máximo sus primeras 40 páginas. Si la extracción falla o no hay texto, la sesión MUST enviarse igual, sin texto. Las sesiones enviadas antes se procesan una vez con un comando del equipo.

#### Scenario: Word
- **WHEN** la docente envía un .docx cuyo cuerpo dice «Formamos equipos»
- **THEN** la sesión guarda ese texto y aparece al buscar «equipos»

#### Scenario: PDF con texto
- **WHEN** la docente envía un PDF con capa de texto
- **THEN** la sesión guarda su texto

#### Scenario: PDF escaneado
- **WHEN** la docente envía un PDF que solo tiene imágenes
- **THEN** la sesión se envía con el mismo éxito y queda sin texto

#### Scenario: Archivo que no se puede leer
- **WHEN** la extracción falla por un archivo dañado, cifrado o demasiado grande al descomprimir
- **THEN** la sesión se envía con el mismo éxito, queda sin texto y la docente no ve ningún error

#### Scenario: Sesiones anteriores
- **WHEN** el equipo corre el comando sobre sesiones enviadas antes de este cambio
- **THEN** cada una queda con su texto, o sin texto si no se pudo leer, y volver a correrlo no cambia las que ya lo tienen

### Requirement: Listas solo del rol Docente
«Mis sesiones» y «Repositorio» MUST ser solo del rol Docente, tenga o no sección asignada. La dirección y el Administrador van a su pantalla de inicio y una visita sin sesión, al ingreso. Desde US-040, la dirección ve las sesiones de su institución (RN-019) solo desde la pestaña Sesiones del detalle de una sección (spec `consolidados-direccion`), no en estas listas.

#### Scenario: Docente sin sección
- **WHEN** una docente sin sección en el año ABIERTO abre el repositorio
- **THEN** ve las sesiones compartidas de su institución

#### Scenario: Otro rol o sin sesión
- **WHEN** la dirección, el Administrador o una visita sin sesión piden «Mis sesiones» o el repositorio, con o sin filtros
- **THEN** el sistema los lleva a su inicio o al ingreso y no muestra ninguna sesión

### Requirement: Listas accesibles y sin desplazamiento horizontal
«Mis sesiones», «Repositorio» y el panel de filtros MUST NOT tener infracciones graves de axe en ambos temas ni desplazamiento horizontal a 360 px; cada control mide 44 px o más.

#### Scenario: Revisión de las listas
- **WHEN** se revisan «Mis sesiones» y «Repositorio» con sesiones, y el panel de filtros abierto, a 360 px en claro y oscuro
- **THEN** axe no reporta infracciones graves, la página no se desplaza en horizontal y cada control mide al menos 44 px

#### Scenario: Título largo
- **WHEN** una sesión tiene un título de 200 caracteres sin espacios
- **THEN** la tarjeta lo parte en varias líneas y la página no se desplaza en horizontal

### Requirement: Material de referencia en las listas
Una sesión de referencia SHALL mostrarse en el repositorio con la misma tarjeta, pero con «Material de referencia» en el lugar de la autora y sus grados como rango («3.º–5.º grado»). El filtro de grado MUST encontrarla con cualquier grado de su rango, y el conteo por área la cuenta una vez. No aparece en «Mis sesiones» de nadie.

#### Scenario: Tarjeta
- **WHEN** se lista «Contamos y agrupamos objetos», de 3.º a 5.º grado, Matemática, cargada el 10 de noviembre
- **THEN** la tarjeta muestra el título, «3.º–5.º grado · Matemática» y «Material de referencia · 10 nov», sin el nombre de una persona

#### Scenario: Un solo grado
- **WHEN** la sesión de referencia es solo de 2.º grado
- **THEN** la tarjeta dice «2.º grado · …», como la de una docente

#### Scenario: Filtrar por un grado del rango
- **WHEN** la docente filtra por 4.º grado
- **THEN** ve la sesión de referencia de 3.º a 5.º, y no la ve si filtra por 6.º

#### Scenario: Conteo por área
- **WHEN** hay una sesión de referencia de Matemática de 3.º a 5.º y ningún filtro de grado
- **THEN** Matemática suma 1, no 3

#### Scenario: No está en Mis sesiones
- **WHEN** la docente abre «Mis sesiones»
- **THEN** no ve ninguna sesión de referencia y su contador no las cuenta
