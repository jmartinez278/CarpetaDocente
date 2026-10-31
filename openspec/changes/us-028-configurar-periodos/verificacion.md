# Verificación: US-028 – Configurar los periodos del año escolar

Rama `feature/US-028-configurar-periodos-del-año-escolar`. Los 35 escenarios de los tres specs (27 de `periodos-anio-escolar`, 5 de `datos-demostracion` y 3 de `registro-actividad`) tienen al menos una prueba: están en "Escenarios (cierre, 4.2)", junto con la DoD 1 a 9.

## Minor del revisor

### Parte 1A: `btree_gist`, `Periodo` y migración

- `test_modelos_periodo.py`: `test_la_base_crea_la_extension_btree_gist` ya no puede fallar en la base de pruebas, porque `institucion/0005` crea la extensión antes. Sirvió para la comprobación previa al modelo (tarea 1.1); en Neon, la prueba es la vista previa de Vercel (tarea 1.3).
- `test_modelos_periodo.py`: el cruce se prueba con `SET CONSTRAINTS … IMMEDIATE` y no al confirmar (pytest-django revierte la transacción). Que no estalle en el `COMMIT` lo cubren las tareas 2.2 y 2.3.
- `models.py`, `Periodo.__str__`: hace una consulta por periodo para leer `anio_escolar`. Si el inline lo muestra por fila, usar `select_related`.

### Parte 2A: servicios, registro de actividad y periodo vigente

- Tarea 2.3: su texto pide que uno de los dos guardados reciba `MENSAJE_CRUCE`. Con el bloqueo de D4 y la escritura por número, el segundo espera y edita lo del primero (4 PERIODO_EDITADO); la prueba fija eso. Sin el bloqueo, el resultado es `IntegrityError` de `uq_periodo`. El cruce que solo ve la base lo cubre `test_cruce_que_solo_ve_la_base_da_el_mensaje_sin_guardar_nada`. También son nuevos: `validar_organizacion` y el rechazo de vaciar las filas de un año que ya tiene periodos.
- `guardar_periodos` bloquea primero la institución y después el año. Desde la ficha del año, `RegistraEnPanel` bloquea primero el año, así que el orden queda al revés y puede haber un deadlock con la demo. Se resuelve en la tarea 2.6.
- `test_concurrencia_periodos.py`: `segundo.join(1)` depende del tiempo y no comprueba que el segundo hilo esté esperando el bloqueo.

### Parte 2B: ficha del año y de la institución en el panel

- `AnioEscolarAdmin`: `institucion` sigue editable en la ficha. Resuelto en la tarea 3.0: de solo lectura cuando el año tiene periodos.
- `test_admin_periodos.py`: falta la prueba de un POST que cierra el año y cambia periodos a la vez (se rechaza con "El año escolar está cerrado…" y no guarda nada).
- `FormsetPeriodos.poner_error`: un `error_dict` del guardado con claves que no son números de fila daría 500; hoy `guardar_periodos` no lo produce.

### Parte 3: demo y pantalla

- `AnioEscolarAdmin.get_readonly_fields`: `obj.periodos.exists()` suma una consulta por cada vista de la ficha. Inocuo.

## Revisión adversarial (A2, Codex)

- Corregido: con periodos guardados, el año calendario de la ficha era editable. Si solo cambiaba el año, el formset no cambiaba y nada revalidaba las fechas, así que los periodos quedaban fuera del año nuevo y `periodo_vigente` dejaba de encontrarlos. Ahora `anio` es de solo lectura cuando hay periodos, como `institucion`.

## Escenarios (cierre, 4.2)

Pruebas en `src/backend/institucion/tests/` salvo las de `actividad`. Abreviaturas: `mod` = `test_modelos_periodo.py`, `srv` = `test_servicios_periodos.py`, `conc` = `test_concurrencia_periodos.py`, `vig` = `test_periodo_vigente.py`, `adm` = `test_admin_periodos.py`, `e2e` = `test_periodos_e2e.py`, `demo` = `test_demo.py`, `cmd` = `test_comandos_demo.py`, `amod` = `actividad/tests/test_modelos.py`, `cat` = `actividad/tests/test_catalogo.py`.

