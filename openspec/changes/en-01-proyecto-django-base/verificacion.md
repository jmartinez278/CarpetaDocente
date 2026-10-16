# Verificación de EN-01 (tareas 8.1 a 8.4)

Fecha: 15/10/2026 · Rama: `feature/EN-01-proyecto-django` · Laptop Windows 11 con Docker Desktop.

## 8.1 Arranque desde cero, pruebas y Ruff

### Arranque desde cero

La imagen de `web` y las imágenes base (`postgres:17`, `node:24-slim`) ya estaban descargadas. En un clon nuevo hay que sumar la construcción de la imagen de `web` (unos 21 s medidos) y la descarga de las imágenes base.

```text
$ docker compose down -v
 Container carpetadocente-frontend-1 Removed 
 Container carpetadocente-web-1 Removed 
 Container carpetadocente-db-1 Removed 
 Volume carpetadocente_datos_postgres Removing 
 Volume carpetadocente_node_modules_frontend Removing 
 Volume carpetadocente_node_modules_frontend Removed 
 Volume carpetadocente_datos_postgres Removed 
 Network carpetadocente_default Removed 
$ rm -rf src/backend/static/dist
$ docker compose up -d
 Container carpetadocente-db-1 Started 
 Container carpetadocente-frontend-1 Started 
 Container carpetadocente-db-1 Healthy 
 Container carpetadocente-web-1 Started 
GET / -> 200 ; GET /static/dist/app.css -> 200 ; tiempo desde 'up': 12 s
$ docker compose logs web (migraciones)
  Applying institucion.0001_initial... OK
  Applying cuentas.0001_initial... OK
Starting development server at http://0.0.0.0:8000/
```

### Pruebas con cobertura

Cobertura medida sobre el código propio de `src/backend`, sin contar migraciones ni pruebas (`[tool.coverage.run]` en `pyproject.toml`). Lo que falta cubrir son los puntos de entrada `manage.py`, `asgi.py` y `wsgi.py`, y el `__str__` de `Institucion`.

```text
$ uv run pytest --cov
============================= test session starts =============================
platform win32 -- Python 3.13.16, pytest-9.1.1, pluggy-1.7.0
django: version: 5.2.18, settings: config.settings (from ini)
rootdir: C:\Proyectos\CarpetaDocente
configfile: pyproject.toml
testpaths: src/backend
plugins: cov-7.1.0, django-4.14.0
collected 37 items

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
============================= 37 passed in 6.11s ==============================
```

### Ruff

```text
$ uv run ruff check .
All checks passed!
$ uv run ruff format --check .
98 files already formatted
```

## 8.2 Versión de Python

`.python-version`, `requires-python` y el `Dockerfile` fijan 3.13.

```text
$ uv run python --version
Python 3.13.16
$ docker compose run --rm web python --version
Python 3.13.16
```

## 8.3 DoD, criterio 9 (documentación)

- [x] README: sección "Configuración local" (opciones A y B, variables, pruebas y problemas frecuentes) y estado del proyecto.
- [x] Docstrings en los módulos, modelos, gestor, formularios, vistas y configuración propios.
- [x] Catálogo de rutas: `docs/03 Implementación/Catálogo de rutas.md` (`/` y `/admin/`), coincide con `config/urls.py`.
- [x] Especificación del cambio en OpenSpec: `openspec validate en-01-proyecto-django-base --strict` es válido.
- [x] Documento 11 actualizado a V_1_1_0 (sección 8: diferencias con el DDL).

## 8.4 DoD, criterio 8 y revisión antes de cerrar

Revisados los 97 archivos que entran al PR (commits de la rama más los cambios pendientes):

- Rutas prohibidas (`.env`, `insumos/`, `node_modules/`, `static/dist/`, bases sqlite, cachés): ninguna.
- Valores de la clave secreta, la contraseña de PostgreSQL o `DATABASE_URL` locales: ninguno.
- Patrones de claves (`django-insecure`, llaves privadas, tokens de npm, GitHub o AWS): ninguno.
- Correos: ninguno, salvo el noreply de GitHub en los commits.
- Datos de prueba: solo ficticios ("I.E. Ficticia N.° 1", `docente_ficticio`, `admin_ficticio`, `Clave-Ficticia-2026`, URL de base ficticia). No hay datos de estudiantes.
- Archivos de terceros: solo los archivos de bloqueo generados (`uv.lock`, `package-lock.json`); HTMX y Alpine se copian a `static/dist/`, que no se versiona.

## Estado de la DoD global para EN-01

| N.° | Criterio | Estado |
|---|---|---|
| 1 | Cobertura ≥ 80 % | Cumple en local: 87 %. La puerta automática llega con EN-08 |
| 2 | Análisis estático sin críticas ni altas | Ruff limpio, con las reglas `S` de seguridad. CodeQL y SonarQube Cloud llegan con EN-08 |
| 3 | Revisión por otra integrante | Pendiente: en el PR |
| 4 | Despliegue automático en ambiente de pruebas | Pendiente: depende de EN-02 |
| 5 | Escenarios Gherkin y Playwright | Escenarios de las specs cubiertos por pytest y por el arranque desde cero. Playwright llega con EN-08 |
| 6 | Reglas de negocio con pruebas propias | No aplica: EN-01 no implementa reglas del documento 09 |
| 7 | Accesibilidad de pantallas nuevas | Pendiente: la página inicial es provisional; la revisión automática llega con EN-07 |
| 8 | Sin datos reales | Cumple (8.4) |
| 9 | Documentación actualizada | Cumple (8.3) |
