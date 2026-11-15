# Design: rebrand de Estudiantes (US-006)

## Context

- Decisiones cerradas en `insumos/rebrand-estudiantes/decisiones.md` y ids aprobados al final de `auditoria-emil.md` (E-02, E-03, E-05, E-06). Base del marco en `openspec/changes/archive/2026-11-09-rebrand-base/`; diálogo y estado vacío en `…/2026-11-09-rebrand-us-010/` (D3, D4, D6). Lo nuevo de este propose está en `proposal.md`.
- Hoy el `<dialog id="estudiantes" class="modal-estudiantes" hx-target="this" hx-swap="innerHTML">` vive vacío en `cuentas/portada_docente.html`; cada respuesta HTMX reemplaza **todo su interior** con `dialogo.html` (`{% include parcial %}` + `_aviso_portada.html` OOB). Sin HTMX, la vista responde `pagina.html` (extiende `marco.html`). Lo decide `SeccionDocenteMixin.responder` (`institucion/views.py:57`), que no cambia.
- `_base.html` pinta `header.modal-cabecera` (título `#modal-titulo`, `#modal-cantidad`, «Cerrar» `data-cerrar` solo en el diálogo, bloque `accion`), `div.modal-cuerpo#modal-cuerpo` y `footer.modal-pie#modal-pie`. Las vistas lo extienden.
- `estudiantes.js` usa `data-abrir-estudiantes`, `data-cerrar`, `data-foco`, `#estudiantes` y `body.con-dialogo`, y **una clase**: `dialogo.querySelector(".modal-cuerpo")?.scrollTo(…)`.
- `rb/dialogo.html` pinta el `<dialog>` entero con cuerpo y pie incluidos: sirve cuando el diálogo nace con la página (Sesiones), no cuando HTMX llena un `<dialog>` vacío.
- `.dialog` (`rebrand/componentes.css:174`) mide `min(480px, …)` de ancho y `calc(100svh - 32px)` de alto máximo; la hoja, `calc(100svh - 24px)`. `base_rebrand.html` tiene `width=device-width, initial-scale=1`.
- Pruebas por clase (decisiones.md, «Mapa de pruebas»): `test_vistas_estudiantes.py` busca `modal-cabecera`, `modal-pie`, `estudiante__numero`, `estudiante__nombre`, `accion-peligro`, `volver-lista`, `confirmacion-nombre`, `campo__error` con `id` `agregar-nombres-error` y `mensaje mensaje--*`; `test_estudiantes_e2e.py`, `.estudiante__nombre` y `.estudiantes`.

## Riesgos y zonas delicadas (primero)

- **[Diálogo nuevo dentro de la portada vieja]** → D8: entre este cambio y `rebrand-portada` la portada carga `app.css` y las vistas del diálogo usan clases del rebrand, así que se ven sin estilo. Por eso no hay push entre los dos. Las e2e que miden aspecto dentro del diálogo se saltan con motivo `rebrand-portada` y esa historia las reactiva; las de conducta (abrir, foco, Esc, Atrás, importar, sesión vencida, sin permiso) siguen corriendo aquí.
- **[Componentes compartidos con otras pantallas]** → D5, D6, D7: `rb/boton.html`, `rb/campo.html` y `rb/mensaje.html` los usan Ingreso, Sesiones y «sin permiso»; cada parámetro es opcional y sin él el HTML no cambia (prueba de no cambio en `test_componentes_rb.py`). El viewport y `dvh` tocan todas las pantallas del rebrand: commit propio y e2e de `cuentas` y `repositorio` en su verificación.
- **[`interactive-widget=resizes-content`]** → D7: con el teclado abierto el área de diseño se achica en Chrome de Android; el ☰ y la cuenta (también `dialog`) se reacomodan igual. Safari lo ignora. Se comprueba a mano en un Android al cierre; si no alcanza, va al pulido final (decisiones.md, «Deuda»).
- **[Numeración de líneas en Pegar lista]** → D6: el salto tras `<textarea …>` se conserva (E-03) y una prueba lo fija.
- **[Datos personales a la vista]** (RN-015): solo cambia el marcado de los nombres; el escape de plantillas no se toca (sin `|safe`).

