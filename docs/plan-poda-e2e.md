# Plan de poda de las pruebas e2e

Fecha: 2026-11-16 · Rama medida: `feature/us-011-012-016-buscar-descargar-eliminar-sesion` (commit `fe8c554`) · Estado: **nivel 1 aplicado** el 2026-11-23 en `feature/us-040-consultar-consolidados` (sección 5 bis); el nivel 2 sigue como propuesta.

## 1. Lo que se midió

| Medida | Valor |
|---|---|
| Casos e2e recogidos (`pytest -m e2e --collect-only`) | **595** en 331 funciones y 19 archivos |
| Líneas de los archivos `*_e2e.py` | **8096** (más 127 de `cuentas/tests/e2e.py`) |
| Líneas de todas las pruebas (unitarias + e2e) | 34 822 |
| Líneas de pruebas unitarias | ≈ 26 700 (2 533 casos) |
| Líneas de código de `src/backend` sin pruebas ni migraciones | 8 752 |
| Duración e2e en serie, medida para este plan | 849 s (14 min 9 s) |
| Duración e2e en la laptop (comentario de `ci.yml`, 2026-11-14, 590 casos) | 10 min 45 s en serie · 3 min 17 s con `-n 4` |

**Corrección al contexto de partida.** Las 27 000 líneas no son de las e2e: son las pruebas unitarias. Las e2e son 8 096 líneas. La poda de este plan reduce casos y minutos; casi no reduce líneas, porque la matriz vive en decoradores `parametrize`, no en código repetido.

**Cómo se midió.** Cada archivo se corrió en serie en una máquina Linux de 2 núcleos con PostgreSQL 18 y Chromium 153 (no el 156 de Playwright), con `--junitxml`. El tiempo de cada caso incluye preparación y limpieza. Los tiempos absolutos son 1,32 veces los de la laptop; la columna «min laptop» multiplica por 0,76 (645 s / 849 s) y es una estimación. Con `-n 4` el ahorro real es más o menos un tercio del de serie.

**Cuatro casos fallaron en esta máquina** y hay que confirmarlos en la laptop antes de tocar nada: `test_diez_cortes_de_red_sin_perder_ni_duplicar` y `test_volver_al_estado_guardado_tras_un_fallo_se_guarda` (asistencia; quedó «Sin conexión» en vez de «Guardado»), y `test_las_pantallas_no_desbordan_a_360_px` en los indicadores del panel, en los dos temas. Pueden deberse a la versión de Chromium o a las fuentes.

## 2. Inventario por pantalla

Clases: **N** necesita navegador · **M** matriz redundante · **B** duplica otra prueba · **S** no usa navegador.

| Archivo (`test_…_e2e.py`) | Pantalla | Líneas | Casos | s medidos | N | M | B | S | Qué comprueba |
|---|---|--:|--:|--:|--:|--:|--:|--:|---|
| `asistencia` | Asistencia del día | 1058 | 65 | 225 | 41 | 24 | 0 | 0 | toques y guardado, nota, cuenta regresiva de «marcar restantes», cortes de red y reintentos, avisos al salir; 4 grupos axe × 4 (uno × 3 vistas) |
| `estudiantes` | Estudiantes (diálogo y página completa) | 975 | 107 | 143 | 33 | 74 | 0 | 0 | flujo del diálogo (foco, Esc, atrás, historial), importar, agregar, editar, quitar, vaciar; 17 grupos axe × 4 combinaciones, 9 de ellos repiten el estado como página completa |
| `accesibilidad` | Ingresar, portada, inicio de Dirección y Sin permiso | 294 | 104 | 95 | 8 | 96 | 0 | 0 | axe sobre 18 vistas × 2 temas × 2 anchos (72 casos); desborde a 320/360 del inicio de sesión y del menú; medidas de 44 px |
| `sesiones` | Subir sesión (popup) | 692 | 34 | 64 | 34 | 0 | 0 | 0 | validación en el cliente, términos, subida en curso, cortes y reintento idempotente, historial; Slow 4G |
| `hoja` | Hoja de notas | 1004 | 43 | 64 | 36 | 4 | 3 | 0 | teclado en la grilla, panel del celular, conclusiones, guardar y errores, conteo de faltantes, columnas fijas; axe × 4; Slow 4G |
| `competencias` | Competencias | 740 | 43 | 53 | 40 | 0 | 3 | 0 | marcar/guardar, cápsula de áreas, periodos, deshacer, obligatorias, diálogo de salida, sin red, sesión vencida; axe × 2 temas |
| `portada` | Portada de la docente | 388 | 55 | 41 | 21 | 34 | 0 | 0 | disposición a 360/1280, tokens por tema, aviso «Próximamente», enlaces de tarjetas; desborde × 18 y × 8, axe × 8 |
| `marco_rebrand` | Marco: barra, menú y cuenta | 560 | 38 | 37 | 30 | 8 | 0 | 0 | abrir/cerrar menú y cuenta con mouse, teclado y sin JS; animaciones y marcas de teclado; desborde del menú y la cuenta × 4 |
| `borradores` | Borradores de notas (localStorage) | 658 | 21 | 35 | 21 | 0 | 0 | 0 | persistencia, dos pestañas, otra cuenta, cierre de sesión, conflictos con la base |
| `periodos` | Admin: periodos | 128 | 16 | 21 | 1 | 14 | 1 | 0 | llenar bimestres, cruce de fechas; 3 grupos axe × 4; desborde a 360 × 2 temas |
| `repositorio` | Mis sesiones y repositorio | 319 | 7 | 17 | 7 | 0 | 0 | 0 | buscar, filtrar, pestañas con flechas, foco del buscador; axe × 2 temas |
| `panel` | Admin: registro de actividad | 104 | 13 | 17 | 1 | 12 | 0 | 0 | axe de lista e indicadores × 4; desborde × 4; descarga del CSV |
| `detalle` | Página de la sesión | 188 | 4 | 10 | 4 | 0 | 0 | 0 | diálogos de eliminar y compartir; axe × 2 temas |
| `asignar_seccion` | Admin: asignar sección → portada | 81 | 5 | 8 | 1 | 2 | 2 | 0 | recorrido del administrador; axe y desborde de la portada con sección |
| `cerrar_sesion` | Cerrar sesión | 159 | 8 | 8 | 8 | 0 | 0 | 0 | cierre manual y por inactividad, botón atrás (bfcache), menú sin JS |
| `ingresar` | Ingresar | 283 | 13 | 6 | 12 | 0 | 1 | 0 | recorrido, mostrar contraseña, estado «Ingresando», foco tras error, regiones de estado, sin JS |
| `gestion_cuentas` | Admin: cuentas | 66 | 1 | 3 | 1 | 0 | 0 | 0 | crear, ingresar y desactivar una docente |
| `rendimiento` | Ingresar con red lenta | 58 | 1 | 2 | 1 | 0 | 0 | 0 | carga con Slow 4G |
| `hoja_rebrand` | Hoja de estilos | 341 | 17 | 1 | 3 | 0 | 0 | 14 | 14 casos leen app.css como texto (tokens, transiciones, dvh); 3 miden en el navegador |
| **Total** | | **8096** | **595** | **849** | **303** | **268** | **10** | **14** | |

El detalle función por función está en el anexo.

## 3. Clasificación

