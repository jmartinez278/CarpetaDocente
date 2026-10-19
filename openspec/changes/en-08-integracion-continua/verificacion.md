# Verificación de EN-08

Rama: `feature/EN-08-integracion-continua` · Laptop Windows 11 con Docker Desktop.

## 2.1 Cobertura antes del umbral

Fecha: 16/10/2026. Medida con `db` levantado (`docker compose up -d db`) y sin umbral en `pyproject.toml`. El total, **87 %**, supera el 80 % que exige la DoD 1, así que el umbral se activa sin cambios en las pruebas. Lo que falta cubrir es lo mismo que en EN-01: los puntos de entrada `manage.py`, `asgi.py` y `wsgi.py`, y el `__str__` de `Institucion`.

```text
$ uv run pytest --cov
collected 37 items

src\backend\config\tests\test_base_datos.py .                            [  2%]
src\backend\cuentas\tests\test_admin.py ...                              [ 10%]
src\backend\cuentas\tests\test_modelos.py ............                   [ 43%]
src\backend\institucion\tests\test_admin.py .                            [ 45%]
src\backend\institucion\tests\test_modelos.py ......                     [ 62%]
src\backend\config\tests\test_settings.py .......                        [ 81%]
src\backend\cuentas\tests\test_inicio.py .......                         [100%]

Name                                Stmts   Miss  Cover   Missing
-----------------------------------------------------------------
src\backend\actividad\apps.py           4      0   100%
src\backend\asistencia\apps.py          4      0   100%
src\backend\catalogo\apps.py            4      0   100%
src\backend\config\asgi.py              4      4     0%   10-16
src\backend\config\settings.py         26      0   100%
src\backend\config\urls.py              4      0   100%
src\backend\config\wsgi.py              4      4     0%   10-16
src\backend\cuentas\admin.py           19      0   100%
src\backend\cuentas\apps.py             4      0   100%
src\backend\cuentas\models.py          25      0   100%
src\backend\cuentas\views.py            3      0   100%
src\backend\direccion\apps.py           4      0   100%
src\backend\exportaciones\apps.py       4      0   100%
src\backend\institucion\admin.py        6      0   100%
src\backend\institucion\apps.py         4      0   100%
src\backend\institucion\models.py      17      1    94%   43
src\backend\manage.py                  11     11     0%   4-23
src\backend\notas\apps.py               4      0   100%
src\backend\repositorio\apps.py         4      0   100%
-----------------------------------------------------------------
TOTAL                                 155     20    87%

32 empty files skipped.
============================= 37 passed in 7.50s ==============================
```

## 2.2 Umbral de 80 % y rutas relativas

Fecha: 16/10/2026. `pyproject.toml`: `relative_files = true` en `[tool.coverage.run]` y `fail_under = 80` en `[tool.coverage.report]`.

### Rojo

La tarea pedía ver el rojo con `uv run pytest --cov -k test_pagina_inicial_responde`. No sirve con el código actual: esa sola prueba ya da 85 %, porque pytest-django arranca Django y eso importa modelos, admin y apps, que son casi todo el código de EN-01. En su lugar, el umbral se puso de forma temporal en 90 para comprobar que pytest-cov lo lee de `pyproject.toml` y hace fallar el comando aunque las pruebas pasen. Luego se dejó en 80. El rojo con 80 % real se demuestra en la rama `demo/EN-08-rojo` (tarea 6.4).

```text
$ uv run pytest --cov -k test_pagina_inicial_responde     # sin umbral todavía
TOTAL                                 155     24    85%
====================== 1 passed, 36 deselected in 0.49s =======================

$ uv run pytest --cov                                      # fail_under = 90 (temporal)
TOTAL                                 155     20    87%
FAIL Required test coverage of 90.0% not reached. Total coverage: 87.10%
============================= 37 passed in 5.68s ==============================
exit=1
```

### Verde

```text
$ uv run pytest --cov --cov-report=xml                     # fail_under = 80
Coverage XML written to file coverage.xml
Required test coverage of 80.0% reached. Total coverage: 87.10%
============================= 37 passed in 4.99s ==============================
exit=0
```

