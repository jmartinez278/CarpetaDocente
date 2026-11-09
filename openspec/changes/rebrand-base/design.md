# Design: rebrand de la base (marco común y «sin permiso»)

## Context

- Decisiones cerradas en `insumos/rebrand-base/decisiones.md` (1 a 13); plan en `insumos/rebrand/PLAN.md`; norma en `DESIGN.md` 1.1 de la raíz. Lo nuevo de este propose está en `proposal.md`.
- Hoy hay una sola hoja: `src/frontend/css/app.css` (Tailwind v4, `@source` sobre todas las plantillas, tokens 0.3.1 en `@theme`, ~5000 líneas) → `static/dist/app.css`. `package.json` la compila en `build`, `dev` y `dev:contenedor`; Vercel (`scripts/build_vercel.py`) y CI corren `npm run build`; el contenedor `frontend` corre `npm run dev:contenedor` en Linux; el Dockerfile no compila CSS. `copiar-vendor.mjs` copia HTMX, Alpine y Besley (con su licencia como `fuentes/LICENSE`).
- Marco actual: `base.html` (precarga Besley, carga `app.css`) y `marco.html` (barra con el nombre de la I.E. y `componentes/menu_cuenta.html`, pie, `bfcache.js`). El menú de la cuenta es `<details data-menu-cuenta>` con `menu.js` (Escape, toque fuera, borrado de borradores al salir) y `notas-borrador.js`.
- «Sin permiso» (`cuentas/sin_permiso.html`, `SinPermisoView`, `acceso.sin_permiso`) es solo de la docente: la dirección y el Administrador van a su inicio. Sus pruebas buscan por texto, rol y `href` (`test_sin_permiso.py`, `test_accesibilidad_e2e.py`).
- Disponibilidad de las dimensiones: `cuentas/dimensiones.py` (`DIMENSIONES`, `para_portada`) con `institucion.servicios.seccion_unica`. Secciones de la docente: `secciones_docente` y `texto_seccion`.
- Íconos: Lucide en `templates/iconos/` con `stroke-width="1.75"`; `test_plantillas.py` fija el trazo, la lista de D9, la licencia ISC y que ninguna plantilla (`**/templates/**/*.html`, `rb/` incluida) tenga hex ni `style=`.
- Pruebas que buscan clases del menú: `test_accesibilidad_e2e.py` (`.menu-cuenta__panel`) y `test_cerrar_sesion_e2e.py` (`.menu-cuenta__nombre`).
- Prototipo: `insumos/rebrand/assets/app.css` (barra `.appbar`, `.btn`, `.account`, `.drawer`, `.footer`) y `insumos/rebrand/pantallas-nuevas/assets/app.css` (`.message`, `.field`, `.permission`, pulsación con `[data-pointer]`). Su `motion/motion.css` es la fuente de E-02 y E-05; el ☰ del prototipo es un `<dialog>` con animaciones de fotogramas (fuente de E-03).

## Riesgos y zonas delicadas (primero)

