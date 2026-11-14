# Verificación: rebrand de la Portada del docente

Rama `feature/rebrand` (paso 3 del PLAN del rebrand). Todos los escenarios de la spec delta de `pantallas-de-inicio` tienen prueba. El requisito «Carrusel de dimensiones en el celular» queda retirado y su migración también tiene prueba. Las e2e de `estudiantes-seccion` que estaban en `skip` por D8 de `rebrand-us-006` ya corren dentro del diálogo, sin ninguna saltada.

Pruebas en `src/backend/`. Abreviaturas: en `cuentas/tests/`, `pant` = `test_pantallas.py`, `dim` = `test_dimensiones.py`, `por` = `test_portada_e2e.py`, `axe` = `test_accesibilidad_e2e.py`, `marco` = `test_marco_rebrand.py`; en `institucion/tests/`, `e2e` = `test_estudiantes_e2e.py`.

## Minor para la descripción del PR

- Sin revisor: ninguna parte era de alto riesgo (`tasks.md`).
- La A2 (Codex) dio *approve* sin hallazgos. Codex no pudo iniciar Chromium en su entorno de solo lectura; las e2e las corrió Marco en local (ver DoD 5).
- Teclado real en un celular (E-02 de `rebrand-us-006`) sigue sin verificarse: solo hay emulación de DevTools. Pasa a la deuda del pulido final.

## Revisión A2 (Codex)

Sin hallazgos. Foco: spec `pantallas-de-inicio`, D3 (tarjeta), D5 (`portada.js` sin Alpine) y D6 (diálogo de Estudiantes en el CSS compartido). El hallazgo [high] de `rebrand-us-006` (lista larga cortada en el diálogo) se corrigió aquí con D6; lo prueba `e2e::test_con_40_el_ultimo_editar_se_alcanza_desplazando_el_cuerpo`.

## Escenarios

### Spec delta (`pantallas-de-inicio`)

| Escenario | Prueba |
|---|---|
| Portada al entrar | `pant::test_tres_tarjetas_en_orden_con_su_frase_y_sin_subtitulo_formal`, `pant::test_la_portada_saluda_con_el_nombre_completo`; `dim::test_las_tres_dimensiones_en_orden_con_sus_textos`, `dim::test_las_tarjetas_no_traen_el_subtitulo_formal` |
| Orden de lectura | `pant::test_tres_tarjetas_en_orden_con_su_frase_y_sin_subtitulo_formal`, `pant::test_las_tarjetas_van_en_la_navegacion_tus_accesos`; `por::test_a_360_las_tres_se_apilan_en_el_orden_del_dom` |
| Tarjetas en el celular | `por::test_a_360_las_tres_se_apilan_en_el_orden_del_dom`, `por::test_a_360_sesiones_y_notas_llevan_la_miniatura_junto_al_texto`; sin chips ni puntos: `pant::test_la_portada_no_lleva_el_carrusel`; sin desplazamiento: `por::test_la_portada_no_se_desplaza_en_horizontal` |
| Tarjetas en la computadora | `por::test_a_1280_asistencia_ocupa_la_columna_principal`, `por::test_en_asistencia_el_boton_va_debajo_de_la_miniatura` |
| Saludo según la hora | `pant::test_el_saludo_depende_de_la_hora_de_lima` (parametrizada: 12:00 y 19:00) |
| Docente con una sección | `pant::test_la_portada_muestra_la_seccion_bajo_el_saludo_y_fuera_del_h1` |
| Docente con varias secciones | `pant::test_la_portada_ordena_las_secciones_por_grado_y_nombre` |
| Docente sin sección | `pant::test_la_portada_sin_seccion_dice_que_aparecera` |
| Sección de un año cerrado | `pant::test_la_portada_con_la_unica_seccion_en_un_anio_cerrado` |
| Enlace a la lista con una sección | `pant::test_con_una_seccion_ver_estudiantes_va_junto_a_la_linea`, `pant::test_con_una_seccion_la_portada_tiene_el_dialogo_vacio`; `e2e::test_ver_estudiantes_abre_el_dialogo_sin_cambiar_la_direccion` |
| Sin enlace con varias secciones | `pant::test_sin_seccion_o_con_varias_no_hay_enlace_ni_aviso_ni_dialogo` (caso varias) |
| Sin enlace sin sección | `pant::test_sin_seccion_o_con_varias_no_hay_enlace_ni_aviso_ni_dialogo` (caso sin sección) |
| Sección sin estudiantes | `pant::test_la_seccion_sin_estudiantes_muestra_el_aviso_bajo_la_linea`, `pant::test_con_estudiantes_la_portada_no_muestra_el_aviso` |
| El aviso desaparece al cargar la lista | `e2e::test_tras_importar_y_cerrar_la_portada_ya_no_muestra_el_aviso`, `e2e::test_vaciar_25_deja_la_lista_vacia_y_el_aviso_vuelve_a_la_portada` |
| Asistencia de hoy pendiente | `pant::test_la_asistencia_de_hoy_pendiente_lleva_la_pildora` (ninguno y a medias); sin animación (D7): `por::test_la_pildora_no_tiene_animacion` |
| Asistencia de hoy completa | `pant::test_con_la_jornada_completa_no_hay_pildora`, `pant::test_la_jornada_de_otro_dia_no_completa_la_de_hoy` |
| Fin de semana o sección sin estudiantes | `pant::test_el_sabado_no_hay_pildora`, `pant::test_sin_estudiantes_no_hay_pildora` |
| Revisión de cada pantalla (axe) | `axe::test_sin_infracciones_graves_de_accesibilidad`: las 8 vistas de la portada (normal, una sección, varias, sin estudiantes, «Hoy: pendiente», «Próximamente» con su aviso, menú de la cuenta, diálogo de Estudiantes) más inicio de sesión, dirección y «sin permiso», en claro y oscuro, a 360 y 1280 px; `por::test_la_portada_con_y_sin_pildora_pasa_axe`; `e2e::test_la_portada_con_el_aviso_pasa_axe`, `e2e::test_la_lista_con_estudiantes_pasa_axe` |
| Pantallas a 320 px | `por::test_el_documento_no_se_desplaza_en_horizontal`; `axe::test_el_inicio_de_sesion_no_desborda`, `axe::test_sin_permiso_no_desborda_y_su_boton_es_tactil` |
| Portada sin desplazamiento interno | `por::test_la_portada_no_se_desplaza_en_horizontal` (320 y 360 px, ambos temas, con la píldora y con el aviso: ni el documento ni `.accesos`) |

