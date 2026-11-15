# Verificación: US-010, US-014 y EN-03 – Enviar una sesión a la dirección

Rama `feature/us-010-014-en-03-enviar-sesion`. Los 63 escenarios de los cuatro specs (39 de `envio-sesiones`, 11 de `almacenamiento-archivos`, 7 de `indicadores-adopcion` y 6 de `registro-actividad`) tienen al menos una prueba o una nota de por qué no aplica: están en "Escenarios (cierre, 5.2)", junto con la DoD 1 a 9.

## Minor para la descripción del PR

- Parte A: fuera de Vercel, R2 a medias (alguna variable `AWS_*` sí y otra no) no arranca, para que boto3 no tome credenciales de `~/.aws` sin avisar (ajuste a D2). Quien tenga una `AWS_*` exportada por otro proyecto debe quitarla (el mensaje nombra la variable).
- Parte A: Django 5.2 no escribe `ON DELETE` en el DDL; las FK de `sesion` quedan `NO ACTION` diferidas y PROTECT lo aplica el ORM (cuatro pruebas de `ProtectedError`). La verificación de 1.2 («las FK con su `ON DELETE`») no se cumple tal como está escrita.
- Parte B: si falla el borrado del archivo tras un error de la base, el log no nombra la clave (`sesiones/<UUID>`) del objeto que queda en R2 para borrarlo a mano.
- Parte B: ninguna prueba cubre el reintento con el mismo `id` sin archivo o con otros datos (D5 devuelve la sesión previa antes de validar).
- Parte B: un POST a mano con un carácter NUL en `titulo` o `proposito` da 500 en PostgreSQL y no un error del campo; desde la pantalla no se provoca.
- Parte C: «Falla el almacenamiento» se prueba en el servicio (`test_servicios_enviar.py`), no en la vista; ahí sale como 500, que D7 trata como «Se cortó la conexión».
- Parte C: «Otro rol» prueba el GET sin `HX-Request`; el GET con `HX-Request` lo cubre `RolRequeridoMixin`, sin prueba propia en Sesiones.
- Parte C: `EnviarSesionView` lee `error.message_dict`; un `ValidationError` sin campo desde el servicio daría 500 y no 400 (hoy el servicio siempre arma un dict).
- Parte D: en `test_validar_archivo.py`, los casos «comentario-dentro», «comentario-antes-y-vba» y «tipo-docx-en-otro-lugar» llevan además un `Override` .docm; los rechaza la regla `macroEnabled` y no aíslan que un comentario o un `Default` no cuentan. Falta un caso con el tipo .docx solo en un comentario o un `Default`, sin `Override` ni .docm.
- Parte D: «dos-override» mezcla .docx y .docm; también lo rechaza `macroEnabled`. Para aislar la regla del `Override` único harían falta dos `Override` idénticos con el tipo .docx.
- Parte D: si el almacén guarda con otro nombre (`guardado != clave`), el `except` borra también `clave`, que en ese caso sería de otro objeto. Solo pasaría si se repite un token de 64 bits.

## Revisión A2 (Codex) y su corrección (Parte D)

| Hallazgo | Corrección | Prueba |
|---|---|---|
| D4/D5: la clave `sesiones/<UUID>.<ext>` se repetía entre intentos; un intento que fallaba al confirmar podía borrar, tarde, el archivo del reintento que ya confirmó | Clave por intento `sesiones/<UUID>-<token>.<ext>`, generada antes de escribir (D4, spec «Clave del archivo») | `test_el_intento_que_falla_no_borra_el_archivo_del_reintento_que_gano`, `test_cada_intento_tiene_su_propia_clave` |
| D4: la clave solo se conocía después de `save`; un `save` que escribe y luego lanza dejaba el archivo | El `except` borra siempre la clave del intento (y el nombre devuelto, si fue otro) | `test_el_almacen_escribe_y_luego_falla_no_deja_el_archivo` |
| D6: `_es_docx` buscaba el tipo .docx en los bytes; un .docm con esa cadena en un comentario XML pasaba | `[Content_Types].xml` (64 KB como máximo) leído con ElementTree sin `DOCTYPE`; un solo `Override` de `/word/document.xml` con el tipo exacto; rechazo de `macroEnabled` y de `word/vbaProject.bin` | `test_un_docm_con_el_tipo_docx_escondido_se_rechaza` y vecinas en `test_validar_archivo.py` |