## Goals / Non-Goals

**Goals:**
- Todas las vistas de la lista sobre el marco y los componentes del rebrand, con la misma conducta, rutas, `id`, ganchos y textos.
- `rb/boton.html`, `rb/campo.html` y `rb/mensaje.html` listos para las vistas con pie fijo y formularios de Django.

**Non-Goals:**
- La portada y su `<dialog id="estudiantes">` (`rebrand-portada`).
- Cambiar vistas, servicios, formularios o la conducta de `estudiantes.js`.
- Un máximo de estudiantes por sección (E-07).

## Decisions

### D1. Página completa (`pagina.html`)

- Extiende `marco_rebrand.html`; `titulo_barra` «Estudiantes»; `<title>` sigue «{{ titulo }} · CarpetaDocente». Dentro de `principal`: «Volver a la portada» (`rb/boton.html` variante texto, `icono="chevron-left"`) y `<section class="panel-lista" aria-labelledby="modal-titulo">` con el parcial. El `<main>` es el del marco.
- `.panel-lista`: la misma cabecera, cuerpo y pie que el diálogo, en una superficie `--card` con borde y `--r-lg`, `max-width: 760px`, centrada, sin sombra ni alto fijo; el cuerpo no se desplaza (crece la página). Es el `page-mode` del boceto.

### D2. Lo que no se toma del boceto

El «Cerrar» del pie de la lista y su rótulo «Estudiantes de 2.º A» (ya están en la cabecera), el ícono `+` de «Agregar estudiante» (no está en `templates/iconos/`; mismo criterio que Sesiones, D1) y el número por `counter()` de CSS: se conserva `<span class="estudiante-numero" aria-hidden="true">` del repo, que la `<ol>` ya anuncia. «Volver a tu inicio» del pie de la página completa tampoco: queda «Volver a la portada» arriba, como hoy.

### D3. Diálogo de la lista (`.dialog--lista`)

- `_base.html` pinta el **interior** de `rb/dialogo.html` con sus clases: `<header class="dialog-cabecera">`, `<div class="dialog-cuerpo" id="modal-cuerpo">` y `<footer class="dialog-pie" id="modal-pie">`. En el diálogo, el cuerpo lleva `tabindex="0" role="region" aria-labelledby="modal-titulo"` (como `rb/dialogo.html`); en la página, nada de eso. El `<dialog>` que lo envuelve recibe `class="dialog dialog--lista"` en `rebrand-portada`.
- Cabecera: fila con el título (`<h2>` en el diálogo, `<h1>` en la página, `#modal-titulo`, `data-foco tabindex="-1"` según el bloque `foco_titulo` actual) y `#modal-cantidad` (`.small`, cifras tabulares) a la izquierda; «Cerrar» a la derecha, solo en el diálogo: `<button class="btn btn--secondary dialog-cerrar" type="button" data-cerrar>` con `x.svg` y el texto «Cerrar»; bajo 700 px el texto pasa a `sr-only` y el botón queda de 44 × 44 (el nombre accesible sigue siendo «Cerrar»). Debajo, el bloque `accion` («Agregar estudiante», `rb/boton.html` principal).
- `.dialog--lista` (en `componentes.css`, sobre `.dialog`): desde 700 px `width: min(760px, calc(100vw - 48px))` y `height: min(720px, calc(100dvh - 48px))`, alto fijo para que el cambio de vista no mueva la ventana; bajo 700 px, `width: calc(100vw - 16px)` y `height: calc(100dvh - 16px)`, centrado (hoja casi completa del boceto), sin el `translateY(100%)` de la hoja. Movimiento, `::backdrop`, marca de teclado y movimiento reducido: los de `.dialog`.
- Pie: en la PC, acciones en fila (principal a la izquierda, «Volver a la lista» a la derecha, como el boceto); bajo 700 px, en columna a todo el ancho, con `safe-area-inset-bottom`. `.dialog-pie:empty` no se pinta.
- `body.con-dialogo { overflow: hidden }` pasa a `pantallas/estudiantes.css` (hoy solo está en `app.css`).