| Spec | Escenario | Prueba |
| --- | --- | --- |
| periodos-anio-escolar | Camino ideal | `adm::test_guardar_las_4_filas_crea_los_periodos_y_lo_registra`, `e2e::test_el_administrador_llena_los_cuatro_bimestres_y_guarda`, `vig::test_dentro_y_en_los_bordes_es_el_bimestre_1` |
| periodos-anio-escolar | Trimestres | `adm::test_la_ficha_muestra_una_fila_por_periodo_numerada_y_sin_borrar` (BIMESTRE 4 y TRIMESTRE 3), `srv::test_trimestres_son_tres_filas` |
| periodos-anio-escolar | Fin antes del inicio | `srv::test_fin_no_posterior_al_inicio_en_su_fila`, `adm::test_cada_regla_muestra_su_mensaje_en_la_ficha_y_no_guarda_nada`; en la base, `mod::test_fin_no_posterior_al_inicio_lo_rechaza_la_base` |
| periodos-anio-escolar | Número repetido o fuera de rango en la base | `mod::test_numero_repetido_en_el_anio_lo_rechaza_la_base`, `test_numero_fuera_de_rango_lo_rechaza_la_base` |
| periodos-anio-escolar | Faltan filas | `srv::test_filas_incompletas_dicen_cuantas_completar`, `adm::test_cada_regla_muestra_su_mensaje_en_la_ficha_y_no_guarda_nada` |
| periodos-anio-escolar | Sin borrar | `adm::test_la_ficha_muestra_una_fila_por_periodo_numerada_y_sin_borrar`, `test_un_post_con_delete_no_borra_periodos` |
| periodos-anio-escolar | Guardar el año sin tocar los periodos | `adm::test_editar_el_estado_con_las_filas_vacias_guarda_el_anio_sin_periodos`, `test_cerrar_un_anio_con_periodos_sin_tocarlos_lo_cierra`, `srv::test_guardar_todas_vacias_no_crea_nada` |
| periodos-anio-escolar | Organización vacía | `adm::test_sin_organizacion_la_ficha_avisa_con_el_enlace_y_sin_filas`, `srv::test_organizacion_vacia_se_rechaza` |
| periodos-anio-escolar | Organización fija con periodos | `adm::test_con_periodos_la_organizacion_es_de_solo_lectura`, `test_con_periodos_un_post_que_cambia_la_organizacion_no_la_cambia`, `test_el_formulario_de_la_institucion_rechaza_cambiar_la_organizacion_con_periodos`; `srv::test_cambiar_la_organizacion_con_periodos_guardados_se_rechaza`, `test_vaciar_la_organizacion_con_periodos_guardados_se_rechaza` |
| periodos-anio-escolar | Caso de error | `srv::test_cruce_en_la_fila_de_numero_mayor`, `test_cruce_entre_periodos_no_vecinos`, `adm::test_cada_regla_muestra_su_mensaje_en_la_ficha_y_no_guarda_nada`, `e2e::test_un_cruce_muestra_el_mensaje_junto_a_la_fila` |
| periodos-anio-escolar | Mismo día de borde | `srv::test_cruce_en_la_fila_de_numero_mayor[mismo-dia]`; en la base, `mod::test_cruce_en_el_anio_lo_rechaza_la_base[mismo-dia]` |
| periodos-anio-escolar | Correr dos periodos a la vez | `srv::test_correr_el_fin_del_1_y_el_inicio_del_2_a_la_vez_se_guarda`; en la base, `mod::test_correr_dos_periodos_en_dos_updates_no_falla` (cruce diferido) |
| periodos-anio-escolar | Cruce que llega a la base | `srv::test_cruce_que_solo_ve_la_base_da_el_mensaje_sin_guardar_nada`, `adm::test_un_cruce_que_llega_al_guardado_muestra_el_mensaje_sin_500`; dos guardados reales a la vez, `conc::test_dos_guardados_a_la_vez_van_en_fila_sin_integrity_error` y `test_la_ficha_del_anio_y_un_guardado_a_la_vez_van_en_fila_sin_deadlock` (con el bloqueo de D4, el segundo espera; ver Minor de la Parte 2A) |
| periodos-anio-escolar | Cruce fuera del panel | `mod::test_cruce_en_el_anio_lo_rechaza_la_base` |
| periodos-anio-escolar | Fuera del año | `srv::test_fuera_del_anio_en_su_fila`, `test_inicio_en_el_anio_anterior_esta_fuera` |
| periodos-anio-escolar | Fuera de orden | `srv::test_fuera_de_orden_en_la_fila_siguiente`; cruce y desorden a la vez, `test_cruce_y_desorden_a_la_vez_da_el_mensaje_del_cruce` |
| periodos-anio-escolar | Vacaciones entre bimestres | `srv::test_hueco_de_vacaciones_es_valido` |
| periodos-anio-escolar | Flujo alternativo válido | `srv::test_editar_dos_periodos_deja_dos_periodo_editado_sin_cambiar_sus_id`, `adm::test_editar_dos_periodos_los_corrige_sin_cambiar_su_id`. Las notas llegan con US-020: hoy se prueba que el periodo conserva su id, que es lo que mantiene cada nota en su periodo |
| periodos-anio-escolar | Año cerrado | `adm::test_anio_cerrado_muestra_los_periodos_de_solo_lectura`, `test_anio_cerrado_un_post_que_cambia_las_fechas_no_las_cambia`, `test_anio_cerrado_sin_periodos_no_tiene_filas_para_llenar`, `srv::test_anio_cerrado_se_rechaza` |
| periodos-anio-escolar | Dentro y en el borde | `vig::test_dentro_y_en_los_bordes_es_el_bimestre_1` |
| periodos-anio-escolar | En un hueco | `vig::test_en_un_hueco_no_hay_periodo_vigente` |
| periodos-anio-escolar | Sin periodos | `vig::test_sin_periodos_no_hay_periodo_vigente` |
| periodos-anio-escolar | Hoy en Lima | `vig::test_sin_fecha_es_hoy_en_lima` |
| periodos-anio-escolar | Configurados | `srv::test_guardar_crea_los_periodos_y_deja_periodos_configurados`, `adm::test_guardar_las_4_filas_crea_los_periodos_y_lo_registra` |
| periodos-anio-escolar | Editado | `srv::test_editar_dos_periodos_deja_dos_periodo_editado_sin_cambiar_sus_id`; sin cambios no deja entradas, `test_guardar_sin_cambios_no_deja_entradas` |
| periodos-anio-escolar | Rechazado | `srv::test_rechazado_por_cruce_no_deja_entradas` |
| periodos-anio-escolar | Otro rol | `adm::test_docente_y_direccion_no_ven_la_ficha_ni_cambian_periodos` |
| datos-demostracion | Año sin periodos | `demo::test_con_bimestres_y_sin_periodos_crea_los_cuatro_de_ejemplo`, `cmd::test_cargar_demo_nombra_los_bimestres_en_el_resumen` |
| datos-demostracion | Año con periodos | `demo::test_con_periodos_la_carga_no_los_cambia` (con un guardado en el panel a la vez de la carga, ver "Deuda") |
| datos-demostracion | Organización vacía o en trimestres | `demo::test_sin_bimestres_no_crea_periodos_y_lo_dice`, `cmd::test_cargar_demo_sin_organizacion_dice_que_se_configuran_en_el_panel` |
| datos-demostracion | Volver a cargar sin periodos | `demo::test_volver_a_cargar_sin_periodos_crea_solo_los_periodos` |
| datos-demostracion | Quitar la demostración | `demo::test_quitar_demo_y_descartar_seccion_no_tocan_los_periodos` |
| registro-actividad | Catálogo de esta historia | `amod::test_solo_las_operaciones_de_asistencia_cuentan_para_kpi_01`; PERIODOS_CONFIGURADOS y PERIODO_EDITADO en `cat::test_la_tabla_cubre_el_catalogo_menos_las_reservadas` |
| registro-actividad | Operación fuera del catálogo | `amod::test_operacion_fuera_del_catalogo_la_rechaza_la_base` (sin cambios de US-008) |
| registro-actividad | Cada operación tiene su prueba | `cat::test_cada_escenario_es_una_prueba_que_existe`: las dos operaciones nuevas apuntan a pruebas de `srv` (`actividad/tests/escenarios.py`) |

