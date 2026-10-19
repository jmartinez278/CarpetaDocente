# Spec Delta

## Purpose

Define las verificaciones automáticas que todo Pull Request hacia la rama principal debe pasar para poder fusionarse, de modo que los criterios 1, 2 y 5 de la DoD se comprueben sin revisiones manuales y sin claves reales.

## ADDED Requirements

### Requirement: Canal en cada Pull Request hacia la rama principal
Cada Pull Request dirigido a la rama principal SHALL ejecutar automáticamente las verificaciones de estilo, pruebas con cobertura, pruebas de punta a punta, análisis de seguridad y puerta de calidad, y mostrar el resultado de cada una en el propio Pull Request. Un nuevo commit en el Pull Request MUST volver a ejecutarlas.

#### Scenario: Pull Request abierto
- **WHEN** una integrante abre un Pull Request hacia la rama principal
- **THEN** el Pull Request muestra una verificación por cada herramienta (estilo, pruebas y cobertura, punta a punta, análisis de seguridad y puerta de calidad), cada una con su estado

#### Scenario: Nuevo commit en el Pull Request
- **WHEN** se agrega un commit a un Pull Request abierto hacia la rama principal
- **THEN** las verificaciones se ejecutan de nuevo sobre el último commit

### Requirement: Fusión solo con verificaciones en verde
La rama principal SHALL aceptar la fusión de un Pull Request solo cuando todas las verificaciones obligatorias del canal terminaron en verde.

#### Scenario: Pull Request que cumple
- **WHEN** un Pull Request tiene pruebas que pasan, cobertura de 80 % o más, sin alertas críticas ni altas y con la puerta de calidad superada
- **THEN** todas las verificaciones aparecen en verde y el Pull Request puede fusionarse tras la revisión

### Requirement: Análisis de la rama principal
Cada fusión en la rama principal SHALL ejecutar el canal sobre esa rama y actualizar su análisis en SonarQube Cloud, para que el código nuevo de cada Pull Request posterior se compare contra el estado vigente de la rama principal.

#### Scenario: Fusión en la rama principal
- **WHEN** se fusiona un Pull Request en la rama principal
- **THEN** el canal se ejecuta sobre la rama principal y SonarQube Cloud muestra el análisis actualizado de esa rama

### Requirement: Pruebas y cobertura mínima
El canal SHALL ejecutar todas las pruebas automatizadas que no son de punta a punta y medir la cobertura del código propio, sin contar migraciones ni pruebas. La verificación MUST fallar si alguna prueba falla o si la cobertura total es menor que 80 %.

#### Scenario: Prueba fallida
- **WHEN** un Pull Request contiene una prueba que falla
- **THEN** la verificación de pruebas aparece en rojo y GitHub impide fusionar el Pull Request

#### Scenario: Cobertura insuficiente
- **WHEN** un Pull Request deja la cobertura total por debajo de 80 %
- **THEN** la verificación de pruebas aparece en rojo, indica la cobertura obtenida y GitHub impide fusionar el Pull Request

#### Scenario: Mismo umbral en local
- **WHEN** una integrante ejecuta en su laptop las pruebas con medición de cobertura
- **THEN** el resultado falla con el mismo umbral de 80 % que el canal

### Requirement: Estilo y reglas de seguridad de Ruff
El canal SHALL revisar el código con Ruff en modo revisión y en modo verificación de formato, con las mismas reglas que el proyecto usa en local, incluidas las de seguridad. La verificación MUST fallar si Ruff reporta algún problema.

#### Scenario: Problema de estilo o de seguridad
- **WHEN** un Pull Request introduce código que Ruff reporta, sea de estilo, formato o seguridad
- **THEN** la verificación de estilo aparece en rojo, señala el archivo y la línea, y GitHub impide fusionar el Pull Request

### Requirement: Análisis de seguridad con CodeQL
Cada Pull Request hacia la rama principal SHALL analizarse con CodeQL. Una alerta de severidad de seguridad alta o crítica en el código del Pull Request MUST impedir la fusión.

#### Scenario: Consulta SQL armada con texto del usuario
- **WHEN** un Pull Request arma una consulta SQL concatenando texto escrito por el usuario
- **THEN** CodeQL registra una alerta de severidad alta o crítica en el Pull Request y GitHub impide fusionarlo

### Requirement: Puerta de calidad de SonarQube Cloud
Cada Pull Request hacia la rama principal SHALL analizarse en SonarQube Cloud con la cobertura medida por el canal. Si su código nuevo no supera la puerta de calidad, GitHub MUST impedir la fusión.

#### Scenario: Puerta de calidad no superada
- **WHEN** el código nuevo de un Pull Request tiene cobertura menor a 80 % o un problema crítico o alto
- **THEN** la puerta de calidad aparece como fallida en el Pull Request y GitHub impide fusionarlo

#### Scenario: Cobertura visible en SonarQube Cloud
- **WHEN** termina el análisis de un Pull Request
- **THEN** SonarQube Cloud muestra la cobertura del código nuevo, tomada del informe del canal, y no 0 % por falta del informe

### Requirement: Pruebas de punta a punta
El canal SHALL ejecutar las pruebas de punta a punta en un navegador real contra la aplicación levantada con sus estilos compilados. Si una de ellas falla, la verificación MUST fallar. Al menos una prueba de punta a punta MUST recorrer la página inicial.

#### Scenario: Página inicial en el navegador
- **WHEN** el canal abre la página inicial en el navegador
- **THEN** ve el nombre del sistema y las tres dimensiones en orden, la hoja de estilos carga sin error, y HTMX y Alpine.js están disponibles en la página

#### Scenario: Prueba de punta a punta fallida
- **WHEN** un Pull Request rompe el recorrido que verifica una prueba de punta a punta
- **THEN** la verificación de punta a punta aparece en rojo y GitHub impide fusionar el Pull Request

### Requirement: Pruebas de punta a punta separadas en local
Las pruebas de punta a punta SHALL estar marcadas aparte, de modo que la ejecución de pruebas por defecto en la laptop no las incluya ni exija un navegador instalado. Ejecutarlas MUST requerir pedirlas de forma explícita.

#### Scenario: Pruebas locales sin navegador
- **WHEN** una integrante sin navegadores de Playwright instalados ejecuta las pruebas con el comando por defecto
- **THEN** las pruebas de punta a punta no se ejecutan y el resto pasa

#### Scenario: Pruebas de punta a punta a pedido
- **WHEN** una integrante pide de forma explícita las pruebas de punta a punta, con el navegador instalado y los estilos compilados
- **THEN** se ejecutan contra la aplicación levantada en su laptop

### Requirement: Canal sin claves reales
El canal SHALL ejecutar las pruebas contra una base de datos PostgreSQL temporal, creada para cada ejecución, que solo contiene datos ficticios, y MUST NOT usar claves de producción ni de vistas previas. El único secreto que el canal puede usar es el token de SonarQube Cloud, guardado en los secretos de GitHub y nunca en el repositorio.

#### Scenario: Base de datos temporal y ficticia
- **WHEN** el canal ejecuta las pruebas
- **THEN** usa una base de datos PostgreSQL temporal con datos ficticios, que se descarta al terminar, y ninguna clave de producción

#### Scenario: Repositorio sin el token
- **WHEN** se revisan los archivos del repositorio
- **THEN** ninguno contiene el token de SonarQube Cloud ni otra clave; los workflows solo lo leen desde los secretos de GitHub
