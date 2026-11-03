# Design: US-010, US-014 y EN-03 – Enviar una sesión a la dirección

## Context

- Decisiones cerradas en `insumos/US-010/decisiones.md` (1 a 14). Interfaz: boceto `C:\Proyectos\prototipos-cd\US-010\` (`index.html`, `sesiones.js`, `sesiones.css`, `notas.md`, capturas de los estados 1 a 10, variante **4a**); su envío simulado y sus parámetros `?estado=` no se copian. Lo nuevo de este propose está en `proposal.md`.
- La app `repositorio` existe vacía (doc 12). `settings.py` no define `STORAGES`; `.env.example` ya trae `AWS_*` «para EN-03» y `.gitignore` ya ignora `media/`. No hay ninguna dependencia de almacenamiento.
- Acceso: `RolRequeridoMixin` (`cuentas/acceso.py`) reserva una vista a un rol y resuelve la sesión vencida con `HX-Redirect` si la petición trae `HX-Request`. Sesiones no es una ruta de sección: no usa `SeccionDocenteMixin` ni entra a la matriz de `acceso-secciones`.
- Datos para el formulario: `institucion.servicios.secciones_docente` (año ABIERTO) y `texto_seccion_corto` («2.º A»); áreas con `InstitucionArea(se_trabaja=True)` por `area__orden`, como `notas.servicios.areas_de_la_seccion` pero por institución.
- `actividad.registrar` exige transacción abierta y valida el detalle contra `DETALLE_PERMITIDO`; agregar una operación obliga a migrar `ck_actividad_operacion` (`actividad/0005`). `indicadores_por_semana` deja `sesiones` en `None`.
- Patrón de popup: `static/js/estudiantes.js` (`showModal`, una entrada de historial al abrir, `popstate` cierra, cerrar consume la entrada con `history.back()`); `comp-dialogo` de Notas para el popup chico. Guardados con `fetch`, `X-CSRFToken` y `HX-Request`.
- Vercel: cuerpo de la petición de una función hasta 4,5 MB; por eso el tope es 4 MB (decisión 6) y el archivo puede pasar por el servidor (decisión 7).

## Riesgos y zonas delicadas (primero)

- **[Subida lenta en Vercel]** (zona de cuidado) → D3: 4 MB con Slow 4G puede pasar de 40 s. Se mide en la vista previa con la ruta ya hecha y **antes** de la pantalla; si la función corta, el apply se detiene y decide el equipo (volver al enlace firmado de subida del EN-03 original, o bajar el tope).
- **[Botón «atrás» en Android]** (zona de cuidado, decisión 4) → D8: una entrada de historial por popup abierto; en Chrome de Android «atrás» con un `<dialog>` modal dispara primero su `cancel` (close watcher), no `popstate`; los dos caminos terminan en el mismo cierre. Prueba e2e de los dos.
- **[Envío duplicado]** → D5: UUID de la sesión generado en el navegador; un reintento devuelve el mismo éxito. Dos envíos simultáneos con el mismo UUID: el segundo espera la fila del primero y responde su éxito, sin escribir el archivo.
- **[Archivo huérfano o sesión sin archivo]** → D4: fila, actividad y archivo en una transacción, y el archivo se borra si la confirmación falla.
- **[Archivo disfrazado]** → D6: el tipo sale del contenido y debe coincidir con la extensión; un .docm renombrado o un ejecutable llamado `.pdf` se rechazan. No se abre ni se procesa el documento más allá de su cabecera y su índice.
- **[Claves de R2]** → D2: solo por variables de entorno, nunca en el repo ni en los logs; bucket privado. Lo configura el equipo en Vercel (Preview y Production).
- **[Privacidad]** (RN-015, zona de cuidado) → el término 3 es una declaración; el sistema no lee el documento. El registro solo guarda el UUID y `compartida` (D10).
- **[Tamaño del paquete de Vercel]** → `boto3`/`botocore` suman decenas de MB al paquete; se comprueba en el build de la vista previa (D3).
- **[Cambio de requisito y de modelo]** (decisión 1, zonas de cuidado) → solo se mencionan; van a la deuda (proposal).

## Goals / Non-Goals

**Goals:**
- Toda regla y toda escritura en `repositorio/servicios.py`; las vistas leen la petición, llaman al servicio y responden.
- Un envío es todo o nada e idempotente, y lo escrito sobrevive a un corte de red.
- La laptop y el canal de integración no necesitan R2.

**Non-Goals:**
- Descargar, ver o listar sesiones; enlaces firmados (US-011, US-012).
- Panel de administración para sesiones (bloque 2).
- Funcionar sin JavaScript: el popup lo necesita; sin él, la pantalla muestra un `<noscript>` («Para subir una sesión necesitas activar JavaScript.»).

## Decisions

### D1. Modelo `Sesion` (`repositorio/models.py`, migración `0001`)

- `db_table="sesion"`, campos del doc 11 que usa este bloque: `id` UUID (PK, sin `default`: lo trae el envío, D5), `institucion` FK PROTECT, `autor` y `subido_por` FK usuario PROTECT, `grado` (1 a 6), `area` FK `catalogo.Area` PROTECT, `titulo` `CharField(200)`, `proposito` `TextField(default="")` (cadena vacía en vez de NULL, como en US-030), `origen` (`PROPIA`; cada historia agrega el suyo), y los nuevos `estado` (`ENVIADA`; el bloque 2 agrega los suyos) y `compartida` (bool). Del archivo: `archivo_clave` `CharField(300)` UQ, `archivo_nombre` (255), `tipo_mime` (100), `tamano_bytes`. `terminos_aceptados_en` nulo. `creado_en`, `actualizado_en`.
- Restricciones: `ck_sesion_grado`, `ck_sesion_origen`, `ck_sesion_estado`, `ck_sesion_tipo_mime` (PDF y DOCX), `ck_sesion_tamano` (1 a 4 194 304), `ck_sesion_titulo` (no vacío), `ck_sesion_terminos` (`compartida` ⇔ `terminos_aceptados_en IS NOT NULL`). Índices `idx_sesion_busqueda` (institucion, grado, area) y `idx_sesion_autor` del doc 11; sin `pg_trgm` (US-011).
- PROTECT y no RESTRICT/CASCADE: las cuentas se desactivan, no se borran; una sesión no desaparece porque se borre su autora. Sin `sesion_origen_id`, `fuente`, `permiso_uso` ni `sesion_competencia` (otras historias).
- **Alternativa descartada:** `terminos_aceptados_en` obligatorio como el DDL del doc 11: contradice la decisión 1.

### D2. Almacenamiento por entorno (`settings.py`, EN-03)

- Alias propio `STORAGES["sesiones"]`, sin tocar `default` ni `staticfiles`:
  - Con `AWS_STORAGE_BUCKET_NAME`: `storages.backends.s3.S3Storage` con el endpoint de R2, `region_name="auto"`, `default_acl=None`, `querystring_auth=True`, `file_overwrite=True` (la clave es única por UUID; evita una consulta previa al bucket) y sin `custom_domain`. La configuración exacta de R2 se consulta en Context7 (django-storages) en el apply.
  - En Vercel sin las cuatro variables: `ImproperlyConfigured` que nombra la que falta.
  - **Ajuste del apply:** fuera de Vercel, R2 a medias (alguna de las cuatro variables y no todas) también da `ImproperlyConfigured`; si no, boto3 tomaría las credenciales que falten de `~/.aws` sin avisar. Van las cuatro o ninguna.
  - Fuera de Vercel sin variables: `FileSystemStorage(location=ROOT_DIR / "media")`.
  - Pruebas: un fixture `autouse` en `src/backend/conftest.py` cambia el alias a `InMemoryStorage`; pytest-django lo aplica también al `live_server` de las e2e.
- `FILE_UPLOAD_MAX_MEMORY_SIZE = 4,5 MB`: el archivo queda en memoria y no en `/tmp`.
- Dependencia: `django-storages[s3]` en las de ejecución (`uv add`).
- **Alternativa descartada:** `default` apuntando a R2: cualquier `FileField` futuro iría a R2 sin decidirlo.

### D3. Medición en la vista previa antes de la pantalla

- Con el modelo, el servicio y la ruta POST listos (partes A a C), el equipo define las variables de R2 en Vercel (Preview), se publica la rama y se envía un PDF de 4 194 304 bytes a `/docente/sesiones/enviar/` con la velocidad de subida limitada a la de Slow 4G (`curl --limit-rate`, o la página de la parte D más tarde). Se anotan en `verificacion.md` el tiempo, el tamaño del paquete del build y el objeto en R2.
- Si falla por tiempo o por tamaño, se detiene el apply y el equipo decide; no se sigue con la parte D.

### D4. Envío todo o nada: `enviar_sesion(usuario, datos, archivo)`

1. Valida todo (D6, campos, términos) antes de escribir; devuelve errores por campo.
2. `transaction.atomic()`: crea la fila con la clave `sesiones/<uuid>.<ext>`, `registrar(SESION_ENVIADA)`, y al final `storage.save(clave, archivo)`; si el nombre devuelto no es la clave, falla. Si el almacenamiento falla, la excepción deshace la fila y la entrada.
3. Si la confirmación falla después de guardar el archivo, `storage.delete(clave)` en el `except` y se vuelve a lanzar.
- La fila va antes del archivo para que un segundo envío con el mismo UUID quede esperando en la PK (D5) y nunca escriba.
- El nombre original: `Path(nombre).name` (sin rutas), recortado a 255 conservando la extensión.

### D5. Envío idempotente con el UUID del navegador

- Al abrir el formulario, `crypto.randomUUID()` va en un campo oculto `id`; «Reintentar envío» manda el mismo; «Subir otra» y cada apertura generan otro.
- El servicio: si ya existe una sesión con ese `id` y la misma autora, responde su éxito sin escribir nada. Si la inserción choca con la PK (envío simultáneo), deshace, relee y responde igual. Si es de otra autora o el `id` no es un UUID, error general «No se pudo enviar. Recarga la página e intenta de nuevo.» sin escribir.
- **Alternativa descartada:** UUID en el servidor: un reintento tras perder la respuesta duplicaría la sesión.

### D6. Validación del archivo (`repositorio/servicios.py`)

- Extensión `.pdf` o `.docx` (sin distinguir mayúsculas) y contenido que coincide:
  - PDF: empieza con `%PDF-`.
  - DOCX: ZIP válido (`zipfile`, solo el índice) con `[Content_Types].xml` que declara `wordprocessingml.document.main+xml` y la parte `word/document.xml`. Se lee como máximo 64 KB de `[Content_Types].xml`. Un .docm (`macroEnabled`) no pasa.
- Tamaño de 1 a 4 194 304 bytes. `tipo_mime` sale del tipo reconocido, nunca del navegador.
- Mensajes del boceto: «Elige un archivo PDF o Word (.docx).», «Este archivo no es PDF ni Word (.docx). Elige otro archivo.», «El archivo supera los 4 MB. Elige uno más pequeño.». Campos: «Falta indicar el grado.», «Falta indicar el área.», «Falta indicar el título.», «El título puede tener hasta 200 caracteres.», «El propósito puede tener hasta 1000 caracteres.», «Elige un área de la lista.» (área que la institución no trabaja), y el de términos de la spec.
- En el navegador, `sesiones.js` repite tipo y tamaño al elegir el archivo (firma `%PDF-` o ZIP con `word/document.xml`, como el boceto), solo como ayuda.

### D7. Rutas, vistas y respuestas (`repositorio/views.py`, `repositorio/urls.py`)

- `config/urls.py`: `path("docente/sesiones/", include("repositorio.urls"))`, `app_name="sesiones"`.
- `SesionesView` (GET `sesiones:inicio`): cabecera, estado vacío y el popup en la página (no se carga por HTMX), con las áreas, el grado por defecto y su ayuda.
- `EnviarSesionView` (POST `sesiones:enviar`), con `RolRequeridoMixin` (Docente): lee `request.POST` y `request.FILES`, llama a `enviar_sesion` y responde:
  - 201 con el fragmento `repositorio/_enviada.html` (Mensaje de éxito, resumen con `filesizeformat` y «Subir otra»);
  - 400 con JSON `{"errores": {"campo": "mensaje"}}`;
  - la sesión vencida o el otro rol, con `HX-Redirect` (ya lo hace `RolRequeridoMixin` con `HX-Request`).
- Cliente: `XMLHttpRequest` con `upload.onprogress` (`fetch` no informa el avance de la subida), `FormData` del formulario, `X-CSRFToken` y `HX-Request: true`. Un 2xx pinta el fragmento; un 400 pinta los errores; `HX-Redirect` navega; cualquier otra cosa (red, 413, 5xx) es «Se cortó la conexión».
- **Alternativa descartada:** HTMX con `hx-encoding`: la confirmación de términos entre el clic y el envío y el reintento con el mismo archivo quedan más simples en JS propio, como Notas y Asistencia.

### D8. Popups y botón «atrás» (`static/js/sesiones.js`)

- Dos `<dialog>` en la página: `#subir` (formulario) y `#terminos` (4a, encima). Cada `showModal()` agrega una entrada de historial; `popstate` cierra el de arriba; cerrar con un botón o Esc consume la entrada con `history.back()` y una marca para ignorar su `popstate`.
- En Chrome de Android «atrás» dispara `cancel` del diálogo de arriba: se trata igual que Esc.
- Mientras sube: `cancel` hace `preventDefault()`; si el navegador cierra el diálogo igual (close watcher sin activación) o llega un `popstate`, se vuelve a abrir y se repone la entrada; `beforeunload` pide confirmar. La subida no depende del diálogo.
- Al éxito: se cierra `#subir`, se consume su entrada, se pinta el fragmento en la región `role="status"` y el foco va a su título.
- Foco: al abrir, el título del popup (`tabindex="-1"`); al cerrar, el botón que lo abrió; al abrir los términos, su título; con errores, el primer campo con error. El cuerpo desplazable es enfocable (`tabindex="0"`, `role="region"`) para el teclado durante la subida (crítica del boceto).
- Avance: `<progress>` con `aria-label`, y el texto «Subiendo… N %» en una región `aria-live="polite"` que se anuncia al empezar y cada 25 %.

