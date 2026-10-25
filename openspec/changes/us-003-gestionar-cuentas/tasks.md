# Tasks

**Reglas para todas las tareas:**
- Pruebas primero (TDD): cada prueba se escribe y se ve fallar antes del código. Ante una falla inesperada, depuración sistemática.
- Antes de usar una API de Django o de Playwright, se consulta Context7.
- Solo datos ficticios.
- Un commit por grupo. Su casilla y su evidencia en `verificacion.md` van en ese commit. Antes de cada commit:
  - revisión del grupo (Superpowers `requesting-code-review`): Critical e Important se corrigen; los Minor van a la descripción del PR;
  - lo que entra va al índice y se corre `uv run python scripts/verificar.py --antes-del-commit`;
  - se muestran los archivos y el mensaje, y se espera la aprobación. Sin push.
- No cambia ninguna ruta: el Catálogo de rutas y el README no se tocan.

## 1. Backend: formato del usuario, alta, edición y sin eliminar (D1 a D5)

- [x] 1.1 Prueba primero, `cuentas/tests/test_servicios_usuario.py`:
  - `usuario_valido` acepta "jperez", "jperez2" y "jperez10", y rechaza "JPerez", "jpérez", "jpeñez", "j perez", "j.perez", "jperez1", "jperez01" y "j";
  - `usuario_base` de "Ñahui Rosa" / "Núñez Ávila" da "nnunez";
  - `sugerir_usuario` da la base libre o el primer número libre desde el 2, sin distinguir mayúsculas, y `None` si la base tiene menos de dos letras.

  Luego `FORMATO_USUARIO`, `usuario_valido`, `usuario_base` y `sugerir_usuario` en `cuentas/servicios.py`, con docstrings que citen R-11 y RF-003. Verificar: rojo y luego verde
- [x] 1.2 Prueba primero, en `cuentas/tests/test_admin.py`. Se adaptan `datos_alta` y las pruebas del alta que ya existen (sin `usable_password`, con un usuario del formato, nombres y apellidos). Casos:
  - camino ideal con "Cuenta creada" y la cuenta activa, sin `is_staff` ni `is_superuser`;
  - cada obligatorio vacío;
  - el formulario sin `usable_password`;
  - ADMINISTRADOR rechazado;
  - "El usuario ya existe", también con otras mayúsculas, y "Prueba con jperez3.";
  - el formato inválido;
  - el `help_text` del usuario.

  Luego `FormularioAltaUsuario` sobre `UserCreationForm`, `add_fieldsets` y `response_add` (D2, D3). Verificar: rojo y luego verde
- [x] 1.3 Prueba primero, en `test_admin.py`. Casos:
  - la edición no tiene `is_staff`, `is_superuser`, `groups`, `user_permissions` ni `debe_cambiar_password`;
  - el usuario es de solo lectura, y el rol también en una cuenta de Administrador;
  - el rol ofrece solo Docente y Dirección;
  - corregir los apellidos conserva el usuario y la contraseña.

  Luego `fieldsets`, `get_readonly_fields`, `FormularioEdicionUsuario` y `list_filter` (D4). Las pruebas de "Desbloquear cuenta" siguen en verde. Verificar: rojo y luego verde
- [x] 1.4 Prueba primero, en `test_admin.py`. Casos:
  - sin botón ni acción de eliminar, y un POST a la vista de eliminación da 403 y la fila sigue;
  - una cuenta desactivada no ingresa (mensaje genérico), sigue en la lista como inactiva y su sesión abierta termina en `/ingresar/`;
  - la cuenta creada en el panel abre `/admin/` y termina en su portada;
  - un docente y la dirección no ven la lista ni el alta de cuentas.

  Luego `has_delete_permission` (D5). Verificar: rojo y luego verde (las pruebas de la sesión y del acceso pueden pasar desde el inicio: se anota en `verificacion.md` que fijan un comportamiento que ya existe); `uv run pytest --cov` en verde y con 80 % o más
