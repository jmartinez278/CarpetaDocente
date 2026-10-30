# Verificación: EN-06 – Catálogo curricular y datos ficticios

Rama `feature/EN-06-datos-iniciales`. Pruebas en `src/backend/`. Abreviaturas: `mod` = `catalogo/tests/test_modelos.py`, `mig` = `catalogo/tests/test_migracion_catalogo.py`, `srv` = `catalogo/tests/test_servicios.py`, `adm` = `catalogo/tests/test_admin.py`, `demo` = `institucion/tests/test_demo.py`, `conc` = `institucion/tests/test_demo_concurrencia.py`, `cmd` = `institucion/tests/test_comandos_demo.py`.

## Escenarios de `catalogo-curricular`

| Escenario | Prueba |
| --- | --- |
| Catálogo cargado | `mig::test_once_areas_con_codigo_nombre_y_orden` |
| Exonerables y transversales | `mig::test_solo_educacion_fisica_y_religiosa_admiten_exoneracion`, `test_solo_los_bloques_0006_y_0007_son_transversales` |
| Área repetida | `mod::test_area_con_codigo_repetido_se_rechaza`, `test_area_con_nombre_repetido_se_rechaza` (en la base; el panel no permite agregar: `adm::test_sin_url_de_agregar`) |
| Carga idempotente | `mig::test_repetir_la_carga_no_duplica_ni_restaura_lo_editado` |
| Competencias por área | `mig::test_treinta_competencias_activas_con_los_conteos_por_area`, `test_orden_de_competencias_es_01_a_n_en_cada_area` |
| Orden del SIAGIE y no del Anexo 03 | `mig::test_arte_y_cultura_va_en_el_orden_del_siagie` |
| Texto completo de la leyenda | `mig::test_competencia_01_de_comunicacion_con_el_texto_de_la_leyenda`, `test_competencias_con_su_texto_completo`, `test_gestiona_su_aprendizaje_en_minuscula` |
| Competencia repetida en el área | `mod::test_competencia_repetida_en_la_misma_area_se_rechaza`, `test_mismo_nombre_de_competencia_en_otra_area_se_acepta` |
| Institución existente al migrar | `mig::test_institucion_existente_al_migrar_recibe_sus_areas` (con `MigrationExecutor`) |
| Institución nueva | `srv::test_institucion_nueva_nace_con_las_11_areas_y_solo_0002_sin_trabajar` |
| Área repetida en la institución | `mod::test_dos_filas_de_la_misma_area_para_una_institucion_se_rechazan`; `srv::test_asegurar_areas_repetido_no_duplica_ni_cambia_un_se_trabaja_editado` |
| Desactivar una competencia | `adm::test_desmarcar_activa_deja_la_competencia_inactiva_y_existente` |
| Sin borrar | `adm::test_sin_url_de_borrado`, `test_sin_accion_eliminar_en_lote`, `test_la_ficha_no_tiene_boton_de_borrar`; `mod::test_borrar_un_area_con_competencias_falla` |
| Sin agregar | `adm::test_sin_url_de_agregar` |
| Campos fijos | `adm::test_ficha_del_area_solo_edita_el_orden` |
| Otro rol | `adm::test_otro_rol_llega_a_su_inicio` (Docente y Dirección) |

Además: `se_trabaja` desde la lista (`adm::test_se_trabaja_se_cambia_desde_la_lista`) y la fixture `catalogo` para pruebas transaccionales (`mig::test_fixture_catalogo_lo_vuelve_a_cargar`).

## Escenarios de `datos-demostracion`

