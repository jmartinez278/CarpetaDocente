# Verificación: US-004 – Restringir el acceso según el rol

Rama `feature/us-004-restringir-acceso-segun-rol`. Los 52 escenarios de los seis specs (18 de `acceso-secciones`, 14 de `registro-actividad`, 6 de `asistencia-jornada`, 6 de `competencias-periodo`, 4 de `estudiantes-seccion` y 4 de `registro-notas`) tienen al menos una prueba o una nota de por qué no aplica: están en "Escenarios (cierre, 4.2)", junto con la DoD 1 a 9.

## Minor para la descripción del PR

- Parte B: la e2e de asistencia comprueba que no se guardan pendientes nuevos de la sección con 403, pero no siembra pendientes de otro día para ver que también se borran (`olvidarPendientes`).
- Parte B: la e2e del diálogo de la portada cubre «Agregar» (POST); la carga de la lista por HTMX con 403 queda cubierta solo por las pruebas de vista (`HX-Redirect`).
- Parte B: `notas.js` borra los borradores de la sección solo en la pestaña que recibe el 403; otra pestaña abierta con la misma hoja podría volver a escribirlos al editar (solo con varias pestañas). La A2 lo confirmó (medium) y queda como deuda: propagar una señal de revocación por usuario y sección, como el cierre de sesión entre pestañas, con una e2e de dos pestañas.

## A2 (Codex, revisión adversarial)

- Corregido: un id de sección de más de 40 dígitos daba 500 sin registrar el intento (`DataError` en `entidad_id`). Ahora `registrar_intento_sin_permiso` guarda los primeros 40 caracteres y el id completo queda en la ruta; prueba `test_un_id_que_no_cabe_en_el_registro_da_403_y_una_entrada`.
- A la deuda: los borradores en otra pestaña (Minor de la Parte B, arriba).

## Escenarios (cierre, 4.2)

Pruebas en `src/backend/`. Abreviaturas: en `institucion/tests/`, `sacc` = `test_servicios_acceso.py`, `vest` = `test_vistas_estudiantes.py`, `ee2e` = `test_estudiantes_e2e.py`, `iact` = `test_actividad.py`; en `cuentas/tests/`, `sp` = `test_sin_permiso.py`, `mat` = `test_matriz_permisos.py`, `a11y` = `test_accesibilidad_e2e.py`; en `actividad/tests/`, `amod` = `test_modelos.py`, `acat` = `test_catalogo.py`, `ses` = `test_sesion.py`, `pin` = `test_panel_instrumentado.py`; en `asistencia/tests/`, `avis` = `test_vistas.py`, `aact` = `test_actividad.py`, `ae2e` = `test_asistencia_e2e.py`; en `notas/tests/`, `nvis` = `test_vistas.py`, `vh` = `test_vistas_hoja.py`, `acc` = `test_vistas_acceso.py`, `vha` = `test_vistas_hoja_acceso.py`, `ph` = `test_plantilla_hoja.py`, `he2e` = `test_hoja_e2e.py`, `ce2e` = `test_competencias_e2e.py`. `mat::test_matriz` corre 10 filas (ruta y método) × 5 perfiles.

