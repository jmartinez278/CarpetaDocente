# Design: EN-01 – Proyecto Django base

## Context

El repositorio solo tiene documentación, OpenSpec y la configuración de Fase 0 (`.gitignore`, `.env.example`, README). No hay código. Motivación y alcance en `proposal.md`; comportamiento esperado en `specs/entorno-desarrollo` y `specs/cuentas-usuarios`.

Restricciones que dan forma al diseño:
- Stack fijo del documento 10, sección 4: Django en su LTS vigente, PostgreSQL, plantillas con Tailwind, HTMX y Alpine.js; Docker Compose en local; pytest y Ruff.
- La consigna pide carpetas `src/frontend/` y `src/backend/`, pero con plantillas de Django no hay una aplicación de frontend aparte.
- Repositorio público: ninguna clave en el código (documento 02/01, "Manejo de claves").
- Regla de dependencias del C4 (documento 12, sección 4): vistas → servicios → modelos.
- En las laptops del equipo puede estar instalado Python 3.15, que Django 5.2 todavía no soporta.

## Goals / Non-Goals

**Goals:**
- Que los tres integrantes tengan el mismo entorno con `docker compose up`, o con `db` en Docker y Django en la laptop.
- Dejar fijado desde la primera migración el modelo de usuario propio.
- Dejar listas las convenciones de carpetas, pruebas y estilo que seguirán todas las historias.

**Non-Goals:**
- Inicio de sesión, permisos, middleware de seguridad y cierre por inactividad (EN-04).
- Capa de servicios con reglas de negocio: aún no hay reglas que aplicar; se crea con la primera historia que la necesite.
- Despliegue, `collectstatic` en Vercel y compilación de CSS en la nube (EN-02).
- Pipeline de CI (EN-08).

## Decisions

### D1. Estructura de carpetas

```
CarpetaDocente/
├── pyproject.toml        # dependencias, pytest y Ruff
├── uv.lock
├── .python-version       # 3.13
├── Dockerfile            # imagen de la app web (desarrollo)
├── docker-compose.yml    # servicios db, web y frontend
├── .env.example
└── src/
    ├── backend/
    │   ├── manage.py
    │   ├── config/       # settings.py, urls.py, wsgi.py, asgi.py
    │   ├── cuentas/  institucion/  catalogo/  repositorio/  notas/
    │   ├── asistencia/  direccion/  exportaciones/  actividad/
    │   ├── templates/    # base.html, inicio.html
    │   └── static/
    │       └── dist/     # salida de src/frontend (no se versiona)
    └── frontend/
        ├── package.json
        ├── css/app.css   # entrada de Tailwind
        └── scripts/copiar-vendor.mjs
```

- `pyproject.toml` en la raíz para que pytest, Ruff y (en EN-08) GitHub Actions corran desde la raíz sin cambiar de carpeta.
- Apps planas dentro de `src/backend/` (no `apps/<nombre>`): imports cortos (`cuentas.models`) y nombres idénticos al C4.
- Plantillas compartidas en `src/backend/templates/`; cada app tendrá su `templates/<app>/` cuando tenga pantallas.
- **Alternativa descartada:** poner `package.json` en la raíz. Se descarta porque la consigna pide que lo de frontend viva en `src/frontend/`.

### D2. Nueve apps con nombres del C4

`cuentas`, `institucion`, `catalogo`, `repositorio`, `notas`, `asistencia`, `direccion`, `exportaciones`, `actividad`, todas en `INSTALLED_APPS`. En EN-01 solo `cuentas` (Usuario y la vista de inicio) e `institucion` (Institucion) tienen código. La vista de inicio va en `cuentas` porque será la página de entrada tras el login (RF-001).

### D3. Gestor de dependencias: uv

- **uv**: un solo archivo de bloqueo (`uv.lock`) que garantiza versiones idénticas en las tres laptops y en Docker; instala por sí mismo la versión de Python fijada, lo que resuelve el caso de Python 3.15; `uv sync` y `uv run` sustituyen a crear y activar el entorno virtual a mano (menos errores en Windows).
- **Alternativas:** pip + `requirements.txt` (sin bloqueo de dependencias transitivas ni gestión de Python); Poetry (no instala Python y es más lento). Pipenv está en desuso.

