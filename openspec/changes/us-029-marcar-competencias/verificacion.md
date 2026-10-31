# Verificación: US-029 – Marcar las competencias desarrolladas en el periodo

Rama `feature/us-029-marcar-competencias-desarrolladas`. Los 63 escenarios de los cuatro specs (9 de `catalogo-curricular`, 43 de `competencias-periodo`, 5 de `datos-demostracion` y 6 de `registro-actividad`) tienen al menos una prueba: están en "Escenarios (cierre, 5.2)", junto con la DoD 1 a 9.

## Minor para la descripción del PR

### Parte A: `CompetenciaPeriodo`, `a_cargo_docente_curso` y migraciones

- `catalogo/tests/test_admin.py`, `test_otro_rol_no_cambia_a_cargo_del_docente_de_curso`: buscar `a_cargo_docente_curso` en el cuerpo del 302 no prueba nada; lo que cubre el escenario es que no hay cambio ni CATALOGO_EDITADO.
- `catalogo/0003`: `AddField` sin `db_default`. Mientras Vercel migra Neon, el despliegue anterior no manda la columna: crear una institución en esa ventana falla. Con `db_default=False` no pasaría.
- `notas/models.py`, `CompetenciaPeriodo.__str__`: hace tres consultas. Si llega a un panel o a una lista, usar `select_related`.

### Parte B: servicios de `notas`, actividad y demo

- `notas/servicios.py`, `marcar_todo_sin_registro`: no bloquea la sección. Si una docente demo guarda mientras corre la carga, choca con `uq_competencia_periodo` y se revierte toda la carga (se vuelve a correr).
- `notas/tests/test_servicios_guardar.py`, obligatorias del bimestre 4: revisa `cambios.agregadas`, pero no el `detalle` de COMPETENCIAS_MARCADAS («las obligatorias cuentan como agregadas»).
- Tarea 2.4, «competencia de otra institución»: el catálogo es global; se probó con Castellano (no se trabaja) y con un id que no existe. El aislamiento por institución lo cubre `test_un_area_de_otra_institucion_no_se_marca`.

### Parte C: vistas, rutas y permisos

- `notas/tests/test_vistas_acceso.py`, «Portada sin cambios»: supone que Notas es la segunda tarjeta; buscar el `<article>` con `id="ins-notas"`.

### A2 (Codex, adversarial)

- Corregido (alto): una competencia reactivada con la pantalla abierta perdía su marca al guardar. Ahora el POST lleva el universo que se mostró y, si cambió, responde 400 sin guardar (escenario «Catálogo cambiado al guardar», design D5).
- Deuda (medio), `static/js/competencias.js`, `pendiente()`: con B1={X,Y} y B4={Y} guardados, quitar X del B1 la vuelve obligatoria en el B4; `base()` y `borrador()` la suman, `cambios()` da 0 y «Guardar» queda deshabilitado, aunque X no tiene marca en ningún periodo del año. El servidor la agrega en el próximo guardado del B4. Arreglo propuesto: `pendiente()` verdadero si falta una obligatoria en `guardado`.
- Corregido (medio), `catalogo/0003`: `db_default=False` en el campo y en la migración (es el Minor de la parte A). Un INSERT sin la columna, como el de `main`, la deja en `False`.

## Escenarios (cierre, 5.2)

Pruebas en `src/backend/notas/tests/` salvo las indicadas. Abreviaturas: `mod` = `test_modelos.py`, `uni` = `test_servicios_universo.py`, `per` = `test_servicios_periodos.py`, `obl` = `test_servicios_obligatorias.py`, `ini` = `test_servicios_estado_inicial.py`, `gua` = `test_servicios_guardar.py`, `conc` = `test_concurrencia.py`, `acc` = `test_vistas_acceso.py`, `vis` = `test_vistas.py`, `pla` = `test_plantilla.py`, `e2e` = `test_competencias_e2e.py`; en otras apps, `cadm` = `catalogo/tests/test_admin.py`, `cmig` = `catalogo/tests/test_migracion_catalogo.py`, `cmod` = `catalogo/tests/test_modelos.py`, `demo` = `institucion/tests/test_demo.py`, `cmd` = `institucion/tests/test_comandos_demo.py`, `amod` = `actividad/tests/test_modelos.py`, `acat` = `actividad/tests/test_catalogo.py`.