Rutas en `coverage.xml`: la carpeta fuente queda relativa (`<source>src/backend</source>`) y cada archivo, relativo a ella (`filename="cuentas/models.py"`), sin la ruta absoluta de la laptop. Es el formato que muestra la documentación de SonarQube Cloud para Python (`source` + `relative_files = True`, consultada en Context7). SonarQube Cloud lo resuelve como `src/backend/cuentas/models.py` desde la raíz del repositorio; se confirma en el PR de EN-08 con la cobertura distinta de 0 % (tarea 6.2).

```text
<source>src/backend</source>
filename="manage.py"
filename="actividad/apps.py"
filename="asistencia/apps.py"
filename="catalogo/apps.py"
filename="config/asgi.py"
```

## 3. Playwright y pruebas de punta a punta

Fecha: 16/10/2026.

### 3.1 Consulta y dependencia

Consultado en Context7:
- pytest-django: `live_server` sirve los estáticos cuando `django.contrib.staticfiles` está instalado, y usa `transactional_db`.
- Django 5.2 (*Async safety*): `DJANGO_ALLOW_ASYNC_UNSAFE` desactiva el chequeo `SynchronousOnlyOperation`; no se usa en producción.
- pytest-playwright: opciones `--browser`, `--tracing retain-on-failure` y `--output` (por defecto `test-results/`).

```text
$ uv add --dev pytest-playwright
 + playwright==1.64.0
 + pytest-playwright==0.10.0
 (y greenlet, pyee, python-slugify, text-unidecode, typing-extensions)
$ uv sync --locked
Resolved 25 packages in 1ms
Checked 24 packages in 1ms
```

### 3.2 Marcador `e2e` fuera del `pytest` por defecto

Sin navegadores de Playwright instalados (no existía `%LOCALAPPDATA%\ms-playwright`):

```text
$ uv run pytest --cov
Required test coverage of 80.0% reached. Total coverage: 87.10%
============================= 37 passed in 5.41s ==============================
```

### 3.3 Rojo

`src/backend/static/dist/` vacío (su contenido se movió fuera del repositorio y luego se regeneró con `npm run build`). Sin la variable, todas las pruebas dan error al crear la base de prueba, como anticipaba D10:

```text
$ uv run pytest -m e2e --browser chromium
E   django.core.exceptions.SynchronousOnlyOperation: You cannot call this from an async context - use a thread or sync_to_async.
====================== 37 deselected, 4 errors in 11.36s ======================
```

Con `DJANGO_ALLOW_ASYNC_UNSAFE=true`, fallan por lo que debe faltar: la hoja de estilos y los scripts. El nombre y las dimensiones pasan, porque el HTML no depende de `dist/`.

```text
$ DJANGO_ALLOW_ASYNC_UNSAFE=true uv run pytest -m e2e --browser chromium
E       AssertionError: assert 404 == 200      (app.css)
E       AssertionError: assert 'undefined' != 'undefined'      (typeof htmx)
E       AssertionError: assert 'undefined' != 'undefined'      (typeof Alpine)
FAILED src/backend/cuentas/tests/test_inicio_e2e.py::test_la_hoja_de_estilos_carga[chromium]
FAILED src/backend/cuentas/tests/test_inicio_e2e.py::test_htmx_y_alpine_estan_disponibles[chromium-htmx]
FAILED src/backend/cuentas/tests/test_inicio_e2e.py::test_htmx_y_alpine_estan_disponibles[chromium-Alpine]
================= 3 failed, 1 passed, 37 deselected in 3.13s ==================
```

### 3.4 Verde

El único ajuste es la variable de entorno en el comando; `settings.py` no cambia.