### D4. Python 3.13

- Django 5.2 LTS soporta Python 3.10 a 3.14 (3.14 desde 5.2.8). **3.15 no está soportado**.
- Se elige 3.13: soportado desde la primera versión de Django 5.2, con un año de ruedas binarias publicadas por todas las librerías del stack (psycopg, librerías de Excel), y con soporte de seguridad de Python hasta octubre de 2029, más allá de la posprueba (2027).
- **Alternativa:** 3.14, más nueva y también válida; se descarta para no depender de un soporte agregado en una versión menor de Django. La compatibilidad del runtime de Python de Vercel se confirma en EN-02.
- **Una sola versión en todo el proyecto:** `.python-version` (uv, laptop) y la imagen base del `Dockerfile` (`python:3.13-slim`) dicen 3.13, y `requires-python` en `pyproject.toml` es `>=3.13,<3.14`. Si se cambia, se cambian los tres en el mismo commit; la verificación final compara `python --version` en la laptop y en el contenedor.

### D5. Django 5.2 LTS

Es la LTS vigente al iniciar el desarrollo (documento 10, sección 4), con soporte de seguridad hasta abril de 2028. Django 6.x no es LTS; la siguiente LTS será 6.2.

### D6. Configuración con django-environ y un solo `settings.py`

- `config/settings.py` lee `.env` de la raíz del repositorio con django-environ: `DJANGO_SECRET_KEY` (obligatoria, sin valor por defecto), `DJANGO_DEBUG` (por defecto `False`), `DJANGO_ALLOWED_HOSTS` (lista) y `DATABASE_URL` (obligatoria, parseada a `DATABASES`).
- Si una variable obligatoria falta, Django falla al arrancar con `ImproperlyConfigured` y el nombre de la variable.
- La conexión a PostgreSQL lleva `connect_timeout = 10` s por defecto (un `connect_timeout` en `DATABASE_URL` tiene prioridad). Hallazgo de la tarea 3.2: en Windows, sin base levantada, la conexión no se rechaza sino que espera indefinidamente y pytest queda colgado. 10 s deja margen al arranque en frío de Neon (EN-02).
- Un solo archivo de configuración; las diferencias entre local, vista previa y producción las ponen las variables (documento 12, sección 6: "solo cambian las variables").
- **Alternativas:** `dj-database-url` + `os.environ` (dos piezas y lectura manual de `.env`); varios `settings/` por ambiente (más archivos sin ganancia mientras todo dependa de variables).
- Idioma `es-pe`, zona horaria `America/Lima`, `USE_TZ = True`, `DEFAULT_AUTO_FIELD = BigAutoField` (coincide con `BIGSERIAL` del documento 11).

### D7. Modelos `Usuario` e `Institucion` fieles al documento 11

- `cuentas.Usuario` hereda de `AbstractUser` y agrega `rol`, `institucion` (FK con `PROTECT`, equivalente a `ON DELETE RESTRICT`), `debe_cambiar_password`, `intentos_fallidos` y `bloqueado_hasta`. `AUTH_USER_MODEL = "cuentas.Usuario"` se define antes de la primera migración.
- `institucion.Institucion`: `nombre`, `codigo_modular` (único y opcional), `organizacion_periodos` (opcional), `creado_en`.
- Nombres de tabla `usuario` e `institucion` (`db_table`) para que coincidan con el DDL del documento 11.
- Las restricciones del DDL se declaran como `CheckConstraint` en los modelos, con los mismos nombres (`ck_usuario_institucion`, etc.), para que las pruebas las verifiquen contra PostgreSQL y no solo en formularios. La sintaxis exacta se consulta en Context7 al implementar.
- Ambos se registran en el panel de administración de Django (rol Administrador, documento 10).

### D8. Docker Compose