- **[Dos vigilantes en Windows]** → D2: `cmd` no corre dos `tailwindcss --watch` a la vez con `&`; un script de Node arranca los dos y los cierra juntos. Se prueba a mano en PowerShell y en el contenedor.
- **[Choque de clases del prototipo con utilidades de Tailwind]** → D1: si una clase copiada se llama como una utilidad (`sr-only`, `hidden`, `container`…), la capa de utilidades gana. `rebrand.css` escanea solo las plantillas del marco nuevo y una prueba falla si un selector de utilidad repite una clase de componente.
- **[Tokens que no cambian con el tema]** → D3: las variantes oscuras y de celular no caben dentro de `@theme`; van en una capa posterior. Una prueba lee la hoja compilada y comprueba los tres bloques.
- **[Cifras tabulares]** → D3: si el WOFF2 de Fontsource perdió `tnum`, las cifras de Notas y Asistencia bailan. Una prueba e2e lo mide; si falla, se generan los WOFF2 desde los TTF del prototipo.
- **[☰ sin JavaScript]** (decisión 10, cambiada por Marco en el propose) → D4: un `<dialog>` modal solo abre con JS. Sin JS el ☰ es un enlace a la portada, cuyas tarjetas llevan a cada dimensión; `marco.js` lo cambia por el botón que abre el diálogo.
- **[Foco con el diálogo modal]** → D4: `showModal()` vuelve inerte el resto de la página; el retorno del foco al ☰ lo hace `marco.js` en el evento `close`, también cuando el cierre viene de Escape o del velo.
- **[Salto al cerrar a medio abrir]** (E-03) → D5: transiciones de CSS en lugar de animaciones de fotogramas; una transición interrumpida vuelve desde su valor actual. `close()` se llama recién al terminar la salida, para que el panel no deje la capa superior de golpe.
- **[Marco viejo y nuevo a la vez]** → D9: cada página carga una sola hoja; las pantallas del marco viejo no cambian, salvo los ganchos `data-*` de su menú de la cuenta.
- **[Escenarios de pantallas que aún no migran]** → D10: la portada y el inicio de la dirección siguen en el marco viejo; sus escenarios nuevos se prueban con su pantalla del rebrand.

## Goals / Non-Goals

**Goals:**
- Que cada pantalla del rebrand solo tenga que heredar `marco_rebrand.html`, usar `rb/` y sumar su CSS a `rebrand.css`.
- Ningún cambio de conducta en el marco viejo ni en `menu.js`, `notas-borrador.js` y `bfcache.js`.

**Non-Goals:**
- Reescribir el CSS del prototipo con utilidades (PLAN, «Camino»).
- Medir otra vez RNF-002: el ingreso no cambia en este cambio.

## Decisions

### D1. Segunda hoja: `src/frontend/css/rebrand.css`

- `@import "tailwindcss" source(none);` y `@source` explícito sobre `templates/base_rebrand.html`, `templates/marco_rebrand.html`, `templates/rb/` y cada plantilla migrada (hoy `templates/cuentas/sin_permiso.html`). Cada pantalla del rebrand agrega su línea. Además, `@source "./rebrand"` sobre la carpeta de los parciales: con `--poll` (contenedor) la CLI solo ve cambios en sus `@source` y en la entrada, no en los archivos importados (ajuste del apply; la hoja compilada no cambia con esa línea). Por qué: el CSS del prototipo se copia como componentes, casi no se usan utilidades, y escanear todo traería las utilidades de las pantallas viejas y más choques posibles.
- Partes en archivos importados desde `rebrand.css`: `rebrand/tokens.css`, `rebrand/base.css` (reinicio y foco), `rebrand/marco.css` (barra, ☰, cuenta, pie, enlace «Ir al contenido»), `rebrand/componentes.css` (botón, campo, mensaje) y `rebrand/pantallas/sin-permiso.css`. El CSS copiado va en `@layer components`.
- Es el único archivo del marco nuevo con hex (tokens). El `::backdrop` del ☰ conserva los dos valores del prototipo (`rgb(48 39 31 / .4)` y `rgb(0 0 0 / .55)` en oscuro).
- Alternativa descartada: un prefijo de Tailwind (`prefix(tw)`) evitaría los choques, pero también prefija las variables del `@theme` y rompería los `var(--ink)` del CSS copiado (decisión 3).

### D2. Build y vigilancia

- `build`: `copiar-vendor`, luego `tailwindcss` de `app.css` y de `rebrand.css`, las dos con `--minify`, en serie con `&&`.
- `dev` y `dev:contenedor`: `copiar-vendor` y `node scripts/vigilar.mjs` (`--poll=1000` en el contenedor). `vigilar.mjs` arranca un `tailwindcss --watch=always` por entrada con `spawn`, con el mismo Node (`process.execPath`) y la ruta del `bin` de `@tailwindcss/cli`, sin `shell`, para que `kill()` llegue al vigilante y no a un `cmd` (ajuste del apply); reenvía la salida con el nombre de la hoja y, si uno termina o llega Ctrl+C, cierra el otro. Por qué: sin dependencia nueva y en el mismo estilo que `copiar-vendor.mjs`; `concurrently` o `npm-run-all2` sumarían un paquete solo para esto.
- Vercel, CI, el Dockerfile y `build_vercel.py` no cambian (corren `npm run build`).

