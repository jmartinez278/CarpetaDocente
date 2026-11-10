# Propuesta: rebrand de la Portada del docente

## Why

Segunda mitad del paso 3 de `insumos/rebrand/PLAN.md`: la portada pasa a `marco_rebrand.html` y solo carga `rebrand.css`, con lo que el diálogo de Estudiantes migrado en `rebrand-us-006` recupera su estilo y se puede hacer push de los dos. Cubre RF-001 (transversal, usuarios y acceso: la entrada a las tres dimensiones de la tesis, **planificación de sesiones de aprendizaje**, **registro y control de notas** y **control de asistencia**), con RNF-002, RNF-005 y RNF-008.

## What Changes

Se aplica tal cual `insumos/rebrand-portada/decisiones.md`. Lo nuevo de este propose:

- **Sin Alpine en la portada:** con el carrusel fuera, Alpine solo quedaba para el aviso de «Próximamente»; `portada.js` pasa a JavaScript sin dependencias con un `data-proxima` en la tarjeta, y la portada deja de cargar `alpine.min.js` (design D5). La conducta del aviso no cambia.
- **Orden y frases en `dimensiones.py`:** la tupla `DIMENSIONES` pasa a Asistencia, Sesiones y Notas, y el campo `subtitulo` se cambia por `frase`. Las banderas, `para_portada` y la navegación del ☰ (que tiene su propio orden) no cambian; `tarjeta_inicial` y el contexto `inicial` de la vista se borran con el carrusel (design D2).
- **Se conservan los verbos de la spec** («Registrar asistencia», «Ver sesiones», «Registrar notas») en `acc-<clave>`, no los del boceto («Tomar asistencia», «Abrir…»): decisiones.md no cambia textos de conducta (design D3).
- **Tarjeta y miniaturas a `templates/rb/`:** `rb/tarjeta_dimension.html` y `rb/miniatura_<clave>.html` con las miniaturas del boceto; se borran las de `templates/componentes/` que solo usaba la portada (design D3, D4).
- **Barra de la portada no fija:** variante de `marco_rebrand.html` con el bloque `navegacion` vacío y la barra sin `position: sticky` (DESIGN.md, Layout «Portada») (design D1).
- **«Hoy: pendiente» sin animación de entrada:** la subida al cargar de US-030 no responde a una acción y DESIGN.md 1.1 (Movimiento) no la admite (design D7).
- **Diálogo de Estudiantes:** el `<dialog id="estudiantes">` recibe `dialog dialog--lista`; vuelven las e2e saltadas con motivo `rebrand-portada` y entra la del A2 [high] de `rebrand-us-006` (lista que supera el alto del diálogo) (design D6).

**Fuera de alcance:** el botón de tema → T-04 (rama apilada); el inicio de la dirección → paso 7 del PLAN; borrar `app.css`, `marco.html`, Alpine del vendor y los componentes viejos que aún usan otras pantallas → paso 8; la actualización de RNF-005 para Notas → `rebrand-notas`. Activar Sesiones → rama apilada (US-011/012/016).

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `pantallas-de-inicio`: «Portada del docente» (orden Asistencia, Sesiones y Notas; frase en lugar del subtítulo formal), «Carrusel de dimensiones en el celular» se retira, «Sin desplazamiento horizontal» pierde la excepción del carrusel y «Accesibilidad en ambos temas» revisa la portada con el marco del rebrand y el diálogo de Estudiantes abierto.

## Impact

- **Plantillas:** `cuentas/portada_docente.html` extiende `marco_rebrand.html`; nuevas `rb/tarjeta_dimension.html` y `rb/miniatura_{asistencia,sesiones,notas}.html`; se borran `componentes/tarjeta_dimension.html` y `componentes/miniatura_*.html`.
- **CSS:** nuevo `rebrand/pantallas/portada.css`; `rebrand.css` suma su `@import` y el `@source` de `cuentas/portada_docente.html`; `marco.css`, la variante de barra no fija.
- **JS:** `portada.js` reescrito sin Alpine (solo «Próximamente»); `estudiantes.js` no cambia.
- **Python:** `cuentas/dimensiones.py` (orden, `frase`, sin `tarjeta_inicial`) y `PortadaDocenteView` (sin `inicial`).
- **Pruebas:** `cuentas/tests/test_dimensiones.py`, `test_pantallas.py`, `test_portada_e2e.py`, `test_accesibilidad_e2e.py`, `test_marco_rebrand.py`; `institucion/tests/test_estudiantes_e2e.py`.
- **Sin cambios:** rutas, servicios, modelos y migraciones; `docs/03` y el README.
- **Rama:** `feature/rebrand`, mismo PR borrador hacia `main`; push al cerrar este cambio, con aprobación.
