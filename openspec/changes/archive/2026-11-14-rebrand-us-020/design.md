# Design: rebrand de Notas (US-020, US-021, US-022)

## Context

- Decisiones cerradas en `insumos/rebrand-notas/decisiones.md`; boceto `insumos/rebrand/notas.html` y `capturas/notas-*`, `estado-notas-*`. Aquí solo va lo que se aparta del boceto o de DESIGN.md, o toca conducta.
- Hoy `hoja.html` extiende `marco.html` y carga `app.css`. El servidor dibuja el marco (cabecera, tira, barra, diálogos, editor) y `notas.js` dibuja la rejilla desde `#datos-notas`. La vista abre **un** periodo por página: su `json_script` y su clave de borrador (`clave_borrador`, con el número del periodo) son de ese periodo; `pendientes()` ya lee del dispositivo los borradores de los otros periodos.
- `notas.js` usa como selectores estas clases: `.notas-tabla`, `.notas-nivel`, `.notas-nivel-grande`, `.notas-celda-movil`, `.notas-rellenar`, `.notas-panel__borrador`, `.notas-inactiva`; y pinta otras (`notas-nota`, `notas-pendiente`, `notas-invalida`, `notas-punto`, `notas-vacio`, `notas-corte`, `notas-tabla--apilada`, `mensaje*`…). Corte celular/PC: `(max-width: 959px)`.
- `#lista-niveles`, `#competencia-detalle` y `#nota-editor` ya son `position: fixed` y se colocan con `posicionar()`, que centra sobre la celda y limita a la ventana. El `scroll` se escucha en captura, así que también llega el de un contenedor interno.
- El boceto no desplaza columnas (ese fue el hallazgo 1) y su selector son botones con `aria-pressed` sobre datos de demostración.

## Riesgos y zonas delicadas (primero)

- **[Cabecera sticky dentro de un contenedor con `overflow-x`]** Un contenedor con desplazamiento horizontal pasa a ser el contenedor de `sticky` en los dos ejes: la cabecera C1…Cn deja de pegarse bajo la barra al bajar la página → D2.
- **[Cambiar de periodo sale de la página]** El interceptor de salida abriría «¿Salir sin guardar?» y el `beforeunload` el aviso del navegador → D1.
- **[Lógica de `notas.js` intocable salvo los deltas]** Las e2e de conducta (teclado de rejilla, borradores, dos pestañas, otro dispositivo, guardado, rechazo, 403, salida) corren sin tocar su lógica; solo D1–D4 la cambian, cada una con su prueba.
- **[Tamaño]** 1587 líneas de JS y una plantilla de 124: el trabajo va en dos partes con commit propio (estructura y CSS; conducta).

## Goals / Non-Goals

**Goals:** la pantalla del boceto sobre `marco_rebrand.html` y `rebrand.css`, con los mismos ganchos `data-*` e `id`, los arreglos de break-ui y los deltas de `registro-notas`.

**Non-Goals:** cambiar niveles, teclado de rejilla, borradores, dos pestañas, otro dispositivo, guardado, rechazo, faltantes o filtro; tocar rutas, modelos o `servicios.py`; cargar varios periodos en una página.

## Decisions

### D1. Selector de periodo: enlaces que recargan la hoja, sin diálogo

