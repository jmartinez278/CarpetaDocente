# Verificación: US-020, US-021 y US-022 – Hoja de notas por área

Rama `feature/us-020-021-022-registrar-notas`. Los 117 escenarios de los seis specs (78 de `registro-notas`, 17 de `competencias-periodo`, 8 de `pantallas-de-inicio`, 7 de `registro-actividad`, 4 de `indicadores-adopcion` y 3 de `datos-demostracion`) tienen al menos una prueba o una nota de por qué no aplica: están en "Escenarios (cierre, 6.2)", junto con la DoD 1 a 9.

## Minor para la descripción del PR

### Parte A: `Calificacion` y su migración

- `institucion/servicios.py`, docstring de `quitar_estudiante`: dice «hoy, `asistencia`»; `calificacion` también bloquea con RESTRICT.
- `notas/models.py`, `ck_calificacion_conclusion`: en B y C acepta diez o más espacios; la red es el `strip()` del servicio (D5, paso 4), que se prueba en la parte B.
- `notas/models.py`: el comentario «Escala de calificación (RN-001)» va sobre las constantes de longitud y no sobre `Nivel`, y los CHECK repiten la escala en vez de usar `Nivel.values`.

### Parte B: servicios de la hoja, actividad, indicadores y demo

- `notas/servicios.py`, `notas_faltantes`: ordena los pares por id de estudiante y no por apellidos como la hoja; si US-026 o US-042 recorren «la siguiente faltante» con ellos, conviene usar el orden de `estudiantes_ordenados`.
- `notas/servicios.py`, `hoja_de_notas`: un trasladado va a solo lectura si tiene nota en una columna marcada, no en cualquier competencia del área; hoy es lo mismo (una competencia con notas no se desmarca), pero una competencia desactivada en el catálogo oculta su nota.
- `notas/servicios.py`, docstring de `hoja_de_notas`: el número de consultas que nombra no coincide con lo que enumera; la cifra que vale es la de `test_la_hoja_se_lee_en_un_numero_fijo_de_consultas` (5).

### Parte C: vistas, rutas, permisos y bandera

- `notas/views.py`: la regla «área que la institución trabaja» se repite en `_area_inicial` y `_ir_a_competencias`; un solo helper evitaría que se desalineen en la parte 4.
- `notas/views.py`, `GuardarHojaView`: el 404 de periodo o área va sin cuerpo y los demás errores en JSON con `mensaje`; `notas.js` (parte 4) debe tratar el 404 aparte.
- `cuentas/tests/test_portada_e2e.py`: el `if ancho == 360` ata la prueba de la píldora a que Notas sea la primera tarjeta disponible.

### Parte D: borradores en el dispositivo

- ~~`static/js/notas.js`, `persistir`: cerrar sesión en una pestaña y editar en otra vuelve a escribir el borrador~~ → corregido en la 6.1 (hallazgo de la A2).
- `notas/tests/test_borradores_e2e.py`: no prueba la rama de D11 en que «Guardar» combina primero y se detiene ante un choque nuevo entre pestañas; el escenario «Misma celda en las dos» solo comprueba el aviso.

### 6.1: revisión A2 (Codex) y vista previa

- A2 con tres hallazgos (dos high y un medium), corregidos en `5ab5681` con su e2e y su escenario en `registro-notas`: respuesta perdida, base de otra pestaña (D7) y cierre de sesión en otra pestaña (D10).
- `static/js/notas.js`: tras una respuesta perdida, el reintento dice «1 nota cambió en otro dispositivo» aunque el cambio lo hizo el propio envío perdido; el resultado es seguro (D7), solo el texto no es exacto.
- Vercel: el commit `5ab5681` tuvo un primer despliegue fallido (`7P3ckVfAD6EFzvJ5yLU7nLW9mV6B`) cuyo log se corta en «Using uv», sin error, y que no aparece en la lista de despliegues; el segundo (`D9z5JGMpQ68Sxdc9nShJGozG5nJE`) desplegó bien y aplicó `notas/0002` y `actividad/0004` en la rama de Neon.

