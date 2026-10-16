# Tasks

Ejecución con pruebas primero (TDD): en cada tarea con comportamiento, la prueba se escribe y se ve fallar antes del código. Antes de usar una API de Django, django-environ, pytest-django, Tailwind, HTMX o Alpine.js, consultar Context7. Todo módulo, modelo y vista nuevo lleva docstring en español (DoD 9).

## 1. Dependencias y esqueleto

- [ ] 1.1 Crear `.python-version` (3.13) y `pyproject.toml` con uv (`requires-python = ">=3.13,<3.14"`): Django 5.2.x, django-environ, psycopg[binary]; dev: pytest, pytest-django, pytest-cov, ruff. Verificar: `uv sync` termina y `uv run python --version` muestra 3.13.x
- [ ] 1.2 Crear el proyecto `config` en `src/backend/` y las 9 apps (`cuentas`, `institucion`, `catalogo`, `repositorio`, `notas`, `asistencia`, `direccion`, `exportaciones`, `actividad`), todas en `INSTALLED_APPS`. Verificar: los 9 directorios existen con su `apps.py`
- [ ] 1.3 Configurar Ruff (D10) y pytest-django (`DJANGO_SETTINGS_MODULE`, `pythonpath`, `testpaths`) en `pyproject.toml`; agregar `src/backend/static/dist/` a `.gitignore`. Verificar: `uv run ruff check .` y `uv run ruff format --check .` limpios

## 2. Configuración desde el entorno

- [ ] 2.1 Actualizar `.env.example`: agregar `POSTGRES_PORT`, comentarios de uso local (formato de `DATABASE_URL` sin contraseña real) y conservar las variables de R2 vacías para EN-03. Verificar: ninguna variable tiene valor de clave
- [ ] 2.2 Prueba primero: `DEBUG` es `False` si `DJANGO_DEBUG` no está definida, y la falta de `DJANGO_SECRET_KEY` o `DATABASE_URL` produce `ImproperlyConfigured` con el nombre de la variable. Verificar: la prueba falla antes de 2.3
- [ ] 2.3 Reescribir `config/settings.py` con django-environ (D6): `.env` de la raíz, `DATABASES` desde `DATABASE_URL`, `es-pe`, `America/Lima`, `BigAutoField`, `templates/` y `static/` de `src/backend/`, `STATIC_ROOT`, docstring del módulo. Sin claves en el código. Verificar: pruebas de 2.2 en verde y ninguna clave literal en `settings.py`

## 3. PostgreSQL con Docker Compose

- [ ] 3.1 Crear `docker-compose.yml` con el servicio `db` (D8: `postgres:17` con comentario "provisional, igualar a Neon en EN-02", variables `POSTGRES_*`, volumen con nombre, `healthcheck`, puerto `${POSTGRES_PORT:-5432}`). Verificar: `docker compose up -d db` y `docker compose ps` muestra `db` como `healthy`
- [ ] 3.2 Prueba primero: la conexión `default` es a PostgreSQL (`connection.vendor == "postgresql"`). Verificar: `uv run pytest` en verde con `db` levantado

## 4. Modelos `Institucion` y `Usuario`

- [ ] 4.1 Pruebas primero de `Institucion` según `specs/cuentas-usuarios` (solo nombre válido, código modular repetido rechazado, organización de periodos fuera de BIMESTRE/TRIMESTRE rechazada), con datos ficticios. Verificar: fallan antes de 4.2
- [ ] 4.2 Implementar `institucion.Institucion` (D7, `db_table = "institucion"`, restricciones con nombre, docstrings) y registrarla en el panel. Verificar: pruebas de 4.1 en verde
- [ ] 4.3 Pruebas primero de `Usuario` (rol no permitido, DOCENTE sin institución rechazado, ADMINISTRADOR sin institución aceptado, institución con usuarios no se elimina, contraseña con hash, valores iniciales de los campos de control), con datos ficticios. Verificar: fallan antes de 4.4
- [ ] 4.4 Implementar `cuentas.Usuario` (D7, `AUTH_USER_MODEL`, `db_table = "usuario"`, `ck_usuario_institucion` y check de rol, docstrings) y registrarlo en el panel; generar las migraciones iniciales. Verificar: pruebas de 4.3 en verde y `uv run python src/backend/manage.py makemigrations --check --dry-run` sin cambios pendientes
- [ ] 4.5 Aplicar migraciones sobre la base vacía. Verificar: `uv run python src/backend/manage.py migrate` sin errores y `\dt` en `psql` lista `usuario` e `institucion`

## 5. Frontend y página inicial

