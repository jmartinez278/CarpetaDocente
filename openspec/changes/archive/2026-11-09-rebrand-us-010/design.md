# Design: rebrand de Sesiones (US-010)

## Context

- Decisiones cerradas en `insumos/rebrand-sesiones/decisiones.md`; base del marco en `openspec/changes/archive/2026-11-09-rebrand-base/` (D1 a D10); norma en `DESIGN.md` 1.1. Lo nuevo de este propose está en `proposal.md`.
- Hoy `repositorio/sesiones.html` extiende `marco.html` (marco viejo, `app.css`) y pone su propio `<main class="vista-sesiones" data-dimension="sesiones">`; los popups son `_formulario.html` (`dialog#subir.modal-sesion`) y `_terminos.html` (`dialog#terminos.modal-terminos`), y `_enviada.html` es el éxito que `sesiones.js` pinta en `[data-resultado]`. Su CSS está en `src/frontend/css/app.css`.
- `marco_rebrand.html` ya pone `<main id="contenido" class="wrap page">`; la pantalla llena `{% block principal %}` y `{% block titulo_barra %}`. El ☰ marca Sesiones como «Próximamente» y sin `aria-current` (rebrand-base, D6).
- `sesiones.js` usa solo ganchos `data-*` e `id`, salvo dos cosas: `$("p", errorGeneral)` (primer párrafo del mensaje de error general) y la clase `rechazado` en `[data-archivo-control]`. Abre con `showModal()`, cierra con `close()`, maneja `cancel`, `close` y el historial.
- `rb/campo.html` solo pinta un `<input>` desde un `BoundField`; `rb/mensaje.html` pinta título y texto; `rb/boton.html` pinta enlace o botón.
- Pruebas que dependen de clases: `test_plantillas.py` (`franjas-cabecera`, `modal-cuerpo`, `campo__error`, `mensaje mensaje--error`, `acciones-modal`, `opcional`), `test_vistas.py` (`franjas-cabecera`) y `test_sesiones_e2e.py` (`.modal-cuerpo`, `label.elegir-archivo`, `label.casilla` en `OBJETIVOS_PEQUENOS`).

## Riesgos y zonas delicadas (primero)

- **[JS del producto que depende del marcado]** → D3 y D5: el primer `<p>` de `[data-error-general]` sigue siendo donde `sesiones.js` escribe, y `.rechazado` existe en el CSS nuevo. Las e2e de US-010/014 corren completas en esta pantalla.
- **[Salida del diálogo sin tocar `sesiones.js`]** → D4: la salida animada depende de `transition-behavior: allow-discrete` sobre `display` y `overlay`. Sin soporte de `overlay` (Firefox), el diálogo deja la capa superior de golpe: se pierde la salida, no la conducta.
- **[Regla 1 con un diálogo que abre otro JS]** → D4: la marca de teclado vive en `<html>` y la pone `marco.js`; Esc es tecla, así que cierra sin salida.
- **[Dos diálogos apilados]** → D4: los términos se abren sobre el formulario; cada uno tiene su `::backdrop` y el de arriba oscurece el de abajo, como hoy.
- **[Clases del prototipo que chocan con utilidades]** → D6: `rebrand.css` suma `templates/repositorio/` a `@source`; la prueba de la base que compara capas sigue en verde.

## Goals / Non-Goals

**Goals:**
- Sesiones sobre el marco nuevo con la misma conducta y los mismos textos de la spec.
- `rb/dialogo.html` y `rb/estado_vacio.html` listos para las pantallas siguientes.

**Non-Goals:**
- Cambiar `sesiones.js`, vistas, rutas o servicios.
- Borrar el CSS viejo de Sesiones en `app.css` (paso 8 del PLAN).

## Decisions

### D1. Página (`repositorio/sesiones.html`)