## Escenarios (cierre, 6.2)

Pruebas en `src/backend/notas/tests/` salvo las indicadas. Abreviaturas: `mod` = `test_modelos.py`, `sh` = `test_servicios_hoja.py`, `gh` = `test_servicios_guardar_hoja.py`, `gua` = `test_servicios_guardar.py`, `obl` = `test_servicios_obligatorias.py`, `conc` = `test_concurrencia.py`, `vh` = `test_vistas_hoja.py`, `vha` = `test_vistas_hoja_acceso.py`, `vis` = `test_vistas.py`, `acc` = `test_vistas_acceso.py`, `ph` = `test_plantilla_hoja.py`, `pla` = `test_plantilla.py`, `e2e` = `test_hoja_e2e.py`, `bor` = `test_borradores_e2e.py`, `ce2e` = `test_competencias_e2e.py`; en otras apps, `dim` = `cuentas/tests/test_dimensiones.py`, `pan` = `cuentas/tests/test_pantallas.py`, `port` = `cuentas/tests/test_portada_e2e.py`, `ind` = `actividad/tests/test_indicadores.py`, `amod` = `actividad/tests/test_modelos.py`, `acat` = `actividad/tests/test_catalogo.py`, `demo` = `institucion/tests/test_demo.py`, `cmd` = `institucion/tests/test_comandos_demo.py`.

