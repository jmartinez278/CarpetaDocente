# Tasks

Notas es de alto riesgo (decisiones.md y la regla de notas): dos partes con su commit, A (estructura y CSS) y B (conducta de `notas.js`). Ninguna lleva revisor: no tocan modelos, migraciones, permisos ni qué datos personales se guardan o muestran. El primer commit de la rama (archivo de `rebrand-us-029`) ya está hecho (`d5c295a`); RNF-005 1.3.0, también (`3ba491c`).

Comandos: `uv run pytest src/backend/notas` (vistas y plantilla) y `uv run pytest -m e2e src/backend/notas/tests/test_hoja_e2e.py src/backend/notas/tests/test_borradores_e2e.py --browser chromium` (e2e, con el CSS compilado y `DJANGO_ALLOW_ASYNC_UNSAFE=true`).

## 1. Notas en el marco del rebrand

### Parte A: estructura, CSS y clases (alto riesgo)

- [x] 1.1 Prueba primero, `test_vistas_hoja.py` (D1, deltas «Periodo de la hoja» y «Sin periodo vigente»): en `#datos-notas`, `periodo.nombre` es «III bimestre» y cada `periodos[].nombre` está en romanos; antes del primer periodo, «El I bimestre empieza el 9 de marzo.»; el contexto trae todos los periodos del año para el selector. Luego la vista. Verificar: rojo y luego verde; `uv run pytest src/backend/notas`
- [x] 1.2 Prueba primero, `test_plantilla_hoja.py`: `hoja.html` carga solo `dist/rebrand.css` y `notas.js`, tiene un solo `<main>` (el del marco), la barra dice «Notas» y el ☰ marca Notas con `aria-current`; «1.º grado, sección A · 2026» y `<h1>` «Registrar notas». Luego `hoja.html` extiende `marco_rebrand.html`, nuevo `rebrand/pantallas/notas.css` con su `@import` y el `@source` de `templates/notas/hoja.html` y sus parciales en `rebrand.css`. Verificar: rojo y luego verde; pruebas de `notas`
- [x] 1.3 Prueba primero, `test_plantilla_hoja.py` (D1, delta «Periodo de la hoja»): `_selector_periodo.html` pinta un enlace por periodo editable a `?periodo=N&area=<área inicial>` con `data-periodo`, «III» y «Vigente», `aria-current="page"` en el visible y las fechas solo en `sr-only`; el futuro, `<span aria-disabled="true">` sin `href`; en vacaciones marca «II» con «Anterior». Las comprobaciones de `notas-periodo` («B3 · Vigente») pasan a esto. Luego el parcial. Verificar: rojo y luego verde; pruebas de `notas`
- [x] 1.4 Prueba primero, `test_plantilla_hoja.py` (delta «Áreas de la hoja»): la tira conserva `data-tira`, `data-area-pildora`, `aria-pressed` y la descripción del docente de curso; el enlace `data-ir-competencias` (ícono `list-checks`, «Competencias») queda fuera de `[data-tira]`. La comprobación de `<div class="notas-tira">` pasa a esto. Luego el marcado. Verificar: rojo y luego verde; pruebas de `notas`
- [x] 1.5 Prueba primero, `test_plantilla_hoja.py` (D5): siguen todos los `id` y `data-*` que lee `notas.js` (inventario con grep: `hoja`, `superficie-hoja`, `barra-guardar`, `guardar`, `estado-guardado`, `faltantes`, `alcance`, `panel-*`, `nota-*`, `conclusion-*`, `confirmar-*`, `lista-niveles`, `competencia-detalle`, `rellenar-movil`, `data-borrador`, `data-rango`, `data-anuncio`, `data-alerta`…); `#barra-guardar` queda fuera de `#hoja`; la leyenda bajo la hoja; «Rellenar vacías» y «¿Salir sin guardar?» sobre `rb/dialogo.html` con sus `id`, `autofocus` y orden del DOM; `#rellenar-movil` sin la clase de solo celular; el `noscript` «Activa JavaScript para registrar las notas.» con `rb/mensaje.html`. Luego las plantillas. Verificar: rojo y luego verde; `uv run pytest src/backend/cuentas/tests/test_componentes_rb.py` y pruebas de `notas`
- [x] 1.6 Prueba primero, `test_hoja_e2e.py` y `test_borradores_e2e.py`: los localizadores por clase (`.notas-tabla`, `.notas-nivel`, `.notas-celda-movil`, `.notas-comp__boton`, `.notas-nota`, `.notas-invalida`, `.notas-tira`, `.notas-periodo`) pasan a `data-*`, rol o las clases nuevas; «B2 · Anterior» pasa al selector y `#alcance` a «Matemática · III bimestre»; con eso fallan. Luego, en `notas.js`, solo nombres de clase, fragmentos que pinta y el texto de `#alcance` (D5). Verificar: rojo y luego verde; e2e de notas sin cambios de lógica
- [x] 1.7 `notas.css`: encabezado con el selector, tira con Competencias fijo, tarjeta del área con «Rellenar vacías», hoja a todo el ancho (nombre cerca del 40 %, en MAYÚSCULAS), cabecera `sticky` con `top: var(--bar-height)`, `overflow: clip`, celdas con icono de conclusión y marca de cambio, panel con niveles de 64 px, recuadro, barra café fija al pie; `--alto-barra` medida con `ResizeObserver` en `notas.js` para `scroll-padding-bottom` y el `padding-bottom` de la hoja, con `safe-area-inset-bottom`, y se retira `--extra-hoja` (D5). Prueba primero, `test_hoja_e2e.py`: en `test_escribir_el_nivel_baja_a_la_misma_competencia_del_siguiente`, a 360 px, con Tab hasta la última fila la celda con el foco queda por encima de la barra. Verificar: rojo y luego verde; e2e de notas
- [x] 1.8 Pantalla vista en claro/oscuro y celular/escritorio, con cambios sin guardar, con el rechazo, con el panel y con el recuadro (la marca Marco). `verificar.py` y commit