- [ ] 5.1 Crear `src/frontend/` (D9): `package.json` con tailwindcss y @tailwindcss/cli v4, htmx.org 2.0.x y alpinejs 3.x; `css/app.css` con `@source` hacia las plantillas; `scripts/copiar-vendor.mjs`; scripts `build` y `dev`. Verificar: `npm ci && npm run build` genera `src/backend/static/dist/app.css`, `dist/vendor/htmx.min.js` y `dist/vendor/alpine.min.js`
- [ ] 5.2 Pruebas primero de la página inicial: `/` responde 200, muestra el nombre del sistema y las tres dimensiones en orden, y enlaza `dist/app.css`, `htmx.min.js` y `alpine.min.js`. Verificar: fallan antes de 5.3
- [ ] 5.3 Implementar `templates/base.html` (`lang="es"`, viewport para celular, estáticos de 5.1; sin aplicar todavía la identidad visual), `templates/inicio.html`, la vista `inicio` en `cuentas` con docstring y la ruta `/`. Verificar: pruebas de 5.2 en verde y la página se ve con estilos en `runserver`

## 6. Aplicación web y compilación del CSS en Docker Compose

- [ ] 6.1 Crear `Dockerfile` con `python:3.13-slim` (la misma versión que `.python-version`) + uv, `uv sync --frozen`, entorno fuera de la carpeta montada, y `.dockerignore`. Verificar: `docker compose build web` termina sin errores
- [ ] 6.2 Agregar el servicio `web` a `docker-compose.yml` (D8: `DATABASE_URL` armado con `POSTGRES_*` y host `db`, depende de `db` sano, `migrate` y luego `runserver 0.0.0.0:8000`, montaje de `src/backend/`). Verificar: con la base vacía, `docker compose up` aplica migraciones y `http://localhost:8000/` responde
- [ ] 6.3 Agregar el servicio `frontend` (D9b: `node:24-slim`, monta `src/frontend/` y `src/backend/`, `node_modules` en volumen con nombre, `npm ci` y `npm run dev`). Verificar: tras `docker compose up` en un clon sin `static/dist/`, el archivo `app.css` aparece y `http://localhost:8000/` se ve con estilos sin haber instalado Node en la laptop

## 7. Documentación (DoD 9)

- [ ] 7.1 README, sección "Configuración local": requisitos (Docker Desktop; uv y Node 24 solo para la opción B), copiar `.env`, opción A `docker compose up` (el servicio `frontend` compila el CSS), opción B `db` en Docker + `uv run ... runserver` + `npm run dev` en otra terminal, nota "si la página sale sin estilos, falta compilar el CSS", `pytest` y Ruff, cambio de `POSTGRES_PORT`. Verificar: seguir los pasos desde un clon limpio levanta el proyecto con estilos en ambas opciones
- [ ] 7.2 Crear `docs/03 Implementación/Catálogo de rutas.md` (D11) con `/` y `/admin/` (método, vista, rol, RF) y el enlace de retorno al README; enlazarlo desde el README. Verificar: las rutas del catálogo coinciden con `config/urls.py`
- [ ] 7.3 Actualizar en el README el estado del proyecto (Sprint 1 en curso). Verificar: enlaces relativos funcionan

## 8. Verificación integral y cierre según la DoD

- [ ] 8.1 Desde una base vacía (`docker compose down -v`): `docker compose up` responde en `/` con estilos; `uv run pytest --cov` en verde con cobertura de 80 % o más (DoD 1); `uv run ruff check .` y `uv run ruff format --check .` limpios. Verificar: salida de cada comando registrada en el PR
- [ ] 8.2 Versión de Python igual en laptop y contenedor. Verificar: `uv run python --version` y `docker compose run --rm web python --version` muestran 3.13.x
- [ ] 8.3 DoD 9: README, docstrings en modelos, vista y configuración, catálogo de rutas y specs del cambio al día. Verificar: lista de comprobación en la descripción del PR
- [ ] 8.4 DoD 8 y revisión antes de cerrar: `git status` y diff sin `.env`, `insumos/`, claves, datos reales de estudiantes ni archivos de terceros; solo datos ficticios en pruebas. Verificar: lista de archivos del commit revisada con el usuario

## Workflow follow-up

- Commit con el correo noreply de GitHub del autor y sin `Co-Authored-By`, solo con aprobación del usuario.
- Push de `feature/EN-01-proyecto-django` y PR **hacia `main`** enlazado al issue EN-01, solo con confirmación. El PR lo aprueba otra integrante (DoD 3) e indica que los criterios 2, 4 y 5 de la DoD esperan a EN-08 y EN-02.
- Mover EN-01 en el tablero a In Review.
- Archivar el cambio (`/opsx:archive`) después de fusionar el PR.
- Llevar a EN-02 los pendientes de `design.md` ("Pendientes para EN-02"): compilar Tailwind antes de `collectstatic` en Vercel, igualar PostgreSQL a Neon y confirmar Python 3.13 en Vercel.
- Proponer al equipo los ajustes de `design.md` ("Pendientes de documentación"), con subida de versión.
