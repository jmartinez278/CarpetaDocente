# Spec Delta

## Purpose

Define lo que ve cada rol al entrar: la pantalla de inicio de sesión, la portada del docente con las tres dimensiones y el inicio de la dirección, sobre el marco visual común de DESIGN.md, en tema claro y oscuro, accesible y liviano para datos móviles.

## ADDED Requirements

### Requirement: Pantalla de inicio de sesión
La pantalla de inicio de sesión SHALL mostrar, en este orden, el nombre "I.E. Virgen del Carmen", "Huayucachi", "Sesiones · Notas · Asistencia", el formulario con Usuario, Contraseña, el botón "Ingresar" y la ayuda "Si olvidaste tu contraseña, pide al administrador que la restablezca.", y al final el pie "CarpetaDocente · 2026". No muestra logo ni escudo, ni enlaces a funciones que no existen.

#### Scenario: Contenido de la pantalla
- **WHEN** alguien sin sesión abre `/ingresar/`
- **THEN** ve el nombre de la I.E., el lugar, las tres dimensiones, el formulario con su ayuda y el pie, sin escudo, sin menú y sin un enlace para recuperar la contraseña

#### Scenario: Mensaje de error sobre el formulario
- **WHEN** un ingreso es rechazado
- **THEN** el mensaje aparece sobre la tarjeta del formulario, con ícono, la primera línea destacada y la segunda en el color del texto, y lo anuncia el lector de pantalla

### Requirement: Mostrar la contraseña
El campo de contraseña SHALL tener un botón "Mostrar contraseña" que alterna entre ver y ocultar lo escrito e informa su estado al lector de pantalla. Sin JavaScript, el botón no aparece y el campo funciona como siempre. Al enviar el formulario, la contraseña vuelve a ocultarse.

#### Scenario: Ver la contraseña
- **WHEN** el usuario toca "Mostrar contraseña"
- **THEN** la contraseña se ve en texto y el botón queda marcado como presionado; al tocarlo otra vez, se oculta

#### Scenario: Sin JavaScript
- **WHEN** la página se abre sin JavaScript
- **THEN** el botón no aparece y el formulario se puede enviar igual

### Requirement: Estado de envío
Mientras se envía el formulario, el botón SHALL decir "Ingresando…" con un fondo distinto del normal y los dos campos MUST quedar de solo lectura, para que el cambio no dependa solo del texto y no se envíe dos veces.

#### Scenario: Envío en curso
- **WHEN** el usuario toca "Ingresar" con los dos campos llenos
- **THEN** el botón cambia a "Ingresando…" con el fondo de envío y los campos quedan de solo lectura hasta que llega la respuesta

### Requirement: Portada del docente
La portada del docente SHALL saludar al docente por su nombre y mostrar las tarjetas de las tres dimensiones en este orden: Sesiones, Notas y Asistencia, cada una con su título corto, su subtítulo formal y su miniatura esquemática, sin ningún dato que pueda leerse como un registro del docente.

#### Scenario: Portada al entrar
- **WHEN** un docente entra al sistema
- **THEN** ve "Hola," con su nombre y las tres tarjetas en orden, con sus subtítulos "Planificación de sesiones de aprendizaje", "Registro y control de notas" y "Control de asistencia"

### Requirement: Disponibilidad de cada dimensión
Cada dimensión SHALL tener una bandera de disponibilidad que activa la historia que construye su pantalla. Una dimensión no disponible se muestra como "Próximamente" y nunca se oculta; una disponible enlaza a su pantalla. Ninguna tarjeta MUST enlazar a una página que no existe. Al cerrar US-001, las tres están en "Próximamente".

#### Scenario: Tres dimensiones en "Próximamente"
- **WHEN** un docente abre la portada al cerrar US-001
- **THEN** las tres tarjetas muestran la insignia "Próximamente" y ninguna contiene un enlace

#### Scenario: Toque en una tarjeta "Próximamente"
- **WHEN** el docente toca una tarjeta "Próximamente"
- **THEN** la página no cambia de dirección y la tarjeta muestra "Llegará en una próxima versión." durante unos segundos, en un aviso que anuncia el lector de pantalla y que no mueve el resto de la tarjeta

#### Scenario: Dimensión activada por su historia
- **WHEN** la historia de una dimensión activa su bandera
- **THEN** su tarjeta pasa a disponible, con el verbo de su acción ("Ver sesiones", "Registrar notas" o "Registrar asistencia") y un enlace a su pantalla, y toda la tarjeta responde al toque

#### Scenario: Bandera activa sin pantalla
- **WHEN** se activa la bandera de una dimensión cuya pantalla no existe
- **THEN** las pruebas automáticas fallan antes de que el cambio pueda fusionarse

