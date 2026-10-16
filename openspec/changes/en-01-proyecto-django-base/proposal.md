# Propuesta: EN-01 – Proyecto Django base con PostgreSQL en Docker Compose

## Why

Ninguna historia del Sprint 1 puede empezar sin un proyecto Django común que los tres integrantes levanten igual en su laptop. EN-01 (`docs/02 Planificación/01 Transformando a ágil`, sección 6) pide un proyecto Django con sus 9 módulos y PostgreSQL que se levante con un solo comando. Además, el modelo de usuario propio (documento 11, sección 3.2) tiene que existir **antes de la primera migración**: cambiarlo después obliga a rehacer la base de datos.

## What Changes

- Estructura de código en dos carpetas, según la consigna:
  - `src/backend/`: proyecto Django completo (configuración, apps, modelos, vistas, **plantillas** y estáticos).
  - `src/frontend/`: solo las fuentes de Tailwind CSS y la copia de HTMX y Alpine.js; su compilación escribe en los estáticos de `src/backend/`.
- Nueve apps de Django, con los nombres del C4 (documento 12, nivel 3): `cuentas`, `institucion`, `catalogo`, `repositorio` (dimensión 1: planificación de sesiones de aprendizaje), `notas` (dimensión 2), `asistencia` (dimensión 3), `direccion`, `exportaciones` y `actividad`. En EN-01 solo `cuentas` e `institucion` tienen modelos; las demás quedan vacías y registradas.
- Modelo de usuario propio `cuentas.Usuario` (`AUTH_USER_MODEL`) y modelo `institucion.Institucion`, con los campos y restricciones `CHECK` del DDL del documento 11 para esas dos tablas.
- Configuración leída solo desde variables de entorno / `.env` (`DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `DATABASE_URL`, `POSTGRES_*`), sin claves en el código.
- `docker-compose.yml` con tres servicios: `db` (PostgreSQL), `web` (Django con `runserver`) y `frontend` (compila Tailwind en modo observación). Se puede levantar todo junto o solo `db` y correr Django y la compilación del CSS en la laptop.
- Gestor de dependencias **uv** con **Python 3.13** fijado en `.python-version` (justificación en `design.md`).
- Página inicial en `/` con la plantilla base (Tailwind, HTMX y Alpine.js cargados).
- pytest + pytest-django + pytest-cov y Ruff configurados en `pyproject.toml`, con pruebas iniciales.
- README: sección "Configuración local" con los pasos para levantar el proyecto.

**Fuera de alcance:** Cloudflare R2 y `django-storages` (EN-03), Vercel y Neon (EN-02), inicio de sesión y permisos (EN-04, RF-001+), GitHub Actions/CodeQL/SonarQube (EN-08), Playwright, y el resto de tablas del documento 11.

**Desviación aprobada por el usuario:** el escenario 2 de EN-01 ("la base de datos tiene las tablas y restricciones del documento 11") se cumple **parcialmente**: en EN-01 solo entran `usuario` e `institucion`. Cada tabla restante llega con la historia que la usa, con pruebas primero.

## Capabilities

### New Capabilities

- `entorno-desarrollo`: cómo se levanta y configura el sistema en local (Docker Compose, PostgreSQL, variables de entorno, página inicial, pruebas y Ruff).
- `cuentas-usuarios`: modelo de usuario propio con rol e institución, y la entidad Institución (documento 11, secciones 3.1 y 3.2).

### Modified Capabilities

_(ninguna; no hay especificaciones previas en `openspec/specs/`)_

## Impact

- **Código nuevo:** `src/backend/` (proyecto `config` y 9 apps), `src/frontend/` (`package.json`, CSS de entrada, script de copia), `pyproject.toml`, `uv.lock`, `.python-version`, `Dockerfile`, `docker-compose.yml`.
- **Archivos modificados:** `.gitignore` (estáticos compilados), `.env.example` (comentarios de uso local; las variables de R2 se conservan sin valor para EN-03), `README.md`.
- **Dependencias Python:** Django 5.2 LTS, django-environ, psycopg 3; de desarrollo: pytest, pytest-django, pytest-cov, Ruff.
- **Dependencias Node (solo `src/frontend/`):** tailwindcss y @tailwindcss/cli v4, htmx.org 2.0.x, alpinejs 3.x.
- **Requisitos:** EN-01; base para EN-02, EN-04 y las historias del Sprint 1. RNF-012 (contraseñas solo con hash) queda cubierto por el modelo de usuario de Django.