### D3. Tokens y fuentes

- `rebrand/tokens.css`: el bloque `:root` del Quick Start, con sus nombres (`--ink`, `--g-main`…), va en `@theme static` para que se emita entero; los alias que necesiten utilidades van en `@theme inline` con prefijo `--color-*` (`--color-ink: var(--ink)`…). Los bloques oscuros (`html[data-theme=dark]` y `@media (prefers-color-scheme: dark) { :root:not([data-theme=light]) }`) y el de celular (`@media (max-width:699px)`) van tal cual en `@layer base`, que va después de `theme` y les gana. Los cortes 700/900/960/1100 se escriben a mano en cada `@media`; no se definen `--breakpoint-*`. Antes de escribirlo, Context7 para `@theme static`, `@theme inline` y `source(none)` de Tailwind v4.
- Instrument Sans 400 y 500 de `@fontsource/instrument-sans` (`files/instrument-sans-latin-400-normal.woff2` y `-500-`), copiadas por `copiar-vendor.mjs` a `dist/fuentes/` con su licencia como `fuentes/LICENSE-instrument-sans` (la de Besley sigue en `fuentes/LICENSE`). `@font-face` con `font-display: swap`; `base_rebrand.html` precarga las dos. Sin Besley: ni `@font-face` en `rebrand.css` ni precarga en `base_rebrand.html`.
- Cifras tabulares: una prueba e2e compara el ancho de «0000» y «1111» con `tabular-nums`; si difieren, los WOFF2 salen de los TTF del prototipo con subconjunto latino (`pyftsubset`, una sola vez) y se versionan en `src/frontend/fuentes/`, y `copiar-vendor.mjs` los copia desde ahí.
- `font-synthesis: none`, controles con `font: inherit` y `--touch-min` en `min-width` y `min-height` (Quick Start, último párrafo).

### D4. ☰: enlace sin JS, `<dialog>` con JS (`rb/menu_navegacion.html`)

- **Sin JS:** el ☰ es `<a href="{% url 'docente:portada' %}" data-menu-navegacion>` de 44 × 44 px con el ícono `menu` y nombre accesible «Inicio» (lleva ahí; un enlace llamado «Menú de navegación» anunciaría algo que no hace). El `<dialog>` va en el HTML pero sin JS nunca se abre.
- **Con JS:** `marco.js` cambia el enlace por un `<button type="button" data-menu-navegacion>` con el mismo ícono, nombre «Menú de navegación», `aria-haspopup="dialog"`, `aria-controls` y `aria-expanded`. Al tocarlo, cierra el menú de la cuenta si está abierto y llama a `showModal()`.
- **Panel:** `<dialog class="drawer drawer-nav" id="navegacion" aria-labelledby="navegacion-titulo">` como el boceto: cabecera con «CarpetaDocente» (`id="navegacion-titulo"`) y el botón ✕ (`x`, 44 × 44 px, `aria-label="Cerrar navegación"`, `data-cerrar`), y `<nav aria-label="Navegación principal">` con la lista de D6. Fijo a la izquierda desde arriba hasta abajo, cubre la barra; 320 px de ancho como máximo (`calc(100vw - 32px)` en celular), radio solo en el borde derecho. `html:has(dialog[open])` sin desplazamiento, como el prototipo. El bloque del boceto con el nombre, la I.E. y la sección no se copia: lo muestra la cuenta (D7).
- **Cierre:** el ✕, Escape (`cancel` con `preventDefault`) y el toque en el velo (clic fuera del rectángulo del diálogo) usan el cierre de D5; en `close`, `aria-expanded="false"` y el foco vuelve al ☰.
- **Foco:** al abrir, el foco va al ✕ (primer control, como `showModal()` por defecto); el resto de la página queda inerte.
- La cuenta sigue con `<details>` (D7); queda inerte mientras el diálogo está abierto.
- Solo en interiores de la docente: `marco_rebrand.html` lo pone en `{% block navegacion %}`; la portada del docente y el inicio de la dirección lo dejarán vacío al migrar.

