# Design: US-002 – Cerrar sesión

## Context

- US-001 dejó el ingreso por `/ingresar/` (`IngresarView`, `LOGIN_URL = "ingresar"`), la verificación de rol (`RolRequeridoMixin`) y `marco.html`, con la barra sin menú.
- Las sesiones usan la configuración por defecto de Django 5.2: base de datos, `SESSION_COOKIE_AGE` de dos semanas, sin `SESSION_SAVE_EVERY_REQUEST`. Hoy no hay cierre por inactividad.
- `/admin/logout/` es la vista de Django: muestra su página "Sesión cerrada".
- Cada pantalla carga solo los scripts que usa (D6 de US-001): el inicio de la dirección no carga Alpine.
- El diseño visual sale de DESIGN.md 0.3.1 (Barra superior, Mensaje), que queda fijo hasta el pulido.

## Goals / Non-Goals

**Goals:**
- RN-025 en la capa de servicios, con pruebas propias (DoD 6).
- Un solo punto que aplique la inactividad y la falta de caché a todas las pantallas con sesión, el panel incluido.

**Non-Goals:**
- Temporizador en el navegador que cierre la pantalla sola (ver Risks).
- Tope absoluto de la sesión distinto del que ya trae Django.

## Decisions

### D1. RN-025 en servicios y aplicada por un middleware

- **Servicio** (`cuentas/servicios.py`): `INACTIVIDAD_MAXIMA = timedelta(minutes=60)` y `sesion_vencida(ultima_actividad, ahora)`, con la hora pasada como argumento, igual que en RN-024. Vence con 60 minutos o más. Una sesión sin marca no vence: recibe la marca (pasa con las sesiones abiertas antes del despliegue).
- **Middleware** (`cuentas/middleware.py`, `InactividadMiddleware`), después de `AuthenticationMiddleware` y de `MessageMiddleware`. Con un usuario autenticado:
  - lee `ultima_actividad` de la sesión (marca de tiempo numérica, serializable en JSON);
  - si venció: `logout()`, deja el aviso (D4) y redirige a `/ingresar/`. Si la petición era GET, la redirección lleva `next` con la dirección pedida; si no, sin `next`, para no volver a un envío (spec, "Envío después de la inactividad");
  - si no venció: guarda la marca con la hora actual.
- **Alternativa descartada:** `SESSION_COOKIE_AGE = 3600` con `SESSION_SAVE_EVERY_REQUEST`. Cuando la cookie vence, el navegador la borra y el servidor no puede distinguir "venció" de "nunca entró", así que no habría aviso. Además, la regla quedaría en la configuración, sin prueba en servicios.
- **Alternativa descartada:** el paquete `django-session-timeout`, por ser una dependencia nueva para unas pocas líneas.
- `SESSION_COOKIE_AGE` sigue en el valor por defecto y sirve de tope.

### D2. Cerrar sesión con `LogoutView` y `LOGOUT_REDIRECT_URL`

- La ruta `/salir/` (nombre `salir`) usa `LogoutView` de Django, que en 5.2 solo cierra la sesión por POST.
- `LOGOUT_REDIRECT_URL = "ingresar"`. El cierre del panel también usa `LogoutView`, sin `next_page`, así que ese ajuste lo lleva a `/ingresar/`. Una prueba lo confirma (1.3). Si no alcanzara, `/admin/logout/` se enruta a la misma vista antes de `admin.site.urls`, como ya se hace con `/admin/login/`.
- El cierre elegido no deja aviso.

### D3. Pantallas con sesión sin caché

- El mismo middleware de D1 agrega `add_never_cache_headers` a cada respuesta de una petición que llegó con sesión. Así queda cubierto todo lo que exista y lo que se agregue, sin depender de que cada vista recuerde un decorador. El panel y `LoginView` ya responden sin caché.
- **Respaldo para la caché de páginas del navegador (bfcache):** `static/js/bfcache.js` recarga la página en `pageshow` cuando `event.persisted` es verdadero. Con la recarga, el servidor redirige a `/ingresar/`. Se agrega porque Safari no corre en el canal. Es un script aparte de `menu.js` (D5) para cargarlo también en el panel de administración, con `templates/admin/base_site.html`, que no tiene el menú de la cuenta (hallazgo 2 de la revisión final).
- **Alternativa descartada:** `never_cache` en `RolRequeridoMixin`, porque deja fuera las vistas que no lo usen.

### D4. Aviso de inactividad con el framework de mensajes

- El middleware deja un mensaje de nivel INFO con la etiqueta `inactividad` después del `logout()`. El almacenamiento por defecto (`FallbackStorage`) lo guarda en una cookie, así que sobrevive al vaciado de la sesión. Se muestra una sola vez.
- `ingresar.html` lo muestra sobre el formulario con el componente Mensaje de DESIGN.md:
  - variante de aviso: clase nueva `.mensaje--aviso`, con `--color-aviso`;
  - ícono Lucide `clock`;
  - `role="status"`, porque no es un error.
- Texto (spec `cierre-sesion`), en dos pesos: "Tu sesión se cerró por inactividad." y "Pasaron 60 minutos sin uso. Ingresa de nuevo para continuar."
- **Alternativa descartada:** `?motivo=inactividad` en la dirección. Cualquiera podría armar un enlace con un aviso falso, y el aviso se repetiría al recargar o al volver por el historial.

### D5. Menú de la cuenta con `<details>` y JavaScript propio mínimo