```text
$ cd src/frontend && npm ci && npm run build
copiado alpine.min.js
≈ tailwindcss v4.3.3
Done in 72ms
$ DJANGO_ALLOW_ASYNC_UNSAFE=true uv run pytest -m e2e --browser chromium
plugins: cov-7.1.0, django-4.14.0, playwright-0.10.0
collected 41 items / 37 deselected / 4 selected
src\backend\cuentas\tests\test_inicio_e2e.py ....                        [100%]
====================== 4 passed, 37 deselected in 3.05s =======================
$ uv run ruff check . && uv run ruff format --check .
All checks passed!
105 files already formatted
$ uv run pytest --cov
====================== 37 passed, 4 deselected in 6.37s =======================
```

### 3.5 Comandos del README

Ejecutados tal cual desde la sección "Pruebas de punta a punta (Playwright)":

```text
# Git Bash
$ uv run playwright install chromium     → exit 0
$ cd src/frontend; npm ci; npm run build → Done
$ DJANGO_ALLOW_ASYNC_UNSAFE=true uv run pytest -m e2e --browser chromium
====================== 4 passed, 37 deselected in 3.02s =======================

# PowerShell
PS> $env:DJANGO_ALLOW_ASYNC_UNSAFE = "true"; uv run pytest -m e2e --browser chromium
====================== 4 passed, 37 deselected in 2.88s =======================
```

## 4.1 Versiones y SHA de las acciones

Consultado el 16/10/2026 con `git ls-remote` (tags del repositorio de cada acción). Los seis son tags ligeros (sin entrada `^{}`), así que el SHA del tag es el del commit. Las entradas usadas se comprobaron en el `action.yml` de cada SHA; todas corren en `node24`.

| Acción | Versión | SHA completo |
|---|---|---|
| `actions/checkout` | v7.0.1 | `3d3c42e5aac5ba805825da76410c181273ba90b1` |
| `actions/setup-node` | v7.1.0 | `949feb2413d6458794dcd2491c4babbbce0c15c1` |
| `actions/upload-artifact` | v7.0.2 | `cf430e030ddbb5b0abf93d22962f4752f3646cd9` |
| `actions/download-artifact` | v8.0.2 | `9000827ccba6bdab643e8b6fd33ac0654aef8333` |
| `astral-sh/setup-uv` | v10.3.0 | `1c37ad07a6a961277cf70c0d37d6f313000f5884` |
| `SonarSource/sonarqube-scan-action` | v8.3.0 | `d209202bc7d53ff1cc128f7f907dac145c9d6ae9` |

Notas de la consulta:
- `sonarqube-scan-action`: la documentación de SonarQube Cloud todavía muestra la v7. La v8 solo cambia un valor por defecto (`skipSignatureVerification` pasa a `false`: el escáner descargado se verifica por firma) y no cambia el uso de `SONAR_TOKEN` ni de `sonar-project.properties`.
- `download-artifact` v8: un hash que no coincide ahora hace fallar el paso (`digest-mismatch: error`); al descargar por nombre, los archivos siguen quedando directo en `path`.
- zizmor 1.31.1 exige, desde la v1.20, SHA también en `actions/*` (antes aceptaba versión). Por eso las seis acciones van fijadas por SHA, no solo las dos de terceros.

## 4.2 a 4.4 Workflow y `sonar-project.properties`

Fecha: 16/10/2026. El usuario aprobó `.github/workflows/ci.yml` después de revisar el borrador completo; la copia en el repositorio es idéntica al borrador aprobado (`cmp` sin diferencias). Ajustes respecto del design: ver las notas de "Ajustes en la implementación" en D2, D9 y D11 de `design.md`.

Reglas pedidas por el usuario y dónde se cumplen en `ci.yml`:
- Disparadores: solo `pull_request` hacia `main` y `push` a `main`; no hay `pull_request_target`.
- Permisos: `permissions: {}` en el workflow y `contents: read` en cada uno de los cuatro trabajos.
- Acciones: las seis por SHA completo verificado con `git ls-remote` (tabla de 4.1).
- Token: solo `${{ secrets.SONAR_TOKEN }}`, en el `env:` del paso del análisis.
- Sin `continue-on-error`.
- `DJANGO_ALLOW_ASYNC_UNSAFE`: solo en el `env:` del paso "Pruebas de punta a punta".
- `sonar-project.properties` sin `sonar.qualitygate.wait` (D9).

