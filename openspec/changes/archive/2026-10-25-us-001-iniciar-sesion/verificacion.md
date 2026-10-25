# Verificación de US-001

Rama: `feature/US-001-iniciar-sesion` · Laptop Windows 11 con Docker Desktop · Django 5.2.18, Python 3.13.16, pytest 9.1.1, pytest-django 4.14.0.

## 1. Falla intermitente de pytest (D13)

### 1.1 Treinta corridas seguidas

Fecha: 22/10/2026. Con `db` levantado (`docker compose up -d db`), 30 corridas seguidas de:

```text
uv run pytest --cov --cov-fail-under=80 -rfE --junitxml=<scratchpad>/corrida-N.xml
```

La salida de cada corrida y su XML quedaron fuera del repositorio, en el scratchpad de la sesión (`g1/serie30/`).

| Corridas | Pasaron | Fallaron | Pruebas por corrida | Cobertura | Duración |
| --- | --- | --- | --- | --- | --- |
| 30 | 30 | 0 | 284 pasan, 4 deseleccionadas (`e2e`) | 95,68 % en las 30 | 10 a 13 s |

Nota: hacia las corridas 12 y 13 se creó por unos segundos un `conftest.py` de borrador en `cuentas/tests/` (solo cambia el hasher de esas pruebas) y se retiró enseguida; ninguna corrida cambió de resultado ni de cobertura.

La falla no se reproduce corriendo pytest solo.

### 1.2 Hipótesis de D13

#### Hipótesis 1: dos corridas de pytest al mismo tiempo

Fecha: 22/10/2026. Cinco pares de `uv run pytest --cov --cov-fail-under=80 -rfE` lanzados a la vez (`g1/h1/`).

| Par | Corrida A | Corrida B |
| --- | --- | --- |
| 1 | **284 errores** (53,7 s) | 284 pasan (10,3 s) |
| 2 | 284 pasan | **284 errores** |
| 3 | 284 pasan | **284 errores** |
| 4 | 284 pasan | **284 errores** |
| 5 | **284 errores** | 284 pasan |

**Se reproduce en los 5 pares.** Las dos corridas usan la misma base de pruebas, `test_carpetadocente`. La que llega segunda no puede crearla:

```text
_______________ ERROR at setup of test_conexion_es_a_postgresql _______________
sql = 'CREATE DATABASE "test_carpetadocente" ', params = None
E           psycopg.errors.UniqueViolation: duplicate key value violates unique constraint "pg_database_datname_index"
E           DETAIL:  Key (datname)=(test_carpetadocente) already exists.
Got an error creating the test database: duplicate key value violates unique constraint "pg_database_datname_index"
```

Los dos `CREATE DATABASE` chocan en el catálogo de PostgreSQL. Ese error no es `DuplicateDatabase`, así que Django (`postgresql/creation.py`, `_execute_create_test_db`) lo trata como cualquier otro y sale con `SystemExit: 2`: todas las pruebas de esa corrida quedan en error.

Con otro desfase, la base ya existe y el error sí es `DuplicateDatabase`. Entonces Django, sin preguntar (pytest-django no es interactivo), borra la base y la crea de nuevo. Si lo logra mientras la otra corrida está a mitad de camino, esa corrida pierde su base: falla una parte de sus pruebas y la cobertura baja un poco. Es la explicación más probable del síntoma del 21/10/2026 (FALLA con 95,13 % en lugar de 95,68 %), pero en estos 5 pares no se observó: las dos corridas arrancaron casi juntas y salió siempre la variante "todo en error".

Observación aparte: las corridas en error también informan 95,68 %. Las dos escriben el mismo archivo `.coverage` de la raíz, así que el total de una corrida puede mezclar datos de la otra. No se corrige en US-001 (ver "Dudas y pendientes" en el avance); con bases separadas, las dos corridas pasan y miden lo mismo.

#### Hipótesis 2: pruebas que llaman a `uv run` dentro de un repositorio temporal

Fecha: 22/10/2026. `uv run pytest -q -rfE -p no:cacheprovider scripts/tests/test_hooks.py -k test_hook_real --no-cov`, 50 veces seguidas (`g1/h2/`): **50 de 50 pasan** (3 pruebas cada vez, unos 2,1 s). No se reproduce.

#### Hipótesis 3: borrado de archivos de solo lectura en Windows

Fecha: 22/10/2026. `uv run pytest -q -rfE -p no:cacheprovider "scripts/tests/test_copiar_para_proyecto.py::test_reemplaza_destino_con_archivos_de_solo_lectura" --no-cov`, 50 veces seguidas (`g1/h3/`): **50 de 50 pasan** (0,09 a 0,12 s). No se reproduce.

#### Conclusión

La causa es la hipótesis 1: dos ejecuciones de pytest comparten el nombre de la base de pruebas. Las hipótesis 2 y 3 no se reproducen y no se tocan.

### 1.3 Corrección de la hipótesis 1

#### Base de pruebas propia por ejecución (prueba primero)

- Prueba nueva: `config/tests/test_base_datos.py::test_cada_ejecucion_de_pytest_usa_su_propia_base`. En rojo antes de la corrección (`'test_carpetadocente'.endswith('_24004')` es falso).
- Corrección: `src/backend/conftest.py` redefine `django_db_modify_db_settings`, el punto que documenta pytest-django para cambiar la base de pruebas, y le pone el número del proceso: `test_<nombre>_<pid>`. Conserva el sufijo de xdist y tox. En verde; Django la borra al terminar (comprobado en `pg_database`).

#### Segunda pieza compartida: el archivo `.coverage`

Con la base corregida, 15 pares de `pytest --cov` común (`g1/h1-corregida/`, en una copia del repositorio): las 291 pruebas pasaron en las 30 corridas, sin ningún error de base. Pero 10 corridas terminaron con código 3, en un `INTERNALERROR` de coverage al combinar los datos:

```text
INTERNALERROR> sqlite3.OperationalError: no such table: file
INTERNALERROR> PermissionError: [WinError 5] Acceso denegado: '…\copia-g1\.coverage'
```

pytest-cov guarda los datos de cada proceso en `.coverage.<equipo>.<pid>.<azar>` y al final combina todos los `.coverage.*` de la carpeta: también los del otro pytest, que todavía está escribiendo.

