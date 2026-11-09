# Tasks

Ninguna parte es de alto riesgo: no toca modelos, permisos, transacciones, datos personales ni notas, y decisiones.md no marca zonas de cuidado. Cada componente nuevo va en su commit (decisiones.md, punto 5).

## 1. Diálogo (D3, D4)

### Parte A: `rb/dialogo.html` y su movimiento (normal)

- [x] 1.1 Prueba primero, `cuentas/tests/test_componentes_rb.py` (con `render_to_string`): `rb/dialogo.html` en variante hoja y chico pinta `<dialog>` con `aria-labelledby` hacia su `<h2 tabindex="-1">`, `aria-describedby` solo con descripción, cuerpo con `tabindex="0"`, `role="region"` y nombre, `data-cuerpo` solo si se pide, y el pie después del cuerpo; sin `open`, sin ✕, sin hex ni `style=`. `rb/boton.html` con `datos` pone el atributo `data-*` y sin él no cambia. Luego `rb/dialogo.html` y el parámetro de `rb/boton.html` (D1, D3). Verificar: rojo y luego verde; `uv run pytest src/backend/cuentas/tests/test_componentes_rb.py`
- [x] 1.2 Prueba primero, `cuentas/tests/test_hoja_rebrand_e2e.py` (lee la hoja compilada): `.dialog` transiciona solo `transform`, `opacity`, `display` y `overlay`, con `@starting-style`; `html[data-teclado] .dialog` y su `::backdrop` sin transición; dentro de `prefers-reduced-motion: reduce`, `.dialog` sin `transform`; sigue sin transiciones de `width` ni `height`. Luego `.dialog`, `.dialog--hoja` y `.dialog--chico` en `rebrand/componentes.css` desde el `dialog` del prototipo (D3, D4). Verificar: rojo y luego verde; `uv run pytest -m e2e src/backend/cuentas/tests/test_hoja_rebrand_e2e.py --browser chromium` con el CSS compilado
- [x] 1.3 Prueba primero, `cuentas/tests/test_marco_rebrand_e2e.py` en «sin permiso»: un `keydown` pone `data-teclado` en `<html>` y un `pointerdown` lo quita; la marca `data-pointer` (E-05) y el ☰ siguen como antes. Luego `marco.js` (D4). Verificar: rojo y luego verde; e2e de `cuentas`
- [x] 1.4 `verificar.py` y commit

## 2. Estado vacío (D6)

### Parte B: `rb/estado_vacio.html` (normal)

- [x] 2.1 Prueba primero, `cuentas/tests/test_componentes_rb.py`: `rb/estado_vacio.html` con ícono `aria-hidden`, el texto, y la acción solo si se pasa (enlace o botón por `rb/boton.html`). Luego el componente y `.empty` en `rebrand/componentes.css`. Verificar: rojo y luego verde; `uv run pytest src/backend/cuentas/tests/test_componentes_rb.py`
- [x] 2.2 `verificar.py` y commit

## 3. Pantalla Sesiones (D1, D2, D5, D7)

### Parte C: Sesiones en el marco del rebrand (normal)