### actionlint y zizmor sobre `.github/workflows/`

```text
$ uvx --from actionlint-py --with shellcheck-py actionlint -verbose
verbose: Collected 1 YAML files
verbose: Found 0 parse errors in 0 ms for .github\workflows\ci.yml
verbose: Rule "pyflakes" was disabled: exec: "pyflakes": executable file not found in %PATH%
verbose: Found total 0 errors in 65 ms for .github\workflows\ci.yml
exit=0

$ uvx zizmor .github/workflows/
 INFO zizmor: 🌈 zizmor v1.31.1
 WARN audit: zizmor: zizmor is running in offline mode by default; some audits and auto-fixes will not be available.
 INFO audit: zizmor: 🌈 completed .github\workflows\ci.yml
No findings to report. Good job! (3 suppressed)
exit=0
```

actionlint 1.7.12 corre con shellcheck (de `shellcheck-py`), que revisa los scripts de `run:`; la regla `pyflakes` queda deshabilitada porque no hay Python en línea. zizmor corre sin conexión (sin `gh` ni token de GitHub), así que no ejecuta las auditorías en línea; los SHA de las acciones se verificaron aparte con `git ls-remote`.

Los 3 hallazgos suprimidos solo aparecen con `--persona=auditor` y no se corrigen en EN-08 (D11):

```text
$ uvx zizmor --persona=auditor .github/workflows/
error[unpinned-images]: unpinned image references          --> .github\workflows\ci.yml:57:9
error[unpinned-images]: unpinned image references          --> .github\workflows\ci.yml:104:9
warning[secrets-outside-env]: secrets referenced without a dedicated environment --> .github\workflows\ci.yml:183:28
3 findings: 0 informational, 0 low, 1 medium, 2 high
```

### Búsqueda de tokens (4.4)

`ci.yml` y `sonar-project.properties` aún no estaban en el índice, por eso se usó `--untracked` (los archivos ignorados, como `.env`, quedan fuera).

```text
$ git grep --untracked -n -i "sonar_token\|token"
.env.example:6:            secrets.token_urlsafe(50)   ← cómo generar la clave de Django
.github/workflows/ci.yml:8:      comentario: "El único secreto es SONAR_TOKEN…"
.github/workflows/ci.yml:82:     secrets.token_urlsafe(50)   ← clave de Django generada en el trabajo
.github/workflows/ci.yml:139:    secrets.token_urlsafe(50)   ← ídem, trabajo Playwright
.github/workflows/ci.yml:183:    SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}   ← única referencia al token
README.md:69:                    secrets.token_urlsafe(50)   ← cómo generar la clave de Django
sonar-project.properties:2:      comentario: "el token vive en los secretos de GitHub"
docs/…, openspec/…:              textos de documentación (design, proposal, spec, tasks, verificación)
```

Resultado: la única referencia al token es `${{ secrets.SONAR_TOKEN }}`; el resto es documentación o la función `secrets.token_urlsafe`, que no contiene ningún valor.

Control adicional de patrones de claves reales (tokens de SonarQube `sqp_`/`sqa_`/`squ_`, de GitHub, de AWS, llaves privadas y `django-insecure`):

```text
$ git grep --untracked -n -E "sq[pau]_[0-9a-f]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|BEGIN [A-Z ]*PRIVATE KEY|django-insecure"
openspec/changes/en-01-proyecto-django-base/verificacion.md:122:- Patrones de claves (`django-insecure`, …): ninguno.
```

Única coincidencia: el texto de EN-01 que describe esta misma búsqueda. No hay claves.

## 4.5 Sección "Integración continua" del README

Fecha: 16/10/2026. La sección incluye la tabla de verificaciones con cómo reproducir cada una en la laptop, la puesta en marcha (pasos 1.1 a 1.3), la guía del *ruleset* de `main` (paso B10) separando lo que exige EN-08 de lo que agrega el equipo, el aviso de no renombrar los trabajos y que el token vive solo en los secretos de GitHub. `SonarQube Cloud`, `SonarCloud Code Analysis` y CodeQL no se reproducen en la laptop; la tabla lo dice.

