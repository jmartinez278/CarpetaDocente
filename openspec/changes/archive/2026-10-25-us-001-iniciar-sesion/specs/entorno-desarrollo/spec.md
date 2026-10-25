# Spec Delta

## MODIFIED Requirements

### Requirement: Página inicial
El sistema SHALL responder en la ruta raíz con una redirección según la sesión: a la pantalla de inicio de sesión si no hay sesión y a la pantalla de inicio del rol si la hay (US-001). Todas las pantallas se construyen sobre la plantilla base en español, que carga la hoja de estilos compilada de Tailwind CSS. HTMX y Alpine.js se sirven como archivos estáticos propios y cada pantalla carga solo los scripts que usa.

#### Scenario: Visita a la página inicial
- **WHEN** un visitante sin sesión abre la ruta raíz `/`
- **THEN** recibe una redirección a `/ingresar/`, que responde con éxito en español, adaptada al celular, con el nombre de la I.E. y las tres dimensiones en este orden: sesiones, notas, asistencia

#### Scenario: Recursos de interfaz cargados
- **WHEN** se carga la pantalla de inicio de sesión o la portada del docente
- **THEN** el HTML enlaza la hoja de estilos compilada de Tailwind CSS servida como archivo estático propio. La portada carga además Alpine.js; el inicio de sesión no lo carga