| Escenario | Prueba |
| --- | --- |
| Demostración cargada | `demo::test_carga_las_ocho_primeras_secciones`, `test_las_otras_dieciseis_siguen_vacias`; `cmd::test_cargar_demo_imprime_el_resumen` |
| Sin datos reales | `demo::test_nombres_de_las_listas_ficticias_sin_repetir` (estudiantes y docentes) |
| Solo días de clase pasados | `demo::test_solo_dias_de_clase_pasados_del_anio`, `test_con_pocos_dias_en_el_anio_carga_los_que_hay`; una jornada por sección y fecha la garantiza `uq_jornada` (US-030) |
| Otro número de estudiantes | `demo::test_otro_numero_de_estudiantes`, `test_numero_de_estudiantes_fuera_de_rango` (0 y 61) |
| Volver a cargar | `demo::test_volver_a_cargar_no_crea_nada`, `test_mismo_resultado_en_cada_carga` |
| Sin año abierto | `demo::test_sin_anio_abierto_no_crea_nada` |
| Sección con docente real | `demo::test_seccion_con_docente_real_niega_toda_la_carga` (2.° B), `test_seccion_con_estudiantes_sin_docente_demo_niega_la_carga`; `cmd::test_cargar_demo_negada_es_error_del_comando` |
| Producción sin confirmar | `cmd::test_cargar_demo_fuera_de_desarrollo_sin_confirmar`, `test_cargar_demo_con_confirmar_fuera_de_desarrollo` |
| Ingreso con una cuenta demo | `demo::test_cuenta_demo_ingresa_a_su_portada`, `test_cuentas_demo_docentes_de_la_institucion` |
| Cuenta real con un usuario de la lista | `demo::test_cuenta_real_con_usuario_de_la_lista_niega_la_carga` (A2), `test_cuenta_de_la_lista_ajena_niega_la_carga` (otro rol y otra institución) |
| Sin contraseña configurada | `demo::test_sin_clave_no_crea_nada`; `cmd::test_cargar_demo_sin_clave` |
| Secciones liberadas | `demo::test_quitar_libera_las_secciones_demo`; `cmd::test_quitar_demo_con_confirmar`, `test_quitar_demo_sin_confirmar_dice_lo_que_borraria` |
| Otras secciones intactas | `demo::test_quitar_no_toca_otras_secciones` |
| Cuenta real con un usuario de la lista intacta | `demo::test_quitar_no_toca_una_cuenta_real_con_usuario_de_la_lista` (A2) |
| Carga y retiro a la vez | `conc::test_quitar_durante_una_recarga_no_deja_cuentas_activas_sin_seccion` (A2), `test_primera_carga_durante_un_retiro_no_deja_secciones_con_cuentas_inactivas` (revisión del grupo 3); dos conexiones |
| Cuenta demo inactiva | `demo::test_cuenta_demo_no_ingresa_despues_de_quitar` |
| Volver a quitar | `demo::test_volver_a_quitar_no_cambia_nada`; `cmd::test_quitar_demo_sin_demo` |
| Sección descartada | `demo::test_descartar_borra_lista_y_asistencia_y_conserva_la_docente`; `cmd::test_descartar_con_confirmar` |
| Sin confirmar | `cmd::test_descartar_sin_confirmar_dice_lo_que_borraria`; `demo::test_conteos_de_una_seccion_no_borran` |
| Sección de un año cerrado | `demo::test_descartar_en_anio_cerrado_no_borra_nada` (en el servicio; sin prueba a nivel de comando, ver Minor) |

Además: reactivar una cuenta demo inactiva y rotar la clave (`demo::test_cuenta_demo_inactiva_se_reactiva_con_la_clave`, `test_volver_a_cargar_pone_la_clave_nueva`, `test_cuenta_demo_activa_sin_seccion_queda_sin_cambio_pendiente`), estados y hora de la toma (`test_estados_y_nota_de_justificado`, `test_tomas_a_las_ocho_de_su_fecha`), y cargar después de quitar (`test_cargar_despues_de_quitar_vuelve_a_llenar`).

## Revisión final (A2)