| Clase | Casos | s medidos | % del tiempo | Lectura |
|---|--:|--:|--:|---|
| N · necesita navegador | 303 | 514 | 61 % | Foco, teclado, diálogos, historial, localStorage, cortes de red, temporizadores, medidas reales. No se toca. |
| M · matriz redundante | 268 | 326 | 38 % | El mismo estado repetido en tema × ancho (× vista). Aquí está la poda. |
| B · duplica otra prueba | 10 | 9 | 1 % | Solo leen HTML que ya revisa una unitaria, o repiten otra e2e. |
| S · no usa navegador | 14 | 0 | 0 % | 14 casos de `hoja_rebrand` leen `app.css` como texto. Son e2e solo porque necesitan el CSS compilado. Cuestan menos de 1 s: se quedan. |

Dos hallazgos que cambian el plan:

- **La duplicación con las unitarias es pequeña** (10 casos, 9 s). Casi todo caso funcional que parece repetir una regla del servidor comprueba en realidad el JavaScript de la pantalla (validación en el cliente, estado que pone Alpine, manejo del 403 con HTMX).
- **El tiempo no está donde están los casos.** `asistencia` tiene el 11 % de los casos y el 27 % del tiempo: 22 casos esperan temporizadores reales (cuenta regresiva de 5 s, reintentos) y suman 183 s. Eso no se arregla podando (sección 6).

Casos B, con la prueba que los cubre (confirmar cada una antes de borrar):

| Caso e2e | Lo cubre | Seguridad |
|---|---|---|
| competencias · `sin_periodos_solo_el_aviso` | `notas/tests/test_vistas.py::test_sin_periodos` | alta |
| competencias · `el_periodo_futuro_no_se_puede_elegir` | `notas/tests/test_plantilla.py::test_el_futuro_va_deshabilitado_y_los_que_empezaron_no` | alta |
| competencias · `las_areas_del_docente_de_curso_no_se_pueden_marcar` | unitarias de `area_del_docente_de_curso`; falta ubicar la que mira `disabled` en la plantilla | media |
| hoja · `un_trasladado_sin_nivel_no_cuenta` | `notas/tests/test_servicios_hoja.py::test_el_trasladado_sin_nivel_no_cuenta` (cubre el conteo; no el texto en pantalla) | **no la cubre**: el texto lo pone `notas.js`; se queda (N) |
| hoja · `la_barra_cuenta_las_notas_que_faltan` | `test_el_resultado_trae_las_faltantes_del_area`; «Faltan 3 notas» lo escribe `notas.js` (`textoFaltan`), no el servidor | **no la cubre**; se queda (N) |
| hoja · `con_todo_guardado_dice_area_completa` | «Matemática completa» también lo escribe `notas.js` | **no la cubre**; se queda (N) |
| ingresar · `la_direccion_llega_a_su_inicio` | `test_la_direccion_llega_a_su_pantalla` y `test_ingresar.py`; el recorrido en navegador ya lo hace la docente | alta |
| periodos · `un_cruce_muestra_el_mensaje_junto_a_la_fila` | `test_un_cruce_que_llega_al_guardado_muestra_el_mensaje_sin_500` y `test_servicios_periodos.py` | alta |
| asignar_seccion · `la_portada_con_la_seccion_pasa_axe` (2) | la vista `portada-una-seccion` de `test_accesibilidad_e2e` | alta |

## 4. Qué conservar y con qué criterio

El criterio ya está escrito. `openspec/config.yaml` (reglas de tareas, 2026-11-12) dice: una e2e solo si hace falta un navegador real; sin e2e para valores de CSS; por pantalla, el flujo principal, la conducta de JS, un desplazamiento horizontal a 360 px y axe sobre el estado principal y cada diálogo abierto en ambos temas; sin matriz de estados × temas × anchos; un ancho por e2e (360 px). La suite es anterior a esas reglas. `.claude/rules/plantillas.md` pide ver cada pantalla en ambos temas a 360 y 1280, pero como revisión de Marco en la pantalla, no como e2e.

Este plan aplica esas reglas en dos niveles.

**Nivel 1: la parte mecánica (lo que se cuantifica abajo).**

1. **Lo funcional (N) se conserva entero.**
2. **axe a 360 px en los dos temas.** Cada grupo axe pasa de 4 casos a 2. Excepción: Hoja de notas, donde el DOM cambia con el ancho (grilla en PC, panel en celular); ahí los 2 casos son `360-dark` y `1280-light`.
3. **Desborde sin tema.** El tema cambia colores, no cajas: el desplazamiento horizontal se prueba por ancho, en un solo tema.
4. **Página completa, una vez.** En Estudiantes, cada estado ya auditado en el diálogo se repite como página completa (respaldo sin JS). Esa variante queda con 1 caso.
5. **B se borra solo con su reemplazo nombrado.** Si la prueba de vista no existe o no afirma lo mismo, se escribe primero y se ve fallar.

**Nivel 2: lo que pide juicio caso por caso.** La misma regla manda listarlas como «e2e a retirar» para que Marco las apruebe; por eso aquí solo se estiman.

- axe por variante de datos: de las 18 vistas de `test_accesibilidad_e2e`, unas 7 son estado principal o diálogo; el resto son variantes (con error, vacío, una o varias secciones, pendiente).
- Un solo desborde a 360 px por pantalla.
- e2e de valores de CSS: los 17 casos de `hoja_rebrand` y parte de `portada`, `marco_rebrand` e `ingresar` (tokens, animaciones, alturas de línea). Una búsqueda automática marca unos 45 casos, pero mezcla CSS puro con conducta; hay que separarlos a mano.
- Estimación gruesa: quedarían unos 350 casos y el ahorro subiría a unos 3 min en serie en la laptop.

| Archivo | Casos hoy | Se conservan | Qué se conserva |
|---|--:|--:|---|
| `estudiantes` | 107 | 61 | 33 funcionales; 8 estados axe del diálogo a 360 en los dos temas; 9 de página completa con 1 caso |
| `accesibilidad` | 104 | 56 | 18 vistas axe a 360 en los dos temas (36); desborde por ancho en un tema; medidas |
| `asistencia` | 65 | 53 | 41 funcionales; 6 estados axe a 360 en los dos temas |
| `portada` | 55 | 38 | 21 de disposición, tokens y avisos; axe a 360 en los dos temas; desborde por ancho |
| `periodos` | 16 | 8 | recorrido del administrador; 3 estados axe a 360 en los dos temas; desborde en 1 tema |
| `hoja` | 43 | 38 | 36 funcionales; axe en `360-dark` y `1280-light` |
| `panel` | 13 | 7 | CSV; axe a 360 en los dos temas; desborde en 1 tema |
| `marco_rebrand` | 38 | 34 | 30 funcionales; desborde de menú y cuenta por ancho |
| `asignar_seccion` | 5 | 2 | recorrido del administrador; desborde a 320 en 1 tema |
| `competencias` | 43 | 40 | 36 funcionales; axe × 2 temas |
| `ingresar` | 13 | 12 | 12 funcionales |
| `cerrar_sesion`, `gestion_cuentas`, `hoja_rebrand`, `rendimiento`, `borradores`, `detalle`, `repositorio`, `sesiones` | 93 | 93 | Todo en el nivel 1. No tienen matriz ni duplicados. |
| **Total** | **595** | **442** | |

## 5. Orden de la poda

Un commit por paso, con la suite e2e completa en verde antes y después. Ordenado por minutos ahorrados.

