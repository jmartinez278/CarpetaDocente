# Propuesta: US-010, US-014 y EN-03 – Enviar una sesión a la dirección

## Why

Hoy la docente lleva su sesión impresa a la dirección para que la firmen. US-010 (RF-010), US-014 (RF-014) y EN-03 (RNF-004), las tres de prioridad Alta, le permiten enviarla desde el celular en un solo paso y decidir ahí si además la comparte con sus colegas, con consentimiento explícito. Es la **dimensión 1 (planificación de sesiones de aprendizaje)** y llena por primera vez un dato que mide la tesis: las «sesiones cargadas» de Indicadores, y suma a los docentes activos (KPI-01).

## What Changes

Se aplican tal cual `insumos/US-010/decisiones.md` (decisiones 1 a 14) y el boceto `C:\Proyectos\prototipos-cd\US-010\`, variante **4a**. Lo nuevo de este propose:

- **Un envío repetido no duplica la sesión**: el navegador genera el UUID de la sesión al abrir el formulario y lo manda con el envío; si la red se corta después de guardar y la docente reintenta, el servidor responde el mismo éxito sin otra sesión, otro archivo ni otra entrada de actividad (design D5).
- **La subida usa `XMLHttpRequest`**, la única API del navegador que informa el avance de la subida («Subiendo… 45 %»); los errores vuelven como JSON por campo y el éxito como un fragmento HTML con el resumen (design D7).
- **El archivo no queda huérfano**: la fila y el archivo se guardan en una transacción; si falla la base, se borra el archivo (design D4).
- **Antes de construir la pantalla se mide la vista previa**: un archivo de 4 MB con Slow 4G contra la función de Vercel. Si la función corta por tiempo o por tamaño, se detiene el apply y el equipo decide (design D3, zona de cuidado de decisiones.md).
- **Sin almacenamiento en la nube fuera de Vercel**: en la laptop los archivos van a `media/` (ya ignorada) y en las pruebas a memoria; en Vercel, sin las variables de R2, Django no arranca (design D2).
- **«Sesiones cargadas»** de Indicadores cuenta las entradas SESION_ENVIADA de cuentas reales.
- **Textos**: los del boceto (`sesiones.js`, `index.html`), en tuteo; los que faltan siguen su forma («Falta indicar el grado.»).

**Fuera de alcance (deuda para la descripción del PR):**
- Bandeja de la dirección, visto bueno, observaciones, estado que ve la docente y la lista de Sesiones → bloque 2. La tarjeta Sesiones de la portada sigue en «Próximamente» hasta entonces.
- Unidad de aprendizaje → bloque 2. Compartir después una sesión ya enviada → bloque 2 o 3.
- Buscar, descargar, vista previa y eliminar → US-011, US-012, US-016. Enlaces firmados de descarga (la otra mitad de EN-03) → US-012.
- Competencias de la sesión (`sesion_competencia`) → después del Sprint 3. Sesión adaptada → US-013; entregada por la dirección → US-017; material de referencia → US-018.
- Sesiones de cuentas demo: quitar la demostración no las borra ni borra sus archivos → bloque 3, con eliminar.

**Contradicciones que solo se mencionan (documentos congelados, van a la deuda):**
- Decisión 1 (toda sesión va a la dirección; compartir es opcional): doc 06 §1 y RF-010, RF-014, RF-015 (retirado) y RF-017, doc 08 §3.1, RN-019 y los criterios de US-010 y US-014 («Sesión publicada», «debe aceptar»).
- Doc 11, tabla `sesion`: suma `estado` y `compartida`; `terminos_aceptados_en` solo si se comparte; `tipo_mime` sin `application/msword`; tope de 4 MB (no 10 MB); sin `sesion_origen_id`, `fuente` ni `permiso_uso` todavía.
- 4 MB frente a 10 MB en RN-021, RNF-004, docs 10, 11 y 12 y en los escenarios de EN-03 (9 MB, 12 MB); EN-03 pedía subida directa con enlace firmado y aquí el archivo pasa por el servidor (decisión 7).

## Capabilities

### New Capabilities

- `envio-sesiones`: la pantalla Sesiones de la docente (cabecera, estado vacío y resumen del último envío) y el popup «Subir una sesión»: campos, valores por defecto, validación en el navegador y en el servidor, compartir con los términos (US-014), subida con avance, corte de red, envío repetido, botón «atrás» y acceso solo del rol Docente.
- `almacenamiento-archivos`: dónde y cómo se guardan los archivos de las sesiones (R2 privado en Vercel, `media/` en la laptop, memoria en las pruebas), su clave, su contenido validado y su borrado si falla la base (EN-03).

### Modified Capabilities

- `registro-actividad`: «Catálogo cerrado de operaciones» suma SESION_ENVIADA, que cuenta para KPI-01; nuevo requisito «Envío de sesiones».
- `indicadores-adopcion`: «Jornadas registradas» deja de mostrar «—» en «sesiones cargadas».

## Impact

- **Código:**
  - `src/backend/repositorio/`: modelo `Sesion` y su migración `0001`, `servicios.py` (validación del archivo, envío, resumen), vistas, rutas, pruebas.
  - `src/backend/actividad/`: SESION_ENVIADA, su detalle, `CUENTAN_KPI_01`, «sesiones cargadas» y la migración `0005`.
  - `src/backend/config/settings.py` (`STORAGES`, límites de subida), `config/urls.py`, `templates/repositorio/`, `static/js/sesiones.js`, `src/frontend/` (CSS), ícono nuevo si hace falta (`upload`).
- **Rutas:** `/docente/sesiones/` (GET) y `/docente/sesiones/enviar/` (POST). Se actualiza el Catálogo de rutas de `docs/03`.
- **Dependencias:** `django-storages[s3]` (con `boto3`).
- **Variables de entorno:** `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_STORAGE_BUCKET_NAME` y `AWS_S3_ENDPOINT_URL`, ya en `.env.example`; el equipo crea el bucket privado y las define en Vercel (Preview y Production). El README no cambia: la laptop y las pruebas no necesitan R2.
- **Requisitos:** US-010, US-014, EN-03, RF-010, RF-014, RN-015, RN-019, RN-021, RNF-002, RNF-004, RNF-005, doc 09 §4, doc 11 (3.4). DoD 1 a 9.
- **Rama:** `feature/us-010-014-en-03-enviar-sesion`, desde `main`; su primer commit (archivo de US-004) ya está.