- Extiende `marco_rebrand.html`; `titulo_barra` «Sesiones». Dentro de `principal`: un `<div data-dimension="sesiones">` (el gancho deja el `<main>`, que es del marco) con la cabecera del boceto (`.page-heading.sessions-heading`): `<h1>Sesiones</h1>`, el subtítulo «Planificación de sesiones de aprendizaje» y `rb/boton.html` principal «Subir una sesión» con `data-abrir-subir`. `rb/boton.html` suma un parámetro opcional `datos` para el atributo `data-*` (sin él, nada cambia).
- En el celular el botón pasa debajo si no cabe (`flex-wrap`), con el texto completo: no se copian `.full-upload` / `.compact-upload` ni el ícono `+` del boceto.
- Debajo: `<noscript>` con `rb/mensaje.html` de aviso, la región `[data-resultado]` (`role="status"`) y `rb/estado_vacio.html` con `inbox` y el texto oficial. Después, los dos diálogos y `#anuncio`.

### D2. Lo que no se toma del boceto

El ✕ de la cabecera de ambos diálogos, «Acepto y comparto», el texto del cuarto término sin «eliminándola», el orden «Cancelar / Enviar» del DOM y el `<p class="error">` genérico del boceto. Mandan la spec y decisiones.md («Se conserva»): se cierra con «Cancelar», «Volver» o Esc; en el DOM «Enviar» va antes que «Cancelar» (arriba en el celular) y el CSS lo pone a la derecha en la PC.

### D3. Diálogo (`rb/dialogo.html`)

- Componente con `{% include … %}` y bloques por parámetros: `id`, `titulo`, `titulo_id`, `descripcion` (opcional, con su `id`), `variante` (`hoja` o `chico`), y el cuerpo y el pie como plantillas a incluir (`cuerpo`, `pie`). Pinta `<dialog class="dialog dialog--{{ variante }}" aria-labelledby aria-describedby>` con cabecera (`<h2 tabindex="-1">` y la descripción), cuerpo desplazable (`tabindex="0" role="region"` con nombre, `data-cuerpo` si se pide) y pie fijo.
- Estructura en columna: cabecera y pie no se encogen; el cuerpo tiene `overflow: auto` y `min-height: 0`; el diálogo, `max-height: calc(100svh - 32px)` (en la hoja, `calc(100svh - 24px)`). Así «Acepto y envío» y «Volver» siguen a la vista en una pantalla baja.
- **Hoja** (formulario): en el celular (`max-width: 699px`), fija abajo, a todo el ancho, radio solo arriba (`--r-lg`), `safe-area-inset-bottom` en el pie; desde 700 px, centrada, `width: min(480px, calc(100vw - 32px))`, radio `--r-lg`. **Chico** (términos): centrado en todos los anchos, `min(440px, calc(100vw - 32px))`.
- Superficie, borde, sombra (`--shadow-dialog`) y `::backdrop` como el prototipo (`dialog` y `dialog::backdrop` de `assets/app.css`), con el velo oscuro de la base.
- Si `_formulario.html` o `_terminos.html` no encajan en los parámetros, el apply puede pasar a `{% extends %}` con bloques; la estructura y las clases no cambian.

### D4. Movimiento del diálogo (DESIGN.md, «Movimiento»; reglas 1, 2 y 4)

- Solo CSS: `transform` y `opacity` en 200 ms con `--m-ease`, y `display` y `overlay` con `allow-discrete`; entrada con `@starting-style` sobre `dialog[open]`. Hoja: `translateY(100%)` → 0 en el celular; en la PC y en el chico, opacidad 0 y `translateY(8px)` → 0. El `::backdrop` solo con opacidad. Una transición interrumpida vuelve desde su valor actual (regla 2), así que cerrar a media entrada no salta.
- **Regla 1:** `marco.js` pone `data-teclado` en `<html>` con cualquier `keydown` y lo quita con `pointerdown`. Con la marca, `.dialog` y su `::backdrop` van con `transition: none`: abrir con Enter o Espacio y cerrar con Esc es inmediato. No toca la marca `data-pointer` de E-05 ni la lógica del ☰.
- **Reducido:** sin `transform`; solo opacidad hasta 200 ms.
- Ninguna transición de `width` ni `height` (la prueba de la base lo sigue comprobando sobre la hoja compilada).
- Alternativa descartada: replicar en `sesiones.js` el `data-cerrando` del ☰. Cambia el JS del producto (decisiones.md, «Se conserva») y el `close()` diferido chocaría con el manejo de `cancel` y del historial.