| Paso | Archivo | Casos que salen | Líneas | s medidos | min laptop (serie) | Cambio |
|--:|---|--:|--:|--:|--:|---|
| 1 | `estudiantes` | 46 | ≈ 2 | 64 | 0,8 | 8 grupos axe 4 → 2; 9 de página completa 4 → 1; `no_se_desplazan` y `carga_empezando_arriba` sin tema |
| 2 | `accesibilidad` | 48 | ≈ 2 | 44 | 0,6 | `sin_infracciones_graves` 72 → 36; los tres de desborde sin tema |
| 3 | `asistencia` | 12 | ≈ 2 | 27 | 0,3 | `vistas_de_la_parte_c` 12 → 6; otros 3 grupos axe 4 → 2 |
| 4 | `portada` | 17 | ≈ 2 | 10 | 0,1 | `el_documento_no_se_desplaza` 18 → 9; `la_portada_no_se_desplaza` 8 → 4; axe 8 → 4 |
| 5 | `periodos` | 8 | ≈ 14 | 10 | 0,1 | 3 grupos axe 4 → 2; desborde 2 → 1; sale el cruce (B) |
| 6 | `hoja` | 5 | ≈ 33 | 10 | 0,1 | axe 4 → 2; salen 3 de conteo (B) |
| 7 | `panel` | 6 | ≈ 2 | 8 | 0,1 | 2 grupos axe 4 → 2; desborde 4 → 2 |
| 8 | `marco_rebrand` | 4 | ≈ 2 | 4 | 0,0 | menú y cuenta abiertos 4 → 2 |
| 9 | `asignar_seccion` | 3 | ≈ 11 | 2 | 0,0 | sale axe (B); desborde 2 → 1 |
| 10 | `competencias` | 3 | ≈ 24 | 3 | 0,0 | salen 3 (B) |
| 11 | `ingresar` | 1 | ≈ 7 | 0 | 0,0 | sale 1 (B) |
| | **Total** | **153** | **≈ 101** | **184** | **2,3** | 595 → 442 casos (−26 %); −22 % del tiempo |

Resultado esperado: de 10 min 45 s a unos 8 min 25 s en serie en la laptop; en CI con `-n 4`, de 3 min 17 s a unos 2 min 35 s. Las líneas bajan menos del 2 %.

## 5 bis. Nivel 1 aplicado (2026-11-23)

Un solo commit en `feature/us-040-consultar-consolidados`, no uno por paso. Suite e2e: **619 → 465 casos (−154)**, 465 en verde con `-n 4 --dist loadfile` en 3 min 51 s en la laptop.

- Diferencias con la tabla de la sección 5: los 3 casos de conteo de `hoja` se quedan (ver tabla B); los 2 grupos axe que trajo US-031 en `asistencia` (`un_dia_pasado` y `periodo_cerrado`) siguieron la misma regla (8 → 4); `test_plantilla_siagie_e2e.py`, posterior a la medición, no se tocó.
- Reemplazos confirmados de los B borrados: el cruce de `periodos` → `test_admin_periodos.py::test_cada_regla_muestra_su_mensaje_en_la_ficha_y_no_guarda_nada`; `ingresar · la_direccion_llega_a_su_inicio` → `test_ingresar.py::test_cada_rol_llega_a_su_pantalla[direccion]` y `test_pantallas.py::test_la_direccion_saluda_y_muestra_el_estado_vacio` (la prueba que nombraba la tabla no existe); `competencias` → `test_plantilla.py::test_un_area_a_cargo_va_atenuada_con_su_aviso_y_casillas_deshabilitadas`, `test_el_futuro_va_deshabilitado_y_los_que_empezaron_no` y `test_vistas.py::test_sin_periodos`.
- La página completa de Estudiantes queda en 360 px, tema claro; el desborde sin tema, en claro.
- Los axe de `asistencia` ya no miden el desborde a 1280 px.

## 6. Lo que la poda no resuelve

- **Temporizadores reales en asistencia.** 22 casos suman 183 s medidos (≈ 2,3 min en la laptop), lo mismo que ahorra todo el nivel 1. Usan `wait_for_timeout` de hasta 6 s y esperan la cuenta de 5 s. Con el reloj simulado de Playwright (`page.clock`) esos casos correrían en una fracción del tiempo sin perder cobertura. Ninguna e2e lo usa hoy. Ahorro sin medir; requiere un cambio aparte.
- **Solapes de axe sobre la portada.** `test_accesibilidad_e2e` (8 vistas de portada), `portada_e2e::la_portada_con_y_sin_pildora_pasa_axe` y `estudiantes_e2e::la_portada_con_el_aviso_pasa_axe` auditan estados parecidos. No se incluyó en los números: hay que comparar los estados uno por uno.
- **Si el objetivo son las 27 000 líneas**, el trabajo está en las unitarias (2 533 casos) y necesita su propia medición.

## 7. Pendientes antes de ejecutar

- Repetir la medición en la laptop: `uv run pytest -m e2e --browser chromium --durations=0 --junitxml=e2e.xml`.
- Confirmar los 4 fallos de la sección 1.
- Aprobar el nivel 1 y decidir si se hace el nivel 2.
- Confirmar las filas de seguridad «media» de la tabla B.

## Anexo. Medición por función

`conservar` es la cantidad de casos que quedan con el nivel 1.


### `test_panel_e2e.py`

| Prueba | Casos | s | Clase | Conservar |
|---|--:|--:|:-:|--:|
| `la_lista_del_registro_pasa_axe` | 4 | 7.5 | M | 2 |
| `los_indicadores_por_semana_pasan_axe` | 4 | 5.3 | M | 2 |
| `las_pantallas_no_desbordan_a_360_px` | 4 | 3.2 | M | 2 |
| `el_boton_descarga_el_csv_de_lo_filtrado` | 1 | 0.8 | N | 1 |

### `test_asistencia_e2e.py`