Además: todo o nada de la carga de la demo (`demo::test_si_la_carga_falla_despues_de_los_periodos_no_queda_ninguno`), guardar con el año leído de la base y no con una copia vieja (`srv::test_guardar_usa_el_anio_de_la_base_y_no_una_copia_vieja`), `periodo_vigente` en una sola consulta (`vig::test_hace_una_sola_consulta`) y año y `institucion` de la ficha de solo lectura con periodos (tarea 3.0 y A2).

Corrida del cierre (31/10/2026): `uv run pytest --cov`: 1339 pasan, cobertura total 98,30 %. `test_periodos_e2e.py` en Chromium: 16 pasan.

## DoD 1 a 9

| N.° | Criterio | Estado |
| --- | --- | --- |
| 1 | Cobertura ≥ 80 % | Local: 98,30 % total; `institucion/servicios.py` 98 %, `institucion/models.py` 100 %. Sonar way: pendiente del PR |
| 2 | Análisis estático sin críticas ni altas | Ruff en verde con `verificar.py`. CodeQL y SonarQube Cloud: pendiente del PR |
| 3 | Aprobación de otra integrante | Pendiente del PR |
| 4 | Vista previa de Vercel | Pendiente del PR: debe aplicar `institucion/0005` (con `btree_gist`) en Neon (tarea 4.1) |
| 5 | Escenarios en verde y e2e de la ruta ideal | Los 35 escenarios tienen prueba y pasan en local; la ruta ideal, `e2e::test_el_administrador_llena_los_cuatro_bimestres_y_guarda`. GitHub Actions: pendiente del PR |
| 6 | Reglas de negocio con pruebas propias | RN-006 (4 bimestres o 3 trimestres): `srv::test_trimestres_son_tres_filas`, `test_filas_incompletas_dicen_cuantas_completar`. RN-023 (no se borra): `adm::test_un_post_con_delete_no_borra_periodos`. RN-002 queda como base para US-020 |
| 7 | Accesibilidad sin errores críticos | `e2e::test_la_ficha_con_filas_vacias_pasa_axe`, `test_la_ficha_con_el_error_pasa_axe`, `test_la_ficha_de_un_anio_cerrado_pasa_axe` (claro y oscuro, 360 y 1280 px) y `test_a_360_px_la_ficha_no_se_desplaza_en_horizontal` |
| 8 | Sin datos reales | Fechas y bimestres de ejemplo ficticios en pruebas y demo. Revisión del PR: pendiente |
| 9 | Documentación | Specs del cambio en OpenSpec y docstrings. No hay rutas nuevas (la ficha es del panel de Django), así que el catálogo de rutas de `docs/03` no cambia. Ningún requisito cambió: el documento 06 sigue igual |

## Deuda

- `cargar_demo` (`demo.py`): `planear_demo` decide `CREAR_PERIODOS` bajo el bloqueo advisory, que solo hace esperar a otra carga o retiro de la demo, no al panel. Si un administrador guarda periodos entre esa decisión y la llamada a `guardar_periodos`, la carga actualiza esos periodos con las fechas de ejemplo, contra el spec `datos-demostracion` ("solo si el año aún no tiene periodos"). Arreglo: antes de crear los periodos, bloquear la institución y el año (el orden de D4), volver a revisar si hay periodos y, si los hay, no tocarlos y mostrar `YA_TIENE_PERIODOS` en el resumen. Se deja porque solo pasa si alguien guarda periodos en el panel justo mientras corre la carga desde la consola.