| Spec | Escenario | Prueba |
| --- | --- | --- |
| registro-notas | Sección de otra docente | `vha::test_otra_docente_recibe_404_y_no_guarda` |
| registro-notas | Sección de un año cerrado | `vha::test_la_seccion_de_un_anio_cerrado_da_404_y_no_guarda`, `gh::test_un_anio_cerrado_no_se_guarda` |
| registro-notas | Otro rol | `vha::test_la_direccion_llega_a_su_pantalla` |
| registro-notas | Sin sesión | `vha::test_sin_sesion_va_a_ingresar_con_next`, `test_sin_sesion_un_guardado_con_htmx_recibe_hx_redirect` |
| registro-notas | Abre en el vigente | `sh::test_sin_pedido_abre_el_vigente`, `vh::test_abre_en_el_vigente`, `ph::test_el_vigente_no_lleva_aviso_de_periodo` |
| registro-notas | Periodo anterior pedido | `sh::test_un_periodo_anterior_pedido`, `vh::test_abre_el_periodo_anterior_pedido`, `ph::test_el_periodo_anterior_dice_anterior_y_avisa` |
| registro-notas | Periodo futuro pedido | `sh::test_un_periodo_futuro_pedido_abre_el_vigente`, `test_un_pedido_que_no_es_un_numero_abre_el_vigente`, `vh::test_un_periodo_futuro_o_invalido_abre_el_vigente` |
| registro-notas | Guardado de un periodo futuro | `gh::test_un_periodo_futuro_no_se_guarda`, `vh::test_un_periodo_futuro_da_409` |
| registro-notas | Sin periodos | `sh::test_sin_periodos_no_abre_ninguno`, `vh::test_sin_periodos_avisa_sin_hoja`, `ph::test_sin_periodos_solo_el_aviso`, `e2e::test_axe_sin_periodos` |
| registro-notas | Vacaciones | `sh::test_en_vacaciones_abre_el_ultimo_anterior`, `test_tras_el_ultimo_vigente_abre_el_ultimo_anterior`, `vh::test_en_vacaciones_abre_el_ultimo_periodo_pasado`, `ph::test_en_vacaciones_avisa_y_abre_el_ultimo_anterior` |
| registro-notas | Antes del primer periodo | `sh::test_antes_del_primero_no_abre_ninguno`, `vh::test_antes_del_primer_periodo_avisa_la_fecha_sin_hoja`, `ph::test_antes_del_primer_periodo_sin_hoja` |
| registro-notas | Bimestre sin marcas | `vh::test_sin_marcas_lleva_a_competencias_con_periodo_area_y_desde`, `test_sin_marcas_conserva_el_area_pedida`, `test_sin_marcas_del_periodo_pedido_lleva_a_ese_periodo`, `test_abrir_la_hoja_sin_marcas_no_guarda_marcas_ni_notas` |
| registro-notas | Cambiar de área | `e2e::test_cambiar_de_area_conserva_lo_digitado_y_marca_el_punto`, `vh::test_area_pedida_valida`, `ph::test_el_area_pedida_abre_presionada` |
| registro-notas | Área con cambios sin guardar | `e2e::test_cambiar_de_area_conserva_lo_digitado_y_marca_el_punto` |
| registro-notas | Área del docente de curso | `sh::test_el_area_a_cargo_va_sin_celdas`, `vh::test_el_area_del_docente_de_curso_se_puede_pedir`, `ph::test_las_areas_a_cargo_van_atenuadas`, `e2e::test_el_area_del_docente_de_curso_no_tiene_celdas`, `gh::test_area_del_docente_de_curso` |
| registro-notas | Área sin competencias marcadas | `sh::test_la_marcable_sin_marcas_va_sin_celdas`, `vh::test_el_area_marcable_sin_marcas_no_lleva_celdas`, `ph::test_la_tira_trae_las_10_areas_tambien_las_sin_competencias` |
| registro-notas | Competencia sin marcar | `sh::test_las_columnas_son_las_marcadas_con_su_numero_del_catalogo`, `test_el_numero_es_la_posicion_entre_las_activas` |
| registro-notas | Nombre de la competencia | `e2e::test_el_nombre_de_la_competencia_aparece_al_recibir_el_foco` |
| registro-notas | Trasladado con notas | `sh::test_el_trasladado_con_notas_va_al_final_y_la_retirada_sin_notas_no` |
| registro-notas | Retirado sin notas | `sh::test_el_trasladado_con_notas_va_al_final_y_la_retirada_sin_notas_no`, `test_las_filas_son_los_activos_por_apellidos` |
| registro-notas | Escribir el nivel | `e2e::test_escribir_el_nivel_baja_a_la_misma_competencia_del_siguiente` |
| registro-notas | Logro destacado | `e2e::test_escribir_el_nivel_baja_a_la_misma_competencia_del_siguiente` (AD con «A» y «D» seguidas) |
| registro-notas | Tecla fuera de la escala | `e2e::test_escribir_el_nivel_baja_a_la_misma_competencia_del_siguiente` (la tecla se ignora con su aviso) |
| registro-notas | Barra de niveles | `e2e::test_la_barra_de_niveles_elige_con_flechas_y_enter` |
| registro-notas | Panel de la celda | `e2e::test_el_panel_del_celular_elige_y_pasa_al_siguiente`, `ph::test_el_panel_del_celular_el_recuadro_y_el_relleno` |
| registro-notas | Camino ideal (US-021) | `gh::test_c_con_conclusion_guarda_el_nivel_y_la_conclusion`, `test_c_con_diez_caracteres_se_guarda`, `mod::test_c_con_conclusion_de_10_a_500_caracteres_se_guarda` |
| registro-notas | Conclusión en B | `e2e::test_elegir_b_abre_el_recuadro_y_listo_conserva_el_texto` |
| registro-notas | Nivel A sin conclusión | `e2e::test_a_no_abre_ningun_recuadro`, `gh::test_a_con_conclusion_la_guarda_vacia`, `mod::test_ad_y_a_con_conclusion_los_rechaza_la_base` |
| registro-notas | De B a A | `e2e::test_de_b_a_a_borra_la_conclusion_al_guardar`, `gh::test_de_b_a_a_actualiza_y_deja_el_par_cambiado_sin_niveles` |
| registro-notas | Conclusión de un trasladado | `e2e::test_la_conclusion_de_un_trasladado_se_lee_sin_editar` |
| registro-notas | Borrar una nota guardada | `e2e::test_suprimir_no_borra_una_nota_guardada`, `gh::test_una_nota_no_vuelve_a_vacia` |
| registro-notas | Rellenar con A | `e2e::test_rellenar_vacias_solo_toca_las_vacias_y_queda_como_borrador` |
| registro-notas | Solo AD o A | `e2e::test_rellenar_vacias_solo_toca_las_vacias_y_queda_como_borrador`; el diálogo solo ofrece AD y A (`hoja.html`, `#confirmar-relleno`) |
| registro-notas | Camino ideal (US-020) | `gh::test_camino_ideal_guarda_la_nota_de_ana_quispe_y_deja_notas_guardadas`, `vh::test_guardar_responde_200_con_los_faltantes`, `test_la_nota_guardada_vuelve_al_abrir_la_hoja`, `e2e::test_guardar_persiste_al_recargar` |
| registro-notas | Flujo alternativo válido (US-020) | `gh::test_una_escritura_que_falla_a_mitad_no_deja_notas_ni_entrada` (todo o nada), `conc::test_dos_guardados_de_la_misma_celda_uno_guarda_y_el_otro_choca` |
| registro-notas | Envío repetido | `gh::test_el_envio_repetido_no_cambia_nada_ni_deja_otra_entrada` |
| registro-notas | Guardar con celdas vacías | `gh::test_con_celdas_vacias_guarda_las_demas_y_cuenta_las_faltantes`, `test_guardar_sin_celdas_no_deja_entrada` |
| registro-notas | Caso de error (US-021) | `e2e::test_c_sin_conclusion_no_guarda_nada_y_marca_la_celda`, `gh::test_conclusion_faltante_o_corta_no_guarda_nada` |
| registro-notas | Conclusión corta en B | `gh::test_conclusion_faltante_o_corta_no_guarda_nada`, `mod::test_b_y_c_sin_conclusion_valida_los_rechaza_la_base` |
| registro-notas | Envío sin conclusión que llega al servidor | `vh::test_una_c_sin_conclusion_da_400_con_las_celdas`, `gh::test_conclusion_faltante_o_corta_no_guarda_nada` |
| registro-notas | Camino ideal (US-022) | `gh::test_camino_ideal_guarda_la_nota_de_ana_quispe_y_deja_notas_guardadas` (nivel de la escala) |
| registro-notas | Minúsculas y espacios | `gh::test_minusculas_y_espacios` |
| registro-notas | Caso de error (US-022) | `gh::test_un_valor_fuera_de_la_escala_no_guarda_nada`, `test_con_valor_no_valido_y_conclusion_faltante_manda_el_de_la_escala`, `vh::test_un_valor_fuera_de_la_escala_da_400_con_las_celdas`, `mod::test_un_nivel_fuera_de_la_escala_lo_rechaza_la_base` |
| registro-notas | Estudiante trasladado con la hoja abierta | `gh::test_estudiante_trasladado_con_la_hoja_abierta`, `bor::test_un_estudiante_que_ya_no_es_activo_sale_del_borrador_con_aviso` |
| registro-notas | Competencia de otra área | `gh::test_competencia_de_otra_area`, `test_competencia_no_marcada_en_el_periodo`, `test_competencia_marcada_pero_desactivada`, `vh::test_una_celda_de_otra_area_da_400_hoja_cambiada` |
| registro-notas | Caso de error (US-020) | `e2e::test_sin_conexion_conserva_todo_y_reintentar_guarda` |
| registro-notas | Reintento | `e2e::test_sin_conexion_conserva_todo_y_reintentar_guarda` |
| registro-notas | Respuesta perdida | `bor::test_tras_una_respuesta_perdida_volver_al_valor_anterior_sigue_siendo_un_cambio` (6.1) |
| registro-notas | Guardar con la sesión vencida | `e2e::test_con_la_sesion_vencida_no_guarda_y_ofrece_volver_a_ingresar`, `vha::test_con_la_sesion_vencida_un_guardado_con_htmx_recibe_hx_redirect` |
| registro-notas | Volver con un borrador | `bor::test_el_borrador_vuelve_al_recargar_y_descartar_lo_borra`, `test_el_borrador_sobrevive_a_cerrar_el_navegador_y_su_guardar_guarda` |
| registro-notas | Descartar | `bor::test_el_borrador_vuelve_al_recargar_y_descartar_lo_borra` |
| registro-notas | Sin nombres en el dispositivo | `bor::test_el_dispositivo_guarda_solo_identificadores_niveles_conclusiones_y_fechas`, `vh::test_lleva_la_clave_del_borrador_sin_nombres` |
| registro-notas | Otra cuenta en el mismo navegador | `bor::test_otra_cuenta_en_el_mismo_navegador_no_ve_el_borrador` |
| registro-notas | Cerrar sesión desde la portada | `bor::test_cerrar_sesion_desde_la_portada_borra_los_borradores_de_la_cuenta`, `test_cerrar_sesion_desde_competencias_con_marcas_sin_guardar_borra_los_borradores`, `pan::test_cerrar_sesion_lleva_la_cuenta_para_borrar_sus_borradores` |
| registro-notas | Cierre por inactividad | `bor::test_el_cierre_por_inactividad_conserva_el_borrador` |
| registro-notas | Otra pestaña abierta al cerrar sesión | `bor::test_cerrar_sesion_en_otra_pestana_impide_volver_a_escribir_borradores` (6.1) |
| registro-notas | Cambio en otra pestaña | `bor::test_lo_que_cambia_en_una_pestana_aparece_en_la_otra` |
| registro-notas | Misma celda en las dos | `bor::test_la_misma_celda_en_las_dos_pestanas_conserva_lo_de_cada_una_y_avisa` (ver Minor de la parte D) |
| registro-notas | Borrador más antiguo que la nota | `bor::test_un_borrador_mas_antiguo_que_la_nota_avisa_y_guardar_guarda_lo_que_muestra` |
| registro-notas | Cambio de otra pestaña con otra nota guardada | `bor::test_un_cambio_de_otra_pestana_con_otra_base_avisa_la_nota_cambiada` (6.1) |
| registro-notas | Cambio al guardar | `gh::test_una_base_distinta_no_guarda_nada_y_trae_la_nota_actual`, `test_tras_el_choque_el_segundo_guardado_con_la_base_nueva_guarda`, `test_una_nota_creada_en_otro_dispositivo_sobre_una_celda_vacia_es_un_choque`, `vh::test_una_nota_cambiada_en_otro_dispositivo_da_409_con_las_celdas`, `e2e::test_una_nota_cambiada_desde_otro_lado_detiene_el_guardado_y_el_segundo_guarda`, `bor::test_una_nota_cambiada_en_otro_navegador_detiene_el_guardado` |
| registro-notas | Nada cambió en otro lado | `gh::test_nada_cambio_en_otro_lado_guarda_sin_avisos`, `test_una_base_distinta_con_la_actual_igual_a_la_enviada_no_es_un_choque` |
| registro-notas | Salir con cambios | `bor::test_salir_con_cambios_nombra_las_areas_de_todos_los_periodos_y_conserva_el_borrador`, `ph::test_el_dialogo_de_salida` |
| registro-notas | Salir sin guardar | `bor::test_salir_con_cambios_nombra_las_areas_de_todos_los_periodos_y_conserva_el_borrador` |
| registro-notas | Cerrar sesión con cambios | `bor::test_cerrar_sesion_con_cambios_dice_que_los_borradores_se_borraran`, `test_seguir_editando_tras_cerrar_sesion_conserva_el_borrador` |
| registro-notas | Recargar con cambios | `bor::test_recargar_con_cambios_muestra_el_aviso_del_navegador` |
| registro-notas | Conteo por notas | `sh::test_cuenta_notas_y_no_estudiantes`, `test_la_hoja_cuenta_los_mismos_faltantes_sin_otra_consulta`, `test_las_competencias_sin_marcar_no_cuentan`, `test_las_de_otra_area_no_cuentan`, `e2e::test_la_barra_cuenta_las_notas_que_faltan` |
| registro-notas | Trasladado sin nivel | `sh::test_el_trasladado_sin_nivel_no_cuenta`, `e2e::test_un_trasladado_sin_nivel_no_cuenta` |
| registro-notas | El borrador cuenta | `e2e::test_el_borrador_baja_el_conteo_y_se_anuncia` |
| registro-notas | Último bimestre | `sh::test_en_el_ultimo_bimestre_las_obligatorias_cuentan` |
| registro-notas | Flujo alternativo válido (US-022) | `e2e::test_tocar_el_conteo_deja_solo_los_pendientes_y_enter_salta` |
| registro-notas | Siguiente faltante en la PC | `e2e::test_tocar_el_conteo_deja_solo_los_pendientes_y_enter_salta`; en el celular, `test_en_el_celular_el_panel_salta_entre_faltantes` |
| registro-notas | Fila completada | `e2e::test_tocar_el_conteo_deja_solo_los_pendientes_y_enter_salta` |
| registro-notas | Matemática completa | `e2e::test_con_todo_guardado_dice_area_completa` |
| registro-notas | Completa sin guardar | `e2e::test_completa_sin_guardar_dice_un_cambio_y_sin_faltantes` |
| registro-notas | Axe en ambos temas | `e2e::test_axe_con_notas_errores_filtro_y_dialogo`, `test_axe_en_vacaciones`, `test_axe_sin_periodos` (claro y oscuro, 360 y 1280 px) |
| registro-notas | Sin desplazamiento de la página | `e2e::test_personal_social_no_desplaza_la_pagina_y_la_tira_se_desplaza_sola`, `test_las_areas_tactiles_miden_44_px`, `ph::test_la_tira_vive_en_su_propio_contenedor` |
| registro-notas | Lector de pantalla en una celda | `e2e::test_el_lector_lee_estudiante_competencia_y_nivel`, `ph::test_las_regiones_del_lector_de_pantalla_y_el_noscript` |
| competencias-periodo | Sección de otra docente / Sección de un año cerrado / Otro rol / Sin sesión | Sin cambios de US-029: `acc::test_otra_docente_recibe_404_y_no_guarda`, `test_la_seccion_de_un_anio_cerrado_da_404_y_no_guarda`, `test_la_direccion_llega_a_su_pantalla`, `test_sin_sesion_va_a_ingresar_con_next` |
| competencias-periodo | Portada sin cambios | `acc::test_la_portada_lleva_a_la_hoja_y_no_a_las_competencias` |
| competencias-periodo | Desde la hoja de notas | `ph::test_el_boton_competencias_lleva_el_periodo_y_el_area`, `e2e::test_competencias_vuelve_a_las_notas_del_periodo_y_el_area` |
| competencias-periodo | Caso de error | `ce2e::test_desmarcar_una_competencia_con_notas_muestra_el_motivo` (ya sin parchear `tiene_notas`) |
| competencias-periodo | Guardado que la quita | `vis::test_quitar_una_competencia_con_notas_responde_409`, `ce2e::test_un_guardado_que_choca_con_notas_las_bloquea_en_pantalla`, `conc::test_notas_y_marcas_a_la_vez_nunca_dejan_una_nota_de_una_competencia_desmarcada` |
| competencias-periodo | Una sola nota basta | `obl::test_una_sola_nota_basta`, `test_las_notas_de_otra_seccion_no_cuentan_en_el_periodo` |
| competencias-periodo | Notas de otro periodo | `obl::test_las_notas_de_otro_periodo_no_cuentan`, `gua::test_con_notas_en_otro_periodo_se_puede_quitar` |
| competencias-periodo | Flujo alternativo válido | `obl::test_una_con_notas_en_un_solo_periodo_anterior_ya_no_es_obligatoria`, `test_las_notas_de_otra_seccion_no_cuentan`; los de US-029 siguen |
| competencias-periodo | Marcada antes, sin notas | `obl::test_marcada_antes_sin_notas_sigue_siendo_obligatoria` |
| competencias-periodo | Guardado sin las obligatorias / Otro periodo | Sin cambios de US-029: `gua::test_en_el_bimestre_4_las_obligatorias_se_agregan_aunque_falten_en_el_envio`, `obl::test_en_el_bimestre_3_ninguna_es_obligatoria` |
| competencias-periodo | Volver a las notas | `pla::test_registrar_notas_lleva_el_periodo_y_el_area`, `test_el_periodo_pedido_cambia_el_enlace_de_notas`, `e2e::test_competencias_vuelve_a_las_notas_del_periodo_y_el_area` |
| competencias-periodo | Llega sin competencias confirmadas | `pla::test_con_desde_notas_avisa_que_el_bimestre_no_tiene_competencias`, `test_sin_desde_notas_no_hay_aviso_de_confirmar`, `vh::test_sin_marcas_lleva_a_competencias_con_periodo_area_y_desde` |
| competencias-periodo | Con cambios sin guardar | Sin prueba propia del enlace: «Registrar notas» es un enlace de la pantalla y pasa por el mismo diálogo de salida que prueban `ce2e::test_el_dialogo_de_salida_nombra_los_periodos_y_pone_el_foco_en_seguir_editando` y `test_salir_sin_guardar_sale_sin_aviso_del_navegador` |
| registro-actividad | Catálogo de esta historia | `amod::test_solo_las_operaciones_de_asistencia_y_notas_guardadas_cuentan_para_kpi_01` |
| registro-actividad | Operación fuera del catálogo | Sin cambios: `amod::test_operacion_fuera_del_catalogo_la_rechaza_la_base` |
| registro-actividad | Cada operación tiene su prueba | `acat::test_la_tabla_cubre_el_catalogo_menos_las_reservadas`, `test_cada_escenario_es_una_prueba_que_existe` (NOTAS_GUARDADAS → `gh::test_camino_ideal_guarda_la_nota_de_ana_quispe_y_deja_notas_guardadas`) |
| registro-actividad | Primer guardado del área | `gh::test_camino_ideal_guarda_la_nota_de_ana_quispe_y_deja_notas_guardadas` |
| registro-actividad | Corrección | `gh::test_de_b_a_a_actualiza_y_deja_el_par_cambiado_sin_niveles` |
| registro-actividad | Solo cambia la conclusión | `gh::test_solo_cambia_la_conclusion_lista_el_par_sin_el_texto` |
| registro-actividad | Sin cambios | `gh::test_el_envio_repetido_no_cambia_nada_ni_deja_otra_entrada`, `test_guardar_sin_celdas_no_deja_entrada` |
| pantallas-de-inicio | Tres dimensiones en "Próximamente" / Toque en una tarjeta "Próximamente" | Sin cambios: `pan::test_las_tarjetas_proximamente_son_botones_sin_enlace`, `test_cada_tarjeta_proximamente_tiene_su_region_aria_live_vacia`, `port::test_tarjeta_proximamente_avisa_sin_mover_la_miniatura` |
| pantallas-de-inicio | Dimensión activada por su historia | `dim::test_desde_us_020_notas_y_asistencia_estan_disponibles`, `test_notas_y_asistencia_son_pantallas_de_la_seccion` |
| pantallas-de-inicio | Bandera activa sin pantalla | Sin cambios: `dim::test_toda_dimension_disponible_resuelve_su_pantalla`, `test_la_revision_detecta_una_bandera_activa_sin_pantalla` |
| pantallas-de-inicio | Asistencia con una sección / Asistencia sin sección única | Sin cambios de US-030: `port::test_la_tarjeta_asistencia_lleva_a_la_asistencia_de_hoy`, `pan::test_sin_seccion_unica_asistencia_es_proximamente` |
| pantallas-de-inicio | Notas con una sección | `pan::test_con_una_seccion_notas_lleva_a_la_hoja_de_notas`, `vh::test_sin_marcas_lleva_a_competencias_con_periodo_area_y_desde` |
| pantallas-de-inicio | Notas sin sección única | `pan::test_sin_seccion_unica_notas_es_proximamente` |
| indicadores-adopcion | Columnas aún sin datos | `ind::test_sesiones_queda_sin_dato` |
| indicadores-adopcion | Secciones con notas | `ind::test_secciones_con_notas_cuenta_secciones_distintas`, `test_las_notas_cuentan_en_su_semana`, `test_guardar_notas_cuenta_como_docente_activa` |
| indicadores-adopcion | Semana sin notas | `ind::test_semana_sin_notas_dice_cero` |
| indicadores-adopcion | Notas de la demostración | `ind::test_las_notas_de_la_demostracion_no_cuentan` |
| datos-demostracion | Quitar la demostración con notas | `demo::test_quitar_la_demostracion_con_notas`, `cmd::test_quitar_demo_dice_las_notas_que_borraria` |
| datos-demostracion | Descartar una sección con notas | `demo::test_descartar_una_seccion_con_notas`, `cmd::test_descartar_borra_las_notas_y_las_nombra` |
| datos-demostracion | Cargar la demostración | `demo::test_cargar_la_demostracion_no_crea_notas` |

