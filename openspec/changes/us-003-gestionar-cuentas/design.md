# Design: US-003 – Gestionar cuentas de usuario

## Context

- `cuentas/admin.py` registra `Usuario` con `UserAdmin`.
  - El alta hereda de `AdminUserCreationForm`: trae `usable_password` y deja las contraseñas como opcionales.
  - La edición suma a `UserAdmin.fieldsets`, que trae `is_staff`, `is_superuser`, grupos y permisos.
  - La acción "Desbloquear cuenta" y los campos de solo lectura son de US-001 (spec `inicio-sesion`) y no cambian.
- En Django 5.2.18, `UserCreationForm.clean_username` ya rechaza un usuario que solo cambia en mayúsculas (`username__iexact`), con el mensaje de unicidad del modelo.
- `BackendConBloqueo` hereda `get_user` de `ModelBackend`, que rechaza las cuentas inactivas. Una sesión abierta de una cuenta desactivada queda anónima en la siguiente petición, y `RolRequeridoMixin` la lleva a `/ingresar/`.
- `/ingresar/` usa `componentes/campo.html`, que hoy no tiene texto de ayuda.
- El ingreso compara el usuario tal como se escribe, distinguiendo mayúsculas. `BackendConBloqueo.authenticate` busca la cuenta con `get_by_natural_key` (igualdad exacta) y le pasa el intento a `servicios.intentar_ingreso`, que cuenta los intentos de RN-024.
- Las pruebas del alta en `test_admin.py` usan `docente_ficticio` y `usable_password`. Hay que adaptarlas al formato nuevo.

## Goals / Non-Goals

**Goals:**
- El formato y la sugerencia del usuario van en la capa de servicios, con pruebas propias (DoD 6), sin tocar la base de datos.
- Usar los puntos de extensión del panel de Django. No se escriben vistas propias.

**Non-Goals:**
- Un JavaScript que llene el usuario mientras se escriben los nombres.
- Una acción masiva "Desactivar".
- Validar el formato al editar: el usuario no se edita.

## Decisions

### D1. Formato y sugerencia del usuario en `cuentas/servicios.py`

- `FORMATO_USUARIO`: `^[a-z]{2,}(?:[2-9]|[1-9][0-9]+)?$`. Solo letras a–z, al menos dos, y un número final opcional desde el 2. Se rechazan "jperez1", "jperez01", "j.perez", "j perez", "jpérez" y "JPerez".
- `usuario_valido(usuario) -> bool`.
- `usuario_base(nombres, apellidos) -> str`: inicial de la primera palabra de los nombres más la primera palabra de los apellidos. Pasa a minúsculas y quita las marcas con `unicodedata` (NFKD), de modo que "Ñ" queda en "n" y "Á" en "a". Descarta lo que no sea a–z.
- `sugerir_usuario(nombres, apellidos) -> str | None`: devuelve la base si está libre o, si no, la base con el primer número libre desde el 2. Compara sin distinguir mayúsculas. Si la base sale con menos de dos letras, devuelve `None`.
- **Alternativa descartada:** exigir que el usuario coincida con el que sale de los nombres. Con apellidos compuestos ("De la Cruz") no hay una sola respuesta correcta, y el criterio deja que el Administrador escriba el usuario. El panel valida la forma y propone; el Administrador decide.

### D2. Formulario de alta sobre `UserCreationForm`

- `FormularioAltaUsuario` hereda de `UserCreationForm`, no de `AdminUserCreationForm`. Así no hay `usable_password` y las dos contraseñas son obligatorias, con los validadores de `AUTH_PASSWORD_VALIDATORS`.
- Campos: `username`, `first_name`, `last_name`, `rol`, `institucion`, `password1` y `password2`. Nombres, apellidos e institución se marcan obligatorios en el formulario, no en el modelo, porque el Administrador de `createsuperuser` no tiene institución.
- `rol` ofrece solo DOCENTE y DIRECCION. Un POST con ADMINISTRADOR da el error de opción inválida.
- `clean_username`:
  1. Si existe sin distinguir mayúsculas, da "El usuario ya existe" y, como segunda línea, "Prueba con jperez3." (`sugerir_usuario`). Para eso los nombres y apellidos se limpian antes que el usuario (orden de los campos). Va primero para que "JPerez" con "jperez" ya existente diga que el usuario existe, como pide el spec, y no solo que el formato falla.
  2. Si no cumple `usuario_valido`, da el error de formato, con el ejemplo jperez.
- El `help_text` del campo usuario explica el formato: "Inicial del primer nombre y primer apellido, en minúsculas, sin tildes ni ñ (ej. jperez). Si ya existe, se agrega un número (jperez2)."
- `is_staff` e `is_superuser` no están en el formulario, así que quedan en falso.

### D3. Mensaje "Cuenta creada"

- `UsuarioAdmin.response_add` cambia el mensaje de éxito de Django por "Cuenta creada". Se sigue el flujo de `UserAdmin`, que tras el alta lleva a la edición. El punto de extensión exacto se confirma con Context7 al implementar.
- El historial del panel (`LogEntry`) registra el alta como siempre.

### D4. Edición

- `fieldsets` propios, que ya no suman a `UserAdmin.fieldsets`:
  - usuario y contraseña (el enlace de restablecer de Django);
  - nombres, apellidos y correo;
  - rol e institución;
  - estado: "Activo", último ingreso y fecha de alta;
  - control de la cuenta: intentos fallidos y bloqueo.
