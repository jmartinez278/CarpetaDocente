# Tasks

Ninguna parte es de alto riesgo: no toca modelos, permisos, transacciones ni notas; los nombres (RN-015) solo cambian de marcado y decisiones.md no marca zonas de cuidado. Cada componente compartido va en su commit (decisiones.md, punto 7).

## 1. Componentes compartidos: botón (D5)

### Parte A: `rb/boton.html` con `formulario` (normal) — E-05

- [x] 1.1 Prueba primero, `cuentas/tests/test_componentes_rb.py`: `rb/boton.html` con `tipo="submit"` y `formulario="form-x"` pinta `<button … type="submit" form="form-x">`; sin `formulario`, el HTML es idéntico al de hoy; con `href`, `formulario` se ignora. Luego el parámetro y su línea en el comentario del componente. Verificar: rojo y luego verde; `uv run pytest src/backend/cuentas/tests/test_componentes_rb.py`
- [x] 1.2 `verificar.py` y commit

## 2. Componentes compartidos: campo y mensaje (D6)

### Parte B: `rb/campo.html` y `rb/mensaje.html` (normal) — E-06

- [x] 2.1 Prueba primero, `cuentas/tests/test_componentes_rb.py`: con un formulario de `CharField(max_length=120)`, `rb/campo.html` pinta `maxlength="120"` sin pasarlo, y sin `max_length` no lo pinta; `autocapitalize="characters"` pinta ese atributo y `spellcheck="false"`; `descrito_por="ayuda-x"` entra en `aria-describedby` junto a la ayuda y al error; `foco="apellidos"` pone `data-foco` solo en ese campo; el campo del ingreso (`sin_correccion`, `mostrar_clave`) no cambia. Luego los cuatro parámetros (D6). Verificar: rojo y luego verde; `uv run pytest src/backend/cuentas/tests/test_componentes_rb.py`
- [x] 2.2 Prueba primero, `cuentas/tests/test_componentes_rb.py`: `rb/mensaje.html` con `estado` pinta `role="status"`; con `alerta` o `enfocar` sigue como hoy; sin ninguno, sin `role`. Luego el parámetro (D6). Verificar: rojo y luego verde; mismo archivo
- [x] 2.3 Pruebas de Ingreso y «sin permiso» sin cambios: `uv run pytest src/backend/cuentas`. `verificar.py` y commit

## 3. Viewport y alto del diálogo (D7)

### Parte C: viewport y alto en `dvh` (normal) — E-02

- [x] 3.1 Prueba primero, `cuentas/tests/test_marco_rebrand.py`: el `<meta name="viewport">` de una pantalla del rebrand trae `interactive-widget=resizes-content`; y en `cuentas/tests/test_hoja_rebrand_e2e.py` (hoja compilada): ninguna regla de `.dialog` ni `.dialog--hoja` usa `svh`, su `max-height` usa `dvh`, y siguen sin transiciones de `width` ni `height`. Luego `base_rebrand.html` y `rebrand/componentes.css` (D7). Verificar: rojo y luego verde; `uv run pytest src/backend/cuentas` y `uv run pytest -m e2e src/backend/cuentas/tests/test_hoja_rebrand_e2e.py --browser chromium` con el CSS compilado
- [x] 3.2 E-2e de `cuentas` y `repositorio` (Sesiones: «Pantalla baja», hoja a 360 px, ventana a 1280 px) en verde con el viewport nuevo. `verificar.py` y commit

## 4. Pantalla Estudiantes (D1–D6, D8)

### Parte D: Estudiantes en el marco del rebrand (normal)