| Spec | Escenario | Prueba |
| --- | --- | --- |
| acceso-secciones | Camino ideal | `mat::test_matriz` (perfil `propia`, `notas:hoja`), `vh::test_el_area_lleva_columnas_filas_notas_faltantes_y_su_url`, `sacc::test_acceso_devuelve_la_seccion_de_la_docente_sin_estudiante` |
| acceso-secciones | Caso de error | `vha::test_otra_docente_recibe_403_y_no_guarda`, `vest::test_otra_docente_recibe_403_sin_nombres_y_queda_el_intento`, `sacc::test_acceso_seccion_de_otra_docente_es_ajena` |
| acceso-secciones | Sección inexistente o de un año cerrado | `vest::test_una_seccion_que_no_existe_da_403_inexistente`, `test_una_seccion_del_anio_cerrado_da_403_anio_cerrado`, `test_un_id_que_no_cabe_en_el_registro_da_403_y_una_entrada` (A2); `sacc::test_acceso_seccion_inexistente_es_inexistente`, `test_acceso_seccion_propia_en_anio_cerrado_es_anio_cerrado` |
| acceso-secciones | Guardado en una sección ajena | `vest::test_otra_docente_no_puede_agregar_en_la_seccion`, `test_otra_docente_no_puede_pegar_en_la_seccion`, `test_otra_docente_no_puede_editar_ni_quitar`, `test_otra_docente_no_puede_vaciar_la_seccion`; `avis::test_otra_docente_recibe_403_y_no_guarda`; `acc::test_otra_docente_recibe_403_y_no_guarda`; `vha::test_otra_docente_recibe_403_y_no_guarda`; `mat::test_matriz` (perfil `ajena`, filas POST) |
| acceso-secciones | Estudiante de otra sección | `vest::test_un_estudiante_de_otra_seccion_da_403_estudiante` (editar y quitar, GET y POST), `avis::test_un_estudiante_de_otra_seccion_responde_403`, `sacc::test_acceso_estudiante_de_otra_seccion_es_estudiante`, `test_acceso_estudiante_inexistente_es_estudiante` |
| acceso-secciones | Periodo o área que no existen | `nvis::test_un_numero_de_periodo_que_no_existe_responde_404`, `vh::test_un_periodo_que_no_existe_da_404`, `test_un_area_que_no_es_de_la_institucion_da_404` (los tres sin entrada) |
| acceso-secciones | Página completa | `vest::test_otra_docente_recibe_403_sin_nombres_y_queda_el_intento` (403 con el mensaje en la misma dirección, sin nombres), `sp::test_sin_permiso_respuesta_403_con_la_pagina` |
| acceso-secciones | Volver a tu inicio | `sp::test_sin_permiso_la_docente_ve_el_mensaje_sin_crear_entrada` (el enlace lleva a `/docente/`); sin e2e que lo pulse: es un enlace simple a la portada, que ya tiene sus pruebas |
| acceso-secciones | Diálogo de la portada | `ee2e::test_agregar_en_una_seccion_que_ya_no_es_suya_lleva_a_sin_permiso`, `vest::test_con_htmx_la_seccion_ajena_da_403_con_hx_redirect` (ver Minor de la Parte B) |
| acceso-secciones | Guardado de la hoja de notas | `he2e::test_guardar_en_una_seccion_que_ya_no_es_suya_lleva_a_sin_permiso`; competencias y asistencia, `ce2e::test_guardar_en_una_seccion_que_ya_no_es_suya_lleva_a_sin_permiso`, `ae2e::test_marcar_en_una_seccion_que_ya_no_es_suya_lleva_a_sin_permiso` |
| acceso-secciones | La página de «sin permiso» no registra | `sp::test_sin_permiso_la_docente_ve_el_mensaje_sin_crear_entrada` |
| acceso-secciones | Otro rol en la página de «sin permiso» | `sp::test_sin_permiso_la_direccion_va_a_su_inicio`, `test_sin_permiso_sin_sesion_va_al_ingreso` |
| acceso-secciones | Intento registrado | `vha::test_otra_docente_recibe_403_y_no_guarda`, `sacc::test_acceso_registrar_intento_deja_una_entrada_con_ruta_y_motivo` |
| acceso-secciones | Cada intento cuenta | `sacc::test_acceso_cada_intento_cuenta` |
| acceso-secciones | Un intento por HTMX deja una sola entrada | `he2e::test_guardar_en_una_seccion_que_ya_no_es_suya_lleva_a_sin_permiso`, `ce2e::…_lleva_a_sin_permiso`, `ae2e::…_lleva_a_sin_permiso`, `ee2e::…_lleva_a_sin_permiso` (cada una sigue a la página y deja `["ajena"]`) |
| acceso-secciones | Motivos | `sacc::test_acceso_seccion_inexistente_es_inexistente`, `test_acceso_seccion_propia_en_anio_cerrado_es_anio_cerrado`, `test_acceso_estudiante_de_otra_seccion_es_estudiante`, `test_acceso_seccion_de_otra_docente_en_anio_cerrado_es_ajena`, `test_acceso_la_seccion_ajena_manda_sobre_el_estudiante`, `test_acceso_seccion_sin_docente_es_ajena`, `test_acceso_lo_decide_en_una_consulta_por_objeto` |
| acceso-secciones | Otros roles sin registro | `mat::test_matriz` (perfiles `direccion`, `administrador` y `anonimo`: 302 y ninguna entrada), `vest::test_la_direccion_llega_a_su_pantalla` |
| acceso-secciones | Matriz | `mat::test_matriz`, `test_la_matriz_cubre_las_rutas_de_seccion` (pegar, quitar, vaciar y restantes, fuera de la tabla, con su prueba en cada app); se vio fallar quitando el registro del mixin en local (2.4) |
| asistencia-jornada | Sección de otra docente | `avis::test_otra_docente_recibe_403_y_no_guarda` (abrir, marcar y restantes) |
| asistencia-jornada | Sección de un año cerrado | `avis::test_una_seccion_del_anio_cerrado_da_403_y_no_guarda` |
| asistencia-jornada | Otro rol | `avis::test_la_direccion_llega_a_su_pantalla` |
| asistencia-jornada | Estudiante de otra sección | `avis::test_un_estudiante_de_otra_seccion_responde_403` |
| asistencia-jornada | Estudiante de la sección que ya no está activo | `avis::test_un_estudiante_retirado_responde_404` (sin entrada) |
| asistencia-jornada | Restantes con un id ajeno | `avis::test_restantes_con_un_id_ajeno_responde_404_sin_guardar` (sin entrada, D7) |
| competencias-periodo | Sección de otra docente | `acc::test_otra_docente_recibe_403_y_no_guarda`, `ce2e::test_guardar_en_una_seccion_que_ya_no_es_suya_lleva_a_sin_permiso` |
| competencias-periodo | Sección de un año cerrado | `acc::test_la_seccion_de_un_anio_cerrado_da_403_y_no_guarda` |
| competencias-periodo | Otro rol | Sin cambios: `acc::test_la_direccion_llega_a_su_pantalla` |
| competencias-periodo | Sin sesión | Sin cambios: `acc::test_sin_sesion_va_a_ingresar_con_next`, `test_sin_sesion_un_guardado_con_htmx_recibe_hx_redirect` |
| competencias-periodo | Portada sin cambios | Sin cambios: `acc::test_la_portada_lleva_a_la_hoja_y_no_a_las_competencias` |
| competencias-periodo | Desde la hoja de notas | Sin cambios: `ph::test_el_boton_competencias_lleva_el_periodo_y_el_area`, `he2e::test_competencias_vuelve_a_las_notas_del_periodo_y_el_area` |
| estudiantes-seccion | Sección de otra docente | `vest::test_otra_docente_recibe_403_sin_nombres_y_queda_el_intento`, `test_otra_docente_no_puede_editar_ni_quitar` |
| estudiantes-seccion | Sección de un año cerrado | `vest::test_una_seccion_del_anio_cerrado_da_403_anio_cerrado` |
| estudiantes-seccion | Estudiante de otra sección | `vest::test_un_estudiante_de_otra_seccion_da_403_estudiante`; el quitado entre la carga y el guardado sigue en 404, `test_editar_un_estudiante_quitado_mientras_se_enviaba_da_404_sin_recrearlo` |
| estudiantes-seccion | Otro rol | `vest::test_la_direccion_llega_a_su_pantalla` |
| registro-notas | Sección de otra docente | `vha::test_otra_docente_recibe_403_y_no_guarda`, `he2e::test_guardar_en_una_seccion_que_ya_no_es_suya_lleva_a_sin_permiso` |
| registro-notas | Sección de un año cerrado | `vha::test_la_seccion_de_un_anio_cerrado_da_403_y_no_guarda` |
| registro-notas | Otro rol | Sin cambios: `vha::test_la_direccion_llega_a_su_pantalla` |
| registro-notas | Sin sesión | Sin cambios: `vha::test_sin_sesion_va_a_ingresar_con_next`, `test_sin_sesion_un_guardado_con_htmx_recibe_hx_redirect` |
| registro-actividad | Catálogo de esta historia | `amod::test_el_catalogo_de_esta_historia`, `test_solo_las_operaciones_de_asistencia_y_notas_guardadas_cuentan_para_kpi_01`, `test_ninguna_operacion_esta_reservada` |
| registro-actividad | Operación fuera del catálogo | Sin cambios: `amod::test_operacion_fuera_del_catalogo_la_rechaza_la_base` |
| registro-actividad | Cada operación tiene su prueba | `acat::test_la_tabla_cubre_el_catalogo_menos_las_reservadas` (ya sin reservadas), `test_cada_escenario_es_una_prueba_que_existe`: INTENTO_SIN_PERMISO apunta a `sacc::test_acceso_registrar_intento_deja_una_entrada_con_ruta_y_motivo` (`actividad/tests/escenarios.py`) |
| registro-actividad | Una lectura no deja entrada | Sin cambios: `ses::test_abrir_la_portada_no_deja_entrada`, `iact::test_abrir_la_lista_de_estudiantes_no_deja_entrada`, `aact::test_abrir_la_asistencia_de_hoy_no_deja_entrada`; además, `mat::test_matriz` (perfil `propia`, filas GET, ninguna entrada) |
| registro-actividad | Un intento sin permiso deja entrada | `vest::test_otra_docente_recibe_403_sin_nombres_y_queda_el_intento` |
| registro-actividad | Inicio y cierre de sesión | Sin cambios: `ses::test_ingreso_correcto_deja_inicio_sesion`, `test_cerrar_sesion_con_el_boton_deja_cierre_sesion_con_motivo_boton` |
| registro-actividad | Cierre por inactividad | Sin cambios: `ses::test_cierre_por_inactividad_deja_motivo_inactividad` |
| registro-actividad | Operación del panel | Sin cambios: `pin::test_alta_de_cuenta_deja_cuenta_creada`, `test_editar_cuenta_deja_los_nombres_de_los_campos_sin_valores` y las demás de US-008 |
| registro-actividad | Desactivar una cuenta | Sin cambios: `pin::test_desmarcar_activo_deja_cuenta_desactivada` |
| registro-actividad | Asignar y liberar una sección | Sin cambios: `pin::test_elegir_docente_deja_seccion_asignada`, `test_quitar_docente_deja_seccion_liberada` |
| registro-actividad | Ningún camino del panel escribe sin registrar | Sin cambios: `pin::test_cada_model_admin_que_escribe_usa_la_mezcla`, `test_borrar_una_institucion_responde_403` |
| registro-actividad | Estudiante editado | Sin cambios: `iact::test_editar_deja_estudiante_editado_sin_los_nombres` |
| registro-actividad | Justificación | Sin cambios: `aact::test_nota_cambiada_lo_dice_sin_el_texto` |
| registro-actividad | Intento sin permiso (detalle) | `vest::test_la_consulta_no_va_en_la_ruta_registrada`, `vha::test_la_consulta_no_va_en_la_ruta_registrada`, `sacc::test_acceso_intento_con_una_clave_de_mas_lanza_value_error` |

