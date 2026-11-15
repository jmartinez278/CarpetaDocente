# almacenamiento-archivos Specification

## Purpose
Define dónde y cómo se guardan los archivos de las sesiones de aprendizaje en cada entorno (Vercel, laptop y pruebas), con qué clave y qué pasa si el guardado falla a mitad (EN-03).

## Requirements

### Requirement: Archivos en R2 privado en la nube
En Vercel, los archivos de las sesiones SHALL guardarse en un bucket privado de Cloudflare R2, configurado con las variables `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_STORAGE_BUCKET_NAME` y `AWS_S3_ENDPOINT_URL`. El archivo pasa por el servidor; no hay enlace firmado de subida. Sin alguna de esas variables, la aplicación MUST NOT arrancar en Vercel.

#### Scenario: Vercel sin las variables de R2
- **WHEN** la aplicación arranca con `VERCEL=1` y sin `AWS_STORAGE_BUCKET_NAME`
- **THEN** Django se detiene con un error que nombra la variable que falta, sin mostrar valores

#### Scenario: Archivo no público
- **WHEN** alguien pide la URL pública del objeto de una sesión guardada en R2, sin firma
- **THEN** R2 no entrega el archivo

#### Scenario: Revisión de despliegue
- **WHEN** se ejecuta `manage.py check --deploy` con las variables de un despliegue de Vercel y claves de prueba de R2
- **THEN** el resultado no tiene errores ni advertencias

### Requirement: Laptop y pruebas sin R2
Fuera de Vercel y sin las variables de R2, los archivos SHALL guardarse en la carpeta `media/` de la raíz del repositorio, que git ignora; las pruebas automáticas los guardan en memoria y MUST NOT escribir en disco ni en R2.

#### Scenario: Laptop
- **WHEN** una docente envía una sesión en la laptop sin variables de R2
- **THEN** el archivo queda en `media/sesiones/` y `git status` no lo muestra

#### Scenario: Pruebas
- **WHEN** corre la suite de pruebas
- **THEN** ninguna prueba crea archivos en `media/` ni se conecta a R2

### Requirement: Clave del archivo
La clave de cada archivo SHALL ser `sesiones/<UUID de la sesión>-<token del intento>` más la extensión de su tipo (`.pdf` o `.docx`), única, sin el nombre original ni datos de la docente. Cada intento de envío tiene su propio token, así que dos intentos con el mismo UUID nunca comparten clave. El nombre original se guarda aparte, en la sesión.

#### Scenario: Clave de un PDF
- **WHEN** la docente envía «Leemos un cuento.pdf»
- **THEN** el archivo queda con la clave `sesiones/<UUID>-<token>.pdf` y la sesión guarda «Leemos un cuento.pdf» como nombre original

#### Scenario: Intento fallido y reintento con el mismo UUID
- **WHEN** un intento guarda su archivo y falla al confirmar, y el reintento con el mismo UUID confirma antes de que el primero borre
- **THEN** el primero borra solo su propio archivo y queda el del reintento, con su sesión

#### Scenario: Nombre original largo o con rutas
- **WHEN** el nombre original trae una ruta o pasa de 255 caracteres
- **THEN** se guarda solo el nombre del archivo, recortado a 255 caracteres conservando la extensión

### Requirement: Sin archivos huérfanos
Una sesión y su archivo SHALL guardarse juntos o no guardarse: si el archivo no se puede guardar, no queda la sesión ni su entrada de actividad; si la base falla después de guardar el archivo, el archivo se borra.

#### Scenario: Falla el almacenamiento
- **WHEN** el almacenamiento rechaza el archivo
- **THEN** no queda la sesión ni la entrada SESION_ENVIADA y la docente ve el error de conexión para reintentar

#### Scenario: Falla la base después del archivo
- **WHEN** la base falla al guardar la sesión después de guardar el archivo
- **THEN** el archivo ya no está en el almacenamiento y no queda la sesión

### Requirement: Subida dentro de los límites de Vercel
Un envío con un archivo de 4 MB SHALL caber en el límite de cuerpo de una función de Vercel (4,5 MB) y terminar dentro de su tiempo máximo con el perfil Slow 4G (RNF-002). Se mide en la vista previa antes de construir la pantalla.

#### Scenario: 4 MB con Slow 4G en la vista previa
- **WHEN** en la vista previa del PR se envía un PDF de 4 194 304 bytes con el perfil Slow 4G de Chrome DevTools
- **THEN** la sesión se guarda, el archivo llega a R2 y la función no corta por tiempo ni por tamaño