## DoD 1 a 9

| N.° | Criterio | Estado |
| --- | --- | --- |
| 1 | Cobertura ≥ 80 % | Local: 98,47 % total (`verificar.py`, sin e2e). Sonar way: pendiente del PR |
| 2 | Análisis estático sin críticas ni altas | Ruff en verde con `verificar.py`. CodeQL y SonarQube Cloud: pendiente del PR |
| 3 | Aprobación de otra integrante | Pendiente del PR |
| 4 | Vista previa de Vercel | `5ab5681` desplegó y aplicó `notas/0002` y `actividad/0004` en la rama de Neon (ver 6.1). Se repite con el commit de cierre |
| 5 | Escenarios en verde y e2e de la ruta ideal | Los 117 escenarios tienen prueba o nota y pasan en local; la ruta ideal, `e2e::test_guardar_persiste_al_recargar`. GitHub Actions: pendiente del PR |
| 6 | Reglas de negocio con pruebas propias | RN-001 (escala AD, A, B, C): `gh::test_un_valor_fuera_de_la_escala_no_guarda_nada`, `mod::test_un_nivel_fuera_de_la_escala_lo_rechaza_la_base`. RN-003 (conclusión en B y C): `gh::test_conclusion_faltante_o_corta_no_guarda_nada`, `mod::test_b_y_c_sin_conclusion_valida_los_rechaza_la_base`. RN-005 (nivel al cerrar el año): `obl::test_marcada_antes_sin_notas_sigue_siendo_obligatoria`, `sh::test_en_el_ultimo_bimestre_las_obligatorias_cuentan`. RN-015 (registro sin datos sensibles): `gh::test_de_b_a_a_actualiza_y_deja_el_par_cambiado_sin_niveles`, `test_solo_cambia_la_conclusion_lista_el_par_sin_el_texto`. RN-023 (no se borra): `gh::test_una_nota_no_vuelve_a_vacia`, `mod::test_borrar_un_estudiante_con_notas_falla` |
| 7 | Accesibilidad sin errores críticos | `e2e::test_axe_con_notas_errores_filtro_y_dialogo`, `test_axe_en_vacaciones`, `test_axe_sin_periodos` (claro y oscuro, 360 y 1280 px), `test_personal_social_no_desplaza_la_pagina_y_la_tira_se_desplaza_sola`, `test_las_areas_tactiles_miden_44_px`, `test_el_lector_lee_estudiante_competencia_y_nivel`; rendimiento con `test_la_hoja_mas_grande_con_slow_4g` |
| 8 | Sin datos reales | Secciones, estudiantes y notas ficticios en pruebas y demo; el dispositivo no guarda nombres (`bor::test_el_dispositivo_guarda_solo_identificadores_niveles_conclusiones_y_fechas`). Revisión del PR: pendiente |
| 9 | Documentación | Specs del cambio en OpenSpec y docstrings. Las rutas nuevas están en el Catálogo de rutas de `docs/03`. Ningún requisito cambió. Los ajustes a `decisiones.md` y las contradicciones con los documentos congelados están en `tasks.md` ("Ajustes del propose" y "Workflow follow-up") |
