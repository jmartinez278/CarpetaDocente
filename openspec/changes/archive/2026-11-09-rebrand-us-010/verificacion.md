# Verificación: rebrand de Sesiones (US-010)

Rama `feature/rebrand` (paso 1 del PLAN del rebrand). Los 6 escenarios de la spec delta de `envio-sesiones` tienen prueba, y los 35 escenarios de `envio-sesiones` que no cambian se vuelven a correr sobre el marco nuevo con sus pruebas de US-010/014 (ajustadas de clases viejas a ganchos, tarea 3.1). `sesiones.js`, vistas, servicios, modelos y rutas no cambian.

Pruebas en `src/backend/`. Abreviaturas: en `repositorio/tests/`, `vis` = `test_vistas.py`, `pl` = `test_plantillas.py`, `e2e` = `test_sesiones_e2e.py`, `srv` = `test_servicios_enviar.py`, `va` = `test_validar_archivo.py`, `mod` = `test_modelos.py`, `con` = `test_concurrencia.py`; en `cuentas/tests/`, `rb` = `test_componentes_rb.py`, `hoja` = `test_hoja_rebrand_e2e.py`, `me2e` = `test_marco_rebrand_e2e.py`, `dim` = `test_dimensiones.py`.

## Minor para la descripción del PR

- Sin revisor: ninguna parte era de alto riesgo (`tasks.md`).
- Auditoría de Emil (4.1, `insumos/rebrand-sesiones/auditoria-emil.md`): A-04 y B-02 aplicados con su prueba; K-05 no se aplica. B-01 (la hoja detrás del teclado virtual) y la altura de 320 × 240 van a la deuda: no se provocan en Playwright y se ven en un celular real en el pulido final.
- Al correr las e2e en 4.1, `quieto()` de `e2e` pasó de `requestAnimationFrame` a sondear cada 100 ms: en oscuro la espera se colgaba aunque las animaciones terminaban.

## Revisión A2 (Codex, 4.2)

| Hallazgo | Decisión | Prueba |
|---|---|---|
| D3/D4 [medium] (`rebrand/componentes.css:138-139`): en los 200 ms de salida tras `close()` el diálogo sigue visible, no modal y con controles que aceptan clics; un clic en «Enviar a la dirección» justo después de «Cancelar» podría guardar la sesión cancelada (trazado estático, sin clic físico verificado) | Marco: se anota y no se corrige en esta rama (deuda del PR, `tasks.md` «Workflow follow-up»). Arreglo propuesto: `pointer-events: none` en el diálogo cerrado y su `::backdrop` | Pendiente con el arreglo: e2e que pulse Enviar durante la salida y compruebe que no sale ningún POST |

## Escenarios (cierre, 4.3)

### Spec delta (`envio-sesiones`, requisitos modificados)

| Escenario | Prueba |
|---|---|
| Pantalla Sesiones · Primera visita | `vis::test_primera_visita_cabecera_boton_y_estado_vacio_sin_lista`; `pl::test_la_pantalla_carga_solo_la_hoja_del_rebrand`, `test_la_barra_dice_sesiones_y_el_menu_la_deja_en_proximamente`, `test_la_marca_de_sesiones_va_dentro_del_main_del_marco`, `test_el_estado_vacio_y_la_region_del_resultado`; componente: `rb::test_estado_vacio_*` |
| Pantalla Sesiones · Cabecera sin ícono ni franjas | `pl::test_la_cabecera_tiene_titulo_subtitulo_y_boton_sin_icono_ni_franjas` |
| Pantalla Sesiones · Botón en el celular | `e2e::test_en_el_celular_subir_una_sesion_se_lee_completo` (360 px, sin desplazamiento horizontal) |
| Pantalla Sesiones · Portada sin cambio | `dim::test_las_tres_dimensiones_en_orden_con_sus_textos`, `dim::test_toda_dimension_disponible_resuelve_su_pantalla` (la portada no se toca en este cambio) |
| Pantalla accesible · Estados del boceto | `e2e::test_los_estados_del_boceto_son_accesibles_y_sin_desplazamiento` (11 estados × claro/oscuro × 360/1280 px, ☰ y cuenta cerrados); `pl::test_cada_campo_tiene_su_ayuda_y_su_error_asociados`, `test_el_cuerpo_del_popup_se_alcanza_con_el_teclado`; `rb::test_dialogo_cuerpo_alcanzable_con_teclado_y_con_nombre` |
| Pantalla accesible · Pantalla baja | `e2e::test_pantalla_baja_los_terminos_se_desplazan_y_sus_botones_siguen_a_la_vista` (360 × 560), `e2e::test_b02_en_una_pantalla_muy_baja_el_cuerpo_del_popup_sigue_a_la_vista` (320 × 320 y 568 × 320) |

### Diálogo y su movimiento (D3, D4)