- Quedan fuera `is_staff`, `is_superuser`, `groups`, `user_permissions` y `debe_cambiar_password`. Un campo que no está en el formulario no se modifica al guardar.
- `get_readonly_fields`: siempre `username`, `intentos_fallidos` y `bloqueado_hasta`; además `rol`, si la cuenta es de un Administrador. Así no se baja el rol de un administrador que sigue siendo superusuario.
- `FormularioEdicionUsuario` limita `rol` a DOCENTE y DIRECCION.
- `list_filter` ya no incluye `is_staff`.

### D5. Desactivar sin eliminar

- `has_delete_permission` devuelve `False`. Django quita el botón "Eliminar", la acción `delete_selected` y responde 403 a la vista de eliminación. Lo mismo vale para un superusuario.
- Se desactiva con la casilla "Activo" de la edición. La lista muestra `is_active`, como ahora.
- Lo de la sesión abierta no requiere código: ya lo hace `get_user` (Context). Una prueba lo fija.

### D6. Pista del campo Usuario en `/ingresar/`

- `componentes/campo.html` recibe `ayuda`. Si viene, muestra `<p id="<campo>_ayuda">` bajo el control, con las clases de ayuda que ya usa la pantalla (`text-caption`, `text-texto-suave`).
- `aria-describedby` junta la ayuda y el error cuando hay los dos.
- `ingresar.html` la pasa solo al campo Usuario: "Ejemplo: jperez (inicial y apellido)".
- DESIGN.md 0.3.1 no fija esta pista. No se edita (reglas de ritmo) y queda como deuda para el pulido.

### D7. Usuario en minúsculas al ingresar

- **Convención:** los usuarios de todos los roles van en minúsculas, también los que se crean con `createsuperuser`. El alta del panel ya lo exige por el formato (D1).
- `Usuario.normalize_username` pasa el usuario a minúsculas, después de la normalización Unicode de Django. `create_user` y `create_superuser`, que es lo que usa `createsuperuser`, lo aplican al guardar. Así "Marco" queda como "marco" e ingresa con D7.
  - Si "marco" ya existe, `createsuperuser` con "Marco" falla y no crea una segunda cuenta.
  - La API exacta del comando se confirma con Context7 al implementar.
- `BackendConBloqueo.authenticate` pasa el usuario a minúsculas (`str.lower()`) antes de buscar la cuenta. Así la búsqueda, la autenticación y el conteo de intentos de RN-024 caen en la misma cuenta, sin importar cómo se escribió el usuario.
  - Es el único backend de `AUTHENTICATION_BACKENDS`, de modo que cubre `/ingresar/` y cualquier `authenticate()` futuro.
  - El formulario conserva el usuario tal como se escribió para volver a mostrarlo tras un rechazo, como hoy (spec `inicio-sesion`).
- Un usuario inexistente sigue calculando el hash (#20760), así que el tiempo de respuesta no cambia.
- **Alternativa descartada:** pasarlo a minúsculas en `FormularioIngreso.clean_username`. Un `authenticate()` que no use el formulario contaría los intentos en otra búsqueda.
- **Alternativa descartada:** buscar con `username__iexact`. La base de datos no impide dos cuentas que solo cambian en mayúsculas creadas fuera del panel. La búsqueda podría dar dos filas, y el bloqueo dependería de cuál se toma.

### D8. Pruebas

- **Unitarias, primero la prueba:**
  - `test_servicios_usuario.py`: formato, base y sugerencia, con tildes, ñ y números.
  - `test_admin.py`: alta, roles, duplicados, edición, eliminación, la cuenta creada que no entra al panel y la sesión de una cuenta desactivada. Se adaptan las pruebas del alta que ya existen.
  - `test_plantillas.py` o `test_ingresar.py`: la pista y su `aria-describedby`.
  - `test_backend.py` y `test_ingresar.py`: "JPerez" entra en la cuenta "jperez", y los 5 intentos escritos con distintas mayúsculas bloquean esa misma cuenta, y `createsuperuser` con "Marco" guarda "marco" (D7).
- **Punta a punta** (`test_gestion_cuentas_e2e.py`): el Administrador crea una docente en el panel, ve "Cuenta creada" y la docente ingresa por `/ingresar/`. Después el Administrador la desactiva y la docente ya no ingresa.
- **axe:** las combinaciones de `test_accesibilidad_e2e.py` sobre `/ingresar/` ya cubren la pista. El panel de Django no entra en axe: no es una pantalla nueva del proyecto.

## Risks / Trade-offs

- **[Hay cuentas fuera del formato]:** las de prueba y la de `createsuperuser`. → Mitigación: el formato solo se valida en el alta y el usuario no se edita.
- **[El Administrador se desactiva a sí mismo]:** pierde el acceso. → Mitigación: se recupera con `createsuperuser` o con el shell. Se acepta y va a la descripción del PR.
- **[Apellidos compuestos]:** la sugerencia toma la primera palabra. → Mitigación: el Administrador escribe el usuario y el panel solo propone.
- **[Contraseña inicial conocida por el Administrador]:** el cambio obligatorio es RF-007. → Mitigación: es deuda del PR. `debe_cambiar_password` queda oculto y en su valor por defecto.
