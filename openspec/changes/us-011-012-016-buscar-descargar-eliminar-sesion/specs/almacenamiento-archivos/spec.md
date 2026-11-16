# Spec Delta

## ADDED Requirements

### Requirement: Entrega del archivo con enlace firmado
En Vercel, el archivo de una sesión SHALL entregarse redirigiendo, después de revisar el permiso, a un enlace firmado de R2 que vence a los 60 segundos y fija el nombre original y el modo (descarga o vista en el navegador). El bucket sigue privado y la clave del archivo MUST NOT aparecer en ninguna página. En la laptop y en las pruebas, sin R2, el aplicativo entrega el archivo él mismo, con el mismo nombre y modo.

#### Scenario: Descarga en Vercel
- **WHEN** una docente con permiso pide la descarga de una sesión en la vista previa
- **THEN** el aplicativo responde una redirección a un enlace firmado de R2 y el navegador guarda el archivo con su nombre original

#### Scenario: Enlace vencido
- **WHEN** alguien usa el enlace firmado pasados 60 segundos
- **THEN** R2 no entrega el archivo

#### Scenario: La página no trae enlaces de R2
- **WHEN** se revisa el HTML de la página de una sesión y de las listas
- **THEN** no contiene la clave del archivo ni una dirección de R2; solo enlaces del aplicativo

#### Scenario: Laptop y pruebas
- **WHEN** una docente con permiso pide la descarga sin variables de R2
- **THEN** el aplicativo responde el archivo con su tipo, su nombre original y el modo pedido, sin conectarse a R2

#### Scenario: Respuesta sin caché
- **WHEN** el aplicativo responde una descarga o una vista
- **THEN** la respuesta indica que no se guarde en caché

### Requirement: El archivo se borra con su sesión
Al eliminar una sesión, su archivo SHALL borrarse del almacenamiento después de confirmarse el borrado de la sesión; si la sesión no llega a borrarse, el archivo MUST seguir. Si el almacenamiento falla al borrar, la sesión queda eliminada igual y la clave del archivo queda en el log del servidor para borrarlo a mano.

#### Scenario: Sesión eliminada
- **WHEN** la autora elimina su sesión
- **THEN** el archivo ya no está en el almacenamiento

#### Scenario: Falla la base
- **WHEN** la base falla al eliminar la sesión
- **THEN** la sesión y su archivo siguen, sin entrada de actividad

#### Scenario: Falla el almacenamiento al borrar
- **WHEN** el almacenamiento rechaza el borrado del archivo después de eliminarse la sesión
- **THEN** la docente ve «Sesión eliminada», la sesión ya no existe y el log nombra la clave del archivo, sin el título ni la autora
