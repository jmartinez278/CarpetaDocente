# Design: rebrand del Ingreso (US-001)

## Context

- Decisiones cerradas en `insumos/rebrand-ingreso/decisiones.md`; base del marco en `openspec/changes/archive/2026-11-09-rebrand-base/`; norma en `DESIGN.md` 1.1 («Inicio de sesión» en Components y la excepción de Besley). Lo nuevo de este propose está en `proposal.md`.
- Hoy `cuentas/ingresar.html` extiende `base.html` (carga `app.css` y precarga Besley) y usa `componentes/campo.html` (con `es_clave`, el ojo y `autocapitalize`/`spellcheck` en Usuario), `componentes/pie.html` y clases viejas (`.mensaje--aviso`, `.mensaje--error`, `.boton-principal`). El error general lleva `role="alert"`; el aviso de inactividad, `role="status"` con el ícono `clock`.
- `ingresar.js` se conserva sin cambios. Usa solo ganchos (`data-mostrar-clave` con `aria-controls`, `data-formulario-ingreso`, `data-boton-ingresar`, `data-estado-ingreso`) y, en el envío, **reescribe `textContent` del botón**, pone `aria-disabled="true"` en el botón, `aria-busy="true"` en el formulario, `readOnly` en los campos `text`/`password` y alterna la clase `boton-principal--enviando` (que también usa para descartar un segundo envío).
- `rb/campo.html` pinta un `<input>` desde un `BoundField`, sin ojo ni variante; `rb/mensaje.html` usa siempre `circle-alert` (o `check`) y no admite foco; `rb/pie.html` pinta los dos textos; `base_rebrand.html` solo precarga Instrument Sans y tiene el bloque `scripts`.
- Pruebas que dependen de clases viejas: `test_pantallas.py` (`campo__etiqueta`, `campo__error`, `mensaje--aviso`), `test_accesibilidad_e2e.py` (`.campo__error`, `.mensaje--aviso`) y `test_ingresar_e2e.py` (espera la respuesta de `dist/app.css`; la clase `boton-principal--enviando` la sigue poniendo el JS).

## Riesgos y zonas delicadas (primero)

- **[El JS borra lo que haya dentro del botón]** → D4: el giro es un `::before` del botón, no un `<span>`; así sobrevive a `textContent = "Ingresando…"` y `ingresar.js` no se toca.
- **[Doble anuncio del error]** → D2: sin `role="alert"`; el anuncio sale del foco. Una prueba comprueba el foco y que el mensaje no está en una región viva.
- **[Carga en conexión lenta con una fuente más]** → D5: Besley con `font-display: optional` (sin cambio de letra a media carga) y precargada solo aquí. «Carga en conexión lenta» se vuelve a correr.
- **[Componentes compartidos]** → D3: cada parámetro nuevo es opcional; las pruebas de `test_componentes_rb.py` cubren el caso sin parámetro, para que Sesiones y «sin permiso» no cambien.
- **[Tailwind no ve la plantilla]** → `rebrand.css` suma `@source "../../backend/templates/cuentas/ingresar.html"`; la prueba de la base que compara capas sigue en verde.

## Goals / Non-Goals

**Goals:**
- El ingreso sobre `base_rebrand.html` con la propuesta D, los mismos textos y la misma conducta.
- Los cinco estados (normal, error, campos vacíos, «Ingresando…» y aviso de inactividad) sin infracciones graves de axe en los dos temas y los dos anchos.

**Non-Goals:**
- Cambiar `ingresar.js`, la vista, el formulario o los mensajes de la vista.
- Borrar `componentes/campo.html`, `componentes/pie.html` ni Besley de `app.css` (paso 8 del PLAN; otras pantallas viejas aún los usan).

## Decisions

### D1. Página (`cuentas/ingresar.html`)

- Extiende `base_rebrand.html`; `titulo` igual que hoy; `scripts` carga `ingresar.js`; `precargas` (D5) precarga Besley. Sin barra ni ☰.
- `<main id="contenido" class="login">` con el orden del boceto: `.login-identidad` (`<div class="login-escudo" aria-hidden="true">` vacío, `<h1 class="login-ie">`, `.login-filete` decorativo, «Huayucachi», «Sesiones · Notas · Asistencia»), los mensajes, la ficha `.login-ficha` con el `<form>` (mismos atributos y ganchos: `method="post" novalidate aria-label="Iniciar sesión" data-formulario-ingreso`, CSRF y `next`), los dos campos, «Ingresar» con `rb/boton.html` principal `tipo="submit"` y `datos="boton-ingresar"` a todo el ancho, y la ayuda. La región `<p class="sr-only" role="status" data-estado-ingreso>` sigue fuera del formulario.
- Debajo, `rb/pie.html` con `solo_marca=True` (D3).
- El aviso de inactividad y el error general van entre la identidad y la ficha, en el mismo lugar y con el mismo ancho que la ficha.

### D2. Foco del error sin doble anuncio

- El error general es `rb/mensaje.html` de tipo error con `enfocar=True`: pinta `tabindex="-1"` y `autofocus`, **sin** `role="alert"`. Título: el primer error de `non_field_errors`; texto: «Revisa tus datos. Si el problema sigue, pide ayuda al administrador.».
- El navegador enfoca el mensaje al cargar y el lector lee su contenido una vez, como cualquier foco. Sin JavaScript funciona igual. `autofocus` se pinta solo con error; los campos no lo llevan.
- Alternativas descartadas: `role="alert"` más foco (JAWS lo lee dos veces; NVDA a veces ignora la alerta presente al cargar), y enfocar desde `ingresar.js` (lo cambia y falla sin JS).
- El borde de foco del mensaje es el anillo del rebrand (`:focus-visible` no salta con `autofocus` en todos los navegadores): el mensaje lleva `outline` con `:focus`, porque es la única forma de que la docente vea dónde quedó el foco.
- El aviso de inactividad sigue con `role="status"` y sin foco (cierre-sesion no cambia); con su ícono `clock` vía `icono="clock"`.

