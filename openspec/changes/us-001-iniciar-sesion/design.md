# Design: US-001 – Iniciar sesión

## Context

La motivación y el alcance están en `proposal.md`. El comportamiento esperado está en `specs/inicio-sesion`, `specs/pantallas-de-inicio` y en los deltas de `entorno-desarrollo` e `integracion-continua`.

**Estado actual (rama `feature/US-001-iniciar-sesion`, sobre `main` con EN-01 y EN-08):**
- **`Usuario`** (`cuentas/models.py`):
  - Hereda de `AbstractUser`, con `rol` (DOCENTE, DIRECCION o ADMINISTRADOR) e `institucion`.
  - Ya tiene `intentos_fallidos` y `bloqueado_hasta`, creados en EN-01 para RN-024, así que no hace falta migración.
  - `create_superuser` fuerza el rol ADMINISTRADOR.
- **`UsuarioAdmin`:** hereda de `UserAdmin` y deja editables los campos de control.
- **Settings:** `USE_TZ = True`, `TIME_ZONE = "America/Lima"`, `APP_DIRS = True` y plantillas en `src/backend/templates/`. No hay `AUTHENTICATION_BACKENDS` ni `LOGIN_URL`.
- **Interfaz actual:**
  - `/` es `InicioView`, una página pública de EN-01.
  - `base.html` carga `app.css`, HTMX y Alpine en todas las páginas.
  - `app.css` solo importa Tailwind v4 y declara las carpetas `@source` de plantillas.
- **Prototipo aprobado:** `insumos/prototipo/US-001/prototipo/final/` (local, no se sube).
  - HTML estático con CSS propio de tipo BEM (`final.css`, unos 27 KB) sobre `tokens.css`, que es el bloque del Quick Start de DESIGN.md.
  - Dos scripts propios: `clave.js` y `portada.js`.
  - Alpine solo en la portada.
  - Mediciones y decisiones en `revision.md` (R-01 a R-31).
- **Canal (EN-08):**
  - El trabajo `Playwright` ya compila el CSS con `npm ci && npm run build` y corre `pytest -m e2e` en Chromium.
  - SonarQube Cloud analiza `src` y `scripts` con la puerta Sonar way: cobertura del código nuevo ≥ 80 % y duplicación ≤ 3 %.

**Restricciones:**
- **CLAUDE.md:** sin hex en las plantillas, sin desplazamiento horizontal salvo el carrusel, sin logo ni escudo, y las reglas de negocio en la capa de servicios. Para Django, HTMX, Tailwind, Alpine y Playwright se consulta Context7.
- **Consultas hechas en Context7 el 21/10/2026:**
  - Django 5.2: backends de autenticación, `LoginView`, `AuthenticationForm.confirm_login_allowed` y acciones del panel.
  - Tailwind v4: `@theme`, variables en CSS propio y la variante `dark` con `prefers-color-scheme`.
  - Alpine: `Alpine.data` dentro de `alpine:init`, con el script propio antes de Alpine.
  - Playwright Python: `emulate_media(color_scheme=…)`, `add_script_tag(path=…)` y `new_cdp_session`. En la versión 1.57 se quitó `page.accessibility` y se remite a Axe.
  - axe-core: `runOnly` por etiquetas WCAG.

## Goals / Non-Goals

**Goals:**
- Un solo camino de ingreso, el formulario y el backend, donde RN-024 no se puede saltar. Eso incluye al Administrador.
- Las plantillas de Django reproducen el prototipo G4e con los tokens de DESIGN.md y sin perder lo medido en el tramo 5: contraste, áreas táctiles, R-17 a R-31 y Slow 4G.
- La verificación de rol queda como una pieza reutilizable para las pantallas de cada rol que vengan después.

**Non-Goals:**
- Limitar intentos por IP o por dispositivo: RN-024 es por cuenta.
- Avisar que la cuenta está bloqueada. RF-001 lo prohíbe y queda como T-07 en `docs/PENDIENTES_TESIS.md`.
- Mantener la coherencia entre el rol ADMINISTRADOR y `is_staff` al crear cuentas (US-003), y revisar los permisos del panel (US-004).
- Medir cobertura del JavaScript propio con pruebas unitarias.
- Probar en Safari de iPhone y en WebKit (EN-07).

## Decisions

### D1. RN-024 en un backend propio que delega en la capa de servicios

