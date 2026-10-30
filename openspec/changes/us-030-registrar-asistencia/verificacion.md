# Verificación: US-030 – Registrar la asistencia de una jornada

Rama `feature/US-030-registrar-asistencia`. Pruebas en `src/backend/`. Abreviaturas: `mod` = `asistencia/tests/test_modelos.py`, `srv` = `asistencia/tests/test_servicios.py`, `vis` = `asistencia/tests/test_vistas.py`, `e2e` = `asistencia/tests/test_asistencia_e2e.py`, `ina` = `cuentas/tests/test_inactividad.py`, `pan` = `cuentas/tests/test_pantallas.py`, `dim` = `cuentas/tests/test_dimensiones.py`, `por` = `cuentas/tests/test_portada_e2e.py`, `emod` = `institucion/tests/test_modelos_estudiante.py`, `esrv` = `institucion/tests/test_servicios_estudiantes.py`, `ee2e` = `institucion/tests/test_estudiantes_e2e.py`.

## Escenarios de `asistencia-jornada`

| Escenario | Prueba |
| --- | --- |
| Sección de otra docente | `vis::test_otra_docente_recibe_404_y_no_guarda` |
| Sección de un año cerrado | `vis::test_una_seccion_del_anio_cerrado_da_404` |
| Otro rol | `vis::test_la_direccion_llega_a_su_pantalla`; `ina::test_una_peticion_htmx_de_otro_rol_lleva_a_su_pantalla_con_hx_redirect` |
| Estudiante de otra sección | `vis::test_un_estudiante_de_otra_seccion_responde_404`, `test_restantes_con_un_id_ajeno_responde_404_sin_guardar`; `srv::test_estudiante_de_otra_seccion_se_rechaza_sin_crear_jornada`, `test_un_id_ajeno_hace_fallar_todo_el_lote` |
| Selector de la semana | `vis::test_el_selector_tiene_hoy_como_unico_dia_activo`, `test_la_semana_que_cruza_de_mes_lo_dice`; `srv::test_semana_de_un_miercoles`, `test_semana_que_cruza_de_mes` |
| Fecha de Lima | `vis::test_a_las_23_30_de_lima_es_el_dia_de_lima_y_no_el_de_utc` (agregada en 3.2; falla con `TIME_ZONE = "UTC"`) |
| Guardado de otro día | `vis::test_un_guardado_de_otro_dia_responde_409`, `test_restantes_de_otro_dia_responde_409`; `srv::test_fecha_que_no_es_hoy_se_rechaza_sin_crear_jornada`, `test_marcar_restantes_rechaza_una_fecha_que_no_es_hoy` |
| Sábado | `vis::test_el_sabado_no_hay_clases`, `test_un_guardado_en_sabado_responde_409`; `srv::test_sabado_se_rechaza_sin_crear_jornada`, `test_en_fin_de_semana_es_la_semana_que_acaba_de_pasar_sin_hoy`; `e2e::test_el_fin_de_semana_pasa_axe` |
| Lista vacía | `vis::test_sin_estudiantes_un_aviso_lleva_a_la_lista`, `test_solo_con_retirados_es_una_seccion_sin_estudiantes`; `e2e::test_la_seccion_sin_estudiantes_pasa_axe` |
| Primera vez en el día | `vis::test_primera_vez_en_el_dia_todos_sin_marcar`, `test_las_filas_van_en_orden_con_nombre_completo_y_su_circulo`; `srv::test_lista_de_hoy_ordena_y_numera_de_1_a_m_solo_los_activos` |
| Estudiante retirado | `vis::test_los_no_activos_van_al_final_sin_circulo_y_sin_contar`, `test_un_estudiante_retirado_responde_404`; `srv::test_estudiante_no_activo_se_rechaza_sin_crear_jornada` |
| Nombre largo a 320 px | `e2e::test_nombre_de_120_mas_120_a_320_px` |
| Camino ideal | `e2e::test_camino_ideal` (contado en la base) |
| Después de Justificado | `srv::test_la_fila_dice_su_estado_y_el_siguiente` (Justificado → Asistió) |
| Volver a abrir | `e2e::test_volver_a_abrir_muestra_lo_guardado`; `vis::test_un_estado_guardado_se_dibuja_en_palabras_y_en_el_circulo` |
| Primer toque del día | `srv::test_el_primer_toque_crea_la_jornada`, `test_dos_toques_dejan_una_sola_jornada`; `mod::test_segunda_jornada_de_la_misma_seccion_y_fecha_la_rechaza_la_base` |
| Abrir sin tocar | `vis::test_abrir_la_asistencia_no_crea_la_jornada`; `srv::test_lista_de_hoy_sin_jornada_no_la_crea` |
| Jornada ya registrada | `e2e::test_volver_a_abrir_muestra_lo_guardado`; `vis::test_un_estado_guardado_se_dibuja_en_palabras_y_en_el_circulo` |
| Envío repetido por conexión inestable | `vis::test_el_mismo_guardado_dos_veces_deja_una_fila`; `srv::test_el_mismo_guardado_dos_veces_deja_una_fila`; `mod::test_segundo_estado_del_mismo_estudiante_en_la_jornada_lo_rechaza_la_base` |
| Toques rápidos mientras se guarda | `e2e::test_toques_rapidos_mientras_se_guarda`, `test_aviso_al_salir_con_un_guardado_en_curso_que_vuelve_al_confirmado`; `srv::test_dos_estados_seguidos_dejan_el_ultimo` |
| Cortes de red | `e2e::test_diez_cortes_de_red_sin_perder_ni_duplicar`, `test_volver_al_estado_guardado_tras_un_fallo_se_guarda`, `test_el_lote_no_sale_dos_veces_al_volver_la_red`, `test_un_rechazo_no_descarta_las_marcas_pendientes_de_otras_filas`, `test_un_rechazo_del_lote_no_descarta_la_fila_que_salio_de_el` (tras un 400, 404 o 409, las pendientes vuelven por `sessionStorage`). Sin prueba: el corte después de que el servidor aceptó el POST (hallazgo 2 de la A2), que va a la deuda |
| Flujo alternativo válido | `e2e::test_flujo_alternativo_valido`; `vis::test_restantes_guarda_asistio_y_responde_204`; `srv::test_marcar_restantes_pone_asistio_a_los_sin_marcar` |
| Con estudiantes ya marcados | `e2e::test_marcar_los_restantes_no_toca_a_los_ya_marcados`; `srv::test_marcar_restantes_no_pisa_a_los_ya_marcados` |
| Sin estudiantes Sin marcar | `vis::test_la_jornada_completa_se_dibuja_con_el_cierre` (sin el botón) |
| Deshacer | `e2e::test_deshacer_no_guarda_nada` |
| Fin de la cuenta | `e2e::test_fin_de_la_cuenta_y_su_anuncio`, `test_la_cuenta_se_pausa_con_el_puntero`, `test_la_cuenta_se_pausa_con_el_foco_de_teclado`, `test_el_foco_que_pone_la_pantalla_no_pausa_la_cuenta` |
| Toque durante la cuenta | `e2e::test_toque_durante_la_cuenta` |
| Cerrar la pestaña durante la cuenta | `e2e::test_cerrar_la_pagina_durante_la_cuenta_guarda_el_lote` |
| Anuncio de la barra | `e2e::test_fin_de_la_cuenta_y_su_anuncio` (el texto en la región de anuncios; la cuenta con `aria-hidden` y la barra sin `aria-live`) |
| Nota guardada | `e2e::test_la_nota_se_guarda_al_salir_del_campo`, `test_la_nota_se_guarda_sola_al_dejar_de_escribir`; `vis::test_el_guardado_lleva_la_nota_de_justificacion`; `srv::test_la_nota_se_guarda_solo_con_justificado` |
| Nota demasiado larga | `srv::test_la_nota_de_100_caracteres_se_guarda`, `test_nota_de_101_caracteres_se_rechaza_sin_crear_jornada`; `vis::test_un_estado_o_una_nota_que_no_valen_responden_400` |
| Salir de Justificado | `srv::test_la_nota_se_borra_al_pasar_a_otro_estado`; `mod::test_nota_con_estado_distinto_de_justificado_la_rechaza_la_base` |
| Caso de error (avance) | `vis::test_marcar_los_n_restantes_cuenta_los_sin_marcar` (18 de 25); `srv::test_lista_de_hoy_cuenta_el_avance_y_los_totales`, `test_pendiente_hoy_con_la_jornada_sin_completar`; `e2e::test_el_avance_y_los_totales_cambian_con_cada_toque` |
| Totales a medio marcar | `vis::test_los_totales_del_panel_a_medio_marcar`; `srv::test_el_resumen_va_en_el_orden_de_la_pantalla` |
| Guardado sano | `e2e::test_guardado_sano` |
| Fallo de un guardado | `e2e::test_fallo_de_un_guardado` |
| Sin conexión | `e2e::test_sin_conexion_solo_al_tercer_fallo_y_una_vez` |
| Salir con una marca sin guardar | `e2e::test_aviso_al_salir_con_una_marca_pendiente`, `test_aviso_al_salir_con_un_guardado_en_curso_que_vuelve_al_confirmado`, `test_sin_nada_pendiente_se_sale_sin_aviso` |
| Última marca guardada | `e2e::test_el_cierre_aparece_tras_el_ultimo_guardado`, `test_el_cierre_tras_la_cuenta`; `vis::test_la_jornada_completa_se_dibuja_con_el_cierre` |
| Última marca sin guardar | `e2e::test_sin_cierre_con_la_ultima_marca_sin_guardar`, `test_sin_cierre_durante_la_cuenta_ni_tras_deshacer` |
| Toque tras 60 minutos sin actividad | `e2e::test_sesion_vencida_durante_los_toques`; `vis::test_con_la_sesion_vencida_un_guardado_con_htmx_recibe_hx_redirect`; `ina::test_una_peticion_htmx_vencida_responde_200_con_hx_redirect` |
| Revisión de cada vista | `e2e::test_la_lista_a_medio_marcar_pasa_axe`, `test_el_fin_de_semana_pasa_axe`, `test_la_seccion_sin_estudiantes_pasa_axe`, `test_las_vistas_de_la_parte_c_pasan_axe`, `test_nombre_de_120_mas_120_a_320_px` |