### Parte B: conducta de `notas.js` (alto riesgo)

- [ ] 1.9 Prueba primero, `test_borradores_e2e.py` (D1, delta «Periodo de la hoja», escenarios «Elegir otro periodo» y «Cambiar de periodo conserva el borrador»): con una nota sin guardar en Matemática del III, elegir «II» abre la hoja de Matemática del II sin «¿Salir sin guardar?» ni aviso del navegador; volver a «III» muestra la nota como cambio sin guardar. Y en `test_sin_almacenamiento_la_hoja_guarda_igual` (escenario «Cambiar de periodo sin almacenamiento»): con la nota sin guardar, elegir «II» abre «¿Salir sin guardar?» y «Seguir editando» la conserva. Luego `dibujarPildoras()` (área en `[data-periodo]`) y el interceptor de enlaces. Verificar: rojo y luego verde; e2e de borradores
- [ ] 1.10 Prueba primero, `test_hoja_e2e.py` (D5, escenario «Área activa a la vista»): a 360 px, la hoja abierta en Personal Social muestra su píldora entera dentro de la tira y el acceso a Competencias a la vista. Luego el `scrollIntoView` al abrir. Verificar: rojo y luego verde; e2e de notas
- [ ] 1.11 Prueba primero, `test_hoja_e2e.py` (D2, escenario «Columnas que no caben»; hallazgos 1 y 3): a 360 px, Personal Social con 5 competencias: `[data-columnas]` se desplaza y la página no; tras llevarlo hasta C5, la cabecera C5 y su celda quedan alineadas y el nombre sigue a la vista; al bajar la página, la cabecera queda bajo la barra superior; tocar C1 muestra `#competencia-detalle` entero en la ventana. Luego `[data-columnas]`, la columna del nombre fija, `scroll-padding-left`, el `translateY` de la cabecera, la señal del borde, y se retira `notas-tabla--apilada`. Verificar: rojo y luego verde; e2e de notas
- [ ] 1.12 Prueba primero, `test_hoja_e2e.py` (D3, escenario «Recuadro en la última columna»; hallazgo 2): a 1280 px, en un área con una sola competencia marcada, elegir «B» abre el recuadro entero dentro de la ventana y junto a la celda; Escape lo cierra y el foco vuelve a la celda. Luego la colocación al lado de la celda. Verificar: rojo y luego verde; e2e de notas
- [ ] 1.13 Prueba primero, `test_hoja_e2e.py` (D3, escenario «Vista previa de la conclusión»): a 1280 px, el foco en el icono de una conclusión anotada muestra `#nota-previa` con su comienzo y el icono la referencia con `aria-describedby`; Escape la cierra y el foco sigue en el icono. Luego `#nota-previa` y sus eventos, sin el `title` del icono. Verificar: rojo y luego verde; e2e de notas
- [ ] 1.14 Prueba primero, `test_hoja_e2e.py` (D4, delta «Nivel en el celular»): a 360 px, elegir «B» en C1 sin conclusión y pulsar «Siguiente ↓» muestra al estudiante siguiente en C1; al cerrar el panel, la celda del primero dice «B» con «Falta conclusión». Y (delta «Rellenar vacías») `test_rellenar_vacias_solo_toca_las_vacias_y_queda_como_borrador` usa `#rellenar-movil` y elige C1 en `#elegir-columna` a 1280 px. Luego el manejador de `#siguiente` y `abrirRelleno` (D5). Verificar: rojo y luego verde; e2e de notas
- [ ] 1.15 Axe y desplazamiento (delta «Hoja accesible…»): `test_axe_con_notas_errores_filtro_y_dialogo` suma la vista previa en su rama de 1280 px y el diálogo de «Rellenar vacías»; `test_personal_social_no_desplaza_la_pagina_y_la_tira_se_desplaza_sola` sigue a 320 y 360 px con el marco nuevo; `test_las_areas_tactiles_miden_44_px` mide píldoras, celdas y niveles del panel por `data-*` o rol, y suma el acceso a Competencias y «Rellenar vacías». Retirar las e2e de la lista de abajo si Marco las aprueba. Luego los ajustes de contraste o foco en `notas.css`. Verificar: e2e de notas en verde
- [ ] 1.16 Pantalla vista en claro/oscuro y celular/escritorio con Personal Social desplazada, el recuadro en la última columna, la vista previa y el cambio de bimestre (la marca Marco). `verificar.py` y commit

