# Propuesta: US-011, US-012 y US-016 – Mis sesiones y repositorio (buscar, descargar, eliminar)

## Why

La docente ya envía sus sesiones (US-010), pero no puede volver a verlas, descargarlas ni retirarlas, y no ve las que comparten sus colegas. US-011 (RF-011), US-012 (RF-012) y US-016 (RF-016) cierran ese circuito para el rol Docente. Es la **dimensión 1 (planificación de sesiones de aprendizaje)**; para la tesis guarda quién vio y quién descargó cada sesión (uso del repositorio).

## What Changes

Se aplican tal cual `insumos/US-011/decisiones.md` (decisiones 1 a 18); la referencia visual es `insumos/rebrand/repositorio.html` y `sesion.html`. Lo nuevo de este propose:

- **Rutas**: `/docente/sesiones/` es «Mis sesiones» y `/docente/sesiones/repositorio/` el «Repositorio»; la página de la sesión es `/docente/sesiones/<id>/` (la decisión 9 decía `/sesiones/<id>/`; se conserva el prefijo que ya existe). La búsqueda y los filtros viajan en la dirección (`?q=`, `grado`, `area`), así que un resultado se puede recargar o volver con «atrás».
- **Búsqueda**: varias palabras se buscan todas (Y), en cualquier orden, en el título, el propósito o el texto; un grado y un área a la vez. Sin índice nuevo (design D4).
- **Texto transcrito**: se guarda recortado a 100 000 caracteres; del PDF se leen como máximo 40 páginas. Las sesiones ya enviadas se procesan con un comando que corre el equipo una vez, no con una migración que dependa de R2 (design D3).
- **Vistas**: cuenta la primera vez que cada colega abre la página de una sesión ajena; solo esa primera vez deja entrada de actividad. Cada «Descargar» y cada «Ver» deja la suya, también los de la autora (design D6).
- **Operaciones nuevas**: SESION_VISTA, SESION_DESCARGADA, SESION_COMPARTIDA, SESION_DESCOMPARTIDA y SESION_ELIMINADA. Ninguna cuenta para KPI-01.
- **KPI-01 y «sesiones cargadas» no se restan** al eliminar: el registro no se reescribe y cada envío fue un uso real; SESION_ELIMINADA permite calcular el neto si la tesis lo pide (design D9).
- **Eliminar, compartir o dejar de compartir una sesión ajena** con una petición armada a mano deja INTENTO_SIN_PERMISO.
- **Después de enviar**, la lista de la pestaña abierta se actualiza sola; el estado vacío ya no queda bajo el Mensaje de éxito.
- **BREAKING (base de datos)**: `ck_sesion_terminos` pasa de «compartida ⇔ fecha» a «compartida ⇒ fecha».

**Fuera de alcance:**
- Bandeja, visto bueno, búsqueda y descarga de la dirección → bloque 2 (RF-011 y RF-012 la incluyen; aquí solo el rol Docente).
- Guardadas (marcador) → historia futura. Adaptada → US-013; entregada por la dirección → US-017; repositorio inicial → US-018; competencias de la sesión → después del Sprint 3.
- Botón de tema (T-04) → su propio cambio en esta rama.
- Índice `idx_sesion_titulo_trgm` y extensión `pg_trgm` (doc 11) → deuda, si la búsqueda se vuelve lenta.

**Contradicciones que solo se mencionan (documentos congelados, van a la deuda):**
- RF-015 se retiró («no hay sesiones privadas») y «Dejar de compartir» lo revive; RF-016 y US-016 dicen «la retira del repositorio» y aquí eliminar anula la entrega también para la dirección.
- Doc 11, tabla `sesion`: suma `texto` y `texto_busqueda`, la tabla `sesion_vista` y el `CHECK` relajado; sin `pg_trgm`.
- DESIGN.md («No añadas tarjetas café a Repositorio o Sesión») frente a la tarjeta café «Tu sesión» de `sesion.html` y de la decisión 9: manda decisiones.md.

## Capabilities

### New Capabilities

- `repositorio-sesiones`: las pestañas «Mis sesiones» y «Repositorio» de la pantalla Sesiones: listas, tarjeta, búsqueda por palabra, filtros de grado y área, paginación, estados vacíos y el texto transcrito que alimenta la búsqueda.
- `detalle-sesion`: la página de una sesión: quién la ve, sus datos y la vista previa del texto, Descargar y Ver, el conteo de colegas que la vieron, y las acciones de la autora (compartir, dejar de compartir y eliminar).

### Modified Capabilities

- `envio-sesiones`: «Pantalla Sesiones» (cabecera sin subtítulo, pestañas, portada disponible), «Envío exitoso» (la lista se actualiza) y «Sesión guardada» (texto transcrito; compartida ⇒ fecha).
- `almacenamiento-archivos`: enlaces firmados de descarga (la otra mitad de EN-03) y borrado del archivo al eliminar la sesión.
- `registro-actividad`: el catálogo suma las cinco operaciones; ver y descargar una sesión son lecturas que sí se registran; requisito nuevo «Operaciones sobre sesiones».
- `pantallas-de-inicio`: la bandera de Sesiones se enciende en la portada y en el ☰.
- `datos-demostracion`: sesiones de ejemplo al cargar y su borrado, con archivos, al quitar.

## Impact

- **Código:**
  - `src/backend/repositorio/`: `Sesion` (`texto`, `texto_busqueda`, `CHECK`), `SesionVista`, migración `0002`; `servicios.py` (listas, búsqueda, visibilidad, vistas, enlace del archivo, eliminar, compartir) y un módulo nuevo para la extracción de texto; vistas, rutas, comando `extraer_textos`, pruebas.
  - `src/backend/actividad/`: cinco operaciones, su detalle permitido y su migración.
  - `src/backend/institucion/demo.py` (sesiones de ejemplo), `cuentas/dimensiones.py` (bandera), `templates/repositorio/`, `static/js/`, `src/frontend/` (CSS), íconos nuevos (buscar, filtrar, descargar, compartir, papelera).
- **Rutas nuevas:** `repositorio/`, `<uuid>/`, `<uuid>/descargar/`, `<uuid>/ver/`, `<uuid>/compartir/`, `<uuid>/dejar-de-compartir/` y `<uuid>/eliminar/`, bajo `/docente/sesiones/`. Se actualiza el Catálogo de rutas de `docs/03`.
- **Dependencias:** `pypdf` (Python puro) para leer el texto de los PDF. El .docx se lee con la biblioteca estándar.
- **Requisitos:** US-011, US-012, US-016, RF-011, RF-012, RF-016, EN-03 (enlaces firmados), RN-015, RNF-002, doc 09 §4. DoD 1 a 9.
- **Rama:** `feature/us-011-012-016-buscar-descargar-eliminar-sesion`; su primer commit (archivo de `rebrand-ajustes-auditoria`) ya está.
