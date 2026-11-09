# Tasks

## 1. Build de dos hojas (D1 a D3)

### Parte A: segunda entrada de Tailwind, vigilancia, tokens y fuente (alto riesgo)

- [ ] 1.1 Prueba primero, `scripts/tests/test_paquete_frontend.py`: `build` compila `css/app.css` → `dist/app.css` y `css/rebrand.css` → `dist/rebrand.css`, las dos con `--minify`; `dev` y `dev:contenedor` llaman a `scripts/vigilar.mjs` (el del contenedor con `--poll=1000`) y `vigilar.mjs` nombra las dos entradas; `copiar-vendor.mjs` copia Instrument Sans latina 400 y 500 (WOFF2) y su licencia como `fuentes/LICENSE-instrument-sans`, sin pisar la de Besley. Luego `npm install @fontsource/instrument-sans`, `package.json`, `vigilar.mjs` (D2) y `copiar-vendor.mjs`. Verificar: rojo y luego verde; `npm run build` deja las dos hojas en `dist/`; `npm run dev` en PowerShell y `docker compose up frontend` regeneran las dos al guardar cada entrada y Ctrl+C cierra los dos vigilantes
- [ ] 1.2 Prueba primero, `cuentas/tests/test_hoja_rebrand_e2e.py` (marca e2e: lee la hoja compilada): `rebrand.css` trae los tokens del Quick Start con sus valores claros, el bloque `html[data-theme=dark]`, el de `prefers-color-scheme: dark` con `:root:not([data-theme=light])` y las variables de celular dentro de `max-width:699px`; `@font-face` de Instrument Sans 400 y 500 en WOFF2 con `swap` y ninguna de Besley; ninguna transición de `width` ni `height`; ningún selector de la capa de utilidades repite una clase de la de componentes; `app.css` no trae `--g-main`. Luego `css/rebrand.css`, `rebrand/tokens.css` y `rebrand/base.css` (D1, D3), con Context7 para `@theme static`, `@theme inline` y `source(none)`. Verificar: rojo y luego verde; `uv run pytest -m e2e src/backend/cuentas/tests/test_hoja_rebrand_e2e.py --browser chromium`
- [ ] 1.3 Prueba primero, en el mismo archivo: en una página con `rebrand.css`, «0000» y «1111» en Instrument Sans 400 con `tabular-nums` miden lo mismo (decisión 4). Si falla, los WOFF2 salen de los TTF del prototipo (D3) y se ajusta 1.1. Verificar: rojo (con la fuente de respaldo) y luego verde
- [ ] 1.4 Revisión de la parte (agente `revisor`) y commit

## 2. Marco nuevo (D4 a D9)

### Parte B: íconos, ☰, cuenta, barra, pie y movimiento, sobre «sin permiso» (alto riesgo)

