# Design: US-011, US-012 y US-016 – Mis sesiones y repositorio

## Context

- Decisiones cerradas en `insumos/US-011/decisiones.md` (1 a 18). Interfaz: `insumos/rebrand/repositorio.html` y `sesion.html` con DESIGN.md; su JS simulado (`pagina-repositorio.js`, datos en el navegador, «Deshacer» del toast) no se copia. Lo nuevo de este propose está en `proposal.md`.
- `repositorio` ya tiene `Sesion` (`0001`), `enviar_sesion` (todo o nada, idempotente por UUID), `SesionesView` y `EnviarSesionView` bajo `/docente/sesiones/` con `DocenteMixin`, y `sesiones.js` para el popup. La pantalla hoy no lista nada.
- `STORAGES["sesiones"]`: `S3Storage` con `querystring_auth=True` en Vercel, `FileSystemStorage` en la laptop e `InMemoryStorage` en las pruebas. Nadie llama todavía a `.url()`.
- `actividad.registrar` exige transacción y valida el detalle contra `DETALLE_PERMITIDO`; una operación nueva obliga a migrar su `CHECK`. `entidad_id` es texto: la entrada sobrevive al borrado de la sesión.
- `cuentas/dimensiones.py`: Sesiones sin `url_name` ni `disponible`; `POR_SECCION` no la incluye, así que al encenderla enlaza también sin sección.
- `institucion/demo.py`: `quitar_demo` borra por sección y desactiva las cuentas demo; hoy no toca sesiones (deuda de US-010).
- No hay dependencia para leer PDF. El .docx ya se abre con `zipfile` y `ElementTree` sin DOCTYPE en `validar_archivo`.

## Riesgos y zonas delicadas (primero)

- **[Fuga entre docentes o instituciones]** (decisión 11) → D5: una sola función decide si una sesión es visible y la usan la página, la descarga, la vista y las tres escrituras. Lo no visible responde igual que lo inexistente (404, mismo cuerpo). Las listas filtran siempre por `institucion_id` del usuario, nunca por un parámetro.
- **[Enlace firmado]** (decisión 10) → D7: 60 s, creado después del permiso, nunca en el HTML. Un enlace ya emitido sigue vivo hasta 60 s después de eliminar o dejar de compartir: se acepta.
- **[Eliminar deja un archivo huérfano o una fila sin archivo]** → D8: primero la fila y su entrada en una transacción; el archivo se borra al confirmar. El fallo posible es un objeto huérfano en un bucket privado (queda en el log), nunca una sesión que apunta a un archivo que no existe.
- **[Extracción en el envío]** (zona de cuidado) → D2 y D3: corre antes de la transacción, con topes de páginas, de tamaño descomprimido y de caracteres, y cualquier excepción deja la sesión sin texto. Se mide en la vista previa con un .docx y un PDF de 4 MB **antes** de construir las pantallas; si la función corta o la extracción pasa de 5 s, el apply se detiene y decide el equipo.
- **[Archivo hostil]** → D2: un PDF o un ZIP armados para gastar CPU o memoria. Topes y `try` amplio; lo que quede lo corta el tiempo máximo de la función, y esa docente ve el error de conexión de US-010. Lo provoca solo una cuenta Docente autenticada.
- **[`ck_sesion_terminos`]** (zona de cuidado) → D1: se reemplaza en la misma migración; las filas actuales ya cumplen la regla nueva. La vuelta atrás falla si ya hay una sesión que dejó de compartirse.
- **[Datos personales]** (RN-015) → el texto transcrito puede traer lo que la docente escribió; se muestra solo a quien ya puede descargar el archivo y nunca va al registro ni a los logs (D6, D8).
- **[Lecturas que escriben]** → D6: abrir la página y descargar escriben en `GET`. Son idempotentes para quien navega (la vista se cuenta una vez) y no cambian la sesión.
- **[HTML del texto]** → título, propósito y texto pasan por el autoescape de Django; nunca `|safe`.
- **[Historial de HTMX]** → D10: `hx-history="false"` en la pantalla; HTMX no guarda en `localStorage` una copia de las listas de un equipo compartido.
- **[Tarjeta café]** (zona de cuidado) → «Tu sesión» solo en las propias; DESIGN.md dice lo contrario y manda decisiones.md (va a la deuda).

## Goals / Non-Goals

**Goals:**
- Toda regla, consulta y escritura en `repositorio/servicios.py`; la extracción en `repositorio/texto.py`. Las vistas leen la petición, llaman al servicio y responden.
- Las listas y los filtros funcionan como enlaces y formularios normales; HTMX solo evita recargar.
- La laptop y la integración continua siguen sin R2.

