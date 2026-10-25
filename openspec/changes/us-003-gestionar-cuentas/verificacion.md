# Verificación de US-003

Rama: `feature/US-003-gestionar-cuentas` · Laptop Windows 11 con Docker Desktop · Django 5.2.

Las pruebas están en `src/backend/cuentas/tests/`. Abreviaturas: `adm` = `test_admin.py`, `srv` = `test_servicios_usuario.py`, `ing` = `test_ingresar.py`, `bk` = `test_backend.py`, `blq` = `test_servicios_bloqueo.py`, `e2e` = `test_gestion_cuentas_e2e.py`.

## Revisión final A2 (Codex)

Fecha: 25/10/2026. `/codex:adversarial-review --base main --background`, con foco en los specs del cambio: veredicto `needs-attention`, un High y un Medium.

- **High, cuentas existentes con mayúsculas:** sin migración, porque solo hay datos ficticios; una cuenta creada antes con mayúsculas se recrea o se pasa a minúsculas a mano (D7).
- **Medium, número en el usuario sin que la base exista:** el spec se alineó con D1 (se valida la forma y se propone; el Administrador decide). El código no cambió.
- Sin pendientes de Critical ni Important. Minor nuevos: ninguno.

## Escenarios de `gestion-cuentas` (19)

| Escenario | Evidencia |
| --- | --- |
| Alta: camino ideal | `adm::test_alta_desde_el_panel_crea_docente_activo_y_muestra_cuenta_creada`; `e2e::test_el_administrador_crea_una_docente_que_ingresa_y_luego_la_desactiva` |
| Dato obligatorio vacío | `adm::test_alta_con_un_obligatorio_vacio_no_crea_la_cuenta`, `test_alta_de_docente_sin_institucion_senala_el_campo` |
| Sin opción de cuenta sin contraseña | `adm::test_el_alta_no_ofrece_crear_la_cuenta_sin_contrasena` |
| La cuenta creada no entra al panel | `adm::test_la_cuenta_creada_en_el_panel_no_entra_al_panel` |
| Intento de crear un Administrador | `adm::test_el_alta_rechaza_el_rol_administrador` |
| Roles ofrecidos | `adm::test_formulario_de_alta_incluye_rol_e_institucion` |
| Usuario repetido | `adm::test_usuario_repetido_dice_que_ya_existe_y_propone_el_siguiente` |
| Usuario repetido con otras mayúsculas | `srv::test_compara_sin_distinguir_mayusculas`; `adm::test_formato_invalido_explica_el_ejemplo` (las mayúsculas se rechazan por el formato) |
| Formato inválido | `adm::test_formato_invalido_explica_el_ejemplo`, `test_el_usuario_explica_el_formato`; `srv::test_usuario_valido_rechaza_lo_que_no_cumple` |
| Usuario con número | `adm::test_usuario_con_numero_se_acepta`; `srv::test_usuario_valido_acepta_el_formato` |
| Sugerencia del siguiente libre | `adm::test_usuario_repetido_dice_que_ya_existe_y_propone_el_siguiente`; `srv::test_salta_los_numeros_ocupados` |
| Sugerencia con tilde o ñ | `adm::test_la_sugerencia_parte_de_los_nombres_con_tilde_y_enie`; `srv::test_con_tilde_y_enie`, `test_usuario_base_es_inicial_mas_primer_apellido_sin_tildes` |
| Editar los nombres | `adm::test_corregir_los_apellidos_conserva_usuario_y_contrasena`, `test_la_edicion_permite_cambiar_nombres_rol_institucion_y_activo`, `test_el_usuario_es_de_solo_lectura_en_la_edicion` |
| Campos ocultos | `adm::test_la_edicion_no_muestra_privilegios_ni_cambio_obligatorio`, `test_un_post_no_puede_dar_privilegios_en_la_edicion`, `test_intentos_y_bloqueo_son_de_solo_lectura_en_el_formulario` |
| Rol de un Administrador | `adm::test_el_rol_de_un_administrador_es_de_solo_lectura`, `test_la_edicion_rechaza_asignar_el_rol_administrador` |
| Docente que ya no trabaja | `adm::test_una_cuenta_desactivada_no_ingresa_y_sigue_en_la_lista`; `e2e` (la desactiva) |
| Sesión abierta de una cuenta desactivada | `adm::test_la_sesion_abierta_de_una_cuenta_desactivada_lleva_a_ingresar` |
| No existe la opción de eliminar | `adm::test_el_panel_no_ofrece_eliminar_cuentas`, `test_una_peticion_directa_de_eliminacion_se_rechaza`, `test_la_accion_de_eliminar_varias_se_rechaza` |
| Docente o dirección en la gestión de cuentas | `adm::test_docente_y_direccion_no_ven_la_gestion_de_cuentas` |

