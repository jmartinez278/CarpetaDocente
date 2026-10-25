# Propuesta: US-001 – Iniciar sesión

## Why

Hoy cualquiera que abre el sistema ve la página inicial de EN-01, sin cuenta ni rol. US-001 (RF-001, prioridad Alta) es la puerta de todas las historias del Sprint 1: cada docente, la dirección y el administrador tienen que entrar con su usuario y su contraseña y llegar a la pantalla de su rol. Con la entrada viene el bloqueo de RN-024, que el documento 09 asigna a esta historia, y la primera versión de las pantallas con el sistema de diseño ya aprobado en el prototipo (DESIGN.md 0.3, variante G4e).

## What Changes

- **Rutas nuevas:**
  - `/ingresar/`: inicio de sesión único para los tres roles.
  - `/docente/`: portada del docente.
  - `/direccion/`: inicio de la dirección, con el estado vacío de R-23.
  - El Administrador entra por `/ingresar/` y llega al panel de Django en `/admin/`.
  - `/admin/login/` redirige a `/ingresar/`.
  - `/` redirige: sin sesión, a `/ingresar/`; con sesión, a la pantalla de su rol.
  - **BREAKING:** la página inicial de EN-01 deja de existir.
- **Bloqueo por intentos (RN-024) en el backend de autenticación, con la lógica en la capa de servicios:**
  - 5 intentos fallidos consecutivos bloquean la cuenta 15 minutos (`bloqueado_hasta`).
  - Los intentos durante el bloqueo no cuentan.
  - Un ingreso correcto reinicia el contador.
  - Contraseña incorrecta, cuenta inactiva y cuenta bloqueada muestran el mismo mensaje genérico de RF-001 V_1_5_0, en dos líneas.
- **Acción "Desbloquear cuenta"** en el panel de Django, registrada en el historial del usuario.
- **Verificación de rol reutilizable:** cada rol entra solo a su pantalla y otro rol es redirigido a la suya. El control completo de permisos es de US-004 y no se adelanta.
- **Interfaz desde el prototipo G4e:**
  - Plantillas de Django que usan solo los tokens de DESIGN.md (sin hex), con tema claro y oscuro según `prefers-color-scheme`.
  - Besley 600 alojada en el propio servidor, desde `@fontsource/besley` (npm) con su licencia OFL, como HTMX y Alpine.
  - Íconos Lucide como SVG incrustado, con el aviso ISC.
  - "Mostrar contraseña" con JavaScript propio mínimo; el inicio de sesión no carga Alpine.
  - Carrusel con CSS y Alpine como mejora progresiva.
  - Barra sin menú (el menú entra con US-002).
- **Portada en US-001:**
  - Las tres tarjetas en "Próximamente", cada una con una bandera de disponibilidad que su historia activará (US-030 activa Asistencia).
  - Ningún enlace apunta a una página que no existe.
- **Pruebas (TDD):**
  - Pruebas unitarias del servicio de bloqueo, de las vistas y redirecciones por rol, y de la acción del panel.
  - La prueba de punta a punta de la página inicial pasa a `/ingresar/` (delta de `integracion-continua`).
  - Revisión automática de accesibilidad con axe-core en Playwright, en ambos temas.
  - Medición de RNF-002 con Slow 4G (≤ 2 MB, usable en ≤ 5 s).
- **Falla intermitente de pytest** vista en `scripts/verificar.py`: se investiga y se corrige. Si no se reproduce, `verificar.py` guarda la salida completa de pytest cuando falla, para no perder el detalle otra vez.
- **Catálogo de rutas** actualizado (DoD 9).

**Fuera de alcance:**
- Cerrar sesión y cierre por inactividad (US-002, RN-025).
- Restablecer y cambiar la contraseña (US-007).
- Permisos completos por rol y por sección (US-004).
- Registro de asistencia (US-030).
- Selector de tema.
- Vista previa en Vercel (EN-02).

## Capabilities

### New Capabilities

- `inicio-sesion`: entrada al sistema con usuario y contraseña, mensaje genérico ante cualquier rechazo, bloqueo temporal por intentos fallidos (RN-024), desbloqueo desde el panel del Administrador, redirección a la pantalla de cada rol y verificación de rol reutilizable.
- `pantallas-de-inicio`: lo que ve cada rol al entrar:
  - la portada del docente, con las tarjetas de las tres dimensiones, su disponibilidad por bandera y el carrusel en el celular;
  - el inicio de la dirección, con su estado vacío;
  - el marco visual común: barra, pie, temas claro y oscuro, y accesibilidad.

### Modified Capabilities

- `entorno-desarrollo`: el requisito "Página inicial" cambia. La ruta raíz ya no muestra una página pública; redirige según la sesión. La plantilla base carga la hoja de estilos compilada, y cada página carga solo los scripts que usa.
- `integracion-continua`: el requisito "Pruebas de punta a punta" cambia. La prueba obligatoria recorre `/ingresar/` en lugar de la página inicial, y se suman la revisión de accesibilidad en ambos temas y la medición con Slow 4G.

## Impact

- **Código:**
  - `src/backend/cuentas/`: backend de autenticación, servicios, formulario, vistas, verificación de rol, panel y pruebas.
  - `src/backend/direccion/`: vista del inicio y pruebas.
  - `src/backend/config/`: `settings.py` (`AUTHENTICATION_BACKENDS`, `LOGIN_URL`) y `urls.py`.
  - Plantillas en `src/backend/templates/`.
  - `src/frontend/css/app.css`, con los tokens y los componentes.
  - JavaScript propio en `src/backend/static/js/`.
  - La fuente y su licencia, copiadas por el build a `src/backend/static/dist/fuentes/` (sin versionar).
- **Se reemplaza:** `InicioView`, `inicio.html`, `test_inicio.py` y `test_inicio_e2e.py`, todo de EN-01.
- **Dependencias:** `axe-core`, como dependencia de desarrollo, y `@fontsource/besley`, como dependencia (igual que `alpinejs` y `htmx.org`), en `src/frontend/package.json`. Sin dependencias nuevas de Python.
- **Migraciones:** ninguna, porque los campos de RN-024 ya existen desde EN-01.
- **Documentos:** `docs/03 Implementación/Catálogo de rutas.md` (versión 1.1.0) y el README (cómo correr accesibilidad y rendimiento).
- **Canal:** el trabajo `Playwright` del CI corre las pruebas nuevas, sin cambios en el YAML salvo que la implementación lo exija.
- **Requisitos:** US-001, RF-001, RN-024, RNF-002, RNF-005, RNF-008 y RNF-012; DoD 1 a 9, con la DoD 4 sujeta a EN-02.
- **Rama:** `feature/US-001-iniciar-sesion`. Ya lleva los cuatro commits de diseño y documentos (DESIGN.md 0.3, docs 07, 02/01 y 06), que entran en el mismo PR.