## 2. Cierre

### Parte C: A2 y verificacion.md

- [ ] 2.1 `-m e2e` completo una vez y `verificar.py --completo` (80 % o más). Con la A2 que corre el usuario (`/codex:adversarial-review --base main --background`, con foco en la spec `registro-notas` del cambio y en D1–D5), corregir los Critical e Important con la prueba primero. Verificar: `verificar.py --antes-del-commit` en verde
- [ ] 2.2 `verificacion.md` corta: DoD 1 a 9, escenarios del delta sin prueba con su motivo y los Minor. Verificar: commit

## e2e a retirar (esperan la aprobación de Marco)

- `test_axe_en_vacaciones` y `test_axe_sin_periodos` (8 casos): son estados sin boceto, no diálogos; el escenario «Axe en ambos temas» queda en el estado principal, el panel, el rechazo, los diálogos, el recuadro y la vista previa.

Se conserva `test_las_areas_tactiles_miden_44_px` (decidido por Marco en el propose): los 44 px son una restricción de la spec y de US-020, no una forma del boceto. Se ajusta a los ganchos nuevos en 1.15.

## Ajustes del propose a decisiones.md

Regla que aplica este cambio (Marco, 13-11-2026): **el boceto manda en la forma** (dónde está cada cosa y cómo se ve); **las restricciones de US-020, US-021 y US-022 se conservan** (qué se puede hacer, con qué límites y qué se protege). Una decisión vieja de forma que choca con el boceto se deja; su restricción sigue.

- Punto 3: el selector son **enlaces** que recargan la hoja (`?periodo=N&area=…`), no botones con todos los periodos en memoria; conserva los borradores porque ya viven en el dispositivo por periodo (D1).
- Punto 5 y spec «Rellenar vacías»: un solo botón en la tarjeta, en todos los anchos, con la elección de la competencia; salen los botones por columna (delta; decidido por Marco en el propose).
- Punto 6: la cabecera sincronizada es el mismo `<thead>`, que se mueve con `translateY` solo cuando las columnas no caben (D2).
- Punto 11: «Faltan N notas» sigue filtrando la hoja (spec «Pendientes de registro», US-022 D5); no es un enlace a la primera faltante (D5).
- Punto 15: además de clases y marcado, `notas.js` cambia en lo que piden los deltas: enlaces de periodo sin diálogo (D1), cabecera y señal del contenedor horizontal (D2), colocación del recuadro y vista previa (D3), «Siguiente ↓» (D4), píldora activa a la vista, `--alto-barra` y el foco de «Rellenar vacías» (D5).

## Workflow follow-up

- **(push)** Al cerrar este cambio, push de `feature/rebrand` con aprobación; sigue el PR borrador único hacia `main`.
- **(paso 8)** Borrar de `app.css` el CSS de notas (`.vista-notas`, `.notas-*`, `.comp-dialogo` si ya no lo usa nadie) y retirar `PeriodoDeLaSeccion.nombre` («B3») si ninguna pantalla lo usa.
- **(auditoría visual)** 64 px de los niveles del panel, el `translateY` de la cabecera en un celular lento y los textos de DESIGN.md C-04 frente a los de la spec.
- **(RNF-005)** Prueba manual en Firefox de la tira y de las columnas desplazables (fila de verificación de RNF-005, antes del piloto).
- **(pulido final)** Sigue la deuda P3 de US-020/021/022: lector de pantalla real y teclado español físico. Y «Siguiente ↓» no vuelve a las celdas saltadas, que con D4 incluye las B/C sin conclusión: se encuentran con «Ir a la primera conclusión pendiente» al guardar.
- **(T-04)** El lugar del botón de tema en la barra queda vacío.
- Al proponer el paso 7 (Inicio de la dirección), su primer commit archiva este con `/opsx:archive` y «Sync now».
