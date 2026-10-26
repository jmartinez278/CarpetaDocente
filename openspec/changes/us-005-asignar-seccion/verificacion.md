# Verificación de US-005

Rama: `feature/US-005-asignar-seccion` · Laptop Windows 11 con Docker Desktop · Django 5.2.

Las pruebas están en `src/backend/institucion/tests/`. Abreviaturas: `mod` = `test_modelos_anio_seccion.py`, `srv` = `test_servicios.py`, `adm` = `test_admin.py`.

## Grupo 1: modelos, migración, panel y regla D3

- `sqlmigrate institucion 0002`: `uq_anio_escolar`, `uq_anio_escolar_abierto` (índice único parcial `WHERE estado = 'ABIERTO'`), `ck_anio_escolar_anio`, `ck_anio_escolar_estado`, `uq_seccion` y `ck_seccion_grado`. `makemigrations --check`: sin cambios.
- `uv run pytest --cov`: 542 pasan, cobertura total 97,5 % (`institucion` 100 %).
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
| Camino ideal | `adm::test_asignar_una_docente_en_la_ficha_la_guarda`; `srv::test_asignar_una_docente_a_una_seccion_vacia`. La parte de la portada: grupo 2 |
| Docente con dos secciones | `srv::test_una_docente_puede_tener_dos_secciones` |
| Caso de error | `adm::test_seccion_ocupada_muestra_el_mensaje_y_no_guarda_nada`; `srv::test_seccion_ocupada_rechaza_a_otra_docente_por_la_validacion` |
| Asignación fuera del panel | `srv::test_seccion_ocupada_rechaza_a_otra_docente_por_el_orm`, `test_seccion_ocupada_rechaza_una_copia_desactualizada` |
| Mismo docente | `srv::test_guardar_el_mismo_docente_no_da_error`; `adm::test_la_ficha_con_docente_inactiva_se_guarda_sin_cambios` |
| Flujo alternativo válido | `srv::test_cambio_de_seccion_en_dos_pasos_conserva_la_original`. La portada: grupo 2; la prueba con estudiantes: US-006 |
| Carga de las secciones (4 escenarios) | Grupo 2 |

Sin eliminar en el panel (design, D4): `adm::test_el_panel_no_ofrece_eliminar`.

## Escenarios de `pantallas-de-inicio`

Grupo 2.

## DoD 1 a 9

Se completa en el grupo 3.

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