### D5. Formulario, términos y éxito

- `_formulario.html` sobre `rb/dialogo.html` (hoja), con los mismos `id`, `name`, `data-*`, `aria-describedby` y orden. Los campos se escriben a mano con las clases de `rb/campo.html` (`.field`, `.input`, `.small` para la ayuda, `.field-error` para el error, `aria-invalid` lo pone `sesiones.js`). Grado y área en `.field-pair` (dos columnas desde 700 px). Casilla con `.check-label`. «(opcional)» en `.muted`.
- Control de archivo: se conserva el del repo (`[data-archivo-control]`, nombre, detalle y «Elegir» / «Cambiar»), con clases nuevas (`.file-control`, `.file-control-elegir`) y `.rechazado` con borde `--danger`.
- Errores de red y general: marcado de `rb/mensaje.html` de error con `role="alert"` y `hidden`. El general lleva un primer `<p>` vacío donde escribe `sesiones.js`.
- Progreso: `.progress` con el texto y `<progress>` estilado en `--gold` sobre `--line`, sin animar el ancho (el valor cambia el relleno de una vez).
- `_terminos.html` sobre `rb/dialogo.html` (chico), con la lista del doc 09 §4 y el texto actual.
- `_enviada.html`: `rb/mensaje.html` de éxito con el título oficial y el resumen en una superficie `--card`, con «Subir otra» (`rb/boton.html` principal, `data-subir-otra`).

### D6. Estado vacío (`rb/estado_vacio.html`)

Recibe `icono`, `texto` y, opcional, `accion` (texto, `href` o `datos`, con `rb/boton.html`). Ícono decorativo de 32 px en `--muted`, texto en `--text-body`, centrado, con borde punteado `--line` y radio `--r-lg`. Sesiones lo usa sin acción.

### D7. CSS y pruebas

- `rebrand/componentes.css`: `.dialog`, `.progress`, `.empty`, `.file-control`, `.check-label`. `rebrand/pantallas/sesiones.css`: la cabecera y el resumen del éxito. `rebrand.css` suma `@source "../../backend/templates/repositorio"`.
- Las pruebas que buscan por clase pasan a ganchos (`data-cuerpo`, `[data-error-red]`, `id`) o a las clases nuevas; `OBJETIVOS_PEQUENOS` pasa a `label[for=archivo]` y `label:has(#compartir)`. Las que buscan por rol, texto, `data-*` o `id` no cambian.

### Datos de la tesis

Ninguno nuevo: la sesión guarda lo mismo que en US-010/014.

## Risks / Trade-offs

- [`overlay` sin soporte en Firefox] → la salida no se ve; la conducta y el foco no cambian.
- [La marca de teclado en `<html>` queda puesta tras usar Tab] → el siguiente diálogo abierto con el mouse quita la marca en el `pointerdown` antes de abrir, así que sí se anima.
- [El CSS viejo de Sesiones queda en `app.css`] → sin efecto: esta página ya no carga `app.css`. Se borra en el paso 8.
- [`rb/dialogo.html` con parámetros de plantilla] → si el include se vuelve incómodo, `{% extends %}` con bloques (D3); se decide en la primera tarea, sin cambiar la spec.

## Migration Plan

Sin migraciones. Para volver atrás basta con revertir los commits: la vista y el JS no cambian.