- Deuda: la carrera del hallazgo 1 se prueba en un solo hilo, con `InMemoryStorage` que sobrescribe como R2. Falta una prueba de concurrencia con PostgreSQL y R2 reales (dos envíos con el mismo `id`, uno falla al confirmar).
- `# noqa: S314` en `_declara_docx`: los ataques de XML conocidos (billion laughs, blowup cuadrático, XXE) necesitan un DTD; el lector corta en `<!DOCTYPE>` y lee como máximo 64 KB. No se agrega `defusedxml`.

## Medición D3 (tarea 3.3)

Vista previa de `968e27c` (`dpl_8xoetvbC8WFnQ4CVf5ftkuEWJkuY`), región `iad1`. Cuenta ficticia `demounoa`, cargada con `cargar_demo --institucion 2` en la rama de Neon de la vista previa. Subida con `curl --limit-rate 84375` (675 kbit/s, la subida de Slow 4G), sin la latencia del perfil.

- Build: migraciones `actividad.0005` y `repositorio.0001` aplicadas en Neon; Django 5.2.18 arranca (`GET /ingresar/` 200).
- Paquete: función `django` de 39,02 MB (`vercel inspect`; el log del build no lo muestra).

| Intento | Archivo | Tiempo | Respuesta | Sesión | Objeto en R2 |
|---|---|---|---|---|---|
| 1 (2026-11-04) | PDF de 4 194 304 bytes | 50,7 s (subida completa, 4 195 090 bytes) | 500: `PutObject` → `Unauthorized` de R2 | No (reenvío del mismo `id` → 400) | No |
| 2 (2026-11-04) | PDF de 4 194 304 bytes | 54,0 s (subida completa, 4 195 090 bytes) | 201: «Sesión enviada a la dirección» | Sí (reenvío del mismo `id` → 201) | Sí: `sesiones/<id>.pdf`, 4 194 304 bytes, `application/pdf` |

- Intento 1: la función no cortó por tiempo ni por tamaño; recibió el cuerpo entero y llegó a `storage.save`. R2 rechazó la escritura porque en Vercel (Preview) estaban otras claves; un diagnóstico local con el token del bucket de preview leyó y escribió bien. Todo o nada se cumplió: sin fila, sin entrada y sin archivo.
- Intento 2: claves de Preview reemplazadas y redeploy de `968e27c` (`dpl_DtHr3wnrVP1mfWPni2NdXjB3Fr6Y`, función de 39,02 MB, sin migraciones pendientes). La función no cortó.
- «Archivo no público»: un GET sin firma al objeto en el endpoint S3 de R2 responde 400; el token del bucket de preview no puede leer `carpetadocente-produccion` (403). En el panel de Cloudflare, «Public Development URL» (`r2.dev`) del bucket está desactivado.
- Demo, sesión y objeto de la medición quedan en la vista previa; se limpian con `quitar_demo` (deuda del bloque 3).

## Envío de punta a punta con la clave nueva (tarea 5.1)

Vista previa de `b26ee1c` (`carpeta-docente-i37f225ou`), 2026-11-04: el build no tuvo migraciones pendientes. Desde el navegador, con la cuenta demo `demounoa`, se enviaron un PDF y un .docx. En el bucket `carpetadocente-preview`, prefijo `sesiones/`:

| Objeto | Tipo | Tamaño |
|---|---|---|
| `29c2f5b3-5969-4248-a065-d2c2c3335681-8e0b9e7e1b6c44f0.pdf` | `application/pdf` | 905,38 kB |
| `2d48c13f-0adb-4d4e-8204-acf0d5d63ecd-e33e28789c1f007b.docx` | `application/vnd.openxmlformats-…` | 124,67 kB |
| `f0a5779a-ffb4-4fb5-a62b-32f5ae1cffb6.pdf` | `application/pdf` | 4,19 MB (medición D3, clave anterior a la corrección A2) |

