# Design: rebrand de Competencias (US-029)

## Context

- Decisiones cerradas en `insumos/rebrand-competencias/decisiones.md`; boceto `insumos/rebrand/competencias.html` (lo pinta `assets/pagina-competencias.js`) y `capturas/competencias-*`, `estado-competencias-*`. Aquí solo va lo que se aparta del boceto o de DESIGN.md, o toca conducta.
- Hoy `competencias.html` extiende `marco.html`, trae su propio `<main class="vista-competencias">` y carga `app.css`. `competencias.js` toma `raiz.closest("main")` (ahí pone `aria-busy`), y depende de clases: `.comp-area` y `comp-area--curso`, `.comp-competencia` y sus modificadores `--notas`/`--anual`, `.comp-capsula`, `.comp-navegacion`, `comp-motivo`, `mensaje__texto`, `comp-guardado--*` y `boton-principal--enviando`; el corte es `matchMedia("(max-width: 959px)")`.
- Los nombres «B*n*»/«T*n*» salen de `PeriodoDeLaSeccion.nombre` (`notas/servicios.py`), que también usa la hoja de notas; la hoja no se toca hasta el paso 6. `competencias.js` deriva la palabra del periodo de `nombre_largo` («Bimestre 4»).
- El JS ya devuelve el foco al botón del periodo elegido (`boton.focus()` sin reemplazar los botones): C-02 era un fallo del prototipo, no del repo; aquí solo gana su prueba.
- `rb/dialogo.html` pone `aria-describedby` solo con `descripcion` (un `<p>` de la cabecera). `.dialog-acciones` ya invierte el orden visual: el principal va primero en el DOM.

## Riesgos y zonas delicadas (primero)

- **[El JS depende de clases y textos]** → D3: se cambian solo selectores, nombres de clase, textos y fragmentos que pinta; las e2e de conducta (borradores, bloqueos, guardado, 400/409, red caída, sesión vencida, 403, salida) corren sin tocar su lógica.
- **[La barra fija de abajo tapa la fila con el foco en el celular]** → D4: `scroll-padding-bottom` con el alto de la barra y una e2e de foco con Tab a 360 px.
- **[La hoja de notas cambia sin querer]** → D1: los romanos son propiedades nuevas; `nombre` («B3») sigue igual para la hoja.
- **[Salir por el ☰ con cambios]** → el cajón del menú es un `<dialog>` modal; «¿Salir sin guardar?» se abre encima con `showModal()` (capa superior), sin cambio en el JS. La e2e de salida se repite una vez desde un enlace del ☰.

## Goals / Non-Goals

**Goals:** la pantalla del boceto sobre `marco_rebrand.html` y `rebrand.css`, con los mismos ganchos, `id` y conducta, y los textos de los deltas.

**Non-Goals:** cambiar borradores, guardado, bloqueos, obligatorias o la salida; tocar rutas, modelos o reglas de `servicios.py`; renombrar los periodos de la hoja de notas (paso 6).

## Decisions

### D1. Romanos en dos propiedades del periodo

- `PeriodoDeLaSeccion` gana dos propiedades de solo lectura: `romano` («IV», del número) y `nombre_romano` («IV bimestre», con la palabra de `nombre_largo`). `nombre` y `nombre_largo` no cambian; Notas las usará en el paso 6. Alternativa descartada: cambiar `nombre`, que renombraba la hoja de notas antes de su paso.
- La vista pasa al `json_script` de cada periodo `nombre` = `nombre_romano` y `corto` = `romano`; `nombre_largo` sigue igual, así `competencias.js` sigue sacando «bimestre» de él. Con eso los textos que el JS arma con `periodo.nombre` salen solos: «Guardado · IV bimestre», «20/21 para el IV bimestre», «Registrar notas del IV bimestre», la lista de la salida y los anuncios.
- En el servidor: botones «I»–«IV», «IV aún no tiene competencias confirmadas», «Puedes revisar y corregir las competencias del I y II bimestre» (`periodos_elegibles` en romanos) y «El I bimestre empieza el 9 de marzo.» (antes del primer periodo), para no mezclar «B1» y «I» en la misma pantalla.

### D2. Botón del periodo: fechas en el nombre accesible, sin `aria-label`

- Contenido del botón: `<strong>IV</strong><span class="sr-only"> bimestre,</span> <span data-estado-periodo>Vigente</span><span class="sr-only">, del 13 de octubre al 19 de diciembre</span>`. El nombre accesible es «IV bimestre, Vigente, del 13 de octubre al 19 de diciembre» y contiene el texto visible (WCAG 2.5.3).
- Alternativa descartada: el `aria-label` del boceto. Taparía el «Sin guardar» que `competencias.js` escribe en `data-estado-periodo` (spec «Borradores por periodo»), y mantenerlo pedía lógica nueva en el JS.
- `data-fecha-periodo` se conserva como `<span hidden>`: el JS le sigue escribiendo las fechas y nadie las ve, como pide la decisión 4. La ayuda «Puedes volver a los bimestres anteriores.» y el `<h2>` «Bimestre» del selector salen (el boceto no los tiene); el grupo conserva su `aria-label` «Bimestres de 2026».

### D3. `competencias.js`: clases, textos y fragmentos que pinta

Solo cambia esto; el resto del archivo queda igual:

