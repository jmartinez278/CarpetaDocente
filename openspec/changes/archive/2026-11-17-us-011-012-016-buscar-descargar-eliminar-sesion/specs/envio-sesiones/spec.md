# Spec Delta

## MODIFIED Requirements

### Requirement: Pantalla Sesiones
La docente SHALL tener la pantalla Sesiones en el marco del rebrand, con «Sesiones» en la barra, y debajo la cabecera de la página: el título «Sesiones» y el botón «Subir una sesión» en una misma fila, sin subtítulo, sin ícono ni franjas del tinte; bajo la cabecera van las pestañas «Mis sesiones» y «Repositorio» (spec `repositorio-sesiones`). En el celular el botón dice «Subir», con su signo «+», y su nombre accesible sigue siendo «Subir una sesión». La tarjeta Sesiones de la portada dice «Ver sesiones» y enlaza a esta pantalla.

#### Scenario: Primera visita
- **WHEN** una docente que no ha enviado sesiones abre la pantalla Sesiones
- **THEN** ve «Sesiones» en la barra, la cabecera con su título y el botón «Subir una sesión», sin subtítulo, las pestañas «Mis sesiones» y «Repositorio» y, en «Mis sesiones», el estado vacío «Aquí verás las sesiones que envíes y su estado.»

#### Scenario: Cabecera sin ícono ni franjas
- **WHEN** la docente abre la pantalla Sesiones
- **THEN** el título «Sesiones» no lleva ícono ni franjas del tinte de Sesiones

#### Scenario: Botón en el celular
- **WHEN** la docente abre la pantalla Sesiones a 360 px
- **THEN** el botón dice «Subir», va en la misma fila que el título, sin desplazamiento horizontal, y el lector de pantalla lo anuncia como «Subir una sesión»

#### Scenario: Portada sin cambio
- **WHEN** una docente, con o sin sección asignada, abre su portada
- **THEN** la tarjeta Sesiones dice «Ver sesiones» y lleva a la pantalla Sesiones

### Requirement: Envío exitoso
Al guardarse la sesión, el popup SHALL cerrarse y la pantalla Sesiones mostrar el Mensaje de éxito «Sesión enviada a la dirección» o «Sesión enviada a la dirección y compartida en el repositorio», con el título, el grado, el área, el nombre del archivo, su tipo y su tamaño (en el formato de `es-pe`), y el botón «Subir otra», que abre un formulario nuevo. La lista de la pestaña abierta y los contadores de las pestañas se actualizan sin recargar la página.

#### Scenario: Éxito sin compartir
- **WHEN** la docente envía «Leemos un cuento», 2.º grado, Comunicación, con un PDF de 1,2 MB, sin compartir
- **THEN** el popup se cierra y la pantalla dice «Sesión enviada a la dirección», con «Leemos un cuento», «2.º grado», «Comunicación», «leemos-un-cuento.pdf» y «PDF · 1,2 MB», y el anuncio llega al lector de pantalla

#### Scenario: Éxito compartida
- **WHEN** la misma sesión se envía con la casilla marcada y los términos aceptados
- **THEN** la pantalla dice «Sesión enviada a la dirección y compartida en el repositorio»

#### Scenario: La lista se actualiza
- **WHEN** la docente, en «Mis sesiones», envía su primera sesión
- **THEN** bajo el Mensaje el estado vacío da paso a la tarjeta de la sesión en el grupo «Hoy», con el chip «Enviada», y el contador de «Mis sesiones» dice 1

#### Scenario: Recargar después del éxito
- **WHEN** la docente recarga la pantalla después del éxito
- **THEN** ve la pantalla sin el Mensaje, con la sesión en su lista, y no se envía otra sesión

### Requirement: Sesión guardada
Cada envío válido SHALL guardar una sesión de la institución de la docente, con ella como autora y quien la subió, el grado, el área, el título, el propósito, origen PROPIA, estado ENVIADA, si se compartió, la fecha y hora de aceptación solo si se compartió, del archivo su nombre original, su tipo y su tamaño, y el texto transcrito del archivo si se pudo extraer. Una sesión compartida siempre tiene fecha de aceptación; una que dejó de compartirse la conserva.

#### Scenario: Datos guardados
- **WHEN** la docente envía una sesión sin compartir
- **THEN** la sesión queda con esos datos, estado ENVIADA, no compartida y sin fecha de aceptación

#### Scenario: Coherencia en la base
- **WHEN** se intenta guardar una sesión compartida sin fecha de aceptación, o una de más de 4 MB
- **THEN** la base de datos la rechaza

#### Scenario: No compartida con fecha
- **WHEN** una sesión compartida deja de compartirse
- **THEN** la base de datos la acepta como no compartida con su fecha de aceptación