Cada comando local de la tabla, ejecutado tal cual (con `db` levantado):

```text
$ uv run ruff check .
All checks passed!
$ uv run ruff format --check .
105 files already formatted
$ uv run pytest --cov
Required test coverage of 80.0% reached. Total coverage: 87.10%
====================== 37 passed, 4 deselected in 3.94s =======================
$ uv run pytest --cov --cov-report=xml
Coverage XML written to file coverage.xml
Required test coverage of 80.0% reached. Total coverage: 87.10%
====================== 37 passed, 4 deselected in 3.91s =======================
$ uv run playwright install chromium        → exit 0
$ cd src/frontend && npm ci && npm run build → Done
$ DJANGO_ALLOW_ASYNC_UNSAFE=true uv run pytest -m e2e --browser chromium
====================== 4 passed, 37 deselected in 2.51s =======================
```

## 4.6 Revisión local completa antes del commit

Fecha: 16/10/2026. Con `db` levantado (`docker compose up -d db`), el CSS compilado y Chromium instalado. Las pruebas `e2e` se corren con `DJANGO_ALLOW_ASYNC_UNSAFE=true`, como indica el README (sin la variable fallan con `SynchronousOnlyOperation`, ver 3.3).

```text
$ uv run ruff check .
All checks passed!
exit=0

$ uv run ruff format --check .
105 files already formatted
exit=0

$ uv run pytest --cov
============================= test session starts =============================
platform win32 -- Python 3.13.16, pytest-9.1.1, pluggy-1.7.0
django: version: 5.2.18, settings: config.settings (from ini)
rootdir: C:\Proyectos\CarpetaDocente
configfile: pyproject.toml
testpaths: src/backend
plugins: cov-7.1.0, django-4.14.0, playwright-0.10.0
collected 41 items / 4 deselected / 37 selected

src\backend\config\tests\test_base_datos.py .                            [  2%]
src\backend\cuentas\tests\test_admin.py ...                              [ 10%]
src\backend\cuentas\tests\test_modelos.py ............                   [ 43%]
src\backend\institucion\tests\test_admin.py .                            [ 45%]
src\backend\institucion\tests\test_modelos.py ......                     [ 62%]
src\backend\config\tests\test_settings.py .......                        [ 81%]
src\backend\cuentas\tests\test_inicio.py .......                         [100%]

=============================== tests coverage ================================
______________ coverage: platform win32, python 3.13.16-final-0 _______________

Name                                Stmts   Miss  Cover   Missing
-----------------------------------------------------------------
src\backend\actividad\apps.py           4      0   100%
src\backend\asistencia\apps.py          4      0   100%
src\backend\catalogo\apps.py            4      0   100%
src\backend\config\asgi.py              4      4     0%   10-16
src\backend\config\settings.py         26      0   100%
src\backend\config\urls.py              4      0   100%
src\backend\config\wsgi.py              4      4     0%   10-16
src\backend\cuentas\admin.py           19      0   100%
src\backend\cuentas\apps.py             4      0   100%
src\backend\cuentas\models.py          25      0   100%
src\backend\cuentas\views.py            3      0   100%
src\backend\direccion\apps.py           4      0   100%
src\backend\exportaciones\apps.py       4      0   100%
src\backend\institucion\admin.py        6      0   100%
src\backend\institucion\apps.py         4      0   100%
src\backend\institucion\models.py      17      1    94%   43
src\backend\manage.py                  11     11     0%   4-23
src\backend\notas\apps.py               4      0   100%
src\backend\repositorio\apps.py         4      0   100%
-----------------------------------------------------------------
TOTAL                                 155     20    87%

32 empty files skipped.
Required test coverage of 80.0% reached. Total coverage: 87.10%
====================== 37 passed, 4 deselected in 4.04s =======================
exit=0

$ DJANGO_ALLOW_ASYNC_UNSAFE=true uv run pytest -m e2e --browser chromium
============================= test session starts =============================
platform win32 -- Python 3.13.16, pytest-9.1.1, pluggy-1.7.0
django: version: 5.2.18, settings: config.settings (from ini)
rootdir: C:\Proyectos\CarpetaDocente
configfile: pyproject.toml
testpaths: src/backend
plugins: cov-7.1.0, django-4.14.0, playwright-0.10.0
collected 41 items / 37 deselected / 4 selected

src\backend\cuentas\tests\test_inicio_e2e.py ....                        [100%]

====================== 4 passed, 37 deselected in 2.64s =======================
exit=0
```