## Escenarios del delta `inicio-sesion` (11)

| Escenario | Evidencia |
| --- | --- |
| Camino ideal del docente | `ing::test_cada_rol_llega_a_su_pantalla` |
| Ingreso de la dirección | `ing::test_cada_rol_llega_a_su_pantalla` |
| Ingreso del administrador | `ing::test_cada_rol_llega_a_su_pantalla` |
| Campos vacíos | `ing::test_campos_vacios_muestran_su_mensaje_sin_contar_un_intento` |
| Usuario con mayúsculas | `ing::test_usuario_con_mayusculas_entra_y_llega_a_su_pantalla`; `bk::test_el_usuario_con_mayusculas_entra_en_la_cuenta_en_minusculas`; `e2e` |
| Quinto intento fallido | `blq::test_quinto_fallo_bloquea_15_minutos_y_reinicia_el_conteo` |
| Contraseña correcta durante el bloqueo | `ing::test_cuenta_bloqueada_rechaza_la_contrasena_correcta_con_el_mismo_mensaje`; `bk::test_cuenta_bloqueada_con_la_clave_correcta_devuelve_none` |
| Intentos durante el bloqueo | `blq::test_durante_el_bloqueo_nada_entra_ni_cuenta` |
| Fin del bloqueo | `blq::test_a_los_14_59_sigue_bloqueada_y_a_los_15_00_entra` |
| Primer fallo después del bloqueo | `blq::test_primer_fallo_despues_del_bloqueo_no_vuelve_a_bloquear` |
| Intentos con otras mayúsculas | `ing::test_cinco_rechazos_con_distintas_mayusculas_bloquean_la_cuenta`; `bk::test_cinco_fallos_con_distintas_mayusculas_bloquean_la_misma_cuenta` |

## Escenarios del delta `pantallas-de-inicio` (3)

| Escenario | Evidencia |
| --- | --- |
| Contenido de la pantalla | `ing::test_la_pantalla_de_ingreso_responde`; `test_plantillas.py::test_plantilla_sin_colores_ni_estilos_en_linea` |
| Pista del campo Usuario | `ing::test_la_pista_va_bajo_el_campo_usuario_y_lo_describe`, `test_el_campo_contrasena_no_tiene_pista` |
| Mensaje de error sobre el formulario | `ing::test_los_cuatro_rechazos_dan_el_mismo_mensaje_en_dos_lineas`, `test_con_un_error_el_campo_describe_la_pista_y_el_error` |

Total: 33 escenarios, ninguno sin prueba.

## Suite

- `uv run pytest --cov`: 489 pasan, cobertura 97,23 %.
- `uv run pytest -m e2e --browser chromium` (CSS compilado, `DJANGO_ALLOW_ASYNC_UNSAFE=true`): 84 pasan.
- `uv run ruff check .` y `uv run ruff format --check .`: sin hallazgos.

## DoD 1 a 9

| N.° | Estado | Evidencia |
| --- | --- | --- |
| 1 | Cumple en local; **pendiente del PR** | 97,23 % (mínimo 80 %). La puerta Sonar way solo se ve en el PR |
| 2 | Cumple en local; **pendiente del PR** | Ruff sin hallazgos. CodeQL y SonarQube Cloud solo corren en el PR |
| 3 | **Pendiente (equipo)** | Aprobación de otra integrante en el PR |
| 4 | No aplica hasta EN-02 | Vista previa de Vercel |
| 5 | Cumple en local; **pendiente del PR** | Los escenarios de las tablas pasan; ruta ideal: `e2e`; 84 e2e en verde. El canal se ve en el PR |
| 6 | Cumple | RN-024 con pruebas propias en la capa de servicios (`blq`) y en el backend (`bk`); formato del usuario en `srv` |
| 7 | Parcial | Los 32 casos de axe de `/ingresar/` (incluida la pista) ya existen y pasan. Las pantallas del panel de Django no tienen informe de axe propio |
| 8 | Cumple | Solo datos ficticios (usuarios de `conftest.py` y del `e2e`); ningún dato de la I.E. inventado |
| 9 | Cumple | Este cambio en OpenSpec y docstrings. Ninguna ruta cambia, así que el Catálogo de rutas y el README no se tocan |

## Minor

Ninguno nuevo de la revisión A2. Los de los grupos 1 y 2 van a la descripción del PR.
