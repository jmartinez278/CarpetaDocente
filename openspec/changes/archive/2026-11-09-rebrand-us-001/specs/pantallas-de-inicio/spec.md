## MODIFIED Requirements

### Requirement: Pantalla de inicio de sesión
La pantalla de inicio de sesión SHALL mostrar, en este orden, el nombre "I.E. Virgen del Carmen", "Huayucachi", "Sesiones · Notas · Asistencia", el formulario con Usuario, Contraseña, el botón "Ingresar" y la ayuda "Si olvidaste tu contraseña, pide al administrador que la restablezca.", y al final el pie "CarpetaDocente · 2026". No muestra logo ni escudo, ni enlaces a funciones que no existen. Desde US-003 el campo Usuario lleva debajo la pista de una línea "Ejemplo: jperez (inicial y apellido)", asociada al campo para el lector de pantalla. Desde el rebrand, tras un ingreso rechazado el mensaje de error MUST recibir el foco al cargar la página y el lector de pantalla MUST anunciarlo una sola vez.

#### Scenario: Contenido de la pantalla
- **WHEN** alguien sin sesión abre `/ingresar/`
- **THEN** ve el nombre de la I.E., el lugar, las tres dimensiones, el formulario con su ayuda y el pie, sin escudo, sin menú y sin un enlace para recuperar la contraseña

#### Scenario: Pista del campo Usuario
- **WHEN** alguien sin sesión abre `/ingresar/`
- **THEN** bajo el campo Usuario ve "Ejemplo: jperez (inicial y apellido)" en una línea, y el lector de pantalla la anuncia como descripción del campo, también cuando el campo muestra un error

#### Scenario: Mensaje de error sobre el formulario
- **WHEN** un ingreso es rechazado
- **THEN** el mensaje aparece sobre la tarjeta del formulario, con ícono, la primera línea destacada y la segunda en el color del texto, recibe el foco al cargar la página y el lector de pantalla lo anuncia una sola vez

#### Scenario: Error y teclado
- **WHEN** un ingreso es rechazado y el usuario pulsa Tab desde el mensaje enfocado
- **THEN** el foco pasa al campo Usuario, que conserva lo escrito

### Requirement: Accesibilidad en ambos temas
Cada pantalla nueva MUST pasar la revisión automática de accesibilidad (WCAG 2.1, niveles A y AA) sin infracciones críticas ni graves, en tema claro y en tema oscuro, a 360 px y a 1280 px (RNF-008, DoD 7). El contraste de texto queda incluido en la revisión.

#### Scenario: Revisión de cada pantalla
- **WHEN** se ejecuta la revisión automática sobre el inicio de sesión con el marco del rebrand (normal, con error, con campos vacíos, «Ingresando…» y con el aviso de inactividad), la portada del docente y el inicio de la dirección (cada una con el menú cerrado y abierto) y «sin permiso» (con el ☰ y el menú de la cuenta cerrados, con el ☰ abierto y con el menú de la cuenta abierto), en ambos temas y en ambos anchos
- **THEN** no hay infracciones críticas ni graves
