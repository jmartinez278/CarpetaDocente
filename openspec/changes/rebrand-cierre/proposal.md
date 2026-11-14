# Propuesta: cierre del rebrand (inicio de la dirección y retiro de lo viejo)

## Why

Pasos 7 y 8 de `insumos/rebrand/PLAN.md`, según `insumos/rebrand-cierre/decisiones.md`: el inicio de la dirección es la última pantalla en el marco viejo; sin ella, `base.html`, `marco.html`, `componentes/` y el `app.css` viejo se pueden borrar y el rebrand queda con una sola hoja y nombres finales. Cubre RF-001 (transversal, usuarios y acceso; sin dimensión propia de la tesis) con RNF-005 y RNF-008; no guarda datos nuevos.

## What Changes

- `direccion/inicio.html` pasa a `marco_rebrand.html` en la variante de portada, **solo con DESIGN.md** (sin boceto; `pantallas-nuevas/direccion.html` no es referencia). Delta de «Accesibilidad en ambos temas»: la dirección se revisa con el marco del rebrand.
- Tres commits, en este orden: dirección → retiro de lo viejo (y el botón del pie de Sesiones a `rb/boton.html`) → nombres finales (`base.html`, `marco.html`, `app.css`), solo nombres y referencias.
- **Fuera de alcance:** diseño real de la dirección y sus consolidados → US-040; panel de administración y `panel.css` → fuera del rebrand; botón de tema → T-04; auditoría visual única → después de este cambio, antes de fusionar #73.

## Capabilities

### Modified Capabilities

- `pantallas-de-inicio`: «Accesibilidad en ambos temas» (la dirección, con el marco del rebrand).

## Impact

`templates/direccion/inicio.html`, `repositorio/_subir_pie.html`; se borran `base.html`, `marco.html`, `componentes/` y `src/frontend/css/app.css`; se renombran `base_rebrand.html`, `marco_rebrand.html` y `rebrand.css`. `package.json`, `vigilar.mjs` y las pruebas que nombran hojas o marcos (lista en decisiones.md). Sin cambios en rutas, vistas, modelos ni `servicios.py`.
