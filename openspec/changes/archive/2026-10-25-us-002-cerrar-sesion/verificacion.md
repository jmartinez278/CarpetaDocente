# Verificación de US-002

Rama: `feature/US-002-cerrar-sesion` · Laptop Windows 11 con Docker Desktop · Django 5.2.

## Grupo 1. Backend: inactividad, cierre y caché

### 1.1 Regla de inactividad (RN-025)

- `cuentas/tests/test_servicios_inactividad.py`: 59:59 no vence, 60:00 vence, más de 60 minutos vence, una sesión sin marca no vence, y el aviso toma los minutos de `INACTIVIDAD_MAXIMA` (no hay un 60 escrito a mano en el texto).
- Rojo primero: 5 pruebas fallaban porque `sesion_vencida` no existía; luego 6 en verde.

### 1.2 Middleware de inactividad

- `cuentas/tests/test_inactividad.py` (8 pruebas): GET vencido a `/ingresar/?next=…`; POST vencido a `/ingresar/` sin `next`; mensaje con la etiqueta `inactividad`; a los 59 minutos se ve la pantalla y la marca se renueva; sesión sin marca la recibe; anónimo sin cambios; panel y dirección.
- Escenario **"El aviso no se repite"**: depende de que `ingresar.html` muestre el mensaje (grupo 2). Con el cliente de Django, leer `context["messages"]` no lo consume, así que la prueba queda en 2.1/2.2.

### 1.3 Cierre y caché

- `cuentas/tests/test_salir.py` (10 pruebas): POST a `/salir/` cierra y lleva a `/ingresar/` sin aviso; la dirección también; GET da 405 y deja la sesión; POST sin token CSRF da 403 y deja la sesión; POST sin sesión lleva a `/ingresar/`; `/admin/logout/` lleva a `/ingresar/`; `/docente/`, `/direccion/` y `/admin/` responden con `no-store`; tras el cierre, `/docente/` lleva a `/ingresar/?next=/docente/`.
- **D2:** con `LOGOUT_REDIRECT_URL = "ingresar"` la prueba del panel pasa; **no hizo falta la alternativa de D2** (enrutar `/admin/logout/` a la vista propia).
- `uv run pytest --cov`: 394 pasan, cobertura 97,01 %.

### 1.4 Documentación

- Catálogo de rutas a la 1.2.0, con `/salir/` y `/admin/logout/`, la nota de inactividad y caché y la fila 1.2.0 del historial. El archivo no lleva la versión en el nombre, así que `subir_version.py` no aplica: se editó a mano.
- `clearsessions` y la prueba de bfcache en iPhone anotados en `insumos/pendientes-docs.md`.

### Revisión del grupo 1: Minor (no se corrigen ahora)

- Sin Critical ni Important.
- Corregidos antes del commit, por ser evidencia de un escenario del spec: la prueba de "Envío después de la inactividad" con `Client(enforce_csrf_checks=True)` (302 a `/ingresar/`, no 403; Risk de D3) y la comprobación de `no-store` en la redirección por inactividad.
- Un GET vencido a `/salir/` deja `?next=/salir/`; tras ingresar da 405. Caso raro; opcional no poner `next` en esa ruta.
- HTMX: cuando existan vistas parciales con sesión, responder `HX-Redirect` si llega `HX-Request`.
- La marca se guarda en cada petición (aceptado en Risks de D1); guardar solo si pasó más de un minuto si pesa.
- `sesion_vencida` daría `TypeError` con una marca no numérica (teórico: la sesión va firmada).
- El aviso viaja como un solo mensaje con salto de línea; `ingresar.html` (grupo 2) debe separar las dos líneas.

## Grupo 2. Interfaz: menú, aviso, punta a punta y axe

### 2.1 Plantillas

- `test_pantallas.py`: la barra de la portada y de la dirección lleva `<details data-menu-cuenta>` con el nombre (o el usuario si no tiene nombre) y un formulario POST a `/salir/` con token CSRF; `ingresar.html` muestra el aviso (`.mensaje--aviso`, `role="status"`, ícono `clock`, dos líneas) sobre el formulario solo tras la inactividad, y no se repite al recargar ni aparece tras un cierre elegido o un ingreso normal. Cubre "El aviso no se repite", que quedó pendiente del grupo 1.
- Pruebas existentes ajustadas por D5: la barra ya no es "sin menú" y las pantallas cargan `menu.js` y `bfcache.js` (la dirección ya no está sin scripts; la portada tiene cuatro).
- `test_plantillas.py`: los tres íconos Lucide nuevos (`circle-user-round`, `log-out`, `clock`) y ningún color hexadecimal ni estilo en línea.
- El aviso viaja como un mensaje con dos párrafos (`\n\n`) que la plantilla muestra con `linebreaks`.
- `npm run build` sin errores.

### 2.2 Punta a punta

