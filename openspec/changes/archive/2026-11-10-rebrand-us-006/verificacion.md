# Verificación: rebrand de Estudiantes (US-006)

Rama `feature/rebrand` (paso 2 del PLAN del rebrand). Los 3 escenarios de la spec delta de `estudiantes-seccion` tienen prueba como página completa. Los 31 escenarios de `estudiantes-seccion` que no cambian se vuelven a correr con las pruebas de US-006/031, ajustadas de clases viejas a ganchos (`id`, `data-estudiante`, `.estudiante-nombre`). `servicios.py`, modelos y rutas no cambian; de `estudiantes.js` cambia solo un selector (`.modal-cuerpo` → `#modal-cuerpo`, D4).

Pruebas en `src/backend/`. Abreviaturas: en `institucion/tests/`, `vis` = `test_vistas_estudiantes.py` y `e2e` = `test_estudiantes_e2e.py`; en `cuentas/tests/`, `rb` = `test_componentes_rb.py`, `hoja` = `test_hoja_rebrand_e2e.py`, `marco` = `test_marco_rebrand.py`.

## Minor para la descripción del PR

- Sin revisor: ninguna parte era de alto riesgo (`tasks.md`).
- 5.1 (E-02) no se verificó en un celular real: solo con la emulación de DevTools, que no abre el teclado. Pasa a la deuda del pulido final y se prueba sobre el popup en `rebrand-portada`. Safari en iPhone ignora `interactive-widget`, así que el pie podría quedar bajo el teclado.
- 10 e2e están en `skip` con motivo `rebrand-portada` (D8): miden el aspecto dentro del diálogo, que la portada aún no tiene. Sus gemelas como página completa están en verde.

## Revisión A2 (Codex, 5.2)

| Hallazgo | Decisión | Prueba |
|---|---|---|
| [high] `_base.html:17`: el diálogo de la portada (`<dialog class="modal-estudiantes">`, solo `app.css`) ya no encuentra `overflow-y:auto`, porque el cuerpo pasó de `.modal-cuerpo` a `.dialog-cuerpo`, que solo existe en `rebrand.css`. Una lista larga queda cortada sin forma de desplazarla. Confirmado leyendo `app.css` y `portada_docente.html:28`, sin correr el navegador | Marco: no se corrige en esta rama. Se corrige en `rebrand-portada`, donde el `<dialog id="estudiantes">` recibe `dialog dialog--lista` y carga `rebrand.css`. El push espera a que se cierren los dos cambios, así que la rama no llega a `main` con este estado | En `rebrand-portada`: quitar los 10 `skip` y añadir una e2e con una lista que supere el alto del diálogo (por ejemplo 60 estudiantes) que compruebe que el cuerpo se desplaza y el último «Editar» se alcanza |

## Escenarios (cierre, 5.3)

### Spec delta (`estudiantes-seccion`, requisitos modificados)

| Escenario | Prueba |
|---|---|
| Revisión de cada vista | Como página completa, claro y oscuro, 360 y 1280 px: `e2e::test_la_lista_vacia_como_pagina_completa_pasa_axe`, `test_la_lista_como_pagina_completa_pasa_axe`, `test_la_lista_con_el_aviso_de_importados_como_pagina_completa_pasa_axe`, `test_pegar_lista_como_pagina_completa_pasa_axe`, `test_revisar_lista_como_pagina_completa_pasa_axe`, `test_agregar_como_pagina_completa_pasa_axe`, `test_agregar_con_homonimo_como_pagina_completa_pasa_axe`, `test_editar_como_pagina_completa_pasa_axe`, `test_quitar_vaciar_y_los_bloqueos_como_pagina_completa_pasan_axe`. **Dentro del diálogo: saltadas (`rebrand-portada`)** |
| Página completa en el marco del rebrand | `vis::test_la_pagina_completa_va_en_el_marco_del_rebrand`, `test_sin_htmx_responde_la_pagina_completa_con_h1`, `test_la_pagina_completa_no_tiene_cerrar_y_vuelve_a_la_portada` |
| Nombre largo a 320 px | `e2e::test_un_nombre_de_120_mas_120_se_lee_completo_como_pagina_completa` (también al 200 %), `e2e::test_a_360_el_pie_apila_sus_acciones_a_todo_el_ancho`. **En el diálogo: saltada (`rebrand-portada`)** |

### Componentes y viewport (D5, D6, D7)

