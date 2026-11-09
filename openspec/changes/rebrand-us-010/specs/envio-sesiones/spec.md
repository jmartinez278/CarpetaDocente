## MODIFIED Requirements

### Requirement: Pantalla Sesiones
La docente SHALL tener la pantalla Sesiones en el marco del rebrand, con «Sesiones» en la barra, y debajo la cabecera de la página (título «Sesiones» y el subtítulo «Planificación de sesiones de aprendizaje», sin ícono ni franjas del tinte), el botón «Subir una sesión» y el estado vacío «Aquí verás las sesiones que envíes y su estado.», sin lista de sesiones. La tarjeta Sesiones de la portada sigue en «Próximamente».

#### Scenario: Primera visita
- **WHEN** una docente abre la pantalla Sesiones escribiendo su dirección
- **THEN** ve «Sesiones» en la barra, la cabecera con su título y subtítulo, el botón «Subir una sesión» y el estado vacío, y ninguna lista

#### Scenario: Cabecera sin ícono ni franjas
- **WHEN** la docente abre la pantalla Sesiones
- **THEN** el título «Sesiones» no lleva ícono ni franjas del tinte de Sesiones

#### Scenario: Botón en el celular
- **WHEN** la docente abre la pantalla Sesiones a 360 px
- **THEN** «Subir una sesión» se lee completo y, si no cabe junto al título, va debajo de la cabecera, sin desplazamiento horizontal

#### Scenario: Portada sin cambio
- **WHEN** la docente abre su portada
- **THEN** la tarjeta Sesiones sigue en «Próximamente», sin enlace a la pantalla

### Requirement: Pantalla accesible y sin desplazamiento horizontal
La pantalla Sesiones, el formulario, los términos, los errores, la subida y el éxito MUST NOT tener infracciones graves de axe en ambos temas, a 360 y 1280 px, ni desplazamiento horizontal, con el marco del rebrand (barra con ☰ y cuenta) cerrado; los objetivos táctiles miden 44 px o más. Cada error queda asociado a su campo y el teclado alcanza el cuerpo del popup.

#### Scenario: Estados del boceto
- **WHEN** se revisan los estados 1, 2, 3, 4a, 5, 6a, 6b, 7, 8, 9 y 10 del boceto en claro y oscuro, a 360 y 1280 px, con el ☰ y la cuenta cerrados
- **THEN** axe no reporta infracciones graves, la página no se desplaza en horizontal y cada control mide al menos 44 px

#### Scenario: Pantalla baja
- **WHEN** el popup de los términos no cabe en la altura de la pantalla
- **THEN** su cuerpo se desplaza y «Acepto y envío» y «Volver» siguen a la vista
