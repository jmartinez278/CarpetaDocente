# Tasks

Ninguna parte es de alto riesgo: no toca modelos, permisos, transacciones ni notas; en `asistencia.js` solo cambian selectores y nombres de clase (D3), y decisiones.md no marca zonas de cuidado. Los nombres de estudiantes (RN-015) solo cambian de contenedor. El primer commit de la rama (archivo de `rebrand-portada`) ya está hecho (`4492ec3`).

Comandos: `uv run pytest src/backend/asistencia` (vistas) y `uv run pytest -m e2e src/backend/asistencia/tests/test_asistencia_e2e.py --browser chromium` (e2e, con el CSS compilado y `DJANGO_ALLOW_ASYNC_UNSAFE=true`).

## 1. Asistencia en el marco del rebrand

### Parte A: Asistencia (normal)

- [x] 1.1 Prueba primero, `asistencia/tests/test_vistas.py`: `hoy.html` carga solo `dist/rebrand.css` y `asistencia.js`, tiene un solo `<main>`, la barra dice «Asistencia» y el ☰ marca Asistencia con `aria-current`; encabezado con «2.º grado, sección A · 2026», `<h1>` «Asistencia de hoy» y la fecha de Lima; sin «Asistencia · 2.º A» en el `<h1>` (el `<title>` se conserva). Luego `hoy.html` extiende `marco_rebrand.html`, nuevo `rebrand/pantallas/asistencia.css` con su `@import` y el `@source` de `templates/asistencia` en `rebrand.css`. Verificar: rojo y luego verde; pruebas de vistas
- [x] 1.2 Prueba primero, `test_vistas.py`: una sola tarjeta café «Tu jornada» en el HTML, sin `.controles`, `.franja-jornada` ni `_panel.html`; dentro, el estado del guardado, `<progress data-progreso>`, los cuatro `data-total`, `data-cierre`, `data-resumen-completo` y dos `data-marcar-todos` (tarjeta y debajo de ella) (D1). Luego `asistencia/_tarjeta.html` y borrar `_panel.html` y `_resumen.html` si quedan sin uso. Verificar: rojo y luego verde; pruebas de vistas
- [x] 1.3 Prueba primero, `test_vistas.py`, escenario «Caso de error» (delta): con 18 de 25 marcados, el HTML trae «18/25 marcados» y «18/25 ·» con `aria-hidden`, una sola copia `sr-only` «18 de 25 marcados» con `data-marcados`, y dos enlaces `data-sin-marcar` «7 sin marcar» hacia la primera fila Sin marcar; la jornada sigue incompleta (D2). Las comprobaciones de `avance__largo` y `avance__corto` pasan a esto. Luego el marcado del conteo. Verificar: rojo y luego verde; pruebas de vistas
- [x] 1.4 Prueba primero, `test_vistas.py`: el selector va en la cabecera de la hoja de la lista con «Solo puedes marcar hoy.», hoy con `aria-current="date"` y los otros días y las flechas con `aria-disabled` (D4); la cabecera de la lista dice «25 estudiantes activos» y «Hoy». Luego `_selector.html` y la hoja en `hoy.html`. Verificar: rojo y luego verde; pruebas de vistas
- [x] 1.5 Prueba primero, `test_vistas.py`: cada fila conserva `id="fila-<pk>"`, `data-estudiante`, `data-estado`, `data-marcar` con su `aria-label`, `data-etiqueta`, `#fallo-<pk>`, `data-nota` y `#nota-<pk>`; el número va con dos cifras («01») y `aria-hidden`; el nombre es `<strong>APELLIDOS,</strong> NOMBRES` y su texto es «APELLIDOS, NOMBRES» (D3); el estado en palabras va fuera del nombre. Las comprobaciones por `class=` de `fila-asistencia`, `estudiante__numero`, `etiqueta-estado`, `nota-justificacion`, `opcional` y `estado--*` pasan a ganchos `data-*` o a las clases nuevas. Luego `_fila.html` y `_circulo.html`. Verificar: rojo y luego verde; pruebas de vistas
- [x] 1.6 Prueba primero, `test_vistas.py`: leyenda lateral «Cada toque cambia el estado» con los cinco estados (Sin marcar incluido) y «Después de Justificado, sigue Asistió. Una marca guardada ya no queda Sin marcar.»; leyenda plegable del celular en un `<details>` como el boceto. Luego `_leyenda.html`. Verificar: rojo y luego verde; pruebas de vistas
- [x] 1.7 Prueba primero, `test_vistas.py`: «Fuera del registro de hoy» va después de la última fila, con las marcas «RETIRADO» y «TRASLADADO» y sin círculo; la barra de «Deshacer» (`data-barra-deshacer`, `data-deshacer`, `data-segundos`) y `#anuncio` siguen en la página; «Sin conexión» va en un envoltorio `data-sin-conexion hidden` con `rb/mensaje.html` de error, justo después de la tarjeta (D1, D5). Las comprobaciones de `inactivos`, `marca-inactivo`, `barra-deshacer` y `.message--aviso` pasan a ganchos o clases nuevas. Verificar: rojo y luego verde; pruebas de vistas
- [x] 1.8 Prueba primero, `cuentas/tests/test_componentes_rb.py`: `rb/estado_vacio.html` con `titulo` pinta el título antes del texto; sin él, el HTML no cambia. Luego el parámetro (D5). Prueba primero, `test_vistas.py`: sábado → «Hoy no hay clases» / «La asistencia se registra de lunes a viernes.» con `rb/estado_vacio.html`, sin lista ni «Marcar los N restantes»; sección sin estudiantes → «Tu sección aún no tiene estudiantes» / «Agrégalos para poder tomar asistencia.» con «Ver estudiantes» a la lista. Luego `_fin_de_semana.html` y `_sin_estudiantes.html`. Verificar: rojo y luego verde; `uv run pytest src/backend/cuentas/tests/test_componentes_rb.py src/backend/repositorio src/backend/institucion/tests/test_vistas_estudiantes.py` y pruebas de vistas
- [x] 1.9 Prueba primero, `test_asistencia_e2e.py`: los localizadores `.panel-jornada`, `.controles` y `.vista-asistencia` pasan a la tarjeta y al contenedor nuevos; con eso las e2e de conducta fallan por los selectores del JS. Luego `asistencia.js`: `closest` del contenedor nuevo y moldes desde `.leyenda--lateral .estado`, sin otro cambio (D3). Verificar: rojo y luego verde; e2e de asistencia (cola, reintentos, lote y pausa, aviso al salir, cierre, sesión vencida) sin cambios de lógica
- [x] 1.10 `asistencia.css`: encabezado, lateral de 304 px (256 px entre 700 y 960 px), una columna hasta 699 px, tarjeta café con un solo acento, resumen compacto `sticky` bajo la barra, filas de 76/80 px, círculo de 44 px con los colores fijos de `--tarde-*` y `--justificado-*`, nota de justificación, inactivos, barra de «Deshacer» y una variante del conteo y de «Marcar los N restantes» por ancho (D1, D2). Prueba primero, `test_asistencia_e2e.py` a 360 px: tras desplazar la lista, el resumen sigue visible bajo la barra; con Tab hasta un círculo de la mitad de la lista, el círculo queda debajo del resumen; «N sin marcar» lleva a la primera fila Sin marcar sin que la tape el resumen. Verificar: rojo y luego verde; e2e de asistencia
- [x] 1.11 Cierre sin trazo: `cierre-animado` solo hace el fundido de color de 140 ms y nada con movimiento reducido; «Jornada completa» con el resumen de totales y «✓ Asistencia de hoy completa» (D3, D4). Prueba primero: las e2e del cierre (`test_el_cierre_aparece_tras_el_ultimo_guardado`, `test_sin_cierre_*`, `test_el_cierre_tras_la_cuenta`) siguen en verde con el contenedor nuevo. Verificar: e2e de asistencia
- [x] 1.12 Sin desplazamiento horizontal y axe (delta «Asistencia accesible…»): `test_nombre_de_120_mas_120_a_320_px` y las e2e de axe (lista a medio marcar, fin de semana, sin estudiantes, con barra, sin conexión, completa) en ambos temas y anchos, con el marco del rebrand. Luego los ajustes de contraste o foco en `asistencia.css`. Verificar: e2e de asistencia en verde
- [x] 1.13 Pantalla vista en claro/oscuro y celular/escritorio, con el lote en cuenta, sin conexión y completa (la marca Marco). `verificar.py` y commit

