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