- Servicio `db`: imagen oficial `postgres:17` (**provisional**: el documento 10 no fija la versión de PostgreSQL; en EN-02 se iguala a la versión mayor de Neon), credenciales tomadas de `POSTGRES_DB`, `POSTGRES_USER` y `POSTGRES_PASSWORD` del `.env`, volumen con nombre para los datos, `healthcheck` con `pg_isready` y puerto 5432 publicado para usar Django desde la laptop.
- Servicio `web`: `Dockerfile` basado en `python:3.13-slim` con uv; instala dependencias con `uv sync --frozen` en un entorno fuera de la carpeta montada; monta `src/backend/` para recarga automática; espera a que `db` esté sano, aplica migraciones y arranca `runserver 0.0.0.0:8000`.
- En `web`, `DATABASE_URL` se arma en `docker-compose.yml` con las variables `POSTGRES_*` y el host `db`; el `DATABASE_URL` del `.env` apunta a `localhost` para el modo laptop. Así no hay contraseñas en el YAML.
- Servicio `frontend`: compila Tailwind en modo observación (D9b). `web` no depende de él: la aplicación responde aunque el CSS aún no esté listo.
- **Alternativa descartada:** solo PostgreSQL en Docker (más simple, pero no cumple el escenario "docker compose up → la aplicación responde" de EN-01).

### D9. Frontend: Tailwind v4 CLI, HTMX y Alpine.js servidos como estáticos propios

- `src/frontend/package.json` con `tailwindcss` y `@tailwindcss/cli` (v4), `htmx.org` (2.0.x) y `alpinejs` (3.x).
- `css/app.css` importa Tailwind y declara con `@source` las plantillas de `src/backend/`. `npm run build` compila a `src/backend/static/dist/app.css` y copia `htmx.min.js` y `cdn.min.js` de Alpine a `static/dist/vendor/`; `npm run dev` compila en modo observación.
- Se sirven desde los estáticos propios y no desde un CDN externo: versiones fijadas por `package-lock.json` y sin depender de terceros para la política de seguridad de contenido de EN-04.
- `static/dist/` no se versiona (es compilado). La compilación en la nube se resuelve en EN-02.

### D9b. Quién compila Tailwind en cada forma de levantar el proyecto

Si nadie compila, la página sale sin estilos. Por eso cada forma de levantar el proyecto tiene un responsable:

| Forma | Quién compila | Qué hace el integrante |
|---|---|---|
| `docker compose up` (opción A) | Servicio `frontend` del compose (`node:24-slim`): `npm ci` y luego `npm run dev:contenedor` (modo observación por sondeo, `--poll=1000`), escribiendo en `src/backend/static/dist/` por la carpeta montada | Nada; no necesita Node en la laptop |
| `db` en Docker + Django en la laptop (opción B) | El integrante, en otra terminal: `npm ci` (una vez) y `npm run dev` en `src/frontend/` | Tener Node 24 instalado |
| Solo pruebas (`pytest`) | Nadie | Las pruebas verifican el enlace al CSS, no su contenido |

- `node_modules` del servicio `frontend` vive en un volumen con nombre, no en la carpeta montada: así no se mezclan los binarios de Linux (contenedor) con los de Windows (laptop).
- El README explica las dos opciones en la sección "Configuración local", con una nota: "si la página sale sin estilos, falta compilar el CSS" y el comando para hacerlo.
- **Alternativa descartada:** compilar el CSS dentro de la imagen de `web` (mezcla Node en la imagen de Python y no observa cambios).

### D10. Pruebas y estilo

- pytest-django con `DJANGO_SETTINGS_MODULE = "config.settings"` y `pythonpath = ["src/backend"]` en `pyproject.toml`; pruebas en `src/backend/<app>/tests/`. Las pruebas usan la base PostgreSQL del compose (pytest-django crea y borra su propia base de prueba).
- Pruebas iniciales: página inicial (estado 200, dimensiones en orden, recursos estáticos enlazados), conexión a PostgreSQL, configuración (`DEBUG` por defecto) y restricciones de `Usuario` e `Institucion`.
- Ruff con `target-version = "py313"`, reglas `E`, `F`, `W`, `I`, `B`, `UP`, `DJ` y `S` (seguridad, derivadas de Bandit); `S101` permitido en pruebas; migraciones excluidas. Se verifica con `ruff check` y `ruff format --check`.
- Cobertura con pytest-cov; se reporta localmente y se espera 80 % o más (DoD 1). La puerta automática llega con EN-08.

### D11. Cierre según la DoD (criterios 8 y 9)