## Escenarios de `estudiantes-seccion`

Sin cambios desde US-006 y con sus pruebas: Nombre guardado en mayúsculas, Homónimo exacto en la misma sección, Mismo nombre en otra sección, Camino ideal y Líneas en blanco (ver el `verificacion.md` archivado de US-006).

| Escenario | Prueba |
| --- | --- |
| Estudiante nuevo | `emod::test_estudiante_nuevo_queda_activo_y_sin_fecha_de_estado`, `test_importar_lista_deja_activos_a_los_estudiantes`, `test_agregar_estudiante_lo_deja_activo` |
| Estado desconocido | `emod::test_estado_fuera_de_los_tres_lo_rechaza_la_base_de_datos`, `test_los_tres_estados_validos_se_guardan` |
| Paso siguiente tras importar | `ee2e::test_tomar_la_asistencia_abre_la_asistencia_como_pagina_completa`; `vis::test_el_aviso_de_importados_lleva_a_tomar_la_asistencia_de_hoy`, `test_sin_aviso_de_importados_no_hay_enlace_a_la_asistencia` |

Además: quitar y vaciar con asistencia real (`esrv::test_quitar_con_asistencia_real_lanza_y_no_borra`, `test_vaciar_con_asistencia_real_lanza_y_no_borra_ninguno`), y axe y 320 px de la lista con el aviso (`ee2e::test_la_lista_con_el_aviso_de_importados_pasa_axe`, `test_a_320_la_lista_con_el_aviso_no_se_desplaza_en_horizontal`).