- Prueba primero, en `scripts/tests/test_verificar.py`: pytest se corre con un `COVERAGE_FILE` propio; `ejecutar` agrega ese entorno solo al comando que lo pide; el archivo se borra al terminar. En rojo y luego en verde.
- Corrección: `verificar.py` corre pytest con `COVERAGE_FILE=.verificar/.coverage-<pid>` y lo borra al terminar. La cobertura que informa sale igual de la salida de pytest. Una corrida real en la laptop: `[OK] pytest --cov (mínimo 80 %)`, 96,02 %, sin archivos en la raíz.

#### Repetición de la hipótesis 1: 50 pares

Fecha: 22/10/2026. En una copia del repositorio con todo lo anterior (`g1/h1-final/`), 50 pares de `uv run python scripts/verificar.py` real junto a un `uv run pytest --cov --cov-fail-under=80 -rfE` común, lanzados a la vez:

| Proceso | Pasaron | Fallaron |
| --- | --- | --- |
| `verificar.py` (línea de pytest) | **50** | **0** |
| `pytest --cov` común, al mismo tiempo | 47 | 3 (pares 10, 11 y 14), con las 318 pruebas en verde y un `INTERNALERROR` de coverage al combinar: dos `PermissionError: [WinError 32] … está siendo utilizado por otro proceso` al borrar su archivo de datos y un `DataError: no such table: other_db.file` |

Control: 20 corridas del mismo `pytest --cov` común, **solo**, en la misma copia (`g1/solo-copia/`): 20 de 20 en verde. El residuo aparece solo con otra corrida al mismo tiempo.

**Resultado:** el caso de D13 (`verificar.py` mientras otra terminal corre pytest) queda corregido: 0 fallas de `verificar.py` en 50 pares y ninguna falla de base de datos. El criterio literal de la tarea (0 fallas en 50 para la hipótesis 1) **no se cumple** para el pytest común que corre al lado, que falló 3 veces en la combinación de coverage. Que dos pytest comunes no choquen en `.coverage` pediría cambiar la configuración de pruebas de todo el equipo (por ejemplo, un plugin propio que fije `COVERAGE_FILE` antes de que arranque pytest-cov). Decisión del 22/10/2026: el residuo queda documentado en D13 (`design.md`) como limitación conocida (dos pytest simultáneos en la misma máquina; no ocurre en CI), el aislamiento global de `.coverage` queda como un chore aparte, fuera de US-001, y la tarea 1.3 se deja sin marcar.

### 1.4 Registro de la salida de pytest

Prueba primero en `scripts/tests/test_verificar.py` (5 en rojo y luego en verde): cuando pytest falla, `verificar.py` guarda la salida completa en `.verificar/pytest-AAAAMMDD-HHMMSS.txt` y su resumen dice "salida completa en .verificar/…"; cuando pasa, no guarda nada. `.verificar/` está en `.gitignore`:

```text
$ git check-ignore -v .verificar/prueba.txt
.gitignore:21:.verificar/	.verificar/prueba.txt
```

`git status` no lista `.verificar/`. `uv run pytest --cov`: en verde.

## 2. Servicio de bloqueo y backend de autenticación (D1)

Fecha: 22/10/2026. Prueba primero: `test_servicios_bloqueo.py` en rojo porque `cuentas.servicios` no existía (`ImportError`); `test_backend.py` con 4 en rojo (único backend, cuenta bloqueada, intento contado por `authenticate()` y versión asíncrona). Los otros 5 casos de `test_backend.py` (usuario inexistente con hash, cuenta inactiva, datos correctos, sin usuario y sin contraseña) ya los cumplía `ModelBackend` y se comprobó que siguen igual.

```text
$ uv run pytest src/backend/cuentas/tests/test_servicios_bloqueo.py src/backend/cuentas/tests/test_backend.py
23 passed
```

- `ModelBackend.aauthenticate` de Django 5.2 no pasa por `authenticate()`: `BackendConBloqueo` también la redefine, para que un ingreso asíncrono no se salte RN-024 (prueba `test_la_version_asincrona_tambien_respeta_el_bloqueo`).
- `settings.AUTHENTICATION_BACKENDS == ["cuentas.backends.BackendConBloqueo"]`. Las pruebas de `test_admin.py` existentes siguen en verde.
- Cobertura: `servicios.py` y `backends.py` al 100 %.

## 3. Ingreso, pantalla de inicio por rol y redirecciones (D2, D3)

Fecha: 22/10/2026. Prueba primero: `test_acceso.py` en rojo (`ModuleNotFoundError: cuentas.acceso`, luego 12 de 15 en rojo por las rutas que faltaban) y `test_ingresar.py` con 24 de 25 en rojo. La que pasaba (`test_login_del_panel_ignora_un_next_externo`) lo hacía porque el login propio del panel ya devolvía al staff; sigue valiendo con `IngresoPanelView`.

```text
$ uv run pytest src/backend/cuentas/tests/test_acceso.py src/backend/cuentas/tests/test_ingresar.py
40 passed
```

- Mutación de control: sin el `PermissionDenied` del ADMINISTRADOR sin `is_staff` y sin el filtro de `next` a `/ingresar/`, fallan `test_administrador_sin_is_staff_recibe_403_sin_ciclo` y `test_ingresar_con_sesion_y_next_a_ingresar_no_falla`. Se revirtió.
- Plantillas `cuentas/ingresar.html`, `cuentas/portada_docente.html` y `direccion/inicio.html`: **mínimas y provisionales**, marcadas como tales; las reemplazan 5.5 y 5.7.
- Se quitaron `InicioView`, `inicio.html`, `test_inicio.py` y `test_inicio_e2e.py` (este importaba de `test_inicio.py` y probaba la página de EN-01). Hasta 6.2, `pytest -m e2e` no junta pruebas.

### 3.6 Catálogo de rutas

`docs/03 Implementación/Catálogo de rutas.md` a la versión 1.1.0. Rutas registradas en Django (`get_resolver().url_patterns`) frente a las filas del catálogo:

```text
''             raiz              → fila /
'ingresar/'    ingresar          → fila /ingresar/
'docente/'     docente:portada   → fila /docente/
'direccion/'   direccion:inicio  → fila /direccion/
'admin/login/' ingreso_panel     → fila /admin/login/
'admin/'       admin             → fila /admin/
```

Seis rutas y seis filas; ninguna fila apunta a una ruta que no existe.