- **Criterio 8 (sin datos reales):** las pruebas y cualquier dato de ejemplo usan nombres y valores evidentemente ficticios; revisión del diff antes del commit.
- **Criterio 9 (documentación):**
  - README actualizado (D9b y "Configuración local").
  - Docstrings en español en modelos, vista y módulo de configuración.
  - **Catálogo de rutas** en `docs/03 Implementación/Catálogo de rutas.md`, fuera de las carpetas de sprint porque crece con todo el proyecto. En EN-01 tiene `/` (página inicial, `cuentas`) y `/admin/` (panel del Administrador), con método, vista, rol y RF. Cada historia que agrega rutas lo actualiza.
  - Especificación en OpenSpec: este cambio; sus specs pasan a `openspec/specs/` al archivarlo después de fusionar el PR.
- Los criterios 2 (CodeQL, SonarQube), 4 (vista previa de Vercel) y 5 (Playwright) dependen de EN-08 y EN-02, que aún no existen; en el PR de EN-01 se indica que quedan pendientes por eso.

## Pendientes para EN-02

- Vercel ejecuta `collectstatic`, así que el CSS de Tailwind (y la copia de HTMX y Alpine) **tiene que compilarse antes**, en el mismo build: `npm ci && npm run build` en `src/frontend/` y luego `collectstatic`.
- Igualar la versión de PostgreSQL del compose a la de Neon (D8).
- Confirmar que el runtime de Python de Vercel admite 3.13 (D4).

## Pendientes de documentación (para el equipo)

No se editan en este cambio; se proponen aparte, con subida de versión si el equipo aprueba:

- `docs/02 Planificación/01 Transformando a ágil`, EN-02: el título dice "Despliegue en Vercel, Neon y R2", pero el trabajo con R2 está en EN-03 y los escenarios de EN-02 no mencionan R2.
- `docs/02 Planificación/03 Registro de riesgos`, RSK-13: el plan de contingencia habla de "sesiones privadas de cada docente", pero el documento 06 (V_1_2_0) eliminó las sesiones privadas.
- `docs/02 Planificación/01 Transformando a ágil`, EN-01, escenario 2: ajustar a "tablas de usuario e institución; las demás con su historia" (desviación aprobada).

## Risks / Trade-offs

- [Puerto 5432 ocupado por un PostgreSQL instalado en la laptop] → El puerto publicado se toma de una variable `POSTGRES_PORT` con valor por defecto 5432; el README lo explica.
- [Integrante sin compilar el CSS ve la página sin estilos] → En la opción A lo compila el servicio `frontend` (D9b); en la opción B, paso explícito en el README. La prueba de la página inicial verifica el enlace, no el archivo.
- [El modo observación de Tailwind dentro del contenedor no detecta cambios de archivos guardados desde Windows en la carpeta montada: comprobado en la tarea 6.3] → El servicio `frontend` usa `npm run dev:contenedor`, que observa por sondeo (`--poll=1000`); con eso el cambio se detecta en unos 2 s. En la laptop, `npm run dev` usa los eventos nativos. No afecta a `runserver`, que revisa los archivos por sondeo.
- [Python 3.15 instalado en la laptop] → uv descarga y usa 3.13 según `.python-version`.
- [Finales de línea de Windows dentro del contenedor] → No se usan scripts de shell en la imagen; el comando del servicio va en `docker-compose.yml`.
- [Solo dos tablas del documento 11 en EN-01] → Desviación aprobada; cada historia agrega las suyas con pruebas. Conviene ajustar el escenario 2 de EN-01 en el documento 02/01 (propuesta aparte, con subida de versión).
- [Aplicar migraciones al arrancar `web` puede ocultar un error de migración entre otros logs] → El comando se detiene si `migrate` falla, y `web` no arranca.

## Migration Plan

Proyecto nuevo: no hay datos que migrar. Para volver atrás basta con no fusionar la rama; `docker compose down -v` borra la base local.

## Open Questions

- Versión mayor de PostgreSQL en Neon: se confirma en EN-02 y, si difiere de 17, se ajusta la imagen del compose (ver "Pendientes para EN-02").
- Hex de los acentos dorado/ocre de la identidad visual: los define el equipo antes de US-001; no afecta a EN-01.