### Revisión del diff (DoD 8 y claves)

Se revisaron las 371 líneas agregadas respecto de `HEAD` en `README.md`, `design.md`, `tasks.md`, `verificacion.md`, `.github/workflows/ci.yml` y `sonar-project.properties`.

- **DoD 8, sin datos reales:** no hay correos, números de 8 o 9 dígitos (DNI o teléfonos), nombres de estudiantes ni datos de la I.E. El workflow no carga datos: la base del canal solo tiene lo que crean las pruebas. La única referencia a una persona es `jmartinez278`, el usuario dueño del repositorio público, que también es la organización pública de SonarQube Cloud (`sonar.organization` y `sonar.projectKey`).
- **Claves:** la única referencia al token en archivos que se ejecutan es `.github/workflows/ci.yml:183` (`SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}`). Las demás menciones de `secrets.SONAR_TOKEN` están en la documentación (README, design, verificación). `secrets.token_urlsafe` es la función que genera la clave de Django en cada trabajo. No aparecen patrones de claves reales (`sqp_`/`sqa_`/`squ_`, tokens de GitHub, claves de AWS, llaves privadas ni `django-insecure`). Las únicas coincidencias son los textos de esta verificación que describen esa búsqueda. No hay contraseñas: el PostgreSQL del canal usa `POSTGRES_HOST_AUTH_METHOD: trust`.
- **Archivos fuera del repositorio:** `coverage.xml` y `src/backend/static/dist/` están ignorados y no entran en el diff; `.env` no aparece.

## 6. Puesta en marcha y evidencia de los escenarios

Datos aportados por el equipo el 17/10/2026. Las capturas de la demostración están en el documento de pruebas del equipo `merge_fallido.docx` (17/10/2026); no se copian imágenes al repositorio.

### 6.1 Integración de `main`

`main` se integró en la rama con `git merge main` (merge `4518e0b`), sin rebase ni force push.

**Repetición de 4.6:** fecha 17/10/2026, en `chore/archivar-en-08` (`214b4f0`). Con `db` levantado (`docker compose up -d db`) y Chromium ya instalado. El código es el mismo que tenía la rama después del merge: `git diff 4518e0b de0c5b0` no muestra diferencias, y de `de0c5b0` a `214b4f0` solo cambian `README.md` y el documento 11. Las cuatro revisiones pasan.

