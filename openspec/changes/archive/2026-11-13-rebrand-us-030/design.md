# Design: rebrand de Asistencia (US-030)

## Context

- Decisiones cerradas en `insumos/rebrand-asistencia/decisiones.md`; boceto `insumos/rebrand/asistencia.html` y `capturas/estado-asistencia-*`. Aquí solo va lo que se aparta del boceto o de DESIGN.md, o toca conducta.
- Hoy `hoy.html` extiende `marco.html` y pinta el resumen **dos veces**: la franja fija del celular (`.controles .franja-jornada`) y el panel de PC (`_panel.html`); `asistencia.js` actualiza todas las copias por `data-*`.
- `asistencia.js` depende de cuatro selectores de clase: `.vista-asistencia` (`closest`, y ahí pone `jornada-completa` y `cierre-animado`), `.panel-jornada .leyenda .estado` (moldes de los círculos), `.estudiante__nombre` (nombre de la fila para `aria-label` y «Falta guardar») y `[data-cierre] .icono`; además asigna `className = "guardado guardado--…"`.
- `rb/estado_vacio.html` solo recibe `texto`; las dos vistas vacías de la spec tienen título y texto.

## Riesgos y zonas delicadas (primero)

- **[El JS depende de clases]** → D3: se cambian solo selectores y nombres; las e2e de conducta (cola, reintentos, lote, pausa, aviso al salir, cierre, sesión vencida) corren sin tocar su lógica.
- **[Resumen fijo que tapa filas o foco en el celular]** → D1: la e2e de «N sin marcar» y una nueva de foco con Tab comprueban que el círculo queda debajo del resumen.
- **[Conteo accesible desactualizado o leído dos veces]** → D2: una sola copia accesible, con el mismo `data-marcados` que ya pinta el JS.

## Goals / Non-Goals

**Goals:** la pantalla del boceto sobre `marco_rebrand.html` y `rebrand.css`, con los mismos ganchos, `id`, textos y conducta.

**Non-Goals:** cambiar la cola de guardado, los reintentos, el lote, la pausa, el aviso al salir o el anuncio del cierre; tocar vistas, servicios o rutas.

## Decisions

### D1. Una sola tarjeta café, que se reacomoda por ancho

- La tarjeta «Tu jornada» existe una vez en el DOM (patrón 1): lateral fijo al bajar en PC; hasta 699 px, resumen compacto `position: sticky` bajo la barra (una fila: conteo y estado del guardado, más la barra de avance), con los totales y la leyenda ocultos. Desaparecen `.controles`, `.franja-jornada` y `_panel.html`. Alternativa descartada: conservar la franja y el panel, que ponía dos acentos café en el DOM y duplicaba el texto accesible.
- «Marcar los N restantes como Asistió» va dentro de la tarjeta en PC (botón principal claro sobre café) y como botón secundario debajo de la tarjeta en el celular, como el boceto; son dos `data-marcar-todos` y el CSS muestra uno por ancho (el JS ya pinta y enfoca el visible).
- «Sin conexión» (`rb/mensaje.html`, error) va en el flujo justo debajo de la tarjeta, no dentro del resumen fijo, para que el alto fijo no crezca.
- Las filas llevan `scroll-margin-top` igual a la barra más el alto máximo del resumen compacto (dos renglones, cuando el cierre baja de línea), en un token de la pantalla.
- El selector de la semana pasa de la tarjeta al encabezado de la hoja de la lista, como el boceto.

### D2. Conteo visible y texto accesible

- PC: `<span aria-hidden="true"><strong data-marcados>18</strong>/25 marcados</span>`; celular: `<span aria-hidden="true"><span data-marcados>18</span>/25 ·</span>` seguido del enlace. El CSS muestra una variante por ancho.
- Una sola copia accesible en la tarjeta: `<span class="sr-only"><span data-marcados>18</span> de 25 marcados</span>`. El JS ya actualiza todos los `data-marcados`, sin cambios.
- «7 sin marcar» sigue siendo el enlace `data-sin-marcar` que lleva a la primera fila Sin marcar (en el boceto del celular es texto): en PC bajo la barra de avance, con la flecha; en el celular, dentro de la fila del conteo. Así el lector oye «18 de 25 marcados» y el enlace «7 sin marcar», y en el celular la docente ve «18/25 · 7 sin marcar».

### D3. `asistencia.js`: solo selectores y nombres de clase

- `closest(".vista-asistencia")` apunta al contenedor nuevo de la pantalla (dentro del `<main>` del marco), que conserva `jornada-completa` y `cierre-animado`.
- Los moldes salen de la leyenda lateral (`.leyenda--lateral .estado`). La leyenda gana el círculo Sin marcar del boceto; el bucle de moldes lo admite sin cambio de lógica (queda una clave sin uso) y el molde `""` del JS se mantiene.
- El nombre de la fila es `<span class="estudiante__nombre"><strong>APELLIDOS,</strong> NOMBRES</span>`, con el espacio fuera del `<strong>`: su `textContent` sigue siendo «APELLIDOS, NOMBRES». El estado en palabras va fuera de ese `span`.
- `guardado guardado--inicial|--error`, `estado estado--<clave>` y `.icono` del cierre conservan su nombre; el CSS nuevo los estiliza. No se añade lógica.
- `cierre-animado` ya no traza las franjas (el boceto no las tiene): el cierre aparece con un fundido de color de 140 ms (DESIGN.md, Movimiento), sin cambio en el JS.

### D4. Desvíos del boceto que manda la spec

- Con todos marcados, el avance da paso al resumen de totales («Asistió: 21 · Tarde: 1 · Faltó: 2 · Justificado: 1») y a «✓ Asistencia de hoy completa», con el título «Jornada completa»; no se muestra el «12/12 · 0 sin marcar» del boceto (spec «Totales del día» y lógica del JS, que oculta el avance en cero).
- Durante la cuenta del lote el estado del guardado dice «Pendiente de deshacer», no «6 sin guardar» (spec «Estado del guardado»).
- Las flechas del selector siguen siendo botones con `aria-disabled` y su nombre (en el boceto son íconos sueltos), y los días conservan las etiquetas del repo (spec «Selector de la semana»).

### D5. Estados sin boceto con `rb/`

- `rb/estado_vacio.html` gana un `titulo` opcional (un `<p>` más, antes del texto); sin él, el HTML de Sesiones no cambia. Fin de semana: el selector de la semana que pasó y el vacío «Hoy no hay clases» / «La asistencia se registra de lunes a viernes.». Sección sin estudiantes: «Tu sección aún no tiene estudiantes» / «Agrégalos para poder tomar asistencia.» con la acción «Ver estudiantes» (`href` a la lista).
- `data-sin-conexion hidden` va en un envoltorio de `rb/mensaje.html`, que no recibe atributos.
- El fallo de la fila conserva `#fallo-<pk>` bajo el estado, con el ícono de alerta.

### Datos de la tesis

Ninguno nuevo: el rebrand no cambia qué se guarda.

## Risks / Trade-offs

- [El enlace «7 sin marcar» en el celular se ve como enlace y no como texto] → se pinta con el color de la tinta café y subrayado; conserva un atajo que ya tenía la docente.
- [Alto fijo del resumen en el celular] → con letra grande el cierre puede ocupar más de dos renglones; la e2e de foco lo detecta a 360 px y el token se ajusta.
- [Se pierde el trazo del cierre] → el texto «✓ Asistencia de hoy completa» y su anuncio no cambian.

## Migration Plan

Sin migraciones. Volver atrás es revertir el commit; el CSS viejo de asistencia sigue en `app.css` hasta el paso 8.