- [x] 4.1 Prueba primero, `institucion/tests/test_vistas_estudiantes.py`: sin `HX-Request`, cada vista carga solo `dist/rebrand.css`, trae «Estudiantes» en la barra y el ☰, un solo `<main>` (el del marco), «Volver a la portada» y `<section class="panel-lista">` con `<h1 id="modal-titulo">` y sin «Cerrar»; con `HX-Request`, `<h2 id="modal-titulo">`, «Cerrar» con `data-cerrar`, `#modal-cuerpo` con `tabindex="0"` y `role="region"`, y el aviso OOB `#aviso-portada`. Las comprobaciones de `modal-cabecera`, `modal-pie`, `volver-lista`, `estudiante__numero` y `estudiante__nombre` pasan a `id`, `data-estudiante` y `.estudiante-nombre` (escenario «Página completa en el marco del rebrand»). Luego `pagina.html`, `_base.html`, `pantallas/estudiantes.css` con `.panel-lista`, `.dialog--lista` en `componentes.css`, y en `rebrand.css` su `@import` y el `@source` de `templates/institucion/estudiantes` (D1, D3). Verificar: rojo y luego verde; `uv run pytest src/backend/institucion/tests/test_vistas_estudiantes.py`
- [x] 4.2 Prueba primero, `test_vistas_estudiantes.py`: lista vacía con `rb/estado_vacio.html` y sus dos acciones en el pie; lista con número, nombre completo, «Editar» con su `aria-label`, «Agregar estudiante» arriba y «Vaciar lista» al final (`.btn--peligro`); aviso de importados con `role="status"` y «Tomar la asistencia de hoy» sin `hx-get`; `_aviso_portada.html` con `rb/mensaje.html` aviso y `estado`, mismo `id` y OOB. Luego `_lista.html`, `_lista_vacia.html` y `_aviso_portada.html` (D5). Verificar: rojo y luego verde; mismo archivo
- [x] 4.3 Prueba primero, `test_vistas_estudiantes.py`: Agregar y Editar con `rb/campo.html`: `maxlength="120"`, `autocapitalize="characters"`, `#ayuda-nombres` en el `aria-describedby` de los dos campos de Agregar, `data-foco` en el campo que manda la vista, error en `.field-error` con `id_nombres_error`; homónimo con `rb/mensaje.html` error y `role="alert"`; «Guardar y agregar otro» y «Guardar cambios» con `form="form-estudiante"` (E-05, E-06). Luego `_agregar.html`, `_editar.html` y `_error_homonimo.html`, y borrar `_campo_estudiante.html` (D5, D6). Verificar: rojo y luego verde; mismo archivo
- [x] 4.4 Prueba primero, `test_vistas_estudiantes.py`: un texto que empieza con una línea vacía y tiene error en la línea 3 vuelve con el `<textarea>` que conserva esa primera línea y el error dice «Línea 3» (E-03); con errores, `aria-describedby` suma `pegar-errores`; «Importar» con `form="form-pegar"`; «ya tiene estudiantes» con `role="status"` y sin cuadro de texto. Luego `_pegar.html` y `_pegar_con_estudiantes.html` (D6). Verificar: rojo y luego verde; mismo archivo
- [x] 4.5 Prueba primero, `test_vistas_estudiantes.py`: Quitar con `.confirmacion` y el nombre completo, «Quitar estudiante» con `form="form-quitar"`; Vaciar con el aviso en singular y plural y `form="form-vaciar"`; los dos bloqueos con `rb/mensaje.html` error, `role="alert"` y solo «Volver a la lista». Luego `_quitar.html` y `_vaciar.html` (D5). Verificar: rojo y luego verde; `uv run pytest src/backend/institucion`
- [x] 4.6 `estudiantes.js`: `.modal-cuerpo` → `#modal-cuerpo` (D4). Prueba primero, `test_estudiantes_e2e.py`: tras desplazar la lista del diálogo y abrir Editar, el cuerpo vuelve arriba. Verificar: rojo y luego verde; `git diff --stat` solo nombra esa línea del JS
- [x] 4.7 Prueba primero, `institucion/tests/test_estudiantes_e2e.py`: axe y ancho de cada vista de la spec como página completa (lista vacía, lista, importados, Pegar, Revisar, Agregar con error y con éxito, homónimo, Editar, Quitar, Vaciar y los dos bloqueos), claro y oscuro, 360 y 1280 px, con el ☰ y la cuenta cerrados; nombre de 120 + 120 a 320 px y con el texto al 200 % se lee completo y «Editar» queda a la vista; a 360 px el pie apila sus acciones a todo el ancho. Las e2e que miden el diálogo dentro de la portada pasan a `skip` con motivo `rebrand-portada` (D8); `.estudiante__nombre` y `.estudiantes` pasan a `.estudiante-nombre` y `.estudiantes-lista`. Luego los ajustes de CSS. Verificar: rojo y luego verde; `uv run pytest -m e2e src/backend/institucion --browser chromium` con el CSS compilado y `DJANGO_ALLOW_ASYNC_UNSAFE=true`
- [x] 4.8 E-2e de conducta del diálogo en verde sin cambios de lógica: abrir, foco al título, Esc, «Cerrar», Atrás, importar, sesión vencida a `/ingresar/` con el aviso y «sin permiso» como página completa (spec `acceso-secciones`, «Diálogo de la portada»), y «Sin JavaScript». Verificar: e2e de `institucion` en verde
- [x] 4.9 Pantalla vista en claro/oscuro y celular/escritorio como página completa (la marca Marco). `verificar.py` y commit