`/codex:adversarial-review --base main --background`, con foco en los specs, la migración `0002` y los comandos que borran. Veredicto: *needs-attention*, 1 hallazgo high y 1 medium, sin Minor. Los dos se corrigieron con la prueba vista en rojo (detalle en 3.1, abajo). Según su registro, Codex comparó los 30 textos de `0002` con el Excel y coinciden.

## DoD 1 a 9

| N.° | Estado | Evidencia |
| --- | --- | --- |
| 1 | Cumple en local; **pendiente del PR** | `uv run pytest --cov` desde la raíz: 1050 pasan (847 de `src/backend` más las de `scripts/`), cobertura total 98,49 % (mínimo 80 %). La puerta Sonar way solo se ve en el PR |
| 2 | Cumple en local; **pendiente del PR** | Ruff sin hallazgos (`check` y `format --check`, en `verificar.py`). CodeQL y SonarQube Cloud solo corren en el PR |
| 3 | **Pendiente del PR (equipo)** | Aprobación de otra integrante |
| 4 | **Pendiente del PR** | Vista previa de Vercel del PR, con `catalogo/0001`, `catalogo/0002` y `cuentas/0002` en su rama de Neon |
| 5 | Cumple en local; **pendiente del PR** | Cada escenario con su prueba (tablas de arriba). E2E: 244 en verde (EN-06 no agrega e2e: no tiene pantallas). El canal se ve en el PR |
| 6 | Cumple | Reglas en `catalogo/servicios.py` e `institucion/demo.py` (módulo aparte de servicios, D6); los comandos solo leen opciones, confirman y escriben el resumen. La base impide los repetidos (`uq_competencia`, `uq_institucion_area` y los únicos de `area`) |
| 7 | No aplica | Sin pantallas propias: el catálogo se ve en el panel de Django (su pantalla es US-027) |
| 8 | Cumple | Solo nombres ficticios (`APELLIDOS` y `NOMBRES` de `demo.py`); textos del catálogo copiados del SIAGIE; ningún dato de la I.E. inventado |
| 9 | Cumple | Este cambio en OpenSpec, docstrings y la sección del README (cargar, quitar y descartar). Sin rutas nuevas: el Catálogo de rutas de `docs/03` no cambia |

## Evidencia por parte

### Grupo 1, parte A: modelos y migraciones (1.1 a 1.3)

- 1.1: `catalogo/tests/test_modelos.py` falló primero (`ImportError` de `Area`) y luego pasó (9 pruebas). `makemigrations --check` no da cambios. `sqlmigrate catalogo 0001` muestra `uq_competencia`, `uq_institucion_area` y el `UNIQUE` de `codigo_siagie` y de `nombre` en `area`.
- 1.2: `catalogo/tests/test_migracion_catalogo.py` falló primero (no existía `0002_catalogo_siagie`) y luego pasó (13 pruebas). En la base local, `migrate catalogo zero` y `migrate` funcionan, y quedan 11 áreas, 30 competencias y 11 filas de `institucion_area` para la institución local.
- 1.3: el revisor no encontró Critical ni Important. `verificar.py --antes-del-commit` PASA (cobertura 98,31 %, 978 pruebas).

### Grupo 1, parte B: áreas de cada institución y panel (1.4 a 1.6)

- 1.4: `catalogo/tests/test_servicios.py` falló primero (`ImportError` de `servicios`; luego, con `asegurar_areas` y sin la señal, 3 de 4 fallaron porque la institución nacía sin filas) y pasó con la señal (4 pruebas). Con la señal activa, `catalogo` (26) y la suite completa (982) pasan, también `test_modelos.py` (Minor 5).
- 1.5: `catalogo/tests/test_admin.py` falló primero (18 de 20; las dos de «otro rol» ya pasaban por `IngresoPanelView`) y luego pasó (20 pruebas). `uv run pytest --cov`: 1002 pruebas, cobertura 98,51 %.
- 1.6: el revisor no encontró Critical; su único Important era esta evidencia.

### Grupo 2: datos de demostración (2.1 a 2.4)