| Prueba | Casos | s | Clase | Conservar |
|---|--:|--:|:-:|--:|
| `camino_ideal` | 1 | 5.7 | N | 1 |
| `el_avance_y_los_totales_cambian_con_cada_toque` | 1 | 1.1 | N | 1 |
| `volver_a_abrir_muestra_lo_guardado` | 1 | 2.4 | N | 1 |
| `toques_rapidos_mientras_se_guarda` | 1 | 1.4 | N | 1 |
| `guardado_sano` | 1 | 0.9 | N | 1 |
| `la_nota_se_guarda_al_salir_del_campo` | 1 | 1.3 | N | 1 |
| `la_nota_se_guarda_sola_al_dejar_de_escribir` | 1 | 2.5 | N | 1 |
| `intro_y_espacio_en_el_circulo` | 1 | 1.0 | N | 1 |
| `la_lista_a_medio_marcar_pasa_axe` | 4 | 7.3 | M | 2 |
| `n_sin_marcar_lleva_a_la_primera_fila_sin_marcar` | 1 | 2.1 | N | 1 |
| `el_conteo_sigue_visible_con_la_jornada_completa` | 1 | 6.3 | N | 1 |
| `el_enlace_n_sin_marcar_mide_44_y_no_se_cruza_con_el_guardado` | 1 | 0.9 | N | 1 |
| `el_foco_no_queda_bajo_la_barra_deshacer` | 1 | 2.1 | N | 1 |
| `el_resumen_fijo_no_tapa_las_filas_ni_el_foco` | 1 | 1.1 | N | 1 |
| `ninguna_parada_del_foco_queda_bajo_el_resumen` | 1 | 3.3 | N | 1 |
| `el_fin_de_semana_pasa_axe` | 4 | 3.9 | M | 2 |
| `la_seccion_sin_estudiantes_pasa_axe` | 4 | 4.0 | M | 2 |
| `flujo_alternativo_valido` | 1 | 6.4 | N | 1 |
| `marcar_los_restantes_no_toca_a_los_ya_marcados` | 1 | 8.4 | N | 1 |
| `deshacer_no_guarda_nada` | 1 | 7.1 | N | 1 |
| `fin_de_la_cuenta_y_su_anuncio` | 1 | 6.2 | N | 1 |
| `toque_durante_la_cuenta` | 1 | 7.2 | N | 1 |
| `cerrar_la_pagina_durante_la_cuenta_guarda_el_lote` | 1 | 1.2 | N | 1 |
| `la_cuenta_se_pausa_con_el_puntero` | 1 | 8.3 | N | 1 |
| `la_cuenta_se_pausa_con_el_foco_de_teclado` | 1 | 3.4 | N | 1 |
| `el_foco_que_pone_la_pantalla_no_pausa_la_cuenta` | 1 | 6.2 | N | 1 |
| `diez_cortes_de_red_sin_perder_ni_duplicar` | 1 | 15.0 | N | 1 |
| `fallo_de_un_guardado` | 1 | 4.9 | N | 1 |
| `volver_al_estado_guardado_tras_un_fallo_se_guarda` | 1 | 6.1 | N | 1 |
| `el_lote_no_sale_dos_veces_al_volver_la_red` | 1 | 7.1 | N | 1 |
| `sin_conexion_solo_al_tercer_fallo_y_una_vez` | 2 | 16.7 | N | 2 |
| `aviso_al_salir_con_una_marca_pendiente` | 1 | 1.4 | N | 1 |
| `aviso_al_salir_con_un_guardado_en_curso_que_vuelve_al_confirmado` | 1 | 1.6 | N | 1 |
| `un_rechazo_no_descarta_las_marcas_pendientes_de_otras_filas` | 1 | 3.7 | N | 1 |
| `un_rechazo_del_lote_no_descarta_la_fila_que_salio_de_el` | 1 | 7.4 | N | 1 |
| `sin_nada_pendiente_se_sale_sin_aviso` | 1 | 1.0 | N | 1 |
| `sesion_vencida_durante_los_toques` | 1 | 1.5 | N | 1 |
| `el_cierre_aparece_tras_el_ultimo_guardado` | 1 | 3.8 | N | 1 |
| `sin_cierre_con_la_ultima_marca_sin_guardar` | 1 | 4.0 | N | 1 |
| `sin_cierre_durante_la_cuenta_ni_tras_deshacer` | 1 | 0.9 | N | 1 |
| `el_cierre_tras_la_cuenta` | 1 | 6.2 | N | 1 |
| `las_vistas_de_la_parte_c_pasan_axe` | 12 | 39.6 | M | 6 |
| `nombre_de_120_mas_120_a_320_px` | 1 | 1.2 | N | 1 |
| `marcar_en_una_seccion_que_ya_no_es_suya_lleva_a_sin_permiso` | 1 | 1.5 | N | 1 |

### `test_accesibilidad_e2e.py`

| Prueba | Casos | s | Clase | Conservar |
|---|--:|--:|:-:|--:|
| `sin_infracciones_graves_de_accesibilidad` | 72 | 72.1 | M | 36 |
| `el_menu_abierto_no_desborda_la_ventana` | 8 | 6.4 | M | 4 |
| `el_inicio_de_sesion_no_desborda` | 12 | 7.0 | M | 6 |
| `b01_un_error_de_campo_sin_espacios_no_desborda` | 2 | 1.0 | N | 2 |
| `el_ojo_mide_44_px_dentro_del_campo` | 2 | 0.7 | N | 2 |
| `el_nombre_de_la_ie_mide_40_px_en_pc_y_30_en_celular` | 2 | 0.8 | N | 2 |
| `sin_permiso_no_desborda_y_su_boton_es_tactil` | 4 | 3.4 | M | 2 |
| `sin_permiso_controles_del_marco_de_44_px` | 2 | 3.2 | N | 2 |

### `test_cerrar_sesion_e2e.py`

| Prueba | Casos | s | Clase | Conservar |
|---|--:|--:|:-:|--:|
| `camino_ideal_abre_el_menu_y_cierra_la_sesion` | 1 | 0.8 | N | 1 |
| `atras_despues_de_cerrar_sesion_no_muestra_el_saludo` | 1 | 0.9 | N | 1 |
| `inactividad_muestra_el_aviso_y_atras_no_muestra_la_pantalla` | 1 | 1.0 | N | 1 |
| `escape_cierra_el_menu_y_devuelve_el_foco` | 1 | 0.7 | N | 1 |
| `un_toque_fuera_cierra_el_menu` | 1 | 0.7 | N | 1 |
| `sin_javascript_el_menu_abre_y_cierra_la_sesion` | 1 | 0.7 | N | 1 |
| `panel_atras_tras_el_cierre_manual_no_muestra_la_pantalla` | 1 | 1.3 | N | 1 |
| `panel_atras_tras_la_inactividad_no_muestra_la_pantalla` | 1 | 1.4 | N | 1 |

### `test_gestion_cuentas_e2e.py`

| Prueba | Casos | s | Clase | Conservar |
|---|--:|--:|:-:|--:|
| `el_administrador_crea_una_docente_que_ingresa_y_luego_la_desactiva` | 1 | 2.6 | N | 1 |

### `test_hoja_rebrand_e2e.py`

| Prueba | Casos | s | Clase | Conservar |
|---|--:|--:|:-:|--:|
| `tokens_claros_del_quick_start_en_la_capa_theme` | 1 | 0.0 | S | 1 |
| `tema_oscuro_elegido` | 1 | 0.0 | S | 1 |
| `tema_oscuro_del_sistema_salvo_eleccion_clara` | 1 | 0.0 | S | 1 |
| `variables_de_celular_solo_hasta_699_px` | 1 | 0.0 | S | 1 |
| `instrument_sans_400_y_500_en_woff2_con_swap_y_besley_solo_600_optional` | 1 | 0.0 | S | 1 |
| `ninguna_transicion_de_ancho_ni_alto` | 1 | 0.0 | S | 1 |
| `ninguna_utilidad_repite_una_clase_de_componente` | 1 | 0.0 | S | 1 |
| `el_dialogo_transiciona_solo_transform_opacity_display_y_overlay` | 1 | 0.0 | S | 1 |
| `el_dialogo_y_su_velo_entran_con_starting_style` | 1 | 0.0 | S | 1 |
| `el_velo_del_dialogo_solo_transiciona_opacidad_display_y_overlay` | 1 | 0.0 | S | 1 |
| `con_la_marca_de_teclado_el_dialogo_y_su_velo_no_transicionan` | 1 | 0.0 | S | 1 |
| `con_movimiento_reducido_el_dialogo_no_se_desplaza` | 1 | 0.0 | S | 1 |
| `ninguna_regla_del_dialogo_anima_ancho_ni_alto` | 1 | 0.0 | S | 1 |
| `el_alto_del_dialogo_y_de_la_hoja_usa_dvh_no_svh` | 1 | 0.0 | S | 1 |
| `el_dialogo_de_la_lista_mide_760_sin_svh_ni_transiciones_de_ancho_o_alto` | 1 | 0.4 | N | 1 |
| `cifras_tabulares_de_instrument_sans_miden_lo_mismo` | 1 | 0.3 | N | 1 |
| `sin_tabular_nums_las_cifras_son_proporcionales` | 1 | 0.3 | N | 1 |

### `test_ingresar_e2e.py`