| Comportamiento | Prueba |
|---|---|
| `rb/dialogo.html` (hoja y chico, nombre, descripción, cuerpo, pie, sin ✕) | `rb::test_dialogo_*`; `pl::test_los_popups_no_llevan_boton_de_cerrar` |
| Hoja en el celular y ventana en la PC | `e2e::test_en_el_celular_el_popup_es_una_hoja_abajo_a_todo_el_ancho`, `e2e::test_en_la_pc_el_popup_es_una_ventana_centrada_de_480_px_o_menos` |
| Transiciones permitidas, `@starting-style`, sin ancho ni alto | `hoja::test_el_dialogo_transiciona_solo_transform_opacity_display_y_overlay`, `test_el_dialogo_y_su_velo_entran_con_starting_style`, `test_el_velo_del_dialogo_solo_transiciona_opacidad_display_y_overlay`, `test_ninguna_regla_del_dialogo_anima_ancho_ni_alto` |
| Regla 1: con el teclado, sin transición | `me2e::test_la_marca_de_teclado_va_en_html_con_una_tecla_y_se_quita_con_el_puntero`, `test_la_marca_de_teclado_no_toca_la_marca_del_mouse_ni_el_menu`; `hoja::test_con_la_marca_de_teclado_el_dialogo_y_su_velo_no_transicionan`; `e2e::test_con_el_teclado_el_popup_abre_y_cierra_sin_transicion` |
| Movimiento reducido | `hoja::test_con_movimiento_reducido_el_dialogo_no_se_desplaza`, `e2e::test_con_movimiento_reducido_el_popup_no_se_desplaza` (360 y 1280) |
| Salida en columna (A-04) | `e2e::test_a04_al_cerrar_con_el_mouse_el_popup_sale_en_columna` (360 y 1280) |

### Escenarios de `envio-sesiones` que se vuelven a correr

La conducta no cambia; las pruebas son las de US-010/014 (`openspec/changes/archive/2026-11-08-us-010-014-en-03-enviar-sesion/verificacion.md`), con sus selectores pasados a los ganchos del marcado nuevo.

| Escenario | Prueba |
|---|---|
| Docente sin sección | `vis::test_la_docente_sin_seccion_abre_sesiones_y_envia`, `srv::test_docente_sin_seccion_tambien_envia` |
| Otro rol | `vis::test_otro_rol_va_a_su_inicio_sin_guardar_ni_registrar` |
| Sin sesión | `vis::test_sin_sesion_va_a_ingresar_con_next`, `test_sin_sesion_el_envio_del_popup_recibe_hx_redirect`, `test_con_la_sesion_vencida_el_envio_recibe_hx_redirect` |
| Abrir el popup | `e2e::test_abrir_el_popup_enfoca_su_titulo_y_deja_la_pantalla_inerte`, `pl::test_el_popup_tiene_su_titulo_y_su_descripcion` |
| Tocar afuera | `e2e::test_tocar_afuera_no_cierra_el_popup` |
| Cancelar | `e2e::test_cancelar_cierra_sin_guardar_y_al_abrir_otra_vez_esta_vacio` (botón y Esc) |
| Orden de los botones | `e2e::test_orden_de_los_botones` (360 y 1280), `pl::test_el_pie_tiene_el_avance_y_los_botones_en_su_orden` |
| Atrás en el formulario | `e2e::test_atras_en_el_formulario_lo_cierra_y_sigue_en_sesiones` |
| Atrás en los términos | `e2e::test_atras_en_los_terminos_cierra_solo_los_terminos` |
| Atrás mientras sube | `e2e::test_atras_mientras_sube_no_cierra_y_la_subida_sigue` |
| Áreas de la institución | `pl::test_las_areas_son_las_de_la_institucion_con_una_opcion_vacia`, `e2e::test_las_areas_son_las_que_trabaja_la_institucion_en_orden_siagie`, `vis::test_el_contexto_trae_las_areas_que_trabaja_la_institucion` |
| Archivo elegido | `e2e::test_archivo_elegido_muestra_nombre_tipo_tamano_y_cambiar`, `test_un_docx_se_reconoce_como_word` |
| Una sección | `pl::test_con_una_seccion_el_grado_viene_elegido_con_su_ayuda`, `e2e::test_el_grado_viene_con_el_de_su_seccion` |
| Varias secciones o ninguna | `pl::test_con_varias_secciones_el_grado_viene_sin_elegir`, `test_sin_seccion_el_grado_viene_sin_elegir` |
| Tipo no permitido | `e2e::test_un_archivo_que_no_es_pdf_aunque_se_llame_asi_se_rechaza`, `va::*` |
| Archivo de más de 4 MB | `e2e::test_un_archivo_de_mas_de_4_mb_se_rechaza`, `va::test_un_byte_mas_de_4_mb_se_rechaza` |
| Justo 4 MB | `va::test_justo_4_mb_pasa`, `srv::test_justo_4_mb_se_guarda` (sin cambios de servidor) |
| Envío que salta el navegador | `vis::test_un_archivo_disfrazado_responde_400_con_el_mensaje_del_campo`, `srv::test_archivo_que_salta_el_navegador_no_se_guarda` |
| Área y título vacíos | `e2e::test_sin_area_ni_titulo_muestra_sus_errores_y_enfoca_el_primero`, `test_corregir_un_campo_quita_su_error`, `vis::test_datos_que_faltan_responden_400_con_un_mensaje_por_campo` |
| Sin archivo | `e2e::test_sin_archivo_lo_pide` |
| Área ajena o grado fuera de rango | `srv::test_dato_fuera_de_rango_dice_su_motivo`, `test_area_que_la_institucion_no_trabaja_se_rechaza` (sin cambios de servidor) |
| Enviar sin compartir | `e2e::test_enviar_sin_compartir_va_directo_y_muestra_el_exito`, `pl::test_la_casilla_de_compartir_desmarcada_con_su_ayuda` |
| Aceptar y enviar | `e2e::test_aceptar_y_enviar_comparte_y_guarda_la_aceptacion`, `pl::test_los_terminos_son_los_del_doc_09_literales_y_en_orden`, `test_los_terminos_tienen_acepto_y_volver` |
| Volver | `e2e::test_volver_cierra_solo_los_terminos_y_conserva_el_formulario` (botón y Esc) |
| Compartir sin aceptar | `vis::test_compartir_sin_aceptar_responde_400`, `srv::test_compartir_sin_aceptar_no_guarda_nada` |
| Datos incompletos con la casilla marcada | `e2e::test_datos_incompletos_con_la_casilla_marcada_no_abren_los_terminos` |
| Subiendo | `e2e::test_subiendo_bloquea_campos_botones_y_esc`, `pl::test_hay_una_region_aria_live_para_el_avance` |
| Recargar mientras sube | `e2e::test_recargar_mientras_sube_pide_confirmar` |
| Se corta y reintenta | `e2e::test_se_corta_y_al_reintentar_se_envia_una_sola_vez`, `pl::test_el_aviso_de_corte_de_red_esta_oculto`, `test_el_error_general_tiene_su_primer_parrafo_vacio` |
| Se guardó pero no llegó la respuesta | `e2e::test_se_guardo_pero_no_llego_la_respuesta_y_el_reintento_da_el_mismo_exito`, `vis::test_el_mismo_id_otra_vez_responde_el_mismo_201_con_una_sola_sesion`, `con::test_dos_envios_con_el_mismo_id_dejan_una_sesion_y_los_dos_ven_el_exito` |
| Éxito sin compartir | `e2e::test_enviar_sin_compartir_va_directo_y_muestra_el_exito`, `pl::test_el_fragmento_del_exito_dice_el_mensaje_y_el_titulo_enfocable` |
| Éxito compartida | `vis::test_un_envio_compartido_lo_dice_en_el_fragmento`, `e2e::test_subir_otra_abre_un_formulario_nuevo` |
| Recargar después del éxito | `e2e::test_recargar_despues_del_exito_no_muestra_el_mensaje_ni_envia_otra` |
| Datos guardados | `srv::test_enviar_sin_compartir_guarda_la_sesion_con_sus_datos` (sin cambios de servidor) |
| Coherencia en la base | `mod::test_la_base_rechaza_una_sesion_incoherente` (sin cambios de modelos) |