`test_cerrar_sesion_e2e.py` (6 pruebas, Chromium): camino ideal; "atrás" tras cerrar sesión llega a `/ingresar/?next=/docente/` sin el saludo; inactividad con la marca envejecida, aviso visible y "atrás"/"adelante" sin la pantalla; Escape cierra el menú y devuelve el foco; un toque fuera lo cierra; sin JavaScript el menú abre y cierra la sesión. Playwright no da rol de botón al `<summary>`, así que la prueba lo busca por su nombre accesible. Suite e2e completa: 81 pasan.

### 2.3 axe y ancho

- `test_accesibilidad_e2e.py`: 8 vistas × 2 temas × 2 anchos = 32 combinaciones, sin `critical` ni `serious`. No falló el contraste de `--color-aviso`: **no hay diff de DESIGN.md**.
- 8 pruebas de ancho (portada y dirección, 320 y 360 px, ambos temas) con el menú abierto: el documento no supera la ventana y el panel queda dentro de ella.
- axe solo guarda informe en `test-results/` cuando hay infracciones; no hubo.

### 2.4 Deuda para el pulido (D5)

Lo que DESIGN.md no fija del menú, resuelto con tokens existentes y a revisar en el pulido:
- Panel: 256 px de ancho (máximo `100vw − 32px`), `--color-superficie`, borde `--color-linea`, radio 12 px, `--shadow-ficha`, a 8 px bajo el botón.
- Botón abierto: relleno `--color-dimension`.
- "Cerrar sesión": botón de 44 px con borde `--color-borde`, ícono `log-out` y texto en `--color-primario` 600.
- Sin animación de apertura.
- La fila "Menú de la barra superior: Pendiente" de DESIGN.md sigue sin actualizarse (queda fijo hasta el pulido).
- El `<summary>` no tiene estado `hover`.

### Revisión del grupo 2

- Sin Critical. Un Important, corregido: la prueba de inactividad no ejercía el "atrás" que decía cubrir (el historial no tenía una entrada interna previa); ahora navega a una segunda entrada antes de envejecer la sesión y comprueba que "atrás" llega a `/ingresar/?next=/docente/`.
- Minor, anotados y no corregidos:
  - `ingresar.html`: `"inactividad" in mensaje.tags` es una búsqueda de subcadena; mejor `mensaje.extra_tags == "inactividad"`. La etiqueta está repetida en el middleware y en la plantilla.
  - `ingresar.html`: el `{% for mensaje in messages %}` consume todos los mensajes, no solo el de inactividad. Si se agregan otros, se perderían al pasar por `/ingresar/`.
  - `menu.js`: el menú no se cierra al salir con Tab. `bfcache.js`: el `pageshow` persistido recarga también pantallas con sesión viva (pierde el estado de Alpine); se prueba en Chromium simulando el evento, y la verificación en Safari queda con EN-07.
  - `menu_cuenta.html`: el `<script>` va dentro del componente; si se incluyera dos veces duplicaría los listeners.
  - El nombre del panel no está asociado al botón (`aria-describedby`): para el pulido.
  - `[.mensaje+&]:mt-4` depende del orden de especificidad de Tailwind; el espacio entre el aviso y un error del formulario queda sin probar.

### Contraste del aviso y Impeccable

- La captura que midió 1,96:1 (título) y 3,11:1 (texto) salió a media animación: `.mensaje` entra con una animación de opacidad de 180 ms. Con la animación terminada, el color calculado sobre `--color-superficie` da:

  | Tema | Título e ícono (`--color-aviso`) | Texto (`--color-texto`) |
  | --- | --- | --- |
  | Claro | 4,82:1 | 16,81:1 |
  | Oscuro | 7,31:1 | 11,42:1 |

  Todo supera 4,5:1: no se cambió ningún color ni DESIGN.md. La prueba de axe de `ingresar-con-aviso` ahora espera a que termine la animación antes de medir, para no leer colores mezclados con la opacidad; sigue sin `critical` ni `serious` en los dos temas y los dos anchos.
- Impeccable no se corre en este cambio: queda para el pulido final, junto con la deuda del panel del menú (D5).

## Grupo 3. Revisión final y verificación

### 3.1 Revisión final A2 (Codex): dos Important, corregidos con prueba primero

Fecha: 25/10/2026. `/codex:adversarial-review --base main --background`, con foco en los specs del cambio: veredicto `needs-attention`, dos Important, ningún Critical.