**Non-Goals:**
- Visor de Word, miniatura real del archivo u OCR.
- Búsqueda con relevancia, sinónimos o índice de texto completo.
- Editar los datos de una sesión enviada.
- Funcionar sin JavaScript en los diálogos (eliminar, términos, panel de filtros del celular): como en US-010.

## Decisions

### D1. Modelo (`repositorio/models.py`, migración `0002`)
- `Sesion.texto` (`TextField`, vacío por defecto): texto transcrito, hasta 100 000 caracteres. `Sesion.texto_busqueda` (`TextField`, vacío por defecto): título, propósito y texto, normalizados (D4). Los dos los escribe solo `servicios`.
- `ck_sesion_terminos` pasa a `compartida = false OR terminos_aceptados_en IS NOT NULL`.
- `SesionVista` (`sesion_vista`): `sesion` (`CASCADE`), `usuario` (`PROTECT`, como el resto del modelo), `creado_en`; `UNIQUE (sesion, usuario)`. Guarda el dato que mide la tesis sobre el uso del repositorio junto con SESION_VISTA y SESION_DESCARGADA del registro.
- Índice nuevo `idx_sesion_autor_fecha (autor, -creado_en)` en lugar de `idx_sesion_autor`, para «Mis sesiones». El repositorio usa `idx_sesion_busqueda`.
- *Alternativa descartada:* contar las vistas desde `registro_actividad`. Ata una función de la pantalla al registro de auditoría, que no se borra con la sesión ni tiene unicidad.

### D2. Extracción del texto (`repositorio/texto.py`)
- `extraer_texto(archivo, tipo_mime) -> str`: nunca lanza; ante cualquier excepción devuelve `""` y deja un `logger.warning` con el tipo de excepción, sin el nombre del archivo. Deja el archivo al principio.
- **.docx:** `word/document.xml` con `zipfile`; si su tamaño descomprimido declarado pasa de 8 MB, no se lee; se lee con tope de 8 MB. `ElementTree` con el `_SinDoctype` que ya existe. Un párrafo (`w:p`) es una línea; `w:tab` y `w:br` se respetan.
- **PDF:** `pypdf`, `strict=False`, como máximo 40 páginas, y se detiene al llegar a 100 000 caracteres. Un PDF cifrado devuelve `""`.
- Limpieza: sin `\x00` ni caracteres de control (PostgreSQL rechaza el NUL), espacios repetidos reducidos, no más de dos saltos seguidos, recorte a 100 000.
- Antes de usar `pypdf` se consulta su documentación actual (Context7): el repo no lo usa.
- *Alternativas:* `pdfminer.six` (más pesado y lento), `python-docx` (dependencia innecesaria: basta el XML), OCR (fuera de alcance).

### D3. Cuándo se extrae
- En `enviar_sesion`, después de validar y **antes** de `_guardar`, fuera de la transacción: la fila se crea ya con `texto` y `texto_busqueda`. Un reintento con el mismo UUID devuelve la sesión previa sin extraer otra vez. Se registra la duración en el log (milisegundos y tipo, sin título).
- Sesiones anteriores: comando `extraer_textos`, que recorre las sesiones con `texto` vacío (la migración `0002` ya llenó `texto_busqueda`), abre su archivo del almacenamiento y guarda. Es repetible. Lo corre el equipo una vez contra producción después de la fusión.
- *Alternativa descartada:* migración de datos. Correría en el build de Vercel, dependería de R2 y metería código de `servicios` en una migración; además, `texto_busqueda` vacío dejaría fuera de la búsqueda por título a las anteriores hasta correr el comando, por eso la migración `0002` sí rellena `texto_busqueda` con el título y el propósito normalizados (`RunPython` con una copia fija de la normalización de D4, sin R2).
- Medición (equipo): con la parte B desplegada en la vista previa, enviar un .docx y un PDF de 4 MB con texto; leer la duración en el log de la función.

### D4. Búsqueda
- `normalizar(texto)`: NFKD, sin marcas diacríticas, `casefold`, espacios reducidos («Recomendación» → «recomendacion»; «ñ» → «n»). `texto_busqueda = normalizar(titulo + proposito + texto)`.
- La consulta: `q` recortada a 100 caracteres, normalizada y partida en palabras (hasta 8); cada palabra es un `texto_busqueda__contains` (Django escapa `%` y `_`), unidas con Y.
- Sin índice: el filtro previo por institución y `compartida` deja pocas filas. `pg_trgm` y `unaccent` quedan como deuda.
- *Alternativa descartada:* `unaccent` + `icontains` sobre tres columnas. Pide la extensión en Neon, en Docker y en la integración continua y `django.contrib.postgres`, para el mismo resultado.

