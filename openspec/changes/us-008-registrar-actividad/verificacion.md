# Verificación: US-008 – Registrar la actividad de los usuarios

Rama `feature/US-008-registrar-actividad`. Pruebas en `src/backend/actividad/tests/`. Abreviaturas: `mod` = `test_modelos.py`, `reg` = `test_registrar.py`. Los 37 escenarios de los dos specs (28 de `registro-actividad` y 9 de `indicadores-adopcion`) tienen al menos una prueba: están en las tablas de cada parte y, el único que no tenía fila, en "Cierre (3.2)". La DoD 1 a 9 va al final de ese apartado.

## Escenarios de `registro-actividad` (parte 1A)

| Escenario | Prueba |
| --- | --- |
| Operación fuera del catálogo | `mod::test_operacion_fuera_del_catalogo_la_rechaza_la_base` (base); `reg::test_operacion_fuera_del_catalogo_lanza_value_error_sin_guardar` (servicio) |
| La operación falla | `reg::test_la_operacion_falla_y_no_queda_entrada` |
| El registro falla | `reg::test_el_registro_falla_y_la_operacion_no_se_guarda` |
| Desde el código | `mod::test_guardar_de_nuevo_una_entrada_existente_lanza_permission_denied`, `test_borrar_una_entrada_lanza_permission_denied` |
| Detalle sin datos personales (mecanismo) | `reg::test_clave_de_detalle_no_permitida_lanza_value_error_sin_guardar`; el recorrido de las entradas reales llega con la tarea 2.6 |

Además: usuario vacío (`mod::test_usuario_vacio_se_permite`, `test_borrar_el_usuario_deja_la_entrada_con_usuario_vacio`, `reg::test_usuario_anonimo_queda_vacio`), orden (`mod::test_orden_de_la_mas_reciente_a_la_mas_antigua`), marcas del catálogo (`mod::test_solo_las_operaciones_de_asistencia_cuentan_para_kpi_01`, `test_solo_intento_sin_permiso_esta_reservada`) y `registrar` fuera de una transacción (`reg::test_fuera_de_una_transaccion_lanza_runtime_error`).

Las pruebas de "falla" usan savepoints y no `transaction=True`: una transacción real vacía la base y rompe las pruebas con `serialized_rollback` de `institucion`.

## Escenarios de `registro-actividad` e `indicadores-adopcion` (parte 1B)

Abreviaturas: `pan` = `test_panel.py`, `exp` = `test_exportar.py`, `ind` = `test_indicadores.py`, `e2e` = `test_panel_e2e.py`.

