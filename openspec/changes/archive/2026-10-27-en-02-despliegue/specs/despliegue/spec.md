# Spec Delta

## Purpose

Define cómo se publica el sistema en el plan A (Vercel Hobby y Neon): la configuración de producción leída del entorno, el build con sus migraciones, la vista previa de cada Pull Request con su propia base de datos de pruebas y la publicación de la rama principal, sin claves en el repositorio.

## ADDED Requirements

### Requirement: Configuración de producción solo en la nube
La configuración de producción (HTTPS obligatorio, cookies seguras, hosts de Vercel) SHALL activarse solo cuando la aplicación corre en Vercel, y MUST NOT cambiar cómo corren la laptop ni el canal de integración continua.

#### Scenario: Laptop y canal sin cambios
- **WHEN** la aplicación corre fuera de Vercel con la depuración apagada, como en el canal
- **THEN** una petición HTTP de prueba a la pantalla de ingreso responde sin redirigir a HTTPS, y las pruebas existentes pasan sin cambios

#### Scenario: Revisión de despliegue de Django sin advertencias
- **WHEN** se ejecuta `manage.py check --deploy` con la depuración apagada y las variables de un despliegue de Vercel, con claves de prueba
- **THEN** el resultado no tiene errores ni advertencias

### Requirement: Hosts y orígenes del despliegue
En Vercel, los hosts permitidos y los orígenes de confianza para CSRF SHALL incluir la URL del despliegue, la de su rama y la de producción que Vercel entrega en sus variables de sistema, más los hosts que se agreguen en la variable de hosts permitidos. Un host que no está en esa lista MUST recibir el rechazo de Django.

#### Scenario: Formulario en la URL de la vista previa
- **WHEN** una usuaria envía el formulario de ingreso desde la URL de una vista previa
- **THEN** la petición pasa la verificación CSRF y el host es aceptado

#### Scenario: Host ajeno
- **WHEN** llega una petición con un host que no es de ese despliegue ni está en la variable de hosts permitidos
- **THEN** Django responde 400

### Requirement: HTTPS y cookies seguras en la nube
En Vercel, la aplicación SHALL reconocer el HTTPS que termina en el proxy de Vercel, redirigir HTTP a HTTPS, enviar HSTS y marcar como seguras las cookies de sesión y de CSRF.

#### Scenario: Petición detrás del proxy
- **WHEN** llega una petición con la cabecera de protocolo del proxy en `https`
- **THEN** Django la trata como segura y no la redirige

#### Scenario: Cookies de sesión
- **WHEN** una usuaria inicia sesión en un despliegue de Vercel
- **THEN** las cookies de sesión y de CSRF llevan el atributo `Secure`

### Requirement: Conexión agrupada de la base de datos
En Vercel, la aplicación SHALL atender las peticiones por la conexión agrupada de Neon sin usar cursores del lado del servidor ni conexiones persistentes entre peticiones.

#### Scenario: Consulta grande por la conexión agrupada
- **WHEN** la aplicación recorre un conjunto de filas con `iterator()` en un despliegue de Vercel
- **THEN** la consulta no abre un cursor con nombre y la configuración no reutiliza la conexión entre peticiones

### Requirement: Logs a la salida estándar
En Vercel, los errores de la aplicación y los avisos de Django SHALL escribirse en la salida estándar, para que se lean en los logs del despliegue. Los logs MUST NOT incluir claves ni la cadena de conexión.

#### Scenario: Error del servidor
- **WHEN** una vista lanza una excepción en un despliegue de Vercel
- **THEN** la traza aparece en los logs de ejecución del despliegue y la usuaria recibe la página de error 500 sin detalles

### Requirement: Build con estilos y migraciones
Cada build en Vercel SHALL compilar los estilos y copiar HTMX y Alpine.js antes de reunir los archivos estáticos, y aplicar las migraciones pendientes en la base de datos de su ambiente por la conexión directa (sin agrupar). Si cualquiera de esos pasos falla, el build MUST fallar.

#### Scenario: Build completo
- **WHEN** Vercel construye un commit válido
- **THEN** el log muestra, en este orden, la compilación del CSS, las migraciones aplicadas y la reunión de estáticos, y las páginas cargan `app.css` con estilos

#### Scenario: Migración que falla
- **WHEN** una migración falla durante el build
- **THEN** el build termina en error y el despliegue no se publica

### Requirement: Paquete sin claves ni herramientas de desarrollo
El paquete desplegado SHALL usar Python 3.13 e incluir solo las dependencias de ejecución. MUST NOT incluir las dependencias de desarrollo, los archivos `.env` ni `.env.local`, ni la carpeta `insumos/`, tampoco cuando el despliegue se sube desde la laptop.

#### Scenario: Despliegue desde la laptop
- **WHEN** se ejecuta `vercel deploy` en una laptop que tiene `.env`, `.env.local` e `insumos/`
- **THEN** la lista de archivos subidos no incluye ninguno de ellos y el log del build no instala pytest, Playwright ni Ruff

### Requirement: Vista previa por Pull Request
Cada Pull Request SHALL generar una vista previa en Vercel conectada a su propia rama de base de datos de Neon, distinta de la de producción, y con acceso solo para el equipo o con un enlace compartible.

#### Scenario: Vista previa por Pull Request
- **WHEN** Vercel termina el despliegue de un Pull Request abierto en GitHub
- **THEN** el Pull Request muestra un enlace a una vista previa conectada a una base de datos de pruebas

#### Scenario: Acceso de una revisora
- **WHEN** una revisora abre la vista previa con el enlace compartible
- **THEN** ve la pantalla de ingreso; sin el enlace ni sesión del equipo en Vercel, la vista previa pide autenticarse

### Requirement: Publicación de la rama principal
Cada fusión en la rama principal SHALL publicarse sola en producción, conectada a la rama de producción de Neon y servida por HTTPS.

#### Scenario: Publicación de la rama principal
- **WHEN** termina el despliegue de un Pull Request aprobado y fusionado en la rama principal
- **THEN** la versión publicada responde por HTTPS con los cambios del Pull Request

### Requirement: Despliegue fallido
Un build fallido MUST NOT reemplazar la versión publicada, y su error SHALL verse en el Pull Request.

#### Scenario: Despliegue fallido
- **WHEN** Vercel intenta desplegar un cambio que rompe la construcción
- **THEN** la versión publicada anterior sigue en línea y el Pull Request muestra el error
