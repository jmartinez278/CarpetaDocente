# Spec Delta

## MODIFIED Requirements

### Requirement: Pruebas de punta a punta
El canal SHALL ejecutar las pruebas de punta a punta en un navegador real contra la aplicación levantada con sus estilos compilados. Si una de ellas falla, la verificación MUST fallar. Al menos una prueba de punta a punta MUST recorrer el inicio de sesión hasta la pantalla del rol, y las pruebas de punta a punta MUST incluir la revisión automática de accesibilidad de las pantallas nuevas en ambos temas y la medición de la carga con Slow 4G.

#### Scenario: Página inicial en el navegador
- **WHEN** el canal abre la página inicial `/` en el navegador, con un docente ficticio creado por la prueba, y en `/ingresar/`, adonde lo lleva la redirección, ingresa su usuario y su contraseña
- **THEN** ve el nombre de la I.E. y las tres dimensiones en orden, la hoja de estilos carga sin error, el inicio de sesión no carga Alpine.js, el docente llega a `/docente/` y en la portada Alpine.js está disponible

#### Scenario: Accesibilidad y carga en el canal
- **WHEN** el canal ejecuta las pruebas de punta a punta
- **THEN** la revisión de accesibilidad recorre cada pantalla nueva en tema claro y en tema oscuro, y la medición con Slow 4G comprueba los umbrales de RNF-002; una infracción crítica o grave, o un umbral superado, deja la verificación en rojo

#### Scenario: Prueba de punta a punta fallida
- **WHEN** un Pull Request rompe el recorrido que verifica una prueba de punta a punta
- **THEN** la verificación de punta a punta aparece en rojo y GitHub impide fusionar el Pull Request
