# Spec Delta

## MODIFIED Requirements

### Requirement: Marco común
Las pantallas de inicio de los roles SHALL compartir una barra superior fija con el nombre "I.E. Virgen del Carmen" y el pie "CarpetaDocente · 2026". Desde US-002 la barra lleva a la derecha el menú de la cuenta (spec `cierre-sesion`).

#### Scenario: Barra y pie
- **WHEN** un docente o la dirección abre su pantalla de inicio
- **THEN** ve la barra con el nombre de la I.E. y el menú de la cuenta a la derecha, y el pie al final

### Requirement: Accesibilidad en ambos temas
Cada pantalla nueva MUST pasar la revisión automática de accesibilidad (WCAG 2.1, niveles A y AA) sin infracciones críticas ni graves, en tema claro y en tema oscuro, a 360 px y a 1280 px (RNF-008, DoD 7). El contraste de texto queda incluido en la revisión.

#### Scenario: Revisión de cada pantalla
- **WHEN** se ejecuta la revisión automática sobre el inicio de sesión (normal, con error, con campos vacíos y con el aviso de inactividad), la portada del docente y el inicio de la dirección (cada una con el menú cerrado y abierto), en ambos temas y en ambos anchos
- **THEN** no hay infracciones críticas ni graves