- **`cuentas/servicios.py`:** funciones puras sobre un `Usuario` y la hora actual (`timezone.now()`, que se puede inyectar para las pruebas):
  - `esta_bloqueado(usuario, ahora)`;
  - `intentar_ingreso(usuario, contrasena, ahora) -> bool`;
  - `desbloquear(usuario) -> bool`;
  - constantes `INTENTOS_MAXIMOS = 5` y `DURACION_BLOQUEO = timedelta(minutes=15)`.
- **`cuentas/backends.py`:** `BackendConBloqueo(ModelBackend)`.
  - Sobrescribe solo `authenticate()`: busca la cuenta por `USERNAME_FIELD` y delega en `intentar_ingreso`.
  - `settings.AUTHENTICATION_BACKENDS = ["cuentas.backends.BackendConBloqueo"]`. Reemplaza a `ModelBackend`, porque si quedaran los dos, Django probaría el segundo y RN-024 se podría saltar.
  - Hereda los permisos de `ModelBackend` sin cambios.
- **`intentar_ingreso`**, dentro de `transaction.atomic()` y con `select_for_update()` sobre la fila de la cuenta, para que dos intentos simultáneos no se pisen el conteo:
  1. Siempre corre `check_password`, también si la cuenta está bloqueada. Así el tiempo de respuesta no delata el bloqueo, y no se pueden probar contraseñas durante el bloqueo midiendo tiempos.
  2. Si `bloqueado_hasta > ahora`, devuelve `False` sin tocar nada: los intentos no cuentan y el bloqueo no se extiende.
  3. Si la contraseña es incorrecta, suma 1 a `intentos_fallidos`. Al llegar a 5, fija `bloqueado_hasta = ahora + 15 min` y deja `intentos_fallidos = 0`, para que el conteo empiece de cero al terminar el bloqueo (escenario "Primer fallo después del bloqueo"). Devuelve `False`.
  4. Si la contraseña es correcta pero la cuenta está inactiva (`user_can_authenticate`), devuelve `False` y no reinicia nada: no es un ingreso.
  5. Si la contraseña es correcta y la cuenta puede entrar, pone `intentos_fallidos = 0` y `bloqueado_hasta = None`, y devuelve `True`.
- **Usuario inexistente:** el backend corre el hasher igual que `ModelBackend` (`Usuario().set_password(contrasena)`), así que no hay diferencia de tiempo que delate si la cuenta existe.
- **Alternativa descartada:** la lógica en `AuthenticationForm.clean()` o en la vista. Otro camino de ingreso, como el login del panel o un `authenticate()` en una historia futura, se la saltaría. Además, CLAUDE.md pide la lógica en servicios.
- **Alternativa descartada:** `django-axes` u otro paquete. Bloquea por IP y por combinación, con su propia tabla. Duplicaría los campos que ya fija el documento 11 y agregaría una dependencia para 5 reglas.
- **Alternativa descartada:** la señal `user_login_failed`. Llega después de que el backend decidió y no puede impedir el ingreso durante el bloqueo.

### D2. Formulario y vista de ingreso

- **`FormularioIngreso(AuthenticationForm)`:**
  - Etiquetas "Usuario" y "Contraseña".
  - `error_messages["invalid_login"]` = "Usuario o contraseña incorrectos, o cuenta inactiva".
  - `error_messages["inactive"]` = el mismo texto.
  - Mensajes de campo obligatorio: "Ingresa tu usuario." y "Ingresa tu contraseña.".
  - La segunda línea ("Revisa tus datos…") la pone la plantilla con el error no ligado a un campo, para respetar los dos pesos de DESIGN.md (R-27) sin HTML dentro del mensaje.
  - Con un campo vacío, `AuthenticationForm` no llama a `authenticate()`, así que no se cuenta un intento.
- **`IngresarView(LoginView)`:**
  - Usa ese formulario, la plantilla `cuentas/ingresar.html` y `redirect_authenticated_user = True`.
  - `get_default_redirect_url()` devuelve `pantalla_de_inicio(request.user)` (D3).
  - El parámetro `next` lo valida `LoginView` con `url_has_allowed_host_and_scheme`. Si apunta a la pantalla de otro rol, la verificación de rol (D3) redirige.
  - El formulario usa `novalidate`: la validación es del servidor, con los textos de DESIGN.md.
  - `LoginView` conserva el usuario escrito en el formulario con errores y no devuelve la contraseña.