## Escenarios de `pantallas-de-inicio`

Sin cambios desde US-005 y US-006 y con sus pruebas: Docente con varias secciones, Docente sin sección, Sección de un año cerrado, Enlace a la lista con una sección, Sin enlace con varias secciones, Sin enlace sin sección, Sección sin estudiantes y El aviso desaparece al cargar la lista.

| Escenario | Prueba |
| --- | --- |
| Portada al entrar | `pan::test_la_portada_saluda_con_el_nombre_completo`, `test_tres_tarjetas_en_orden_con_subtitulo_e_insignia` |
| Saludo según la hora | `pan::test_el_saludo_depende_de_la_hora_de_lima`; `srv::test_saludo_segun_la_hora` |
| Docente con una sección | `pan::test_la_portada_muestra_la_seccion_bajo_el_saludo_y_fuera_del_h1`; `srv::test_texto_fecha_en_espanol` |
| Asistencia de hoy pendiente | `pan::test_la_asistencia_de_hoy_pendiente_lleva_la_pildora`; `srv::test_pendiente_hoy_con_la_jornada_sin_completar`; `por::test_la_pildora_aparece_una_vez_con_una_subida_corta`, `test_con_reducir_movimiento_la_pildora_ya_esta_en_su_lugar` |
| Asistencia de hoy completa | `pan::test_con_la_jornada_completa_no_hay_pildora`; `srv::test_pendiente_hoy_es_falso_con_la_jornada_completa` |
| Fin de semana o sección sin estudiantes | `pan::test_el_sabado_no_hay_pildora`, `test_sin_estudiantes_no_hay_pildora`; `srv::test_pendiente_hoy_es_falso_en_sabado`, `test_pendiente_hoy_es_falso_sin_estudiantes_activos` |
| Tres dimensiones en "Próximamente" | `pan::test_sin_ninguna_disponible_la_tarjeta_inicial_es_sesiones`; `dim::test_sin_ninguna_disponible_abre_en_la_primera` (con las banderas apagadas; desde US-030, Asistencia está disponible) |
| Toque en una tarjeta "Próximamente" | `pan::test_las_tarjetas_proximamente_son_botones_sin_enlace`, `test_cada_tarjeta_proximamente_tiene_su_region_aria_live_vacia`; `por::test_tarjeta_proximamente_avisa_sin_mover_la_miniatura` |
| Dimensión activada por su historia | `dim::test_desde_us_030_solo_asistencia_esta_disponible`, `test_toda_dimension_disponible_resuelve_su_pantalla`; `pan::test_una_dimension_disponible_enlaza_a_su_pantalla` |
| Bandera activa sin pantalla | `dim::test_la_revision_detecta_una_bandera_activa_sin_pantalla` |
| Asistencia con una sección | `pan::test_con_una_seccion_asistencia_lleva_a_la_asistencia_de_hoy`; `por::test_la_tarjeta_asistencia_lleva_a_la_asistencia_de_hoy` |
| Asistencia sin sección única | `pan::test_sin_seccion_unica_asistencia_es_proximamente` |