- Un parcial nuevo `notas/_selector_periodo.html` pinta un **enlace** por periodo editable (`?periodo=N&area=<código>`, `data-periodo`, `aria-current="page"` en el visible) y el futuro como `<span aria-disabled="true">` sin enlace. Mismo aspecto que el selector de Competencias (romano y estado; fechas solo en el texto `sr-only`). Alternativa descartada: botones del boceto con todos los periodos en el `json_script`, que multiplicaba el peso en Slow 4G y cambiaba la vista y la clave del borrador.
- `notas.js`: `dibujarPildoras()` actualiza el `area` de cada `[data-periodo]` como ya hace con `[data-ir-competencias]`; el interceptor de enlaces deja pasar `[data-periodo]` sin `pedirSalida` y pone `permisoSalida` para que `beforeunload` no avise, igual que «Salir sin guardar»; mientras `guardando`, el enlace espera como hoy («Espera a que termine el guardado.»). **Excepción:** si `almacenamiento` es falso (navegador sin almacenamiento, o «Cerraste sesión en otra pestaña»), los cambios solo viven en memoria y el enlace pasa por `pedirSalida` como cualquier salida; si no, se perderían sin aviso (borradores de US-020, decisión 13). Un periodo sin marcas guardadas lleva a Competencias (302 de la vista, US-020 D3), igual que hoy. No hace falta más: cada cambio ya se escribe en el dispositivo (`persistir`), y al volver `recuperarBorradores()` lo carga con su aviso «Cambios sin guardar del …».
- Romanos: la vista pasa `periodo.nombre_romano` a `datos.periodo.nombre` y a cada `datos.periodos[].nombre`, así los textos que arma el JS salen solos («Matemática · III bimestre», salida, relleno, panel); `_aviso(periodos, romanos=True)` como en Competencias. `nombre` («B3») queda sin uso en pantallas (follow-up, paso 8).

### D2. Columnas que no caben: contenedor horizontal y cabecera que sigue a la página

- La tabla va dentro de `[data-columnas]` con `overflow-x: auto` (la única excepción de RNF-005 además de la tira). La columna del nombre (`th` de fila y de cabecera) es `position: sticky; left: 0`, con ancho mínimo para 16 px; `scroll-padding-left` con ese ancho para que el foco de la rejilla (`scrollIntoView` con `inline: "nearest"`) no deje la celda bajo el nombre. Se retira `notas-tabla--apilada` (5 o más competencias bajo 360 px).
- Cuando la tabla cabe, la cabecera es `sticky` con `top: var(--bar-height)` (CSS, como el boceto). Cuando no cabe (`scrollWidth > clientWidth`, medido con `ResizeObserver`), el `<thead>` se desplaza con `transform: translateY(...)` al bajar la página (en `requestAnimationFrame`, limitado al alto de la tabla), y como está dentro del contenedor horizontal sigue a las columnas sin código de sincronización. Un solo `<thead>`: la rejilla, el foco y el lector no cambian. Alternativa descartada: una copia de la cabecera fuera del contenedor sincronizada por `scrollLeft`, que duplicaba botones y foco.
- Señal de «hay más»: sombra en el borde con `data-mas-izquierda` / `data-mas-derecha` según `scrollLeft`.

### D3. Recuadro y vista previa de la conclusión (T-02, hallazgos 2 y 3)

- El recuadro se coloca **al lado** de la celda: a la derecha si cabe en la ventana; si no, a la izquierda; alineado con la fila y limitado a la ventana. Es una variante de `posicionar()`; la lista de niveles y la ayuda de la competencia siguen con la de hoy. Al cerrar, el foco vuelve a la celda (ya lo hace `cerrarNota`).
- Vista previa: un `#nota-previa` (`role="tooltip"`, fijo, 2–3 líneas con recorte) que se abre con `pointerenter` y `focus` del icono `[data-nota]` cuando hay texto, con `aria-describedby` en el icono; sigue abierta mientras el puntero o el foco estén en el icono o en ella, sin temporizador; Escape la cierra sin mover el foco. Se quita el `title` del icono, que duplicaba la ayuda. Clic, Enter y Alt+Enter abren el recuadro como hoy. Solo en PC.
- El recuadro sigue a su celda al desplazar y se cierra conservando el texto si la celda sale de la vista (US-020 D12): el manejador de `scroll` suma los bordes de `[data-columnas]` y de la columna del nombre fija a los de arriba y abajo que ya mide. Hoy el modo desplazable solo ocurre en el celular, donde se usa el panel, así que no lleva e2e propia.
- La ayuda de la competencia (`#competencia-detalle`) ya es fija y limitada a la ventana: queda fuera del contenedor horizontal, así que no se recorta (hallazgo 3); lo cubre la e2e de D2.

