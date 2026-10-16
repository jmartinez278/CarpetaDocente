[← Volver al README Principal](../../README.md)

# Catálogo de rutas de la aplicación

| Campo | Detalle |
|---|---|
| **Proyecto** | Sistema web para la gestión y planificación pedagógica en educación primaria – I.E. Virgen del Carmen, Huayucachi |
| **Producto** | CarpetaDocente (nombre temporal) |
| **Integrantes** | Cuicapuza Remigio Nayely Nilda · Martinez Llanos Marco Jhair · Vera Zea Jhoanna Hade |
| **Asesor** | Ing. Elvis Wilfredo Carmen Delgadillo |
| **Fecha** | 15/10/2026 |
| **Versión** | 1.0.0 |

---

## 1. Propósito

El sistema genera sus páginas en el servidor y no expone una API pública, así que, según el criterio 9 de la DoD (documento 01 de planificación, sección 7), la documentación de rutas reemplaza a OpenAPI/Swagger. Cada historia que agrega o cambia rutas actualiza este catálogo en su mismo Pull Request.

Las rutas se definen en `src/backend/config/urls.py`.

## 2. Rutas

| Ruta | Métodos | Nombre | Vista | Módulo | Acceso | Requisito | Desde |
|---|---|---|---|---|---|---|---|
| `/` | GET | `inicio` | `InicioView` | `cuentas` | Público por ahora; exigirá sesión iniciada con EN-04 | EN-01 (página inicial) | EN-01 |
| `/admin/` | GET, POST | `admin:*` | Panel de administración de Django | Django (`django.contrib.admin`) | Solo cuentas con `is_staff` (rol Administrador) | Panel interno del Administrador (documento 10, sección 4) | EN-01 |

## 3. Notas

- **Archivos estáticos:** en desarrollo, el servidor de Django sirve `/static/` solo con `DJANGO_DEBUG=True`. No es una ruta de la aplicación y no se lista en la sección 2.
- **Panel de administración:** en EN-01 permite administrar instituciones y usuarios (alta con rol e institución).

## Historial de cambios

| Versión | Fecha | Autor | Descripción |
|---|---|---|---|
| 1.0.0 | 15/10/2026 | Equipo del proyecto | Versión inicial: rutas `/` y `/admin/` de EN-01. |

[← Volver al README Principal](../../README.md)