- [x] 1.5 Revisión del grupo y commit (reglas de arriba)

## 2. Ingreso: usuario en minúsculas, pista en `/ingresar/` y punta a punta (D6 a D8)

- [x] 2.1 Prueba primero, en `cuentas/tests/test_backend.py`, `test_ingresar.py` y `test_modelos.py`:
  - "JPerez" con la contraseña correcta entra en la cuenta "jperez" y llega a `/docente/`;
  - 5 contraseñas incorrectas escritas como "jperez", "JPerez" y "JPEREZ" bloquean la cuenta "jperez" (RN-024);
  - tras un rechazo, el formulario conserva el usuario tal como se escribió;
  - `createsuperuser --noinput` con "Marco" guarda "marco" y esa cuenta ingresa con "Marco";
  - con "marco" existente, `createsuperuser` con "Marco" falla y no crea otra cuenta.

  Luego `BackendConBloqueo.authenticate` pasa el usuario a minúsculas antes de `get_by_natural_key`, y `Usuario.normalize_username` lo pasa a minúsculas (D7). Verificar: rojo y luego verde; las pruebas de bloqueo y de ingreso de US-001 siguen en verde

- [x] 2.2 Prueba primero, en `test_plantillas.py` o `test_ingresar.py`:
  - `/ingresar/` muestra "Ejemplo: jperez (inicial y apellido)" bajo el campo Usuario, con `aria-describedby` hacia la pista;
  - con un error en el campo, `aria-describedby` nombra la pista y el error;
  - el campo Contraseña no tiene pista.

  Luego `ayuda` en `componentes/campo.html` y la pista en `ingresar.html`. Verificar: rojo y luego verde; `npm run build` sin errores y ningún color hexadecimal en las plantillas
- [x] 2.3 Prueba de punta a punta, `cuentas/tests/test_gestion_cuentas_e2e.py`:
  - el Administrador crea una docente en el panel y ve "Cuenta creada";
  - la docente ingresa por `/ingresar/` y llega a `/docente/`;
  - el Administrador la desactiva;
  - la docente ya no ingresa y ve el mensaje genérico.

  Verificar: `uv run pytest -m e2e --browser chromium` en verde, con el CSS compilado y `DJANGO_ALLOW_ASYNC_UNSAFE=true`. Las combinaciones de axe de `/ingresar/` y la prueba de ancho a 320 y 360 px siguen sin `critical` ni `serious`
- [x] 2.4 La pantalla vista en claro y oscuro, en celular y escritorio (la marca Marco). Revisión del grupo y commit (reglas de arriba)

## 3. Revisión final y verificación

- [x] 3.1 Con la revisión final A2 que corre el usuario (`/codex:adversarial-review --base main --background`, con foco en los specs del cambio), corregir los Critical e Important, con la prueba primero en cada caso. Los Minor van a la descripción del PR. Verificar: `uv run pytest --cov`, las e2e y `verificar.py --antes-del-commit` en verde
- [x] 3.2 `verificacion.md` corto: tabla escenario → prueba, con los tres specs del cambio, y la DoD 1 a 9. La DoD 4 dice "No aplica hasta EN-02". Verificar: cada escenario tiene su prueba o una nota de por qué no aplica; commit del grupo (reglas de arriba)

## Workflow follow-up

- **(equipo)** Push de `feature/US-003-gestionar-cuentas` y PR hacia `main`, con las verificaciones de EN-08 en verde. En la descripción va la deuda:
  - RF-007;
  - RF-008;
  - R-29 / T-07;
  - la pista que DESIGN.md no fija;
  - el Administrador que se desactiva a sí mismo.
- **(equipo)** Aprobación del PR por otra integrante (DoD 3).
- Después de la fusión: `/opsx:archive`. La siguiente historia sale de `main`, y su primer commit es este archivo.