```text
$ uv run ruff check .
All checks passed!
exit=0

$ uv run ruff format --check .
107 files already formatted
exit=0

$ uv run pytest --cov
============================= test session starts =============================
platform win32 -- Python 3.13.16, pytest-9.1.1, pluggy-1.7.0
django: version: 5.2.18, settings: config.settings (from ini)
rootdir: C:\Proyectos\CarpetaDocente
configfile: pyproject.toml
testpaths: src/backend
plugins: cov-7.1.0, django-4.14.0, playwright-0.10.0
collected 41 items / 4 deselected / 37 selected

src\backend\config\tests\test_base_datos.py .                            [  2%]
src\backend\cuentas\tests\test_admin.py ...                              [ 10%]
src\backend\cuentas\tests\test_modelos.py ............                   [ 43%]
src\backend\institucion\tests\test_admin.py .                            [ 45%]
src\backend\institucion\tests\test_modelos.py ......                     [ 62%]
src\backend\config\tests\test_settings.py .......                        [ 81%]
src\backend\cuentas\tests\test_inicio.py .......                         [100%]

=============================== tests coverage ================================
______________ coverage: platform win32, python 3.13.16-final-0 _______________

Name                                Stmts   Miss  Cover   Missing
-----------------------------------------------------------------
src\backend\actividad\apps.py           4      0   100%
src\backend\asistencia\apps.py          4      0   100%
src\backend\catalogo\apps.py            4      0   100%
src\backend\config\asgi.py              4      4     0%   10-16
src\backend\config\settings.py         26      0   100%
src\backend\config\urls.py              4      0   100%
src\backend\config\wsgi.py              4      4     0%   10-16
src\backend\cuentas\admin.py           19      0   100%
src\backend\cuentas\apps.py             4      0   100%
src\backend\cuentas\models.py          25      0   100%
src\backend\cuentas\views.py            3      0   100%
src\backend\direccion\apps.py           4      0   100%
src\backend\exportaciones\apps.py       4      0   100%
src\backend\institucion\admin.py        6      0   100%
src\backend\institucion\apps.py         4      0   100%
src\backend\institucion\models.py      17      1    94%   43
src\backend\manage.py                  11     11     0%   4-23
src\backend\notas\apps.py               4      0   100%
src\backend\repositorio\apps.py         4      0   100%
-----------------------------------------------------------------
TOTAL                                 155     20    87%

32 empty files skipped.
Required test coverage of 80.0% reached. Total coverage: 87.10%
====================== 37 passed, 4 deselected in 4.44s =======================
exit=0

$ cd src/frontend && npm run build

> build
> npm run copiar-vendor && tailwindcss -i ./css/app.css -o ../backend/static/dist/app.css --minify


> copiar-vendor
> node scripts/copiar-vendor.mjs

copiado htmx.min.js
copiado alpine.min.js
≈ tailwindcss v4.3.3

Done in 95ms
exit=0

$ DJANGO_ALLOW_ASYNC_UNSAFE=true uv run pytest -m e2e --browser chromium
============================= test session starts =============================
platform win32 -- Python 3.13.16, pytest-9.1.1, pluggy-1.7.0
django: version: 5.2.18, settings: config.settings (from ini)
rootdir: C:\Proyectos\CarpetaDocente
configfile: pyproject.toml
testpaths: src/backend
plugins: cov-7.1.0, django-4.14.0, playwright-0.10.0
collected 41 items / 37 deselected / 4 selected

src\backend\cuentas\tests\test_inicio_e2e.py ....                        [100%]

====================== 4 passed, 37 deselected in 4.41s =======================
exit=0
```

### 6.2 PR de EN-08

- PR #52, fusionado en `main` (merge `de0c5b0`), con las 8 verificaciones en verde.
- Análisis de SonarQube Cloud en `main` sobre `de0c5b0`: cobertura de 83,3 %.

Verificaciones del PR #52, todas en verde:

| Origen | Verificación |
|---|---|
| CodeQL | `CodeQL / Analyze (javascript-typescript)` |
| CodeQL | `CodeQL / Analyze (python)` |
| CodeQL | `CodeQL` |
| CI | `CI / Playwright` |
| CI | `CI / Pruebas y cobertura` |
| CI | `CI / Ruff` |
| SonarQube Cloud | `SonarCloud Code Analysis` |
| CI | `CI / SonarQube Cloud` |

### 6.3 *Ruleset* de `main`

*Ruleset* "proteger-main" activo: 1 aprobación, fusión por *merge commit*, verificaciones requeridas y *code scanning*. La fusión bloqueada se confirmó en el PR #53 (6.5).

La captura del *ruleset* consta en el documento de pruebas del equipo; no se copia al repositorio.

### 6.4 Rama `demo/EN-08-rojo`

La salida local de `uv run pytest --cov` con la prueba fallando no se guardó. Consta el PR #53 (6.5).

### 6.5 PR de demostración #53

PR #53, cerrado sin fusionar; la rama se borró.

