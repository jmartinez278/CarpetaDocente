# Propuesta: rebrand de Asistencia (US-030)

## Why

Paso 4 de `insumos/rebrand/PLAN.md`: `asistencia/hoy.html` pasa a `marco_rebrand.html` y `rebrand.css` con el boceto `insumos/rebrand/asistencia.html` y sus estados (`capturas/estado-asistencia-*`), según `insumos/rebrand-asistencia/decisiones.md`. Cubre RF-030, dimensión **control de asistencia**; no guarda datos nuevos.

## What Changes

- Encabezado, selector, lista, una sola tarjeta café «Tu jornada» (lateral en PC, resumen fijo en el celular), leyenda, barra de «Deshacer» y estados sin boceto con `rb/`; conteo visible «18/25 marcados» / «18/25 · 7 sin marcar» con texto accesible aparte (design D1–D5).
- Lo nuevo de este propose: con todo marcado se conserva el resumen de totales de la spec en lugar del «12/12 · 0 sin marcar» del boceto, y durante el lote se conserva «Pendiente de deshacer» en lugar de «6 sin guardar» (design D4).
- **Fuera de alcance:** botón de tema → T-04; borrar el CSS de asistencia de `app.css` y los parciales viejos → paso 8; auditoría visual → al final del rebrand.

## Capabilities

### Modified Capabilities

- `asistencia-jornada`: «Avance de la jornada» (conteo visible nuevo y texto accesible) y «Asistencia accesible y sin desplazamiento horizontal» (vistas con el marco del rebrand).

## Impact

Plantillas `asistencia/*.html` y `rb/estado_vacio.html`; nuevo `rebrand/pantallas/asistencia.css` y su línea en `rebrand.css`; en `asistencia.js` solo clases y fragmentos de marcado; pruebas de `asistencia`. Sin cambios en rutas, vistas, servicios ni modelos.