Además: axe de la portada con y sin píldora (`por::test_la_portada_con_y_sin_pildora_pasa_axe`) y 320 px sin desplazamiento (`por::test_la_portada_con_la_pildora_no_se_desplaza_en_horizontal`).

## Revisión final (A2)

`/codex:adversarial-review --base main --background`, con foco en los specs del cambio y en RNF-011. Veredicto: *needs-attention*, 3 hallazgos high.

1. Un guardado en curso dejaba de contar como pendiente si los toques volvían al estado confirmado, y se salía sin aviso. Corregido: `pendiente()` cuenta también `enCurso`. Prueba: `e2e::test_aviso_al_salir_con_un_guardado_en_curso_que_vuelve_al_confirmado`.
2. Un POST aceptado antes de un corte puede terminar después del reintento y dejar la marca vieja con "Guardado" en pantalla. **A la deuda**, por decisión de Marco (estimado: 2 a 3 h). El riesgo está en D3 del design y el arreglo propuesto, en la deuda de "## Workflow follow-up" de `tasks.md`.
3. Un 400, 404 o 409 recargaba sin guardar las marcas pendientes de otras filas. Corregido: `recordarPendientes()` antes de recargar, sin la fila rechazada (así no hay bucle de recargas). Prueba: `e2e::test_un_rechazo_no_descarta_las_marcas_pendientes_de_otras_filas`.

Las dos pruebas se vieron en rojo antes del cambio.

Revisión del grupo 3: sin Critical; 1 Important corregido con su prueba, vista en rojo (un rechazo del lote también descartaba la fila tocada mientras el lote viajaba, que ya había salido de él; prueba `e2e::test_un_rechazo_del_lote_no_descarta_la_fila_que_salio_de_el`). En 3.2 se agregó `vis::test_a_las_23_30_de_lima_es_el_dia_de_lima_y_no_el_de_utc`. Las cifras de la DoD son las del final, con las dos pruebas nuevas.

## DoD 1 a 9

