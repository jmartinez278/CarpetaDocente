# Propuesta: ajustes de la auditoría visual del rebrand

## Why

La auditoría sobre `af7780c` (`insumos/rebrand-auditoria/informe.md`) dejó desviaciones de DESIGN.md 1.1 y de specs vigentes en Asistencia, Estudiantes, Notas y Sesiones (pantallas de US-030, US-006, US-020 y US-010; las tres dimensiones). Van antes de US-011/012/016.

## What Changes

- Ids aprobados: A-01, A-02 (también durante el lote), A-03, A-04, A-07, A-09, A-10, A-14 y A-15. Sin boceto: la norma es DESIGN.md y las specs `asistencia-jornada` y `registro-notas`, que no cambian (`skip_specs`).
- **Fuera:** A-05 (con el rótulo, la píldora activa no cabe en la tira a 360 px; Marco, 15-11-2026: se queda el círculo y va a la deuda), A-06 y A-08 (chocan con `registro-notas:150/161/169`; van a la deuda), A-11, A-12/T-04 y A-13 (ya en la Deuda del PR #73).

## Impact

Plantillas `asistencia/_tarjeta.html` y `notas/hoja.html`; `asistencia.js`, `notas.js`; CSS de asistencia, estudiantes, notas y `componentes.css` (pie de diálogo, compartido). Sin rutas, vistas, modelos ni datos nuevos.