## 4. Acción "Desbloquear cuenta" en el panel (D4)

### 4.1 `ModelAdmin.log_change` en Django 5.2

Fecha: 22/10/2026. Revisado en el código instalado (`.venv`, Django 5.2.18):

- `django/contrib/admin/options.py`, línea 962: existe `ModelAdmin.log_change(self, request, obj, message)`. Crea el registro con `LogEntry.objects.log_actions(user_id=request.user.pk, queryset=[obj], action_flag=CHANGE, change_message=message, single_object=True)`: autor, objeto y fecha (`action_time`) quedan en el `LogEntry`.
- `django/contrib/admin/models.py`, `LogEntry.get_change_message()`: si el mensaje no empieza con `[` (no es el JSON que arma el panel), lo devuelve tal cual.
- `templates/admin/object_history.html`, línea 32: el historial del objeto muestra `{{ action.get_change_message }}`.

Conclusión: `self.log_change(request, usuario, "Cuenta desbloqueada.")` deja "Cuenta desbloqueada." en el historial de la cuenta, con autor y fecha. No hace falta llamar a `LogEntry.objects.log_actions` directamente.

### 4.2 y 4.3 Acción del panel

Prueba primero: 7 en rojo (`No se seleccionó ninguna acción.`, campos editables, sin columna) y luego en verde.

```text
$ uv run pytest src/backend/cuentas/tests/test_admin.py
10 passed
```

El historial del panel (`/admin/cuentas/usuario/<id>/history/`) muestra "Cuenta desbloqueada."; el `LogEntry` es de cambio, con el autor y la fecha. `intentos_fallidos` y `bloqueado_hasta` son de solo lectura y `bloqueado_hasta` está en la lista.

## Suite completa al cerrar el grupo 4

```text
$ uv run ruff check .
All checks passed!
$ uv run ruff format --check .
137 files already formatted
$ uv run pytest --cov
TOTAL                                 901     30    97%
Required test coverage of 80.0% reached. Total coverage: 96.67%
358 passed
```

## 5. Plantillas e interfaz (D5 a D9)

### 5.7 Tarjeta disponible (verificación temporal)

- Asistencia con `disponible=True` y una ruta existente (`docente:portada`) solo durante la prueba, con `monkeypatch` sobre `cuentas.dimensiones.DIMENSIONES`, sin tocar el código: nada que revertir.
- Capturas con Playwright (Chromium, fuera del repo) a 360 y 1280, en claro y oscuro: la tarjeta se dibuja como en `portada-sprint1.html` (fondo `--color-dimension`, verbo "Registrar asistencia" con flecha, sin insignia) y el carrusel abre en Asistencia.
- La misma comprobación queda automatizada en `test_pantallas.py` (`test_una_dimension_disponible_enlaza_a_su_pantalla`).
- En esas capturas, portada y dirección a 320, 360 y 1280 en ambos temas: `scrollWidth` igual a `clientWidth` del documento. La prueba definitiva es la 6.3.


## 6. Pruebas de punta a punta, accesibilidad y Slow 4G (D10, D11)

### 6.1 a 6.3 Pruebas de punta a punta

- `axe-core ^4.14.0` en `devDependencies`; `npm ci` sin errores y `node_modules/axe-core/axe.min.js` presente. Un primer `npm ci` falló con `EPERM` porque un `npm run dev` (Tailwind en modo `--watch`) tenía abierto `lightningcss`; al cerrarlo, pasó.
- `test_ingresar_e2e.py` (5) y `test_portada_e2e.py` (20): en rojo sin `app.css` compilado y en verde con él (`pytest -m e2e`: 25 pasadas). Las 18 pruebas de desborde horizontal pasaron desde la primera corrida (el CSS ya cumplía); su rojo no se demostró.
- La prueba de "Ingresando…" detiene la navegación con un `preventDefault` registrado después del de `ingresar.js`, porque un POST retenido hace que Playwright espere la navegación sin terminar. Comprueba el estado en pantalla, no el envío al servidor.

### 6.4 Accesibilidad (axe-core)

- `test_accesibilidad_e2e.py`: 5 vistas × claro y oscuro × 360 y 1280 = 20 pruebas, con `wcag2a`, `wcag2aa`, `wcag21a` y `wcag21aa`.
- En rojo: con la etiqueta del campo quitada de `componentes/campo.html` (revertido con una copia, `git status` limpio), las 20 fallaron. Las del inicio de sesión dejaron su informe en `test-results/accesibilidad-<vista>-<tema>-<ancho>.json`; las de la portada y la dirección fallaron antes, porque no se podía iniciar sesión sin la etiqueta.
- En verde con la plantilla restaurada: 20 pasadas, sin infracciones `critical` ni `serious`.
- `test-results/` se agregó a `.gitignore`.

### 6.5 Slow 4G (RNF-002)

- `test_rendimiento_e2e.py`, Chromium, sin caché, `/ingresar/` (servidor de pruebas sin compresión): **48,7 KB** en 4 respuestas y usable en **1,52 s** (umbrales: 2 MB y 5 s). El prototipo dio 50 KB.
- Pasó en la primera corrida: el umbral no se vio fallar.


## 7. Revisión local completa

Partida: rama `feature/US-001-iniciar-sesion`, último commit `e0b24db` (6.4 a 6.6), `git status` limpio. El único `node.exe` abierto era el de otra herramienta, no un `npm run dev`; el CSS se recompiló con `npm run build` sin errores.

### 7.1 Ruff, pytest y Playwright

- `ruff check .`: sin hallazgos. `ruff format --check .`: 131 archivos con el formato correcto.
- `pytest --cov`: **452 pasadas**, 46 `e2e` excluidas; cobertura total **96,88 %** (mínimo 80 %).
- `pytest -m e2e --browser chromium` (con `DJANGO_ALLOW_ASYNC_UNSAFE=true` y el CSS compilado): **46 pasadas**.
- `git status` quedó limpio después de las tres corridas.

### 7.2 Firefox a 360 px

Prueba manual de Marco en Firefox a 360 px (chips, punto, aviso "Próximamente" e historial sin cambios): todo bien. Safari de iPhone queda como pendiente.

### 7.3 Revisión del diff