| N.° | Estado | Evidencia |
| --- | --- | --- |
| 1 | Cumple en local; **pendiente del PR** | `uv run pytest --cov`: 956 pasan, cobertura total 98,44 % (mínimo 80 %). La puerta Sonar way solo se ve en el PR |
| 2 | Cumple en local; **pendiente del PR** | Ruff sin hallazgos (`check` y `format --check`, en `verificar.py`). CodeQL y SonarQube Cloud solo corren en el PR |
| 3 | **Pendiente del PR (equipo)** | Aprobación de otra integrante |
| 4 | **Pendiente del PR** | Vista previa de Vercel del PR, con las migraciones `institucion/0004` y `asistencia/0001` en su rama de Neon |
| 5 | Cumple en local; **pendiente del PR** | Cada escenario con su prueba (tablas de arriba), salvo el caso de la A2 que va a la deuda. 244 e2e en verde (asistencia: 59). El canal se ve en el PR |
| 6 | Cumple | Jornada única, estado de destino con upsert, lote, nota, día de hoy y estudiante activo en `asistencia/servicios.py` (`srv`); las vistas no escriben en la BD |
| 7 | Cumple | Axe sin infracciones críticas ni graves en cada vista de la asistencia, en la portada con y sin píldora y en la lista con el aviso, claro y oscuro, 360 y 1280 px; sin desplazamiento horizontal a 320 px |
| 8 | Cumple | Solo nombres ficticios (los del boceto); ningún dato de la I.E. inventado |
| 9 | Cumple | Este cambio en OpenSpec, docstrings, DESIGN.md 0.4 y el Catálogo de rutas de `docs/03` (tres rutas nuevas). El README no cambia |

## Evidencia por parte