- 2.1: `institucion/tests/test_demo.py` falló primero (22 de 22, con `demo.py` vacío) y luego pasó. Dos fallas eran de la prueba y no del código: el 1-1-2027 es viernes y entra entre los días hábiles, y `last_name` se guarda en tipo título.
- 2.2: las 8 pruebas de quitar y descartar fallaron primero (`AttributeError`) y luego pasaron.
- 2.3: `institucion/tests/test_comandos_demo.py` falló primero (12 de 12, comandos inexistentes) y luego pasó. `uv run pytest --cov`: 1044 pruebas, cobertura 98,48 %.
  - En la base local, el año abierto era 2027 y hoy es 30-10-2026, así que `cargar_demo` dio «0 días de asistencia». Con la opción que eligió el equipo, se cerró 2027 en local y se cargó 2026 (`cargar_secciones --anio 2026`).
  - Con eso, `quitar_demo --confirmar` y `cargar_demo` reactivaron las 8 cuentas. `demounoa` ingresa (302 a `/docente/`) y ve la portada de 1.° A con 10 jornadas del 16 al 29 de octubre, de lunes a viernes, con 25 estados cada una y la toma a las 8:00 de Lima. El README pasa la carga inicial de producción a 2026 (decisión del equipo).
- 2.4: el revisor no encontró Critical. Encontró dos Important:
  - Una recarga no ponía la clave vigente a las cuentas demo activas ni les quitaba el cambio de contraseña pendiente, aunque el design dice que la clave se rota con una nueva carga. Se corrigió con la prueba primero: `test_volver_a_cargar_pone_la_clave_nueva` y `test_cuenta_demo_activa_sin_seccion_queda_sin_cambio_pendiente` fallaron y luego pasaron.
  - Faltaba esta evidencia.
  - Después de las correcciones, la suite completa da 1046 pruebas y 98,48 % de cobertura.

### Grupo 3: revisión final y verificación (3.1 y 3.2)

- 3.1: la revisión A2 de Codex (`--base main`, foco en los specs, la `0002` y los comandos que borran) dio `needs-attention` con dos hallazgos y ningún Minor. Según su registro, comparó los 30 textos de competencias de `0002` con el Excel y coinciden. Las dos correcciones se hicieron con la prueba primero:
  - [high] Una Docente real con usuario `demounoa` pasaba por cuenta demo: `cargar_demo` le cambiaba la clave y `quitar_demo` borraba su sección. `test_cuenta_real_con_usuario_de_la_lista_niega_la_carga` y `test_quitar_no_toca_una_cuenta_real_con_usuario_de_la_lista` fallaron y luego pasaron con `Usuario.es_demo` (`cuentas/0002`), que solo pone la carga (D8). Dos pruebas que creaban a mano una cuenta de la lista ahora le ponen la marca.
  - [medium] Un `quitar_demo` que terminaba durante una recarga dejaba 8 cuentas demo activas sin sección. `test_demo_concurrencia.py` (dos hilos, dos conexiones) lo reprodujo con ese resultado y pasó con el bloqueo de las secciones; pasó tres veces seguidas. La revisión del grupo mostró que en la primera carga el retiro no encuentra filas que bloquear: `test_primera_carga_durante_un_retiro_no_deja_secciones_con_cuentas_inactivas` falló (8 secciones con su docente demo inactiva) y pasó, tres veces seguidas, con `pg_advisory_xact_lock` en las dos operaciones, que reemplaza el bloqueo de secciones de la carga (D7, D9). `quitar_demo` cuenta ahora después de bloquear, lo que cierra también el Minor del resumen desfasado.
  - `makemigrations --check` sin cambios; `uv run pytest --cov`: 1049 pruebas, cobertura 98,48 %.