- `verificar.py`: **PASA** (noreply, sin atribuciones, `git status` limpio, sin archivos prohibidos, Ruff, pytest ≥ 80 %).
- Hex en plantillas (`git grep` sobre los `.html` versionados): 0 coincidencias.
- `style=` en plantillas: 0 coincidencias.
- Claves (`secret`, `password`, `api_key`, `token` asignados a un literal): 2 coincidencias, ambas en `scripts/tests/test_hooks.py` y falsas: son pruebas del hook que arman un valor ficticio con un f-string.
- `insumos/`, `PRODUCT.md`, `PENDIENTES_TESIS.md` y `.env` en `git ls-files`: ninguno.
- Datos reales (DoD 8): solo hay datos ficticios en pruebas y plantillas; los correos de los commits son noreply de GitHub.
- La revisión completa del diff contra `main` la hace Codex al final; no se lanzó agente ni revisor.

### Nota de plan (2026-10-23)

La crítica del tramo 8 pasó a Codex en solo lectura (prompt A, lo corre el usuario) en lugar de dos subagentes de Claude Code, y la tarea 9.2 se redujo a un solo commit (9.1), porque ya se hace un commit por grupo.

## 8. Crítica del tramo 8 (8.1 y 8.2; la crítica 8.3 la hace Codex)

### 8.1 Capturas de la aplicación local

- Aplicación local con `runserver`, base `tramo8` aparte de la de pruebas, CSS compilado y tres usuarios ficticios (docente, dirección y administrador; clave generada, fuera del repositorio). El administrador entra al panel de Django, que no es una de las 5 vistas.
- 20 capturas (5 vistas × claro y oscuro × 360 y 1280) en `insumos/prototipo/US-001/tramo8/capturas/`; láminas y porcentaje de píxeles distintos frente a `capturas/final/` en `tramo8/capturas/comparacion/`.
- Inicio de sesión: normal y con campos vacíos, 0 % distinto en los dos temas y anchos. Con error: 0,15 % a 360 y 1,41 % a 1280 (el usuario escrito, `ana.quispe` en vez de `aquispe`).
- Portada (36 a 46 % distinto) y dirección a 360 (11 %): el contenido es el de US-001, no el del prototipo. Sin "Prof." ni grado y sección (no hay dónde guardarlos, D8); las tres tarjetas en "Próximamente" y sin enlaces (ninguna disponible); la tarjeta ya no tiene fondo propio ni sombra en la ficha, ahora es blanca con borde; en el celular aparecen los chips de dimensión y los puntos del carrusel; dirección dice "Hola, Rosa Huamán" y no "Hola, Lic. Rosa Huamán", y el estado vacío tiene su recuadro. Las capturas no muestran nada que contradiga DESIGN.md. La altura de la página cambia en la portada (834 a 800 a 360; 800 a 809 a 1280).

### 8.2 Detector

- `impeccable detect --json` con `.impeccable/config.json`. JSON en `tramo8/detector/detector.json`.
- URL pública `/ingresar/` en claro con `--viewport` (360 y 1280): 0 hallazgos. Las vistas con sesión y los estados de error solo se alcanzan por `--cdp`, que se usó en las 20 combinaciones (el tema oscuro, con `color_scheme=dark` verificado).
- **Total con `--cdp`: 18 hallazgos principales, 0 avisos.**
  - `cream-palette` (`body`, `#f3eee3`): 10, uno por vista en claro. Es `--color-fondo` de DESIGN.md 0.3 (R-30, aceptada en el tramo 5). En oscuro, 0.
  - `nested-cards` (`.ficha`): 8 en la portada (3 a 1280 y 1 a 360, en claro y en oscuro). Es la "miniatura que desborda" de DESIGN.md (R-10). La exención de `.impeccable/config.json` solo cubre `final/portada-*.html`, así que no alcanza a la plantilla de Django. D15 suponía que la ficha no aparecía en US-001; sí aparece.
- Sin hallazgos en inicio de sesión (normal, con error y vacío) ni en dirección en oscuro.
- No se cambió la configuración ni el código: queda para decisión de Marco si se amplía la exención.

### 8.3 Crítica de Codex

- Informe en `insumos/prototipo/US-001/tramo8/critique/codex.md.md`. Puntaje: **29/40** (Bueno), −1 frente al recálculo de 30/40: la heurística 1 (visibilidad del estado) baja de 4 a 3.
- Hallazgos de gravedad 2 o mayor: **2 en total** (1 nuevo, C8-01; 1 heredado, R-29). Gravedad 3: 0. Gravedad 4: 0.
- Las 18 entradas del detector no se suman: corresponden a R-10 (`nested-cards`) y R-30 (`cream-palette`), ya aceptadas.

### 8.4 Corrección de C8-01

- Prueba primero: una de marcado (`test_pantallas.py`) y cinco de navegador (`test_ingresar_e2e.py`: Enter desde Contraseña, botón, campo vacío sin anuncio y restablecer con `pageshow` persistido, y la guarda cuando falta la región, escrita tras la revisión). Las cinco primeras fallaban porque la región no existía.
- Corrección: `<p class="sr-only" role="status" data-estado-ingreso>` vacía, después del formulario, y `marcarEnvio()` de `ingresar.js` la escribe y la vacía. Envío nativo y bloqueo del doble envío sin cambios; `DESIGN.md` sin tocar.
- Estado de cada punto en `insumos/prototipo/US-001/tramo8/revision.md` (local: `insumos/` está fuera del repositorio).
- Suite completa: 453 pasan (cobertura 96,88 %); `pytest -m e2e --browser chromium`: 51 pasan.

## 9. Evidencia por escenario y DoD (9.1, D15)

Fecha: 23/10/2026. Partida: rama `feature/US-001-iniciar-sesion` en `4052ab8`, sin push ni PR. Estado de las pruebas: `pytest --cov` **453 pasadas** (cobertura 96,81 % en `verificar.py --antes-del-commit`, mínimo 80 %) y `pytest -m e2e --browser chromium` **51 pasadas**. Las pruebas están en `src/backend/cuentas/tests/`; en las tablas, `ingresar` es `test_ingresar.py`, `pantallas` es `test_pantallas.py` y e2e es `test_ingresar_e2e.py`, salvo que se nombre otro archivo.

Estados: **Verificado** (prueba automática o inspección que cubre el escenario); **Verificado, sin prueba automática** (solo marcado, CSS o capturas; se dice cuál); **Pendiente del PR** (solo el canal de GitHub puede darlo).

