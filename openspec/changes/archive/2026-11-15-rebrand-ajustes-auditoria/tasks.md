# Tasks

Tres partes y un commit por cada una. Notas va primero porque es de alto riesgo (la parada de A-05 ya se resolvió: descartado); no lleva revisor porque no toca modelos, permisos ni datos personales. Commits con el sufijo `(rebrand-ajustes-auditoria)`.

Comandos: `uv run pytest src/backend/<app>` y, para las e2e, `uv run pytest -m e2e <archivo> --browser chromium` con `npm run build` hecho y `DJANGO_ALLOW_ASYNC_UNSAFE=true`.

## 1. Notas

### Parte A: panel, tira y hoja (alto riesgo)

- [x] 1.1 (D3, A-05) Descartado: con el rótulo, el escenario de la tira no pasó a 360 px (píldora de 147 px en una tira de 124 px). Se paró y Marco decidió (15-11-2026) dejar el círculo y llevar A-05 a la deuda. Sin cambios en `notas.css` ni en la prueba
- [x] 1.2 Prueba primero, `notas/tests/test_plantilla_hoja.py` (D4, A-04): el panel trae `#error-conclusion` oculto y el textarea `#conclusion-movil` con `aria-describedby="ayuda-conclusion error-conclusion"`; el editor de PC, `#error-nota` oculto y `#conclusion-pc` con `aria-describedby="ayuda-nota error-nota"`. Luego `hoja.html`. Verificar: rojo y luego verde; pruebas de `notas`
- [x] 1.3 Prueba primero, `notas/tests/test_hoja_e2e.py` (D4, A-04): a 360 px, con «B» y la conclusión vacía en el panel, se ven «Falta conclusión» y «Escribe de 10 a 500 caracteres.» a la vez; con 3 caracteres, «Usa de 10 a 500 caracteres.» y la instrucción; con 10, el error desaparece y la instrucción queda; `aria-invalid` sigue al error. Luego `notas.js` (`dibujarPanel` e `input` de `#conclusion-movil`). Verificar: rojo y luego verde; esa e2e
- [x] 1.3b Prueba primero, `notas/tests/test_hoja_e2e.py` (D4, A-04, editor de PC; 1280 px porque el editor solo existe en PC): al elegir «B» y pulsar «Listo» con la conclusión vacía, el editor sigue abierto con «Falta conclusión.» y «De 10 a 500 caracteres.» a la vez (con 3 caracteres, el error de longitud y la instrucción); al escribir, el error se va y la instrucción queda. Luego `notas.js` (`terminarNota`, `:790`, `:1437`). Verificar: rojo y luego verde; esa e2e y las del editor existentes en `test_hoja_e2e.py`
- [x] 1.4 CSS sin prueba automática (lo ve Marco): A-07 `.hn-estado-fila` y `.hn-completa-marca` a `--text-label`; A-09 `.hn-tabla thead th` con `--grid-head`; A-10 `.hn-nivel-grande` con `--text-level` y `--leading-level`, sin cambiar su `min-height`. Verificar: `test_las_areas_tactiles_miden_44_px`; pantalla vista en claro y oscuro, a 360 y 1280 px (la marca Marco)
- [x] 1.5 `verificar.py` y commit

## 2. Asistencia, Estudiantes y Sesiones

### Parte B: conteo, barra «Deshacer», numeración y botones del pie (normal)

- [x] 2.1 Prueba primero, `asistencia/tests/test_vistas.py` (D1, A-02): con la jornada completa, `data-avance` sin `hidden`, «25/25 · » y «0 sin marcar» sin `href`. Luego `_tarjeta.html`. Verificar: rojo y luego verde; pruebas de `asistencia`
- [x] 2.2 Prueba primero, `asistencia/tests/test_asistencia_e2e.py` (D1, A-02): a 360 px, tras «Marcar los restantes» se ve «25/25 · 0 sin marcar» junto a «Pendiente de deshacer», y sigue visible al terminar la cuenta junto a «Guardado» y con «Asistencia de hoy completa». Luego `asistencia.js` (`contar()`: el avance no se oculta; con 0, sin `href`) y `asistencia.css` (desglose en su fila; flecha de PC oculta con 0). Verificar: rojo y luego verde; esa e2e y `test_el_avance_y_los_totales_cambian_con_cada_toque`
- [x] 2.3 Prueba primero, `asistencia/tests/test_asistencia_e2e.py` (D1, A-01): a 360 px con filas sin marcar, el enlace «N sin marcar» mide al menos 44 × 44 px y su caja no se cruza con la de `[data-guardado]`. Luego `asistencia.css:745` y `--asistencia-margen-fila` al alto real del resumen. Verificar: rojo y luego verde; esa e2e, `test_n_sin_marcar_lleva_a_la_primera_fila_sin_marcar` y `test_ninguna_parada_del_foco_queda_bajo_el_resumen`
- [x] 2.4 Prueba primero, `asistencia/tests/test_asistencia_e2e.py` (D2, A-14): a 360 px, durante la cuenta del lote (pausada por el foco), al avanzar con Tab desde el primer círculo hasta el último, ningún círculo con foco se cruza con la barra «Deshacer». Luego `asistencia.css`. Verificar: rojo y luego verde; esa e2e y `test_la_cuenta_se_pausa_con_el_foco_de_teclado`; arnés `insumos/rebrand-ajustes-auditoria/test_condicionales.py` a 360 px, claro y oscuro
- [x] 2.5 CSS sin prueba automática (A-03): `estudiantes.css` hasta 699 px, numeración de 24 px como mínimo y sin salto de línea. Verificar: pantalla vista a 360 px con 25 estudiantes (la marca Marco)
- [x] 2.6 CSS sin prueba automática (D5, A-15): `componentes.css`, `.dialog-acciones .btn` a `flex: 1 1 auto`. Verificar: arnés de A-15 a 1280 px (una línea, 44 px o más de alto); `uv run pytest -m e2e src/backend/repositorio/tests/test_sesiones_e2e.py --browser chromium`; pantalla vista a 360 y 1280 px de Sesiones (formulario y términos) y un diálogo de Notas (la marca Marco)
- [x] 2.7 `verificar.py` y commit (toca `componentes.css`, compartido: corre toda la suite)

## 3. Cierre

### Parte C: A2 y verificacion.md

- [x] 3.1 `-m e2e` completo una vez y `verificar.py --completo` (80 % o más). Con la A2 que corre el usuario (`/codex:adversarial-review --base main --background`, con foco en la parte A), corregir los Critical e Important con la prueba primero. Verificar: `verificar.py --antes-del-commit` en verde
- [x] 3.2 `verificacion.md` corta: DoD 1 a 9; A-05 descartado (D3, decisión de Marco); A-06 descartado (`registro-notas:150` y `:161` definen que la conclusión se oculta y se borra con A/AD; la app cumple); A-08 no aplica (`registro-notas:169` fija «Rellena la conclusión»); A-03, A-07, A-09, A-10 y A-15 sin prueba automática (CSS, vistos por Marco); los Minor. Verificar: commit

## e2e a retirar

Ninguna.

## Workflow follow-up

- **(deuda del cambio)** A-05: rotular Competencias en el celular sin sacar de la vista la píldora activa (alternativa vista: fila propia bajo la tira, +52 px). Capturas en el chat del 15-11-2026.
- **(deuda del cambio)** Alinear DESIGN.md T-02 con registro-notas (título del editor y conclusión con A/AD).
- **(PR #73, deuda, sin tocar)** A-11 (espaciado de Competencias), A-12/T-04 (botón de tema) y A-13 (`incomplete` de axe).