### D3. Componentes (`rb/`)

- **`rb/campo.html`** suma tres parámetros opcionales:
  - `mostrar_clave`: envuelve el `<input>` en `.input-grupo` y agrega el botón del ojo con los atributos actuales (`type="button" data-mostrar-clave aria-controls aria-pressed="false" aria-label="Mostrar contraseña" hidden`) y los dos íconos de Lucide (`eye`, `eye-off`), de los que el CSS muestra uno según `aria-pressed`. 44 × 44 px dentro del campo, a la derecha; el `<input>` reserva su espacio.
  - `variante`: con `"ingreso"`, `.field--ingreso` (52 px de alto y fondo `--g-alt`).
  - `sin_correccion`: pone `autocapitalize="none" spellcheck="false"` (Usuario, como hoy).
  - Se conservan los `id` de Django y sus `_ayuda` / `_error`, y la contraseña nunca se reescribe.
- **`rb/mensaje.html`** suma `icono` (nombre de `templates/iconos/`; sin él, el de hoy) y `enfocar` (D2). El aviso de inactividad llega como un solo mensaje («título\n\ndetalle», de `middleware.py`); un filtro nuevo `partes_aviso` en `cuentas/templatetags/marco.py` lo parte en título y texto para `rb/mensaje.html`. El middleware y el mensaje no cambian.
- **`rb/pie.html`** suma `solo_marca`: solo «CarpetaDocente · 2026», centrado (`.footer--marca`). Sin el parámetro, el pie de hoy.
- Alternativa descartada: componentes propios del ingreso. decisiones.md pide ampliar `rb/campo.html`, y el ojo y el foco del mensaje pueden servirle a otra pantalla.

### D4. «Ingresando…» solo con CSS

- Sobre lo que ya pone `ingresar.js`: `[data-boton-ingresar][aria-disabled="true"]` toma fondo y borde `--folder` con texto `--ink` (no opacidad) y un `::before` con el indicador de giro (borde parcial en `currentColor`, 16 px, `aria-hidden` implícito por ser pseudoelemento). Los campos de `[aria-busy="true"]` con `read-only` toman borde punteado.
- El giro es una rotación continua de `transform`; con `prefers-reduced-motion: reduce` queda quieto (el fondo y el texto ya dicen el estado). No hay otra animación: el cambio de fondo es inmediato.
- Alternativa descartada: un `<span class="giro">` como el boceto. `ingresar.js` lo borraría al reescribir el texto.
- El estado del boceto (`?estado=ingresando`) se reproduce en las pruebas con el envío retenido (como la e2e actual del estado de envío).

### D5. Besley

- `@font-face` de Besley 600 latina en `rebrand/pantallas/ingreso.css`, con `font-display: optional` y la URL relativa de `dist/fuentes/` (como Instrument Sans en `base.css`). Solo `.login-ie` la usa: 40 px / 1,12 en PC y 30 px por debajo de 700 px, tracking −0,01em, color `--action`.
- `base_rebrand.html` suma `{% block precargas %}{% endblock %}` después de las precargas de Instrument Sans; solo `ingresar.html` lo llena con Besley. Otra pantalla del rebrand no la descarga: el navegador solo pide una fuente de `@font-face` cuando algún texto la usa.
- Alternativa descartada: precargar dentro del bloque `scripts` (funciona, pero confunde) o en `base_rebrand.html` (la bajaría cada pantalla).

### D6. CSS y pruebas

- `rebrand/pantallas/ingreso.css` (importado en `rebrand.css`): `.login*`, el `@font-face` y el estado de envío. En `rebrand/componentes.css`: `.input-grupo`, el botón del ojo, `.field--ingreso` y el foco de `.message[tabindex]`. En `rebrand/marco.css`: `.footer--marca`.
- Las pruebas que buscan por clase pasan a `for`/`id`, a los ganchos o a las clases nuevas (`.field-error`, `.message--aviso`); `test_ingresar_e2e.py` espera `dist/rebrand.css` en vez de `app.css`.

### Datos de la tesis

Ninguno nuevo: el ingreso guarda lo mismo que en US-001 (el registro de actividad no cambia).

## Risks / Trade-offs

- [`font-display: optional` en Slow 4G] → en la primera visita el nombre puede salir en Georgia; desde la segunda, en Besley. Se acepta: es lo que pide decisiones.md y evita el salto de letra.
- [`autofocus` en un `div` con `tabindex="-1"`] → lo cumplen Chrome, Edge, Firefox y Safari actuales; si un navegador lo ignora, el mensaje sigue arriba de la ficha y visible. La e2e lo prueba en Chromium.
- [El giro gira mientras dura el envío] → es un indicador de estado, no una transición de algo que hizo la docente; con movimiento reducido no gira.
- [La clase `boton-principal--enviando` queda sin estilo] → el JS la usa como marca interna; el CSS mira `aria-disabled`. Se anota para el paso 8 (renombrarla cuando se borre el marco viejo).

## Migration Plan

Sin migraciones. Para volver atrás basta con revertir los commits: vista y JS no cambian.
