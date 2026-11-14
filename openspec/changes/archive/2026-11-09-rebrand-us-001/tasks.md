# Tasks

La página es de alto riesgo: es el formulario de autenticación (CSRF, `next`, el campo de contraseña y el error que no dice qué campo falló). Los componentes van antes, en una parte normal. `rebrand-us-010` ya está archivado (commit `80f3e12`).

## 1. Componentes (D3)

### Parte A: `rb/campo.html`, `rb/mensaje.html` y `rb/pie.html` (normal)

- [x] 1.1 Prueba primero, `cuentas/tests/test_componentes_rb.py`: `rb/campo.html` con `mostrar_clave` pinta el `<input>` dentro de `.input-grupo` y el botón con `type="button"`, `data-mostrar-clave`, `aria-controls` hacia el `id` del campo, `aria-pressed="false"`, `aria-label="Mostrar contraseña"`, `hidden` y los dos íconos `aria-hidden`; con `variante="ingreso"` lleva `.field--ingreso`; con `sin_correccion`, `autocapitalize="none"` y `spellcheck="false"`; la contraseña nunca trae `value`; sin los parámetros, el marcado de hoy. Luego el componente, `.input-grupo`, el ojo (44 × 44 px, un ícono según `aria-pressed`) y `.field--ingreso` (52 px, `--g-alt`) en `rebrand/componentes.css`. Verificar: rojo y luego verde; `uv run pytest src/backend/cuentas/tests/test_componentes_rb.py`
- [x] 1.2 Prueba primero, `cuentas/tests/test_componentes_rb.py`: `rb/mensaje.html` con `icono="clock"` usa ese ícono; con `enfocar` pinta `tabindex="-1"` y `autofocus` y no lleva `role="alert"` aunque se pase `alerta`; sin ellos, igual que hoy. `rb/pie.html` con `solo_marca` pinta solo «CarpetaDocente · 2026» con `.footer--marca`; sin él, los dos textos. El filtro `partes_aviso` parte «título\n\ndetalle» en sus dos líneas. Luego los componentes, el filtro en `cuentas/templatetags/marco.py`, el foco visible de `.message[tabindex]` y `.footer--marca` centrado en `rebrand/marco.css` (D2, D3). Verificar: rojo y luego verde; `uv run pytest src/backend/cuentas/tests/test_componentes_rb.py`
- [x] 1.3 `verificar.py` y commit

## 2. Pantalla de ingreso (D1, D2, D4, D5, D6)

### Parte B: el ingreso en el marco del rebrand (alto riesgo)

- [x] 2.1 Prueba primero, `cuentas/tests/test_pantallas.py`: `/ingresar/` carga solo `dist/rebrand.css` (no `app.css`), precarga Besley e Instrument Sans y ninguna otra pantalla del rebrand precarga Besley; sin barra ni ☰; el orden del escudo vacío `aria-hidden`, el `<h1>` «I.E. Virgen del Carmen», «Huayucachi», «Sesiones · Notas · Asistencia», la ficha con el formulario (`data-formulario-ingreso`, `aria-label`, CSRF, `next`), Usuario con su pista y `sin_correccion`, Contraseña con el ojo, «Ingresar» con `data-boton-ingresar` y la ayuda; la región `data-estado-ingreso` fuera del formulario; el pie solo con «CarpetaDocente · 2026»; sin enlaces de recuperación. Las comprobaciones de `campo__etiqueta` y `campo__error` pasan a `label[for=id_…]` y `.field-error` con sus `id`. Luego `base_rebrand.html` (bloque `precargas`), `cuentas/ingresar.html`, `rebrand/pantallas/ingreso.css` con el `@font-face` de Besley (`font-display: optional`) y el `@source` y el import en `rebrand.css` (D1, D5). Verificar: rojo y luego verde; `uv run pytest src/backend/cuentas`
- [x] 2.2 Prueba primero, `cuentas/tests/test_pantallas.py` y `test_ingresar.py`: con un rechazo, el error va antes de la ficha con el título del error de la vista y «Revisa tus datos…», `tabindex="-1"`, `autofocus` y sin `role="alert"`; ningún campo lleva `autofocus`; Usuario conserva lo escrito y Contraseña llega vacía. Tras la inactividad, el aviso va en el mismo lugar con el ícono `clock`, sus dos líneas y `role="status"`, una sola vez; tras un cierre elegido no aparece. Las comprobaciones de `mensaje--aviso` pasan a `.message--aviso`. Luego el marcado de los dos mensajes (D2). Verificar: rojo y luego verde; `uv run pytest src/backend/cuentas`
- [x] 2.3 Prueba primero, `cuentas/tests/test_ingresar_e2e.py`: espera `dist/rebrand.css`; tras un rechazo `document.activeElement` es el mensaje de error, que no está dentro de ninguna región viva, y Tab lleva a Usuario (escenarios «Mensaje de error sobre el formulario» y «Error y teclado»); con el envío retenido, el botón dice «Ingresando…», su fondo calculado es el de `--folder` y distinto del normal, tiene el `::before` del giro, y los campos son de solo lectura con borde punteado; con movimiento reducido el giro no tiene animación; «Mostrar contraseña» alterna `aria-pressed` y el tipo, y al enviar vuelve a `password`; sin JavaScript el ojo no aparece y el formulario se envía. Luego el estado de envío y el giro en `ingreso.css` (D4). Verificar: rojo y luego verde; `uv run pytest -m e2e src/backend/cuentas/tests/test_ingresar_e2e.py --browser chromium` con el CSS compilado y `DJANGO_ALLOW_ASYNC_UNSAFE=true`; `git diff --stat` no nombra `ingresar.js`
- [x] 2.4 Prueba primero, `cuentas/tests/test_accesibilidad_e2e.py`: axe en los cinco estados del inicio de sesión (normal, error, campos vacíos, «Ingresando…» y aviso de inactividad) en claro y oscuro, a 360 y 1280 px, con esperas por `.field-error` y `.message--aviso`; el ojo mide 44 × 44 px; sin desplazamiento horizontal a 320 y 360 px. Luego los ajustes de CSS (nombre a 30 px y ficha más estrecha por debajo de 700 px). Verificar: rojo y luego verde; e2e de `cuentas`
- [x] 2.5 `cuentas/tests/test_rendimiento_e2e.py` sin cambios: «Primera visita con Slow 4G» con Instrument Sans y Besley, 2 MB o menos e «Ingresar» usable en 5 s o menos. Verificar: verde; si falla, depuración sistemática antes de tocar la carga de fuentes
- [x] 2.6 Pantalla vista en claro/oscuro y celular/escritorio (la marca Marco). Revisor sobre `git diff --cached` de la parte; Critical e Important corregidos. `verificar.py` y commit