| Comportamiento | Prueba |
|---|---|
| `rb/boton.html` con `formulario` (E-05) | `rb::test_boton_con_formulario_pone_el_atributo_form`, `test_boton_sin_formulario_no_cambia`, `test_boton_con_href_ignora_formulario` |
| `rb/campo.html`: `maxlength`, `autocapitalize`, `descrito_por`, `foco` (E-06) | `rb::test_campo_pinta_maxlength_desde_el_campo_de_django`, `test_campo_sin_max_length_no_pinta_maxlength`, `test_campo_con_autocapitalize_pinta_el_valor_y_apaga_el_corrector`, `test_campo_con_descrito_por_lo_suma_a_la_ayuda_y_al_error`, `test_campo_con_descrito_por_solo_lo_nombra`, `test_campo_con_foco_marca_solo_el_campo_indicado`, `test_campo_sin_foco_no_trae_data_foco` |
| `rb/mensaje.html` con `estado` | `rb::test_mensaje_con_estado_trae_role_status`, `test_mensaje_con_alerta_o_enfocar_ignora_estado`, `test_mensaje_sin_estado_ni_alerta_no_trae_role` |
| Viewport `interactive-widget=resizes-content` y alto en `dvh` (E-02) | `marco::test_el_viewport_achica_el_area_de_diseno_con_el_teclado`; `hoja::test_el_alto_del_dialogo_y_de_la_hoja_usa_dvh_no_svh`, `test_el_dialogo_de_la_lista_mide_760_sin_svh_ni_transiciones_de_ancho_o_alto`. Teclado real: sin verificar (ver Minor) |
| Marcado de cada vista (D1, D3, D5) | `vis::test_lista_vacia_con_sus_dos_acciones`, `test_la_lista_numera_en_orden_con_el_nombre_completo_y_editar`, `test_agregar_va_arriba_y_vaciar_al_final`, `test_el_aviso_de_la_portada_usa_el_mensaje_del_rebrand`, `test_agregar_tiene_dos_campos_obligatorios_de_120`, `test_quitar_pide_confirmacion_con_el_nombre`, `test_vaciar_pide_confirmacion_con_la_cantidad`, `test_vaciar_con_un_estudiante_va_en_singular` |
| Primera línea vacía y número de línea (E-03) | `vis::test_una_primera_linea_vacia_se_conserva_y_los_numeros_de_error_no_se_corren` |
| El cuerpo vuelve arriba al cambiar de vista (D4) | `e2e::test_al_cambiar_de_vista_el_cuerpo_del_dialogo_vuelve_arriba` |
| Plantillas sin colores fijos | `vis::test_las_plantillas_no_llevan_colores_hexadecimales_ni_style` |

### Escenarios de `estudiantes-seccion` que se vuelven a correr

La conducta no cambia; las pruebas son las de US-006/031 (`openspec/changes/archive/2026-10-29-us-006-importar-estudiantes/verificacion.md`), con sus selectores pasados a los ganchos del marcado nuevo.