| Spec | Escenario | Prueba |
| --- | --- | --- |
| registro-actividad | Caso de error (docente o dirección) | `pan::test_docente_y_direccion_no_entran_al_registro`, `test_docente_y_direccion_no_borran_ni_cambian_por_post` |
| registro-actividad | Administrador en el panel | `pan::test_la_ficha_se_ve_sin_campos_editables_ni_botones`, `test_post_a_agregar_responde_403_y_no_crea_nada`, `test_post_a_la_ficha_responde_403_y_la_entrada_queda_igual`, `test_post_a_borrar_responde_403_y_la_entrada_sigue`, `test_borrar_en_lote_desde_la_lista_no_borra` |
| registro-actividad | Filtrar | `pan::test_filtrar_por_usuario_operacion_y_rango_de_fechas`; hora de Lima en `pan::test_la_lista_muestra_la_hora_de_lima` |
| registro-actividad | Exportar lo filtrado | `exp::test_con_un_filtro_trae_solo_esas_filas_con_bom_columnas_y_hora_de_lima`, `test_deja_registro_exportado_con_filtros_y_numero_de_filas`; en el navegador, `e2e::test_el_boton_descarga_el_csv_de_lo_filtrado` |
| registro-actividad | Celda que parece fórmula | `exp::test_celda_que_parece_formula_sale_con_apostrofo`, `test_el_csv_escapa_las_celdas_peligrosas` |
| registro-actividad | Otro rol (exportar) | `exp::test_otro_rol_no_obtiene_el_csv`, `pan::test_docente_y_direccion_no_entran_a_exportar_ni_a_indicadores` |
| indicadores-adopcion | Flujo alternativo válido (consultar un periodo) | `ind::test_la_pagina_muestra_las_semanas_del_rango_elegido`, `test_semanas_de_lunes_a_domingo_todas_con_cero_si_no_hay_actividad`, `test_un_rango_que_corta_una_semana_la_muestra_entera` |
| indicadores-adopcion | Rango por defecto | `ind::test_rango_por_defecto_del_1_de_enero_del_anio_abierto_a_hoy` (y sus tres variantes), `test_la_pagina_sin_fechas_usa_el_rango_por_defecto` |
| indicadores-adopcion | Rango al revés | `ind::test_rango_al_reves_muestra_su_mensaje_y_ninguna_fila` |
| indicadores-adopcion | Domingo por la noche | `ind::test_el_domingo_a_las_23_30_de_lima_cuenta_en_su_semana` |
| indicadores-adopcion | Otro rol | `pan::test_docente_y_direccion_no_entran_a_exportar_ni_a_indicadores` |
| indicadores-adopcion | Solo iniciar sesión | `ind::test_solo_iniciar_y_cerrar_sesion_no_cuenta_como_activa` |
| indicadores-adopcion | Registra asistencia | `ind::test_asistencia_dos_dias_de_la_semana_cuenta_una_vez` |
| indicadores-adopcion | Columnas aún sin datos | `ind::test_sesiones_y_secciones_con_notas_quedan_sin_dato` |
| indicadores-adopcion | Demo cargada | `ind::test_demo_cargada_no_cuenta`, `test_jornadas_cuentan_registro_asistencia_sin_demo_ni_usuario_vacio`, `test_participantes_solo_docentes_activas_reales_con_seccion_en_anio_abierto` |
| indicadores-adopcion | Revisión automática | `e2e::test_los_indicadores_por_semana_pasan_axe` (claro y oscuro, 360 y 1280 px); la lista del registro, `e2e::test_la_lista_del_registro_pasa_axe` |

Accesibilidad: la guía-rastro del panel de Django no pasaba axe (`link-in-text-block`, enlaces blancos sin subrayado sobre texto celeste, 1,42:1). `static/css/panel.css`, cargada desde `templates/admin/base_site.html`, la subraya en todas las pantallas del panel.

## Escenarios de `registro-actividad` (parte 2A)

Abreviaturas: `ses` = `actividad/tests/test_sesion.py`, `asi` = `asistencia/tests/test_actividad.py`.

| Spec | Escenario | Prueba |
| --- | --- | --- |
| registro-actividad | Inicio y cierre de sesión | `ses::test_ingreso_correcto_deja_inicio_sesion`, `test_cerrar_sesion_con_el_boton_deja_cierre_sesion_con_motivo_boton` |
| registro-actividad | Cierre por inactividad | `ses::test_cierre_por_inactividad_deja_motivo_inactividad` |
| registro-actividad | Una lectura no deja entrada | `ses::test_abrir_la_portada_no_deja_entrada`, `asi::test_abrir_la_asistencia_de_hoy_no_deja_entrada` (la lista de estudiantes llega con la parte 2B) |
| registro-actividad | Camino ideal (registro de asistencia) | `asi::test_primer_toque_deja_registro_asistencia_y_asistencia_cambiada`, `test_el_segundo_toque_no_deja_otro_registro_asistencia` |
| registro-actividad | Primer toque del día | `asi::test_primer_toque_deja_registro_asistencia_y_asistencia_cambiada` |
| registro-actividad | Mismo estado otra vez | `asi::test_mismo_estado_y_nota_otra_vez_no_deja_entrada`, `test_lote_repetido_no_deja_entradas_nuevas` |
| registro-actividad | Lote | `asi::test_lote_deja_una_entrada_por_cada_sin_marcar_con_origen_lote`, `test_lote_que_abre_la_jornada_deja_registro_asistencia` |
| registro-actividad | Jornada completa | `asi::test_jornada_completa_al_marcar_al_ultimo_activo`, `test_jornada_completa_una_sola_vez_aunque_luego_cambie_un_estado`, `test_jornada_completa_cuando_el_lote_marca_al_ultimo`, `test_un_estudiante_no_activo_no_impide_la_jornada_completa` |
| registro-actividad | Justificación | `asi::test_nota_cambiada_lo_dice_sin_el_texto`, `test_la_primera_justificacion_con_nota_dice_nota_cambiada` |
| registro-actividad | La operación falla | `asi::test_toque_de_otra_seccion_no_deja_entrada`, `test_toque_con_fecha_que_no_es_hoy_no_deja_entrada`, `test_si_falla_el_guardado_no_queda_entrada`; ingreso rechazado, `ses::test_ingreso_rechazado_no_deja_entrada` |
| registro-actividad | El registro falla | ingreso, `ses::test_inicio_de_sesion_y_last_login_van_en_la_misma_transaccion`; toque, `asi::test_si_falla_el_registro_el_toque_no_se_guarda` (agregada tras la revisión; pasó de entrada porque el `atomic()` ya lo garantizaba) |

