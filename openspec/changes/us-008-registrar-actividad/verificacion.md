# Verificación: US-008 – Registrar la actividad de los usuarios

Rama `feature/US-008-registrar-actividad`. Pruebas en `src/backend/actividad/tests/`. Abreviaturas: `mod` = `test_modelos.py`, `reg` = `test_registrar.py`. La tabla crece con cada parte; la tarea 3.2 la completa con los dos specs y la DoD 1 a 9.

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
