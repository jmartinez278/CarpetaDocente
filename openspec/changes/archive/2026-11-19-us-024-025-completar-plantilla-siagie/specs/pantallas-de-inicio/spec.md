# Spec Delta

## MODIFIED Requirements

### Requirement: Inicio de la dirección
El inicio de la dirección SHALL saludar al usuario por su nombre y mostrar, en este orden, el bloque «Plantilla de notas del SIAGIE», con la ayuda «Completa la plantilla de una sección con las notas de CarpetaDocente.» y el botón «Subir plantilla» (spec `plantilla-notas-siagie`), y, mientras no exista el panel de consolidados (US-040), el título «Consolidados» con el estado vacío "Los consolidados de notas y asistencia estarán aquí en una próxima versión."

#### Scenario: Inicio de la dirección en el Sprint 1
- **WHEN** un usuario de la dirección entra al sistema
- **THEN** ve su saludo, el título "Consolidados" y el estado vacío con su ícono, sin tablas ni datos

#### Scenario: Acceso a la plantilla del SIAGIE
- **WHEN** un usuario de la dirección entra al sistema
- **THEN** ve, entre el saludo y los consolidados, «Plantilla de notas del SIAGIE» con su ayuda y «Subir plantilla», que abre el diálogo de subida
