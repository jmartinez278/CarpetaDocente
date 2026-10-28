# Verificación: US-006

Rama `feature/US-006-importar-estudiantes`. Pruebas en `src/backend/`. Abreviaturas: `mod` = `institucion/tests/test_modelos_estudiante.py`, `lec` = `institucion/tests/test_lectura_lista.py`, `srv` = `institucion/tests/test_servicios_estudiantes.py`, `vis` = `institucion/tests/test_vistas_estudiantes.py`, `e2e` = `institucion/tests/test_estudiantes_e2e.py`, `pan` = `cuentas/tests/test_pantallas.py`, `ina` = `cuentas/tests/test_inactividad.py`.

## Escenarios de `estudiantes-seccion`

| Escenario | Prueba |
| --- | --- |
| Nombre guardado en mayúsculas | `mod::test_save_guarda_la_forma_normalizada`; `srv::test_agregar_normaliza_y_guarda` |
| Homónimo exacto en la misma sección | `mod::test_homonimo_exacto_lo_rechaza_la_base_de_datos`, `test_homonimo_exacto_no_pasa_la_validacion`; `srv::test_agregar_el_homonimo_se_rechaza_y_no_cambia_nada`, `test_editar_hacia_un_homonimo_se_rechaza_y_no_cambia_nada`, `test_repetidos_se_agrupan_en_un_error` |
| Mismo nombre en otra sección | `mod::test_mismo_nombre_en_otra_seccion_se_guarda`; `srv::test_importar_con_un_nombre_igual_en_otra_seccion_se_guarda` |
| Sección de otra docente | `vis::test_otra_docente_recibe_404_y_no_ve_nombres`, `test_un_estudiante_de_otra_seccion_da_404`, `test_otra_docente_no_puede_pegar_en_la_seccion`, `test_otra_docente_no_puede_agregar_en_la_seccion`, `test_otra_docente_no_puede_vaciar_la_seccion` |
| Sección de un año cerrado | `vis::test_una_seccion_del_anio_cerrado_da_404`; `srv::test_secciones_docente_ordena_y_excluye_el_anio_cerrado` |
| Otro rol | `vis::test_la_direccion_llega_a_su_pantalla`; `ina::test_una_peticion_htmx_de_otro_rol_lleva_a_su_pantalla_con_hx_redirect` |
| Abrir la lista | `e2e::test_ver_estudiantes_abre_el_dialogo_sin_cambiar_la_direccion`, `test_camino_ideal_importa_los_25_con_lineas_en_blanco` (cabecera "25 estudiantes") |
| Cerrar el diálogo | `e2e::test_esc_cierra_el_dialogo_y_el_foco_vuelve_al_enlace`, `test_cerrar_cierra_el_dialogo_y_el_foco_vuelve_al_enlace` |
| Sin JavaScript | `e2e::test_sin_javascript_todo_funciona_como_pagina_completa` (pegar, agregar, editar, quitar y vaciar); `vis::test_sin_htmx_responde_la_pagina_completa_con_h1` |
| Lista vacía | `vis::test_lista_vacia_con_sus_dos_acciones` |
| Orden y número | `vis::test_la_lista_numera_en_orden_con_el_nombre_completo_y_editar`; `srv::test_alvarez_va_antes_de_bravo`, `test_nunez_va_antes_de_nuñez`, `test_ñaupa_va_antes_de_ochoa` |
| Camino ideal | `e2e::test_camino_ideal_importa_los_25_con_lineas_en_blanco`; `srv::test_25_lineas_validas_crean_25_estudiantes`; `vis::test_importar_una_lista_valida_redirige_con_303_y_guarda` |
| Líneas en blanco | `srv::test_las_lineas_en_blanco_no_dan_error`; `lec::test_las_lineas_en_blanco_se_ignoran_pero_cuentan_en_la_numeracion` |
| Lista con estudiantes | `vis::test_la_lista_con_estudiantes_no_ofrece_pegar_lista` |
| Dirección de Pegar lista con estudiantes | `vis::test_pegar_con_estudiantes_muestra_el_aviso_sin_el_cuadro` |
| Envío a una sección con estudiantes | `vis::test_el_envio_a_una_seccion_con_estudiantes_no_guarda_nada`; `srv::test_pegar_lista_con_la_seccion_con_un_estudiante_no_guarda_nada` |
| Caso de error | `e2e::test_caso_de_error_no_guarda_nada_y_conserva_el_texto`; `vis::test_con_errores_el_texto_vuelve_intacto_con_aria_invalid` |
| Línea con tabulaciones | `lec::test_linea_con_tabulacion_pide_pegar_solo_la_columna` (con y sin coma) |
| Falta la coma | `lec::test_linea_sin_coma` |
| Estudiante repetido | `srv::test_repetidos_se_agrupan_en_un_error`, `test_tres_repetidos_se_listan_con_comas_y_una_y` |
| Campo demasiado largo | `srv::test_121_caracteres_en_apellidos`, `test_121_caracteres_en_nombres` |
| Más de 60 estudiantes | `lec::test_61_lineas_con_texto_da_solo_el_error_de_60`; `srv::test_mas_de_60_lineas_no_guarda_nada` |
| Texto vacío | `srv::test_texto_vacio_pide_pegar_al_menos_un_estudiante`; `vis::test_el_texto_vacio_pide_pegar_al_menos_uno` |
| Flujo alternativo válido | `e2e::test_flujo_alternativo_valido_agrega_y_la_cabecera_pasa_a_26` |
| Homónimo al agregar | `vis::test_el_homonimo_al_agregar_conserva_lo_escrito_y_sugiere_el_segundo_nombre` |
| Campo vacío | `vis::test_un_campo_vacio_muestra_su_error_y_no_guarda` |
| Corregir un nombre | `e2e::test_corregir_un_nombre_vuelve_a_la_lista_con_el_nombre_corregido`; `vis::test_guardar_cambios_vuelve_a_la_lista_con_el_nombre_corregido` |
| Corrección que crea un homónimo | `vis::test_la_correccion_que_crea_un_homonimo_no_se_guarda` |
| Quitar sin registros | `e2e::test_quitar_uno_baja_la_cabecera_en_uno`; `vis::test_quitar_sin_registros_vuelve_a_la_lista_con_uno_menos` |
| Vaciar sin registros | `e2e::test_vaciar_25_deja_la_lista_vacia_y_el_aviso_vuelve_a_la_portada` |
| Vaciar con registros | **Simulado hasta US-030** (`RestrictedError` simulado; aún no existen `asistencia` ni `notas`): `srv::test_vaciar_con_registros_lanza_y_no_borra_ninguno`; `vis::test_vaciar_con_registros_muestra_el_bloqueo_y_no_quita_ninguno` |
| Quitar con registros | **Simulado hasta US-030**: `srv::test_quitar_con_registros_lanza_y_no_borra`; `vis::test_quitar_con_registros_muestra_el_bloqueo_y_no_quita` |
| Acción tras 60 minutos sin actividad | `e2e::test_sesion_vencida_al_importar_lleva_la_pagina_a_ingresar`; `ina::test_un_post_htmx_vencido_tambien_lleva_a_la_portada_como_next` |
| Revisión de cada vista | `e2e::test_la_lista_vacia_en_el_dialogo_pasa_axe`, `test_la_lista_vacia_como_pagina_completa_pasa_axe`, `test_la_lista_con_estudiantes_pasa_axe`, `test_la_lista_como_pagina_completa_pasa_axe`, `test_pegar_y_revisar_lista_pasan_axe`, `test_revisar_lista_como_pagina_completa_pasa_axe`, `test_agregar_y_editar_pasan_axe`, `test_agregar_con_homonimo_como_pagina_completa_pasa_axe`, `test_quitar_vaciar_y_los_bloqueos_pasan_axe` (claro y oscuro, 360 y 1280 px, con el ancho del documento o del diálogo) |
| Nombre largo a 320 px | `e2e::test_un_nombre_de_120_mas_120_se_lee_completo_sin_desplazamiento` |