- [ ] 2.1 Prueba primero, `cuentas/tests/test_plantillas.py`: todos los íconos con `stroke-width="1.6"`; `menu` entre los de D9. Luego el trazo en `templates/iconos/` y `iconos/menu.svg` de Lucide. Verificar: rojo y luego verde; `uv run pytest src/backend/cuentas/tests/test_plantillas.py`
- [ ] 2.2 Prueba primero, `cuentas/tests/test_dimensiones.py` e `institucion/tests/test_servicios.py`: `navegacion_docente` da Inicio, Sesiones, Asistencia y Notas en ese orden; Sesiones sin `url`; Asistencia y Notas con la `url` de las tarjetas con sección única y sin `url` sin ella; `actual` en Inicio desde la portada, en Notas desde la hoja y Competencias, en Asistencia desde la asistencia de hoy, y en ninguno desde «sin permiso» (escenarios «Abrir el ☰», «Destino no disponible», «Ubicación actual»); `secciones_de_la_cuenta` con una sección, con dos (orden por grado y nombre), sin sección, con la única en un año CERRADO y para la dirección (escenarios «Docente con sección», «Docente sin sección», «Dirección»). Luego D6 y D7. Verificar: rojo y luego verde; `uv run pytest src/backend/cuentas src/backend/institucion`
- [ ] 2.3 Prueba primero, `cuentas/tests/test_marco_rebrand.py`: «sin permiso» de la docente carga solo `dist/rebrand.css` (sin `app.css` ni Besley) y precarga Instrument Sans; trae «Ir al contenido», el `<header>` con el ☰ como enlace a `/docente/` (`data-menu-navegacion`, nombre «Inicio»), «Sin permiso» como texto de la barra, la cuenta al final y sin «I.E. Virgen del Carmen» en la barra; el `<dialog>` del ☰ sin `open`, con `aria-labelledby`, «Cerrar navegación» (`data-cerrar`), sus destinos, «Próximamente» sin enlace y ningún `aria-current`; la cuenta con «Tu cuenta», nombre, I.E., la línea de secciones, `data-menu-cuenta`, `data-cuenta-panel`, `data-cuenta-nombre`, `data-salir`, `data-usuario` y CSRF; el pie con sus dos textos después de `</main>`; `test_sin_permiso.py` sigue en verde. `test_accesibilidad_e2e.py` y `test_cerrar_sesion_e2e.py` pasan a `data-cuenta-panel` y `data-cuenta-nombre`. Luego `base_rebrand.html`, `marco_rebrand.html`, `rb/menu_navegacion.html`, `rb/menu_cuenta.html`, `rb/pie.html`, `cuentas/templatetags/marco.py`, los dos ganchos en `componentes/menu_cuenta.html` y `sin_permiso.html` sobre el marco nuevo con su contenido actual (D4, D7, D8). Verificar: rojo y luego verde; `uv run pytest src/backend/cuentas`
- [ ] 2.4 Prueba primero, `cuentas/tests/test_marco_rebrand_e2e.py`, en «sin permiso»: «Barra de una pantalla interior» (72 px a 1280 y 64 px a 360; sigue visible al desplazar), «Pie» (bordes alineados con el contenido a 1280 y a 360, sin desplazamiento horizontal); de «Navegación de la docente»: «Abrir el ☰» (con JS el ☰ es un botón con `aria-expanded` y abre el diálogo modal sobre la barra), «Teclado» (Tab no sale del diálogo; Escape cierra y devuelve el foco), «Cerrar con el ✕», «Toque fuera del panel», «Sin JavaScript» (contexto sin JS: el ☰ es un enlace y lleva a la portada) y «☰ abierto a 320 px» en ambos temas; abrir el ☰ con la cuenta abierta la cierra; de «Menú de la cuenta»: «Abrir el menú», «Docente con sección», «Teclado», «Toque fuera del menú», «Sin JavaScript» y «Menú abierto a 320 px»; la portada sigue cargando solo `app.css` (D9). Luego `rebrand/marco.css` desde el CSS del prototipo y `static/js/marco.js` (D4, D5). Verificar: rojo y luego verde; `uv run pytest -m e2e src/backend/cuentas --browser chromium` con el CSS compilado y `DJANGO_ALLOW_ASYNC_UNSAFE=true`
- [ ] 2.5 Prueba primero, en el mismo archivo e2e: E-02 (foco con Tab sobre el ☰ y un botón: sin animaciones y `outline-offset` de 4 px de inmediato, también con movimiento reducido); E-03 (cerrar el ☰ con Escape a mitad de la entrada: el `transform` del panel justo después de pedir el cierre es el mismo que justo antes, sin salto; el diálogo sigue abierto hasta terminar la salida y luego se cierra con el foco en el ☰); E-05 (activar un botón con Enter o Espacio no le da `transform`; con el mouse sí); movimiento reducido (el ☰ abre y cierra sin `transform` y el cierre es inmediato). Luego los ajustes de `marco.css` y `marco.js`. Verificar: rojo y luego verde; e2e de `cuentas`
- [ ] 2.6 Revisión de la parte (agente `revisor`) y commit

## 3. Componentes y «sin permiso» (normal)

