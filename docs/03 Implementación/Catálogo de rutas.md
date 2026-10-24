[← Volver al README Principal](../../README.md)

# Catálogo de rutas de la aplicación

| Campo | Detalle |
|---|---|
| **Proyecto** | Sistema web para la gestión y planificación pedagógica en educación primaria – I.E. Virgen del Carmen, Huayucachi |
| **Producto** | CarpetaDocente (nombre temporal) |
| **Integrantes** | Cuicapuza Remigio Nayely Nilda · Martinez Llanos Marco Jhair · Vera Zea Jhoanna Hade |
| **Asesor** | Ing. Elvis Wilfredo Carmen Delgadillo |
| **Fecha** | 22/10/2026 |
| **Versión** | 1.1.0 |

---

## 1. Propósito

El sistema genera sus páginas en el servidor y no expone una API pública, así que, según el criterio 9 de la DoD (documento 01 de planificación, sección 7), la documentación de rutas reemplaza a OpenAPI/Swagger. Cada historia que agrega o cambia rutas actualiza este catálogo en su mismo Pull Request.

Las rutas se definen en `src/backend/config/urls.py`, que incluye las de `src/backend/cuentas/urls.py` (namespace `docente`) y `src/backend/direccion/urls.py` (namespace `direccion`).

## 2. Rutas

| Ruta | Métodos | Nombre | Vista | Módulo | Acceso | Requisito | Desde |
|---|---|---|---|---|---|---|---|
| `/` | GET | `raiz` | `RaizView` | `cuentas` | Cualquiera. Sin sesión redirige a `/ingresar/`; con sesión, a la pantalla de inicio de su rol | RF-001 (US-001) | US-001 (antes, página inicial de EN-01) |
| `/ingresar/` | GET, POST | `ingresar` | `IngresarView` | `cuentas` | Sin sesión: muestra el formulario. Con sesión: redirige a la pantalla de su rol | RF-001, RN-024 (US-001) | US-001 |
| `/docente/` | GET | `docente:portada` | `PortadaDocenteView` | `cuentas` | Solo rol Docente. Sin sesión, a `/ingresar/?next=…`; otro rol, a su pantalla | RF-001 (US-001) | US-001 |
| `/direccion/` | GET | `direccion:inicio` | `InicioDireccionView` | `direccion` | Solo rol Dirección. Sin sesión, a `/ingresar/?next=…`; otro rol, a su pantalla | RF-001 (US-001) | US-001 |
| `/admin/login/` | GET | `ingreso_panel` | `IngresoPanelView` | `cuentas` | Reemplaza el ingreso propio del panel. Sin sesión, a `/ingresar/` con `next`; con `is_staff`, al panel; otro rol, a su pantalla; Administrador sin `is_staff`, 403 | RF-001, RN-024 (US-001) | US-001 |
| `/admin/` | GET, POST | `admin:*` | Panel de administración de Django | Django (`django.contrib.admin`) | Solo cuentas con `is_staff` (rol Administrador). Sin sesión, a `/ingresar/` pasando por `/admin/login/` | Panel interno del Administrador (documento 10, sección 4) | EN-01 |

## 3. Notas

- **Archivos estáticos:** en desarrollo, el servidor de Django sirve `/static/` solo con `DJANGO_DEBUG=True`. No es una ruta de la aplicación y no se lista en la sección 2.
- **Panel de administración:** en EN-01 permite administrar instituciones y usuarios (alta con rol e institución). En US-001 suma la acción "Desbloquear cuenta" (RN-024). Su cierre de sesión propio (`/admin/logout/`) sigue hasta US-002.
- **Pantalla de inicio de cada rol:** Docente, `/docente/`; Dirección, `/direccion/`; Administrador, `/admin/`. La verificación de rol de US-001 es `RolRequeridoMixin` (`cuentas/acceso.py`); los permisos completos por rol son de US-004.

## Historial de cambios

| Versión | Fecha | Autor | Descripción |
|---|---|---|---|
| 1.0.0 | 15/10/2026 | Equipo del proyecto | Versión inicial: rutas `/` y `/admin/` de EN-01. |
| 1.1.0 | 22/10/2026 | Equipo del proyecto | US-001: `/` pasa a redirigir según la sesión; se agregan `/ingresar/`, `/docente/`, `/direccion/` y `/admin/login/`, con su acceso por rol. Se quita la nota "exigirá sesión con EN-04". |

[← Volver al README Principal](../../README.md)
