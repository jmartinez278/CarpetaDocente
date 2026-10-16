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