- 3.2: las tablas de escenarios y la DoD de arriba. Revisión del grupo 3: sin Critical ni Important; 6 Minor. Se corrigieron el de la primera carga con el retiro (por decisión de Marco, con su prueba vista en rojo) y el docstring de `serialized_rollback`; el número de pruebas se aclaró (847 de `src/backend` más `scripts/`) y la casilla 3.2 se marcó; los otros dos van abajo.

## Minor para la descripción del PR

- La prueba con `MigrationExecutor` (`test_migracion_catalogo.py`) vuelve a `catalogo 0001` y solo reaplica `catalogo 0002`. Cuando una migración de otra app dependa de `catalogo` (US-027, US-028, US-020), conviene terminar la prueba migrando a `executor.loader.graph.leaf_nodes()`.
- La fixture `catalogo` reproduce solo la carga de `0002`. Si una migración futura corrige un texto, la fixture tiene que aplicar también esa corrección, porque si no crea la competencia vieja como nueva.
- Las pruebas comparan unos 7 de los 30 textos de competencias, que es lo que pide la tarea. Comparar la lista completa detectaría un cambio accidental en `0002`.
- No hay prueba de `RESTRICT` en `InstitucionArea.area`: la tarea 1.1 solo lo pide para `Competencia.area`.
- En `test_modelos.py`, que las pruebas no dependan de la señal de la parte B se basa en el orden de los argumentos `(institucion, area)`.
- En `conftest.py`, `from django.apps import apps` va dentro de la fixture y no arriba (estilo).
- «Campos fijos» se prueba solo en la ficha del área, como pide el spec; que `area` y `nombre` de la competencia, e `institucion` y `area` de la fila, sean de solo lectura no tiene prueba.
- «Otro rol» se prueba solo con `/admin/catalogo/area/`; las otras dos listas las cubre el mismo `IngresoPanelView`.
- `test_sin_accion_eliminar_en_lote` no revisa el código de la respuesta del POST, solo que el objeto siga existiendo.
- `ignore_conflicts=True` en `asegurar_areas` callaría también otro conflicto de unicidad de `institucion_area`; hoy solo existe `uq_institucion_area`.
- `descartar_seccion` sin `--confirmar` sobre un año CERRADO dice «Se borraría…», aunque con `--confirmar` se negaría; no hay prueba del año cerrado a nivel de comando.
- `quitar_demo` sin demo y sin `--confirmar`, y `cargar_demo` con la demo ya cargada fuera de desarrollo y sin `--confirmar`, imprimen un plan que se contradice («Se borraría: No hay demostración…», «Se cargaría: La demostración ya está cargada…»).
- Dos `cargar_demo` a la vez: `importar_lista` lanza `SeccionConEstudiantes`, que no se convierte en `CommandError` (traceback; la transacción revierte igual).
- No se valida la fuerza de `DEMO_CLAVE` (`password_validation.validate_password`).
- El docstring de `demo.py` dice que cada función corre en una transacción; `planear_demo`, `conteos_*` y `secciones_demo` solo leen.
- El README no dice de dónde sacar el id de `--institucion` (panel o `shell`).
- `cuentas/0002` no marca las cuentas demo que ya existen (marcarlas por nombre reabriría el hallazgo high de la A2): quien cargó la demo en local antes de esta migración tiene que recrear su base local o marcarlas a mano. En Neon no hay demo todavía.
- `es_demo` no se ve en la ficha del panel de cuentas; mostrarlo como solo lectura ayudaría a distinguirlas.
- Revisión del bloqueo (sin Critical ni Important): `cargar_demo` ya no bloquea las filas de las 8 secciones; un `importar_lista` o un cambio de docente en el panel podría colarse entre el plan y la asignación (casi imposible: una sección sin docente no recibe listas). Se cierra con `select_for_update(of=("self",))` en `planear_demo` después de `_en_fila()`.
- `test_demo_concurrencia.py` depende de `join(1)`: sin el bloqueo, solo falla si el otro hilo confirma en menos de 1 s. Un `assert ….is_alive()` después del `join(1)` lo haría independiente de la velocidad.