| Prueba | Casos | s | Clase | Conservar |
|---|--:|--:|:-:|--:|
| `de_la_raiz_al_inicio_de_sesion_y_a_la_portada` | 1 | 0.7 | N | 1 |
| `la_direccion_llega_a_su_inicio` | 1 | 0.5 | B | 0 |
| `mostrar_contrasena_alterna_la_vista` | 1 | 0.4 | N | 1 |
| `sin_javascript_no_hay_boton_y_el_formulario_se_envia` | 1 | 0.5 | N | 1 |
| `envio_en_curso_cambia_el_boton_y_deja_los_campos_de_solo_lectura` | 1 | 0.5 | N | 1 |
| `tras_un_rechazo_el_foco_va_al_error_y_tab_lleva_a_usuario` | 1 | 0.5 | N | 1 |
| `ingresando_cambia_el_fondo_a_folder_con_giro_y_campos_punteados` | 1 | 0.5 | N | 1 |
| `con_movimiento_reducido_el_giro_no_gira` | 1 | 0.4 | N | 1 |
| `enviar_con_enter_desde_contrasena_anuncia_ingresando_en_la_region_status` | 1 | 0.4 | N | 1 |
| `enviar_con_el_boton_anuncia_ingresando_en_la_region_status` | 1 | 0.4 | N | 1 |
| `con_un_campo_vacio_no_se_anuncia_nada` | 1 | 0.4 | N | 1 |
| `sin_la_region_de_estado_el_envio_sigue_bloqueando_el_doble_envio` | 1 | 0.5 | N | 1 |
| `al_restablecer_el_estado_la_region_queda_vacia` | 1 | 0.4 | N | 1 |

### `test_marco_rebrand_e2e.py`

| Prueba | Casos | s | Clase | Conservar |
|---|--:|--:|:-:|--:|
| `barra_de_una_pantalla_interior` | 2 | 1.6 | N | 2 |
| `pie_alineado_con_el_contenido` | 2 | 1.6 | N | 2 |
| `abrir_el_menu` | 1 | 1.1 | N | 1 |
| `teclado_no_sale_del_dialogo_y_escape_devuelve_el_foco` | 1 | 1.0 | N | 1 |
| `cerrar_con_la_x` | 1 | 1.6 | N | 1 |
| `toque_fuera_del_panel` | 1 | 1.4 | N | 1 |
| `sin_javascript_el_menu_lleva_a_la_portada` | 1 | 0.8 | N | 1 |
| `menu_abierto_no_desborda` | 4 | 4.4 | M | 2 |
| `abrir_el_menu_cierra_la_cuenta` | 1 | 1.2 | N | 1 |
| `abrir_la_cuenta` | 1 | 0.8 | N | 1 |
| `la_cuenta_con_seccion` | 1 | 0.8 | N | 1 |
| `la_cuenta_con_teclado` | 1 | 0.8 | N | 1 |
| `toque_fuera_de_la_cuenta` | 1 | 0.8 | N | 1 |
| `sin_javascript_la_cuenta_abre_y_cierra_la_sesion` | 1 | 0.8 | N | 1 |
| `cuenta_abierta_no_desborda` | 4 | 3.4 | M | 2 |
| `cada_pagina_carga_una_sola_hoja` | 3 | 1.9 | N | 3 |
| `e02_el_foco_aparece_de_una_vez` | 2 | 1.9 | N | 2 |
| `e03_cerrar_a_media_entrada_sigue_desde_donde_esta` | 1 | 1.2 | N | 1 |
| `cierre_nativo_durante_la_salida_no_cierra_la_reapertura` | 1 | 2.0 | N | 1 |
| `e05_la_pulsacion_solo_con_el_mouse` | 1 | 1.0 | N | 1 |
| `movimiento_reducido_el_menu_no_se_desplaza` | 1 | 0.9 | N | 1 |
| `a01_con_el_teclado_el_menu_abre_y_cierra_de_una_vez` | 1 | 0.8 | N | 1 |
| `a01_el_x_con_el_teclado_cierra_de_una_vez` | 1 | 1.1 | N | 1 |
| `a02_la_pulsacion_dura_90_ms_tambien_con_el_mouse_encima` | 1 | 0.8 | N | 1 |
| `a03_la_marca_del_mouse_dura_solo_su_pulsacion` | 1 | 0.9 | N | 1 |
| `la_marca_de_teclado_va_en_html_con_una_tecla_y_se_quita_con_el_puntero` | 1 | 0.7 | N | 1 |
| `la_marca_de_teclado_no_toca_la_marca_del_mouse_ni_el_menu` | 1 | 1.9 | N | 1 |

### `test_portada_e2e.py`

| Prueba | Casos | s | Clase | Conservar |
|---|--:|--:|:-:|--:|
| `a_1280_asistencia_ocupa_la_columna_principal` | 1 | 3.5 | N | 1 |
| `a_360_las_tres_se_apilan_en_el_orden_del_dom` | 1 | 0.7 | N | 1 |
| `a_360_sesiones_y_notas_llevan_la_miniatura_junto_al_texto` | 2 | 1.3 | N | 2 |
| `en_asistencia_el_boton_va_debajo_de_la_miniatura` | 2 | 1.3 | N | 2 |
| `las_miniaturas_llevan_el_mismo_papel_en_los_dos_temas` | 2 | 1.3 | N | 2 |
| `los_tokens_aplicados_toman_su_valor_del_tema` | 2 | 1.4 | N | 2 |
| `el_saludo_hereda_la_altura_de_linea_del_titulo` | 2 | 1.1 | N | 2 |
| `la_barra_de_la_portada_no_es_una_franja_ni_se_queda_fija` | 2 | 1.7 | N | 2 |
| `tarjeta_proximamente_avisa_sin_mover_la_miniatura` | 1 | 0.7 | N | 1 |
| `un_segundo_toque_vuelve_a_escribir_el_aviso` | 1 | 0.7 | N | 1 |
| `el_aviso_se_vacia_a_los_tres_segundos` | 1 | 3.9 | N | 1 |
| `el_documento_no_se_desplaza_en_horizontal` | 18 | 8.8 | M | 9 |
| `la_pildora_no_tiene_animacion` | 2 | 1.5 | N | 2 |
| `la_tarjeta_asistencia_lleva_a_la_asistencia_de_hoy` | 1 | 0.9 | N | 1 |
| `toda_la_tarjeta_notas_lleva_a_la_hoja` | 1 | 0.9 | N | 1 |
| `la_portada_con_y_sin_pildora_pasa_axe` | 8 | 6.9 | M | 4 |
| `la_portada_no_se_desplaza_en_horizontal` | 8 | 4.9 | M | 4 |

### `test_rendimiento_e2e.py`

| Prueba | Casos | s | Clase | Conservar |
|---|--:|--:|:-:|--:|
| `inicio_de_sesion_con_slow_4g` | 1 | 2.2 | N | 1 |

### `test_asignar_seccion_e2e.py`

| Prueba | Casos | s | Clase | Conservar |
|---|--:|--:|:-:|--:|
| `el_administrador_asigna_la_seccion_y_la_docente_la_ve` | 1 | 5.5 | N | 1 |
| `la_portada_con_la_seccion_pasa_axe` | 2 | 1.7 | B | 0 |
| `la_portada_con_la_seccion_no_desborda_a_320_px` | 2 | 1.1 | M | 1 |

### `test_estudiantes_e2e.py`