- **`settings.LOGIN_URL = "ingresar"`**, para que `LoginRequiredMixin` y el panel lleven a `/ingresar/`.
- **Advertencia de Django sobre `redirect_authenticated_user`:** permite saber desde fuera si un visitante tiene sesión ("social media fingerprinting"). Se acepta porque el sistema no tiene recursos públicos que lo aprovechen. Queda en Riesgos.

### D3. Pantalla de inicio por rol y verificación reutilizable

- **`cuentas/acceso.py`:**
  - `pantalla_de_inicio(usuario) -> str`: DOCENTE → `reverse("docente:portada")`, DIRECCION → `reverse("direccion:inicio")`, ADMINISTRADOR → `reverse("admin:index")`.
  - `RolRequeridoMixin(LoginRequiredMixin)`, con el atributo `rol_requerido`. Sin sesión hace lo de `LoginRequiredMixin` (a `/ingresar/?next=…`). Con otro rol, `redirect(pantalla_de_inicio(usuario))`.
  - Es lo único de control de acceso que entra en US-001. La matriz completa del documento 08 y la denegación con registro son de US-004.
- **Rutas:**
  - `/docente/` en `cuentas` (`PortadaDocenteView`, namespace `docente`), porque es la pantalla de inicio del docente y no de una dimensión.
  - `/direccion/` en la app `direccion` (`InicioDireccionView`, namespace `direccion`), donde US-040 construirá los consolidados.
  - `/` es `RaizView` en `cuentas`: con sesión va a `pantalla_de_inicio`; sin sesión, a `/ingresar/`.
- **`/admin/login/`** se declara en `config/urls.py` antes de `admin.site.urls`:
  - Sin sesión, redirige a `/ingresar/` y conserva `next`.
  - Con sesión y sin `is_staff`, redirige a `pantalla_de_inicio`. Pero si esa pantalla es el panel (un ADMINISTRADOR sin `is_staff`, que solo se crea a mano), responde 403 para cortar el ciclo panel → login → panel. Hay una prueba para ese ciclo.
  - El panel conserva su propio cierre de sesión hasta US-002.
- **Alternativa descartada:** un decorador `rol_requerido` para vistas de función. El proyecto usa vistas de clase (`TemplateView`). Si una historia lo necesita, el mixin se envuelve.
- **Alternativa descartada:** `permission_required` o grupos de Django. Eso es lo que decidirá US-004 con la matriz del documento 08, y adelantarlo fijaría su diseño.

### D4. Acción "Desbloquear cuenta" en el panel

- `UsuarioAdmin.actions = ["desbloquear_cuenta"]`, con `@admin.action(description="Desbloquear cuenta")`.
- Por cada cuenta seleccionada llama a `servicios.desbloquear(usuario)`, que deja `intentos_fallidos = 0` y `bloqueado_hasta = None` y devuelve si cambió algo.
- Si cambió algo, `self.log_change(request, usuario, "Cuenta desbloqueada.")`, que crea un `LogEntry` en el historial con autor y fecha.
- Termina con `message_user`: cuántas se desbloquearon y cuántas no tenían nada que desbloquear.
- `intentos_fallidos` y `bloqueado_hasta` pasan a `readonly_fields`. Así el único camino para desbloquear es la acción, con un mensaje claro en el historial, y no un cambio de campos a mano.
- `list_display` suma `bloqueado_hasta`.
- `log_change` no está en la documentación de `ModelAdmin` (Context7 solo muestra el cambio de nombre de su argumento en Django 4.0), pero es lo que usa el propio panel al guardar. **Verificación en la implementación:** confirmar que existe en Django 5.2 y que el historial lo muestra. Si no, se usa `LogEntry.objects.log_actions(...)`.

### D5. Plantillas, tokens y CSS

- **`src/frontend/css/app.css`** pasa a tener:
  1. El bloque `@theme` del Quick Start de DESIGN.md, copiado tal cual, junto con la redefinición oscura en `:root` dentro de `@media (prefers-color-scheme: dark)` y el `--text-display` de PC. Es el único lugar con hex.
  2. El `@font-face` de Besley 600 (`font-display: swap`).
  3. `@layer components` con los componentes del prototipo que no se expresan bien con utilidades: tarjeta G4e (enlace estirado con `::before` para el anillo de foco y `::after` para el toque, R-17 y R-21), miniaturas esquemáticas, carrusel (`scroll-snap`, líneas de tiempo de desplazamiento con `@supports`), chips, puntos, mensaje y campo de contraseña. Solo usan `var(--color-*)`, `var(--radius-*)` y `var(--spacing-*)`.