### D5. Visibilidad y consultas (`repositorio/servicios.py`)
- `sesion_visible(usuario, id) -> Sesion | None`: la sesión si `autor == usuario`, o si `compartida` y `institucion_id == usuario.institucion_id`; si no, `None`. Es la única puerta de la página, la descarga, la vista y las escrituras.
- `mis_sesiones(usuario, pagina)` y `buscar_repositorio(usuario, q, grado, area, pagina)`: 20 por página, orden `-creado_en, pk`; sin cargar `texto` ni `texto_busqueda` (`defer`), con las primeras líneas anotadas (`Left("texto", 600)`) para la página dibujada y, en «Mis sesiones», `Count("vistas")`. Devuelven también si hay más.
- `conteos_por_area(usuario, q, grado)`: una consulta agrupada, sobre las áreas que la institución trabaja (orden SIAGIE). Los contadores de las pestañas son totales sin filtros.
- Grado y área inválidos se ignoran (no son error): llegan por la dirección.
- Agrupar por día: en el servicio, con la fecha en hora de Lima; «Hoy», «Ayer» y luego «lun 2 nov».

### D6. Vistas y descargas
- `registrar_vista(usuario, sesion)`: si no es la autora, `get_or_create` de `SesionVista` y, solo si se creó, `registrar(SESION_VISTA)`, en una transacción. La llama la vista de la página.
- `entregar_archivo(usuario, id, modo)`: `sesion_visible`; `modo="ver"` solo si es PDF; registra SESION_DESCARGADA (`{"modo", "propia"}`) y devuelve lo que la vista necesita para responder (D7).
- Las descargas no se muestran en ninguna pantalla.

### D7. Entrega del archivo
- Con `S3Storage`: `302` a `storages["sesiones"].url(clave, parameters={"ResponseContentDisposition": …, "ResponseContentType": tipo}, expire=60)`. Con otro almacén: `FileResponse` del propio aplicativo. En los dos, el encabezado se arma con `django.utils.http.content_disposition_header` (nombre original, RFC 5987) y la respuesta lleva `Cache-Control: no-store`; la local, además, `X-Content-Type-Options: nosniff`.
- «Ver» es un enlace con `target="_blank" rel="noopener"`; «Descargar», un enlace normal.
- La firma de `.url()` con `parameters` y `expire` se confirma con la documentación de django-storages (Context7) y, en la vista previa, que R2 respeta el nombre y el modo (tarea del equipo).
- *Alternativa descartada:* pasar el archivo por la función de Vercel. Suma tiempo y memoria a cada descarga sin dar más control: el permiso ya se revisó.

### D8. Escrituras de la autora
- `eliminar_sesion(usuario, id)`, `compartir_sesion(usuario, id, acepta)` y `dejar_de_compartir(usuario, id)`: en `transaction.atomic`, con la fila bloqueada (`select_for_update`). Orden de las comprobaciones: no visible → `SesionNoDisponible`; visible y ajena → `registrar(INTENTO_SIN_PERMISO)` y `SoloLaAutora`; sin cambio (ya compartida, ya no compartida) → devuelve sin registrar.
- Una ajena no visible también registra INTENTO_SIN_PERMISO antes de responder 404 (misma respuesta que inexistente; la entrada no revela nada a quien pide).
- `compartir_sesion` exige `acepta`; guarda `compartida=True` y `terminos_aceptados_en=now()`. `dejar_de_compartir` solo cambia `compartida`.
- Borrado: `_borrar_sesiones(queryset)` borra las filas (sus vistas caen por `CASCADE`) y programa con `transaction.on_commit` el borrado de cada clave; un fallo del almacén se registra con `logger.exception` y la clave, y no se propaga. `eliminar_sesion` le suma el permiso y SESION_ELIMINADA; `quitar_demo` la llama con las sesiones de cuentas demo, sin entrada por sesión (D11).
- Respuestas (formularios normales, `POST`, patrón PRG con `django.contrib.messages`): eliminar → `303` a «Mis sesiones» con «Sesión eliminada»; compartir y dejar de compartir → `303` a la página. `SoloLaAutora` → `403` con la página de la sesión y el Mensaje de error; `SesionNoDisponible` → `404` con la página «no disponible». Compartir sin aceptar → `400` con su mensaje.

### D9. KPI-01 y «sesiones cargadas»
No se resta nada al eliminar. KPI-01 cuenta docentes distintas por semana: reenviar no la cambia. «Sesiones cargadas» cuenta envíos, y un envío eliminado fue un envío. El spec `indicadores-adopcion` no cambia. Si la tesis pide el neto, sale del registro: SESION_ENVIADA menos SESION_ELIMINADA (va a `docs/PENDIENTES_TESIS.md`).