| Prueba | Casos | s | Clase | Conservar |
|---|--:|--:|:-:|--:|
| `ver_estudiantes_abre_el_dialogo_sin_cambiar_la_direccion` | 1 | 3.9 | N | 1 |
| `el_foco_entra_al_titulo_del_dialogo` | 1 | 0.7 | N | 1 |
| `esc_cierra_el_dialogo_y_el_foco_vuelve_al_enlace` | 1 | 0.7 | N | 1 |
| `cerrar_cierra_el_dialogo_y_el_foco_vuelve_al_enlace` | 1 | 1.3 | N | 1 |
| `atras_cierra_el_dialogo_y_la_portada_sigue` | 1 | 1.1 | N | 1 |
| `cerrar_consume_la_entrada_del_historial_y_se_puede_volver_a_abrir` | 1 | 1.5 | N | 1 |
| `el_dialogo_deja_la_portada_inerte_y_sin_desplazamiento` | 1 | 0.8 | N | 1 |
| `la_portada_con_el_aviso_pasa_axe` | 4 | 3.7 | M | 2 |
| `la_lista_vacia_en_el_dialogo_pasa_axe` | 4 | 4.8 | M | 2 |
| `la_lista_vacia_como_pagina_completa_pasa_axe` | 4 | 3.6 | M | 1 |
| `la_portada_y_la_lista_vacia_no_se_desplazan_en_horizontal` | 6 | 3.9 | M | 3 |
| `el_titulo_recibe_el_foco_sin_contorno_y_los_controles_si` | 2 | 1.6 | N | 2 |
| `la_portada_con_el_aviso_carga_empezando_arriba` | 4 | 5.2 | M | 2 |
| `cerrar_es_un_boton_con_borde_de_44_px_con_icono_y_texto` | 2 | 1.9 | N | 2 |
| `camino_ideal_importa_los_25_con_lineas_en_blanco` | 1 | 1.3 | N | 1 |
| `caso_de_error_no_guarda_nada_y_conserva_el_texto` | 1 | 1.2 | N | 1 |
| `sesion_vencida_al_importar_lleva_la_pagina_a_ingresar` | 1 | 1.3 | N | 1 |
| `pegar_y_revisar_lista_pasan_axe` | 4 | 7.2 | M | 2 |
| `tras_importar_y_cerrar_la_portada_ya_no_muestra_el_aviso` | 1 | 1.5 | N | 1 |
| `un_nombre_de_120_mas_120_se_lee_completo_en_el_dialogo` | 2 | 1.6 | N | 2 |
| `la_lista_con_estudiantes_pasa_axe` | 4 | 6.2 | M | 2 |
| `la_lista_como_pagina_completa_pasa_axe` | 4 | 4.2 | M | 1 |
| `revisar_lista_como_pagina_completa_pasa_axe` | 4 | 4.5 | M | 1 |
| `flujo_alternativo_valido_agrega_y_la_cabecera_pasa_a_26` | 1 | 1.2 | N | 1 |
| `corregir_un_nombre_vuelve_a_la_lista_con_el_nombre_corregido` | 1 | 1.2 | N | 1 |
| `agregar_y_editar_pasan_axe` | 4 | 9.3 | M | 2 |
| `agregar_con_homonimo_como_pagina_completa_pasa_axe` | 4 | 4.4 | M | 1 |
| `quitar_uno_baja_la_cabecera_en_uno` | 1 | 1.2 | N | 1 |
| `vaciar_25_deja_la_lista_vacia_y_el_aviso_vuelve_a_la_portada` | 1 | 1.4 | N | 1 |
| `sin_javascript_todo_funciona_como_pagina_completa` | 1 | 2.2 | N | 1 |
| `quitar_vaciar_y_los_bloqueos_pasan_axe` | 4 | 9.7 | M | 2 |
| `tomar_la_asistencia_abre_la_asistencia_como_pagina_completa` | 1 | 1.4 | N | 1 |
| `la_lista_con_el_aviso_de_importados_pasa_axe` | 4 | 6.3 | M | 2 |
| `a_320_la_lista_con_el_aviso_no_se_desplaza_en_horizontal` | 1 | 1.2 | N | 1 |
| `agregar_en_una_seccion_que_ya_no_es_suya_lleva_a_sin_permiso` | 1 | 1.2 | N | 1 |
| `pegar_lista_como_pagina_completa_pasa_axe` | 4 | 4.2 | M | 1 |
| `la_lista_con_el_aviso_de_importados_como_pagina_completa_pasa_axe` | 4 | 5.9 | M | 1 |
| `agregar_como_pagina_completa_pasa_axe` | 4 | 7.2 | M | 1 |
| `editar_como_pagina_completa_pasa_axe` | 4 | 4.6 | M | 1 |
| `quitar_vaciar_y_los_bloqueos_como_pagina_completa_pasan_axe` | 4 | 9.1 | M | 1 |
| `un_nombre_de_120_mas_120_se_lee_completo_como_pagina_completa` | 4 | 3.2 | N | 4 |
| `a_360_el_pie_apila_sus_acciones_a_todo_el_ancho` | 1 | 0.8 | N | 1 |
| `al_cambiar_de_vista_el_cuerpo_del_dialogo_vuelve_arriba` | 1 | 1.0 | N | 1 |
| `con_40_el_ultimo_editar_se_alcanza_desplazando_el_cuerpo` | 2 | 2.4 | N | 2 |

### `test_periodos_e2e.py`

| Prueba | Casos | s | Clase | Conservar |
|---|--:|--:|:-:|--:|
| `el_administrador_llena_los_cuatro_bimestres_y_guarda` | 1 | 1.6 | N | 1 |
| `un_cruce_muestra_el_mensaje_junto_a_la_fila` | 1 | 1.2 | B | 0 |
| `la_ficha_con_filas_vacias_pasa_axe` | 4 | 5.2 | M | 2 |
| `la_ficha_con_el_error_pasa_axe` | 4 | 6.8 | M | 2 |
| `la_ficha_de_un_anio_cerrado_pasa_axe` | 4 | 4.4 | M | 2 |
| `a_360_px_la_ficha_no_se_desplaza_en_horizontal` | 2 | 1.9 | M | 1 |

### `test_borradores_e2e.py`

| Prueba | Casos | s | Clase | Conservar |
|---|--:|--:|:-:|--:|
| `el_borrador_vuelve_al_recargar_y_descartar_lo_borra` | 1 | 4.2 | N | 1 |
| `el_borrador_sobrevive_a_cerrar_el_navegador_y_su_guardar_guarda` | 1 | 1.9 | N | 1 |
| `el_dispositivo_guarda_solo_identificadores_niveles_conclusiones_y_fechas` | 1 | 1.1 | N | 1 |
| `otra_cuenta_en_el_mismo_navegador_no_ve_el_borrador` | 1 | 1.6 | N | 1 |
| `sin_almacenamiento_la_hoja_guarda_igual` | 1 | 1.8 | N | 1 |
| `un_estudiante_que_ya_no_es_activo_sale_del_borrador_con_aviso` | 1 | 1.2 | N | 1 |
| `cerrar_sesion_desde_la_portada_borra_los_borradores_de_la_cuenta` | 1 | 1.4 | N | 1 |
| `el_cierre_por_inactividad_conserva_el_borrador` | 1 | 1.5 | N | 1 |
| `un_borrador_mas_antiguo_que_la_nota_avisa_y_guardar_guarda_lo_que_muestra` | 1 | 2.2 | N | 1 |
| `una_nota_cambiada_en_otro_navegador_detiene_el_guardado` | 1 | 2.3 | N | 1 |
| `lo_que_cambia_en_una_pestana_aparece_en_la_otra` | 1 | 1.4 | N | 1 |
| `la_misma_celda_en_las_dos_pestanas_conserva_lo_de_cada_una_y_avisa` | 1 | 1.2 | N | 1 |
| `salir_con_cambios_nombra_las_areas_de_todos_los_periodos_y_conserva_el_borrador` | 1 | 1.6 | N | 1 |
| `cambiar_de_periodo_no_pregunta_y_conserva_el_borrador` | 1 | 1.3 | N | 1 |
| `cerrar_sesion_con_cambios_dice_que_los_borradores_se_borraran` | 1 | 1.4 | N | 1 |
| `cerrar_sesion_desde_competencias_con_marcas_sin_guardar_borra_los_borradores` | 1 | 1.9 | N | 1 |
| `seguir_editando_tras_cerrar_sesion_conserva_el_borrador` | 1 | 1.7 | N | 1 |
| `recargar_con_cambios_muestra_el_aviso_del_navegador` | 1 | 1.0 | N | 1 |
| `tras_una_respuesta_perdida_volver_al_valor_anterior_sigue_siendo_un_cambio` | 1 | 1.3 | N | 1 |
| `un_cambio_de_otra_pestana_con_otra_base_avisa_la_nota_cambiada` | 1 | 1.3 | N | 1 |
| `cerrar_sesion_en_otra_pestana_impide_volver_a_escribir_borradores` | 1 | 1.7 | N | 1 |