| Estado | Verificaciones |
|---|---|
| En rojo (3) | `Code scanning results / CodeQL`, `CI / Pruebas y cobertura` y `CI / Ruff` |
| Omitida | `CI / SonarQube Cloud` (*skipped*) |
| Pendiente | `SonarCloud Code Analysis` (*Expected*, sin estado reportado) |
| En verde | `CI / Playwright`, `CodeQL / Analyze (python)` y `CodeQL / Analyze (javascript-typescript)` |

- **CodeQL:** 1 alerta nueva de seguridad, regla "SQL query built from user-controlled sources", severidad *High*, en `src/backend/cuentas/demo_vista_sql.py`, línea 15. Bloqueó la fusión.
- **SonarQube Cloud:** omitido, porque el trabajo se salta cuando falla `Pruebas y cobertura`. No hay resultado de la puerta de calidad.
- **Fusión bloqueada:** falta 1 aprobación y CodeQL detectó 1 alerta.

## 6.6 Escenarios de EN-08 (D14)

| Escenario | Evidencia | Estado |
|---|---|---|
| Pull Request que cumple | PR #52 con las 8 verificaciones en verde; SonarQube Cloud en `main` sobre `de0c5b0` con 83,3 % de cobertura | Verificado |
| Prueba fallida o cobertura insuficiente | Lista de verificaciones del PR #53, con `CI / Pruebas y cobertura` en rojo, y la fusión bloqueada | Verificado; la captura del registro del trabajo no consta |
| Alerta crítica de seguridad | PR #53: alerta de CodeQL "SQL query built from user-controlled sources", severidad *High*, en `src/backend/cuentas/demo_vista_sql.py:15`, que bloqueó la fusión | Verificado |
| Puerta de calidad no superada | PR #53: `CI / SonarQube Cloud` omitido y `SonarCloud Code Analysis` sin estado; no hay resultado de la puerta | **Sin demostrar:** el trabajo de SonarQube Cloud se salta cuando falla `Pruebas y cobertura` (D9) |
| Canal sin claves reales | Revisión de `ci.yml` y búsqueda de claves (4.4 y 4.6); ejecución del PR #52 (16/10/2026) y del push a `main` sobre `de0c5b0` | Verificado |

## 6.6 DoD 1 a 9 (D15)

| N.° | Estado | Evidencia |
|---|---|---|
| 1 | Cumple | Umbral de 80 % en el canal; 87,10 % en local (4.6); PR #52 en verde; 83,3 % en SonarQube Cloud sobre `de0c5b0` |
| 2 | Cumple | Ruff, CodeQL y SonarQube Cloud entre las 8 verificaciones en verde del PR #52 |
| 3 | Cumple | El PR #52 tiene una aprobación (*APPROVED*) de otra integrante del equipo |
| 4 | No aplica | Vista previa de Vercel hasta EN-02. El cuerpo del PR #52 no menciona Vercel |
| 5 | Cumple | Prueba de punta a punta de la página inicial (`Playwright`) en verde en el PR #52; 4 pasan en local (4.6) |
| 6 | No aplica | EN-08 no implementa reglas de negocio del documento 09 ni agrega código de servicios (decisión del equipo, 18/10/2026) |
| 7 | No aplica | No hay pantallas nuevas |
| 8 | Cumple | Revisión del diff de EN-08 sin datos reales (4.6) |
| 9 | Cumple | README ("Integración continua"), este cambio en OpenSpec y docstrings en `test_inicio_e2e.py`; el catálogo de rutas no cambia |

## 6.6 Pendientes de documentación del design

Ninguno se editó en EN-08. Siguen **pendientes** de que el equipo los apruebe y se propongan aparte, con subida de versión:

- Documento 07, RNF-018, frente al documento 02/01, DoD 2 ("0 hallazgos críticos" frente a "sin vulnerabilidades críticas ni altas").
- Documento 02/01, DoD 1 y 2 y escenario 4 de EN-08, frente a la puerta Sonar way.
- Documento 02/01, sección 7: registrar que CodeQL usa la configuración por defecto, sin workflow en el repositorio.