### Requirement: Carrusel de dimensiones en el celular
Por debajo de 960 px de ancho, las tarjetas SHALL mostrarse en un carrusel que se desplaza en horizontal dentro de su propio contenedor, con chips tocables de 44 px como mínimo que llevan a cada tarjeta y puntos de paginación visibles; la página no se desplaza en horizontal. Desde 960 px, las tres tarjetas van en fila.

#### Scenario: Chip de una tarjeta
- **WHEN** en un celular de 360 px el docente toca el chip "Notas"
- **THEN** el carrusel muestra la tarjeta Notas, el chip y el punto de Notas quedan marcados como actuales, y la dirección y el historial del navegador no cambian

#### Scenario: Carrusel sin JavaScript
- **WHEN** la portada se abre sin JavaScript
- **THEN** las tres tarjetas siguen accesibles con el desplazamiento y con los chips, que funcionan como enlaces a cada tarjeta

#### Scenario: Tarjeta inicial
- **WHEN** el docente abre la portada en el celular
- **THEN** el carrusel muestra la primera dimensión disponible en el orden de las tarjetas o, si no hay ninguna, la primera tarjeta

#### Scenario: Computadora
- **WHEN** la portada se abre a 1280 px
- **THEN** las tres tarjetas se ven en fila, sin chips ni puntos

### Requirement: Inicio de la dirección
El inicio de la dirección SHALL saludar al usuario por su nombre y mostrar, mientras no exista el panel de consolidados (US-040), el estado vacío "Los consolidados de notas y asistencia estarán aquí en una próxima versión."

#### Scenario: Inicio de la dirección en el Sprint 1
- **WHEN** un usuario de la dirección entra al sistema
- **THEN** ve su saludo, el título "Consolidados" y el estado vacío con su ícono, sin tablas ni datos

### Requirement: Marco común
Las pantallas de inicio de los roles SHALL compartir una barra superior fija con el nombre "I.E. Virgen del Carmen" y el pie "CarpetaDocente · 2026". En US-001 la barra no tiene menú.

#### Scenario: Barra y pie
- **WHEN** un docente o la dirección abre su pantalla de inicio
- **THEN** ve la barra con el nombre de la I.E., sin menú, y el pie al final

### Requirement: Temas claro y oscuro
Cada pantalla SHALL seguir la preferencia de tema del sistema operativo, con los mismos tokens de DESIGN.md en sus valores claros u oscuros, sin un selector de tema. Las plantillas MUST NOT escribir colores hexadecimales ni estilos en línea: solo usan las clases de los tokens.

#### Scenario: Preferencia oscura
- **WHEN** el sistema operativo prefiere el tema oscuro
- **THEN** las pantallas se ven con los valores oscuros de los tokens

#### Scenario: Plantillas sin colores escritos
- **WHEN** se revisan las plantillas del proyecto
- **THEN** ninguna contiene un color hexadecimal ni un atributo de estilo en línea

### Requirement: Accesibilidad en ambos temas
Cada pantalla nueva MUST pasar la revisión automática de accesibilidad (WCAG 2.1, niveles A y AA) sin infracciones críticas ni graves, en tema claro y en tema oscuro, a 360 px y a 1280 px (RNF-008, DoD 7). El contraste de texto queda incluido en la revisión.

#### Scenario: Revisión de cada pantalla
- **WHEN** se ejecuta la revisión automática sobre el inicio de sesión (normal, con error y con campos vacíos), la portada del docente y el inicio de la dirección, en ambos temas y en ambos anchos
- **THEN** no hay infracciones críticas ni graves

### Requirement: Sin desplazamiento horizontal
Ninguna pantalla nueva SHALL desplazarse en horizontal entre 320 px y 1280 px de ancho, en ningún tema; la única excepción es el carrusel de dimensiones dentro de su contenedor (RNF-005).

#### Scenario: Pantallas a 320 px
- **WHEN** cada pantalla nueva se abre a 320 px y a 360 px, en ambos temas
- **THEN** el ancho del documento no supera el de la ventana

### Requirement: Carga en conexión lenta
La pantalla de inicio de sesión MUST transferir 2 MB o menos y quedar usable en 5 segundos o menos con el perfil Slow 4G de Chrome DevTools y sin caché (RNF-002).

#### Scenario: Primera visita con Slow 4G
- **WHEN** un navegador sin caché, con el perfil Slow 4G, abre `/ingresar/`
- **THEN** se transfieren 2 MB o menos y el botón "Ingresar" está visible y habilitado, con la página cargada, en 5 segundos o menos