Además: "Cerrar sesión" sin sesión no deja entrada (`ses::test_salir_sin_sesion_no_deja_entrada`). Como `force_login` también dispara `user_logged_in`, las pruebas del panel entran con `entrar()` (`actividad/tests/conftest.py`), que quita esa entrada de la preparación. Verde: suite unitaria y e2e de `cuentas` y `asistencia` (US-001, US-002 y US-030: 161) y del resto de apps (96). La revisión encontró rota la e2e de la lista del registro (parte 1B: el ingreso real deja INICIO_SESION); `en_el_panel` quita esa entrada con `quitar_inicio_de_sesion`.

## Escenarios de `registro-actividad` (parte 2B)

Abreviaturas: `est` = `institucion/tests/test_actividad.py`, `pin` = `actividad/tests/test_panel_instrumentado.py`, `cat` = `actividad/tests/test_catalogo.py`.

| Spec | Escenario | Prueba |
| --- | --- | --- |
| registro-actividad | Comando de consola | `est::test_cargar_secciones_deja_seccion_creada_por_seccion_nueva`, `test_cargar_demo_deja_demo_cargada_con_usuario_vacio_y_conteos`, `test_quitar_demo_deja_demo_quitada_con_usuario_vacio_y_conteos`, `test_descartar_seccion_deja_seccion_descartada_y_conserva_la_asistencia` |
| registro-actividad | Operación del panel | `pin::test_alta_de_cuenta_deja_cuenta_creada`, `test_editar_cuenta_deja_los_nombres_de_los_campos_sin_valores`, `test_alta_de_institucion_deja_institucion_creada`, `test_editar_institucion_deja_institucion_editada`, `test_alta_de_anio_deja_anio_creado`, `test_editar_anio_deja_anio_editado`, `test_alta_de_seccion_deja_seccion_creada`, `test_editar_seccion_deja_seccion_editada`, `test_editar_un_area_desde_la_ficha_deja_catalogo_editado`, `test_desactivar_una_competencia_deja_catalogo_editado`, `test_editar_desde_list_editable_deja_catalogo_editado`; además contraseña, desbloqueo y reactivar (`test_cambiar_la_contrasena_deja_cuenta_editada_con_password`, `test_desbloquear_deja_cuenta_editada_con_desbloqueo`, `test_reactivar_deja_cuenta_editada_con_is_active`) |
| registro-actividad | Desactivar una cuenta | `pin::test_desmarcar_activo_deja_cuenta_desactivada`, `test_desactivar_y_cambiar_otro_campo_deja_dos_entradas` (agregada tras la revisión) |
| registro-actividad | Asignar y liberar una sección | `pin::test_elegir_docente_deja_seccion_asignada`, `test_quitar_docente_deja_seccion_liberada`, `test_cambiar_docente_en_dos_pasos_deja_liberada_y_asignada`, `test_cambiar_nombre_y_docente_deja_dos_entradas` |
| registro-actividad | Ningún camino del panel escribe sin registrar | `pin::test_cada_model_admin_que_escribe_usa_la_mezcla`, `test_borrar_una_institucion_responde_403`, `test_grupos_fuera_del_panel`, `test_el_historial_de_django_sigue_apareciendo` |
| registro-actividad | Estudiante editado | `est::test_editar_deja_estudiante_editado_sin_los_nombres` |
| registro-actividad | Sección descartada (Conservación) | `est::test_descartar_seccion_deja_seccion_descartada_y_conserva_la_asistencia` |
| registro-actividad | La operación falla | `est::test_quitar_bloqueado_por_registros_no_deja_entrada`, `test_vaciar_bloqueado_por_registros_no_deja_entrada`, `test_importar_con_errores_no_deja_entrada`, `test_agregar_repetido_no_deja_entrada`, `test_vaciar_una_lista_ya_vacia_no_deja_entrada` (agregada tras la revisión) |
| registro-actividad | El registro falla | `est::test_si_falla_el_registro_el_estudiante_no_se_agrega` |
| registro-actividad | Una lectura no deja entrada | `est::test_abrir_la_lista_de_estudiantes_no_deja_entrada` |
| registro-actividad | Cada operación tiene su prueba | `cat::test_la_tabla_cubre_el_catalogo_menos_las_reservadas` (rojo con REGISTRO_EXPORTADO fuera de la tabla, verde con la tabla completa), `test_cada_escenario_es_una_prueba_que_existe`; la tabla está en `actividad/tests/escenarios.py` |
| registro-actividad | Detalle sin datos personales (recorrido) | fixture `escenario_de_operacion` de `src/backend/conftest.py`: al terminar cada prueba de la tabla, comprueba que dejó su operación y que ningún detalle trae nombres ficticios de estudiantes ni texto de notas (se vio fallar apuntando una operación a una prueba que no la genera) |

