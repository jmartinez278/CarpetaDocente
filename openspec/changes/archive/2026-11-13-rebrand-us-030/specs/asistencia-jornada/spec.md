## MODIFIED Requirements

### Requirement: Avance de la jornada
La pantalla SHALL mostrar siempre cuántos estudiantes activos tienen estado y cuántos faltan: en PC «18/25 marcados» y «7 sin marcar»; en el celular, en el resumen fijo, «18/25 · 7 sin marcar». El lector de pantalla oye «18 de 25 marcados» y «7 sin marcar», sin leer la barra «/». Una jornada con estudiantes activos sin estado queda guardada como incompleta y se ve como tal (RN-012); completa o incompleta se calcula al consultarla.

#### Scenario: Caso de error
- **WHEN** la docente deja a 7 de 25 estudiantes sin estado
- **THEN** la jornada queda guardada como incompleta, la pantalla muestra «18/25 marcados» en PC y «18/25 · 7 sin marcar» en el celular, y el lector de pantalla oye «18 de 25 marcados» y «7 sin marcar»

### Requirement: Asistencia accesible y sin desplazamiento horizontal
La pantalla de asistencia, con el marco del rebrand y en todas sus vistas (lista a medio marcar, con fallo, con la barra de deshacer, completa, fin de semana y sin estudiantes), MUST pasar la revisión automática de accesibilidad (WCAG 2.1 A y AA) sin infracciones críticas ni graves, en ambos temas, a 360 y 1280 px, y no desplazarse en horizontal entre 320 y 1280 px. Los círculos miden 44 px.

#### Scenario: Revisión de cada vista
- **WHEN** se ejecuta la revisión automática sobre cada vista, con el marco del rebrand, en ambos temas y anchos
- **THEN** no hay infracciones críticas ni graves y el ancho del documento no supera el de la ventana