- **Grupo 1, parte B (1.2 y 1.3):** pruebas en `institucion/tests/test_modelos_estudiante.py`, `asistencia/tests/test_modelos.py` y `institucion/tests/test_servicios_estudiantes.py` (con asistencia real). Vistas en rojo antes del código; `makemigrations --check` sin cambios; `sqlmigrate` de `institucion/0004` (valor por defecto y `ck_estudiante_estado`) y de `asistencia/0001` (`uq_jornada`, `uq_asistencia`, `ck_asistencia_estado`, `ck_asistencia_nota`). Revisión de la parte: sin Critical ni Important.
- **Grupo 1, parte C (1.5 y 1.6):** pruebas en `asistencia/tests/test_servicios.py` (con `hoy` fijo) y `cuentas/tests/test_inactividad.py` (reloj congelado en 29 s y 30 s). Rojo antes del código. Revisión de la parte: sin Critical; 3 Important (pruebas que no fallaban al quitar `actualizado_en` del upsert, el `atomic` ni el borde de 30 s) corregidos y comprobados quitando cada comportamiento a propósito.
- **Grupo 2, parte A (2.1 y 2.2):** pruebas en `asistencia/tests/test_vistas.py` (rutas, acceso, CSRF, `HX-Redirect`, 204/400/404/409 y el enlace del aviso), `cuentas/tests/test_pantallas.py` (saludo según la hora, fecha, tarjeta Asistencia y píldora) y `test_dimensiones.py`; rojo antes del código. E2E en `test_portada_e2e.py` (píldora una vez y quieta con "reducir movimiento", axe con y sin píldora en ambos temas a 360 y 1280 px, 320 px sin desplazamiento) y `test_estudiantes_e2e.py` (el aviso abre la asistencia como página completa, axe y 320 px). Pruebas de US-001, US-005 y US-006 que miraban "Hola," o la línea sin fecha, actualizadas. Capturas de portada (360 y 1280) y de la lista con el aviso comparadas con `decision-final/capturas/`: iguales, salvo el alto de la ventana (800 frente a 900 px) en la portada de PC. `uv run pytest --cov`: 908, 98 %; e2e: 185 en verde. Revisión de la parte: sin Critical ni Important.
- **Grupo 2, parte B (2.4 y 2.5):** pruebas del HTML de `hoy` en `asistencia/tests/test_vistas.py` (selector con `aria-disabled`, semana que cruza de mes, avance, filas y nombre accesible por estado, no activos, nota solo en Justificado, "Marcar los N restantes" / "el restante", totales del panel, jornada completa sin trazo, sábado, sin estudiantes, `<noscript>` y rutas de guardado) y de `semana()` y las ayudas de la fila en `test_servicios.py`; rojo antes del código. E2E nuevas en `asistencia/tests/test_asistencia_e2e.py`: camino ideal (contado en la base), avance y totales en vivo, volver a abrir, toques rápidos con la ruta retenida por `page.route` (una petición en curso; la segunda lleva `TARDE`), guardado sano, nota al salir del campo y tras 800 ms, Intro y espacio, "N sin marcar" enfoca la fila bajo la franja, y axe de la lista a medio marcar, del fin de semana y de "sin estudiantes" en ambos temas a 360 y 1280 px. Capturas `asistencia-marcando-360-*`, `asistencia-pc-1280-*` y `asistencia-completa-*` (claro y oscuro) comparadas con `decision-final/capturas/`: iguales, salvo los estados de error del boceto (eso es la parte C). `test_plantillas.py` registra los íconos `chevron-left` y `chevron-right`; `test_estudiantes_e2e.py` espera el título "Asistencia · 2.º A". `uv run pytest --cov`: 955, 98 %; e2e en verde. Revisión de la parte: sin Critical; 2 Important corregidos con su prueba ("N sin marcar" no enfocaba ni dejaba visible la fila; faltaba axe de fin de semana y sin estudiantes). Visto por Marco: el tinte de la fila enfocada se cortaba en el relleno de la lista (también en el boceto); ahora llega al borde de la tarjeta, comprobado en capturas a 360, 940 y 1280 px.
- **Grupo 2, parte C (2.7):** E2E nuevas en `asistencia/tests/test_asistencia_e2e.py`, rojo antes del código: lote (flujo alternativo válido, no pisa a los ya marcados, Deshacer sin nada en la base y con la franja en "Sin cambios", fin de la cuenta con sus dos anuncios, toque durante la cuenta, cerrar la página durante la cuenta con `keepalive`, pausa con el puntero y con el foco de teclado, el foco que pone la pantalla no pausa); RNF-011 (10 cortes con `context.set_offline`: 20 filas en la base, ni perdidas ni duplicadas, cada fila fallida con "sin guardar. Reintentando…"; "1 sin guardar" y descripción accesible; "Sin conexión" al tercer fallo, una vez por aviso, contado con `MutationObserver`; volver al estado guardado tras un fallo se reenvía; el lote no sale dos veces al volver la red); aviso al salir (`beforeunload`) y sin aviso sin pendientes; sesión vencida (a `/ingresar/` con el aviso, la marca se guarda al volver y la clave de `sessionStorage` se borra); cierre (tras el último guardado y anunciado, no con la última marca fallida, ni durante la cuenta ni tras deshacer, y tras la cuenta); axe de las vistas con barra, sin conexión y completa en ambos temas a 360 y 1280 px; 320 px con un nombre de 120 + 120. `uv run pytest --cov`: 955, 98 %; e2e: 241 en verde (asistencia: 56). Revisión de la parte: 1 Critical (una fila fallida que volvía al estado confirmado quedaba sin reintento) y 2 Important ("Pendiente de deshacer" se quedaba tras Deshacer; el lote podía salir dos veces con `online`) corregidos con su prueba.
- **Interpretación de D8:** una vez visible el cierre, una corrección en curso no lo quita (evita el parpadeo); un guardado fallido, "Sin conexión" o un lote en cuenta, sí. Para que el equipo lo valide en el PR.
- **Desviación de D10:** `Dimension` gana el campo `url` (opcional), porque `dataclasses.replace` no crea campos; la tarjeta solo lee `d.url`.

## Minor para la descripción del PR