Notas:
- Cambiar de docente en un paso no existe: US-005 obliga a vaciar la sección y luego elegir a la otra docente (D3 de US-005). "Cambiar" deja SECCION_LIBERADA y luego SECCION_ASIGNADA.
- `user_change_password` de Django no abre transacción (como dice D5): `UsuarioAdmin` la envuelve en `atomic()` para que la contraseña y su entrada vayan juntas.
- `cargar_secciones` también deja ANIO_CREADO cuando crea el año (escritura de consola, "Toda escritura queda registrada"). `cargar_demo` deja una sola DEMO_CARGADA, sin ESTUDIANTES_IMPORTADOS por sección (`importar_lista_sin_registro`).
- Verde: `uv run pytest --cov` (1233, 98,43 %) y e2e de `cuentas`, `institucion`, `catalogo`, `actividad` y `config` (US-003, US-005, US-006 y EN-06: 198).
- Los campos del detalle son los nombres de `form.changed_data` (p. ej. `first_name`), que es lo que Django usa para armar el `change_message`, no sus etiquetas. Guardar una ficha sin cambios no deja entrada.

## Cierre (3.2)

| Spec | Escenario | Prueba |
| --- | --- | --- |
| registro-actividad | Catálogo de esta historia | `mod::test_solo_las_operaciones_de_asistencia_cuentan_para_kpi_01`, `test_solo_intento_sin_permiso_esta_reservada`; las 26 operaciones restantes, una por una, en `cat::test_la_tabla_cubre_el_catalogo_menos_las_reservadas` (la tabla de `escenarios.py` nombra cada operación del spec) |

### DoD 1 a 9

| N.° | Estado | Evidencia |
| --- | --- | --- |
| 1 | Cumple en local; **pendiente del PR** | `verificar.py --antes-del-commit` del cierre: PASA, cobertura total 98,32 % (mínimo 80 %). La puerta Sonar way solo se ve en el PR |
| 2 | Cumple en local; **pendiente del PR** | Ruff sin hallazgos (`check` y `format --check`, en `verificar.py`). CodeQL y SonarQube Cloud solo corren en el PR |
| 3 | **Pendiente del PR (equipo)** | Aprobación de otra integrante |
| 4 | **Pendiente del PR** | Vista previa de Vercel del PR, con `actividad/0001_initial` en su rama de Neon |
| 5 | Cumple en local; **pendiente del PR** | Cada escenario con su prueba (tablas de arriba). E2E en verde tras el arreglo de A2 (corrida en esa sesión); ruta ideal en el navegador: `e2e::test_el_boton_descarga_el_csv_de_lo_filtrado`. El canal se ve en el PR |
| 6 | Cumple | Las escrituras del registro pasan solo por `actividad.servicios.registrar`, dentro de la transacción de cada operación; RN-015 (sin datos personales en el detalle) con `DETALLE_PERMITIDO` y el recorrido del fixture `escenario_de_operacion`; la regla de KPI-01 y la exclusión de la demostración, en `ind::` |
| 7 | Cumple | La lista del registro y los indicadores por semana pasan axe en claro y oscuro, a 360 y 1280 px (`e2e::test_la_lista_del_registro_pasa_axe`, `test_los_indicadores_por_semana_pasan_axe`) |
| 8 | Cumple | Solo nombres ficticios; el fixture `escenario_de_operacion` comprueba que ningún detalle trae nombres de estudiantes ni texto de notas |
| 9 | Cumple | Este cambio en OpenSpec (design ajustado en D4 y D5), docstrings y el Catálogo de rutas de `docs/03` (versión 1.5.0: lista, exportar e indicadores). El README no cambia |

