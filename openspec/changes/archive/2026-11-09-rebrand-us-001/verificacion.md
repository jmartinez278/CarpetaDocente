# Verificación: rebrand del Ingreso (US-001)

Rama `feature/rebrand` (paso 2 del PLAN del rebrand). Los 4 escenarios de la spec delta de `pantallas-de-inicio` tienen prueba, y los escenarios de `pantallas-de-inicio` y `cierre-sesion` que tocan el inicio de sesión se vuelven a correr sobre el marco nuevo. `ingresar.js`, la vista, el formulario, servicios, modelos y rutas no cambian.

Pruebas en `src/backend/cuentas/tests/`. Abreviaturas: `pan` = `test_pantallas.py`, `ing` = `test_ingresar.py`, `ie2e` = `test_ingresar_e2e.py`, `a11y` = `test_accesibilidad_e2e.py`, `rend` = `test_rendimiento_e2e.py`, `rb` = `test_componentes_rb.py`, `ina` = `test_inactividad.py`, `sal` = `test_salir.py`, `ce2e` = `test_cerrar_sesion_e2e.py`.

## Minor para la descripción del PR

- Revisor de la parte B (alto riesgo): sin Critical ni Important.
- Auditoría de Emil (3.1, `insumos/rebrand-ingreso/auditoria-emil.md`): sin hallazgos de animación; B-01 (un error de campo sin espacios ensanchaba la página a 688 px) aplicado en `rb/campo.html` vía `.field-error span`, aunque en el ingreso no se provoca: sus errores son fijos. Sirve a Estudiantes y Notas.
- DESIGN.md (línea 141) aún dice que el error del ingreso lleva `role="alert"`; D2 lo quitó para que no se lea dos veces. Corregir el texto de DESIGN.md con aprobación del equipo (deuda, decisión de Marco del 9-11-2026).

## Revisión A2 (Codex, 3.2)

Veredicto `approve`, sin hallazgos materiales, sobre `main...HEAD` (toda la rama del rebrand). No vio el arreglo B-01 (sin commit en ese momento) ni pudo correr las pruebas (su sandbox no abrió Python); se corrieron aquí: suite completa con cobertura (2110) y todas las e2e (535) en verde. Sin correcciones a la A2.

Al correr todas las e2e, `institucion/tests/test_estudiantes_e2e.py::test_sesion_vencida_al_importar_lleva_la_pagina_a_ingresar` fallaba: buscaba el aviso de inactividad del ingreso con la clase vieja `.mensaje--aviso` (2.2 solo pasó las pruebas de `cuentas`). La pantalla mostraba el aviso; el selector pasa a `.message--aviso`. Las demás clases viejas de `institucion/tests/` son de la pantalla Estudiantes, aún sin rebrand.

## Escenarios (cierre, 3.3)

### Spec delta (`pantallas-de-inicio`, requisitos modificados)

| Escenario | Prueba |
|---|---|
| Pantalla de inicio de sesión · Contenido de la pantalla | `pan::test_los_textos_aparecen_en_el_orden_del_spec`, `test_el_nombre_de_la_ie_es_el_unico_h1`, `test_sin_escudo_ni_menu_ni_enlaces`, `test_el_espacio_del_escudo_va_vacio_y_oculto_antes_del_nombre`, `test_el_formulario_va_en_la_ficha_con_sus_ganchos`, `test_ingresar_es_el_boton_principal_con_su_gancho`, `test_el_pie_lleva_solo_la_marca`, `test_carga_solo_la_hoja_del_rebrand_y_precarga_besley_e_instrument_sans`, `test_la_base_del_rebrand_no_precarga_besley_sin_el_bloque_precargas`; `ie2e::test_de_la_raiz_al_inicio_de_sesion_y_a_la_portada` |
| Pantalla de inicio de sesión · Pista del campo Usuario | `ing::test_la_pista_va_bajo_el_campo_usuario_y_lo_describe`, `test_con_un_error_el_campo_describe_la_pista_y_el_error`, `test_el_campo_contrasena_no_tiene_pista` |
| Pantalla de inicio de sesión · Mensaje de error sobre el formulario | `pan::test_el_error_va_sobre_la_ficha_con_sus_dos_lineas_y_recibe_el_foco`, `test_solo_el_error_lleva_autofocus`, `test_sin_rechazo_no_hay_mensaje`; `ie2e::test_tras_un_rechazo_el_foco_va_al_error_y_tab_lleva_a_usuario` (foco en el mensaje y fuera de toda región viva: un solo anuncio); `rb::test_mensaje_con_enfocar_trae_tabindex_y_autofocus_sin_role`, `test_mensaje_sin_enfocar_no_trae_tabindex_ni_autofocus` |
| Pantalla de inicio de sesión · Error y teclado | `ie2e::test_tras_un_rechazo_el_foco_va_al_error_y_tab_lleva_a_usuario`; `pan::test_el_error_conserva_el_usuario_y_no_la_contrasena`; `ing::test_conserva_el_usuario_pero_no_la_contrasena` |
| Accesibilidad en ambos temas · Revisión de cada pantalla | `a11y::test_sin_infracciones_graves_de_accesibilidad` (ingreso normal, con error, con campos vacíos, «Ingresando…» y con aviso; portada, dirección y «sin permiso»; claro/oscuro, 360/1280 px); `a11y::test_el_ojo_mide_44_px_dentro_del_campo` |

### Escenarios que se vuelven a correr

