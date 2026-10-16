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
7. [Requisitos no funcionales](<docs/01 Inicio/07. Requisitos no funcionales V_1_0_0.md>)
8. [Usuarios](<docs/01 Inicio/08. Usuarios V_1_1_0.md>)
9. [Reglas de negocio](<docs/01 Inicio/09. Reglas de negocio V_1_0_0.md>)
10. [Stack tecnológico](<docs/01 Inicio/10. Stack tecnológico V_1_2_0.md>)
11. [Base de datos](<docs/01 Inicio/11. Base de datos V_1_1_0.md>)
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

`uv run pytest --cov` falla si la cobertura total baja de **80 %** (DoD 1), aunque todas las pruebas pasen. El umbral está en `pyproject.toml` (`fail_under`) y es el mismo que aplica el canal de integración continua. La cobertura no cuenta las migraciones ni las pruebas.

Para generar el informe que lee SonarQube Cloud: `uv run pytest --cov --cov-report=xml`. El archivo `coverage.xml` es local y no se versiona (está en `.gitignore`).

### Problemas frecuentes

| Síntoma | Solución |
|---|---|
| La página sale sin estilos | Falta compilar el CSS: en la opción A, revisar `docker compose logs frontend`; en la opción B, `npm run dev` en `src/frontend` |
| Compose dice `required variable ... is missing a value` | Falta esa variable en `.env` (ver el paso 1) |
| El puerto 5432 ya está en uso | Poner otro puerto en `POSTGRES_PORT` (por ejemplo `5433`) y el mismo en `DATABASE_URL` |
| Se quiere empezar con la base vacía | `docker compose down -v` (borra la base local y sus datos) y luego `docker compose up` |

## Datos

El repositorio es público: solo contiene datos ficticios. No se suben datos reales de estudiantes.