### D4. `estudiantes.js`

Un solo cambio: `.modal-cuerpo` → `#modal-cuerpo` en `enfocar()`. El `id` está en la lista de «Se conserva»; la clase desaparece. Nada más del JS cambia (`git diff --stat` lo comprueba).

### D5. Lista, vacía y vistas de confirmación

- **Lista:** `<ol class="estudiantes-lista" aria-label="Estudiantes ordenados por apellidos">`; cada fila `<li class="estudiante-fila" data-estudiante>` en grid `24px minmax(0,1fr) auto` (16 px de número bajo 700 px), con `estudiante-numero`, `estudiante-nombre` (16 px, `min-width: 0`, `overflow-wrap: anywhere`, sin elipsis ni `nowrap`) y «Editar» (`btn btn--text`, 44 px, `aria-label` actual). Los nombres siguen en MAYÚSCULAS desde el servicio: sin `text-transform`. Las pruebas buscan la fila por `data-estudiante` y el nombre por `.estudiante-nombre`.
- **Aviso de importados:** marcado de `.message.message--exito` escrito a mano (`role="status"`), porque lleva el texto con `linebreaks` y el enlace «Tomar la asistencia de hoy» (`btn btn--text`, 44 px, `arrow-right.svg`), que `rb/mensaje.html` no admite.
- **«Vaciar lista»** al final y **«Quitar estudiante»** en Editar: `rb/boton.html` variante texto con `clase="btn--peligro"` (texto `--danger`), enlaces con `hx-get`. `rb/boton.html` no pone `hx-get`: se escriben a mano con sus clases, igual que «Volver a la lista», «Editar» y los botones del pie que son enlaces HTMX.
- **Lista vacía:** `rb/estado_vacio.html` con `inbox` y el texto oficial; «Agregar uno por uno» (principal) y «Pegar lista» (secundario) en el pie, como hoy.
- **Quitar:** «¿Quitar a …?» en `<p class="confirmacion">` con el nombre completo (misma regla de corte que la lista). **Vaciar** y **«ya tiene estudiantes»**: `rb/mensaje.html` aviso con `estado`. **Bloqueos y homónimo:** `rb/mensaje.html` error con `alerta`.
- **Botones del pie** que envían un formulario: `rb/boton.html` principal con `tipo="submit"` y `formulario` (E-05): «Importar», «Guardar y agregar otro», «Guardar cambios», «Quitar estudiante», «Vaciar lista».

### D6. Formularios: Agregar, Editar y Pegar lista

- **Agregar y Editar** con `rb/campo.html` (E-06); `_campo_estudiante.html` se borra. Parámetros nuevos, todos opcionales:
  - `maxlength` sale de `campo.field.max_length` (120) sin pasarlo; sin `max_length`, no se pinta.
  - `autocapitalize` (valor): pinta `autocapitalize="…"` y `spellcheck="false"`. Estudiantes pasa `characters`. `sin_correccion` del ingreso no cambia.
  - `descrito_por` (`id` de una ayuda fuera del campo): se suma a `aria-describedby`. Agregar conserva su ayuda común `#ayuda-nombres` «Los nombres se guardan en mayúsculas.» para los dos campos; Editar usa `ayuda` por campo, como hoy.
  - `foco` (nombre de un campo): si coincide con `campo.name`, pone `data-foco`. La vista ya manda `foco` (`_foco(formulario)`).
  Los `id` pasan a los de Django (`id_apellidos`, `id_nombres`, `id_nombres_error`): Agregar y Editar nunca están a la vez en el DOM.
