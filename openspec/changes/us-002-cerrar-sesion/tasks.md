# Tasks

**Reglas para todas las tareas:**
- Pruebas primero (TDD): cada prueba se escribe y se ve fallar antes del código. Ante una falla inesperada, depuración sistemática.
- Antes de usar una API de Django, Tailwind v4, Playwright o axe-core, se consulta Context7.
- Solo datos ficticios.
- Un commit por grupo. Su casilla y su evidencia en `verificacion.md` van en ese commit. Antes de cada commit:
  - revisión del grupo (Superpowers `requesting-code-review`): Critical e Important se corrigen; los Minor van a `verificacion.md` o a la descripción del PR;
  - lo que entra va al índice y se corre `uv run python scripts/verificar.py --antes-del-commit`;
  - se muestran los archivos y el mensaje, y se espera la aprobación. Sin push.
- README y docs/01 a 03 no se editan (salvo el Catálogo de rutas): lo pendiente va a `insumos/pendientes-docs.md`.

## 1. Backend: inactividad, cierre y caché (D1 a D3, D7)

- [x] 1.1 Prueba primero, `cuentas/tests/test_servicios_inactividad.py`, con la hora pasada como argumento: a los 59:59 no vence, a los 60:00 vence, y una sesión sin marca no vence. Luego `INACTIVIDAD_MAXIMA` y `sesion_vencida` en `cuentas/servicios.py`, con docstrings que citen RN-025 y RNF-015. Verificar: rojo porque no existe `sesion_vencida`, y luego verde
- [x] 1.2 Prueba primero, `cuentas/tests/test_inactividad.py`, escribiendo una marca vieja en la sesión. Casos:
  - un GET vencido termina la sesión y lleva a `/ingresar/?next=…`;
  - un POST vencido lleva a `/ingresar/` sin `next`;
  - queda el mensaje con la etiqueta `inactividad`;
  - a los 59 minutos se ve la pantalla y la marca se renueva;
  - el anónimo no cambia;
  - en `/admin/`, lo mismo que en las demás pantallas.

  Luego `InactividadMiddleware` en `cuentas/middleware.py`, registrado en `MIDDLEWARE` después de `MessageMiddleware`. Verificar: rojo y luego verde
- [x] 1.3 Prueba primero, `cuentas/tests/test_salir.py`. Casos:
  - un POST a `/salir/` termina la sesión y lleva a `/ingresar/`, sin mensaje;
  - un GET da 405 y deja la sesión iniciada;
  - un POST sin sesión lleva a `/ingresar/`;
  - un POST a `/admin/logout/` lleva a `/ingresar/`;
  - la portada, el inicio de la dirección y `/admin/` responden con `Cache-Control` `no-store`;
  - después del cierre, `/docente/` lleva a `/ingresar/?next=…`.

  Luego la ruta `salir` (`LogoutView`), `LOGOUT_REDIRECT_URL` y las cabeceras en el middleware. Si la prueba del panel falla, se aplica la alternativa de D2. Verificar: rojo y luego verde; `uv run pytest --cov` en verde y con 80 % o más
- [x] 1.4 Catálogo de rutas a la versión 1.2.0, según D7, con `scripts/subir_version.py` si corresponde (README). Anotar en `insumos/pendientes-docs.md` el `clearsessions` del despliegue. Verificar: el catálogo nombra `/salir/` y `/admin/logout/`, y su historial tiene la fila 1.2.0. Cierre del grupo y commit (reglas de arriba)

## 2. Interfaz: menú, aviso, punta a punta y axe (D4 a D6)

- [x] 2.1 Prueba primero, en `test_plantillas.py` o `test_pantallas.py`. Casos:
  - la portada y la dirección tienen el menú en la barra, con el nombre del usuario (o su usuario) y un formulario POST a `salir` con el token CSRF;
  - `/ingresar/` muestra el aviso, con sus dos líneas y `role="status"`, cuando hay el mensaje `inactividad`, y no lo muestra en los demás casos.

  Luego `componentes/menu_cuenta.html` en `marco.html`; el aviso en `ingresar.html`; `.mensaje--aviso` y las clases del menú en `app.css`; los íconos Lucide `circle-user-round`, `log-out` y `clock`; y `static/js/menu.js` (D3, D5). Verificar: rojo y luego verde; `npm run build` sin errores y ningún color hexadecimal en las plantillas
- [x] 2.2 Prueba de punta a punta, `cuentas/tests/test_cerrar_sesion_e2e.py`. Casos:
  - camino ideal: ingresar, abrir el menú, "Cerrar sesión" y llegar a `/ingresar/`;
  - botón "atrás" tras cerrar sesión: llega a `/ingresar/` sin el saludo;
  - inactividad: se envejece la marca, se recarga, aparece el aviso y "atrás" no muestra la pantalla;
  - Escape cierra el menú y devuelve el foco;
  - un toque fuera cierra el menú;
  - sin JavaScript, el menú abre y cierra la sesión.

  Verificar: `uv run pytest -m e2e --browser chromium` en verde, con el CSS compilado y `DJANGO_ALLOW_ASYNC_UNSAFE=true`
- [x] 2.3 axe y ancho: sumar `ingresar-con-aviso`, `portada-menu-abierto` y `direccion-menu-abierto` a `test_accesibilidad_e2e.py` (32 combinaciones), y comprobar el ancho a 320 y 360 px con el menú abierto en ambos temas. Verificar: sin `critical` ni `serious`, el ancho del documento no supera el de la ventana y el informe queda en `test-results/`. Si falla el contraste de `--color-aviso`, se muestra el diff propuesto de DESIGN.md y se espera la aprobación
- [x] 2.4 La pantalla vista en claro y oscuro, en celular y escritorio (la marca Marco). Anotar en `verificacion.md` lo que DESIGN.md no fija del panel, como deuda para el pulido (D5). Cierre del grupo y commit (reglas de arriba)

## 3. Revisión final y verificación (D8)

- [ ] 3.1 Con la revisión final A2 que corre el usuario (`/codex:adversarial-review --base main --background`, con foco en los specs del cambio), corregir los Critical e Important, con la prueba primero en cada caso. Los Minor van a la descripción del PR. Verificar: `uv run pytest --cov`, las e2e y `verificar.py --antes-del-commit` en verde
- [ ] 3.2 `verificacion.md` con el formato de US-001: evidencia de cada escenario de los dos specs del cambio y el estado de la DoD 1 a 9. La DoD 4 dice "No aplica hasta EN-02". Verificar: cada escenario tiene su prueba o una nota de por qué no aplica; commit del grupo (reglas de arriba)

## Workflow follow-up

- **(equipo)** Push de `feature/US-002-cerrar-sesion` y PR hacia `main`, con las verificaciones de EN-08 en verde.
- **(equipo)** Aprobación del PR por otra integrante (DoD 3).
- Después de la fusión: `/opsx:archive`. La siguiente historia sale de `main`, y su primer commit es este archivo.
- Pasada final de documentación con lo anotado en `insumos/pendientes-docs.md`.
