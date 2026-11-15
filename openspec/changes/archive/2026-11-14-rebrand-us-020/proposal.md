# Propuesta: rebrand de Notas (US-020, US-021, US-022)

## Why

Paso 6 de `insumos/rebrand/PLAN.md`: `notas/hoja.html` pasa a `marco_rebrand.html` y `rebrand.css` con el boceto `insumos/rebrand/notas.html` (`capturas/notas-*`, `estado-notas-*`), según `insumos/rebrand-notas/decisiones.md`, y corrige los hallazgos de break-ui (`insumos/rebrand-notas/pendientes.md`). Cubre RF-020, RF-021 y RF-022, dimensión **registro y control de notas**; no guarda datos nuevos.

## What Changes

- Selector I–IV dentro de la hoja (cambiar de bimestre conserva los borradores sin preguntar), tira con Competencias fijo, columnas que se desplazan dentro de la hoja con el nombre fijo y la cabecera sincronizada, vista previa y recuadro de conclusión según el espacio, «Siguiente ↓» que no se detiene en una B/C sin conclusión, y romanos en todos los textos.
- **Fuera de alcance:** botón de tema → T-04; borrar el CSS de notas de `app.css` y retirar `nombre` («B3») del periodo → paso 8; auditoría visual (44 px, 64 px, textos de C-04) → al final del rebrand.

## Capabilities

### Modified Capabilities

- `registro-notas`: «Periodo de la hoja», «Sin periodo vigente», «Periodo sin competencias marcadas», «Áreas de la hoja», «Nivel en el celular», «Conclusión en B y C», «Rellenar vacías» (un solo botón en la tarjeta, decidido por Marco en el propose), «Salir sin guardar» y «Hoja accesible y sin desplazamiento horizontal de la página».

## Impact

`notas/hoja.html` (y parciales nuevos), nuevo `rebrand/pantallas/notas.css`; en `notas.js` clases y marcado (decisión 15) más las conductas de los deltas (design D1–D5); en `views.py` el contexto del selector y los romanos. Sin cambios en rutas, modelos, `servicios.py` ni reglas de guardado.