### 9.1 Escenarios de `inicio-sesion` (23)

| Escenario | Evidencia | Estado |
| --- | --- | --- |
| Camino ideal del docente | `ingresar::test_cada_rol_llega_a_su_pantalla`; e2e `test_de_la_raiz_al_inicio_de_sesion_y_a_la_portada` | Verificado |
| Ingreso de la dirección | `ingresar::test_cada_rol_llega_a_su_pantalla`; e2e `test_la_direccion_llega_a_su_inicio` | Verificado |
| Ingreso del administrador | `ingresar::test_cada_rol_llega_a_su_pantalla` (rol ADMINISTRADOR a `/admin/`) | Verificado |
| Campos vacíos | `ingresar::test_campos_vacios_muestran_su_mensaje_sin_contar_un_intento`; `pantallas::test_campos_vacios_marcan_cada_campo_y_lo_enlazan_a_su_mensaje` | Verificado |
| Contraseña incorrecta | `ingresar::test_los_cuatro_rechazos_dan_el_mismo_mensaje_en_dos_lineas`, `test_conserva_el_usuario_pero_no_la_contrasena`; `pantallas::test_el_error_conserva_el_usuario_y_no_la_contrasena` | Verificado |
| Cuenta desactivada | `ingresar::test_los_cuatro_rechazos_dan_el_mismo_mensaje_en_dos_lineas`; `test_backend::test_cuenta_inactiva_devuelve_none` | Verificado |
| Usuario inexistente | `ingresar::test_la_pagina_no_distingue_un_rechazo_de_otro`; `test_backend::test_usuario_inexistente_devuelve_none_y_calcula_el_hash` | Verificado |
| Quinto intento fallido | `test_servicios_bloqueo::test_quinto_fallo_bloquea_15_minutos_y_reinicia_el_conteo`, `test_cuatro_fallos_no_bloquean` | Verificado |
| Contraseña correcta durante el bloqueo | `ingresar::test_cuenta_bloqueada_rechaza_la_contrasena_correcta_con_el_mismo_mensaje`; `test_backend::test_cuenta_bloqueada_con_la_clave_correcta_devuelve_none` | Verificado |
| Intentos durante el bloqueo | `test_servicios_bloqueo::test_durante_el_bloqueo_nada_entra_ni_cuenta` | Verificado |
| Fin del bloqueo | `test_servicios_bloqueo::test_a_los_14_59_sigue_bloqueada_y_a_los_15_00_entra` | Verificado |
| Primer fallo después del bloqueo | `test_servicios_bloqueo::test_primer_fallo_despues_del_bloqueo_no_vuelve_a_bloquear` | Verificado |
| Fallos con un ingreso correcto en medio | `test_servicios_bloqueo::test_un_ingreso_correcto_entre_fallos_reinicia_el_conteo` | Verificado |
| Desbloqueo de una cuenta bloqueada | `test_admin::test_desbloquea_la_cuenta_y_lo_registra_en_su_historial`, `test_el_historial_del_panel_muestra_el_desbloqueo`, `test_despues_de_desbloquear_ingresar_acepta_la_contrasena`; historial confirmado en 4.1 | Verificado |
| Cuenta que no estaba bloqueada | `test_admin::test_una_cuenta_sin_bloqueo_no_cambia_ni_se_registra` | Verificado |
| Ingreso al panel sin sesión | `ingresar::test_panel_sin_sesion_termina_en_ingresar_y_vuelve_al_panel`, `test_login_del_panel_sin_sesion_lleva_a_ingresar_con_next` | Verificado |
| Raíz sin sesión | `ingresar::test_raiz_sin_sesion_lleva_a_ingresar` | Verificado |
| Raíz con sesión | `ingresar::test_raiz_con_sesion_lleva_a_su_pantalla` | Verificado |
| Ingresar con la sesión ya iniciada | `ingresar::test_ingresar_con_la_sesion_iniciada_lleva_a_su_pantalla` | Verificado |
| Pantalla de rol sin sesión | `test_acceso::test_sin_sesion_lleva_a_ingresar_con_next`, `test_cada_pantalla_sin_sesion_lleva_a_ingresar`; `ingresar::test_next_seguro_lleva_a_la_pagina_pedida` (vuelve a `/docente/`) | Verificado |
| Docente en la pantalla de la dirección | `test_acceso::test_cada_pantalla_lleva_a_otro_rol_a_la_suya`, `test_con_otro_rol_lleva_a_su_pantalla_sin_mostrar_la_vista` | Verificado |
| Dirección en la pantalla del docente | Las mismas de la fila anterior (parametrizadas por rol) | Verificado |
| Usuario sin acceso al panel | `ingresar::test_docente_en_el_panel_termina_en_su_portada_sin_ciclo`, `test_administrador_sin_is_staff_recibe_403_sin_ciclo` | Verificado |

### 9.2 Escenarios de `pantallas-de-inicio` (21)