## Escenarios de `pantallas-de-inicio`

Los cinco escenarios de US-005 siguen con sus pruebas: `pan::test_la_portada_saluda_con_el_nombre_completo`, `test_la_portada_muestra_la_seccion_bajo_el_saludo_y_fuera_del_h1`, `test_la_portada_ordena_las_secciones_por_grado_y_nombre`, `test_la_portada_sin_seccion_dice_que_aparecera`, `test_la_portada_con_la_unica_seccion_en_un_anio_cerrado`.

| Escenario | Prueba |
| --- | --- |
| Enlace a la lista con una sección | `pan::test_con_una_seccion_ver_estudiantes_va_junto_a_la_linea`; `e2e::test_ver_estudiantes_abre_el_dialogo_sin_cambiar_la_direccion` |
| Sin enlace con varias secciones | `pan::test_sin_seccion_o_con_varias_no_hay_enlace_ni_aviso_ni_dialogo` (caso de dos secciones); `srv::test_seccion_unica_es_none_con_dos_secciones` |
| Sin enlace sin sección | `pan::test_sin_seccion_o_con_varias_no_hay_enlace_ni_aviso_ni_dialogo` (caso sin sección); `srv::test_seccion_unica_es_none_sin_secciones` |
| Sección sin estudiantes | `pan::test_la_seccion_sin_estudiantes_muestra_el_aviso_bajo_la_linea`, `test_con_estudiantes_la_portada_no_muestra_el_aviso` |
| El aviso desaparece al cargar la lista | `e2e::test_tras_importar_y_cerrar_la_portada_ya_no_muestra_el_aviso`; `vis::test_con_htmx_agregar_quita_el_aviso_de_la_portada` |

