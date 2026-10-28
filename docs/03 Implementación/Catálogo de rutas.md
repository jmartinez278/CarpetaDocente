[← Volver al README Principal](../../README.md)

# Catálogo de rutas de la aplicación

| Campo | Detalle |
|---|---|
| **Proyecto** | Sistema web para la gestión y planificación pedagógica en educación primaria – I.E. Virgen del Carmen, Huayucachi |
| **Producto** | CarpetaDocente (nombre temporal) |
| **Integrantes** | Cuicapuza Remigio Nayely Nilda · Martinez Llanos Marco Jhair · Vera Zea Jhoanna Hade |
| **Asesor** | Ing. Elvis Wilfredo Carmen Delgadillo |
| **Fecha** | 27/10/2026 |
| **Versión** | 1.3.0 |

---

## 1. Propósito

El sistema genera sus páginas en el servidor y no expone una API pública, así que, según el criterio 9 de la DoD (documento 01 de planificación, sección 7), la documentación de rutas reemplaza a OpenAPI/Swagger. Cada historia que agrega o cambia rutas actualiza este catálogo en su mismo Pull Request.

Las rutas se definen en `src/backend/config/urls.py`, que incluye las de `src/backend/cuentas/urls.py` (namespace `docente`), `src/backend/direccion/urls.py` (namespace `direccion`) y `src/backend/institucion/urls.py` (namespace `estudiantes`, bajo `/docente/secciones/<id>/estudiantes/`).

## 2. Rutas

| Ruta | Métodos | Nombre | Vista | Módulo | Acceso | Requisito | Desde |
|---|---|---|---|---|---|---|---|
| `/` | GET | `raiz` | `RaizView` | `cuentas` | Cualquiera. Sin sesión redirige a `/ingresar/`; con sesión, a la pantalla de inicio de su rol | RF-001 (US-001) | US-001 (antes, página inicial de EN-01) |
| `/ingresar/` | GET, POST | `ingresar` | `IngresarView` | `cuentas` | Sin sesión: muestra el formulario. Con sesión: redirige a la pantalla de su rol | RF-001, RN-024 (US-001) | US-001 |
| `/salir/` | POST | `salir` | `LogoutView` | Django (`django.contrib.auth`) | Cualquiera. Termina la sesión y lleva a `/ingresar/`, sin aviso. Solo POST con token CSRF; GET responde 405. Sin sesión, también lleva a `/ingresar/` | RF-002 (US-002) | US-002 |
| `/docente/` | GET | `docente:portada` | `PortadaDocenteView` | `cuentas` | Solo rol Docente. Sin sesión, a `/ingresar/?next=…`; otro rol, a su pantalla | RF-001 (US-001) | US-001 |
| `/docente/secciones/<id>/estudiantes/` | GET | `estudiantes:lista` | `ListaView` | `institucion` | Solo la docente de aula de la sección en el año ABIERTO; otra docente o un año CERRADO, 404; otro rol, a su pantalla; sin sesión, a `/ingresar/?next=…`. Con `HX-Request` responde el parcial para el diálogo de la portada; sin ella, la página completa | RF-006 (US-006) | US-006 |
| `/direccion/` | GET | `direccion:inicio` | `InicioDireccionView` | `direccion` | Solo rol Dirección. Sin sesión, a `/ingresar/?next=…`; otro rol, a su pantalla | RF-001 (US-001) | US-001 |
| `/admin/login/` | GET | `ingreso_panel` | `IngresoPanelView` | `cuentas` | Reemplaza el ingreso propio del panel. Sin sesión, a `/ingresar/` con `next`; con `is_staff`, al panel; otro rol, a su pantalla; Administrador sin `is_staff`, 403 | RF-001, RN-024 (US-001) | US-001 |
| `/admin/logout/` | POST | `admin:logout` | `LogoutView` (la del panel) | Django (`django.contrib.admin`) | Cierra la sesión y lleva a `/ingresar/` (`LOGOUT_REDIRECT_URL`), no a la página "Sesión cerrada" del panel | RF-002 (US-002) | US-002 |
| `/admin/` | GET, POST | `admin:*` | Panel de administración de Django | Django (`django.contrib.admin`) | Solo cuentas con `is_staff` (rol Administrador). Sin sesión, a `/ingresar/` pasando por `/admin/login/` | Panel interno del Administrador (documento 10, sección 4) | EN-01 |

## 3. Notas

- **Archivos estáticos:** en desarrollo, el servidor de Django sirve `/static/` solo con `DJANGO_DEBUG=True`. No es una ruta de la aplicación y no se lista en la sección 2.
- **Panel de administración:** en EN-01 permite administrar instituciones y usuarios (alta con rol e institución). En US-001 suma la acción "Desbloquear cuenta" (RN-024). Su cierre de sesión (`/admin/logout/`) lleva a `/ingresar/` desde US-002.
- **Inactividad y caché (US-002):** en todas las pantallas con sesión, el panel incluido, la sesión termina a los 60 minutos sin ninguna petición (RN-025, RNF-015). La petición que llega después lleva a `/ingresar/`, con `?next=` si era un GET, y deja un aviso que se muestra una sola vez. Toda respuesta a una petición con sesión lleva las cabeceras de no caché, para que el botón "atrás" no muestre la pantalla tras cerrar la sesión.
- **Pantalla de inicio de cada rol:** Docente, `/docente/`; Dirección, `/direccion/`; Administrador, `/admin/`. La verificación de rol de US-001 es `RolRequeridoMixin` (`cuentas/acceso.py`); los permisos completos por rol son de US-004.

- **Peticiones de HTMX (US-006):** con la cabecera `HX-Request`, la sesión vencida, la falta de sesión o un rol distinto responden 200 con `HX-Redirect` (a `/ingresar/?next=/docente/` o a la pantalla del rol), para que la página completa cambie y el formulario de ingreso no aparezca dentro del diálogo. Sin la cabecera, el 302 de siempre.

## Historial de cambios

| Versión | Fecha | Autor | Descripción |
|---|---|---|---|
| 1.0.0 | 15/10/2026 | Equipo del proyecto | Versión inicial: rutas `/` y `/admin/` de EN-01. |
| 1.1.0 | 22/10/2026 | Equipo del proyecto | US-001: `/` pasa a redirigir según la sesión; se agregan `/ingresar/`, `/docente/`, `/direccion/` y `/admin/login/`, con su acceso por rol. Se quita la nota "exigirá sesión con EN-04". |
| 1.2.0 | 25/10/2026 | Equipo del proyecto | US-002: se agregan `/salir/` (solo POST) y `/admin/logout/`, que ahora lleva a `/ingresar/`; nota sobre el cierre por inactividad y la falta de caché en las pantallas con sesión. Se quita "su cierre de sesión propio sigue hasta US-002". |
| 1.3.0 | 27/10/2026 | Equipo del proyecto | US-006: se agrega la lista de estudiantes de la sección (`/docente/secciones/<id>/estudiantes/`); nota sobre las peticiones de HTMX y la sesión vencida. |

[← Volver al README Principal](../../README.md)