## 2. Cierre

### Parte B: A2 y verificacion.md

- [ ] 2.1 `-m e2e` completo una vez y `verificar.py --completo` (80 % o más). Con la A2 que corre el usuario (`/codex:adversarial-review --base main --background`, con foco en la spec `asistencia-jornada` del cambio y en D1–D3), corregir los Critical e Important con la prueba primero. Verificar: `verificar.py --antes-del-commit` en verde
- [ ] 2.2 `verificacion.md` corta: DoD 1 a 9, escenarios del delta sin prueba con su motivo y los Minor. Verificar: commit

## e2e a retirar (Marco aprueba; no se borran sin su visto bueno)

- `test_sin_conexion_solo_al_tercer_fallo_y_una_vez` a 1280 px: con una sola tarjeta el aviso está en el mismo lugar en los dos anchos; queda solo a 360 px.
- Axe por variante de datos a 1280 px (`test_el_fin_de_semana_pasa_axe`, `test_la_seccion_sin_estudiantes_pasa_axe`, `test_las_vistas_de_la_parte_c_pasan_axe`): las reglas piden axe sobre el estado principal en ambos temas, pero el escenario «Revisión de cada vista» exige todas las vistas a 360 y 1280 px. Retirarlas pide ajustar ese escenario; sin esa decisión, se quedan.

## Ajustes del propose a decisiones.md

- Punto 6 y 7: con todo marcado no se muestra «N/N · 0 sin marcar» sino los totales de la spec; durante el lote, «Pendiente de deshacer» (D4).
- Punto 3: las flechas del selector siguen siendo botones con `aria-disabled` (D4).
- Punto 9: «7 sin marcar» del celular es el enlace a la primera fila Sin marcar, no texto (D2).
- Punto 11: `rb/estado_vacio.html` gana `titulo` opcional (D5).

## Workflow follow-up

- **(push)** Al cerrar este cambio, push de `feature/rebrand` con aprobación; sigue el PR borrador único hacia `main`.
- **(paso 8)** Borrar de `app.css` el CSS de asistencia (`.vista-asistencia`, `.panel-jornada`, `.franja-jornada`, `.franjas-cabecera`, `.leyenda`…) y los parciales que queden sin uso.
- **(DESIGN.md)** El Layout de pantallas pide «N/M · K sin marcar» también con K en cero; la spec manda los totales. Anotarlo para la auditoría visual del final del rebrand.
- **(T-04)** El lugar del botón de tema en la barra queda vacío.
- **(auditoría visual)** Con todos marcados (y durante el lote, con todos marcados), la tarjeta oculta «N/M marcados» y muestra la frase «Asistió: 25 · Tarde: 0 · …» de la spec, que en PC repite los cuatro totales. Marco lo deja así; revisarlo junto con el resto de pantallas al final del rebrand.
- Al proponer el paso 5 (Competencias), su primer commit archiva este con `/opsx:archive` y «Sync now».