- Corte: `(max-width: 899px)` (delta «Marcado en el celular y en la PC»).
- Clases: `.comp-competencia` → `.comp-fila`, sus modificadores → `comp-fila--notas`/`comp-fila--anual`; `.comp-navegacion` → `.comp-capsula` (el `<nav>` del boceto es la cápsula); `comp-motivo` → `motivo` (y `motivo--anual`); `mensaje__texto` y `comp-nota__titulo` → `message-texto` y `message-titulo`; `boton-principal--enviando` y `comp-guardado--*` → sus nombres del rebrand. `.comp-area` y `comp-area--curso` se quedan (el boceto usa los mismos).
- Total: `data-conteo` pasa a «20/21» y `data-conteo-periodo` a «para el IV bimestre», ambos con `aria-hidden`; un `data-conteo-lector` nuevo, `sr-only`, dice «20 de 21 para el IV bimestre»; un `<progress data-progreso>` decorativo (`aria-hidden`) toma el mismo valor.
- Celular: la ayuda usa `periodo.corto` («IV · 20 de 21 en total»).
- Aviso del último periodo: título «IV bimestre: último del año», texto del boceto e ícono de alerta. El de periodo anterior conserva «Estás revisando un bimestre anterior» sin las fechas del boceto (decisión 4).
- Salida: en lugar de una frase, el JS llena `<ul data-pendientes>` con un `<li>` por periodo («II bimestre», «III bimestre»).

### D4. Una sola tarjeta café que se vuelve barra

- El lateral (`aside`, 320 px; 280 px hasta 1100 px; fijo al bajar) contiene la tarjeta café «Tu selección» y, fuera de ella, «Registrar notas del IV bimestre →». Hasta 899 px la misma tarjeta es la barra fija de abajo: quedan el estado, la ayuda (el total del celular) y «Guardar»; se ocultan el título, el total grande, la barra de avance, «Las áreas del docente de curso…» y los bloqueos. No hay segunda copia de `#guardar` ni de `data-guardado` (patrón 1).
- «Deshacer cambios» no está en la barra del boceto, pero la spec lo pide en todos los anchos: en el celular aparece en una segunda fila de la barra solo cuando hay cambios.
- El enlace «Registrar notas del …» queda en el flujo del `aside`, que en una columna cae después de la lista: el celular lo ve al pie del área (el boceto no lo muestra en el celular; la spec lo pide).
- `html` lleva `scroll-padding-bottom` con la altura real de la barra: el token de una fila, y el de dos filas cuando se ve «Deshacer cambios» (`:has(#deshacer:not([hidden]))`, solo CSS, sin cambio en el JS).
- Encabezado: enlace «‹ Registrar notas» a la hoja (`url_notas`, sin consulta), sección y año, `<h1>` «Competencias del bimestre» (o «del trimestre»), instrucción por ancho; el selector a la derecha y debajo en el celular.

### D5. Diálogo y estados sin boceto con `rb/`

- «¿Salir sin guardar?» usa `rb/dialogo.html` (variante chico) con `id="confirmar-salida"`, `titulo_id="titulo-salida"`. El cuerpo es `<div id="texto-salida"><p>Tienes cambios pendientes en:</p><ul data-pendientes></ul><p>Si sales, estos cambios se pierden.</p></div>`. `rb/dialogo.html` gana un `descrito_por` opcional (pone `aria-describedby` sin el `<p>` de la cabecera); sin él, su HTML no cambia. El pie tiene `#seguir-editando` (principal, `autofocus`) y luego `#salir-sin-guardar` en el DOM: el bucle de Tab del JS y el orden visual del boceto (`.dialog-acciones` lo invierte) se mantienen. El JS sigue llamando `showModal()` sin enfocar el título.
- Sin periodos: `rb/estado_vacio.html` con título «La dirección aún no configura los periodos» y su texto. Vacaciones y antes del primer periodo: `rb/mensaje.html` de aviso en un envoltorio `data-aviso`; «Elige un bimestre anterior» con `rb/estado_vacio.html` en un envoltorio `data-vacio`. «IV aún no tiene competencias confirmadas» en un envoltorio `data-aviso-sin-marcas`; el `noscript`, también `rb/mensaje.html`.
- Falla de red y sesión vencida: los textos de hoy, junto a «Guardar» dentro de la tarjeta (o la barra). Sin el rebote de la fila bloqueada (E-01): el bloqueo se explica con el motivo y el anuncio.

### Datos de la tesis

Ninguno nuevo: el rebrand no cambia qué se guarda.

## Risks / Trade-offs

- [La barra crece a dos filas con «Deshacer cambios» y tapa más lista] → solo con cambios; el `scroll-padding-bottom` sigue la altura real de la barra y la e2e de foco lo comprueba con «Deshacer cambios» a la vista.
- [DESIGN.md C-04 trae textos del prototipo («Sin guardar · confirma la selección», «Guardado a las <hora>»)] → mandan los de la spec y los de hoy; va a la deuda para la auditoría visual.
- [«Estás revisando un bimestre anterior» pierde las fechas que el boceto ponía] → la decisión 4 las saca de la vista; siguen en el nombre accesible del botón.

## Migration Plan

Sin migraciones. Volver atrás es revertir el commit; el CSS viejo de competencias sigue en `app.css` hasta el paso 8.
