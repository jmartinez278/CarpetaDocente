# Propuesta: rebrand del Ingreso (US-001)

## Why

Paso 2 de `insumos/rebrand/PLAN.md`: el inicio de sesión pasa a `base_rebrand.html` y `rebrand.css` con la propuesta D del boceto. Cubre RF-001 (transversal, usuarios y acceso: la puerta a las tres dimensiones), con RNF-002, RNF-005 y RNF-008; la conducta del ingreso no cambia.

## What Changes

Se aplica tal cual `insumos/rebrand-ingreso/decisiones.md`. Lo nuevo de este propose:

- **Foco sin doble anuncio:** el error general deja de llevar `role="alert"` y recibe el foco al cargar con `autofocus` y `tabindex="-1"` (el lector lo lee una vez, al enfocarlo). Funciona sin JavaScript y no toca `ingresar.js` (design D2).
- **«Ingresando…» sin tocar `ingresar.js`:** el fondo `--folder`, el indicador de giro y el borde punteado de los campos salen del CSS sobre lo que el JS ya pone (`aria-disabled` en el botón, `aria-busy` en el formulario, `readonly` en los campos). El giro es un pseudoelemento, porque el JS reescribe el texto del botón (design D4).
- **Componentes:** `rb/campo.html` suma `mostrar_clave` y `variante="ingreso"`; `rb/mensaje.html` suma `icono` (el reloj del aviso) y `enfocar`; `rb/pie.html` suma `solo_marca`. Sin parámetros, nada cambia (design D3).
- **Besley:** se precarga desde un bloque nuevo `precargas` de `base_rebrand.html`, que solo llena `ingresar.html` (design D5).

**Fuera de alcance** (en `insumos/rebrand-ingreso/pendientes.md`): el escudo (T-06), el botón de tema junto al pie (T-04, rama apilada) y retirar Besley del `app.css` viejo (paso 8 del PLAN).

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `pantallas-de-inicio`: «Pantalla de inicio de sesión» (el error recibe el foco y se anuncia una sola vez) y «Accesibilidad en ambos temas» (el inicio de sesión se revisa con el marco del rebrand en sus cinco estados, sumando «Ingresando…»).

## Impact

- **Plantillas:** `cuentas/ingresar.html` (extiende `base_rebrand.html`); `rb/campo.html`, `rb/mensaje.html`, `rb/pie.html` y `base_rebrand.html` con parámetros o bloques opcionales.
- **CSS:** nuevo `rebrand/pantallas/ingreso.css` (con el `@font-face` de Besley) y lo que el campo de contraseña y el pie necesitan en `rebrand/componentes.css` y `rebrand/marco.css`; `rebrand.css` suma el `@source` de `cuentas/ingresar.html` y el import.
- **JS:** `ingresar.js` sin cambios.
- **Pruebas:** `cuentas/tests/` (`test_pantallas.py`, `test_ingresar_e2e.py`, `test_accesibilidad_e2e.py`, `test_rendimiento_e2e.py`, `test_componentes_rb.py`): de clases viejas a ganchos o clases nuevas, y la prueba nueva del foco.
- **Sin cambios:** vista, ruta, formulario, servicios, modelos y migraciones; `docs/03` y el README.
- **Rama:** `feature/rebrand`, mismo PR borrador hacia `main`.
