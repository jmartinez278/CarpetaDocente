# Verificación: rebrand de la base (marco común y «sin permiso»)

Rama `feature/rebrand` (paso 0 del PLAN del rebrand). Los 21 escenarios de los dos specs (13 de `pantallas-de-inicio` y 8 de `cierre-sesion`) tienen al menos una prueba o una nota; por D10, lo que depende de una pantalla que sigue en el marco viejo se prueba «con su pantalla». Abreviaturas: `m` = `cuentas/tests/test_marco_rebrand.py`, `e2e` = `cuentas/tests/test_marco_rebrand_e2e.py`, `dim` = `cuentas/tests/test_dimensiones.py`, `a11y` = `cuentas/tests/test_accesibilidad_e2e.py`, `srv` = `institucion/tests/test_servicios.py`.

## Minor para la descripción del PR

- Parte A: la prueba de la regla 4 (`test_ninguna_transicion_de_ancho_ni_alto`) no detecta `transition: all` ni `transition-property: all`, que también animan `width` y `height`; conviene sumarlo cuando entre el CSS del prototipo (Parte B).
- Parte A: en PowerShell, si con Ctrl+C un vigilante sale antes de que `vigilar.mjs` reciba SIGINT, se imprime «terminó… se cierra el otro vigilante» y npm muestra un error que no es real (los dos se cierran igual).
- Parte A: D1 y D2 se ajustaron en `design.md` al implementar: `vigilar.mjs` corre la CLI con el mismo Node y sin `shell`, para que `kill()` llegue al vigilante y no a un `cmd`; `rebrand.css` suma `@source "./rebrand"`, porque con `--poll` (contenedor) la CLI no ve los cambios de los parciales importados. La hoja compilada no cambia con esa línea.
- Parte B: ninguna prueba pinta un destino del ☰ con `actual=True` (`aria-current="page"` en `rb/menu_navegacion.html`); la lógica la prueba `dim::test_ubicacion_actual` y el marcado va con la primera pantalla interior que sea destino (Asistencia o Notas).
- Parte B: E-03 (`e2e::test_e03_cerrar_a_media_entrada_sigue_desde_donde_esta`) dispara un `cancel` sintético en vez de pulsar Escape de verdad.
- Parte B: `design.md` D6 dice `repositorio` → Sesiones; el namespace real es `sesiones` (el código está bien).

## Revisión A2 (Codex) y su corrección (4.2)

| Hallazgo | Corrección | Prueba |
|---|---|---|
| D4/D5 [medium]: si el navegador cierra el `<dialog>` a media salida (p. ej. un segundo Escape en Chrome), quedaban el temporizador, `transitionend` y `data-cerrando`; el temporizador viejo cerraba una reapertura inmediata | `descartarSalida()` en `marco.js`, llamada también desde el evento `close` (`1b4e198`) | `e2e::test_cierre_nativo_durante_la_salida_no_cierra_la_reapertura` |

Además, antes del push: `test_portada_e2e.py::test_los_tokens_aplicados_toman_su_valor_del_tema[dark]` leía los tokens oscuros del Quick Start de `DESIGN.md`, que en 1.1 ya trae los del rebrand. La portada sigue en `app.css` hasta el paso 3 del PLAN, así que ahora los lee de `app.css`.

## Prueba manual de `vigilar.mjs` (1.1, 2026-11-08, Parte A `50865d6`)

- PowerShell (Marco): `npm run dev` desde `src/frontend` arranca las dos hojas; guardar `css/rebrand/base.css` recompila `rebrand.css`; Ctrl+C cierra todo y no queda ningún `node` con `tailwindcss --watch`.
- Contenedor (Claude): `docker compose up frontend` con `--poll=1000` recompila al editar los parciales (tras sumar `@source "./rebrand"`); `stop` sale con 137 porque `sh -c` es el PID 1 (ya pasaba antes).

## Escenarios (cierre, 4.3)

### `pantallas-de-inicio`