- **Las plantillas** usan utilidades de Tailwind generadas por los tokens (`bg-fondo`, `text-primario`, `rounded-dimension`…) y las clases de componente. No llevan hex ni `style=`.
- **`tests/test_plantillas.py`** recorre `src/backend/**/templates/**/*.html` y falla ante `#[0-9a-fA-F]{3,8}\b` o `style=`. Es el escenario "Plantillas sin colores escritos".
- **Estructura de las plantillas:**
  - `base.html`: `lang="es-PE"`, `color-scheme`, el `preload` de la fuente, `app.css` y un bloque `scripts` vacío.
  - `marco.html`: barra y pie, para las pantallas internas.
  - `cuentas/ingresar.html`, `cuentas/portada_docente.html` y `direccion/inicio.html`.
  - Parciales: `componentes/tarjeta_dimension.html`, que se incluye en un bucle para que SonarQube no vea duplicación, `componentes/miniatura_<dimension>.html` y `iconos/<nombre>.svg`.
- **Alternativa descartada:** copiar `final.css` como hoja aparte. Quedarían dos fuentes de verdad de los tokens (`tokens.css` y `@theme`), y las utilidades de Tailwind no verían los nombres.
- **Alternativa descartada:** todo con utilidades. Los pseudoelementos, el `@supports` del carrusel y las líneas de tiempo de desplazamiento quedarían en atributos `class` larguísimos y difíciles de revisar contra el prototipo.
- **Fidelidad:** el HTML de cada plantilla sigue la estructura de la pantalla del prototipo, con sus roles ARIA, `aria-live`, `aria-current`, `aria-describedby`, ": ver tarjeta" para el lector, y los nombres "Accesos" y "Tus accesos". Las capturas del tramo 8 se comparan contra `capturas/final/`.

### D6. Scripts por pantalla

- **`base.html`** deja de cargar HTMX y Alpine en todas las páginas. Cada plantilla los pide en el bloque `scripts`.
- **Inicio de sesión:**
  - Solo `static/js/ingresar.js`, que es `clave.js` del prototipo más el estado de envío (spec "Estado de envío").
  - Al enviar con los dos campos llenos, el botón pasa a "Ingresando…" con la clase de envío, los campos quedan en `readOnly` y el botón en `aria-disabled`.
  - No usa `disabled`, porque un botón deshabilitado antes del envío no se envía.
  - Sin JavaScript, el formulario funciona igual.
- **Portada:** `static/js/portada.js` (el del prototipo: `carrusel` y `proxima`), seguido de `dist/vendor/alpine.min.js`, los dos con `defer` y en ese orden, como pide Alpine (`alpine:init`).
- **HTMX:** se sigue copiando a `dist/vendor/` (EN-01), pero ninguna pantalla de US-001 lo carga, porque no hay nada que lo use. Lo pedirá la primera historia que lo use, previsiblemente US-030 con el guardado por toque. Así el inicio de sesión transfiere menos con Slow 4G.
- El JavaScript propio va en `src/backend/static/js/` (versionado), no en `dist/`.

### D7. Bandera de disponibilidad por dimensión

- **`cuentas/dimensiones.py`:** una tupla de `Dimension(clave, titulo, subtitulo, verbo, icono, url_name, disponible)` en orden: Sesiones, Notas y Asistencia. En US-001, las tres van con `disponible=False` y `url_name=None`.
- La historia de cada dimensión cambia su entrada: US-030 pone `disponible=True` y `url_name="asistencia:…"`.
- La plantilla solo dibuja un enlace si `disponible`. Si no, dibuja el botón con `aria-disabled` de "Próximamente".
- **`test_dimensiones.py`:**
  - Toda dimensión disponible tiene un `url_name` que `reverse()` resuelve (escenario "Bandera activa sin pantalla").
  - Hoy ninguna está disponible.
- **Tarjeta inicial del carrusel:** la primera disponible en el orden de las tarjetas o, si no hay ninguna, la primera. Coincide con DESIGN.md en los dos estados descritos: Sprint 1, solo Asistencia, abre en Asistencia; estado final abre en Sesiones. Se marca con `carrusel__item--inicial` y `scroll-initial-target`, con respaldo en `portada.js` como en el prototipo.
- **Alternativa descartada:** banderas en variables de entorno o en la base de datos. Permitirían activar una dimensión sin su pantalla desplegada, que es justo lo que el spec prohíbe, y agregan configuración que nadie va a cambiar en el piloto.

