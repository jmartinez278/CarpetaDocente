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
- Pruebas existentes ajustadas por D5: la barra ya no es "sin menú" y las pantallas cargan `menu.js` (la dirección ya no está sin scripts; la portada tiene tres).
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
  - `menu.js`: el menú no se cierra al salir con Tab; el `pageshow` recarga también pantallas con sesión viva (pierde el estado de Alpine) y esa ruta de bfcache no tiene prueba en Chromium headless (queda con EN-07).
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
