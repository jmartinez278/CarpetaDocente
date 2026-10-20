# CarpetaDocente

Sistema web para la gestión y planificación pedagógica en educación primaria – I.E. Virgen del Carmen, Huayucachi (Huancayo, Junín), 2026.

El sistema cubre tres dimensiones de la gestión pedagógica del docente de primaria:
1. Planificación de sesiones de aprendizaje
2. Registro y control de notas
3. Control de asistencia

Este proyecto se desarrolla con asistencia de Claude Code; las decisiones de diseño y alcance las toma el equipo.

**Stack:** Django · PostgreSQL · HTMX · Tailwind CSS · Alpine.js ([ver justificación](<docs/01 Inicio/10. Stack tecnológico V_1_2_0.md>))

**Equipo:** Martinez Llanos Marco Jhair (Director de Proyecto) · Cuicapuza Remigio Nayely Nilda · Vera Zea Jhoanna Hade
**Asesor:** Ing. Elvis Wilfredo Carmen Delgadillo

## Estado del proyecto

| Fase | Estado |
|---|---|
| 01 Inicio | Completa |
| 02 Planificación | En curso (falta el tablero de GitHub Projects) |
| 03 Implementación – Sprint 1 | En curso (EN-01: proyecto base con Docker Compose) |

## Documentación

### Fase 01: Inicio
1. [Selección del enfoque del proyecto](<docs/01 Inicio/01. Selección del enfoque del proyecto V_1_0_0.md>)
2. [Acta de constitución](<docs/01 Inicio/02. Acta de constitución V_1_3_0.md>)
3. [Declaración de la visión](<docs/01 Inicio/03. Declaración de la visión V_1_1_0.md>)
4. [Registro de supuestos y restricciones](<docs/01 Inicio/04. Registro de supuestos y restricciones V_1_2_0.md>)
5. [Registro de interesados](<docs/01 Inicio/05. Registro de interesados V_1_0_0.md>)
6. [Requisitos funcionales](<docs/01 Inicio/06. Requisitos funcionales V_1_3_0.md>)
7. [Requisitos no funcionales](<docs/01 Inicio/07. Requisitos no funcionales V_1_1_0.md>)
8. [Usuarios](<docs/01 Inicio/08. Usuarios V_1_1_0.md>)
9. [Reglas de negocio](<docs/01 Inicio/09. Reglas de negocio V_1_0_0.md>)
10. [Stack tecnológico](<docs/01 Inicio/10. Stack tecnológico V_1_2_0.md>)
11. [Base de datos](<docs/01 Inicio/11. Base de datos V_1_2_0.md>)
12. [Modelo C4](<docs/01 Inicio/12. Modelo C4 V_1_1_0.md>)
13. [Restricciones](<docs/01 Inicio/13. Restricciones V_1_1_0.md>)

### Fase 02: Planificación
1. [Transformando a ágil](<docs/02 Planificación/01 Transformando a ágil V_1_2_0.md>)
2. Tablero GitHub Projects *(en elaboración)*
3. [Registro de riesgos](<docs/02 Planificación/03 Registro de riesgos V_1_1_0.md>)
4. [Presupuesto del proyecto](<docs/02 Planificación/04 Presupuesto del proyecto V_1_0_0.md>)

### Fase 03: Implementación
- [Catálogo de rutas de la aplicación](<docs/03 Implementación/Catálogo de rutas.md>)

## Configuración local

### Requisitos