### D8. Datos que muestran las pantallas

- **Saludo:** "Hola, {nombre completo}", con `get_full_name()` y, si está vacío, el usuario.
  - El prototipo dice "Prof. Ana Quispe" o "Lic. Rosa Huamán", pero el modelo no tiene tratamiento ni título, y no se inventa (DESIGN.md, Voz).
  - Si el equipo quiere el tratamiento, es un campo nuevo en otra historia.
- **Línea bajo el saludo:**
  - Docente: no se muestra hasta US-005, que asigna grado y sección. El prototipo dice "3.° grado, sección A" y en US-001 sería un dato falso.
  - Dirección: "Dirección".
- **Estado vacío de la dirección:** el texto de R-23 y el ícono del prototipo, bajo el título "Consolidados".
- **Diferencia con RF-001 y US-001 ("panel de consolidados"):** la dirección llega a su inicio, donde vivirá ese panel (US-040). Se anota en Pendientes de documentación. No cambia el escenario: llega a su pantalla.

### D9. Fuente e íconos

- **Fuente** (decisión del usuario del 22/10/2026, que reemplaza la versionada): `@fontsource/besley` por npm, como HTMX y Alpine. `copiar-vendor.mjs` copia `files/besley-latin-600-normal.woff2` (18 916 bytes en la 5.3.0) y su `LICENSE` (SIL OFL 1.1) a `static/dist/fuentes/`, que no se versiona; la versión queda fijada en `package-lock.json`. `preload` en `base.html`.
  - Frente al subconjunto del prototipo (17 352 bytes): +1,5 KB, despreciable frente a los 2 MB de RNF-002. Su rango `latin` (U+0000-00FF, U+2000-206F y otros) cubre el español; los glifos se revisan en las capturas de 5.5 y del tramo 8 contra `capturas/final/`.
- **Íconos:** SVG incrustados con `{% include "iconos/<nombre>.svg" %}`, con `aria-hidden="true"`, `focusable="false"`, `stroke="currentColor"` y `stroke-width="1.75"` (R-20).
  - Solo los usados: `eye`, `eye-off`, `circle-alert`, `arrow-right`, los de las tres dimensiones y el del estado vacío. Los nombres exactos se toman del prototipo.
  - `templates/iconos/LICENSE-lucide.txt` lleva el aviso ISC de Lucide 1.52.0.
- **Sobre CLAUDE.md** ("nunca subir archivos de terceros"): la fuente ya no se versiona. Los trazados de Lucide sí, incrustados en las plantillas, con su aviso ISC: entran por decisión explícita del usuario (22/10/2026).
- **Alternativa descartada:** versionar `besley-600-latin.woff2` y `OFL.txt` del prototipo en `static/fuentes/`. Era la opción inicial; el usuario eligió npm porque Besley 600 latina está publicada en Fontsource, y así no entra al repositorio un archivo de terceros.

### D10. Pruebas

Ejecución con pruebas primero: cada prueba se ve fallar antes del código.

- **Unitarias (`pytest`):**
  - `test_servicios_bloqueo.py`: la hora se pasa como argumento. Cubre los cinco pasos de D1, el bloqueo exacto al quinto fallo, el bloqueo que no se extiende, el fin a los 15 minutos (y no a los 14:59), el reinicio con un ingreso correcto, la cuenta inactiva y `desbloquear`.
  - `test_backend.py`: `authenticate()` con un usuario inexistente, con una cuenta bloqueada y la contraseña correcta, y con una cuenta inactiva. Comprueba que `ModelBackend` no está en `AUTHENTICATION_BACKENDS`.
  - `test_ingresar.py`: GET y POST con el cliente de Django. Cubre los escenarios de `inicio-sesion`: mensaje idéntico en los cuatro rechazos (se compara el HTML del mensaje), el usuario conservado, campos vacíos sin intento contado, redirección por rol, `next`, sesión ya iniciada y `/admin/login/`.
  - `test_acceso.py`: `RolRequeridoMixin` con los tres roles en las dos pantallas, sin sesión, y el ciclo del ADMINISTRADOR sin `is_staff`.
  - `test_admin.py` (ampliado): la acción sobre una cuenta bloqueada, sobre una que no lo está y sobre varias. Revisa el `LogEntry`, el mensaje y los campos de solo lectura.
  - `test_pantallas.py`: contenido de las tres pantallas, como textos, orden y ausencia de enlaces y de escudo; scripts que carga cada una; `test_dimensiones.py` y `test_plantillas.py`.
  - Las pruebas de RN-024 cuentan como la DoD 6 (reglas de negocio con pruebas propias).
