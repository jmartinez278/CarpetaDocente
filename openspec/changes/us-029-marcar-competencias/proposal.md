# Propuesta: US-029 – Marcar las competencias desarrolladas en el periodo

## Why

El registro de notas (US-020) debe pedirle a la tutora solo las competencias que trabajó en el bimestre, y al cierre del año todas deben tener nivel (RN-005). US-029 (RF-029, prioridad Alta) guarda esas marcas por sección y periodo. Es parte de la **dimensión 2 (registro y control de notas)**: no mide todavía un indicador de la tesis, pero `competencia_periodo` es la base de la completitud de notas (US-022) y del registro de US-020.

## What Changes

Las decisiones 1 a 17 de `insumos/US-029/decisiones.md` se aplican tal cual, y la interfaz sale del prototipo aprobado (`insumos/prototipo/US-029-bocetos/`). Lo nuevo de este propose:

- **El guardado solo toca lo que la tutora puede marcar**: las competencias activas de sus áreas (`puede_marcar`). Las marcas de otras áreas (docente de curso) o de competencias desactivadas no se crean ni se borran desde su pantalla (design D4).
- **Conjunto vacío rechazado**: «Marca al menos una competencia para guardar.». Sin una fila que diga «el periodo ya se guardó», un conjunto vacío volvería a abrir con todo marcado (design D5).
- **Antes del primer periodo** (año ABIERTO, hoy antes del inicio del periodo 1): aviso «Hoy no hay un periodo vigente» y la fecha en que empieza el primero, sin periodos que elegir. La pantalla dice «Bimestre» o «Trimestre» según la organización de la institución.
- **Borrador pendiente visible**: el botón de un bimestre con cambios sin guardar dice «Sin guardar» (P2 de `notas.md`). Las instrucciones no aparecen en los estados vacíos (P3).
- **Demo**: no toca `a_cargo_docente_curso`; ese valor lo pone el Administrador en el panel. Volver a cargar marca los periodos que aún no tienen marcas.

**Fuera de alcance (deuda para la descripción del PR):**
- Enlace desde la tarjeta Notas, qué hace notas con un periodo sin marcas y `tiene_notas` con `calificacion` real → US-020.
- Estudiantes sin nivel en las competencias marcadas → US-022. Exonerados (RN-010) → US-035. Bloqueo por entrega (RN-022) → historia de entrega.
- Docentes de curso (área × sección, sus marcas) y Computación → historia de docentes de curso, sin ID.
- Guardar los borradores si la sesión vence: hoy se avisa y se pierden al salir.
- Consultar las marcas de un año CERRADO (decisión 3): hoy es «página no encontrada», como la asistencia → US-009 / historial.

**Contradicciones que solo se mencionan (documentos congelados):**
- Doc 08: la docente tiene CU sobre las marcas; desmarcar es un DELETE (decisión 6).
- Doc 11, 3.3: `institucion_area` no tiene `a_cargo_docente_curso`; amplía lo editable en el panel de EN-06.
- Criterio de US-029, flujo alternativo: «al abrir el registro de notas» se cumple aquí en la pantalla de marcado y en el servicio; US-020 lo llama al abrir las notas.

## Capabilities

### New Capabilities

- `competencias-periodo`: marcas de competencias desarrolladas por sección y periodo; quién marca, qué periodos se marcan, estado inicial, guardado del conjunto, desmarcado con notas, competencias obligatorias del último periodo y la pantalla de marcado.

### Modified Capabilities

- `catalogo-curricular`: «Áreas que trabaja cada institución» y «Mantenimiento del catálogo en el panel» suman la marca «a cargo del docente de curso».
- `registro-actividad`: «Catálogo cerrado de operaciones» suma COMPETENCIAS_MARCADAS, que no cuenta para KPI-01.
- `datos-demostracion`: nuevo requisito «Competencias marcadas de ejemplo» (cargar, quitar y descartar).

## Impact

- **Código:**
  - `src/backend/notas/`: `models.py` (`CompetenciaPeriodo`), migración `0001`, `servicios.py`, `views.py`, `urls.py` y pruebas.
  - `src/backend/catalogo/`: `models.py` (`a_cargo_docente_curso`), migración `0003`, `admin.py`.
  - `src/backend/actividad/`: operación nueva, `DETALLE_PERMITIDO` y su migración de `choices`.
  - `src/backend/institucion/demo.py`: marcas en la carga; borrado en el retiro y el descarte.
  - `config/urls.py`, `templates/notas/`, `static/js/competencias.js`, `src/frontend/` (CSS).
- **Rutas:** `/docente/secciones/<id>/competencias/` (GET) y `/docente/secciones/<id>/competencias/<numero>/` (POST). Se actualiza el Catálogo de rutas de `docs/03`. El README no cambia.
- **Dependencias:** ninguna.
- **Requisitos:** US-029, RF-029, RN-005, RN-007, RN-008, RN-015, doc 11 (3.5). DoD 1 a 9.
- **Rama:** `feature/us-029-marcar-competencias-desarrolladas`, desde `main`; su primer commit (archivo de US-028) ya está.