### D5. Movimiento (E-02, E-03, E-05 y las 4 reglas)

- **E-03, ☰ interrumpible:** el panel y su `::backdrop` se mueven con `transition` de `transform` y `opacity` (240 ms al entrar, 200 ms al salir, `--m-ease`), no con los `@keyframes` del prototipo (`t-slide-in`, `t-slide-out`). La entrada usa `@starting-style` sobre `dialog[open]` (`translateX(-100%)`, opacidad 0,6). Para salir, `static/js/marco.js` marca `data-cerrando` (el panel vuelve a `translateX(-100%)` desde donde esté, también a mitad de la entrada) y llama a `close()` al terminar la transición (`transitionend`, o a los 260 ms si no llega); un segundo pedido de cierre durante la salida no hace nada. El ✕, Escape y el toque en el velo usan este mismo cierre.
- **E-02, foco sin animación:** no se copia `m-focus` ni se transiciona `outline` ni `outline-offset`; el anillo (2 px, separación 4 px, `--focus-ring`) aparece de una vez, también con movimiento reducido.
- **E-05, pulsación solo con puntero fino:** `marco.js` marca `data-pointer` en el control con `pointerdown` de tipo `mouse` y lo quita con cualquier `keydown` (como `common.js` del boceto). La subida de 1 px y la escala 0,985 viven solo en `@media (hover:hover) and (pointer:fine)` y la pulsación exige `[data-pointer]`.
- **Movimiento reducido:** sin `transform` en el ☰ ni en los botones; el diálogo abre y cierra sin desplazarse (`close()` de inmediato); quedan cambios de color y opacidad de hasta 200 ms.
- Ninguna transición de `width` ni `height` (regla 4); una prueba lo comprueba en la hoja compilada.

### D6. Destinos del ☰ (`cuentas/dimensiones.py`)

- `navegacion_docente(seccion, vista_actual)` devuelve Inicio y las tres dimensiones en el orden del ☰ (Inicio, Sesiones, Asistencia, Notas), cada una con `titulo`, `icono`, `url` (o `None` = «Próximamente») y `actual`. Reusa `para_portada`, así que el ☰ y las tarjetas no pueden divergir. Inicio enlaza siempre a `docente:portada`.
- `actual` compara el espacio de nombres de la vista (`request.resolver_match`): `docente:portada` → Inicio, `asistencia` → Asistencia, `notas` → Notas (la hoja y Competencias), `repositorio` → Sesiones (solo un destino disponible puede ser el actual). «Sin permiso» y Estudiantes no marcan ninguno. El enlace actual lleva `aria-current="page"` y se distingue con fondo `--folder`, color y peso, no solo con color.
- Lo llama la etiqueta `{% menu_docente %}` de `cuentas/templatetags/marco.py` (`takes_context`, con `user` y `request`); la etiqueta no decide nada, solo pinta.

### D7. Panel de la cuenta (`rb/menu_cuenta.html`)

- Orden: «Tu cuenta», nombre (`get_full_name` o usuario), «I.E. Virgen del Carmen», línea de secciones (solo docente con secciones en el año ABIERTO) y el formulario «Cerrar sesión» al final. El nombre de la I.E. va escrito en la plantilla, como hoy en la barra.
- La línea sale de `institucion.servicios.secciones_de_la_cuenta(usuario)`: el mismo texto que `texto_secciones_docente` o `None` si no hay secciones o el usuario no es docente (sin el «Tu sección aparecerá…» de la portada).
- Se conservan `<details data-menu-cuenta>`, el `<summary aria-label="Menú de la cuenta">` (el boceto dice «Abrir tu cuenta», pero las pruebas buscan por ese nombre), `data-salir`, `data-usuario`, el CSRF, `menu.js` y `notas-borrador.js`. Ganchos nuevos para las pruebas: `data-cuenta-panel` y `data-cuenta-nombre`, también en `componentes/menu_cuenta.html` del marco viejo (sin otro cambio ahí).
- Lo pinta la etiqueta `{% menu_cuenta %}` de `cuentas/templatetags/marco.py`.