| Herramienta | Para qué | Opción A (todo en Docker) | Opción B (Django en la laptop) |
|---|---|---|---|
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) | PostgreSQL, y en la opción A también Django y la compilación del CSS | Sí | Sí (solo PostgreSQL) |
| [uv](https://docs.astral.sh/uv/) | Python 3.13 y las dependencias de `uv.lock`; pruebas y Ruff | Solo para pruebas y Ruff | Sí |
| [Node.js](https://nodejs.org/) 24 | Compilar Tailwind CSS en la laptop | No | Sí |

uv descarga por sí mismo Python 3.13 (fijado en `.python-version`); no hace falta instalarlo aparte.

### 1. Variables de entorno

Copiar `.env.example` como `.env` y completar los valores. **Nunca subir `.env`**: el repositorio es público.

| Variable | Qué poner |
|---|---|
| `DJANGO_SECRET_KEY` | Una clave propia: `uv run python -c "import secrets; print(secrets.token_urlsafe(50))"` |
| `DJANGO_DEBUG` | `True` en la laptop. **Con Docker Compose es obligatoria**: Compose no arranca si falta, y el servidor de desarrollo solo sirve el CSS y el JavaScript con `True`. Fuera de Compose, si se omite, la depuración queda desactivada |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` (obligatoria con Docker Compose) |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Nombre de la base, usuario y contraseña de la base local. La contraseña solo con letras, números, `-` y `_`, porque va dentro de `DATABASE_URL` |
| `POSTGRES_PORT` | Vacío (usa 5432) o otro puerto si ya hay un PostgreSQL instalado en la laptop |
| `DATABASE_URL` | `postgres://<usuario>:<contraseña>@localhost:<puerto>/<base>`, con los mismos valores de `POSTGRES_*`. Lo usan Django y pytest en la laptop; el servicio `web` de Compose arma el suyo con el host `db` |
| `AWS_*` | Vacías por ahora (archivos de sesiones en Cloudflare R2, EN-03) |

### 2A. Opción A: todo con Docker Compose

```bash
docker compose up
```

Levanta tres servicios: `db` (PostgreSQL), `web` (aplica las migraciones y arranca Django) y `frontend` (compila Tailwind en modo observación). La primera vez construye la imagen. Abrir <http://localhost:8000>.

Para crear la cuenta de Administrador (queda con rol `ADMINISTRADOR`):

```bash
docker compose exec web python src/backend/manage.py createsuperuser
```

### 2B. Opción B: PostgreSQL en Docker y Django en la laptop

```bash
docker compose up -d db
uv sync
uv run python src/backend/manage.py migrate
uv run python src/backend/manage.py runserver
```

En otra terminal, compilar el CSS en modo observación:

```bash
cd src/frontend
npm ci
npm run dev
```

### 3. Pruebas y calidad del código

Las pruebas usan PostgreSQL, así que `db` debe estar levantado (`docker compose up -d db`):

```bash
uv run pytest --cov
uv run ruff check .
uv run ruff format --check .
```

`uv run pytest --cov` falla si la cobertura total baja de **80 %** (DoD 1), aunque todas las pruebas pasen. El umbral está en `pyproject.toml` (`fail_under`) y es el mismo que aplica el canal de integración continua. La cobertura mide `src/backend` y `scripts/`, sin contar las migraciones ni las pruebas.

Para generar el informe que lee SonarQube Cloud: `uv run pytest --cov --cov-report=xml`. El archivo `coverage.xml` es local y no se versiona (está en `.gitignore`).

#### Pruebas de punta a punta (Playwright)

Las pruebas marcadas `e2e` abren la aplicación en Chromium. `uv run pytest` no las ejecuta, así que no hace falta un navegador para las pruebas de siempre. Para correrlas en la laptop:

1. Instalar Chromium para Playwright, una sola vez: `uv run playwright install chromium`.
2. Compilar el CSS. Si `frontend` de Docker Compose (opción A) está corriendo, ya está compilado. Si no:

   ```bash
   cd src/frontend
   npm ci
   npm run build
   ```

3. Con `db` levantado, desde la raíz del repositorio:

   ```bash
   # Git Bash
   DJANGO_ALLOW_ASYNC_UNSAFE=true uv run pytest -m e2e --browser chromium
   ```

   ```powershell
   # PowerShell
   $env:DJANGO_ALLOW_ASYNC_UNSAFE = "true"; uv run pytest -m e2e --browser chromium
   ```

`DJANGO_ALLOW_ASYNC_UNSAFE` hace falta porque Playwright deja abierto un bucle asíncrono en el hilo de la prueba y Django rechaza el acceso a la base desde ahí (`SynchronousOnlyOperation`). Va solo en este comando y en el canal, nunca en `.env` ni en `settings.py` (en PowerShell queda definida hasta cerrar esa terminal).

### Problemas frecuentes

| Síntoma | Solución |
|---|---|
| La página sale sin estilos | Falta compilar el CSS: en la opción A, revisar `docker compose logs frontend`; en la opción B, `npm run dev` en `src/frontend` |
| Compose dice `required variable ... is missing a value` | Falta esa variable en `.env` (ver el paso 1) |
| El puerto 5432 ya está en uso | Poner otro puerto en `POSTGRES_PORT` (por ejemplo `5433`) y el mismo en `DATABASE_URL` |
| Se quiere empezar con la base vacía | `docker compose down -v` (borra la base local y sus datos) y luego `docker compose up` |

## Verificación antes de un commit o PR

Las revisiones que antes se hacían a mano están en dos hooks de git y un script. Todo corre con `uv run` y funciona igual en Git Bash y en PowerShell.

### Hooks de git (una vez por laptop)

Los hooks viven versionados en `.githooks/`. Cada integrante los activa una sola vez, desde la raíz del repositorio:

```bash
git config core.hooksPath .githooks
```

- `commit-msg` rechaza el commit si el mensaje trae líneas de atribución a Claude (la lista está en `scripts/reglas.py`).
- `pre-commit` rechaza el commit si en el índice hay `.env`, `insumos/`, `node_modules/`, `static/dist/` o `coverage.xml`, o si una línea agregada parece una clave: clave de Django, `SECRET_KEY` con un valor escrito, tokens de SonarQube, GitHub o AWS, llaves privadas o una URL con `usuario:contraseña@` (los patrones están en `scripts/reglas.py`). Dice el archivo y la línea sin mostrar el valor. `.env.example` queda fuera, y en las pruebas se aceptan valores falsos si la misma línea dice "ficticio" o "ficticia". Al final corre `uv run ruff check` y `uv run ruff format --check`.

Git para Windows ejecuta los hooks con su propio `sh`, así que no hace falta instalar nada más; solo que `uv` esté en el `PATH`. Si un hook rechaza el commit, se corrige lo que indica y se vuelve a hacer el commit. No se usa `git commit --no-verify`.

### Script de verificación

Se corre con `db` levantado (`docker compose up -d db`), en la rama del cambio. Revisa los commits sobre `main` (correo noreply y sin atribuciones), los archivos prohibidos, Ruff y `pytest --cov` con el mínimo de 80 %. Termina con **PASA** o **NO PASA** y la lista de fallas. Si `main` local está detrás de `origin/main`, avisa que falta `git pull` sin cambiar el veredicto.

Se usa en dos momentos:

| Momento | Quién | Comando | Qué cambia |
|---|---|---|---|
| Antes de cada commit | Claude Code, antes de proponer el commit | `uv run python scripts/verificar.py --antes-del-commit` | Lo que va a entrar debe estar en el índice (`git add`). Falla solo si quedan archivos modificados fuera del índice o sin seguimiento. Los archivos prohibidos se buscan en el índice |
| Antes de pedir revisión | Quien abre el PR | `uv run python scripts/verificar.py --pr 53` | Todo debe estar en commits: `git status` limpio. Con `--pr` y `gh` instalado, revisa además los checks del PR y que tenga una aprobación. La plantilla del PR lo pide |

Para dejar constancia en `verificacion.md`: `uv run python scripts/verificar.py --markdown` imprime un bloque con fecha, resultados, salidas resumidas y cobertura.

### Copia para el Proyecto de claude.ai

```bash
uv run python scripts/copiar_para_proyecto.py                      # en ../CarpetaDocente_para_Proyecto
uv run python scripts/copiar_para_proyecto.py --destino D:/copia   # en otra carpeta
```

Copia el repositorio a una carpeta fuera de él, sin `.git`, `.venv`, `.claude/`, dependencias, archivos generados, `insumos/` ni `.env`, y muestra cuántos archivos copió, el tamaño total y los 5 más pesados. Si la carpeta ya existe, pregunta antes de reemplazarla.

> Genera la copia desde main actualizada (git switch main y git pull); desde otra rama la copia lleva esa versión de los documentos.

### Subir la versión de un documento

```bash
uv run python scripts/subir_version.py "docs/01 Inicio/07. Requisitos no funcionales V_1_0_0.md" --descripcion "Qué cambió."
uv run python scripts/subir_version.py "<ruta>" --descripcion "Qué cambió." --mayor   # V_2_0_0
```

Por defecto sube la versión menor (V_1_0_0 → V_1_1_0). Renombra el archivo con `git mv`, actualiza los campos Versión y Fecha del encabezado, agrega la fila al final del historial de cambios y cambia el enlace del README. Si falta algo (el enlace, el encabezado o el historial), no cambia nada. El contenido se edita aparte y el commit lo hace quien lo corre.

## Integración continua

Cada Pull Request hacia `main`, y cada push a `main`, pasa por el workflow `CI` (`.github/workflows/ci.yml`, EN-08). Con eso se comprueban los criterios 1, 2 y 5 de la DoD. CodeQL corre aparte, con la configuración por defecto de GitHub. Un commit nuevo en el PR vuelve a ejecutar todo.

### Verificaciones

| Verificación | Qué revisa | Cómo reproducirla en la laptop |
|---|---|---|
| `Ruff` | Estilo, formato y reglas de seguridad `S` (Bandit), con las reglas de `pyproject.toml`. Los problemas aparecen como anotaciones en las líneas del PR | `uv run ruff check .` y `uv run ruff format --check .` |
| `Pruebas y cobertura` | Todas las pruebas, menos las `e2e`, contra un PostgreSQL 17 temporal. Falla si una prueba falla o si la cobertura total baja de 80 % | Con `db` levantado: `uv run pytest --cov` |
| `Playwright` | Compila el CSS y abre la página inicial en Chromium (pruebas `e2e`) | Los tres pasos de [Pruebas de punta a punta](#pruebas-de-punta-a-punta-playwright) |
| `SonarQube Cloud` | Sube el análisis y la cobertura (`coverage.xml`) a SonarQube Cloud. Solo falla si el análisis no se pudo subir | No se reproduce: necesita el token. El informe que sube se genera con `uv run pytest --cov --cov-report=xml` |
| `SonarCloud Code Analysis` | Puerta de calidad **Sonar way** sobre el código nuevo del PR: cobertura de 80 % o más, duplicación de 3 % o menos, calificación A en fiabilidad, seguridad y mantenibilidad, y *hotspots* revisados. La publica la aplicación de SonarQube Cloud | No se reproduce: se ve en SonarQube Cloud, en el PR |
| CodeQL | Análisis de seguridad de Python, JavaScript y los workflows. Se bloquea la fusión con alertas de severidad alta o crítica | No se reproduce: las alertas aparecen en el PR y en *Security → Code scanning*. Ruff con las reglas `S` cubre una parte en la laptop |

El canal no usa claves reales:
- La base es un PostgreSQL de servicio, sin contraseña, que se destruye al terminar cada trabajo. Solo tiene los datos ficticios que crean las pruebas.
- La clave de Django se genera en cada ejecución.
- El único secreto es el token de SonarQube Cloud. **Vive solo en los secretos de GitHub** (`SONAR_TOKEN`) y el workflow lo lee como `${{ secrets.SONAR_TOKEN }}`. No va en el repositorio, en `.env` ni en ningún mensaje.

> **No renombrar los trabajos de `ci.yml`.** El `name:` de cada uno (`Ruff`, `Pruebas y cobertura`, `Playwright`, `SonarQube Cloud`) es la verificación que exige el *ruleset* de `main`. Si se renombra uno, el *ruleset* se queda esperando una verificación que ya no existe y ningún PR se puede fusionar. Si hace falta renombrar, hay que actualizar el *ruleset* en el mismo momento.

### Puesta en marcha (equipo, una sola vez)

1. **SonarQube Cloud:** importar `jmartinez278/CarpetaDocente` (plan gratuito). En *Administration → Analysis Method*, apagar *Automatic Analysis*: si quedan activos el análisis automático y el de CI, el de CI falla. La organización y la clave del proyecto van en `sonar-project.properties`.
2. **Token:** generarlo en SonarQube Cloud y pegarlo en GitHub, en *Settings → Secrets and variables → Actions → New repository secret*, con el nombre `SONAR_TOKEN`. El valor no se comparte con nadie.
3. **CodeQL:** *Settings → Code security → Code scanning → CodeQL analysis → Set up → Default*, con el conjunto de consultas *Default*. No hay workflow de CodeQL en el repositorio.

### *Ruleset* de `main` (equipo, paso B10)

Se crea **después** de que el canal corra una vez en un PR: GitHub solo deja elegir verificaciones que ya existen en el repositorio. Ruta: *Settings → Rules → Rulesets → New ruleset → New branch ruleset*. *Enforcement status*: *Active*. *Target branches*: *Include default branch*. Se recomienda dejar vacía la lista de excepciones (*bypass list*), para que nadie fusione sin cumplir.

Lo que exige EN-08:

| Regla | Valor |
|---|---|
| *Require status checks to pass* | `Ruff`, `Pruebas y cobertura`, `Playwright`, `SonarQube Cloud` y `SonarCloud Code Analysis`; activar *Require branches to be up to date before merging* |
| *Require code scanning results* | Herramienta CodeQL: *Security alerts* "High or higher" y *Alerts* "Errors" |

Lo que el equipo agrega en el mismo paso B10, fuera de EN-08:

| Regla | Valor |
|---|---|
| *Require a pull request before merging* | 1 aprobación; *Dismiss stale pull request approvals when new commits are pushed*; *Require approval of the most recent reviewable push* (DoD 3: aprueba otra integrante) |
| *Block force pushes* | Activa |
| *Restrict deletions* | Activa |

## Datos

El repositorio es público: solo contiene datos ficticios. No se suben datos reales de estudiantes.
