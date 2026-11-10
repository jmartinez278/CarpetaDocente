# Design: rebrand de la Portada del docente

## Context

- Decisiones cerradas en `insumos/rebrand-portada/decisiones.md`; boceto `insumos/rebrand/index.html`; norma DESIGN.md 1.1 (Layout «Portada», patrones 1 y 3). Marco y componentes en `openspec/changes/archive/2026-11-09-rebrand-base/`; diálogo de la lista en `…/2026-11-10-rebrand-us-006/` (D3, D8). Lo nuevo de este propose está en `proposal.md`.
- Hoy `cuentas/portada_docente.html` extiende `marco.html` (`app.css`), carga `portada.js`, `alpine.min.js`, `htmx.min.js` y `estudiantes.js`, y pinta `<main class="portada" x-data="carrusel">` con chips, la pista `data-carrusel` (`role="region"`, «Tus accesos»), los puntos y `<dialog class="modal-estudiantes" id="estudiantes">`.
- `componentes/tarjeta_dimension.html` usa Alpine (`x-data="proxima"`, `@click`, `x-text`, `:class`) y clases del carrusel (`carrusel__item`, `--inicial`, `--asoma`). Solo la usa la portada, igual que `componentes/miniatura_*.html`.
- `cuentas/dimensiones.py`: `DIMENSIONES` en el orden Sesiones, Notas y Asistencia, con `subtitulo` (solo lo lee la tarjeta). `tarjeta_inicial` solo sirve al carrusel. `navegacion_docente` tiene su propio orden (`ORDEN_NAVEGACION`) y no lee `subtitulo`.
- `PortadaDocenteView` arma `dimensiones`, `inicial`, `saludo`, `fecha`, `secciones`, `entrada` y `pendiente_hoy`.
- `marco_rebrand.html`: el bloque `navegacion` trae el ☰ por defecto; `.appbar` es `position: sticky` (`rebrand/marco.css:53`). Alpine solo se usa en la portada.
- `institucion/tests/test_estudiantes_e2e.py` tiene 10 pruebas con `SALTO_DIALOGO` (motivo `rebrand-portada`).

## Riesgos y zonas delicadas (primero)

- **[Diálogo de Estudiantes sobre la portada nueva]** → D6: el A2 [high] de `rebrand-us-006` (la lista pierde el desplazamiento dentro del diálogo) se cierra aquí. Una e2e con más estudiantes de los que caben comprueba que el último «Editar» se alcanza. Las 10 e2e saltadas vuelven a correr.
- **[Orden de `DIMENSIONES`]** → D2: el ☰, `para_portada` y `test_dimensiones.py` iteran la tupla. El ☰ usa `ORDEN_NAVEGACION` y no cambia de orden; una prueba lo fija.
- **[«Próximamente» sin Alpine]** → D5: el aviso debe seguir anunciándose en cada toque y no mover la tarjeta. Se conserva la región `aria-live="polite"` vacía desde el inicio y el vaciado antes de escribir, y la e2e actual del aviso se mantiene.
- **[Animación de «Hoy: pendiente»]** → D7: la subida al cargar (US-030) no responde a una acción y DESIGN.md 1.1 (Movimiento) no la admite.
- **[Contraste de la tarjeta café]** → D4: el texto, la insignia y el foco sobre `--cocoa`, en los dos temas, los mide axe en todas las vistas de la spec.

## Goals / Non-Goals

**Goals:**
- La portada del docente sobre `marco_rebrand.html` y `rebrand.css`, sin `app.css` ni Alpine, con la misma conducta, rutas, `id` y ganchos (menos `data-carrusel`).
- El diálogo de Estudiantes con su estilo del rebrand dentro de la portada.

**Non-Goals:**
- El botón de tema (T-04): la barra le deja su lugar, vacío.
- El inicio de la dirección ni otras pantallas que aún usan `marco.html`.
- Cambiar banderas, rutas, servicios o la conducta de `estudiantes.js`.

## Decisions

### D1. Plantilla y variante de portada del marco

