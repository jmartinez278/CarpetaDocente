# Design: cierre del rebrand (inicio de la dirección y retiro de lo viejo)

## Context

- Decisiones cerradas en `insumos/rebrand-cierre/decisiones.md`. La dirección no tiene boceto: se arma con DESIGN.md y los componentes de `templates/rb/`.
- Hoy solo `direccion/inicio.html` extiende `marco.html` (viejo); `marco.html` es la única plantilla que incluye `componentes/menu_cuenta.html` y `componentes/pie.html`; `componentes/campo.html` ya no lo incluye nadie. Ninguna vista ni prueba de Python carga `base.html` o `marco.html` por nombre. Vercel y el Dockerfile corren `npm run build`, sin nombrar hojas.
- `static/dist/` no se versiona y `npm run build` no lo limpia.

## Riesgos y zonas delicadas (primero)

- **[Hoja vieja que queda en el disco]** Tras el retiro, `static/dist/app.css` (la vieja) sigue en cada máquina hasta el siguiente build, y una prueba que la lea pasaría en falso → D2.
- **[Mismo nombre, otro archivo]** `base.html`, `marco.html` y `app.css` desaparecen en el commit B y vuelven en el C con otro contenido. Las pruebas que hoy dicen «`dist/app.css` no se carga» siguen ciertas en B y se invierten en C → D3.
- **[Build de despliegue]** `package.json` lo usan Vercel y el Dockerfile: las partes B y C son de alto riesgo y van con su commit; la vista previa del PR #73 confirma el build.

## Decisions

### D1. Inicio de la dirección con las clases de la portada

- `direccion/inicio.html` extiende `marco_rebrand.html` con `clase_barra` « appbar--portada», `navegacion` vacío y sin `titulo_barra`, igual que la portada; título «Inicio · CarpetaDocente».
- Encabezado con el marcado de la portada: `.bienvenida` y `<h1>` con `.saludo` («Hola,») y `.docente` (el nombre), y debajo `<p>` «Dirección». La sección «Consolidados» lleva un `<h2>` (que ya toma `--text-section` en `base.css`) y `rb/estado_vacio.html` con `inbox`. Sin hoja propia: si hace falta un ajuste, va en `portada.css` junto a `.bienvenida`; el `@source` de `direccion/inicio.html` entra en la hoja.
- Sin `portada.js` ni HTMX: solo los scripts del marco (cuenta, `bfcache.js`, `marco.js`).

### D2. El retiro limpia también la salida local

- La parte B borra a mano `src/backend/static/dist/app.css` antes de correr las pruebas, y la prueba del build pasa a exigir **una** salida. `vigilar.mjs` conserva su forma de lista con una sola entrada (se corrige su comentario de «dos entradas»); simplificarlo no entra en un commit de retiro.
- `test_app_css_no_trae_los_tokens_del_rebrand` (`test_hoja_rebrand_e2e.py`) se borra con su archivo: compara dos hojas que ya no conviven.

### D3. Nombres finales con `git mv`, en un commit sin otra cosa

- `git mv` de `base_rebrand.html`, `marco_rebrand.html` y `src/frontend/css/rebrand.css`, para que el historial los siga; luego solo cambian cadenas: `extends`, `@source`, `package.json`, `vigilar.mjs`, comentarios y pruebas. Las aserciones «carga `dist/rebrand.css` y no `dist/app.css`» pasan a «carga `dist/app.css` y no `dist/rebrand.css`».
- Los archivos de prueba con «rebrand» en el nombre (`test_marco_rebrand.py`, `test_marco_rebrand_e2e.py`, `test_hoja_rebrand_e2e.py`) conservan su nombre, como `templates/rb/` y `css/rebrand/`: renombrarlos no cambia ninguna referencia del producto.

### Datos de la tesis

Ninguno: no cambia qué se guarda.

## Migration Plan

Sin migraciones. Cada commit se revierte solo; tras revertir B o C hace falta `npm run build` para regenerar `static/dist/`.
