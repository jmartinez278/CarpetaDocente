# Propuesta: US-018 – Cargar sesiones del repositorio inicial

## Why

El primer día del piloto el repositorio estaría vacío: solo tiene lo que comparten las docentes. US-018 (RF-018) deja que el Administrador cargue, desde el panel, sesiones de referencia con su fuente y su permiso de uso (RN-020), para que la docente encuentre material desde el inicio. Es la **dimensión 1 (planificación de sesiones de aprendizaje)**; la tesis sigue midiendo el uso del repositorio con las vistas y descargas que ya se registran, y estas sesiones no inflan «sesiones cargadas» ni KPI-01.

## What Changes

Se aplican tal cual las decisiones 1 a 8 de `insumos/US-018/decisiones.md` (sin bocetos). Lo nuevo de este propose:

- **Varios grados como rango**: una sesión de referencia guarda un grado inicial y uno final (3.º a 5.º); la de una docente tiene los dos iguales. El filtro de grado la encuentra con cualquier grado del rango, sin índice nuevo (design D2).
- **En el repositorio, como compartida**: la sesión de referencia queda «compartida» en la base, sin autora, sin estado de envío ni términos; así la ven las listas, la búsqueda, la página, la descarga y el conteo de vistas que ya existen, con las mismas reglas de institución (design D1).
- **Institución elegida en el panel**: el Administrador no siempre tiene institución; la ficha la pide y el área debe ser una que esa institución trabaja (RN-007).
- **Archivo fijo**: editar cambia los datos, no el archivo. Para cambiarlo se elimina y se carga de nuevo.
- **Operaciones nuevas**: SESION_REFERENCIA_CARGADA, SESION_REFERENCIA_EDITADA y SESION_REFERENCIA_ELIMINADA. Ninguna cuenta para KPI-01 ni para «sesiones cargadas».
- **El panel permite borrar un solo modelo**: la sesión de referencia, desde su ficha y con su operación registrada; la acción masiva de borrar no está. Los demás modelos siguen sin borrar (RN-023).
- **Una docente que intenta eliminar, compartir o dejar de compartir una sesión de referencia** con una petición armada a mano recibe «Solo el autor puede eliminar esta sesión» y queda INTENTO_SIN_PERMISO, como con la sesión de una colega.
- **BREAKING (base de datos)**: `autor` admite vacío, `estado` admite vacío y cambian `ck_sesion_origen`, `ck_sesion_estado`, `ck_sesion_grado` y `ck_sesion_terminos`; se suman columnas y restricciones (design D1).

**Fuera de alcance:**
- Varios grados en las sesiones de las docentes → historia futura, si la I.E. tiene aulas multigrado.
- Carga masiva por comando → no se hará por ahora.
- La dirección ve el material de referencia (decisión 3) cuando tenga su pantalla de sesiones → bloque 2; hoy la pantalla Sesiones es solo del rol Docente.
- Sesión adaptada → US-013; entregada por la dirección → US-017.
- Descargar el archivo desde el panel → no hace falta para cargar; el Administrador no usa la pantalla Sesiones.

**Contradicciones que solo se mencionan (documentos congelados, van a la deuda):**
- Doc 11, tabla `sesion`: `grado` es un solo valor (aquí se suma `grado_hasta`), no prevé `estado` vacío ni los `CHECK` nuevos; `fuente` y `permiso_uso` sí están.
- Criterio de US-018: «tipo de permiso»; aquí es texto libre de 300 caracteres, como en el doc 11.

## Capabilities

### New Capabilities

- `material-referencia`: la carga, edición y eliminación de sesiones de referencia en el panel del Administrador: datos obligatorios, fuente y permiso de uso, varios grados, archivo y texto transcrito, quién puede hacerlo, sus operaciones de actividad y que no cuenten en los indicadores.

### Modified Capabilities

- `repositorio-sesiones`: «Repositorio de la institución» incluye el material de referencia; requisito nuevo para su tarjeta, el filtro por cualquiera de sus grados y su ausencia en «Mis sesiones».
- `detalle-sesion`: «Quién ve una sesión» incluye el material de referencia; requisito nuevo para su página (fuente y permiso de uso, sin acciones de autora) y para el intento de una docente de eliminarla o cambiarla.
- `registro-actividad`: el catálogo suma las tres operaciones de referencia.

## Impact

- **Código:**
  - `src/backend/repositorio/`: `Sesion` (origen REFERENCIA, `grado_hasta`, `fuente`, `permiso_uso`, `autor` y `estado` opcionales, `CHECK`), modelo proxy `SesionReferencia`, migración `0003`; `servicios.py` (validar, cargar, editar y eliminar la referencia; filtro de grado por rango); `admin.py`; plantillas `_lista.html` y `sesion.html`; pruebas.
  - `src/backend/actividad/`: tres operaciones, su detalle permitido y su migración; `panel.py` admite el borrado de un `ModelAdmin` que declara su operación.
- **Rutas:** ninguna nueva fuera del panel (`/admin/repositorio/sesionreferencia/`, que da Django). No cambia el Catálogo de rutas de `docs/03`.
- **Dependencias:** ninguna.
- **Requisitos:** US-018, RF-018, RN-007, RN-015, RN-020, RN-023, RNF-002. DoD 1 a 9.
- **Rama:** `feature/us-018-cargar-sesiones-referencia`, apilada sobre US-011/012/016 (sin fusionar); su primer commit (archivo de `us-011-012-016`) ya está.