### `test_competencias_e2e.py`

| Prueba | Casos | s | Clase | Conservar |
|---|--:|--:|:-:|--:|
| `desmarcar_y_guardar_persiste_al_recargar` | 1 | 4.4 | N | 1 |
| `guardar_sin_tocar_nada_guarda_todo_marcado` | 1 | 1.0 | N | 1 |
| `desmarcar_todo_no_se_guarda_y_dice_por_que` | 1 | 2.1 | N | 1 |
| `las_areas_del_docente_de_curso_no_se_pueden_marcar` | 1 | 1.0 | B | 0 |
| `la_capsula_muestra_un_area_a_la_vez` | 1 | 0.9 | N | 1 |
| `la_capsula_no_da_la_vuelta_en_los_extremos` | 1 | 0.9 | N | 1 |
| `las_marcas_de_un_area_se_conservan_y_se_guardan_desde_otra` | 1 | 1.2 | N | 1 |
| `el_guardado_fijo_del_celular_dice_el_total_global` | 1 | 0.9 | N | 1 |
| `en_pc_se_ven_las_diez_areas_y_el_panel` | 1 | 1.0 | N | 1 |
| `a_899_px_se_ve_un_area_a_la_vez_con_la_capsula` | 1 | 0.9 | N | 1 |
| `con_tab_la_ultima_fila_queda_sobre_la_barra` | 1 | 1.2 | N | 1 |
| `con_tab_la_ultima_fila_queda_sobre_la_barra_de_dos_filas` | 1 | 1.3 | N | 1 |
| `el_borrador_de_un_periodo_se_conserva_y_el_boton_lo_dice` | 1 | 1.1 | N | 1 |
| `corregir_un_periodo_anterior_no_toca_el_vigente` | 1 | 1.1 | N | 1 |
| `el_periodo_futuro_no_se_puede_elegir` | 1 | 0.9 | B | 0 |
| `con_tab_y_enter_el_foco_sigue_en_el_boton_del_periodo` | 1 | 0.9 | N | 1 |
| `deshacer_vuelve_a_lo_guardado` | 1 | 1.1 | N | 1 |
| `deshacer_no_aparece_en_el_bimestre_4_sin_cambios` | 1 | 0.9 | N | 1 |
| `deshacer_aparece_con_un_cambio_en_el_bimestre_4` | 1 | 0.9 | N | 1 |
| `la_obligatoria_con_espacio_no_cambia_y_anuncia_su_motivo` | 1 | 1.0 | N | 1 |
| `las_obligatorias_se_guardan_con_las_demas` | 1 | 1.0 | N | 1 |
| `el_resumen_cuenta_las_obligatorias` | 1 | 1.0 | N | 1 |
| `el_ultimo_periodo_explica_las_obligatorias` | 1 | 0.9 | N | 1 |
| `desmarcar_una_competencia_con_notas_muestra_el_motivo` | 1 | 1.0 | N | 1 |
| `un_guardado_que_choca_con_notas_las_bloquea_en_pantalla` | 1 | 1.0 | N | 1 |
| `sin_red_dice_que_no_se_pudo_guardar_y_un_guardado_despues_lo_quita` | 1 | 1.1 | N | 1 |
| `con_la_sesion_vencida_no_guarda_y_ofrece_volver_a_ingresar` | 1 | 1.1 | N | 1 |
| `guardar_en_una_seccion_que_ya_no_es_suya_lleva_a_sin_permiso` | 1 | 1.1 | N | 1 |
| `el_dialogo_de_salida_nombra_los_periodos_y_pone_el_foco_en_seguir_editando` | 1 | 1.2 | N | 1 |
| `salir_por_el_menu_con_cambios_abre_el_dialogo_sobre_el_cajon` | 1 | 1.3 | N | 1 |
| `escape_y_seguir_editando_conservan_los_cambios` | 1 | 1.8 | N | 1 |
| `salir_sin_guardar_sale_sin_aviso_del_navegador` | 1 | 1.4 | N | 1 |
| `sin_cambios_no_hay_pregunta` | 1 | 1.1 | N | 1 |
| `recargar_con_cambios_muestra_el_aviso_del_navegador` | 1 | 1.3 | N | 1 |
| `recargar_sin_cambios_no_muestra_aviso` | 1 | 1.1 | N | 1 |
| `en_vacaciones_se_elige_un_periodo_pasado` | 1 | 1.2 | N | 1 |
| `sin_periodos_solo_el_aviso` | 1 | 0.9 | B | 0 |
| `la_pantalla_con_marcas_pasa_axe` | 2 | 2.7 | N | 2 |
| `el_dialogo_de_salida_pasa_axe` | 2 | 3.0 | N | 2 |
| `no_hay_desplazamiento_horizontal_a_320_y_360` | 2 | 2.7 | N | 2 |

### `test_hoja_e2e.py`

