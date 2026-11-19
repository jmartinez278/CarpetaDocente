# Propuesta: US-024 + US-025 – Completar la plantilla de notas del SIAGIE

## Why

Hoy la docente registra sus notas en CarpetaDocente y la dirección las vuelve a digitar en el SIAGIE, o las recibe en Excel por WhatsApp. Con este cambio la dirección sube la plantilla «Periodo por Excel» que ya descarga del SIAGIE y la recibe llena con las notas de la sección, sin que la docente exporte nada (RF-024 y RF-025). Es la **dimensión 2 (registro y control de notas)**: la tesis sigue cubierta por RF-024 en la lista de cotejo de la VI y en la ficha de la D2. El registro guarda cada llenado con sus conteos (PLANTILLA_SIAGIE_COMPLETADA).

## What Changes

Se aplican tal cual las decisiones 1 a 13 de `insumos/US-024/decisiones.md`, con los bocetos `seccion-a`, `resumen-b` y `resumen-b-limpio` y los estados únicos `index`, `subida`, `procesando` y `error`. Lo nuevo de este propose:

- **Dos pasos sin guardar el archivo**: si la sección no se reconoce sola, el servidor responde con la elección de sección y el navegador vuelve a enviar el mismo archivo junto con la sección elegida. El archivo nunca se guarda, ni de paso (design D3).
- **Descarga sin guardar**: la respuesta del llenado trae el resumen y el archivo lleno; la pantalla del resumen arma la descarga en el navegador. Si la dirección recarga, el resumen ya no está y vuelve al inicio (design D4).
- **Anexo de la institución**: `Institucion` suma `anexo` (0 por defecto), que el Administrador edita en el panel. Sin código modular, ninguna plantilla se reconoce (design D2).
- **Equivalencia de secciones**: modelo nuevo en `exportaciones`, una por sección de la I.E. y una por sección del SIAGIE en el año (design D5).
- **Competencia «01» = primera competencia activa del área en el orden del catálogo**, la misma regla que numera C1, C2… en la hoja de notas (design D6).
- **Estudiantes**: se cruzan con todos los de la sección, también trasladados y retirados; si dos coinciden con el mismo nombre normalizado, la fila no se toca y el nombre va a «No encontrados» (design D7).
- **Escritura de una nota**: el nivel y la conclusión juntos; con AD o A, la conclusión de la celda queda vacía. Una celda cuenta como reemplazada si tenía otro valor, también una fórmula (design D8).
- **«¿No es esta sección?»**: si la sección salió de una equivalencia, el resumen permite borrarla; la próxima plantilla vuelve a preguntar. Operación nueva EQUIVALENCIA_SECCION_BORRADA (design D13).
- **Título del resumen**: «Plantilla completada con observaciones» si hay no encontrados o faltan notas; si no, «Plantilla completada».
- **Seguridad del archivo**: .xlsx reconocido por su contenido, hasta 3 MB (la completada vuelve en base64 y debe caber en una respuesta de Vercel) y con límite de tamaño descomprimido; `defusedxml` entra junto con `openpyxl` (design D9).
- **BREAKING (base de datos)**: columna `institucion.anexo` y tabla nueva de equivalencias.

**Fuera de alcance:**
- Hoja propia de la docente para descargar (criterio original de US-024) → si el piloto la pide.
- Varias plantillas a la vez → si el piloto lo pide.
- Estado de entrega de las notas → US-026 / US-042.
- Consolidados de la dirección → US-041 (el estado vacío de US-040 sigue debajo).
- Trimestres: el periodo del SIAGIE en trimestres aún no se conoce; una plantilla de una institución por trimestres se rechaza → cuando se confirme (US-028).
- Alerta automática cuando hay muchos «no encontrados» (posible equivalencia equivocada) → deuda.

**Contradicciones que solo se mencionan (documentos congelados, van a la deuda):**
- RF-024/RF-025, US-024/US-025 (doc 02) y SUP-12 (doc 04): «docente», «hoja propia», «formato de la UGEL» y el mensaje «…al formato de notas de la UGEL». Manda decisiones.md.
- Doc 11: no tiene `anexo` en `institucion` ni la tabla de equivalencias.

## Capabilities

### New Capabilities

- `plantilla-notas-siagie`: subir la plantilla «Periodo por Excel» del SIAGIE, reconocerla, encontrar la sección (con su equivalencia), cruzar estudiantes, escribir los niveles y conclusiones, el resumen con sus cuatro conteos, la descarga, los rechazos y quién puede hacerlo.

### Modified Capabilities

- `pantallas-de-inicio`: «Inicio de la dirección» suma el bloque «Plantilla de notas del SIAGIE» con «Subir plantilla», encima de los consolidados.
- `registro-actividad`: el catálogo suma PLANTILLA_SIAGIE_COMPLETADA y EQUIVALENCIA_SECCION_BORRADA; un requisito nuevo para el detalle de cada una.
- `cuentas-usuarios`: «Entidad Institución» suma el anexo.

## Impact

- **Código:**
  - `src/backend/exportaciones/`: modelo de equivalencia y migración `0001`; `siagie.py` (lectura y escritura del libro con openpyxl), `servicios.py` (reconocer, resolver la sección, llenar, registrar), `views.py`, `urls.py`, `admin.py` (solo lectura); pruebas con plantillas ficticias generadas en la prueba.
  - `src/backend/institucion/`: `anexo` y su migración; el panel de la institución lo muestra.
  - `src/backend/direccion/`: plantilla del inicio con el bloque nuevo.
  - `src/backend/actividad/`: operación nueva, su detalle permitido y su migración.
  - Plantillas `templates/exportaciones/` y `static/js/plantilla-siagie.js` (subida, elección de sección, resumen y descarga).
- **Rutas:** `/direccion/plantilla-siagie/` y `/direccion/plantilla-siagie/equivalencias/<id>/borrar/` (POST). Cambia el Catálogo de rutas de `docs/03`.
- **Dependencias:** `openpyxl` y `defusedxml`.
- **Requisitos:** US-024, US-025, RF-024, RF-025, RN-002, RN-015, RNF-002, RNF-003, RNF-006. DoD 1 a 9.
- **Rama:** `feature/us-024-025-completar-plantilla-siagie`, desde `main` con US-018 archivada.
