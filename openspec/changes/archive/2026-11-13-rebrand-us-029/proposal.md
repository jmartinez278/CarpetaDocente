# Propuesta: rebrand de Competencias (US-029)

## Why

Paso 5 de `insumos/rebrand/PLAN.md`: `notas/competencias.html` pasa a `marco_rebrand.html` y `rebrand.css` con el boceto `insumos/rebrand/competencias.html` y sus estados (`capturas/competencias-*`, `estado-competencias-*`), según `insumos/rebrand-competencias/decisiones.md`. Cubre RF-029, dimensión **registro y control de notas**; no guarda datos nuevos.

## What Changes

- Encabezado, selector I–IV, lista por área, una sola tarjeta café «Tu selección» (barra fija abajo hasta 899 px), «¿Salir sin guardar?» sobre `rb/dialogo.html` y estados sin boceto con `rb/`; nombres en romanos y fechas solo en el nombre accesible (design D1–D5).
- Lo nuevo de este propose: los romanos salen de dos propiedades del periodo, sin tocar el «B*n*» de la hoja de notas hasta el paso 6 (D1); «Registrar notas del IV bimestre» también se ve en el celular, al pie de la lista (D4).
- **Fuera de alcance:** la hoja de notas y sus nombres → paso 6; botón de tema → T-04; borrar el CSS de competencias de `app.css` y los parciales viejos → paso 8; auditoría visual → al final del rebrand.

## Capabilities

### Modified Capabilities

- `competencias-periodo`: «Periodos que se marcan», «Marcado en el celular y en la PC», «Competencias obligatorias en el último periodo», «Competencias accesibles y sin desplazamiento horizontal» e «Ir a las notas del periodo».

## Impact

Plantillas `notas/competencias.html`, `_area.html`, `_panel.html`, `_periodos.html` y `rb/dialogo.html`; nuevo `rebrand/pantallas/competencias.css`; en `competencias.js` solo clases, textos y fragmentos de marcado (D3); dos propiedades de solo lectura en `PeriodoDeLaSeccion` y su paso al contexto; pruebas de `notas`. Sin cambios en rutas, modelos ni reglas de guardado.
