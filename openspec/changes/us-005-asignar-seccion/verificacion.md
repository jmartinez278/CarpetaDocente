# Verificación de US-005

Rama: `feature/US-005-asignar-seccion` · Laptop Windows 11 con Docker Desktop · Django 5.2.

Las pruebas están en `src/backend/institucion/tests/`. Abreviaturas: `mod` = `test_modelos_anio_seccion.py`, `srv` = `test_servicios.py`, `adm` = `test_admin.py`, `crg` = `test_cargar_secciones.py`, `e2e` = `test_asignar_seccion_e2e.py`, `pan` = `cuentas/tests/test_pantallas.py`.

## Grupo 1: modelos, migración, panel y regla D3

- `sqlmigrate institucion 0002`: `uq_anio_escolar`, `uq_anio_escolar_abierto` (índice único parcial `WHERE estado = 'ABIERTO'`), `ck_anio_escolar_anio`, `ck_anio_escolar_estado`, `uq_seccion` y `ck_seccion_grado`. `makemigrations --check`: sin cambios.
- Al cierre del grupo 1: `uv run pytest --cov` con cobertura total 97,5 % (`institucion` 100 %). La cifra final está en la DoD.
- Pruebas que pasaron desde el inicio: en `srv`, las 8 de asignaciones válidas (camino ideal, dos secciones, mismo docente, dos pasos, docente desactivada que se conserva o se quita), porque `save()` sin la regla ya las aceptaba. Fijan que la regla de D3 no las rompa.
- La concurrencia de dos Administradores se prueba con una copia desactualizada (`srv::test_seccion_ocupada_rechaza_una_copia_desactualizada`); el bloqueo con `select_for_update` no se prueba con dos transacciones reales.
- Agregado en la aplicación (consulta a Context7): un `ModelForm` no valida una restricción con un campo que no está en el formulario. Como el año es de solo lectura en la ficha, `FormularioFichaSeccion.clean` revisa la sección repetida (`adm::test_cambiar_a_una_seccion_repetida_muestra_un_error`).

## Escenarios de `asignacion-secciones`

| Escenario | Evidencia |
| --- | --- |
| Segundo año abierto | `adm::test_segundo_anio_abierto_muestra_el_mensaje_y_no_se_guarda`; `mod::test_segundo_anio_abierto_no_pasa_la_validacion` |
| Segundo año abierto fuera del panel | `mod::test_segundo_anio_abierto_lo_rechaza_la_base_de_datos` |
| Años cerrados | `mod::test_varios_anios_cerrados_y_uno_abierto_se_aceptan` |
| Año repetido | `mod::test_anio_repetido_en_la_institucion_se_rechaza` |
| Grado fuera de rango | `mod::test_grado_fuera_de_rango_se_rechaza` |
| Sección repetida | `mod::test_seccion_repetida_en_el_anio_se_rechaza`; `adm::test_cambiar_a_una_seccion_repetida_muestra_un_error` |
| Docente y dirección sin acceso | `adm::test_docente_y_direccion_no_ven_las_secciones_ni_los_anios` |
| Lista del campo | `adm::test_la_lista_del_docente_muestra_solo_docentes_activas_de_la_institucion`, `test_la_ficha_tiene_el_docente_de_aula_y_el_anio_de_solo_lectura` |
| Asignación inválida fuera del panel | `srv::test_no_se_asigna_una_cuenta_de_la_direccion`, `test_no_se_asigna_una_cuenta_desactivada`, `test_no_se_asigna_una_docente_de_otra_institucion`, `test_no_se_crea_una_seccion_con_una_cuenta_no_elegible` |
| Docente asignada que se desactiva | `adm::test_la_ficha_muestra_a_la_docente_guardada_aunque_este_inactiva`, `test_la_ficha_con_docente_inactiva_se_guarda_sin_cambios`, `test_la_ficha_con_docente_inactiva_se_puede_vaciar`, `test_la_docente_inactiva_no_aparece_en_otras_secciones`; `srv::test_docente_asignada_y_luego_desactivada_se_conserva`, `test_docente_asignada_y_luego_desactivada_se_puede_quitar` |
| Camino ideal | `adm::test_asignar_una_docente_en_la_ficha_la_guarda`; `srv::test_asignar_una_docente_a_una_seccion_vacia`. La portada: `e2e::test_el_administrador_asigna_la_seccion_y_la_docente_la_ve` |
| Docente con dos secciones | `srv::test_una_docente_puede_tener_dos_secciones` |
| Caso de error | `adm::test_seccion_ocupada_muestra_el_mensaje_y_no_guarda_nada`; `srv::test_seccion_ocupada_rechaza_a_otra_docente_por_la_validacion` |
| Asignación fuera del panel | `srv::test_seccion_ocupada_rechaza_a_otra_docente_por_el_orm`, `test_seccion_ocupada_rechaza_una_copia_desactualizada` |
| Mismo docente | `srv::test_guardar_el_mismo_docente_no_da_error`; `adm::test_la_ficha_con_docente_inactiva_se_guarda_sin_cambios` |
| Flujo alternativo válido | `srv::test_cambio_de_seccion_en_dos_pasos_conserva_la_original`. La portada del flujo de dos pasos no tiene prueba propia (Minor); la prueba con estudiantes: US-006 |
| Primera carga | `crg::test_primera_carga_informa_lo_creado`; `srv::test_primera_carga_crea_el_anio_abierto_y_24_secciones` |
| Carga repetida | `crg::test_carga_repetida_informa_que_no_creo_nada`, `test_anio_existente_informa_solo_las_secciones_creadas`; `srv::test_carga_repetida_no_duplica_nada`, `test_carga_completa_las_secciones_que_faltan` |
| Año cerrado u otro año abierto | `crg::test_anio_cerrado_termina_con_error`, `test_otro_anio_abierto_termina_con_error`; `srv::test_carga_rechaza_un_anio_cerrado`, `test_carga_rechaza_otro_anio_abierto` |
| Institución inexistente | `crg::test_institucion_inexistente_termina_con_error` |