## 5. Cierre

### Parte E: A2 y verificacion.md

- [x] 5.1 E-02 a mano: en un Android real, Agregar como página completa con el teclado abierto deja a la vista el campo y el pie. Si no alcanza, a la deuda del pulido final. Verificar: resultado anotado en `verificacion.md`
- [x] 5.2 Con la A2 que corre el usuario (`/codex:adversarial-review --base main --background`, con foco en la spec `estudiantes-seccion` del cambio, D3, D6 y D7), corregir los Critical e Important, con la prueba primero. Verificar: `uv run pytest --cov` (80 % o más), las e2e y `verificar.py --antes-del-commit` en verde
- [x] 5.3 `verificacion.md`: tabla escenario → prueba de la spec delta y de los escenarios de `estudiantes-seccion` que se vuelven a correr (con los saltados por `rebrand-portada` señalados), y la DoD 1 a 9. Verificar: cada escenario tiene su prueba o su nota; commit

## Ajustes del propose a decisiones.md

- Punto 2: el diálogo es `.dialog--lista` (760 px y 720 px de alto en la PC, `100vw/100dvh − 16px` en el celular); `_base.html` pinta el interior de `rb/dialogo.html` porque HTMX llena un `<dialog>` que ya existe (D3).
- Punto 1: del boceto no entran el «Cerrar» del pie de la lista, el ícono `+` ni el número por contador de CSS (D2).
- Punto 7: además de E-05 y E-06, `rb/campo.html` acepta `descrito_por` y `foco`, y `rb/mensaje.html` acepta `estado` (D5, D6).
- «Se conserva» `estudiantes.js`: cambia un selector, `.modal-cuerpo` → `#modal-cuerpo` (D4).
- «Mapa de pruebas»: axe y ancho dentro del diálogo pasan a `rebrand-portada`; aquí se revisan como página completa (D8).

## Workflow follow-up

- **(rebrand-portada)** Dar al `<dialog id="estudiantes">` las clases `dialog dialog--lista`, quitar los `skip` con motivo `rebrand-portada` de `test_estudiantes_e2e.py` y correr axe, ancho, «Cerrar» de 44 px y nombre largo dentro del diálogo. Push solo al cerrar los dos cambios, con aprobación; sigue el PR borrador único hacia `main`.
- **(rebrand-portada, A2 [high])** El popup de la portada pierde el desplazamiento: `_base.html` usa `.dialog-cuerpo` y la portada solo carga `app.css`. Se corrige al dar `dialog dialog--lista` al `<dialog>` y cargar `rebrand.css`; añadir una e2e con una lista que supere el alto del diálogo y comprobar que el último «Editar» se alcanza.
- **(pulido final)** E-02 en un celular real, sobre el popup, Android e iPhone: 5.1 se hizo solo con emulación de DevTools.
- **(equipo)** E-07: ¿hay un máximo de estudiantes por sección? (pregunta en `auditoria-emil.md`). Si sí, cambio de spec propio.
- E-02: si `interactive-widget=resizes-content` no alcanza en Android → pulido final (Sesiones y Estudiantes).
- Paso 8 del PLAN: `_subir_pie.html` de Sesiones a `rb/boton.html formulario=`; enlaces HTMX del pie a `rb/boton.html` si gana `hx-get`; borrar el CSS viejo de Estudiantes en `app.css`.
- Al proponer `rebrand-portada`, su primer commit archiva este con `/opsx:archive` y «Sync now».