- **Componente** `componentes/menu_cuenta.html`, incluido en `marco.html`, a la derecha de la barra. Patrón de divulgación (*disclosure*): `<details>` con `<summary>`.
  - El `<summary>` mide 44 × 44 px, lleva el ícono Lucide `circle-user-round` y el nombre accesible "Menú de la cuenta".
  - El panel muestra el nombre (`get_full_name`, o el usuario) y un formulario POST a `salir` con `{% csrf_token %}` y el botón "Cerrar sesión", con el ícono `log-out`.
  - El panel se alinea al borde derecho y su ancho no pasa de `100vw − 32px` (RNF-005).
- **`static/js/menu.js`** (sin Alpine, como `ingresar.js`): Escape cierra el menú y devuelve el foco al `<summary>`; un toque fuera lo cierra. Sin JavaScript, `<details>` se abre y se cierra solo, y el formulario funciona.
- **Alternativa descartada:** desplegable de Alpine, porque la dirección no carga Alpine y cerrar sesión no debe depender de JavaScript.
- **Alternativa descartada:** `role="menu"` de ARIA, porque exige manejar las flechas, y con un nombre y un botón el patrón de divulgación es el que corresponde.
- **Diseño del panel:** solo tokens de DESIGN.md (`--color-superficie`, `--color-linea`, el radio y la sombra existentes). Lo que DESIGN.md no fija del panel se anota como deuda para el pulido, y también la fila "Menú de la barra superior: Pendiente".

### D6. Pruebas

- **Unitarias, primero la prueba:**
  - `test_servicios_inactividad.py`: 59:59 no vence; 60:00 vence; una sesión sin marca no vence.
  - `test_inactividad.py`: con el cliente de Django, escribiendo una marca vieja en la sesión, sin dependencias para congelar el tiempo. Casos: GET vencido con `next`, POST vencido sin `next`, el aviso, la renovación de la marca, el anónimo sin cambios y el panel.
  - `test_salir.py`: POST, GET con 405, sin sesión, `/admin/logout/` y las cabeceras de no caché.
- **Punta a punta** (`test_cerrar_sesion_e2e.py`): camino ideal; botón "atrás" con `page.go_back()`; inactividad, envejeciendo la marca en la sesión guardada; teclado (Escape); y sin JavaScript (`java_script_enabled=False`).
- **axe** (`test_accesibilidad_e2e.py`): se suman `ingresar-con-aviso`, `portada-menu-abierto` y `direccion-menu-abierto`. Son 8 vistas × 2 temas × 2 anchos = 32 combinaciones. También se comprueba el ancho a 320 y 360 px con el menú abierto.

### D7. Catálogo de rutas y documentación

- **Catálogo** a la versión 1.2.0:
  - fila de `/salir/` (POST, `salir`, `LogoutView`);
  - fila de `/admin/logout/` (lleva a `/ingresar/`);
  - nota sobre la inactividad y la falta de caché en todas las pantallas con sesión;
  - se quita "su cierre de sesión propio sigue hasta US-002".
- Lo que toque el README o docs/01 a 03 va a `insumos/pendientes-docs.md` y se hace en la pasada final de documentación.

### D8. Cierre

- `verificacion.md` con el formato de US-001: evidencia por escenario y DoD 1 a 9.
  - **DoD 4:** no aplica hasta EN-02.
  - **DoD 6:** cubierta por las pruebas de RN-025 en servicios.
  - **DoD 7:** el informe de axe de D6.
- **Revisión final (A2):** `/codex:adversarial-review --base main --background`, con foco en los specs del cambio. Sin crítica de diseño de Codex (A1).

## Risks / Trade-offs

- **[La pantalla sigue visible en el celular después de los 60 minutos, hasta el siguiente toque]**. La sesión ya terminó en el servidor, y cualquier toque o recarga lleva a `/ingresar/`. Un temporizador que recargue la página contaría como actividad y, con dos pestañas abiertas, mantendría viva la sesión sin uso real. → Se deja fuera. Si el piloto lo pide, la versión correcta es un pedido de estado que no cuente como actividad.
- **[Una escritura en la base por cada petición con sesión]**, para guardar la marca. → Con los 30 usuarios de RNF-001 no pesa. Si la prueba de carga lo muestra, se guarda solo si pasó más de un minuto.
- **[Quien vuelve después de dos semanas no ve el aviso]**, porque la cookie ya venció. → Ve el inicio de sesión normal. Es aceptable.
- **[Las filas de sesiones viejas se acumulan en la base].** → `clearsessions` queda para el despliegue (EN-02) y se anota en `insumos/pendientes-docs.md`.
- **[El contraste de `--color-aviso` sobre `--color-superficie` en tema claro]** no está medido en DESIGN.md para texto. → Lo comprueba axe (D6). Si falla, es un caso de accesibilidad y se propone el cambio de DESIGN.md con su diff.
- **[Safari puede guardar la página en bfcache aunque tenga `no-store`].** → Lo cubre el respaldo de D3 (`bfcache.js`, también en el panel). Chromium comprueba la recarga simulando un `pageshow` persistido; la verificación en Safari queda en la prueba pendiente del iPhone (EN-07), sin WebKit en la suite.
- **[Token CSRF vencido al pulsar "Cerrar sesión"]**, si la pestaña lleva mucho tiempo abierta. → Pasados 60 minutos, el middleware atiende la petición antes de la comprobación del token, así que se cierra la sesión y se ve el aviso. Antes de los 60 minutos, el token del formulario sigue coincidiendo con la cookie CSRF, que dura un año por defecto y no vence con la sesión.

## Migration Plan

- Sin migraciones. Las sesiones abiertas reciben la marca en su siguiente petición (D1).
- Para volver atrás: revertir el PR.