### D9. Pantalla y estilos

- Plantillas en `templates/repositorio/`: `sesiones.html` (extiende `marco.html`), `_formulario.html`, `_terminos.html`, `_enviada.html`. Los cuatro puntos de los términos, literales del doc 09 §4, en la plantilla.
- Clases en `src/frontend/css/app.css` con los tokens de `DESIGN.md` y las medidas del boceto (`sesiones.css`): hoja a 16 px del borde superior en el celular, ventana de unos 480 px en la PC, popup de términos ajustado al contenido con altura máxima y cuerpo desplazable. Ícono de subir de Lucide si hace falta (`upload.svg`, con la licencia que ya está).
- Grado por defecto y su ayuda: `repositorio.servicios.datos_del_formulario(usuario)` con `secciones_docente`.

### D10. Actividad e indicadores (`actividad/`)

- `Operacion.SESION_ENVIADA` («Sesión enviada»), en `CUENTAN_KPI_01`; `DETALLE_PERMITIDO[SESION_ENVIADA] = {"compartida"}`; entidad `sesion`, `entidad_id` el UUID. Migración `actividad/0005` del `CHECK`.
- `indicadores_por_semana`: `sesiones` cuenta las SESION_ENVIADA de cuentas reales (`usuario__es_demo=False`), con `_por_semana`.
- **Dato de la tesis:** «sesiones cargadas» y KPI-01 salen de `registro_actividad.operacion = SESION_ENVIADA`; la sesión misma queda en `sesion` (`creado_en`, `compartida`, `terminos_aceptados_en`).

## Risks / Trade-offs

- [El archivo pasa por la función de Vercel] → tope de 4 MB y medición D3; si no alcanza, se vuelve al enlace firmado de subida (el equipo decide).
- [Transacción abierta mientras se escribe en R2] → unos segundos por envío, con pocas docentes; Neon en modo transacción lo admite. Aceptado.
- [El navegador pierde el archivo tras un corte] → el campo lo pide de nuevo (decisión 9).
- [Sesiones de cuentas demo quedan al quitar la demostración] → a la deuda (proposal).
- [Validación por cabecera, no del documento entero] → un PDF dañado con cabecera válida pasa; la dirección lo verá al abrirlo (bloque 2). Aceptado.

## Migration Plan

- `repositorio/0001` crea `sesion`; `actividad/0005` amplía el `CHECK` de operaciones. Las dos se aplican en el build de Vercel (spec `despliegue`).
- Antes de publicar la rama, el equipo crea el bucket privado de R2 (uno para Preview y otro para Production, o prefijos distintos) y define las cuatro variables en Vercel; sin ellas el despliegue no arranca (D2).
- Vuelta atrás: revertir el commit y la migración `repositorio/0001` (tabla nueva, sin datos previos); los objetos de R2 se borran a mano.
