# Propuesta: US-003 – Gestionar cuentas de usuario

## Why

Hoy el panel de Django crea cuentas con solo usuario, rol e institución, permite crearlas sin contraseña, ofrece el rol Administrador, deja marcar `is_staff` y `is_superuser`, y permite eliminar cuentas. US-003 (RF-003, prioridad Alta) deja al Administrador crear, editar y desactivar cuentas de docentes y de la dirección, de modo que solo el personal autorizado use el sistema (doc 08: "CRU, desactiva; no elimina"; RN-023).

## What Changes

- **Alta en el panel existente** (`/admin/`, sin pantalla propia). Son obligatorios: nombres, apellidos, usuario, rol, institución y contraseña inicial.
  - Se quita la opción de crear una cuenta sin contraseña.
  - El rol solo puede ser Docente o Dirección. Los administradores se siguen creando con `createsuperuser`.
  - Ninguna cuenta del panel queda con `is_staff` ni `is_superuser`.
- **Mensajes del criterio:** "Cuenta creada" al guardar el alta y "El usuario ya existe" si el usuario se repite, sin distinguir mayúsculas.
- **Formato del usuario (R-11):** inicial del primer nombre + primer apellido, en minúsculas, sin tildes, ñ ni espacios (jperez). Si ya existe, se agrega un número (jperez2).
  - El alta valida el formato.
  - El campo explica el formato y, cuando el usuario se repite, propone el siguiente libre.
- **Edición:** se ocultan `is_staff`, `is_superuser`, grupos, permisos y `debe_cambiar_password`. `intentos_fallidos` y `bloqueado_hasta` siguen de solo lectura, y "Desbloquear cuenta" no cambia.
- **Desactivar, no eliminar:** se desactiva con "Activo" (`is_active`). El panel no ofrece eliminar cuentas, ni el botón ni la acción masiva. Una cuenta desactivada no ingresa, pierde la sesión que tenía abierta y su fila se conserva.
- **`/ingresar/`:** el campo Usuario lleva una pista de una línea con el ejemplo. Cambia una pantalla de US-001, así que se actualizan su spec y su prueba.
- **Usuario sin distinguir mayúsculas al ingresar:** el usuario se pasa a minúsculas antes de autenticar y antes de buscar la cuenta para el bloqueo (RN-024). "JPerez" entra y suma intentos en la misma cuenta que "jperez". Los usuarios de todos los roles van en minúsculas.
- **Pruebas primero (TDD):** los tres escenarios del criterio y los cinco que agregó el equipo (ver spec `gestion-cuentas`).

**Fuera de alcance (deuda para la descripción del PR):**
- Cambio obligatorio de la contraseña inicial (RF-007).
- Registro de actividad propio (RF-008). Por ahora queda el historial del panel.
- Contacto del administrador en `/ingresar/` (R-29 / T-07, dato de la I.E. pendiente).
- DESIGN.md 0.3.1 no menciona la pista del campo Usuario. No se edita (reglas de ritmo) y queda para el pulido.

## Capabilities

### New Capabilities

- `gestion-cuentas`: alta, edición y desactivación de cuentas de docentes y de la dirección por el Administrador en el panel, con el formato del usuario, los mensajes del criterio y sin eliminación.

### Modified Capabilities

- `pantallas-de-inicio`: "Pantalla de inicio de sesión" agrega la pista del formato bajo el campo Usuario.
- `inicio-sesion`:
  - "Inicio de sesión único": el usuario no distingue mayúsculas.
  - "Bloqueo temporal por intentos fallidos": los intentos con otras mayúsculas cuentan en la misma cuenta.

## Impact

- **Código:**
  - `src/backend/cuentas/`: `servicios.py` (formato y sugerencia del usuario), `admin.py` (formularios de alta y edición, mensaje, sin eliminar), `backends.py` (usuario en minúsculas) y pruebas.
  - `templates/componentes/campo.html` y `templates/cuentas/ingresar.html` (pista del campo Usuario).
- **Dependencias y migraciones:** ninguna. Nombres y apellidos son obligatorios en el formulario, no en el modelo.
- **Rutas:** ninguna nueva ni cambiada. El Catálogo de rutas no se toca, y el README tampoco.
- **Requisitos:** US-003, RF-003, RN-023, doc 08 (matriz de acceso), RNF-005 y RNF-008. DoD 1 a 9, con la DoD 4 sin aplicar hasta EN-02.
- **Rama:** `feature/US-003-gestionar-cuentas`, desde `main`. Su primer commit es el archivo de US-002.