**Hallazgo 1. El ingreso dejaba la sesión sin reloj de inactividad.** El POST de ingreso llega como anónimo y el middleware lo devuelve antes de marcar; la sesión nueva no tenía `ultima_actividad` hasta otra petición, y `sesion_vencida(None)` no vence. Quien recibía la cookie y cortaba la redirección podía volver pasados 60 minutos.
- Prueba primero, `test_inactividad.py::test_el_ingreso_real_inicia_el_reloj_y_a_los_60_minutos_la_primera_consulta_se_rechaza`: POST real a `/ingresar/` sin seguir la redirección, con la hora fijada por `monkeypatch`; a los 60 minutos, el primer GET a `/docente/` lleva a `/ingresar/?next=/docente/`. Rojo: `KeyError: 'ultima_actividad'`; luego verde.
- Corrección: un receptor de `user_logged_in` en `cuentas/middleware.py` guarda la marca al autenticar; `CuentasConfig.ready()` lo conecta. La excepción de las sesiones anteriores al despliegue (sin marca) se conserva y ahora tiene su propia prueba, `test_la_primera_peticion_de_una_sesion_anterior_sin_marca_la_recibe`: `force_login` ya marca la sesión, así que la prueba borra la marca.

**Hallazgo 2. El panel quedaba fuera del respaldo contra bfcache.** El respaldo vivía en `menu.js`, que solo carga el marco de las pantallas; el panel de administración no lo tenía.
- Pruebas primero: `test_pantallas.py::test_el_panel_carga_el_respaldo_de_atras_sin_el_menu` y los ajustes de la portada (cuatro scripts) y de la dirección (`menu.js`, `bfcache.js`); y dos e2e en Chromium, `test_cerrar_sesion_e2e.py::test_panel_atras_tras_el_cierre_manual_no_muestra_la_pantalla` (otra pestaña cierra la sesión desde el panel; la primera recibe un `pageshow` persistido y llega a `/ingresar/?next=/admin/`) y `test_panel_atras_tras_la_inactividad_no_muestra_la_pantalla` (marca envejecida, mismo evento, llega a `/ingresar/` con el aviso). Rojo: las tres de plantilla y las dos e2e se quedaban en la pantalla guardada; luego verde.
- Corrección: `static/js/bfcache.js` (el `pageshow` persistido que estaba en `menu.js`, sin depender del menú); el marco lo carga después de `menu.js` y `templates/admin/base_site.html` (extiende el de Django) lo carga en el panel. Sin WebKit en la suite: la verificación en Safari queda en la prueba pendiente del iPhone (EN-07).

**Suite tras los dos cambios:** `uv run pytest --cov`: 411 pasan, cobertura 97,03 %. `uv run pytest -m e2e --browser chromium`: 83 pasan. Ruff (`check` y `format --check`): sin hallazgos.

### 3.2 Evidencia por escenario y DoD

Las pruebas están en `src/backend/cuentas/tests/`. En las tablas: `inactividad` es `test_inactividad.py`, `salir` es `test_salir.py`, `pantallas` es `test_pantallas.py`, `servicios` es `test_servicios_inactividad.py`, `acc` es `test_accesibilidad_e2e.py` y e2e es `test_cerrar_sesion_e2e.py`.

#### Escenarios de `cierre-sesion` (20)