## Minor para la descripción del PR

Parte 1A (revisión de la parte):

- `reg::test_fuera_de_una_transaccion_lanza_runtime_error` simula la ausencia de transacción con `monkeypatch` de `connection.in_atomic_block`; no la prueba contra una conexión real sin transacción.
- Sin prueba de un detalle con claves permitidas que se guarda tal cual, salvo el de REGISTRO_ASISTENCIA, ni de `detalle` que no sea un diccionario.
- `entidad` y `entidad_id` no se validan contra su `max_length` (60 y 40): un valor largo da un `DataError` de PostgreSQL que revierte la operación, coherente con el spec pero con un mensaje poco claro. Improbable con `db_table` e ids.
- `bulk_update`, `QuerySet.update()` y `delete()` no pasan por `save()` ni `delete()` del modelo; el bloqueo en la base es EN-04 (ya en la deuda).
- `DETALLE_PERMITIDO` deja sin claves a las operaciones sin detalle y a las tres de demostración; las claves de estas se agregan en la tarea 2.4.

Parte 1B (revisión de la parte; corregidos antes del commit: las fechas del formulario de indicadores en formato ISO, `timezone.localdate()` en la prueba del rango por defecto y la tabla de indicadores a 360 px):

- La tabla de indicadores mide justo 360 px a 360 px (relleno de 4 px y separación silábica en celular): sin margen si cambia la fuente o un encabezado.
- Fechas extremas (`hasta=9999-12-31`) dan 500 por `OverflowError` en la lista y en los indicadores, y un rango de siglos genera miles de filas; solo lo alcanza el Administrador. Falta un límite de años o de semanas en `FormularioRango` y en `RangoFechasFilter`.
- "Quitar el rango" aparece al enviar el filtro con las dos fechas vacías (`puesto` mira `[""]`).
- `detalle["filtros"]` de REGISTRO_EXPORTADO guarda toda la cadena de consulta (`q`, `o`, `_facets` incluidos), no solo los filtros que la lista aplica.
- Con un filtro de fecha inválido, `exportar/` redirige a la lista sin filtros ni aviso; un "desde" posterior al "hasta" en la lista da una lista vacía sin mensaje.
- `exportar_csv` carga todo el resultado en memoria (sin `.iterator()`); bajo volumen en el piloto.
- Sin prueba de una cuenta con `is_staff` sin rol Administrador en la lista, `exportar/` e `indicadores/` (403 por código); sin prueba de una exportación de más de 50 entradas (que sale el `queryset` y no la página); `test_una_fecha_invalida_no_rompe_la_lista` acepta 200 o 302.
- La lista hace dos `COUNT(*)` por carga; `show_full_result_count = False` ahorraría uno.

Parte 2A (revisión de la parte; corregido antes del commit: la e2e de la lista del registro):

- El reinicio de intentos de RN-024 se confirma en `authenticate()` (`intentar_ingreso`, su propio `atomic()`), antes de `form_valid`: si INICIO_SESION falla, `last_login` se revierte pero el contador queda en 0. La contraseña era correcta, así que no cambia nada para la docente (D4).
- Sin pruebas de concurrencia de D6 (dos toques finales a la vez → un JORNADA_COMPLETA; primer toque doble → un REGISTRO_ASISTENCIA): lo garantiza el bloqueo de la jornada, sin prueba con hilos. Tampoco se prueba que un lote con un id de otra sección no deje entrada.
- `_registrar_si_completa` hace hasta 4 consultas por toque (cuenta los activos dos veces y luego busca JORNADA_COMPLETA); cada toque suma de 4 a 6 consultas.
- El `select_for_update` sobre `asistencia` en `marcar` y `marcar_restantes` es redundante con el bloqueo de la jornada (D6 lo pide; inofensivo).
- Si la jornada queda completa porque se retira a un estudiante, el siguiente reintento sin cambios deja JORNADA_COMPLETA.