| Escenario | Evidencia | Estado |
| --- | --- | --- |
| Contenido de la pantalla | `pantallas::test_los_textos_aparecen_en_el_orden_del_spec`, `test_sin_escudo_ni_menu_ni_enlaces`, `test_el_nombre_de_la_ie_es_el_unico_h1` | Verificado |
| Mensaje de error sobre el formulario | `pantallas::test_el_error_va_sobre_la_tarjeta_con_role_alert_y_dos_lineas` (`role="alert"`, ícono, dos líneas, sobre el formulario) | Verificado |
| Ver la contraseña | e2e `test_mostrar_contrasena_alterna_la_vista`; `pantallas::test_el_boton_mostrar_contrasena_nace_oculto_y_sin_presionar` | Verificado |
| Sin JavaScript (contraseña) | e2e `test_sin_javascript_no_hay_boton_y_el_formulario_se_envia` | Verificado |
| Envío en curso | e2e `test_envio_en_curso_cambia_el_boton_y_deja_los_campos_de_solo_lectura`; anuncio en la región `status` (C8-01): `pantallas::test_el_anuncio_del_envio_es_una_region_status_vacia_oculta_y_fuera_del_formulario` y 5 pruebas e2e (Enter, botón, campo vacío, restablecer y sin la región) | Verificado |
| Portada al entrar | `pantallas::test_la_portada_saluda_con_el_nombre_completo`, `test_tres_tarjetas_en_orden_con_subtitulo_e_insignia`, `test_la_portada_no_inventa_grado_ni_tratamiento` | Verificado |
| Tres dimensiones en "Próximamente" | `pantallas::test_las_tarjetas_proximamente_son_botones_sin_enlace`; `test_dimensiones::test_al_cerrar_us_001_ninguna_esta_disponible` | Verificado |
| Toque en una tarjeta "Próximamente" | `test_portada_e2e::test_tarjeta_proximamente_avisa_sin_mover_la_miniatura` (texto, misma dirección, miniatura quieta); `pantallas::test_cada_tarjeta_proximamente_tiene_su_region_aria_live_vacia` | Verificado |
| Dimensión activada por su historia | `pantallas::test_una_dimension_disponible_enlaza_a_su_pantalla` (con `monkeypatch`; ver 5.7) | Verificado |
| Bandera activa sin pantalla | `test_dimensiones::test_toda_dimension_disponible_resuelve_su_pantalla`, `test_la_revision_detecta_una_bandera_activa_sin_pantalla` | Verificado |
| Chip de una tarjeta | `test_portada_e2e::test_chip_notas_muestra_la_tarjeta_sin_tocar_el_historial` | Verificado |
| Carrusel sin JavaScript | `pantallas::test_chips_accesos_y_carrusel_tus_accesos` (marcado) y `test_portada_e2e::test_sin_javascript_los_chips_llevan_a_las_tres_tarjetas`: con JavaScript apagado, cada chip cambia la dirección a `#c-…` y deja la tarjeta en la ventana (10.2) | Verificado |
| Tarjeta inicial | `test_dimensiones::test_sin_ninguna_disponible_abre_en_la_primera`, `test_abre_en_la_primera_disponible_en_el_orden_de_las_tarjetas`; `pantallas::test_sin_ninguna_disponible_la_tarjeta_inicial_es_sesiones` | Verificado |
| Computadora | `test_portada_e2e::test_a_1280_las_tres_tarjetas_van_en_una_fila_sin_chips_ni_puntos`: a 1280 las tres tarjetas comparten la misma altura de inicio, van de izquierda a derecha sin cruzarse y caben en la ventana; los chips y los puntos están ocultos (10.2). Además, capturas de 1280 de 8.1 | Verificado |
| Inicio de la dirección en el Sprint 1 | `pantallas::test_la_direccion_saluda_y_muestra_el_estado_vacio`, `test_la_direccion_no_muestra_tablas_ni_tarjetas_ni_scripts` | Verificado |
| Barra y pie | `pantallas::test_barra_con_el_nombre_de_la_ie_y_sin_menu`, `test_pie_al_final_y_titulo_de_la_pagina` | Verificado |
| Preferencia oscura | `test_portada_e2e::test_los_tokens_aplicados_toman_su_valor_del_tema` (claro y oscuro): el valor calculado de `body` (fondo y texto) y del `h1` (color primario) en oscuro es el del Quick Start de DESIGN.md, leído del propio archivo en la prueba; en claro, los tres valores están fijos en la prueba (10.2); además axe y desborde corren con la preferencia oscura, y capturas de 8.1 | Verificado; el aspecto lo siguen juzgando las capturas y la crítica |
| Plantillas sin colores escritos | `test_plantillas::test_plantilla_sin_colores_ni_estilos_en_linea`; `git grep` de hex y `style=` en 7.3: 0 coincidencias | Verificado |
| Revisión de cada pantalla (axe) | `test_accesibilidad_e2e::test_sin_infracciones_graves_de_accesibilidad`: 5 vistas × 2 temas × 2 anchos = 20, sin `critical` ni `serious` (6.4); corridas de nuevo con C8-01 dentro de los 51 e2e de entonces (55 en 10.2) | Verificado |
| Pantallas a 320 px | `test_portada_e2e::test_el_documento_no_se_desplaza_en_horizontal`: 3 pantallas × 3 anchos × 2 temas = 18 (rojo demostrado después, 10.2) | Verificado |
| Primera visita con Slow 4G | `test_rendimiento_e2e::test_inicio_de_sesion_con_slow_4g`: 48,7 KB y 1,52 s (6.5) | Verificado; el rojo de los dos umbrales se demostró después (10.2). Cifras de 10.2.3: 49,1 KB y 1,53 s, la misma medición con una variación normal |

### 9.3 Escenarios de los deltas `entorno-desarrollo` e `integracion-continua` (5)

| Escenario | Evidencia | Estado |
| --- | --- | --- |
| Visita a la página inicial (`entorno-desarrollo`) | `ingresar::test_raiz_sin_sesion_lleva_a_ingresar`; e2e `test_de_la_raiz_al_inicio_de_sesion_y_a_la_portada` (la raíz lleva a `/ingresar/`, en español, con el nombre y las tres dimensiones en orden) | Verificado |
| Recursos de interfaz cargados (`entorno-desarrollo`) | e2e `test_de_la_raiz_…` (`app.css` con 200; `typeof Alpine` indefinido en `/ingresar/` y objeto en `/docente/`); `pantallas::test_carga_ingresar_js_pero_no_alpine_ni_htmx`, `test_la_portada_carga_portada_js_antes_de_alpine` | Verificado |
| Página inicial en el navegador (`integracion-continua`) | La misma e2e `test_de_la_raiz_…` | Verificado en local; **pendiente del PR** en el trabajo `Playwright` |
| Accesibilidad y carga en el canal (`integracion-continua`) | Las 20 pruebas de axe y la de Slow 4G corren dentro de `pytest -m e2e` (README, "Pruebas de punta a punta") | Verificado en local; **pendiente del PR** en el canal |
| Prueba de punta a punta fallida (`integracion-continua`) | Sin cambio respecto de EN-08, cuyo PR #53 lo demostró. US-001 no toca el canal | No aplica a este cambio; se comprueba al abrir el PR |

Total: 23 + 21 + 5 = 49 escenarios, ninguno sin evidencia. Ninguno queda sin prueba automática en local (Carrusel sin JavaScript y Computadora la tienen desde 10.2). Dos del canal dependen del PR.

### 9.4 DoD 1 a 9 (D15)