- **De punta a punta (`pytest -m e2e`, Chromium):**
  - `test_ingresar_e2e.py`: reemplaza a `test_inicio_e2e.py`. Recorre el escenario "Página inicial en el navegador" y la ruta ideal de la DoD 5; prueba "Mostrar contraseña" con y sin JavaScript y el estado de envío.
  - `test_portada_e2e.py`: chip sin historial (R-19), "Llegará en una próxima versión." y desborde horizontal a 320, 360 y 1280 en ambos temas.
  - `test_accesibilidad_e2e.py`: axe-core en las 5 vistas (ingresar normal, con error y con campos vacíos; portada; dirección) × 2 temas (`page.emulate_media`) × 2 anchos.
  - `test_rendimiento_e2e.py`: Slow 4G (D11).
- **Accesibilidad con axe-core**, inyectado con `page.add_script_tag(path=…)` desde `src/frontend/node_modules/axe-core/axe.min.js`:
  - `axe.run` con `runOnly: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]`.
  - La prueba falla ante cualquier infracción con `impact` "critical" o "serious". El contraste insuficiente es "serious" en axe; así se cubre el umbral de 4,5:1 de RNF-008.
  - El informe (reglas, nodos e impacto) se imprime al fallar y se guarda en `test-results/`.
  - **Por qué axe-core por npm:** es el motor que la documentación de Playwright recomienda desde que quitó `page.accessibility` (1.57). Llega por npm, que el proyecto y el canal ya usan, con su versión fijada en `package-lock.json`. No agrega dependencias de Python.
  - **Alternativa descartada:** `axe-playwright-python` (PyPI). Es un envoltorio de terceros sobre el mismo axe-core, con su propia versión empaquetada y menos mantenimiento.
  - **Alternativa descartada:** Lighthouse. Pide Node y Chrome aparte, y mezcla rendimiento con accesibilidad.
- **Datos:** solo ficticios, creados por cada prueba (DoD 8): "Ana Quispe" y "Rosa Huamán" de DESIGN.md, con contraseñas generadas en la prueba.

### D11. Medición de RNF-002

- **`test_rendimiento_e2e.py`**, solo en Chromium:
  - Abre una `new_cdp_session` con `Network.enable`, `Network.setCacheDisabled` y `Network.emulateNetworkConditions`.
  - Usa el perfil Slow 4G de DevTools, el mismo del prototipo (`capturas.py`): bajada de 1,6 Mbps × 0,9, subida de 750 kbps × 0,9 y latencia de 150 ms × 3,75.
- **Bytes:** suma de `encodedDataLength` de `Network.loadingFinished`. Umbral ≤ 2 MB.
- **Usable:** desde `goto` hasta que se cumplen las tres condiciones: evento `load`, `document.fonts.ready` y el botón "Ingresar" visible y habilitado. Umbral ≤ 5 s.
- Las cifras medidas se anotan en `verificacion.md`. El prototipo dio 50 KB y un primer pintado a 1,5 s.
- **`live_server`** sirve los estáticos sin compresión, así que la medición es pesimista frente a producción, que sí comprime. Se acepta: si pasa sin compresión, pasa con ella.

### D12. SonarQube Cloud y el JavaScript propio

- `ingresar.js` y `portada.js` son código nuevo en `src/` que SonarQube analiza, pero ningún informe de cobertura los cubre. Sin un ajuste, bajarían la cobertura del código nuevo y la puerta Sonar way fallaría.
- **Solución:** `sonar.coverage.exclusions=**/static/js/**` en `sonar-project.properties`. Siguen analizados por fiabilidad, seguridad y duplicación; solo no cuentan para la cobertura, porque los prueban las pruebas de punta a punta.
- **Alternativa descartada:** medir la cobertura del JavaScript con Playwright (`page.coverage`, solo Chromium) y convertirla a LCOV. Es mucha infraestructura para unas 100 líneas.

### D13. Falla intermitente de pytest en `verificar.py`

- **Lo que se sabe:**
  - Una corrida de `verificar.py --antes-del-commit` del 21/10/2026 dio FALLA en pytest, con una cobertura de 95,13 % en lugar de 95,68 %. No se guardó la salida.
  - El 21/10/2026, otras 10 corridas seguidas de `uv run pytest --cov --cov-fail-under=80` pasaron: 284 pruebas y 95,68 % en las 10.
  - Que la cobertura haya bajado indica que una parte del código no se ejecutó. No es solo una aserción fallida.
