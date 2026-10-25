# Spec Delta

## Purpose

Controla la salida del sistema: el cierre de sesión que elige el usuario, el cierre automático por inactividad con su aviso y que, una vez cerrada la sesión, ninguna pantalla interna vuelva a mostrarse (RF-002, RN-025, RNF-015).

## ADDED Requirements

### Requirement: Cerrar sesión
El sistema SHALL terminar la sesión del usuario cuando este elige "Cerrar sesión" y SHALL llevarlo al inicio de sesión (`/ingresar/`), sin aviso. El cierre MUST hacerse solo con una petición POST que lleve el token CSRF; una petición GET MUST NOT cerrar la sesión.

#### Scenario: Camino ideal
- **WHEN** un docente con la sesión iniciada elige "Cerrar sesión" en el menú de la barra
- **THEN** la sesión termina y ve el inicio de sesión, sin aviso

#### Scenario: Dirección
- **WHEN** un usuario de la dirección elige "Cerrar sesión"
- **THEN** la sesión termina y ve el inicio de sesión

#### Scenario: Pedido GET
- **WHEN** alguien abre la dirección de cierre de sesión con GET
- **THEN** la sesión no se cierra y el sistema responde que el método no está permitido

#### Scenario: Sin sesión
- **WHEN** alguien sin sesión envía el cierre de sesión
- **THEN** llega al inicio de sesión, sin error

### Requirement: Cierre desde el panel de administración
El cierre de sesión del panel de administración SHALL terminar la sesión y llevar al inicio de sesión del sistema, no a una página propia del panel.

#### Scenario: Administrador cierra sesión en el panel
- **WHEN** el administrador elige cerrar sesión en el panel
- **THEN** la sesión termina y ve el inicio de sesión del sistema

### Requirement: Cierre por inactividad
La sesión de cualquier rol SHALL terminar cuando pasan 60 minutos sin ninguna petición del usuario (RN-025, RNF-015). Cada petición con la sesión vigente reinicia la cuenta. La petición que llega después de ese tiempo MUST NOT mostrar la pantalla pedida: lleva al inicio de sesión y, si era una consulta (GET), conserva la dirección pedida para volver a ella al ingresar.

#### Scenario: Petición a los 59 minutos
- **WHEN** un docente hace una petición 59 minutos después de la anterior
- **THEN** ve la pantalla pedida y la cuenta de inactividad vuelve a empezar

#### Scenario: Petición a los 60 minutos
- **WHEN** un docente hace una petición 60 minutos o más después de la anterior
- **THEN** la sesión termina y llega al inicio de sesión sin ver la pantalla pedida

#### Scenario: Volver a la pantalla pedida
- **WHEN** después del cierre por inactividad el docente ingresa de nuevo
- **THEN** llega a la pantalla que había pedido

#### Scenario: Envío después de la inactividad
- **WHEN** a los 60 minutos sin actividad el docente envía un formulario, por ejemplo "Cerrar sesión"
- **THEN** la sesión termina, llega al inicio de sesión con el aviso y, al ingresar, va a su pantalla de inicio y no a la dirección del envío

#### Scenario: Panel de administración
- **WHEN** el administrador hace una petición al panel 60 minutos después de la anterior
- **THEN** la sesión termina y llega al inicio de sesión del sistema

### Requirement: Aviso de cierre por inactividad
El inicio de sesión SHALL mostrar, una sola vez, el aviso "Tu sesión se cerró por inactividad." con la línea "Pasaron 60 minutos sin uso. Ingresa de nuevo para continuar." cuando la sesión terminó por inactividad. El aviso MUST NOT aparecer tras un cierre elegido por el usuario ni en un ingreso normal.

#### Scenario: Aviso tras la inactividad
- **WHEN** la sesión terminó por inactividad y el usuario llega al inicio de sesión
- **THEN** ve el aviso sobre el formulario, con su ícono y sus dos líneas

#### Scenario: El aviso no se repite
- **WHEN** el usuario recarga el inicio de sesión después de ver el aviso
- **THEN** el aviso ya no aparece

#### Scenario: Cierre elegido
- **WHEN** el usuario cerró sesión desde el menú
- **THEN** el inicio de sesión no muestra el aviso

### Requirement: Pantallas internas sin caché
Las respuestas de las pantallas con sesión iniciada MUST pedir al navegador que no las guarde ni las reutilice, para que el botón "atrás" no muestre información después de cerrar la sesión.

#### Scenario: Botón "atrás" tras cerrar sesión
- **WHEN** un usuario que ya cerró sesión vuelve a una pantalla interna con el botón "atrás" del navegador
- **THEN** no ve la información y llega al inicio de sesión

#### Scenario: Botón "atrás" tras el cierre por inactividad
- **WHEN** la sesión terminó por inactividad y el usuario vuelve con "atrás" a una pantalla interna
- **THEN** no ve la información y llega al inicio de sesión

### Requirement: Menú de la cuenta
Las pantallas internas de los roles SHALL mostrar en la barra un menú de la cuenta que, al abrirse, muestra el nombre del usuario y la opción "Cerrar sesión". El menú MUST funcionar con teclado y sin JavaScript, y abierto MUST NOT causar desplazamiento horizontal (RNF-005).

#### Scenario: Abrir el menú
- **WHEN** un docente toca el menú de la barra
- **THEN** ve su nombre (o su usuario si no tiene nombre) y "Cerrar sesión"

#### Scenario: Teclado
- **WHEN** el usuario abre el menú con el teclado y luego pulsa Escape
- **THEN** el menú se cierra y el foco vuelve al botón del menú

#### Scenario: Toque fuera del menú
- **WHEN** el menú está abierto y el usuario toca fuera de él
- **THEN** el menú se cierra

#### Scenario: Sin JavaScript
- **WHEN** el navegador no ejecuta JavaScript
- **THEN** el menú se abre y "Cerrar sesión" cierra la sesión igual

#### Scenario: Menú abierto a 320 px
- **WHEN** el menú está abierto a 320 px y a 360 px, en ambos temas
- **THEN** el ancho del documento no supera el de la ventana
