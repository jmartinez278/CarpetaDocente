# Propuesta: rebrand de Sesiones (US-010)

## Why

Paso 1 de `insumos/rebrand/PLAN.md`: Sesiones es la primera pantalla que migra al marco del rebrand (`marco_rebrand.html`, `rebrand.css`) y la primera que necesita el diálogo y el estado vacío del DESIGN.md 1.1. Cubre RF-010 y RF-014 (dimensión **planificación de sesiones de aprendizaje**), con RNF-002, RNF-005 y RNF-008; la conducta de envío no cambia.

## What Changes

Se aplica tal cual `insumos/rebrand-sesiones/decisiones.md`. Lo nuevo de este propose:

- **Del boceto no entran el ✕ de los diálogos ni sus textos distintos de la spec** («Acepto y comparto», el último punto de los términos sin «eliminándola», «Subir» corto y el ícono `+` del botón). La spec dice que el popup se cierra con «Cancelar» o Esc, y decisiones.md conserva textos, conducta y orden de los botones (design D2).
- **El movimiento del diálogo es solo CSS** (transiciones con `@starting-style` y `allow-discrete`), para no tocar `sesiones.js`, que llama a `showModal()` y `close()` directo. La regla 1 (sin movimiento con el teclado) se resuelve con una marca general en `marco.js` (design D4).
- **Los campos se escriben a mano con las clases de `rb/campo.html`**: el componente solo pinta un `<input>` de un formulario de Django, y este formulario tiene archivo, selects y textarea (design D5).

**Fuera de alcance** (en `insumos/rebrand-sesiones/pendientes.md`): pestañas, búsqueda, filtros (C-01), tarjetas, `sesion.html`, E-06 y E-07, y encender «Sesiones» en el ☰ y en la portada → rama apilada (US-011/012/016). El estado y la fecha junto al encabezado de la sesión → con `sesion.html`. Borrar el CSS viejo de Sesiones de `app.css` → paso 8 del PLAN.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `envio-sesiones`: «Pantalla Sesiones» pierde el ícono y las franjas del tinte en la cabecera y gana la barra del marco del rebrand con «Sesiones»; «Pantalla accesible y sin desplazamiento horizontal» se revisa con ese marco, con el ☰ y la cuenta cerrados.

## Impact

- **Plantillas:** `repositorio/sesiones.html`, `_formulario.html`, `_terminos.html` y `_enviada.html` con el marcado del boceto y los ganchos actuales; nuevos `rb/dialogo.html` y `rb/estado_vacio.html`.
- **CSS:** `rebrand/componentes.css` (diálogo, estado vacío, barra de progreso) y `rebrand/pantallas/sesiones.css`; `rebrand.css` suma el `@source` de `templates/repositorio/`.
- **JS:** `marco.js` suma la marca de teclado para los diálogos; `sesiones.js` sin cambios.
- **Pruebas:** `repositorio/tests/` (plantillas, vistas y e2e pasan de clases viejas a ganchos o clases nuevas) y `cuentas/tests/test_componentes_rb.py`.
- **Sin cambios:** vistas, rutas, servicios, modelos y migraciones; `docs/03` y el README.
- **Rama:** `feature/rebrand`, mismo PR borrador hacia `main`.