## 3. Cierre

### Parte C: auditoría de Emil, A2 y `verificacion.md`

- [x] 3.1 Auditoría de Emil (`review-animations` del estado de envío y del ojo; `break-ui` con un usuario largo, el error abierto a 320 px y zoom de texto), en solo lectura con Codex → `insumos/rebrand-ingreso/auditoria-emil.md`. Marco aprueba los ids; cada uno se aplica con su prueba primero. Verificar: e2e de `cuentas` en verde
- [x] 3.2 Con la A2 que corre el usuario (`/codex:adversarial-review --base main --background`, con foco en la delta de `pantallas-de-inicio`, D2 y D4), corregir los Critical e Important con la prueba primero. Verificar: `uv run pytest --cov` (80 % o más), las e2e y `verificar.py --antes-del-commit` en verde
- [x] 3.3 `verificacion.md`: tabla escenario → prueba de la delta y de los escenarios de `pantallas-de-inicio` («Mostrar la contraseña», «Estado de envío», «Carga en conexión lenta», «Sin desplazamiento horizontal») y de `cierre-sesion` («Aviso de cierre por inactividad») que se vuelven a correr, y la DoD 1 a 9. Verificar: cada escenario tiene su prueba o su nota; commit

## Ajustes del propose a decisiones.md

- Punto 5: el error deja `role="alert"`; el anuncio sale del foco con `autofocus` y `tabindex="-1"`, sin JS (D2).
- Punto 9 y DESIGN.md: el giro de «Ingresando…» es un `::before` del botón y el estado sale de `aria-disabled` / `aria-busy`, para no tocar `ingresar.js` (D4).
- Punto 3, aviso de inactividad: un filtro parte el mensaje de la vista en sus dos líneas; el middleware no cambia (D3).

## Workflow follow-up

- **(equipo)** Push de `feature/rebrand` con aprobación; sigue el PR borrador único hacia `main`, sin fusión antes del 11-11-2026. En «## Deuda» de su descripción:
  - escudo de la I.E. → T-06 (espacio reservado y vacío);
  - botón de tema junto al pie → T-04, rama apilada;
  - Besley en `app.css`, `componentes/campo.html`, `componentes/pie.html` y la clase `boton-principal--enviando` (marca interna de `ingresar.js`, ya sin estilo) → paso 8 del PLAN;
  - Besley con `font-display: optional` puede no verse en la primera visita con Slow 4G → aceptado;
  - DESIGN.md (línea 141) aún dice `role="alert"` en el error del ingreso; D2 lo quitó → corregir el texto con aprobación del equipo.
- Al proponer el siguiente cambio del rebrand (paso 3, Portada y Estudiantes), su primer commit archiva este con `/opsx:archive` y «Sync now».