- [ ] 3.1 Prueba primero, `cuentas/tests/test_componentes_rb.py` (con `render_to_string`): `rb/boton.html` como enlace o botón, principal, secundario y de texto, con ícono opcional decorativo; `rb/campo.html` con etiqueta `for`/`id`, ayuda y error en `aria-describedby`, `aria-invalid` solo con error y sin `placeholder` como etiqueta; `rb/mensaje.html` de aviso, error y éxito con ícono `aria-hidden`, título y texto, y `role="alert"` solo si se pide. Luego los tres componentes y `rebrand/componentes.css` desde el prototipo (botón de 44 px, campo de 48 px; D8). Verificar: rojo y luego verde; `uv run pytest src/backend/cuentas/tests/test_componentes_rb.py`
- [ ] 3.2 Prueba primero, `cuentas/tests/test_sin_permiso.py`: el mensaje de error con `role="alert"`, el `<h1>` y el texto oficiales, y «Volver a tu inicio» como botón principal hacia `/docente/`. Luego `sin_permiso.html` con `rb/mensaje.html` y `rb/boton.html`, y `rebrand/pantallas/sin-permiso.css` desde el boceto (D8). Verificar: rojo y luego verde; `uv run pytest src/backend/cuentas`
- [ ] 3.3 Prueba primero, `cuentas/tests/test_accesibilidad_e2e.py`: `VISTAS` suma «sin-permiso-menu-abierto» y «sin-permiso-cuenta-abierta» (escenario «Revisión de cada pantalla»); `test_sin_permiso_no_desborda_y_su_boton_es_tactil` además pide el botón a todo el ancho a 360 px; el ☰, el ✕ y la cuenta miden 44 × 44 px. Luego los ajustes de CSS que falten. Verificar: e2e de `cuentas` en verde en claro y oscuro, a 360 y 1280 px
- [ ] 3.4 Pantalla vista en claro/oscuro y celular/escritorio (la marca Marco). `verificar.py` y commit

## 4. Cierre

### Parte C: auditoría de Emil y A2

- [ ] 4.1 Auditoría de Emil (solo `review-animations`, en solo lectura con Codex) sobre el movimiento del marco y «sin permiso» → `insumos/rebrand-base/auditoria-emil.md`. Marco aprueba los ids; cada uno se aplica con su prueba primero. Verificar: e2e de `cuentas` en verde
- [ ] 4.2 Con la A2 que corre el usuario (`/codex:adversarial-review --base main --background`, con foco en los specs del cambio, D2, D4 y D5), corregir los Critical e Important, con la prueba primero. Verificar: `uv run pytest --cov` (80 % o más), las e2e y `verificar.py --antes-del-commit` en verde
- [ ] 4.3 `verificacion.md`: tabla escenario → prueba de los dos specs del cambio (los de D10, «con su pantalla»), la prueba manual de `vigilar.mjs` y la DoD 1 a 9. Verificar: cada escenario tiene su prueba o su nota; commit

## Ajustes del propose a decisiones.md

- Decisión 2: además de los scripts de `package.json`, se agrega `src/frontend/scripts/vigilar.mjs` para correr los dos vigilantes en Windows (D2). Vercel, CI y el Dockerfile no cambian.
- Decisión 9: el `<summary>` de la cuenta conserva el nombre «Menú de la cuenta» (el boceto dice «Abrir tu cuenta»).
- Decisión 10 (cambiada por Marco en el propose): el ☰ deja `<details>` y pasa a `<dialog>` como el boceto, con el panel sobre la barra y su ✕ adentro; sin JavaScript el ☰ es un enlace a la portada (D4). Sus destinos siguen la regla de la portada.
- Decisión 8: en celular el pie conserva sus dos textos (el prototipo oculta el segundo).

## Workflow follow-up

- **(equipo)** Push de `feature/rebrand` con aprobación; el PR borrador único hacia `main` sigue sin fusionarse hasta después del 11-11-2026. En «## Deuda» de su descripción:
  - escenarios del «Marco común» y del «Menú de la cuenta» en la portada, el inicio de la dirección y las demás pantallas del marco viejo → con su pantalla del rebrand (D10);
  - botón de tema → T-04 y Sesiones disponible en el ☰ → US-011/012/016, en la rama apilada;
  - diálogo y estado vacío → la primera pantalla que los use; ingreso con Besley `optional` → paso 2 del PLAN; borrar el marco viejo y `app.css` → paso 8;
  - admin de Django (`panel.css`) → sin decidir (`insumos/rebrand-base/pendientes.md`);
  - filas de Estudiantes, «sin permiso» y Dirección en «Pantallas» de `DESIGN.md` → commit aparte (pendientes.md).
- Al proponer el siguiente cambio del rebrand (`rebrand-us-010`, Sesiones), su primer commit archiva este con `/opsx:archive` y «Sync now».