### D8. Plantillas y componentes

- `base_rebrand.html`: `lang="es-PE"`, `color-scheme`, precarga de Instrument Sans, `dist/rebrand.css` como única hoja, `{% block scripts %}`.
- `marco_rebrand.html`: enlace «Ir al contenido», `<header>` fijo (72/64 px) con `{% block navegacion %}`, `{% block titulo_barra %}` (texto de la barra, no encabezado: el `<h1>` es de cada pantalla), el lugar vacío del tema (T-04) y la cuenta; `<main id="contenido">`; `rb/pie.html`; `bfcache.js` y `marco.js`.
- `rb/pie.html`: «CarpetaDocente · 2026» e «I.E. Virgen del Carmen» con `justify-content: space-between` dentro de `.wrap`; en celular los dos siguen visibles (el prototipo oculta el segundo; manda decisiones.md, punto 8) y pasan a dos líneas si no caben.
- `rb/boton.html`, `rb/campo.html` y `rb/mensaje.html` (decisión 11), con las clases del prototipo (`.btn`, `.btn--primary`, `.btn--secondary`, `.btn--text`, `.field`, `.message`). El campo asocia etiqueta (`for`), ayuda y error (`aria-describedby`, `aria-invalid`). El mensaje recibe el tipo (aviso, error, éxito), el ícono decorativo de 18 px y, si se pide, `role="alert"`.
- «Sin permiso»: el contenido del boceto (`.permission`, mensaje de error con `role="alert"`, `<h1>` y botón principal «Volver a tu inicio» a ancho completo en celular) dentro de `marco_rebrand.html`, con «Sin permiso» en la barra. Textos sin cambio.
- Íconos: `stroke-width="1.6"` en todos los SVG de `templates/iconos/`; `menu.svg` de Lucide.

### D9. Convivencia

`base.html`, `marco.html`, `componentes/` y `app.css` siguen para las pantallas no migradas. Una página carga `app.css` o `rebrand.css`, nunca las dos; una prueba e2e lo comprueba en «sin permiso» y en la portada.

### D10. Escenarios que se prueban con su pantalla

«Barra y pie», el «Pie» y el «Menú de la cuenta» nuevo en esas dos pantallas (y en Asistencia, Notas, Competencias y Estudiantes) se prueban cuando cada una migra; aquí se prueban en «sin permiso». Hasta entonces, las pruebas del marco viejo (`test_pantallas.py`, barra con el nombre de la I.E.) siguen en verde y se reemplazan en el cambio de esa pantalla. `verificacion.md` los anota como «con su pantalla».

### Datos de la tesis

Ninguno: este cambio no guarda datos.

## Risks / Trade-offs

- [`@starting-style` en navegadores viejos] → sin él, el panel aparece sin animación; la conducta no cambia. RNF-005 pide las dos últimas versiones, que lo soportan.
- [Escape que no se deja cancelar] → Chrome no deja cancelar un segundo Escape seguido sin otra interacción; ahí el diálogo se cierra sin la salida animada. El foco vuelve igual al ☰ (evento `close`).
- [JS que falla tras cargar] → si `marco.js` no corre, el ☰ queda como enlace a la portada: se pierde el atajo, no el camino.
- [Dos consultas más por pantalla interior] (sección única y secciones de la cuenta) → son pequeñas y por índice; no se cachean.
- [Ruta de cada pantalla migrada en `@source`] → si una pantalla olvida su línea, sus utilidades no salen; el marco nuevo casi no usa utilidades y la revisión visual lo detecta.
- [Las pantallas viejas siguen con la barra con la I.E.] → convivencia aceptada por el PLAN hasta el paso 8.

## Migration Plan

Sin migraciones de base de datos. En Vercel, el build ya corre `npm run build`, que ahora deja las dos hojas. Para volver atrás basta con revertir el commit: el marco viejo sigue completo.
