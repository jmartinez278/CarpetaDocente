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