- `portada_docente.html` extiende `marco_rebrand.html`; `{% block navegacion %}{% endblock %}` vacío (sin ☰) y `titulo_barra` vacío. `<title>` igual que hoy.
- La barra de la portada no es fija (DESIGN.md, Layout «Portada»). `marco_rebrand.html` gana un bloque `clase_barra` (vacío por defecto) que la portada llena con `appbar--portada`; en `marco.css`, `.appbar--portada { position: static }`. Alto 72/64 px del `--bar-height` común. Alternativa descartada: un `marco_portada.html` aparte, que duplicaría el «Ir al contenido», la cuenta y el pie.
- Dentro de `principal`: `<div class="bienvenida">` con `<h1>` (saludo en `--text-greeting` y nombre en `--text-home`, en el mismo `<h1>`, como el boceto), la línea `{{ fecha }} · {{ secciones }}` en `<p>` (texto, sin estilo de enlace) y «Ver estudiantes» (`id="ver-estudiantes"`, `data-abrir-estudiantes`, `hx-get`, flecha, 44 px), luego el aviso `_aviso_portada.html` (ya en `rb/mensaje.html` desde `rebrand-us-006`).
- Las tarjetas van en `<nav class="accesos" aria-label="Tus accesos">`, en el orden de `dimensiones`. Desaparecen chips, puntos, `x-data="carrusel"` y `data-carrusel`; el `<main>` es el del marco (uno solo).

### D2. `dimensiones.py` y la vista

- `DIMENSIONES` pasa a Asistencia, Sesiones y Notas. `subtitulo` → `frase`, con las frases de decisiones.md, punto 5. Banderas, `url_name`, `verbo`, `icono` y `para_portada` sin cambios.
- Se borran `tarjeta_inicial` y `contexto["inicial"]`. `ORDEN_NAVEGACION` no cambia (Sesiones, Asistencia, Notas): el orden del ☰ es otra regla de la spec.
- Es un ajuste a «Se conserva» de decisiones.md (dimensiones.py y la vista): la regla de disponibilidad (punto 10) queda igual; cambian solo los datos que pinta la tarjeta y lo que pedía el carrusel.

### D3. Tarjeta (`rb/tarjeta_dimension.html`)

- `<article class="dimension dimension--<clave>[ dimension--proxima]" id="c-<clave>" aria-labelledby="dim-<clave>">`. Cabecera: ícono (24–30 px, DESIGN.md Íconos), `<h2 id="dim-<clave>">` con el enlace `dimension-enlace` estirado sobre la tarjeta (`::after`), y la flecha de esquina decorativa.
- Disponible: `<p class="dimension-frase" id="frase-<clave>">`, la píldora `#pend-asistencia` si corresponde y `<p class="dimension-accion" id="acc-<clave>">` con el verbo de la spec y `arrow-right.svg`. El enlace lleva `aria-describedby="acc-<clave>[ pend-asistencia]"`, como hoy. La frase no entra en la descripción: ya se lee en el orden del documento y alargaría cada anuncio.
- «Próximamente»: `<button class="dimension-boton" type="button" aria-disabled="true" aria-describedby="ins-<clave>" data-proxima>` con el título; `<p class="insignia insignia--callada" id="ins-<clave>">Próximamente</p>` (sin color de acción); la frase; `<p class="dimension-aviso" aria-live="polite"></p>` vacía. Sin verbo ni flecha.
- No se toman del boceto el `card-action` con «Tomar asistencia» / «Abrir…» (`aria-hidden`) ni el `<nav>` «Tus dimensiones»: se conservan el verbo con `id` y la etiqueta «Tus accesos».
- Se borra `componentes/tarjeta_dimension.html`.

### D4. Rejilla, tarjeta café y miniaturas (`pantallas/portada.css`)

- `.accesos`: desde 900 px, rejilla de 12 columnas; Asistencia `grid-column: span 7; grid-row: span 2`, Sesiones y Notas `span 5`. Hasta 899 px, una columna. Hasta 699 px, Sesiones y Notas compactas: miniatura a la derecha del texto en una rejilla `minmax(0,1fr) auto`. Todo con `min-width: 0` y `overflow-wrap: anywhere` en la frase.
- Tarjeta café: solo `.dimension--asistencia` usa `--cocoa` con su tinta (patrón 1). Las otras, `--card` con borde. La tarjeta en «Próximamente» conserva su superficie: si es Asistencia (sin sección única), sigue siendo café, porque el acento marca el lugar, no la disponibilidad.
- Miniaturas `rb/miniatura_{asistencia,sesiones,notas}.html` con los esquemas del boceto (tabla con la clave Asistió/Tarde/Faltó/Justificado y tres filas de línea, hoja con lápiz, escala AD/A/B/C), `aria-hidden`, con los tokens `--preview-*` fijos en los dos temas y la sombra `4px 4px 0 var(--preview-sand)`. Sin nombres, fechas ni marcas que se lean como registros. Se borran `componentes/miniatura_*.html`.
- Toque y foco: toda la tarjeta responde al enlace estirado; el anillo de foco es el del marco, sobre la tarjeta (`:has(:focus-visible)`). Hover solo con puntero fino (DESIGN.md Movimiento).
- `rebrand.css` suma `@import "./rebrand/pantallas/portada.css"` y `@source "../../backend/templates/cuentas/portada_docente.html"`.