Parte 2B (revisión de la parte; corregidos antes del commit: desactivar una cuenta y cambiar otro campo en el mismo guardado deja CUENTA_DESACTIVADA y CUENTA_EDITADA; vaciar una lista ya vacía no deja entrada; `_docente_anterior` sale siempre de `request`):

- El fixture `escenario_de_operacion` reconoce las pruebas por `módulo::nombre`: si cambia cómo pytest nombra los módulos (`--import-mode=importlib`, otra raíz), deja de revisar sin avisar. Falta un aviso de sesión si no visitó ningún escenario.
- El fixture pide `db`: chocaría con una prueba de la tabla que use `transactional_db` o `live_server` (hoy ninguna). Si la prueba ya falló, su revisión agrega un segundo error en el teardown.
- "Dejó su operación" acepta cualquier entrada de esa operación, también una creada por un fixture; hoy cada escenario la comprueba por su cuenta. Contar antes y después lo haría más estricto.
- La lista de nombres prohibidos del fixture tiene los apellidos de las pruebas pero no todos los nombres de pila ("ANA", "LUIS"); la prueba de editar sí los busca.
- `cargar_demo` sobre una demo ya cargada deja DEMO_CARGADA con `secciones: 0` (reescribe las contraseñas de las cuentas demo, que sí es una escritura).

Revisión final A2 (Codex; corregido: un guardado que revierte un cambio ajeno ya deja su entrada. `editar_estudiante` compara con la fila bloqueada y la ficha, el cambio de contraseña y `list_editable` del panel releen la fila con `FOR UPDATE`. Las dos medias quedan como deuda por decisión del equipo):

- **[media, deuda]** CIERRE_SESION se confirma antes de borrar la sesión: Django emite `user_logged_out` antes de `session.flush()` y el receptor abre su propio `atomic()`. Si falla el borrado de `django_session`, queda la entrada y la sesión sigue válida. Corrección propuesta: envolver `logout()` completo en un `atomic()` en la salida normal, la del panel y la de inactividad, con una prueba que haga fallar `Session.delete`.
- **[media, deuda]** La guardia de solo lectura de `RegistroActividad.save()` usa `_state.adding`: una instancia nueva con la PK de una entrada existente pasa la guardia y Django hace UPDATE. Solo es alcanzable desde código, no desde la interfaz. Corrección propuesta: forzar INSERT en la primera persistencia (`force_insert`) y una prueba que construya otra instancia con el mismo id.
- La prueba del bloqueo en el panel comprueba que la lectura lleva `FOR UPDATE`, no reproduce dos peticiones con hilos.

Revisión del arreglo de A2 (sin Critical ni Important; los Minor quedan aquí):

- `editar_estudiante` compara `apellidos` y `nombres` con la fila bloqueada, pero `_guardar_estudiante` guarda la instancia entera: una copia vieja revertiría `estado`, `fecha_estado` o `seccion` sin entrada. Hoy no hay forma de llegar a eso (ningún servicio cambia `estado`); hay que corregirlo en US-031 con `update_fields=["apellidos", "nombres"]`.
- `RegistraEnPanel.get_object` se salta el bloqueo en silencio si un POST llega sin transacción (en las pruebas nunca pasa) y usa la conexión por defecto en vez de `router.db_for_write`.
- Las pruebas del panel comprueban que la consulta lleva `FOR UPDATE`, no el comportamiento; una prueba por admin con `get_object` devolviendo una copia vieja lo cerraría.
- El `atomic()` del POST del changelist también cubre las acciones: "Desbloquear cuenta" pasa a ser una sola transacción con puntos de guardado, y su docstring ("una transacción por cuenta") ya no lo describe exactamente.
- `SeccionAdmin.get_object` sustituye a la de la mezcla sin llamar a `super()` (ya bloquea con una sola lectura); falta decirlo en su docstring.