Además: axe de la portada con el aviso (`e2e::test_la_portada_con_el_aviso_pasa_axe`) y 320 px sin desplazamiento (`e2e::test_la_portada_y_la_lista_vacia_no_se_desplazan_en_horizontal`).

## Revisión final (A2)

`/codex:adversarial-review --base main --background` (2026-10-27), sin texto de foco: no llevó el foco en los specs del cambio. Veredicto: **needs-attention**, un hallazgo `medium` (tratado como Important), sin Critical ni Minor.

| Hallazgo | Resolución |
| --- | --- |
| Important: Editar puede volver a crear un estudiante quitado o vaciado entretanto. `EditarView` lo carga antes de guardar y el `save()` de Django, si el UPDATE no encuentra la fila, hace un INSERT con la misma PK (`servicios.py`, `_guardar_estudiante`) | Corregido con la prueba primero (rojo: `DID NOT RAISE` y 303; luego verde): `srv::test_editar_un_estudiante_ya_quitado_no_lo_vuelve_a_crear[quitar, vaciar]` y `vis::test_editar_un_estudiante_quitado_mientras_se_enviaba_da_404_sin_recrearlo`. `editar_estudiante` guarda con `force_update=True` (Context7: un UPDATE forzado sin filas lanza `DatabaseError` y no inserta) y lanza `Estudiante.DoesNotExist`; la vista responde 404, como Editar y Quitar cuando el estudiante ya no está |

**Para quien revise:** la tabla, la DoD y las casillas del grupo 3 no pasaron por la A2. Estaban sin commit y la revisión es de `main...HEAD`.

## DoD 1 a 9

| N.° | Estado | Evidencia |
| --- | --- | --- |
| 1 | Cumple en local; **pendiente del PR** | `uv run pytest --cov`: 784 pasan, cobertura total 98,28 % (mínimo 80 %). La puerta Sonar way solo se ve en el PR |
| 2 | Cumple en local; **pendiente del PR** | Ruff sin hallazgos (`check` y `format --check`, en `verificar.py`). CodeQL y SonarQube Cloud solo corren en el PR |
| 3 | **Pendiente del PR (equipo)** | Aprobación de otra integrante |
| 4 | **Pendiente del PR** | Vista previa de Vercel del PR, con la migración `institucion/0003` en su rama de Neon |
| 5 | Cumple en local; **pendiente del PR** | Cada escenario con su prueba (tablas de arriba); el bloqueo con registros, simulado hasta US-030. 161 e2e en verde. El canal se ve en el PR |
| 6 | Cumple | Normalización, homónimo, todo o nada, Pegar lista solo con la sección vacía y el bloqueo de quitar y vaciar en `institucion/servicios.py` (`srv`); las vistas no escriben en la BD |
| 7 | Cumple | Axe sin infracciones críticas ni graves en cada vista de la lista y en la portada, claro y oscuro, 360 y 1280 px; sin desplazamiento horizontal de 320 a 1280 px |
| 8 | Cumple | Solo nombres ficticios (los del boceto); ningún dato de la I.E. inventado |
| 9 | Cumple | Este cambio en OpenSpec, docstrings y el Catálogo de rutas de `docs/03` (seis rutas nuevas). El README no cambia |

## Minor para la descripción del PR

Grupo 1 (revisión del grupo, sin DESIGN.md):