- `institucion/tests/test_servicios_estudiantes.py`: la fixture `fecha_asistencia` repite la fixture `fecha` de `asistencia/tests/conftest.py`, y sus imports son locales.
- `asistencia/tests/conftest.py`: `from institucion.tests.conftest import *` acopla `asistencia` a otra app; mejor subir las fixtures compartidas a `src/backend/conftest.py`.
- `Asistencia.__str__` consulta `self.estudiante` en cada llamada (N+1 si se usa en listados o mensajes); revisar si la parte C lo usa.
- Sin prueba directa de `estudiante.delete()` con asistencia a nivel de modelo; la cubren las de servicios.
- `cierre-sesion` dice "cada petición reinicia la cuenta": con D9 la precisión es de 30 s (la sesión puede cerrarse hasta 30 s antes de los 60 minutos, nunca después). Sin delta de ese spec en este cambio; anotado aquí y en el design (D9).
- `InactividadMiddleware`: con el reloj retrocedido (diferencia negativa) la marca futura no se renueva hasta que el reloj la alcanza; `sesion_vencida` tampoco vence en ese caso. Improbable con un servidor.
- `servicios._completa_o_vacia`: el nombre no dice que "sin activos" cuenta como completa, y hace 2 consultas; se puede renombrar (`_sin_pendientes`) o juntar en una agregación.
- `servicios.marcar`: una nota de solo espacios se guarda y cuenta contra los 100; decidir en la vista (parte 2) si se recorta.
- `servicios.marcar_restantes`: los ids deben llegar como enteros (la vista, D10, los convierte); `"5"` y `5` contarían como dos.
- `servicios.marcar`: el estudiante activo se lee sin bloqueo; un retiro simultáneo podría dejar una fila de un RETIRADO, que ya no cuenta en totales ni avance.
- `MarcarView`: el 404 de un estudiante de otra sección lo da `get_object_or_404` del mixin y lleva la página 404 con cuerpo; los demás 404 de los guardados salen vacíos. El JS solo mira el código.
- `_lista.html`: "Tomar la asistencia de hoy" sale con cualquier mensaje de etiqueta `estudiantes` que llegue a la lista; hoy solo llega el de importados. Una etiqueta propia lo dejaría atado a ese aviso.
- Catálogo de rutas, nota "Guardados de la asistencia": describe el envío con `HX-Request` que hará `asistencia.js` (parte B); revisarla al cerrar 2.5 y 2.7.
- `asistencia.js`, `mostrarGuardado`: con una fila fallida y otra guardada se ve "✓ Guardado", y si el primer guardado falla queda "Guardando…". La parte C fija la prioridad: sin guardar > guardando > guardado.
- `asistencia.js`, para la parte C: no hay molde del círculo Sin marcar (los moldes salen de la leyenda del panel), y "Deshacer" lo necesitará; lo mismo el ícono de "Guardado", tomado del cierre. Mejor un `<template>` propio.
- `test_la_nota_se_guarda_al_salir_del_campo` no distingue el guardado por `change` del temporizador de 800 ms.
- El ciclo, las palabras y el orden de los totales están en `servicios.py` y repetidos en `asistencia.js`; las pruebas de nombre accesible los protegen. Se podrían pasar con `json_script`.
- `_sin_estudiantes.html`: `role="status"` en un aviso que ya está al cargar no aporta.
- "Marcar los N restantes" mide 44 px de alto (del boceto); DESIGN.md pide 48 px para el Botón secundario. Para el pulido.
- Las propiedades `Fila.palabra`, `siguiente` y `clase` se escribieron junto con su prueba, sin verla fallar antes.
- `asistencia.js`: un 403 (CSRF) o 401 se reintenta sin fin y se ve como "Sin conexión"; D3 solo nombra 5xx, 408 y 429. Tratar los demás 4xx como los de recarga.
- `asistencia.js`, `anunciar`: el mismo texto dos veces no cambia la región viva, así que un segundo episodio de "Sin conexión" puede no anunciarse; vaciarla y escribir en el siguiente frame.
- E2E: la rama `visibilitychange` (cambiar de aplicación) no tiene prueba propia, solo `page.close`; tampoco la interpretación del cierre con una corrección en curso. Las esperas fijas de 6 s alargan la suite (el reloj de Playwright las acortaría). `retenidas[0]` de la parte B supone que la ruta ya retuvo; la parte C usa `esperar_retenida`.
- `app.css`: el `padding-bottom: 88px` bajo la barra de Deshacer es fijo; con `safe-area-inset-bottom` o el texto en dos líneas podría quedarse corto (`calc(88px + env(safe-area-inset-bottom))`).
- `asistencia.js`, rechazo de una sola fila: se descarta la fila entera aunque su `deseado` haya cambiado después del envío; con un 400, el último toque podía ser válido y se pierde sin aviso. Con 404 y 409 no importa.
- `asistencia.js`: un rechazo durante la cuenta de 5 s guarda las filas del lote en `sessionStorage` y se envían tras la recarga, sin opción de Deshacer. Es lo mismo que hace la sesión vencida (D6).
- `test_vistas.py`, prueba de la fecha de Lima: el `timezone.now` fijo (04:30 UTC del 29-10) puede quedar antes de la marca de actividad de la sesión; hoy pasa. Si se vuelve frágil, fijar también la marca.