- Los dos envíos nuevos tienen la clave por intento (`<UUID>-<16 hex>`) y el .docx, guardado desde Word, pasó la validación con ElementTree.
- El bucket sigue con «Public Access: Disabled».

## Escenarios (cierre, 5.2)

Pruebas en `src/backend/`. Abreviaturas: en `repositorio/tests/`, `srv` = `test_servicios_enviar.py`, `va` = `test_validar_archivo.py`, `vis` = `test_vistas.py`, `pl` = `test_plantillas.py`, `e2e` = `test_sesiones_e2e.py`, `alm` = `test_almacenamiento.py`, `mod` = `test_modelos.py`, `con` = `test_concurrencia.py`; `set` = `config/tests/test_settings.py`; en `actividad/tests/`, `ind` = `test_indicadores.py`, `acat` = `test_catalogo.py`, `amod` = `test_modelos.py`; `dim` = `cuentas/tests/test_dimensiones.py`.

| Spec | Escenario | Prueba |
| --- | --- | --- |
| envio-sesiones | Primera visita | `vis::test_primera_visita_cabecera_boton_y_estado_vacio_sin_lista`; `pl::test_la_cabecera_tiene_el_titulo_las_franjas_de_sesiones_y_el_boton`, `test_el_estado_vacio_y_la_region_del_resultado` |
| envio-sesiones | Portada sin cambio | `dim::test_las_tres_dimensiones_en_orden_con_sus_textos`, `test_toda_dimension_disponible_resuelve_su_pantalla` (la tarjeta Sesiones sigue en «Próximamente») |
| envio-sesiones | Docente sin sección | `vis::test_la_docente_sin_seccion_abre_sesiones_y_envia`, `srv::test_docente_sin_seccion_tambien_envia` |
| envio-sesiones | Otro rol | `vis::test_otro_rol_va_a_su_inicio_sin_guardar_ni_registrar` (dirección y Administrador, GET y POST) |
| envio-sesiones | Sin sesión | `vis::test_sin_sesion_va_a_ingresar_con_next`, `test_sin_sesion_el_envio_del_popup_recibe_hx_redirect`, `test_con_la_sesion_vencida_el_envio_recibe_hx_redirect` |
| envio-sesiones | Abrir el popup | `e2e::test_abrir_el_popup_enfoca_su_titulo_y_deja_la_pantalla_inerte`; `pl::test_el_popup_tiene_su_titulo_y_su_descripcion` |
| envio-sesiones | Tocar afuera | `e2e::test_tocar_afuera_no_cierra_el_popup` |
| envio-sesiones | Cancelar | `e2e::test_cancelar_cierra_sin_guardar_y_al_abrir_otra_vez_esta_vacio` |
| envio-sesiones | Orden de los botones | `e2e::test_orden_de_los_botones` (360 y 1280 px); `pl::test_el_pie_tiene_el_avance_y_los_botones_en_su_orden` |
| envio-sesiones | Atrás en el formulario | `e2e::test_atras_en_el_formulario_lo_cierra_y_sigue_en_sesiones` |
| envio-sesiones | Atrás en los términos | `e2e::test_atras_en_los_terminos_cierra_solo_los_terminos` |
| envio-sesiones | Atrás mientras sube | `e2e::test_atras_mientras_sube_no_cierra_y_la_subida_sigue` |
| envio-sesiones | Áreas de la institución | `srv::test_las_areas_son_las_que_trabaja_la_institucion_en_orden_siagie`, `vis::test_el_contexto_trae_las_areas_que_trabaja_la_institucion`, `pl::test_las_areas_son_las_de_la_institucion_con_una_opcion_vacia`, `e2e::test_las_areas_son_las_que_trabaja_la_institucion_en_orden_siagie` |
| envio-sesiones | Archivo elegido | `e2e::test_archivo_elegido_muestra_nombre_tipo_tamano_y_cambiar`, `test_un_docx_se_reconoce_como_word` |
| envio-sesiones | Una sección | `srv::test_con_una_seccion_el_grado_viene_con_el_de_ella`, `test_una_seccion_de_un_anio_cerrado_no_cuenta`; `vis::test_el_contexto_trae_el_grado_de_su_unica_seccion`; `pl::test_con_una_seccion_el_grado_viene_elegido_con_su_ayuda`; `e2e::test_el_grado_viene_con_el_de_su_seccion` |
| envio-sesiones | Varias secciones o ninguna | `srv::test_con_dos_secciones_el_grado_viene_sin_elegir`, `test_sin_seccion_el_grado_viene_sin_elegir`; `vis::test_sin_seccion_el_contexto_no_trae_grado`; `pl::test_con_varias_secciones_el_grado_viene_sin_elegir`, `test_sin_seccion_el_grado_viene_sin_elegir` |
| envio-sesiones | Tipo no permitido | `va::test_un_archivo_que_no_es_pdf_ni_docx_se_rechaza` (12 casos), `test_un_docm_con_el_tipo_docx_escondido_se_rechaza` y vecinas (A2); `e2e::test_un_archivo_que_no_es_pdf_aunque_se_llame_asi_se_rechaza` |
| envio-sesiones | Archivo de más de 4 MB | `va::test_un_byte_mas_de_4_mb_se_rechaza`, `e2e::test_un_archivo_de_mas_de_4_mb_se_rechaza` |
| envio-sesiones | Justo 4 MB | `va::test_justo_4_mb_pasa`, `srv::test_justo_4_mb_se_guarda`, `mod::test_justo_4_mb_se_guarda` |
| envio-sesiones | Envío que salta el navegador | `srv::test_archivo_que_salta_el_navegador_no_se_guarda`, `vis::test_un_archivo_disfrazado_responde_400_con_el_mensaje_del_campo`, `va::test_el_tipo_que_dice_el_navegador_no_cuenta` |
| envio-sesiones | Área y título vacíos | `srv::test_sin_grado_area_titulo_ni_archivo_dice_cada_motivo`, `test_campos_ausentes_son_datos_que_faltan`; `vis::test_datos_que_faltan_responden_400_con_un_mensaje_por_campo`; `e2e::test_sin_area_ni_titulo_muestra_sus_errores_y_enfoca_el_primero`, `test_corregir_un_campo_quita_su_error` |
| envio-sesiones | Sin archivo | `va::test_sin_archivo_lo_pide`, `srv::test_sin_grado_area_titulo_ni_archivo_dice_cada_motivo`, `e2e::test_sin_archivo_lo_pide` |
| envio-sesiones | Área ajena o grado fuera de rango | `srv::test_dato_fuera_de_rango_dice_su_motivo`, `test_area_que_la_institucion_no_trabaja_se_rechaza`, `test_area_de_otra_institucion_que_la_mia_no_trabaja_se_rechaza` |
| envio-sesiones | Enviar sin compartir | `srv::test_enviar_sin_compartir_guarda_la_sesion_con_sus_datos`, `test_aceptar_sin_compartir_no_la_comparte`; `e2e::test_enviar_sin_compartir_va_directo_y_muestra_el_exito` |
| envio-sesiones | Aceptar y enviar | `srv::test_aceptar_y_enviar_la_deja_compartida_con_la_fecha_de_aceptacion`, `e2e::test_aceptar_y_enviar_comparte_y_guarda_la_aceptacion`; `pl::test_los_terminos_son_los_del_doc_09_literales_y_en_orden` |
| envio-sesiones | Volver | `e2e::test_volver_cierra_solo_los_terminos_y_conserva_el_formulario` |
| envio-sesiones | Compartir sin aceptar | `srv::test_compartir_sin_aceptar_no_guarda_nada`, `vis::test_compartir_sin_aceptar_responde_400` |
| envio-sesiones | Datos incompletos con la casilla marcada | `e2e::test_datos_incompletos_con_la_casilla_marcada_no_abren_los_terminos` |
| envio-sesiones | Subiendo | `e2e::test_subiendo_bloquea_campos_botones_y_esc`; `pl::test_hay_una_region_aria_live_para_el_avance` |
| envio-sesiones | Recargar mientras sube | `e2e::test_recargar_mientras_sube_pide_confirmar` |
| envio-sesiones | Se corta y reintenta | `e2e::test_se_corta_y_al_reintentar_se_envia_una_sola_vez`; `pl::test_el_aviso_de_corte_de_red_esta_oculto` |
| envio-sesiones | Se guardó pero no llegó la respuesta | `e2e::test_se_guardo_pero_no_llego_la_respuesta_y_el_reintento_da_el_mismo_exito`, `vis::test_el_mismo_id_otra_vez_responde_el_mismo_201_con_una_sola_sesion`, `srv::test_envio_repetido_con_el_mismo_id_da_el_mismo_exito_sin_escribir_otra_vez`, `con::test_dos_envios_con_el_mismo_id_dejan_una_sesion_y_los_dos_ven_el_exito` |
| envio-sesiones | Éxito sin compartir | `e2e::test_enviar_sin_compartir_va_directo_y_muestra_el_exito` (anuncio y foco), `vis::test_un_envio_valido_responde_201_con_el_fragmento_y_su_resumen` («PDF · 1,2 MB»), `pl::test_el_fragmento_del_exito_dice_el_mensaje_y_el_titulo_enfocable` |
| envio-sesiones | Éxito compartida | `e2e::test_aceptar_y_enviar_comparte_y_guarda_la_aceptacion`, `vis::test_un_envio_compartido_lo_dice_en_el_fragmento`; «Subir otra»: `e2e::test_subir_otra_abre_un_formulario_nuevo` |
| envio-sesiones | Recargar después del éxito | `e2e::test_recargar_despues_del_exito_no_muestra_el_mensaje_ni_envia_otra` |
| envio-sesiones | Datos guardados | `srv::test_enviar_sin_compartir_guarda_la_sesion_con_sus_datos`, `test_el_proposito_es_opcional_y_los_textos_se_recortan`, `test_titulo_de_200_y_proposito_de_1000_se_guardan` |
| envio-sesiones | Coherencia en la base | `mod::test_la_base_rechaza_una_sesion_incoherente` (con el nombre de cada `CHECK`), `test_la_misma_clave_de_archivo_dos_veces_la_rechaza_la_base` |
| envio-sesiones | Estados del boceto | `e2e::test_los_estados_del_boceto_son_accesibles_y_sin_desplazamiento` (11 estados × claro/oscuro × 360/1280 px; axe espera el fin de las animaciones, `b26ee1c`); `pl::test_cada_campo_tiene_su_ayuda_y_su_error_asociados`, `test_el_cuerpo_del_popup_se_alcanza_con_el_teclado` |
| envio-sesiones | Pantalla baja | `e2e::test_pantalla_baja_los_terminos_se_desplazan_y_sus_botones_siguen_a_la_vista` (360 × 560) |
| almacenamiento-archivos | Vercel sin las variables de R2 | `set::test_en_vercel_sin_una_variable_de_r2_no_arranca` (las cuatro, sin valores en el mensaje), `test_en_vercel_una_variable_de_r2_vacia_cuenta_como_ausente`, `test_fuera_de_vercel_r2_a_medias_no_arranca`, `test_con_las_variables_de_r2_las_sesiones_van_a_un_cubo_privado` |
| almacenamiento-archivos | Archivo no público | Sin prueba automática: necesita R2 real. Medición D3, intento 2: GET sin firma → 400; `r2.dev` desactivado. Configuración: `set::test_con_las_variables_de_r2_las_sesiones_van_a_un_cubo_privado` (sin ACL, con firma) |
| almacenamiento-archivos | Revisión de despliegue | `set::test_en_vercel_check_deploy_no_da_errores_ni_advertencias` |
| almacenamiento-archivos | Laptop | `set::test_fuera_de_vercel_sin_r2_las_sesiones_van_a_media`, `alm::test_git_ignora_los_archivos_de_la_laptop` |
| almacenamiento-archivos | Pruebas | `alm::test_en_las_pruebas_los_archivos_van_a_memoria`, `test_guardar_en_las_pruebas_no_crea_archivos_en_media` |
| almacenamiento-archivos | Clave de un PDF | `srv::test_clave_de_un_pdf_es_sesiones_uuid_token_pdf_y_el_archivo_esta_en_el_almacen`, `test_un_docx_se_guarda_con_su_tipo_y_su_clave` |
| almacenamiento-archivos | Intento fallido y reintento con el mismo UUID | `srv::test_el_intento_que_falla_no_borra_el_archivo_del_reintento_que_gano`, `test_cada_intento_tiene_su_propia_clave` (A2; con PostgreSQL y R2 reales, deuda) |
| almacenamiento-archivos | Nombre original largo o con rutas | `va::test_nombre_limpio_sin_rutas`, `test_nombre_de_300_caracteres_se_recorta_a_255_con_su_extension`, `test_el_archivo_validado_trae_el_nombre_limpio` |
| almacenamiento-archivos | Falla el almacenamiento | `srv::test_falla_el_almacenamiento_no_deja_sesion_ni_entrada`, `test_el_almacen_escribe_y_luego_falla_no_deja_el_archivo` (A2), `test_almacen_que_guarda_con_otro_nombre_no_deja_nada` |
| almacenamiento-archivos | Falla la base después del archivo | `srv::test_falla_la_base_despues_del_archivo_borra_el_archivo` |
| almacenamiento-archivos | 4 MB con Slow 4G en la vista previa | Sin prueba automática: medición D3 (tarea 3.3), intento 2: 4 194 304 bytes a 675 kbit/s en 54,0 s, 201, sesión y objeto en R2; función de 39,02 MB |
| indicadores-adopcion | Columnas aún sin datos | `ind::test_la_pagina_muestra_las_semanas_del_rango_elegido` (ninguna celda con «—») |
| indicadores-adopcion | Sesiones cargadas | `ind::test_sesiones_cargadas_cuenta_las_enviadas_compartidas_o_no`, `test_las_sesiones_cuentan_en_su_semana`, `test_enviar_una_sesion_cuenta_como_docente_activa` |
| indicadores-adopcion | Semana sin sesiones | `ind::test_semana_sin_sesiones_dice_cero` |
| indicadores-adopcion | Sesiones de la demostración | `ind::test_las_sesiones_de_la_demostracion_no_cuentan` |
| indicadores-adopcion | Secciones con notas | `ind::test_secciones_con_notas_cuenta_secciones_distintas`, `test_las_notas_cuentan_en_su_semana` |
| indicadores-adopcion | Semana sin notas | `ind::test_semana_sin_notas_dice_cero` |
| indicadores-adopcion | Notas de la demostración | `ind::test_las_notas_de_la_demostracion_no_cuentan` |
| registro-actividad | Catálogo de esta historia | `amod::test_el_catalogo_de_esta_historia`, `test_solo_asistencia_notas_guardadas_y_sesion_enviada_cuentan_para_kpi_01` |
| registro-actividad | Operación fuera del catálogo | `amod::test_operacion_fuera_del_catalogo_la_rechaza_la_base` |
| registro-actividad | Cada operación tiene su prueba | `acat::test_la_tabla_cubre_el_catalogo_menos_las_reservadas`, `test_cada_escenario_es_una_prueba_que_existe` (SESION_ENVIADA → `srv::test_sesion_compartida_deja_su_entrada_sin_titulo_ni_nombre_de_archivo`); `amod::test_ninguna_operacion_esta_reservada` |
| registro-actividad | Sesión enviada sin compartir | `srv::test_sesion_enviada_sin_compartir_deja_su_entrada` |
| registro-actividad | Sesión compartida | `srv::test_sesion_compartida_deja_su_entrada_sin_titulo_ni_nombre_de_archivo` |
| registro-actividad | Envío rechazado o repetido | `srv::test_envio_rechazado_no_deja_entrada`, `test_envio_repetido_con_el_mismo_id_da_el_mismo_exito_sin_escribir_otra_vez`, `test_id_de_otra_autora_da_error_general_sin_escribir` |