### Requisito retirado: «Carrusel de dimensiones en el celular»

| Comprobación | Prueba |
|---|---|
| Sin `data-carrusel`, chips, puntos, `x-data` ni `carrusel__` | `pant::test_la_portada_no_lleva_el_carrusel`; `dim::test_sin_carrusel_no_hay_tarjeta_inicial` |
| Sin Alpine en la portada (D5) | `pant::test_la_portada_carga_sus_scripts_sin_alpine`, `pant::test_la_portada_carga_solo_la_hoja_del_rebrand` |
| Las tarjetas siguen leyéndose en vertical y `#c-<clave>` sigue llevando a cada una | `por::test_a_360_las_tres_se_apilan_en_el_orden_del_dom`; `pant::test_tres_tarjetas_en_orden_con_su_frase_y_sin_subtitulo_formal` (`id="c-<clave>"`) |

### Decisiones del diseño (D1 a D7)

| Decisión | Prueba |
|---|---|
| D1 barra no fija, bloque `clase_barra` | `pant::test_la_barra_de_la_portada_no_es_fija_ni_lleva_el_menu_de_navegacion`, `por::test_la_barra_de_la_portada_no_es_una_franja_ni_se_queda_fija`; `marco` (el bloque vacío no cambia «sin permiso») |
| D2 `DIMENSIONES` en orden con `frase`, sin `tarjeta_inicial` | `dim::test_las_tres_dimensiones_en_orden_con_sus_textos`, `dim::test_sin_carrusel_no_hay_tarjeta_inicial`, `dim::test_inicio_y_las_tres_dimensiones_en_el_orden_del_menu` |
| D3 tarjeta: disponible y «Próximamente» | `pant::test_una_dimension_disponible_enlaza_a_su_pantalla`, `pant::test_las_tarjetas_proximamente_son_botones_sin_enlace`, `pant::test_cada_tarjeta_proximamente_tiene_su_region_aria_live_vacia`; `por::test_toda_la_tarjeta_notas_lleva_a_la_hoja`, `por::test_la_tarjeta_asistencia_lleva_a_la_asistencia_de_hoy` |
| D4 miniaturas esquemáticas | `pant::test_cada_miniatura_es_esquematica_y_oculta_al_lector`, `pant::test_las_miniaturas_dicen_solo_su_esquema`; `por::test_las_miniaturas_llevan_el_mismo_papel_en_los_dos_temas`, `por::test_los_tokens_aplicados_toman_su_valor_del_tema` |
| D5 aviso de «Próximamente» sin Alpine | `por::test_tarjeta_proximamente_avisa_sin_mover_la_miniatura`, `por::test_un_segundo_toque_vuelve_a_escribir_el_aviso`, `por::test_el_aviso_se_vacia_a_los_tres_segundos` |
| D6 diálogo `dialog--lista` con el cuerpo desplazable | `e2e::test_con_40_el_ultimo_editar_se_alcanza_desplazando_el_cuerpo` (360 y 1280 px), `e2e::test_al_cambiar_de_vista_el_cuerpo_del_dialogo_vuelve_arriba`, `e2e::test_el_dialogo_deja_la_portada_inerte_y_sin_desplazamiento` |
| D7 «Hoy: pendiente» sin animación | `por::test_la_pildora_no_tiene_animacion` |

