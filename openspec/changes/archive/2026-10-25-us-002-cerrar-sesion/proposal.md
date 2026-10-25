# Propuesta: US-002 – Cerrar sesión

## Why

Con US-001 se entra al sistema, pero no hay forma de salir: la sesión dura lo que dure la cookie de Django (dos semanas) y en un celular o una computadora compartidos cualquiera puede seguir usando la cuenta. US-002 (RF-002, prioridad Alta) agrega el cierre de sesión y el cierre automático tras 60 minutos sin actividad (RN-025, RNF-015). La barra de las pantallas internas estaba esperando este menú desde US-001.

## What Changes

- **Cerrar sesión** desde el menú de la barra: termina la sesión y lleva a `/ingresar/`. Solo por POST con token CSRF.
- **Ruta nueva `/salir/`.** `/admin/logout/` (el botón del panel) también lleva a `/ingresar/`, en lugar de la página "Sesión cerrada" de Django.
- **Cierre por inactividad (RN-025):** a los 60 minutos sin ninguna petición, la sesión se termina en el servidor. La petición siguiente lleva a `/ingresar/`, que muestra un aviso corto:
  - **Tu sesión se cerró por inactividad.**
  - Pasaron 60 minutos sin uso. Ingresa de nuevo para continuar.
- **Botón "atrás" después de cerrar sesión:** las pantallas con sesión se sirven sin caché, así que el navegador las vuelve a pedir y el servidor redirige a `/ingresar/` sin mostrar la información.
- **Menú de la cuenta** en la barra (DESIGN.md, Barra superior: a la derecha, 44 × 44 px): un desplegable con el nombre del usuario y "Cerrar sesión". Funciona sin JavaScript.
- **Pruebas:** primero las pruebas (TDD) de la regla de inactividad en la capa de servicios, del cierre, del panel y de la caché; de punta a punta del camino ideal, del botón "atrás" y del aviso; axe en ambos temas con el menú abierto y con el aviso.
- **Catálogo de rutas** a la versión 1.2.0 (DoD 9).

**Fuera de alcance:**
- "Mantener la sesión en este celular" (T-08): rechazado por el equipo; se mantiene RN-025.
- Aviso antes del cierre o cuenta regresiva.
- Cierre de las demás sesiones del usuario en otros equipos.
- Registro del cierre en la actividad (RF-008, US-008).
- Página propia para el token CSRF vencido (riesgo anotado en US-001).

## Capabilities

### New Capabilities

- `cierre-sesion`: cerrar sesión desde el menú y desde el panel, cierre por inactividad con su aviso, pantallas con sesión sin caché (botón "atrás") y el menú de la cuenta.

### Modified Capabilities

- `pantallas-de-inicio`:
  - "Marco común": la barra ya no está sin menú; lleva el menú de la cuenta.
  - "Accesibilidad en ambos temas": la revisión suma el inicio de sesión con el aviso y las pantallas con el menú abierto.

## Impact

- **Código:**
  - `src/backend/cuentas/`: servicio de inactividad, middleware, ruta `/salir/` y pruebas.
  - `src/backend/config/settings.py`: `MIDDLEWARE` y `LOGOUT_REDIRECT_URL`.
  - `src/backend/config/urls.py`.
  - Plantillas `marco.html` e `ingresar.html`, con un componente nuevo para el menú.
  - `src/frontend/css/app.css`: menú y mensaje de aviso.
  - Íconos Lucide nuevos.
  - `src/backend/static/js/menu.js`.
  - `src/backend/static/js/bfcache.js` y `src/backend/templates/admin/base_site.html` (respaldo de "atrás" también en el panel).
- **Dependencias y migraciones:** ninguna.
- **Documentos:** `docs/03 Implementación/Catálogo de rutas.md` (1.2.0). El README y docs/01 a 03 no se editan durante el cambio: lo pendiente va a `insumos/pendientes-docs.md`.
- **Requisitos:** US-002, RF-002, RN-025, RNF-015, RNF-005 y RNF-008; DoD 1 a 9, con la DoD 4 sin aplicar hasta EN-02.
- **Rama:** `feature/US-002-cerrar-sesion`, desde `main`. Su primer commit es el archivo de US-001.