- [x] 3.1 Prueba primero, `repositorio/tests/test_vistas.py` y `test_plantillas.py`: la pantalla carga solo `dist/rebrand.css`, trae «Sesiones» en la barra, el ☰ con Sesiones en «Próximamente» y sin `aria-current`; `<h1>Sesiones</h1>` sin ícono ni `franjas-cabecera`, el subtítulo, «Subir una sesión» con `data-abrir-subir` y el estado vacío con su texto; un solo `<main>` (el del marco) y `data-dimension="sesiones"` dentro (escenarios «Primera visita» y «Cabecera sin ícono ni franjas»). Las comprobaciones que buscaban `modal-cuerpo`, `campo__error`, `mensaje mensaje--error`, `acciones-modal` y `opcional` pasan a `data-cuerpo`, los `id` `-error`, `[data-error-red]`, el pie del diálogo y `.muted`. Luego `sesiones.html` con su cabecera, `rebrand/pantallas/sesiones.css` y el `@source` de `templates/repositorio/` (D1, D7). Verificar: rojo y luego verde; `uv run pytest src/backend/repositorio`
- [x] 3.2 Prueba primero, `repositorio/tests/test_plantillas.py`: `#subir` es un `rb/dialogo.html` de hoja y `#terminos` uno chico; conservan cada `id`, `name`, `data-*` y `aria-describedby` de decisiones.md («Se conserva»), «Enviar a la dirección» antes de «Cancelar» en el DOM, sin ✕, y los textos oficiales («Acepto y envío», el cuarto término con «eliminándola»); el primer `<p>` de `[data-error-general]` existe y está vacío; `_enviada.html` con el mensaje de éxito y «Subir otra» (`data-subir-otra`). Luego `_formulario.html`, `_terminos.html` y `_enviada.html`, y `.progress`, `.file-control` y `.check-label` en `rebrand/componentes.css` (D2, D5). Verificar: rojo y luego verde; `uv run pytest src/backend/repositorio`
- [x] 3.3 Prueba primero, `repositorio/tests/test_sesiones_e2e.py`: `OBJETIVOS_PEQUENOS` con `label[for=archivo]` y `label:has(#compartir)`, y «Pantalla baja» con `[data-cuerpo]` de los términos; nuevas: a 360 px el popup es una hoja abajo a todo el ancho y a 1280 px una ventana centrada de 480 px o menos; abrir «Subir una sesión» con Enter deja el diálogo en su lugar sin transición y Esc lo cierra de inmediato; con movimiento reducido no hay `transform`; «Subir una sesión» completo a 360 px y sin desplazamiento horizontal (escenario «Botón en el celular»). Luego los ajustes de CSS. Verificar: rojo y luego verde; `uv run pytest -m e2e src/backend/repositorio --browser chromium` con el CSS compilado y `DJANGO_ALLOW_ASYNC_UNSAFE=true`
- [x] 3.4 Las e2e de US-010/014 completas sobre el marco nuevo: popup, términos, «atrás», subida, corte de red, éxito, Slow 4G y los estados del boceto con axe en claro y oscuro, a 360 y 1280 px, con el ☰ y la cuenta cerrados. Verificar: e2e de `repositorio` en verde sin tocar `sesiones.js` (`git diff --stat` no lo nombra)
- [x] 3.5 Pantalla vista en claro/oscuro y celular/escritorio (la marca Marco). `verificar.py` y commit

## 4. Cierre

### Parte D: auditoría de Emil y A2

- [ ] 4.1 Auditoría de Emil (`review-animations` del diálogo; `break-ui` con títulos largos y errores abiertos a 320 px), en solo lectura con Codex → `insumos/rebrand-sesiones/auditoria-emil.md`. Marco aprueba los ids; cada uno se aplica con su prueba primero. Verificar: e2e de `repositorio` y `cuentas` en verde
- [ ] 4.2 Con la A2 que corre el usuario (`/codex:adversarial-review --base main --background`, con foco en la spec `envio-sesiones` del cambio, D3 y D4), corregir los Critical e Important, con la prueba primero. Verificar: `uv run pytest --cov` (80 % o más), las e2e y `verificar.py --antes-del-commit` en verde
- [ ] 4.3 `verificacion.md`: tabla escenario → prueba de la spec delta y de los escenarios de `envio-sesiones` que se vuelven a correr, y la DoD 1 a 9. Verificar: cada escenario tiene su prueba o su nota; commit

## Ajustes del propose a decisiones.md

- Punto 1: del boceto no entran el ✕ de los diálogos, «Acepto y comparto», el cuarto término sin «eliminándola» ni el orden «Cancelar / Enviar» del DOM; mandan la spec y «Se conserva» (D2).
- Punto 2: el botón «Subir una sesión» va sin el ícono `+` ni la etiqueta corta «Subir» del boceto; en el celular baja entero si no cabe (D1).
- Punto 4, «Errores de campo»: se usan las clases de `rb/campo.html` en marcado escrito a mano; el componente no sirve para archivo, selects ni textarea (D5).
- Punto 5: el movimiento del diálogo es solo CSS y la regla 1 sale de una marca de teclado en `marco.js`, para no tocar `sesiones.js` (D4).

## Workflow follow-up

- **(equipo)** Push de `feature/rebrand` con aprobación; sigue el PR borrador único hacia `main`, sin fusión antes del 11-11-2026. En «## Deuda» de su descripción:
  - pestañas, búsqueda, filtros (C-01), tarjetas, `sesion.html`, E-06 y E-07, y Sesiones disponible en el ☰ y en la portada → rama apilada (US-011/012/016);
  - estado y fecha de envío junto al encabezado de la sesión → con `sesion.html`;
  - salida del diálogo sin animación en navegadores sin `overlay` (Firefox) → aceptado;
  - CSS viejo de Sesiones en `app.css` → paso 8 del PLAN.
- Al proponer el siguiente cambio del rebrand (paso 2, Ingreso), su primer commit archiva este con `/opsx:archive` y «Sync now».