| N.° | Estado | Evidencia |
| --- | --- | --- |
| 1 | Cumple en local; **pendiente del PR** | 96,81 % en `verificar.py` (mínimo 80 %). La puerta Sonar way (cobertura del código nuevo ≥ 80 % y duplicación ≤ 3 %) solo se ve en el PR. `ingresar.js` y `portada.js` quedan fuera de la cobertura por D12 |
| 2 | Cumple en local; **pendiente del PR** | Ruff sin hallazgos (7.1 y `verificar.py`). CodeQL y SonarQube Cloud solo corren en el PR |
| 3 | **Pendiente (equipo)** | Aprobación de otra integrante en el PR; también ratifica DESIGN.md 0.3.1 |
| 4 | No aplica | Vista previa de Vercel hasta EN-02 |
| 5 | Cumple en local; **pendiente del PR** | Los escenarios de 9.1 a 9.3 pasan, ya sin escenarios "sin prueba automática" (10.2); ruta ideal de punta a punta: `test_de_la_raiz_al_inicio_de_sesion_y_a_la_portada`; 55 e2e en verde. Los comandos del README, ejecutados tal cual, dan el resultado esperado (10.2). El resultado del canal se ve en el PR |
| 6 | Cumple | RN-024 con pruebas propias en la capa de servicios: `test_servicios_bloqueo.py` (13 pruebas), `test_backend.py` (9) y las del panel en `test_admin.py` (D10, secciones 2 y 4) |
| 7 | Cumple | Informe de axe: 20 combinaciones (5 vistas × claro y oscuro × 360 y 1280) sin `critical` ni `serious` (6.4), vuelto a correr tras C8-01 y con el comando del README en 10.2 (20 pasadas) |
| 8 | Cumple | Revisión del diff (7.3): solo datos ficticios ("Ana Quispe", "Rosa Huamán") y contraseñas generadas por cada prueba; ninguna coincidencia de `insumos/`, `PRODUCT.md`, `PENDIENTES_TESIS.md` ni `.env` en `git ls-files`; ningún dato de la I.E. inventado |
| 9 | Cumple | Este cambio en OpenSpec, docstrings de los módulos y de las pruebas, catálogo de rutas 1.1.0 (3.6), README (pruebas e2e, accesibilidad, Slow 4G y fila `Playwright`) y documento 06 en V_1_5_0 (con 02/01 en V_1_4_0 y 07 en V_1_2_0, ya en la rama) |

### 9.5 Crítica del tramo 8 y deuda

- **C8-01** (gravedad 2, nuevo): aplicada en `4052ab8`, con su prueba primero (8.4).
- **R-29 / T-07** (gravedad 2, heredado): **queda para el equipo.** La ayuda remite a "el administrador" sin una referencia verificable; depende de T-07 (dato de la I.E. pendiente). No se aplicó y no se inventó ningún contacto.
- **Minor 2 a 5 de la revisión de cierre del grupo 8:** van a la descripción del PR, no se corrigen ahora. (2) La consulta de la región de estado en `ingresar.js` está dentro del bucle por formulario pero con alcance de `document`. (3) `test_con_un_campo_vacio_no_se_anuncia_nada` podría comprobar también que el botón sigue en "Ingresar" y que no hay `aria-busy`. (4) `spec.md` de `pantallas-de-inicio` y `design.md` D6 no mencionan la región de estado: una línea en `design.md` al archivar. (5) La prueba de marcado supone un `<p>` y un solo `</form>`. El Minor 1 (guarda contra `null`) se corrigió antes del commit.
- **Minor 7 y 8 de la revisión final de Codex:** van a la descripción del PR, no se corrigen ahora. (7) `scripts/verificar.py` (línea 257): el nombre del registro de fallo solo distingue hasta segundos, y dos ejecuciones que fallen en el mismo segundo escriben la misma ruta; corregir con PID y microsegundos o un nombre exclusivo. (8) `test_portada_e2e.py`, `test_tarjeta_proximamente_avisa_sin_mover_la_miniatura`: la variable `miniatura` mide `.franjas` y la ficha es `.ficha`; la prueba puede pasar aunque la ficha se desplace.
- **Detalles menores de Codex** (títulos de página distintos, orientación ante intentos repetidos, pista bajo Usuario, espacio vacío de las miniaturas, `scrollWidth` no medido por Codex): deuda, a la descripción del PR.
- **Detector:** las 18 entradas son R-10 y R-30, ya aceptadas. La exención de `.impeccable/config.json` no cubre `/docente/`: deuda Minor, sin cambiar la configuración.
- **Limitación conocida de D13:** dos `pytest --cov` comunes a la vez en la misma máquina pueden chocar en `.coverage`; no pasa en CI. La tarea 1.3 sigue sin marcar.

### 9.6 Pendientes de documentación del design

Ninguno se editó en US-001. Siguen **pendientes** de que el equipo los apruebe y se propongan aparte, con subida de versión (`scripts/subir_version.py`):

- **Documento 06 (RF-001) y documento 02/01 (US-001), escenario "Flujo alternativo válido":** dicen "panel de consolidados"; US-001 lleva a la dirección a su inicio con un estado vacío hasta US-040 (D8).
- **Documento 10 o README:** HTMX no se carga en las pantallas que no lo usan (D6).
- **Tratamiento en el saludo ("Prof.", "Lic."):** hoy no hay dónde guardarlo (D8); si el equipo lo quiere, es un campo nuevo en otra historia.
- **T-07 / R-29:** la forma de ubicar al administrador y la orientación ante intentos repetidos son decisión del equipo (`docs/PENDIENTES_TESIS.md`, fuera del repositorio).
- **Fuera del alcance de US-001, para después:** página propia de CSRF y de sesión vencida (US-002); Safari de iPhone y WebKit en un equipo real (EN-07); límite por IP si el piloto lo muestra (EN-04); ampliar la exención del detector a `/docente/`.

## 10. Hallazgos 5 y 6 de la revisión final de Codex (10.2)

Fecha: 23/10/2026. Partida: rama `feature/US-001-iniciar-sesion` en `a42269a`, `git status` limpio. Cada demostración en rojo rompió la condición en el archivo indicado, corrió la prueba, revirtió (copia exacta) y confirmó con `git status` que solo quedaba la prueba nueva.

### 10.2.1 Pruebas nuevas (hallazgo 5), en `test_portada_e2e.py`