## DoD 1 a 9

| N.° | Criterio | Estado |
| --- | --- | --- |
| 1 | Cobertura ≥ 80 % | Local: 98,49 % total (`verificar.py`, sin e2e). Sonar way: pendiente del PR |
| 2 | Análisis estático sin críticas ni altas | Ruff en verde con `verificar.py`. CodeQL y SonarQube Cloud: pendiente del PR |
| 3 | Aprobación de otra integrante | Pendiente del PR |
| 4 | Vista previa de Vercel | Sin migraciones en esta historia. Pendiente del commit de cierre en el PR |
| 5 | Escenarios en verde y e2e de la ruta ideal | Los 52 escenarios tienen prueba o nota y pasan en local; la ruta ideal de la historia (sección ajena → «sin permiso» con una entrada), `he2e::test_guardar_en_una_seccion_que_ya_no_es_suya_lleva_a_sin_permiso`. GitHub Actions: pendiente del PR |
| 6 | Reglas de negocio con pruebas propias | RNF-013 (matriz de permisos): `mat::test_matriz`, `test_la_matriz_cubre_las_rutas_de_seccion`. RNF-016 (registro de operaciones sin permiso): `sacc::test_acceso_registrar_intento_deja_una_entrada_con_ruta_y_motivo`, `test_acceso_cada_intento_cuenta`. RN-015 (registro sin datos sensibles): `vest::test_la_consulta_no_va_en_la_ruta_registrada`, `sacc::test_acceso_intento_con_una_clave_de_mas_lanza_value_error` |
| 7 | Accesibilidad sin errores críticos | `a11y::test_sin_infracciones_graves_de_accesibilidad` (vista `sin-permiso`, claro y oscuro, 360 y 1280 px), `test_sin_permiso_no_desborda_y_su_boton_es_tactil` (320 y 360 px, botón de 44 px) |
| 8 | Sin datos reales | Secciones, estudiantes y docentes ficticios en las pruebas; el registro solo guarda ids, la ruta sin consulta y el motivo; la página de «sin permiso» no muestra datos de la sección pedida (`vest::test_otra_docente_recibe_403_sin_nombres_y_queda_el_intento`). Revisión del PR: pendiente |
| 9 | Documentación | Specs del cambio en OpenSpec y docstrings de `institucion/views.py`, `asistencia/views.py`, `notas/views.py` y `cuentas/acceso.py`. Catálogo de rutas de `docs/03`: fila de `/docente/sin-permiso/` y columna «Acceso» con 403 y registro (3.2). Ningún requisito cambió; las contradicciones con los documentos congelados y la deuda están en `tasks.md` ("Contradicciones" y "Workflow follow-up") |
