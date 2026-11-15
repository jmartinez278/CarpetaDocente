# Propuesta: rebrand de Estudiantes (US-006)

## Why

Primera mitad del paso 3 de `insumos/rebrand/PLAN.md`: Estudiantes pasa al marco del rebrand antes que la portada, para que la portada nueva solo cargue `rebrand.css`. Cubre RF-006 (módulo transversal de usuarios y acceso; la lista es la base del **control de asistencia** y del **registro y control de notas**), con RNF-002, RNF-005 y RNF-008; la conducta y los textos no cambian.

## What Changes

Se aplica tal cual `insumos/rebrand-estudiantes/decisiones.md` y los ids aprobados de `auditoria-emil.md` (E-02, E-03, E-05, E-06). Lo nuevo de este propose:

- **Ancho del diálogo:** variante `dialog--lista` de 760 px como máximo y alto fijo en la PC (las vistas no saltan al cambiar), hoja casi completa en el celular; los 480 px de Sesiones no alcanzan para nombres de 242 caracteres (design D3).
- **Del boceto no entran** el «Cerrar» repetido del pie de la lista con su rótulo «Estudiantes de 2.º A», el ícono `+` de «Agregar estudiante» (no está en `templates/iconos/`) ni el número por contador de CSS: se conserva el número del repo (design D2).
- **Dos parámetros más en componentes compartidos**, además de E-05 y E-06: `rb/campo.html` acepta `descrito_por` (la ayuda común de Agregar, `ayuda-nombres`) y `foco` (el `data-foco` que usa `estudiantes.js`); `rb/mensaje.html` acepta `estado` (`role="status"`, que hoy llevan el aviso de la portada, Vaciar y «ya tiene estudiantes») (design D5, D6).
- **`estudiantes.js` cambia un selector:** `.modal-cuerpo` → `#modal-cuerpo` (el `id` se conserva; la clase se va). Es la única línea del JS que dependía de una clase (design D4).
- **Las e2e del diálogo que miden su aspecto** (Cerrar de 44 px, nombre largo, axe dentro del diálogo) se pasan a página completa o se saltan con motivo «rebrand-portada»: hasta que migre la portada, el diálogo vive en una página con `app.css` y sus vistas no tienen estilo. Las e2e de conducta del diálogo siguen corriendo (design D8).

**Fuera de alcance:** la portada, el `<dialog id="estudiantes">` que la envuelve y sus e2e del diálogo → `rebrand-portada` (sigue sin push entre los dos). E-07, máximo de estudiantes por sección → pregunta al equipo, cambio de spec propio. Pasar `_subir_pie.html` de Sesiones a `rb/boton.html formulario=` y borrar el CSS viejo de Estudiantes de `app.css` → paso 8 del PLAN.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `estudiantes-seccion`: «Diálogo accesible y sin desplazamiento horizontal» se revisa con la página completa en el marco del rebrand (barra con ☰ y «Estudiantes»), y el nombre largo también con el texto al 200 %.

## Impact

- **Plantillas:** `institucion/estudiantes/` completo (`pagina.html` extiende `marco_rebrand.html`; `_base.html` con la estructura de `rb/dialogo.html`; vistas y `_aviso_portada.html` con `rb/`); `_campo_estudiante.html` se borra (lo reemplaza `rb/campo.html`). `rb/boton.html`, `rb/campo.html`, `rb/mensaje.html` y `base_rebrand.html` (viewport) cambian.
- **CSS:** `rebrand/componentes.css` (`.dialog` a `dvh`, `.dialog--lista`, panel de página) y nuevo `rebrand/pantallas/estudiantes.css`; `rebrand.css` suma su `@import` y el `@source` de `templates/institucion/estudiantes`.
- **JS:** `estudiantes.js`, un selector.
- **Pruebas:** `institucion/tests/test_vistas_estudiantes.py` y `test_estudiantes_e2e.py`; `cuentas/tests/test_componentes_rb.py`, `test_marco_rebrand.py` y `test_hoja_rebrand_e2e.py`.
- **Sin cambios:** vistas, rutas, formularios, servicios, modelos y migraciones; `docs/03` y el README.
- **Rama:** `feature/rebrand`, mismo PR borrador hacia `main`; sin push hasta cerrar `rebrand-portada`.