- **Hipótesis, en el orden en que se investigan:**
  1. **Dos ejecuciones de pytest al mismo tiempo.** Las dos crean y borran la misma base `test_carpetadocente` de pytest-django. Puede pasar si `verificar.py` corre mientras otra terminal o un agente corre pytest.
  2. **Pruebas que llaman a `uv run`** dentro de un repositorio temporal (`test_hook_real_*`, por los hooks reales). En Windows pueden chocar con el bloqueo del entorno virtual que tiene el `uv run pytest` de fuera.
  3. **Borrado de archivos de solo lectura en Windows** (`test_reemplaza_destino_con_archivos_de_solo_lectura`). Puede fallar a veces por el antivirus, como el `OSError 22` que se vio al escribir PNG en el tramo 5.
- **Método:**
  - 30 corridas seguidas con `-rfE` y `--junitxml` por corrida.
  - Luego, dos corridas en paralelo, para la hipótesis 1.
  - Luego, las pruebas de las hipótesis 2 y 3 repetidas cada una 50 veces con un bucle de la terminal (sin agregar `pytest-repeat`).
  - Ante una falla, se aplica la habilidad de depuración sistemática.
- **Corrección:** depende de la causa.
  - Hipótesis 1: `verificar.py` detecta otra ejecución activa y lo dice, o cada ejecución usa un nombre de base propio.
  - Hipótesis 2: las pruebas reales de hooks pasan a usar el intérprete actual sin `uv run`.
  - Hipótesis 3: reintento acotado en el borrado.
- **Haya o no causa:** `verificar.py` guarda la salida completa de pytest en `.verificar/pytest-<fecha>.txt` (ignorado por git) cuando falla, y su resumen dice dónde quedó. Así una próxima falla no se pierde.
- Si no se reproduce, se anota en `verificacion.md` con el número de corridas y queda solo el registro de la salida.
- **Resultado de la implementación (22/10/2026, `verificacion.md`, sección 1):**
  - La causa es la hipótesis 1. Se reprodujo en 5 de 5 pares; las hipótesis 2 y 3 dieron 50 de 50 en verde.
  - Cada ejecución de pytest usa su propia base, `test_<nombre>_<pid>` (`src/backend/conftest.py`, con `django_db_modify_db_settings`).
  - Las ejecuciones simultáneas también comparten el archivo `.coverage` de la raíz. `verificar.py` corre pytest con su propio `COVERAGE_FILE` en `.verificar/`.
  - En 50 pares de `verificar.py` junto a un `pytest --cov` común, `verificar.py` pasó 50 de 50.
- **Limitación conocida:** dos `pytest --cov` comunes lanzados a la vez en la misma máquina todavía pueden chocar al combinar el `.coverage` de la raíz.
  - Pasa fuera de `verificar.py`, por ejemplo con dos terminales. En los 50 pares, el pytest común de al lado falló 3 veces, siempre en un `INTERNALERROR` de coverage y con todas sus pruebas en verde.
  - No ocurre en CI: cada trabajo corre en su propio ejecutor, con su propio PostgreSQL, y lanza un solo pytest.
  - Aislar el `.coverage` de cualquier pytest cambia la configuración de pruebas de todo el equipo. Queda como un chore aparte, fuera de US-001. La tarea 1.3 queda sin marcar, porque su criterio literal (0 fallas en 50 para la hipótesis 1) no se cumple para ese caso.

### D14. Catálogo de rutas y documentación

- **`docs/03 Implementación/Catálogo de rutas.md`**, versión 1.1.0:
  - Filas para `/` (redirección), `/ingresar/`, `/docente/`, `/direccion/`, `/admin/login/` (redirección) y `/admin/`, con su acceso por rol.
  - Se quita la nota "exigirá sesión con EN-04".
  - Fila en el historial.
  - El archivo no lleva la versión en el nombre, así que solo cambia su contenido.
- **README:**
  - Las pruebas `e2e` ahora necesitan `npm ci` (por axe-core), que ya estaba en los pasos.
  - Cómo correr solo accesibilidad o solo rendimiento.
  - La fila `Playwright` de la tabla del canal.

### D15. Cierre: DoD y crítica aislada