## DoD 1 a 9

| N.° | Criterio | Estado |
| --- | --- | --- |
| 1 | Cobertura ≥ 80 % | Local: 98,50 % total (`verificar.py`, sin e2e). Sonar way: pendiente del PR |
| 2 | Análisis estático sin críticas ni altas | Ruff en verde con `verificar.py` (un `noqa: S314` justificado arriba). A2 de Codex: tres hallazgos corregidos (Parte D). CodeQL y SonarQube Cloud: pendiente del PR |
| 3 | Aprobación de otra integrante | Pendiente del PR |
| 4 | Vista previa de Vercel | `968e27c` aplicó `actividad/0005` y `repositorio/0001` en Neon y pasó la medición D3. `b26ee1c` (`carpeta-docente-i37f225ou`): build sin migraciones pendientes; envío de punta a punta desde el navegador con `demounoa` (ver «Envío de punta a punta») |
| 5 | Escenarios en verde y e2e de la ruta ideal | Los 63 escenarios tienen prueba o nota y pasan en local; 437 e2e en verde (todas las apps). Ruta ideal: `e2e::test_enviar_sin_compartir_va_directo_y_muestra_el_exito`, `test_aceptar_y_enviar_comparte_y_guarda_la_aceptacion`. GitHub Actions: pendiente del PR |
| 6 | Reglas de negocio con pruebas propias | RN-007 (áreas que trabaja la institución): `srv::test_area_que_la_institucion_no_trabaja_se_rechaza`, `test_area_de_otra_institucion_que_la_mia_no_trabaja_se_rechaza`. Términos del doc 09 §4: `pl::test_los_terminos_son_los_del_doc_09_literales_y_en_orden`, `srv::test_compartir_sin_aceptar_no_guarda_nada`. Tipo y tamaño (PDF o .docx de hasta 4 MB; frente a los 10 MB de RN-021, en la deuda): `va::*`, `mod::test_la_base_rechaza_una_sesion_incoherente`. RN-015 (registro sin datos sensibles): `srv::test_sesion_compartida_deja_su_entrada_sin_titulo_ni_nombre_de_archivo`. Todo o nada e idempotencia (D4, D5): `srv` («Sin archivos huérfanos» y «Envío repetido») y `con::*` |
| 7 | Accesibilidad sin errores críticos | `e2e::test_los_estados_del_boceto_son_accesibles_y_sin_desplazamiento` (11 estados, claro y oscuro, 360 y 1280 px, objetivos de 44 px), `test_pantalla_baja_los_terminos_se_desplazan_y_sus_botones_siguen_a_la_vista`, `test_sesiones_carga_con_slow_4g`. Lector de pantalla y gesto «atrás» en un Android físico: pulido final (deuda) |
| 8 | Sin datos reales | Docentes, secciones y archivos ficticios armados en memoria (`repositorio/tests/archivos.py`); la medición D3 usó la cuenta demo `demounoa`. El registro solo guarda el UUID y `compartida`; la clave del archivo no lleva el nombre original. Revisión del PR: pendiente |
| 9 | Documentación | Specs del cambio en OpenSpec (ajuste A2 en «Clave del archivo»), design D4 y D6 con sus ajustes, docstrings de `repositorio/servicios.py` y `models.py`. Catálogo de rutas de `docs/03`: filas de Sesiones (4.4). Las contradicciones con los documentos congelados y la deuda están en `tasks.md` ("Workflow follow-up") |