### Escenarios de `estudiantes-seccion` que vuelven a correr

La conducta no cambia. Corren las e2e de Estudiantes dentro del diálogo, sin ninguna en `skip`: `e2e::test_ver_estudiantes_abre_el_dialogo_sin_cambiar_la_direccion`, `test_el_foco_entra_al_titulo_del_dialogo`, `test_esc_cierra_el_dialogo_y_el_foco_vuelve_al_enlace`, `test_cerrar_cierra_el_dialogo_y_el_foco_vuelve_al_enlace`, `test_atras_cierra_el_dialogo_y_la_portada_sigue`, `test_camino_ideal_importa_los_25_con_lineas_en_blanco`, `test_caso_de_error_no_guarda_nada_y_conserva_el_texto`, `test_sesion_vencida_al_importar_lleva_la_pagina_a_ingresar`, `test_un_nombre_de_120_mas_120_se_lee_completo_en_el_dialogo`, `test_flujo_alternativo_valido_agrega_y_la_cabecera_pasa_a_26`, `test_corregir_un_nombre_vuelve_a_la_lista_con_el_nombre_corregido`, `test_quitar_uno_baja_la_cabecera_en_uno`, `test_vaciar_25_deja_la_lista_vacia_y_el_aviso_vuelve_a_la_portada`.

## DoD 1 a 9

| N.° | Criterio | Estado |
| --- | --- | --- |
| 1 | Cobertura ≥ 80 % | Local: 98,52 % total (`pytest --cov`, 2134 pruebas en verde, sin e2e). Sonar way: pendiente del PR |
| 2 | Análisis estático sin críticas ni altas | Ruff en verde con `verificar.py`. A2 de Codex: sin hallazgos. CodeQL y SonarQube Cloud: pendiente del PR |
| 3 | Aprobación de otra integrante | Pendiente del PR |
| 4 | Vista previa de Vercel | Pendiente del push |
| 5 | Escenarios en verde y e2e de la ruta ideal | Todos los escenarios tienen prueba (tablas de arriba). `pytest -m e2e --browser chromium`: 602 pruebas en verde, ninguna saltada (corrida local de Marco, 15 min 55 s; Codex no pudo iniciar Chromium). GitHub Actions: pendiente del PR |
| 6 | Reglas de negocio con pruebas propias | Sin reglas nuevas: la regla de disponibilidad de `dimensiones.py` no cambia (D2) y `servicios.py` y modelos quedan igual |
| 7 | Accesibilidad sin errores críticos | axe sobre las 8 vistas de la portada, en claro y oscuro, a 360 y 1280 px, incluido el diálogo de Estudiantes (tabla de arriba). Pantalla vista en claro/oscuro y celular/escritorio con el diálogo abierto: tarea 1.13, por Marco |
| 8 | Sin datos reales | Estudiantes y secciones ficticios de las fixtures; las miniaturas no traen nombres, fechas ni cifras de registro |
| 9 | Documentación | Spec delta, `design.md` y `tasks.md`. Sin rutas nuevas: `docs/03` y README sin cambios. Deuda en `tasks.md` («Workflow follow-up»); pendiente de tesis: anotar en `docs/PENDIENTES_TESIS.md` si un capítulo describe la portada con los subtítulos formales |