- **Pegar lista:** el `<textarea>` se escribe a mano con las clases de campo (`.field`, `.input`, `.small`), como Sesiones (D5), con los `id` conservados (`lista-pegada`, `pegar-ayuda`, `pegar-formato`, `pegar-ejemplo`, `form-pegar`) y **el salto de línea tras la etiqueta de apertura** (E-03). Con errores, `aria-describedby` suma `pegar-errores` (del boceto). La lista de errores `<ul id="pegar-errores" class="errores-lista">` muestra título (16 px) y ayuda (`.small`); el mensaje general, `rb/mensaje.html` error con `alerta`.
- `rb/mensaje.html` suma `estado` (`role="status"`), que no se combina con `alerta` ni `enfocar`.

### D7. Viewport y alto en `dvh` (E-02)

- `base_rebrand.html`: `<meta name="viewport" content="width=device-width, initial-scale=1, interactive-widget=resizes-content">`.
- `.dialog` y `.dialog--hoja` pasan de `svh` a `dvh` en `max-height`; `.dialog--lista` nace en `dvh`. Con `resizes-content`, al abrir el teclado se achica el área de diseño y con ella `dvh`, así que el pie fijo queda sobre el teclado. La regla `max-height: 480px` (Emil B-02 de Sesiones) sigue igual.
- Commit propio; afecta a Sesiones, Ingreso y «sin permiso», cuyas e2e corren en su verificación.

### D8. Pruebas

- `test_vistas_estudiantes.py`: las comprobaciones por clase pasan a `id` (`modal-titulo`, `modal-pie`, `modal-cuerpo`), `data-estudiante`, `.estudiante-nombre`, `.message--*`, `.field-error`, `.btn--peligro` y `.confirmacion`. Nuevas: la página extiende el marco (solo `dist/rebrand.css`, «Estudiantes» en la barra, un solo `<main>`); primera línea vacía en Pegar lista con los números de error intactos (E-03); botones del pie con `form` igual al `id` de su formulario (E-05); `maxlength="120"` y `autocapitalize="characters"` en Agregar y Editar (E-06).
- `test_estudiantes_e2e.py`: axe, ancho y nombre largo pasan a la **página completa** (rebrand) en todas las vistas de la spec, 360 y 1280 px, claro y oscuro, con el ☰ y la cuenta cerrados; nombre de 120 + 120 a 320 px y con el texto al 200 %. Las que miden el diálogo dentro de la portada (Cerrar de 44 px, contorno del título, nombre largo y axe en el diálogo) llevan `pytest.mark.skip(reason="rebrand-portada: la portada aún carga app.css")`; su reactivación es tarea de `rebrand-portada`.
- `test_hoja_rebrand_e2e.py` (hoja compilada): `.dialog`, `.dialog--hoja` y `.dialog--lista` sin `svh`; `.dialog--lista` con 760 px; siguen sin transiciones de `width` ni `height`.

### Datos de la tesis

Ninguno nuevo: la lista guarda lo mismo que en US-006.

## Risks / Trade-offs

- [Entre los dos cambios el diálogo de la portada se ve sin estilo] → sin push; las e2e de aspecto del diálogo se saltan con motivo y vuelven en `rebrand-portada`.
- [`resizes-content` cambia el diseño de todas las pantallas al abrir el teclado] → es lo que se busca para los pies fijos; si en Android rompe otra pantalla, se quita y E-02 va al pulido final.
- [Pie de enlaces HTMX escritos a mano con clases de `rb/boton.html`] → mismas clases; si `rb/boton.html` gana `hx-get`, se pasan en el paso 8.
- [Alto fijo de 720 px en la PC] → con 1 estudiante sobra aire; a cambio, las vistas no saltan (boceto, opción A).

## Migration Plan

Sin migraciones. Volver atrás es revertir los commits; vistas y servicios no cambian.