| Escenario | Evidencia | Estado |
| --- | --- | --- |
| Cerrar sesión: camino ideal | `salir::test_post_cierra_la_sesion_y_lleva_a_ingresar_sin_aviso`; e2e `test_camino_ideal_abre_el_menu_y_cierra_la_sesion` | Verificado |
| Cerrar sesión: dirección | `salir::test_la_direccion_tambien_cierra_sesion` | Verificado |
| Pedido GET | `salir::test_get_responde_405_y_deja_la_sesion`; `test_post_sin_token_csrf_se_rechaza_y_deja_la_sesion` | Verificado |
| Sin sesión | `salir::test_post_sin_sesion_lleva_a_ingresar` | Verificado |
| Administrador cierra sesión en el panel | `salir::test_el_cierre_del_panel_lleva_a_ingresar` | Verificado |
| Petición a los 59 minutos | `inactividad::test_a_los_59_minutos_ve_la_pantalla_y_la_marca_se_renueva`; `servicios` (59:59 no vence) | Verificado |
| Petición a los 60 minutos | `inactividad::test_un_get_vencido_termina_la_sesion_y_conserva_next`; `test_el_ingreso_real_inicia_el_reloj_y_a_los_60_minutos_la_primera_consulta_se_rechaza`; `servicios` (60:00 vence) | Verificado |
| Volver a la pantalla pedida | `inactividad::test_un_get_vencido_termina_la_sesion_y_conserva_next` (`next=/docente/`); `test_ingresar.py::test_next_seguro_lleva_a_la_pagina_pedida` | Verificado |
| Envío después de la inactividad | `inactividad::test_un_post_vencido_lleva_a_ingresar_sin_next`, `test_un_envio_vencido_sin_token_csrf_llega_a_ingresar_y_no_da_403`; `pantallas::test_un_envio_tras_la_inactividad_muestra_el_aviso` | Verificado |
| Panel de administración (inactividad) | `inactividad::test_en_el_panel_la_inactividad_cierra_la_sesion`; e2e `test_panel_atras_tras_la_inactividad_no_muestra_la_pantalla` | Verificado |
| Aviso tras la inactividad | `pantallas::test_el_aviso_va_sobre_el_formulario_con_icono_y_dos_lineas`; `inactividad::test_deja_el_aviso_con_la_etiqueta_inactividad`; e2e `test_inactividad_muestra_el_aviso_y_atras_no_muestra_la_pantalla` | Verificado |
| El aviso no se repite | `pantallas::test_el_aviso_no_se_repite_al_recargar` | Verificado |
| Cierre elegido (sin aviso) | `salir::test_post_cierra_la_sesion_y_lleva_a_ingresar_sin_aviso`; `pantallas::test_sin_inactividad_no_hay_aviso`; e2e camino ideal (`.mensaje--aviso` en 0) | Verificado |
| Botón "atrás" tras cerrar sesión | `salir::test_las_pantallas_con_sesion_responden_sin_cache`, `test_despues_del_cierre_el_docente_lleva_a_ingresar_con_next`; e2e `test_atras_despues_de_cerrar_sesion_no_muestra_el_saludo`, `test_panel_atras_tras_el_cierre_manual_no_muestra_la_pantalla` | Verificado en Chromium; Safari **pendiente** (EN-07) |
| Botón "atrás" tras el cierre por inactividad | e2e `test_inactividad_muestra_el_aviso_y_atras_no_muestra_la_pantalla`, `test_panel_atras_tras_la_inactividad_no_muestra_la_pantalla` | Verificado en Chromium; Safari **pendiente** (EN-07) |
| Abrir el menú | `pantallas::test_la_barra_lleva_el_menu_con_el_nombre_y_cerrar_sesion`, `test_el_menu_muestra_el_usuario_si_no_tiene_nombre`; e2e camino ideal (nombre visible) | Verificado |
| Teclado | e2e `test_escape_cierra_el_menu_y_devuelve_el_foco` | Verificado |
| Toque fuera del menú | e2e `test_un_toque_fuera_cierra_el_menu` | Verificado |
| Sin JavaScript | e2e `test_sin_javascript_el_menu_abre_y_cierra_la_sesion` | Verificado |
| Menú abierto a 320 px | `acc::test_el_menu_abierto_no_desborda_la_ventana` (320 y 360 px, ambos temas, portada y dirección) | Verificado |

#### Escenarios del delta `pantallas-de-inicio` (2)

| Escenario | Evidencia | Estado |
| --- | --- | --- |
| Barra y pie | `pantallas::test_la_barra_lleva_el_menu_con_el_nombre_y_cerrar_sesion`; e2e camino ideal | Verificado |
| Revisión de cada pantalla (axe) | `acc::test_sin_infracciones_graves_de_accesibilidad`: 8 vistas × 2 temas × 2 anchos = 32 combinaciones, sin `critical` ni `serious` | Verificado |

Total: 22 escenarios, ninguno sin prueba. Dos dependen de Safari (EN-07) en su parte de bfcache: el spec los cubre con el respaldo de D3, no con una prueba en WebKit.

#### DoD 1 a 9

| N.° | Estado | Evidencia |
| --- | --- | --- |
| 1 | Cumple en local; **pendiente del PR** | 97,03 % (mínimo 80 %). La puerta Sonar way solo se ve en el PR |
| 2 | Cumple en local; **pendiente del PR** | Ruff sin hallazgos. CodeQL y SonarQube Cloud solo corren en el PR |
| 3 | **Pendiente (equipo)** | Aprobación de otra integrante en el PR |
| 4 | No aplica hasta EN-02 | Vista previa de Vercel |
| 5 | Cumple en local; **pendiente del PR** | Los escenarios de las tablas pasan; ruta ideal: e2e `test_camino_ideal_abre_el_menu_y_cierra_la_sesion`; 83 e2e en verde. El canal se ve en el PR |
| 6 | Cumple | RN-025 con pruebas propias en la capa de servicios (`test_servicios_inactividad.py`) y en el middleware (`test_inactividad.py`) |
| 7 | Cumple | Informe de axe: 32 combinaciones sin `critical` ni `serious` (grupo 2, 2.3) |
| 8 | Cumple | Solo datos ficticios (usuarios de `conftest.py`) y contraseñas generadas por cada prueba; ningún dato de la I.E. inventado |
| 9 | Parcial | Este cambio en OpenSpec, docstrings y catálogo de rutas 1.2.0. README y docs/01 a 03 quedan para la pasada final (`insumos/pendientes-docs.md`) |

#### Minor de la revisión final

Ninguno nuevo. Los Minor de los grupos 1 y 2 siguen en sus secciones y van a la descripción del PR (`insumos/pr-us002.md`).