| Escenario | Prueba |
|---|---|
| Marco común · Barra de una pantalla interior | `m::test_la_barra_lleva_el_menu_el_titulo_y_la_cuenta_en_orden`, `m::test_la_barra_no_lleva_el_nombre_de_la_ie`, `e2e::test_barra_de_una_pantalla_interior` (72/64 px, visible al desplazar) |
| Marco común · Barra y pie | Con su pantalla (D10): la portada (paso 3) y el inicio de la dirección (paso 7) siguen en el marco viejo, con sus pruebas actuales |
| Marco común · Pie | `m::test_el_pie_va_despues_del_main_con_sus_dos_textos`, `e2e::test_pie_alineado_con_el_contenido` (1280 y 360). En la portada y la dirección, con su pantalla (D10) |
| Accesibilidad · Revisión de cada pantalla | `a11y::test_sin_infracciones_graves_de_accesibilidad` con «sin-permiso», «sin-permiso-menu-abierto» y «sin-permiso-cuenta-abierta» (claro/oscuro, 360/1280), `a11y::test_sin_permiso_controles_del_marco_de_44_px` |
| Navegación · Abrir el ☰ | `dim::test_inicio_y_las_tres_dimensiones_en_el_orden_del_menu`, `dim::test_con_seccion_unica_enlaza_igual_que_las_tarjetas`, `m::test_con_seccion_unica_enlaza_como_las_tarjetas`, `e2e::test_abrir_el_menu` |
| Navegación · Destino no disponible | `dim::test_sin_seccion_unica_solo_inicio_enlaza`, `m::test_sin_seccion_unica_solo_inicio_enlaza`, `dim::test_un_destino_no_disponible_no_es_el_actual` |
| Navegación · Ubicación actual | `dim::test_ubicacion_actual` (portada, hoja, Competencias, asistencia), `m::test_desde_sin_permiso_ningun_destino_es_el_actual`. Marcado visible: con su pantalla (Minor de la Parte B) |
| Navegación · Teclado | `e2e::test_teclado_no_sale_del_dialogo_y_escape_devuelve_el_foco`, `e2e::test_a01_con_el_teclado_el_menu_abre_y_cierra_de_una_vez` |
| Navegación · Cerrar con el ✕ | `e2e::test_cerrar_con_la_x`, `e2e::test_a01_el_x_con_el_teclado_cierra_de_una_vez` |
| Navegación · Toque fuera del panel | `e2e::test_toque_fuera_del_panel` |
| Navegación · Sin JavaScript | `e2e::test_sin_javascript_el_menu_lleva_a_la_portada` |
| Navegación · ☰ abierto a 320 px | `e2e::test_menu_abierto_no_desborda` (320 y 360, ambos temas) |
| Movimiento (D5; E-02 a E-05, A-01 a A-03) | `e2e::test_e02_*`, `test_e03_*`, `test_e05_*`, `test_movimiento_reducido_el_menu_no_se_desplaza`, `test_a01_*`, `test_a02_*`, `test_a03_*`, `test_cierre_nativo_durante_la_salida_no_cierra_la_reapertura` |

### `cierre-sesion`

| Escenario | Prueba |
|---|---|
| Menú de la cuenta · Abrir el menú | `m::test_la_cuenta_va_con_sus_ganchos_y_su_formulario`, `m::test_la_cuenta_sin_nombre_muestra_el_usuario`, `e2e::test_abrir_la_cuenta` |
| Menú de la cuenta · Docente con sección | `srv::test_cuenta_con_una_seccion`, `srv::test_cuenta_con_dos_secciones_por_grado_y_nombre`, `m::test_la_cuenta_con_seccion_la_muestra_bajo_la_ie`, `e2e::test_la_cuenta_con_seccion` |
| Menú de la cuenta · Docente sin sección | `srv::test_cuenta_sin_seccion_no_lleva_linea`, `srv::test_cuenta_con_la_unica_seccion_en_un_anio_cerrado`, `m::test_la_cuenta_sin_seccion_no_lleva_linea` |
| Menú de la cuenta · Dirección | `srv::test_cuenta_de_la_direccion_no_lleva_linea`. Marcado en el inicio de la dirección: con su pantalla (paso 7, D10) |
| Menú de la cuenta · Teclado | `e2e::test_la_cuenta_con_teclado` |
| Menú de la cuenta · Toque fuera del menú | `e2e::test_toque_fuera_de_la_cuenta` |
| Menú de la cuenta · Sin JavaScript | `e2e::test_sin_javascript_la_cuenta_abre_y_cierra_la_sesion` |
| Menú de la cuenta · Menú abierto a 320 px | `e2e::test_cuenta_abierta_no_desborda` (320 y 360, ambos temas) |

## DoD 1 a 9

| N.° | Criterio | Estado |
| --- | --- | --- |
| 1 | Cobertura ≥ 80 % | Local: 98,52 % total (`verificar.py`, sin e2e). Sonar way: pendiente del push |
| 2 | Análisis estático sin críticas ni altas | Ruff en verde con `verificar.py`. A2 de Codex: un hallazgo medium corregido (4.2). CodeQL y SonarQube Cloud: pendiente del push |
| 3 | Aprobación de otra integrante | Pendiente del PR único del rebrand (al final, no antes del 11-11-2026) |
| 4 | Vista previa de Vercel | Pendiente del push |
| 5 | Escenarios en verde y e2e de la ruta ideal | Los 21 escenarios tienen prueba o nota; e2e de todas las apps: 492 en verde (la última falla, Estudiantes → «sin permiso», era por el `<dialog>` del ☰ y se ajustó). Ruta ideal: `e2e::test_abrir_el_menu`, `e2e::test_abrir_la_cuenta`. GitHub Actions: pendiente del push |
| 6 | Reglas de negocio con pruebas propias | Destinos del ☰ con la misma disponibilidad que las tarjetas (`dim::*`) y secciones del año ABIERTO en la cuenta (`srv::test_cuenta_*`), en la capa de servicios |
| 7 | Accesibilidad sin errores críticos | `a11y::test_sin_infracciones_graves_de_accesibilidad` (claro/oscuro, 360/1280, ☰ y cuenta abiertos), controles de 44 × 44 px, `a11y::test_sin_permiso_no_desborda_y_su_boton_es_tactil`. Pantalla vista en claro/oscuro y celular/escritorio por Marco (3.4) |
| 8 | Sin datos reales | Docentes y secciones ficticios de las fixtures. Único archivo de terceros: Instrument Sans (OFL), con su licencia en `fuentes/LICENSE-instrument-sans` |
| 9 | Documentación | Specs del cambio, `design.md` (D1 y D2 ajustados al implementar), docstrings de `cuentas/templatetags/marco.py` y `institucion/servicios.py`. Sin rutas nuevas: `docs/03` y README sin cambios. Deuda en `tasks.md` («Workflow follow-up») |