Slow 4G: `e2e::test_sesiones_carga_con_slow_4g`.

## DoD 1 a 9

| N.° | Criterio | Estado |
| --- | --- | --- |
| 1 | Cobertura ≥ 80 % | Local: 98,52 % total (`verificar.py`, sin e2e). Sonar way: pendiente del push |
| 2 | Análisis estático sin críticas ni altas | Ruff en verde con `verificar.py`. A2 de Codex: un hallazgo medium, anotado sin corregir por decisión de Marco (4.2). CodeQL y SonarQube Cloud: pendiente del push |
| 3 | Aprobación de otra integrante | Pendiente del PR único del rebrand (no antes del 11-11-2026) |
| 4 | Vista previa de Vercel | Pendiente del push |
| 5 | Escenarios en verde y e2e de la ruta ideal | Los 6 escenarios de la delta y los 35 que se vuelven a correr tienen prueba; e2e de todas las apps: 510 en verde. Ruta ideal: `e2e::test_enviar_sin_compartir_va_directo_y_muestra_el_exito`, `e2e::test_aceptar_y_enviar_comparte_y_guarda_la_aceptacion`. `sesiones.js` sin cambios (`git diff main --stat` no lo nombra). GitHub Actions: pendiente del push |
| 6 | Reglas de negocio con pruebas propias | Sin reglas nuevas: vistas, servicios y modelos sin cambios; las de US-010/014 siguen en verde (`srv::*`, `va::*`, `mod::*`) |
| 7 | Accesibilidad sin errores críticos | `e2e::test_los_estados_del_boceto_son_accesibles_y_sin_desplazamiento` (claro/oscuro, 360/1280), objetivos de 44 px, cuerpo del popup alcanzable con el teclado, movimiento reducido y regla 1. Pantalla vista en claro/oscuro y celular/escritorio por Marco (3.5) |
| 8 | Sin datos reales | Docentes, secciones y archivos ficticios de las fixtures; sin archivos de terceros nuevos |
| 9 | Documentación | Spec delta, `design.md` (D1 a D7), comentario de uso al inicio de `rb/dialogo.html` y `rb/estado_vacio.html`. Sin rutas nuevas: `docs/03` y README sin cambios. Deuda en `tasks.md` («Workflow follow-up») |