- `importar_lista` y `agregar_estudiante` no comparten bloqueo: un agregar concurrente entre el `exists()` y el `bulk_create` podría dar un `IntegrityError` sin capturar. Ventana mínima (una docente por sección); sin prueba de carrera.
- `editar_estudiante` deja la instancia en memoria con los valores rechazados si falla: la vista del grupo 2 debe volver a cargar el estudiante.
- `_guardar_estudiante` traduce cualquier `IntegrityError` a "Este estudiante ya está en la lista" (engañoso si la sección se borra en paralelo; muy improbable).
- Condicional anidado en `_errores_de_filas` poco legible; `_clave_orden` repetida en el desempate de `estudiantes_ordenados`.
- Falta una prueba del máximo de 120 caracteres al editar (solo al agregar).
- El mensaje "Este estudiante ya está en la lista" está en `servicios.py` y en `Estudiante.Meta` (el ciclo de importación impide compartirlo).

Grupo 2, parte A (revisión de la parte, con las secciones de DESIGN.md que usa):

- Mientras no existan las partes B y C, "Agregar uno por uno" y "Pegar lista" abren rutas con `PendienteView` (404): no hacen nada al pulsarlas. Temporal: `PendienteView` (en `institucion/views.py` y `urls.py`) la reemplazan las partes B y C con sus vistas reales, y el catálogo de rutas suma entonces las cinco rutas restantes.
- CSS adelantado para B y C: `.mensaje--exito` y `.campo-ayuda` (aún sin uso).
- Si la petición del parcial falla (500 o red), HTMX no muestra nada en el diálogo.
- Con el diálogo abierto y la sesión vencida, la entrada de historial extra queda al ir a `/ingresar/` (inocuo: tras ingresar va a `/docente/`).
- El aviso de la portada (`role="status"`) cambia por `hx-swap-oob` mientras el diálogo deja la portada inerte: el lector de pantalla probablemente no lo anuncie hasta cerrar el diálogo.
- Para B y C: los POST del diálogo necesitan el token CSRF (`{% csrf_token %}` en cada formulario).

Grupo 2, parte B (revisión de la parte, con Mensaje, Campo de texto y Movimiento de DESIGN.md):

- En Revisar lista, el cuadro (`aria-invalid="true"`) no apunta a la lista de errores con `aria-describedby`: el lector los oye por el `role="alert"` y el foco en "Revisar lista", pero no al volver al cuadro.
- Los errores van arriba del cuadro y sin ícono por línea (como el boceto), no debajo del campo como pide Campo de texto: el mensaje de error de la vista sí lleva ícono.
- El aviso "N estudiantes importados" (`role="status"`) llega dentro del contenido nuevo; el foco va al título, así que el lector probablemente no lo anuncie solo.
- "Importar" no se desactiva mientras envía: un doble clic podría mandar un segundo POST, que encuentra la sección con estudiantes y muestra "Tu sección ya tiene estudiantes" en lugar del aviso de éxito (no se guarda nada de más).
- Las e2e de 2.4 y 2.5 se escribieron después de las pruebas de vistas ya en verde y pasaron al primer intento: no se las vio fallar.

Grupo 2, parte C (revisión de la parte, con Botón principal, Mensaje y Campo de texto de DESIGN.md):

- Como "Importar", "Guardar y agregar otro", "Guardar cambios", "Quitar estudiante" y "Vaciar lista" no se desactivan mientras envían (Botón principal pide `aria-disabled`). Un doble clic en "Guardar y agregar otro" guarda una vez y luego muestra "Este estudiante ya está en la lista" (el contador sí sube); en Quitar, el segundo envío da 404 y HTMX no lo muestra. Misma deuda que "Importar".
- El máximo de 120 caracteres del formulario se mide antes de normalizar: 121 caracteres con un espacio repetido se rechazan aunque guardados serían 120 (el `maxlength="120"` del campo ya impide escribir más).
- `_error_homonimo.html` muestra la sugerencia del segundo nombre con cualquier error general del formulario; hoy el único posible es el homónimo.
- `EditarView` vuelve a cargar al estudiante tras un homónimo (Minor del grupo 1), pero ninguna prueba lo observa: Editar no muestra los valores de la instancia.
- Textos que D9 no fijaba: "Se quitará 1 estudiante." (singular de la confirmación de vaciar), "Escribe los apellidos" / "Escribe los nombres" (campo vacío) y "Usa un máximo de 120 caracteres." (campo largo). Quitar y Editar correctos no muestran aviso (el spec no lo pide).
- Vaciar con la lista ya vacía (dirección abierta a mano) vuelve a la lista con 303 en lugar de mostrar "Se quitarán los 0 estudiantes.".
- Si el estudiante se quitó en otra pestaña, Editar o Quitar dan 404 y el diálogo no muestra nada (como el Minor de la parte A sobre las respuestas con error).

