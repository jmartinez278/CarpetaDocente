## MODIFIED Requirements

### Requirement: Diálogo accesible y sin desplazamiento horizontal
Cada vista de la lista, en el diálogo y como página completa, MUST pasar la revisión automática de accesibilidad (WCAG 2.1, A y AA) sin infracciones críticas ni graves en ambos temas, a 360 px y a 1280 px, y MUST NOT desplazarse en horizontal entre 320 px y 1280 px (RNF-005, RNF-008). La página completa va en el marco del rebrand, con «Estudiantes» en la barra y el ☰ y la cuenta cerrados durante la revisión. Los nombres largos bajan de línea sin "…". Cabecera y pie del diálogo quedan fijos y solo el cuerpo se desplaza.

#### Scenario: Revisión de cada vista
- **WHEN** se revisan la lista vacía, la lista, Pegar lista, Revisar lista, Agregar, Editar, Quitar, Vaciar y el bloqueo, en ambos temas y anchos
- **THEN** no hay infracciones críticas ni graves y el ancho del documento no supera el de la ventana

#### Scenario: Página completa en el marco del rebrand
- **WHEN** la docente abre la dirección de una vista de la lista
- **THEN** ve la barra con el ☰ y «Estudiantes», y debajo la vista con su título «Estudiantes de 2.º A» como encabezado principal, sin «Cerrar»

#### Scenario: Nombre largo a 320 px
- **WHEN** la lista tiene un estudiante de 120 caracteres en apellidos y en nombres y se ve a 320 px, también con el texto al 200 %
- **THEN** el nombre se lee completo en varias líneas, «Editar» sigue a la vista y la página no se desplaza en horizontal
