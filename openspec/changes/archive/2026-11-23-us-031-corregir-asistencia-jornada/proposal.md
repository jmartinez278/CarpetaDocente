# Propuesta: US-031 – Corregir la asistencia de una jornada

## Why

Hoy la pantalla de asistencia solo responde el día actual: una marca equivocada de ayer, una justificación que llega después o un día que la docente olvidó tomar no se pueden registrar. Con este cambio el selector de semana abre los días anteriores del año escolar y los guardados aceptan esas fechas (RF-031). Es la **dimensión 3 (control de asistencia)**. El registro de actividad distingue la corrección de un día pasado con `correccion: true` en ASISTENCIA_CAMBIADA, así la tesis puede contar las correcciones sin una operación nueva.

## What Changes

Se aplican tal cual las decisiones 1 a 9 de `insumos/US-031/decisiones.md`; no hay bocetos (la pantalla es la de US-030). Lo nuevo de este propose:

- **Destino de las flechas**: la flecha de semana abre el mismo día de la semana anterior (o siguiente); si cae antes del inicio del año, abre el primer día de clases del año; si cae después de hoy, abre hoy (design D3).
- **`asistencia/<fecha de hoy>/`** muestra lo mismo que `asistencia/`; los enlaces del selector a hoy usan `asistencia/` (design D2).
- **Fin de semana con fecha**: un sábado o domingo en la ruta responde 404, como un día fuera de rango; «Hoy no hay clases» queda solo para `asistencia/` (design D2).
- **«Fuera del registro»** de un día pasado dice el día: «Fuera del registro del lunes 16» (design D5).
- **Periodo cerrado**: el guardado rechazado responde 409, como la fecha no válida, y la recarga muestra el aviso (design D6).
- **Deuda de US-008**: `editar_estudiante` guarda solo apellidos y nombres (`update_fields`), para que una copia vieja no revierta `estado` ni `fecha_estado` sin registro; la decisión 6 depende de esa fecha.

**Fuera de alcance:**
- Bloqueo real por notas entregadas, mensaje verificado y quién habilita la corrección → US-026 (aquí solo el enganche `periodo_cerrado`).
- Historial, totales por periodo e ingresos tardíos (RN-012) → US-033.
- Quién registra traslados y retiros (`fecha_estado`) → pregunta abierta a la I.E., sin historia.
- Deslizar entre días en el celular → pulido final.
- Recuperar marcas pendientes de días pasados con la sesión vencida → deuda.
- Sábados de recuperación y feriados → no se distinguen.

**Contradicciones que solo se mencionan (van a la deuda):**
- El caso de error de US-031 (doc 02) depende de RN-022 y del estado de entrega de US-026, que aún no existen: su prueba real pasa a US-026.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `asistencia-jornada`: «Solo la jornada de hoy» pasa a «Días que se pueden abrir» (hoy y los días de clases anteriores del año ABIERTO); el selector navega; la lista, el avance, el cierre y los textos dependen del día abierto; requisito nuevo «Periodo cerrado»; la revisión de accesibilidad suma las vistas «día pasado» y «periodo cerrado».
- `registro-actividad`: «Cambios de asistencia» suma `correccion: true` cuando la jornada no es de hoy.

## Impact

- **Código:**
  - `src/backend/asistencia/`: `servicios.py` (rango del año, activos de un día, validación de fecha, `periodo_cerrado`, `correccion`), `views.py` (vista de un día), `urls.py` (ruta `<fecha>/`).
  - `src/backend/actividad/servicios.py`: `correccion` en el detalle permitido de ASISTENCIA_CAMBIADA.
  - `src/backend/institucion/servicios.py`: `editar_estudiante` con `update_fields`.
  - Plantillas `templates/asistencia/` (`hoy.html`, `_selector.html`, `_tarjeta.html`) y `static/js/asistencia.js` (anuncio del cierre con el día).
- **Rutas:** `docente/secciones/<id>/asistencia/<fecha>/` (GET). Cambia el Catálogo de rutas de `docs/03`.
- **Base de datos:** sin migraciones.
- **Requisitos:** US-031, RF-031, RF-008, RN-011, RN-012, RN-015, RN-026, RN-027, RNF-002. DoD 1 a 9.
- **Rama:** `feature/us-031-corregir-asistencia-jornada`, desde `main` con US-024/025 archivada.