| Prueba | Casos | s | Clase | Conservar |
|---|--:|--:|:-:|--:|
| `escribir_el_nivel_baja_a_la_misma_competencia_del_siguiente` | 1 | 4.2 | N | 1 |
| `la_barra_de_niveles_elige_con_flechas_y_enter` | 1 | 0.9 | N | 1 |
| `a_no_abre_ningun_recuadro` | 1 | 1.0 | N | 1 |
| `el_nombre_de_la_competencia_aparece_al_recibir_el_foco` | 1 | 0.9 | N | 1 |
| `el_panel_del_celular_elige_y_pasa_al_siguiente` | 1 | 1.1 | N | 1 |
| `siguiente_avanza_con_una_b_sin_conclusion` | 1 | 1.2 | N | 1 |
| `elegir_b_abre_el_recuadro_y_listo_conserva_el_texto` | 1 | 1.2 | N | 1 |
| `el_recuadro_de_la_ultima_columna_se_ve_entero_junto_a_la_celda` | 1 | 1.0 | N | 1 |
| `el_nivel_queda_centrado_bajo_su_competencia` | 1 | 1.2 | N | 1 |
| `la_vista_previa_muestra_el_comienzo_de_la_conclusion` | 1 | 1.8 | N | 1 |
| `de_b_a_a_borra_la_conclusion_al_guardar` | 1 | 1.1 | N | 1 |
| `la_conclusion_de_un_trasladado_se_lee_sin_editar` | 1 | 0.9 | N | 1 |
| `suprimir_no_borra_una_nota_guardada` | 1 | 1.0 | N | 1 |
| `rellenar_vacias_solo_toca_las_vacias_y_queda_como_borrador` | 1 | 1.3 | N | 1 |
| `guardar_persiste_al_recargar` | 1 | 1.2 | N | 1 |
| `c_sin_conclusion_no_guarda_nada_y_marca_la_celda` | 1 | 1.2 | N | 1 |
| `el_panel_muestra_el_error_y_la_instruccion_a_la_vez` | 1 | 1.1 | N | 1 |
| `el_editor_de_pc_muestra_el_error_y_la_instruccion_a_la_vez` | 1 | 1.3 | N | 1 |
| `sin_conexion_conserva_todo_y_reintentar_guarda` | 1 | 1.3 | N | 1 |
| `con_la_sesion_vencida_no_guarda_y_ofrece_volver_a_ingresar` | 1 | 1.2 | N | 1 |
| `guardar_en_una_seccion_que_ya_no_es_suya_lleva_a_sin_permiso` | 1 | 1.3 | N | 1 |
| `cambiar_de_area_conserva_lo_digitado_y_marca_el_punto` | 1 | 1.2 | N | 1 |
| `el_area_del_docente_de_curso_no_tiene_celdas` | 1 | 1.0 | N | 1 |
| `competencias_vuelve_a_las_notas_del_periodo_y_el_area` | 1 | 1.5 | N | 1 |
| `una_nota_cambiada_desde_otro_lado_detiene_el_guardado_y_el_segundo_guarda` | 1 | 1.3 | N | 1 |
| `la_barra_cuenta_las_notas_que_faltan` | 1 | 1.0 | B | 0 |
| `un_trasladado_sin_nivel_no_cuenta` | 1 | 0.9 | B | 0 |
| `el_borrador_baja_el_conteo_y_se_anuncia` | 1 | 0.9 | N | 1 |
| `tocar_el_conteo_deja_solo_los_pendientes_y_enter_salta` | 1 | 1.1 | N | 1 |
| `en_el_celular_el_panel_salta_entre_faltantes` | 1 | 1.0 | N | 1 |
| `con_todo_guardado_dice_area_completa` | 1 | 0.9 | B | 0 |
| `completa_sin_guardar_dice_un_cambio_y_sin_faltantes` | 1 | 1.0 | N | 1 |
| `axe_con_notas_errores_filtro_y_dialogo` | 4 | 14.9 | M | 2 |
| `personal_social_no_desplaza_la_pagina_y_la_tira_se_desplaza_sola` | 2 | 1.8 | N | 2 |
| `las_columnas_que_no_caben_se_desplazan_con_el_nombre_fijo` | 1 | 1.3 | N | 1 |
| `el_area_activa_queda_a_la_vista_en_la_tira` | 1 | 1.0 | N | 1 |
| `las_areas_tactiles_miden_44_px` | 1 | 1.2 | N | 1 |
| `el_lector_lee_estudiante_competencia_y_nivel` | 1 | 0.8 | N | 1 |
| `la_hoja_mas_grande_con_slow_4g` | 1 | 3.6 | N | 1 |

### `test_detalle_e2e.py`

| Prueba | Casos | s | Clase | Conservar |
|---|--:|--:|:-:|--:|
| `eliminar_abre_el_dialogo_con_foco_en_cancelar_y_confirmar_lleva_a_mis_sesiones` | 1 | 2.5 | N | 1 |
| `compartir_abre_los_terminos_volver_devuelve_el_foco_y_aceptar_deja_el_chip` | 1 | 2.4 | N | 1 |
| `la_pagina_y_sus_dialogos_son_accesibles_y_no_se_desplazan` | 2 | 4.7 | N | 2 |

### `test_repositorio_e2e.py`

| Prueba | Casos | s | Clase | Conservar |
|---|--:|--:|:-:|--:|
| `buscar_filtrar_ver_sin_coincidencias_borrar_y_abrir_una_sesion` | 1 | 4.0 | N | 1 |
| `las_pestanas_se_manejan_con_las_flechas_y_atras_vuelve` | 1 | 1.2 | N | 1 |
| `el_buscador_conserva_el_foco_y_lo_escrito_mientras_la_lista_cambia` | 1 | 3.3 | N | 1 |
| `el_panel_filtrar_abre_con_foco_aplica_al_tocar_y_esc_lo_cierra` | 1 | 1.3 | N | 1 |
| `tras_enviar_una_sesion_la_lista_y_el_contador_se_actualizan` | 1 | 2.3 | N | 1 |
| `las_listas_y_el_panel_son_accesibles_y_no_se_desplazan` | 2 | 4.9 | N | 2 |

### `test_sesiones_e2e.py`

| Prueba | Casos | s | Clase | Conservar |
|---|--:|--:|:-:|--:|
| `abrir_el_popup_enfoca_su_titulo_y_deja_la_pantalla_inerte` | 1 | 3.9 | N | 1 |
| `tocar_afuera_no_cierra_el_popup` | 1 | 1.2 | N | 1 |
| `cancelar_cierra_sin_guardar_y_al_abrir_otra_vez_esta_vacio` | 2 | 3.9 | N | 2 |
| `orden_de_los_botones` | 2 | 2.3 | N | 2 |
| `archivo_elegido_muestra_nombre_tipo_tamano_y_cambiar` | 1 | 1.4 | N | 1 |
| `un_docx_se_reconoce_como_word` | 1 | 1.1 | N | 1 |
| `sin_area_ni_titulo_muestra_sus_errores_y_enfoca_el_primero` | 1 | 1.5 | N | 1 |
| `sin_archivo_lo_pide` | 1 | 1.4 | N | 1 |
| `corregir_un_campo_quita_su_error` | 1 | 1.3 | N | 1 |
| `un_archivo_que_no_es_pdf_aunque_se_llame_asi_se_rechaza` | 1 | 1.4 | N | 1 |
| `un_archivo_de_mas_de_4_mb_se_rechaza` | 1 | 2.0 | N | 1 |
| `enviar_sin_compartir_va_directo_y_muestra_el_exito` | 1 | 2.0 | N | 1 |
| `aceptar_y_enviar_comparte_y_guarda_la_aceptacion` | 1 | 2.3 | N | 1 |
| `volver_cierra_solo_los_terminos_y_conserva_el_formulario` | 2 | 3.9 | N | 2 |
| `datos_incompletos_con_la_casilla_marcada_no_abren_los_terminos` | 1 | 1.5 | N | 1 |
| `subir_otra_abre_un_formulario_nuevo` | 1 | 2.4 | N | 1 |
| `recargar_despues_del_exito_no_muestra_el_mensaje_ni_envia_otra` | 1 | 2.0 | N | 1 |
| `atras_en_el_formulario_lo_cierra_y_sigue_en_sesiones` | 1 | 1.6 | N | 1 |
| `atras_en_los_terminos_cierra_solo_los_terminos` | 1 | 2.2 | N | 1 |
| `subiendo_bloquea_campos_botones_y_esc` | 1 | 2.2 | N | 1 |
| `atras_mientras_sube_no_cierra_y_la_subida_sigue` | 1 | 2.2 | N | 1 |
| `recargar_mientras_sube_pide_confirmar` | 1 | 2.3 | N | 1 |
| `se_corta_y_al_reintentar_se_envia_una_sola_vez` | 1 | 2.5 | N | 1 |
| `se_guardo_pero_no_llego_la_respuesta_y_el_reintento_da_el_mismo_exito` | 1 | 2.1 | N | 1 |
| `los_estados_del_boceto_son_accesibles_y_sin_desplazamiento` | 2 | 5.3 | N | 2 |
| `pantalla_baja_los_terminos_se_desplazan_y_sus_botones_siguen_a_la_vista` | 1 | 1.7 | N | 1 |
| `b02_en_una_pantalla_muy_baja_el_cuerpo_del_popup_sigue_a_la_vista` | 2 | 2.3 | N | 2 |
| `en_el_celular_subir_una_sesion_se_lee_completo` | 1 | 0.9 | N | 1 |
| `sesiones_carga_con_slow_4g` | 1 | 3.4 | N | 1 |