| Escenario | Prueba | Rojo demostrado | Verde |
| --- | --- | --- | --- |
| Carrusel sin JavaScript | `test_sin_javascript_los_chips_llevan_a_las_tres_tarjetas`: contexto con JavaScript apagado, 360 px; cada chip cambia la dirección a `#c-sesiones`, `#c-notas`, `#c-asistencia` y deja esa tarjeta en la ventana | Con el `href` de los chips en `"#"` (`portada_docente.html`): `Page URL expected to be '…/docente/#c-sesiones'`, actual `…/docente/#` | pasa |
| Computadora | `test_a_1280_las_tres_tarjetas_van_en_una_fila_sin_chips_ni_puntos`: misma altura de inicio, orden de izquierda a derecha sin cruzarse, las tres caben en 1280 px; chips y puntos ocultos | Con el bloque de computadora de `app.css` en `min-width: 99960px` y el CSS recompilado: la tercera tarjeta queda en `x = 2496` (`AssertionError` de «caben en 1280»). Una primera versión sin esa comprobación cayó solo en «chips ocultos», porque en el carrusel las tarjetas también van en fila; por eso se agregó | pasa |
| Preferencia oscura | `test_los_tokens_aplicados_toman_su_valor_del_tema[light/dark]`: valor **calculado** de `body` (fondo y color de texto) y de `h1` (color); en oscuro, el valor sale del bloque oscuro de DESIGN.md leído en la prueba; en claro, los valores están escritos en la prueba | Con `--color-fondo` oscuro en `#000000` en `app.css`: `('dark', '--color-fondo', 'rgb(0, 0, 0)', 'rgb(39, 34, 28)')`; la variante clara pasó | pasan las dos |

Los rojos de CSS se hicieron con `npm run build` antes y después; al final, `app.css` y el CSS compilado volvieron al original. `test_portada_e2e.py`: 24 pasadas (20 + 4).

### 10.2.2 Script de comparación de tokens (5.2, hallazgo 6)

El script de 5.2 no quedó en el repositorio. Se **reconstruyó** fuera de él (en el directorio temporal de la sesión) y se corrió ahora: compara línea por línea el `@theme`, el bloque oscuro y el `:root` de 960 px de `app.css` con los del Quick Start de DESIGN.md.

- Resultado: `@theme` 36 líneas, oscuro 21, 960 px 1; **0 diferencias** (salida 0).
- Prueba del script: con `--color-error` cambiado a `#c10008` en `app.css` da 2 diferencias y sale con 1. Se revirtió.
- Excepción: esta es una verificación nueva, no la salida de 5.2 de aquel día. La salida original no se registró y no se reconstruye.

### 10.2.3 Comandos del README, tal como están escritos (6.6, hallazgo 6)

Con `db` levantado, en Git Bash:

- `uv run playwright install chromium`: salida 0.
- `cd src/frontend && npm ci` y `npm run build`: `npm ci` salida 0 (con avisos de `install-scripts` de npm, sin error); el build, "Done in 68 ms".
- `DJANGO_ALLOW_ASYNC_UNSAFE=true uv run pytest -m e2e --browser chromium`: **55 pasadas**, 462 deseleccionadas (51 de antes + 4 nuevas).
- Solo accesibilidad (`…/test_accesibilidad_e2e.py`): **20 pasadas**.
- Solo rendimiento (`…/test_rendimiento_e2e.py -s`): **49,1 KB** en 4 respuestas, usable en **1,53 s**. En PowerShell, con `$env:DJANGO_ALLOW_ASYNC_UNSAFE = "true"` y el mismo comando sin prefijo: 49,1 KB y 1,53 s, 1 pasada.

El resultado coincide con 6.2 a 6.5 (6.2 y 6.3 dentro del total de 55).

### 10.2.4 Rojos que no se habían registrado (demostrados después)

| Tarea | Condición rota | Resultado en rojo |
| --- | --- | --- |
| 5.1 | Plantilla temporal `cuentas/temporal_rojo.html` con `class="text-[#5b2610]"` | `test_plantillas.py`: `assert ['#5b2610'] == []`, 1 falla y 28 pasan; borrada la plantilla, 28 pasan |
| 6.3 (desborde) | `@layer base { body { min-width: 500px; } }` al final de `app.css`, con el CSS recompilado | 12 de las 18 pruebas fallan (las de 320 y 360 en las tres pantallas, claro y oscuro); las 6 de 1280 pasan. Revertido y recompilado: 18 pasan |
| 6.5 (Slow 4G, bytes) | `relleno.css` de 3 MB (en `static/dist/`, ignorado por git) enlazado desde `base.html` | 3121,4 KB en 18,29 s: `AssertionError: 3196312 bytes` |
| 6.5 (Slow 4G, tiempo) | El mismo relleno, de 1,3 MB (bajo el tope de 2 MB) | 1318,9 KB en 8,54 s: `AssertionError: 8.54 s` |

Revertidos el relleno y `base.html`, la prueba vuelve a 49,1 KB y 1,53 s. Con esto no queda ninguna demostración de rojo sin hacer, salvo la excepción de 10.2.2.

### 10.2.5 Estado

- `ruff check .` y `ruff format --check .`: sin hallazgos (131 archivos con el formato correcto).
- `pytest --cov`: **462 pasadas**, 55 `e2e` excluidas; cobertura **96,93 %**.
- `pytest -m e2e --browser chromium`: **55 pasadas**.

### 10.2.6 Minor de la revisión de cierre del grupo 10.2 (a la descripción del PR, no se corrigen ahora)

- La prueba de tokens escribe a mano los valores del tema claro; solo el oscuro sale de DESIGN.md. En oscuro, `--color-fondo` y `--color-fondo-trabajo` valen lo mismo (`#27221c`), así que la prueba no distingue cuál de los dos usa `body`.
- `test_sin_javascript_los_chips_llevan_a_las_tres_tarjetas`: para la primera tarjeta, `to_be_in_viewport` ya se cumple al abrir; decide la dirección. La comprobación `not_to_have_attribute("data-carrusel-js", re.compile(".*"))` es correcta (el atributo se pone vacío) pero cuesta leer.
- `DESIGN_MD = Path(__file__).resolve().parents[4] / "DESIGN.md"` depende de la ubicación del archivo.
- De la prueba de 1280, solo la condición «caben en 1280 px» tiene rojo propio demostrado; las de misma altura y orden no.
- El revisor no corrió `pytest --cov`; el 96,93 % es el de la corrida de 10.2.5.