- **`verificacion.md`** del cambio, con el mismo formato que EN-08: evidencia de cada escenario y estado de la DoD 1 a 9.
  - **DoD 4:** no aplica hasta EN-02.
  - **DoD 6:** cubierta por las pruebas de RN-024 (D10).
  - **DoD 7:** el informe de axe en ambos temas (D10).
  - **DoD 9:** OpenSpec, docstrings y catálogo de rutas (D14). El documento 06 ya subió a V_1_5_0 en esta rama.
- **Tramo 8, crítica aislada de Impeccable sobre las plantillas construidas:**
  - `critique` con dos subagentes aislados (A, revisión de diseño; B, detector y navegador), contra la aplicación levantada en local, en claro y en oscuro, a 360 y a 1280.
  - Se corre también `impeccable detect` sobre las URL, con la exención R-10 de `.impeccable/config.json`. En US-001 puede no hacer falta, porque ninguna tarjeta está disponible y la sombra de la ficha no aparece.
  - Los informes quedan en `insumos/prototipo/US-001/tramo8/`, que es local.
  - **Antes de lanzar los subagentes se avisa al usuario.** No se lanza `impeccable-documenter` ni `impeccable-finish-reviewer` sin su aviso.
  - DESIGN.md no se reescribe: si la crítica pide cambiarlo, se muestra el diff y se espera la aprobación.

## Risks / Trade-offs

- **[Cualquiera puede bloquear una cuenta ajena]** con 5 intentos (denegación de servicio por cuenta). → Lo acepta RN-024. Lo mitiga la acción "Desbloquear cuenta" y el bloqueo dura 15 minutos. El límite por IP queda para EN-04 si el piloto lo muestra.
- **[La docente bloqueada no sabe que debe esperar]** (R-29, T-07). → Lo exige RF-001 y es decisión del equipo; queda en `docs/PENDIENTES_TESIS.md`.
- **[Un ADMINISTRADOR sin `is_staff`]** termina en 403 al ingresar. → Pasa solo con cuentas creadas a mano. `create_superuser` pone `is_staff`. US-003 hará coherentes el rol y `is_staff`.
- **[`redirect_authenticated_user` permite saber desde fuera si hay sesión]** (advertencia de Django). → El sistema no tiene recursos públicos aprovechables y en US-001 no hay imágenes. Se revisa con EN-04.
- **[Token CSRF vencido en el celular]**, por ejemplo con la pestaña abierta varios días: muestra la página 403 genérica de Django. → Fuera de alcance. Se anota como mejora con US-002 (página propia de CSRF y de sesión vencida).
- **[La medición de Slow 4G en el canal varía con la carga del ejecutor]** de GitHub. → La red simulada domina el tiempo. El umbral de 5 s tiene margen frente a los 1,5 s del prototipo. Si falla en el canal y no en local, se investiga antes de tocar el umbral.
- **[El carrusel no se prueba en Safari ni en Firefox en el canal].** → Chromium en el canal. Firefox se prueba a mano en local antes del PR y se anota en `verificacion.md`. Safari de iPhone queda pendiente de un equipo real (revisión del tramo 5, pendiente 2; EN-07).
- **[`@layer components` crece con cada pantalla].** → Una clase por componente de DESIGN.md, con el mismo nombre. Los componentes nuevos se agregan con su historia.
- **[Las plantillas se apartan del prototipo sin que nadie lo note].** → Las capturas del tramo 8 se comparan con `capturas/final/`, y la crítica aislada revisa las plantillas.

## Migration Plan

- **Sin migración de datos:** los campos de RN-024 ya existen.
- **Al desplegar (cuando exista EN-02):** las cuentas existentes empiezan con 0 intentos y sin bloqueo. Cualquier marcador viejo de la página inicial lleva a `/ingresar/`.
- **Para volver atrás:** revertir el PR. Al no haber migraciones, la base no cambia.

## Open Questions

- ¿Se muestra el tratamiento ("Prof.", "Lic.") en el saludo? Hoy no hay dónde guardarlo (D8). Se puede decidir más adelante sin cambiar este diseño.
- **Pendientes de documentación**, para proponer al equipo aparte, con subida de versión. Ninguno cambia el comportamiento de US-001:
  - RF-001 (documento 06) y US-001 (documento 02/01), escenario "Flujo alternativo válido": "panel de consolidados" frente al inicio de la dirección con estado vacío hasta US-040 (D8).
  - Documento 10 o README: HTMX no se carga en las pantallas que no lo usan (D6).
