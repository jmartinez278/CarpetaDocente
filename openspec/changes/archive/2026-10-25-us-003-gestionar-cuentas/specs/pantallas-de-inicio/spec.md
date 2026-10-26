# Spec Delta

## MODIFIED Requirements

### Requirement: Pantalla de inicio de sesión
La pantalla de inicio de sesión SHALL mostrar, en este orden, el nombre "I.E. Virgen del Carmen", "Huayucachi", "Sesiones · Notas · Asistencia", el formulario con Usuario, Contraseña, el botón "Ingresar" y la ayuda "Si olvidaste tu contraseña, pide al administrador que la restablezca.", y al final el pie "CarpetaDocente · 2026". No muestra logo ni escudo, ni enlaces a funciones que no existen. Desde US-003 el campo Usuario lleva debajo la pista de una línea "Ejemplo: jperez (inicial y apellido)", asociada al campo para el lector de pantalla.

#### Scenario: Contenido de la pantalla
- **WHEN** alguien sin sesión abre `/ingresar/`
- **THEN** ve el nombre de la I.E., el lugar, las tres dimensiones, el formulario con su ayuda y el pie, sin escudo, sin menú y sin un enlace para recuperar la contraseña

#### Scenario: Pista del campo Usuario
- **WHEN** alguien sin sesión abre `/ingresar/`
- **THEN** bajo el campo Usuario ve "Ejemplo: jperez (inicial y apellido)" en una línea, y el lector de pantalla la anuncia como descripción del campo, también cuando el campo muestra un error

#### Scenario: Mensaje de error sobre el formulario
- **WHEN** un ingreso es rechazado
- **THEN** el mensaje aparece sobre la tarjeta del formulario, con ícono, la primera línea destacada y la segunda en el color del texto, y lo anuncia el lector de pantalla
