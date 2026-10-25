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