### D4. «Siguiente ↓» no se detiene en una B/C sin conclusión

- El manejador de `#siguiente` deja de devolver el foco a la conclusión: avanza igual (también en el filtro) y anuncia con la región `polite` «Falta conclusión: <estudiante>, Cn.». La celda ya se pinta con el icono de faltante (`indicadorNota`), y el rechazo atómico de «Guardar» no cambia. Lo demás del panel sigue igual.

### D5. Marco, clases, barra y diálogos

- `hoja.html` extiende `marco_rebrand.html` (barra «Notas», ☰ con Notas marcado), carga solo `dist/rebrand.css`; CSS en `rebrand/pantallas/notas.css`. Encabezado: «1.º grado, sección A · 2026», `<h1>` «Registrar notas» y el selector de D1. La tira lleva el acceso `list-checks` «Competencias» fijo fuera de `[data-tira]`; al abrir, el JS lleva la píldora activa al tramo visible con el mismo `scrollIntoView` que ya usa al tocarla (hoy solo lo hace al tocar).
- En `notas.js`, solo nombres de clase y fragmentos que pinta (decisión 15): las clases selectoras pasan a las del boceto y las e2e usan `data-*` o rol; el corte `(max-width: 959px)` no cambia; `#alcance` dice «Matemática · III bimestre». Se conservan las etiquetas de celda «<estudiante>, <competencia>, <nivel>» de US-020 D12 (el boceto dice solo «C1: A») y la rejilla ARIA.
- «Faltan N notas» en la barra sigue siendo el botón que filtra («Pendientes de registro · <área>», foco en la primera faltante; US-022 D5), no un enlace que salta a la primera faltante como sugiere el punto 11 de decisiones.md: ese requisito no tiene delta.
- La barra café es `#barra-guardar`, fija al pie fuera de `#hoja`, una sola por pantalla; `html` lleva `scroll-padding-bottom` y la hoja `padding-bottom` con la altura real de la barra (`--alto-barra`, medida con `ResizeObserver`) más `safe-area-inset-bottom`. El cálculo de `--extra-hoja` (borrador y aviso) se retira: la hoja ya no tiene alto propio.
- «Rellenar vacías» (delta, decidido por Marco en el propose): queda solo `#rellenar-movil` en la cabecera de la tarjeta, en todos los anchos; los botones `[data-rellenar]` de cada cabecera Cn salen del marcado que pinta el JS. En `abrirRelleno`, `#columna-relleno` se muestra siempre (hoy solo en el celular) y el foco vuelve a `#rellenar-movil`; el resto del flujo no cambia.
- «Rellenar vacías» y «¿Salir sin guardar?» pasan a `rb/dialogo.html` (con `descrito_por`) conservando `id`, `autofocus` y orden del DOM; el panel del celular y el recuadro conservan su marcado e `id` con las clases del rebrand. Estados sin boceto con `rb/mensaje.html` y `rb/estado_vacio.html`.

### Datos de la tesis

Ninguno nuevo: el rebrand no cambia qué se guarda.

## Risks / Trade-offs

- [El `translateY` de la cabecera se mueve con la página y puede verse un salto en celulares lentos] → solo en modo desplazable y en `requestAnimationFrame`; si la auditoría visual lo ve, va a su deuda.
- [Volver a un periodo muestra el aviso «Cambios sin guardar del …»] → es la conducta de «Volver con un borrador» y dice la verdad; no se agrega lógica para ocultarlo.
- [Seis e2e nuevas (D1, D2, D3 ×2, D4 y el área activa a la vista)] → cada una cubre conducta de navegador de un delta; ninguna repite ancho ni tema.
- [DESIGN.md pide 64 px en los niveles del panel y la spec 44 px] → manda la spec como mínimo; los 64 px van al CSS y los revisa la auditoría visual.

## Migration Plan

Sin migraciones. Volver atrás es revertir los commits; el CSS viejo de notas sigue en `app.css` hasta el paso 8.