| Escenario | Prueba |
|---|---|
| Acceso: sección de otra docente, año cerrado, estudiante de otra sección, otro rol | `vis::test_otra_docente_recibe_403_sin_nombres_y_queda_el_intento`, `test_una_seccion_del_anio_cerrado_da_403_anio_cerrado`, `test_un_estudiante_de_otra_seccion_da_403_estudiante`, `test_la_direccion_llega_a_su_pantalla` |
| Abrir y cerrar el diálogo | Conducta: `e2e::test_ver_estudiantes_abre_el_dialogo_sin_cambiar_la_direccion`, `test_el_foco_entra_al_titulo_del_dialogo`, `test_esc_cierra_el_dialogo_y_el_foco_vuelve_al_enlace`, `test_cerrar_cierra_el_dialogo_y_el_foco_vuelve_al_enlace`, `test_atras_cierra_el_dialogo_y_la_portada_sigue` |
| Sin JavaScript | `e2e::test_sin_javascript_todo_funciona_como_pagina_completa` |
| Lista vacía, orden y número | `vis::test_lista_vacia_con_sus_dos_acciones`, `test_la_lista_numera_en_orden_con_el_nombre_completo_y_editar` |
| Pegar lista: camino ideal, líneas en blanco, paso siguiente | `e2e::test_camino_ideal_importa_los_25_con_lineas_en_blanco`, `vis::test_importar_una_lista_valida_redirige_con_303_y_guarda`, `test_el_aviso_de_exito_se_ve_una_sola_vez` |
| Pegar solo con la sección vacía | `vis::test_la_lista_con_estudiantes_no_ofrece_pegar_lista`, `test_pegar_con_estudiantes_muestra_el_aviso_sin_el_cuadro`, `test_el_envio_a_una_seccion_con_estudiantes_no_guarda_nada` |
| Errores de la lista pegada | `vis::test_con_errores_responde_200_con_el_formulario_y_no_guarda`, `test_con_errores_el_texto_vuelve_intacto_con_aria_invalid`, `test_el_texto_vacio_pide_pegar_al_menos_uno`; `e2e::test_caso_de_error_no_guarda_nada_y_conserva_el_texto` |
| Agregar: flujo válido, homónimo, campo vacío | `vis::test_guardar_y_agregar_otro_redirige_a_agregar_con_303`, `test_el_homonimo_al_agregar_conserva_lo_escrito_y_sugiere_el_segundo_nombre`, `test_un_campo_vacio_muestra_su_error_y_no_guarda`; `e2e::test_flujo_alternativo_valido_agrega_y_la_cabecera_pasa_a_26` |
| Editar: corregir, homónimo | `vis::test_guardar_cambios_vuelve_a_la_lista_con_el_nombre_corregido`, `test_la_correccion_que_crea_un_homonimo_no_se_guarda`; `e2e::test_corregir_un_nombre_vuelve_a_la_lista_con_el_nombre_corregido` |
| Quitar y vaciar, con y sin registros | `vis::test_quitar_sin_registros_vuelve_a_la_lista_con_uno_menos`, `test_quitar_con_registros_muestra_el_bloqueo_y_no_quita`, `test_vaciar_sin_registros_deja_la_lista_vacia_y_el_aviso_de_la_portada`, `test_vaciar_con_registros_muestra_el_bloqueo_y_no_quita_ninguno`; `e2e::test_quitar_uno_baja_la_cabecera_en_uno`, `test_vaciar_25_deja_la_lista_vacia_y_el_aviso_vuelve_a_la_portada` |
| Sesión vencida con el diálogo abierto | `e2e::test_sesion_vencida_al_importar_lleva_la_pagina_a_ingresar`, `vis::test_con_htmx_la_seccion_ajena_da_403_con_hx_redirect` |
| Estudiante, estado y nombre (servicio) | Sin cambios de servidor: pruebas de servicios de US-006 |

## DoD 1 a 9

| N.° | Criterio | Estado |
| --- | --- | --- |
| 1 | Cobertura ≥ 80 % | Local: 98,52 % total (`verificar.py`, sin e2e). Sonar way: pendiente del push |
| 2 | Análisis estático sin críticas ni altas | Ruff en verde con `verificar.py`. A2 de Codex: un hallazgo [high] anotado sin corregir por decisión de Marco, se corrige en `rebrand-portada` (ver arriba). CodeQL y SonarQube Cloud: pendiente del push |
| 3 | Aprobación de otra integrante | Pendiente del PR único del rebrand |
| 4 | Vista previa de Vercel | Pendiente del push |
| 5 | Escenarios en verde y e2e de la ruta ideal | Los 3 de la delta y los que se vuelven a correr tienen prueba; e2e de `institucion` en verde en 4.7 y 4.8 (no se volvieron a correr en el cierre, sin cambios de código). Ruta ideal: `e2e::test_camino_ideal_importa_los_25_con_lineas_en_blanco`. 10 e2e en `skip` por `rebrand-portada`. GitHub Actions: pendiente del push |
| 6 | Reglas de negocio con pruebas propias | Sin reglas nuevas: `servicios.py` y modelos sin cambios; las de US-006/031 siguen en verde |
| 7 | Accesibilidad sin errores críticos | axe en todas las vistas como página completa (claro/oscuro, 360/1280 px). Dentro del diálogo: pendiente de `rebrand-portada`. Pantalla vista en claro/oscuro y celular/escritorio como página completa por Marco (4.9); popup y teclado real sin ver |
| 8 | Sin datos reales | Estudiantes ficticios de las fixtures |
| 9 | Documentación | Spec delta, `design.md` (D1 a D8) y comentarios de uso de `rb/boton.html`, `rb/campo.html` y `rb/mensaje.html`. Sin rutas nuevas: `docs/03` y README sin cambios. Deuda en `tasks.md` («Workflow follow-up») |