| Escenario | Prueba |
|---|---|
| `pantallas-de-inicio` · Mostrar la contraseña · Ver la contraseña | `ie2e::test_mostrar_contrasena_alterna_la_vista` (alterna `aria-pressed` y el tipo; al enviar vuelve a `password`); `pan::test_el_boton_mostrar_contrasena_nace_oculto_y_sin_presionar`; `rb::test_campo_con_mostrar_clave_envuelve_el_input_y_trae_el_ojo`, `test_campo_con_mostrar_clave_nunca_reescribe_la_contraseña` |
| `pantallas-de-inicio` · Mostrar la contraseña · Sin JavaScript | `ie2e::test_sin_javascript_no_hay_boton_y_el_formulario_se_envia` |
| `pantallas-de-inicio` · Estado de envío · Envío en curso | `ie2e::test_envio_en_curso_cambia_el_boton_y_deja_los_campos_de_solo_lectura`, `test_ingresando_cambia_el_fondo_a_folder_con_giro_y_campos_punteados`, `test_con_movimiento_reducido_el_giro_no_gira`, `test_enviar_con_enter_desde_contrasena_anuncia_ingresando_en_la_region_status`, `test_enviar_con_el_boton_anuncia_ingresando_en_la_region_status`, `test_con_un_campo_vacio_no_se_anuncia_nada`, `test_sin_la_region_de_estado_el_envio_sigue_bloqueando_el_doble_envio`, `test_al_restablecer_el_estado_la_region_queda_vacia`; `pan::test_el_anuncio_del_envio_es_una_region_status_vacia_oculta_y_fuera_del_formulario` |
| `pantallas-de-inicio` · Sin desplazamiento horizontal · Pantallas a 320 px | `a11y::test_el_inicio_de_sesion_no_desborda` (normal, con error y con aviso; claro/oscuro; 320 y 360 px), `test_b01_un_error_de_campo_sin_espacios_no_desborda` (320 y 360 px) |
| `pantallas-de-inicio` · Carga en conexión lenta · Primera visita con Slow 4G | `rend::test_inicio_de_sesion_con_slow_4g` (sin cambios; Instrument Sans y Besley, 2 MB o menos, «Ingresar» usable en 5 s o menos) |
| `cierre-sesion` · Aviso de cierre por inactividad · Aviso tras la inactividad | `pan::test_el_aviso_va_sobre_la_ficha_con_el_reloj_y_dos_lineas`, `test_un_envio_tras_la_inactividad_muestra_el_aviso`; `ina::test_deja_el_aviso_con_la_etiqueta_inactividad`; `ce2e::test_inactividad_muestra_el_aviso_y_atras_no_muestra_la_pantalla`; `rb::test_partes_aviso_parte_titulo_y_detalle`, `test_mensaje_con_icono_usa_ese_icono` |
| `cierre-sesion` · Aviso de cierre por inactividad · El aviso no se repite | `pan::test_el_aviso_no_se_repite_al_recargar` |
| `cierre-sesion` · Aviso de cierre por inactividad · Cierre elegido | `pan::test_sin_inactividad_no_hay_aviso`; `sal::test_post_cierra_la_sesion_y_lleva_a_ingresar_sin_aviso` |

### Componentes sin parámetros nuevos (D3)

| Comportamiento | Prueba |
|---|---|
| `rb/campo.html`, `rb/mensaje.html` y `rb/pie.html` sin los parámetros nuevos quedan como antes (Sesiones y «sin permiso») | `rb::test_campo_sin_los_parametros_nuevos_queda_como_antes`, `test_mensaje_sin_icono_conserva_el_de_hoy`, `test_pie_sin_solo_marca_trae_los_dos_textos`; e2e de `repositorio` en verde |

## DoD 1 a 9

| N.° | Criterio | Estado |
| --- | --- | --- |
| 1 | Cobertura ≥ 80 % | Local: 98,52 % total (`uv run pytest --cov`, 2110 en verde). Sonar way: pendiente del push |
| 2 | Análisis estático sin críticas ni altas | Ruff en verde con `verificar.py`. A2 de Codex: `approve`, sin hallazgos. CodeQL y SonarQube Cloud: pendiente del push |
| 3 | Aprobación de otra integrante | Pendiente del PR único del rebrand (no antes del 11-11-2026) |
| 4 | Vista previa de Vercel | Pendiente del push |
| 5 | Escenarios en verde y e2e de la ruta ideal | Los 5 escenarios de la delta y los 8 que se vuelven a correr tienen prueba; e2e de todas las apps en verde. Ruta ideal: `ie2e::test_de_la_raiz_al_inicio_de_sesion_y_a_la_portada`, `test_la_direccion_llega_a_su_inicio`. `ingresar.js` sin cambios (`git diff main --stat` no lo nombra). GitHub Actions: pendiente del push |
| 6 | Reglas de negocio con pruebas propias | Sin reglas nuevas: vista, formulario y servicios sin cambios; las de US-001 siguen en verde (`ing::test_los_cuatro_rechazos_dan_el_mismo_mensaje_en_dos_lineas`, `test_cuenta_bloqueada_rechaza_la_contrasena_correcta_con_el_mismo_mensaje`, `test_next_externo_se_ignora`) |
| 7 | Accesibilidad sin errores críticos | `a11y::test_sin_infracciones_graves_de_accesibilidad` en los cinco estados (claro/oscuro, 360/1280), ojo de 44 × 44 px, foco del error sin doble anuncio y movimiento reducido. Pantalla vista en claro/oscuro y celular/escritorio por Marco (2.6) |
| 8 | Sin datos reales | Usuarios y claves ficticios de las fixtures; Besley con licencia OFL vía `@fontsource` |
| 9 | Documentación | Spec delta, `design.md` (D1 a D6), comentarios de uso en `rb/campo.html`, `rb/mensaje.html` y `rb/pie.html`. Sin rutas nuevas: `docs/03` y README sin cambios. Deuda en `tasks.md` («Workflow follow-up») y arriba (DESIGN.md) |