### D5. `portada.js` sin Alpine

- Delegación en `document`: un clic en `[data-proxima]` busca la `.dimension-aviso` de su tarjeta, la vacía, escribe «Llegará en una próxima versión.» en el cuadro siguiente (`requestAnimationFrame`) y la vacía a los 3 s; un nuevo toque reinicia el reloj de esa tarjeta. Es la lógica de `Alpine.data("proxima")` sin la dependencia.
- La portada carga `portada.js`, `htmx.min.js` y `estudiantes.js` (`defer`), no `alpine.min.js`. Alpine sigue en `dist/vendor/` hasta el paso 8.
- El aviso ocupa un renglón reservado (alto mínimo fijo), así que aparecer o irse no mueve la miniatura.

### D6. Diálogo de Estudiantes

- `<dialog class="dialog dialog--lista" id="estudiantes" aria-labelledby="modal-titulo" aria-describedby="modal-cantidad" hx-target="this" hx-swap="innerHTML">`, solo con `entrada`. `estudiantes.js` no cambia.
- Se borran `SALTO_DIALOGO` y sus 10 marcas en `test_estudiantes_e2e.py`. Nueva e2e (A2 [high] de `rebrand-us-006`): con 40 estudiantes, el diálogo a 360 y 1280 px deja alcanzar y tocar el último «Editar» desplazando `#modal-cuerpo`, y la página de atrás no se desplaza (`body.con-dialogo`).

### D7. Movimiento

- Se quita la subida de entrada de «Hoy: pendiente» (US-030): no responde a una acción (DESIGN.md 1.1, Movimiento). Se borran sus dos e2e («aparece una vez con una subida corta», «con reducir movimiento ya está en su lugar») y una nueva comprueba que la píldora no tiene `animation`.
- Quedan: hover y pulsación de la tarjeta con puntero fino (sin mover la miniatura), y el fundido del aviso de «Próximamente» (opacidad, 140/200 ms), ambos con su versión de movimiento reducido.

### D8. Pruebas

- `test_dimensiones.py`: orden Asistencia, Sesiones y Notas con `frase` y verbo; el ☰ sigue en Sesiones, Asistencia y Notas; se borran las de `tarjeta_inicial`.
- `test_pantallas.py`: la portada solo carga `dist/rebrand.css` y no carga `alpine.min.js`; un `<main>`; sin ☰; barra con `appbar--portada`; tarjetas en orden en el HTML con su frase y sin los subtítulos formales; «Próximamente» con `data-proxima` y su región vacía; sin `chip`, `punto`, `data-carrusel` ni `carrusel__`; `id` conservados (`ver-estudiantes`, `estudiantes`, `pend-asistencia`, `c-`, `dim-`, `acc-`, `ins-`). Las comprobaciones por `dimension__*`, `.chips` y `.portada` pasan a ganchos e `id`.
- `test_portada_e2e.py`: se borran las del carrusel (chips, puntos, sin JS con chips, «una fila sin chips»); nuevas: orden visual igual al del DOM a 360 y 1280 px; Asistencia ocupa la columna principal a 1280 px; compactas con la miniatura junto al texto a 360 px; «Próximamente» avisa sin mover la miniatura (se mantiene, sin pasar por un chip); tokens leídos de `rebrand.css`; ancho a 320 y 360 px con la píldora y con el aviso.
- `test_accesibilidad_e2e.py`: las vistas de la portada del escenario «Revisión de cada pantalla», en ambos temas y anchos.
- `test_marco_rebrand.py`: el bloque `clase_barra` vacío por defecto no cambia el HTML de las otras pantallas.

### Datos de la tesis

Ninguno nuevo: la portada no guarda datos.

## Risks / Trade-offs

- [Barra no fija solo en la portada] → la cuenta queda arriba al desplazar; la portada es corta (DESIGN.md lo pide así).
- [Frase fuera de `aria-describedby`] → el anuncio del enlace es corto; la frase se lee al recorrer la tarjeta.
- [Tarjeta café en «Próximamente»] → sin sección única, la tarjeta principal no lleva a ninguna parte; la insignia callada y el aviso lo explican, como hoy.
- [Quitar la animación de la píldora] → se pierde una pista de que es nueva; la píldora sigue con ícono y texto.

## Migration Plan

Sin migraciones. Volver atrás es revertir los commits; rutas y servicios no cambian.