Sin eliminar en el panel (design, D4): `adm::test_el_panel_no_ofrece_eliminar`.

## Escenarios de `pantallas-de-inicio`

| Escenario | Evidencia |
| --- | --- |
| Portada al entrar | `pan::test_la_portada_saluda_con_el_nombre_completo`, `test_tres_tarjetas_en_orden_con_subtitulo_e_insignia`, `test_la_linea_de_secciones_no_cambia_las_tarjetas_ni_los_chips` |
| Docente con una sección | `pan::test_la_portada_muestra_la_seccion_bajo_el_saludo_y_fuera_del_h1`; `srv::test_texto_de_una_seccion_del_docente`; `e2e::test_el_administrador_asigna_la_seccion_y_la_docente_la_ve` |
| Docente con varias secciones | `pan::test_la_portada_ordena_las_secciones_por_grado_y_nombre`; `srv::test_texto_de_dos_secciones_guardadas_en_desorden` |
| Docente sin sección | `pan::test_la_portada_sin_seccion_dice_que_aparecera`; `srv::test_texto_sin_seccion` |
| Sección de un año cerrado | `pan::test_la_portada_con_la_unica_seccion_en_un_anio_cerrado`; `srv::test_texto_con_la_unica_seccion_en_un_anio_cerrado` |

Además: `srv::test_texto_ignora_las_secciones_de_otra_docente`; axe de la portada con sección en claro y oscuro y sin desborde a 320 px (`e2e::test_la_portada_con_la_seccion_pasa_axe`, `test_la_portada_con_la_seccion_no_desborda_a_320_px`).

## DoD 1 a 9

| N.° | Estado | Evidencia |
| --- | --- | --- |
| 1 | Cumple en local; **pendiente del PR** | `uv run pytest --cov`: 375 pasan, cobertura total 97,46 % (mínimo 80 %). La puerta Sonar way solo se ve en el PR |
| 2 | Cumple en local; **pendiente del PR** | Ruff sin hallazgos (`check` y `format --check`). CodeQL y SonarQube Cloud solo corren en el PR |
| 3 | **Pendiente (equipo)** | Aprobación de otra integrante en el PR |
| 4 | No aplica hasta EN-02 | Vista previa de Vercel |
| 5 | Cumple en local; **pendiente del PR** | Los escenarios de las tablas tienen prueba; ruta ideal: `e2e`; 89 e2e en verde. El canal se ve en el PR |
| 6 | Cumple | La regla de un docente por sección y la elegibilidad viven en la capa de servicios (`srv`) y se repiten en `Seccion.save()`; el panel solo las muestra |
| 7 | Parcial | Axe de la portada con sección en claro y oscuro. Las pantallas del panel de Django no tienen informe de axe propio |
| 8 | Cumple | Solo datos ficticios (`conftest.py` y el `e2e`); ningún dato de la I.E. inventado (sin código modular) |
| 9 | Cumple | Este cambio en OpenSpec, docstrings y el README (comando `cargar_secciones`). Ninguna ruta cambia: el Catálogo de rutas no se toca |

## Minor para la descripción del PR

- Cambiar la institución de un año con secciones asignadas deja docentes de otra institución en esas secciones (la regla se valida al cambiar el docente, no el año).
- La lista y el campo "Docente de aula" muestran el usuario (aquispe), no el nombre completo.
- El filtro por año de la lista de secciones hace una consulta por año para el nombre de la institución (pocas filas).
- A2 Important 3: carrera de `cargar_secciones` con un cierre de año al mismo tiempo (`servicios.py`); revisarla con RF-009.
- A2 Minor: la portada no filtra por `anio_escolar__institucion_id` (`servicios.py`); cambiar la institución de una cuenta no revalida sus secciones.
- A2 Minor: pruebas pendientes: desempate por nombre, portada en el flujo de dos pasos, rollback de la carga, 24 combinaciones exactas y sin crear usuarios ni instituciones.
- Revisión 2.3: docstring "US-001" en `cuentas/tests/e2e.py`; `.errorlist` sin limitar a `.field-docente` en `test_asignar_seccion_e2e.py`; axe de la portada con sección solo a 360 px.
- Revisión 3.1: la prueba del `FOR UPDATE` en la ficha (`adm::test_el_post_de_la_ficha_bloquea_la_fila_de_la_seccion`) solo confirma el SQL, no la carrera real ni que ocurra dentro de `atomic`; además toma la primera consulta a `seccion`, que sería frágil si el middleware la consultara.
- Revisión 3.1: las pruebas de rol e institución cambiados (`srv`) no comprueban el mensaje `NO_ELEGIBLE`, solo el `ValidationError`; falta un comentario en `SeccionAdmin.get_object` que explique por qué duplica el de Django.