| Spec | Escenario | Prueba |
| --- | --- | --- |
| catalogo-curricular | Institución existente al migrar | `cmig::test_al_migrar_ninguna_area_queda_a_cargo_del_docente_de_curso` (las 11 filas y Castellano sin trabajarse, de EN-06) |
| catalogo-curricular | Institución nueva | `cmod::test_institucion_nueva_nace_sin_areas_a_cargo_del_docente_de_curso`, `test_area_de_institucion_nueva_no_esta_a_cargo_del_docente_de_curso` |
| catalogo-curricular | Área repetida en la institución | Sin cambios de EN-06: la restricción única no se tocó |
| catalogo-curricular | Desactivar una competencia | `cadm::test_desmarcar_activa_deja_la_competencia_inactiva_y_existente` (sin cambios) y `uni::test_sin_las_competencias_inactivas` |
| catalogo-curricular | Área a cargo del docente de curso | `cadm::test_a_cargo_del_docente_de_curso_se_marca_desde_la_lista`, `test_a_cargo_del_docente_de_curso_se_marca_desde_la_ficha`; CATALOGO_EDITADO con el campo, en `cadm` y en `actividad/tests/test_panel_instrumentado.py` |
| catalogo-curricular | Sin borrar / Sin agregar / Campos fijos | Sin cambios de EN-06: `cadm::test_sin_url_de_borrado`, `test_sin_accion_eliminar_en_lote` y las demás de ese archivo |
| catalogo-curricular | Otro rol | `cadm::test_otro_rol_no_cambia_a_cargo_del_docente_de_curso` (ver Minor de la parte A) |
| competencias-periodo | Sección de otra docente | `acc::test_otra_docente_recibe_404_y_no_guarda` |
| competencias-periodo | Sección de un año cerrado | `acc::test_la_seccion_de_un_anio_cerrado_da_404_y_no_guarda`, `gua::test_en_un_anio_cerrado_no_se_guarda` |
| competencias-periodo | Otro rol | `acc::test_la_direccion_llega_a_su_pantalla` |
| competencias-periodo | Sin sesión | `acc::test_sin_sesion_va_a_ingresar_con_next`, `test_sin_sesion_un_guardado_con_htmx_recibe_hx_redirect` |
| competencias-periodo | Portada sin cambios | `acc::test_la_portada_sigue_con_notas_en_proximamente` |
| competencias-periodo | Catálogo de la I.E. | `uni::test_areas_de_la_seccion_en_orden_siagie_con_27_competencias_en_dos_consultas`, `test_el_universo_son_las_21_que_marca_la_tutora`; `pla::test_dibuja_las_10_areas_en_orden_siagie_con_sus_27_competencias`, `test_un_area_a_cargo_va_atenuada_con_su_aviso_y_casillas_deshabilitadas` |
| competencias-periodo | Competencia inactiva | `uni::test_sin_las_competencias_inactivas` |
| competencias-periodo | Área a cargo del docente de curso | `e2e::test_las_areas_del_docente_de_curso_no_se_pueden_marcar`, `gua::test_una_competencia_fuera_del_universo_no_guarda_nada` |
| competencias-periodo | Competencia de otra área en el guardado | `gua::test_una_competencia_fuera_del_universo_no_guarda_nada`, `vis::test_una_competencia_de_ingles_responde_400`, `uni::test_un_area_de_otra_institucion_no_se_marca` |
| competencias-periodo | Marca que la tutora no ve | `gua::test_la_marca_de_una_competencia_desactivada_sigue_tras_guardar`, `test_la_marca_de_un_area_a_cargo_sigue_tras_guardar` |
| competencias-periodo | Abre en el vigente | `per::test_el_30_de_octubre_el_bimestre_3_es_el_vigente`, `vis::test_abre_en_el_vigente`, `pla::test_los_botones_de_periodo_dicen_su_nombre_estado_y_fechas` |
| competencias-periodo | Corregir un periodo anterior | `gua::test_corregir_un_periodo_anterior_no_toca_el_vigente`, `e2e::test_corregir_un_periodo_anterior_no_toca_el_vigente` |
| competencias-periodo | Guardado de un periodo futuro | `gua::test_un_periodo_futuro_no_se_guarda`, `vis::test_un_periodo_futuro_responde_409`, `e2e::test_el_periodo_futuro_no_se_puede_elegir` |
| competencias-periodo | Sin periodos | `vis::test_sin_periodos`, `pla::test_sin_periodos_solo_el_aviso`, `e2e::test_sin_periodos_solo_el_aviso` |
| competencias-periodo | Vacaciones | `per::test_en_un_hueco_no_hay_vigente_y_solo_los_pasados_son_editables`, `vis::test_vacaciones`, `pla::test_en_vacaciones_el_aviso_y_los_periodos_pasados_sin_ninguno_elegido`, `e2e::test_en_vacaciones_se_elige_un_periodo_pasado` |
| competencias-periodo | Antes del primer periodo | `per::test_antes_del_primer_periodo_ninguno_es_editable`, `vis::test_antes_del_primer_periodo`, `pla::test_antes_del_primer_periodo_el_aviso_con_la_fecha_y_nada_que_elegir` |
| competencias-periodo | Periodo sin marcas | `ini::test_sin_marcas_abre_con_todo_el_universo`, `vis::test_un_periodo_sin_marcas_va_en_null_y_abre_con_todo_marcado`, `pla::test_sin_marcas_abre_con_todo_marcado`, `acc::test_abrir_la_pantalla_no_guarda_marcas` |
| competencias-periodo | Periodo con marcas | `ini::test_con_marcas_abre_con_esas`, `vis::test_un_periodo_con_marcas_lleva_esas`, `pla::test_con_marcas_el_panel_cuenta_las_guardadas` |
| competencias-periodo | Camino ideal | `gua::test_primer_guardado_crea_las_marcas_y_deja_competencias_marcadas`, `vis::test_un_guardado_correcto_responde_204_sin_cuerpo`, `e2e::test_desmarcar_y_guardar_persiste_al_recargar` |
| competencias-periodo | Guardar desde otra área en el celular | `e2e::test_las_marcas_de_un_area_se_conservan_y_se_guardan_desde_otra` |
| competencias-periodo | Envío repetido | `gua::test_el_mismo_envio_dos_veces_no_cambia_nada_ni_deja_entrada`, `vis::test_el_mismo_guardado_dos_veces_responde_204` |
| competencias-periodo | Dos guardados a la vez | `conc::test_dos_guardados_a_la_vez_dejan_uno_de_los_dos_completo` |
| competencias-periodo | Conjunto vacío | `gua::test_un_conjunto_vacio_no_se_guarda`, `vis::test_un_conjunto_vacio_responde_400_con_su_mensaje`, `e2e::test_desmarcar_todo_no_se_guarda_y_dice_por_que` |
| competencias-periodo | Catálogo cambiado al guardar | `gua::test_una_competencia_reactivada_con_la_pantalla_abierta_no_pierde_su_marca`, `test_una_competencia_desactivada_con_la_pantalla_abierta_no_guarda_nada`, `vis::test_un_universo_distinto_al_actual_responde_400_sin_guardar` |
| competencias-periodo | Caso de error (notas) | `gua::test_quitar_una_competencia_con_notas_no_guarda_nada`, `e2e::test_desmarcar_una_competencia_con_notas_muestra_el_motivo`. `tiene_notas` va parcheada: es `False` hasta US-020 (`obl::test_tiene_notas_es_falso_hasta_us_020`) |
| competencias-periodo | Guardado que la quita | `vis::test_quitar_una_competencia_con_notas_responde_409`, `e2e::test_un_guardado_que_choca_con_notas_las_bloquea_en_pantalla` |
| competencias-periodo | Flujo alternativo válido | `obl::test_flujo_alternativo_valido_en_el_bimestre_4_las_no_marcadas_antes`, `pla::test_las_obligatorias_del_ultimo_periodo_dicen_su_motivo`, `e2e::test_el_ultimo_periodo_explica_las_obligatorias` |
| competencias-periodo | Guardado sin las obligatorias | `gua::test_en_el_bimestre_4_las_obligatorias_se_agregan_aunque_falten_en_el_envio`, `e2e::test_las_obligatorias_se_guardan_con_las_demas` |
| competencias-periodo | Otro periodo (sin bloqueo) | `obl::test_en_el_bimestre_3_ninguna_es_obligatoria`, `pla::test_en_otro_periodo_ninguna_competencia_va_bloqueada` |
| competencias-periodo | Cápsula de áreas | `e2e::test_la_capsula_muestra_un_area_a_la_vez`, `pla::test_la_capsula_de_areas_lleva_flechas_posicion_y_selector` |
| competencias-periodo | Extremo de la cápsula | `e2e::test_la_capsula_no_da_la_vuelta_en_los_extremos` |
| competencias-periodo | PC | `e2e::test_en_pc_se_ven_las_diez_areas_y_el_panel`; el total del celular, `test_el_guardado_fijo_del_celular_dice_el_total_global` |
| competencias-periodo | Cambiar de periodo con cambios | `e2e::test_el_borrador_de_un_periodo_se_conserva_y_el_boton_lo_dice`, `test_deshacer_vuelve_a_lo_guardado` |
| competencias-periodo | Deshacer en el último periodo | `e2e::test_deshacer_no_aparece_en_el_bimestre_4_sin_cambios`, `test_deshacer_aparece_con_un_cambio_en_el_bimestre_4` |
| competencias-periodo | Salir con cambios | `e2e::test_el_dialogo_de_salida_nombra_los_periodos_y_pone_el_foco_en_seguir_editando`, `test_escape_y_seguir_editando_conservan_los_cambios`, `test_sin_cambios_no_hay_pregunta` |
| competencias-periodo | Salir sin guardar | `e2e::test_salir_sin_guardar_sale_sin_aviso_del_navegador` |
| competencias-periodo | Recargar con cambios | `e2e::test_recargar_con_cambios_muestra_el_aviso_del_navegador`, `test_recargar_sin_cambios_no_muestra_aviso` |
| competencias-periodo | Guardado (estado) | `e2e::test_desmarcar_y_guardar_persiste_al_recargar`; las regiones `role="status"` y `role="alert"`, `pla::test_las_regiones_del_lector_de_pantalla_y_el_noscript` |
| competencias-periodo | Falla la red | `e2e::test_sin_red_dice_que_no_se_pudo_guardar_y_un_guardado_despues_lo_quita` |
| competencias-periodo | Sesión vencida | `e2e::test_con_la_sesion_vencida_no_guarda_y_ofrece_volver_a_ingresar`, `acc::test_con_la_sesion_vencida_un_guardado_con_htmx_recibe_hx_redirect` |
| competencias-periodo | Axe en ambos temas | `e2e::test_la_pantalla_con_marcas_pasa_axe`, `test_la_pantalla_con_bloqueos_pasa_axe`, `test_el_dialogo_de_salida_pasa_axe`, `test_sin_periodos_pasa_axe`, `test_en_vacaciones_pasa_axe` |
| competencias-periodo | Teclado en una competencia bloqueada | `e2e::test_la_obligatoria_con_espacio_no_cambia_y_anuncia_su_motivo` |
| competencias-periodo | Sin desplazamiento horizontal | `e2e::test_no_hay_desplazamiento_horizontal_a_320_y_360`; filas de 44 px, `test_las_filas_miden_al_menos_44_px` |
| datos-demostracion | Demostración con periodos | `demo::test_la_carga_marca_el_universo_en_los_periodos_ya_empezados` |
| datos-demostracion | Sin periodos | `demo::test_sin_periodos_la_carga_no_marca_nada` |
| datos-demostracion | Volver a cargar | `demo::test_volver_a_cargar_sin_marcas_marca_los_periodos_ya_empezados`, `test_volver_a_cargar_solo_marca_los_periodos_sin_marcas`, `test_la_carga_no_cambia_las_areas_a_cargo_del_docente_de_curso` |
| datos-demostracion | Quitar la demostración | `demo::test_quitar_borra_las_marcas_demo_y_no_las_de_tres_a` |
| datos-demostracion | Descartar una sección | `demo::test_descartar_borra_las_marcas_y_las_cuenta`, `cmd::test_descartar_borra_las_marcas_y_las_nombra` |
| registro-actividad | Catálogo de esta historia | `amod::test_solo_las_operaciones_de_asistencia_cuentan_para_kpi_01`; COMPETENCIAS_MARCADAS en `acat::test_la_tabla_cubre_el_catalogo_menos_las_reservadas` |
| registro-actividad | Operación fuera del catálogo | `amod::test_operacion_fuera_del_catalogo_la_rechaza_la_base` (sin cambios) |
| registro-actividad | Cada operación tiene su prueba | `acat::test_cada_escenario_es_una_prueba_que_existe`: COMPETENCIAS_MARCADAS apunta a `gua::test_primer_guardado_crea_las_marcas_y_deja_competencias_marcadas` (`actividad/tests/escenarios.py`) |
| registro-actividad | Primer guardado del periodo | `gua::test_primer_guardado_crea_las_marcas_y_deja_competencias_marcadas` |
| registro-actividad | Corrección | `gua::test_corregir_borra_la_quitada_y_deja_su_entrada` |
| registro-actividad | Sin cambios | `gua::test_el_mismo_envio_dos_veces_no_cambia_nada_ni_deja_entrada` |

