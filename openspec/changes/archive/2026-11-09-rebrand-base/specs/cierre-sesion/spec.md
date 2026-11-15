## MODIFIED Requirements

### Requirement: Menú de la cuenta
Las pantallas internas de los roles SHALL mostrar en la barra un menú de la cuenta que, al abrirse, muestra "Tu cuenta", el nombre del usuario, "I.E. Virgen del Carmen" y, al final, la opción "Cerrar sesión". Para una docente con secciones en el año ABIERTO, bajo la I.E. va la línea de sus secciones con el mismo texto de la portada ("2.º grado, sección A", varias separadas por " · "); sin sección, o para la dirección, esa línea no aparece. El menú MUST funcionar con teclado y sin JavaScript, y abierto MUST NOT causar desplazamiento horizontal (RNF-005).

#### Scenario: Abrir el menú
- **WHEN** un docente toca el menú de la barra
- **THEN** ve "Tu cuenta", su nombre (o su usuario si no tiene nombre), "I.E. Virgen del Carmen" y "Cerrar sesión" al final

#### Scenario: Docente con sección
- **WHEN** una docente con "2.º grado, sección A" en el año ABIERTO abre el menú de la cuenta
- **THEN** bajo "I.E. Virgen del Carmen" ve "2.º grado, sección A"; con dos secciones, ve las dos separadas por " · ", ordenadas por grado y nombre

#### Scenario: Docente sin sección
- **WHEN** una docente sin sección en el año ABIERTO, o con su única sección en un año CERRADO, abre el menú de la cuenta
- **THEN** ve "Tu cuenta", su nombre, la I.E. y "Cerrar sesión", sin línea de sección

#### Scenario: Dirección
- **WHEN** un usuario de la dirección abre el menú de la cuenta
- **THEN** ve "Tu cuenta", su nombre, la I.E. y "Cerrar sesión", sin línea de sección

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