### D10. Rutas, vistas y HTMX
- Bajo `/docente/sesiones/`: `""` (Mis sesiones), `repositorio/`, `<uuid:id>/`, `<uuid:id>/descargar/`, `<uuid:id>/ver/` (GET); `<uuid:id>/compartir/`, `<uuid:id>/dejar-de-compartir/`, `<uuid:id>/eliminar/` (POST). `enviar/` no cambia. Todas con `DocenteMixin`.
- Las dos listas responden la página completa o, con `HX-Request`, solo el fragmento de resultados, con los contadores, los filtros y los filtros activos como intercambios fuera de banda; `Vary: HX-Request`. `?pagina=N` devuelve solo las tarjetas siguientes («Ver más» las agrega y mueve el foco a la primera nueva).
- Pestañas: enlaces reales dentro de un `tablist`; un script corto mueve foco y selección con las flechas. El indicador se mueve con `transform` (E-07) y sin transición cuando el cambio vino del teclado (E-06).
- Buscador: formulario `GET`; con HTMX, `input changed delay:400ms` y `hx-sync` para descartar respuestas viejas; solo se reemplaza el panel de resultados, nunca el campo. Filtros: enlaces con la dirección ya armada.
- Panel de filtros: un solo marcado; hasta 699 px se presenta como panel (`<dialog>`), sin duplicar `id`. Filtros activos: `role="group"` con `aria-label`, solo si hay alguno (C-01).
- Después de un envío, `sesiones.js` emite un evento y el panel de resultados vuelve a pedir su dirección actual.
- Un `id` que no es UUID no llega a la vista: 404 de Django.

### D11. Demostración (`institucion/demo.py`)
- `cargar_demo` crea unas 10 sesiones con UUID determinista (`uuid5` de la cuenta y un índice), repartidas entre las cuentas demo, grados y áreas, con `creado_en` de varios días; archivos generados en código (PDF mínimo con capa de texto, PDF sin texto y .docx), pasados por `extraer_texto`. No pasa por `enviar_sesion` ni registra SESION_ENVIADA. Si la transacción falla, borra los archivos que escribió. Las que ya existen se saltan.
- `quitar_demo`: `_borrar_sesiones(Sesion.objects.filter(autor__es_demo=True))` y borra las `SesionVista` de cuentas demo; el resumen de DEMO_QUITADA suma `sesiones`.

### D12. Pruebas e2e: 9 nuevas
Son dos pantallas nuevas con conducta de JS propia. Lista (`test_repositorio_e2e.py`): (1) buscar, filtrar y abrir una sesión; (2) pestañas con flechas y «atrás»; (3) el buscador conserva el foco y anuncia el total; (4) panel «Filtrar» a 360 px; (5) la lista se actualiza tras enviar; (6) desplazamiento y axe de las dos listas y del panel. Página (`test_detalle_e2e.py`): (7) eliminar con su diálogo, cancelar y confirmar; (8) compartir con los términos y dejar de compartir; (9) desplazamiento y axe de la página y sus dos diálogos. Todo lo demás (permisos, textos, enlaces, 403 y 404) va como prueba de vista.

## Risks / Trade-offs

- [La búsqueda sin índice se vuelve lenta con miles de sesiones compartidas] → deuda: `pg_trgm` sobre `texto_busqueda`.
- [`texto_busqueda` duplica el texto en la base] → hasta 100 000 caracteres por sesión; se acepta por no depender de extensiones.
- [PDF con texto en columnas o tablas sale desordenado] → sirve para buscar; la nota de la vista previa lo advierte.
- [Objeto huérfano en R2 si falla el borrado] → queda en el log; limpieza a mano (deuda: comando de conciliación).
- [«Ver más» con una sesión nueva entre páginas puede repetir una tarjeta] → orden estable por `-creado_en, pk`; se acepta.
- [R2 no respeta `ResponseContentDisposition`] → se comprueba en la vista previa; si no, se entrega por la función (alternativa de D7).
- [La entrada INTENTO_SIN_PERMISO en una ajena no visible] → no cambia la respuesta ni su tiempo de forma apreciable; no revela existencia.

## Migration Plan

1. `repositorio/0002`: campos, `texto_busqueda` rellenado con título y propósito, `sesion_vista`, índice y `CHECK`. `actividad/000N` (el número siguiente): `CHECK` de operaciones. Las aplica el build de Vercel.
2. Parte B desplegada en la vista previa → medición de D3. Si falla, se detiene.
3. Después de la fusión: el equipo corre `extraer_textos` contra producción.
4. Vuelta atrás: revertir el PR. `0002` hacia atrás falla si hay sesiones no compartidas con fecha; en ese caso, antes se limpia esa fecha a mano.

## Open Questions

- ¿La tesis quiere «sesiones cargadas» neto de eliminadas? No cambia lo que se construye (D9); se anota en `docs/PENDIENTES_TESIS.md`.