Además: las tres FK y la restricción `uq_competencia_periodo` (`mod::test_la_misma_marca_dos_veces_la_rechaza_la_base`, `test_borrar_el_anio_borra_sus_periodos_y_las_marcas`, `test_borrar_una_competencia_con_marcas_falla`), el token CSRF del guardado (`vis::test_un_guardado_sin_token_csrf_se_rechaza`), la pantalla sin estilos en línea ni colores hex (`pla::test_sin_estilos_en_linea_ni_colores_hex`) y el universo sin consultas de más (`uni::test_el_universo_de_las_areas_no_vuelve_a_consultar`).

Sin prueba directa: «La pantalla funciona en Slow 4G (RNF-002)», que es parte de un requisito y no de un escenario. Va al pulido final, con Playwright MCP.

Corrida del cierre (31/10/2026): `uv run pytest --cov`: 1509 pasan, cobertura total 98,40 %; `notas/servicios.py` y `notas/views.py` 100 %. Las e2e de `notas` en Chromium (con el CSS compilado y `DJANGO_ALLOW_ASYNC_UNSAFE=true`): 55 pasan.

## DoD 1 a 9

| N.° | Criterio | Estado |
| --- | --- | --- |
| 1 | Cobertura ≥ 80 % | Local: 98,40 % total. Sonar way: pendiente del PR |
| 2 | Análisis estático sin críticas ni altas | Ruff en verde con `verificar.py`. CodeQL y SonarQube Cloud: pendiente del PR |
| 3 | Aprobación de otra integrante | Pendiente del PR |
| 4 | Vista previa de Vercel | Pendiente del PR: debe aplicar `catalogo/0003`, `notas/0001` y la migración de `actividad` en Neon |
| 5 | Escenarios en verde y e2e de la ruta ideal | Los 63 escenarios tienen prueba y pasan en local; la ruta ideal, `e2e::test_desmarcar_y_guardar_persiste_al_recargar`. GitHub Actions: pendiente del PR |
| 6 | Reglas de negocio con pruebas propias | RN-005 (todas con nivel al cerrar el año): `obl::test_flujo_alternativo_valido_en_el_bimestre_4_las_no_marcadas_antes`, `gua::test_en_el_bimestre_4_las_obligatorias_se_agregan_aunque_falten_en_el_envio`. RN-007 (áreas que se trabajan): `uni::test_un_area_que_no_se_trabaja_no_se_marca`. RN-008 (transversales incluidas): `pla::test_las_transversales_dicen_competencia_transversal`. RN-023 (no se borra): el catálogo sigue sin borrado en el panel. RN-022 llega con la historia de entrega |
| 7 | Accesibilidad sin errores críticos | `e2e::test_la_pantalla_con_marcas_pasa_axe`, `test_la_pantalla_con_bloqueos_pasa_axe`, `test_el_dialogo_de_salida_pasa_axe`, `test_sin_periodos_pasa_axe`, `test_en_vacaciones_pasa_axe` (claro y oscuro, 360 y 1280 px), `test_no_hay_desplazamiento_horizontal_a_320_y_360` y `test_las_filas_miden_al_menos_44_px` |
| 8 | Sin datos reales | Secciones, estudiantes y fechas ficticios en pruebas y demo. Revisión del PR: pendiente |
| 9 | Documentación | Specs del cambio en OpenSpec y docstrings. Las dos rutas están en el Catálogo de rutas de `docs/03`. Ningún requisito cambió: el documento 06 sigue igual. Las contradicciones con los docs 08 y 11 y con el criterio de US-029 están en el "Workflow follow-up" de `tasks.md` |
