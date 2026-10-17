# entorno-desarrollo Specification

## Purpose

Define cómo cualquier integrante levanta, configura y verifica el sistema en su laptop, con el mismo motor de base de datos que producción y sin claves en el repositorio público.

## Requirements

### Requirement: Entorno local con un solo comando
El sistema SHALL levantarse en local con Docker Compose, con un servicio de PostgreSQL, uno de la aplicación web y uno que compila los estilos, de modo que tras clonar el repositorio y crear `.env` desde `.env.example` baste un comando para tener la aplicación respondiendo con estilos y conectada a PostgreSQL, sin instalar Node en la laptop.

#### Scenario: Entorno levantado
- **WHEN** un integrante clona el repositorio, crea `.env` a partir de `.env.example` y ejecuta `docker compose up`
- **THEN** PostgreSQL queda disponible y la aplicación responde en el navegador conectada a esa base de datos

#### Scenario: Estilos sin Node en la laptop
- **WHEN** un integrante sin Node instalado ejecuta `docker compose up` en un clon sin los estilos compilados
- **THEN** el servicio de compilación genera la hoja de estilos y la página inicial se ve con estilos

#### Scenario: Solo la base de datos en Docker
- **WHEN** un integrante levanta únicamente el servicio de PostgreSQL y ejecuta el servidor de desarrollo de Django en su laptop
- **THEN** la aplicación responde en el navegador y usa la misma base de datos

### Requirement: Migraciones aplicables
Las migraciones del proyecto SHALL aplicarse sin errores sobre una base de datos PostgreSQL vacía.

#### Scenario: Migraciones aplicadas
- **WHEN** con el entorno levantado se ejecutan las migraciones
- **THEN** terminan sin errores y la base de datos tiene las tablas de usuario e institución con sus restricciones

### Requirement: Configuración solo desde el entorno
Toda la configuración sensible o dependiente del entorno (clave secreta, modo depuración, hosts permitidos y conexión a la base de datos en formato `DATABASE_URL`) SHALL leerse de variables de entorno o del archivo `.env`; el repositorio MUST NOT contener valores de claves.

#### Scenario: Falta la clave secreta
- **WHEN** se inicia la aplicación sin la variable de la clave secreta definida
- **THEN** la aplicación no arranca e indica qué variable falta

#### Scenario: Depuración desactivada por defecto
- **WHEN** la variable de modo depuración no está definida
- **THEN** la aplicación arranca con la depuración desactivada

#### Scenario: Plantilla de variables sin valores
- **WHEN** se revisa `.env.example` en el repositorio
- **THEN** contiene los nombres de todas las variables que la aplicación lee y ninguna tiene valor de clave

### Requirement: Página inicial
El sistema SHALL mostrar en la ruta raíz una página inicial en español que identifica el sistema y sus tres dimensiones, construida sobre la plantilla base que carga los estilos de Tailwind CSS, HTMX y Alpine.js.

#### Scenario: Visita a la página inicial
- **WHEN** un visitante abre la ruta raíz `/`
- **THEN** recibe una respuesta exitosa con el nombre del sistema y las tres dimensiones en este orden: planificación de sesiones de aprendizaje, registro y control de notas, control de asistencia

#### Scenario: Recursos de interfaz cargados
- **WHEN** se carga la página inicial
- **THEN** el HTML enlaza la hoja de estilos compilada de Tailwind CSS y los scripts de HTMX y Alpine.js servidos como archivos estáticos propios

### Requirement: Verificación de calidad local
El proyecto SHALL incluir una suite de pruebas ejecutable con pytest contra PostgreSQL y una configuración de Ruff que incluya las reglas de seguridad; ambas MUST pasar limpias en la rama.

#### Scenario: Pruebas en verde
- **WHEN** con PostgreSQL levantado se ejecuta pytest
- **THEN** todas las pruebas pasan y al menos una confirma que la conexión es a PostgreSQL

#### Scenario: Ruff limpio
- **WHEN** se ejecuta Ruff en modo revisión y en modo formato de verificación
- **THEN** no reporta problemas
