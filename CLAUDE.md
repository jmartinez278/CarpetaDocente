# CLAUDE.md

Guía para Claude Code en este repositorio. El repo es **público**: aquí no van claves, correos personales ni datos reales.

## Proyecto

Sistema web de gestión y planificación pedagógica para primaria (EBR), I.E. Virgen del Carmen – Huayucachi (Huancayo, Junín). Proyecto de tesis: VI "Implementación de un sistema web"; VD "Gestión y planificación pedagógica". Tres dimensiones, en este orden: planificación de sesiones de aprendizaje, registro y control de notas, control de asistencia.

Enfoque descartado: aula virtual / LMS con IA y analítica. No reintroducirlo.

## Fuente de verdad

- **OpenSpec manda** sobre el comportamiento: `openspec/specs/` (vigente) y `openspec/changes/` (en curso). Las reglas para escribir sus artefactos están en `openspec/config.yaml`.
- `docs/01 Inicio/` y `docs/02 Planificación/` son la referencia de lo que se pidió (requisitos 06 y 07, usuarios 08, reglas de negocio 09, stack 10, base de datos 11, C4 12, historias 02/01). Están **congelados**: se leen, no se editan ni se regeneran. Si chocan con OpenSpec, manda OpenSpec y el choque va a la deuda del cambio. Solo se edita un documento si el equipo cambia un requisito, subiendo versión con `scripts/subir_version.py`.
- Alcance: las historias y enablers del Sprint 1, en el orden del tablero (GitHub Projects).
- El equipo (3 integrantes) decide; Claude propone.

## Stack (documento 10)

Django (LTS) + PostgreSQL (Docker Compose en local) + plantillas de Django con HTMX, Tailwind CSS y Alpine.js. Pruebas con pytest / pytest-django y Playwright; estilo con Ruff. Despliegue: Vercel + Neon. Archivos de sesiones en Cloudflare R2 (EN-03).

## Estructura y comandos

- `src/backend/`: proyecto Django (`config/` y una app por módulo del documento 12), plantillas en `templates/`, estáticos en `static/`.
- `src/frontend/`: fuentes de Tailwind; `npm run build` compila el CSS y copia HTMX y Alpine a `src/backend/static/dist/`.
- `scripts/`: `verificar.py` (antes de un commit o PR), `hooks.py` y `reglas.py` (hooks de `.githooks/`), `subir_version.py`.
- `openspec/`: un cambio por historia o enabler en `changes/` (propuesta, design, specs, tasks y `verificacion.md`); al fusionar se archiva y sus specs pasan a `specs/`.
- Comandos (detalle en el README):
  - `docker compose up -d db`
  - `uv run pytest --cov` (mínimo 80 %)
  - `uv run pytest -m e2e --browser chromium`, con el CSS compilado y `DJANGO_ALLOW_ASYNC_UNSAFE=true`
  - `uv run ruff check .` y `uv run ruff format --check .`

## Convenciones

- Las reglas de negocio van en la capa de servicios (`servicios.py`); las vistas no escriben directo en la base de datos. La entidad Institución existe desde el inicio.
- Pruebas primero: cada prueba se ve fallar antes del código.
- Interfaz: la referencia visual es `DESIGN.md`. Las reglas de plantillas están en `.claude/rules/plantillas.md` y se cargan al tocar plantillas, estáticos o `src/frontend/`.
- No renombrar los trabajos de `.github/workflows/ci.yml`: el ruleset `proteger-main` los exige por nombre.
- Si un prompt trae marcadores sin llenar (`___`, `<N>`), pedir el dato; no completarlos.

## Git y Pull Requests

- Una rama y un PR por historia o enabler: `feature/<ID>-<descripcion>` desde `main` actualizada, sin ramas apiladas. El primer commit de cada rama es el archivo (`/opsx:archive`) de la historia anterior.
- Todo PR va **hacia `main`** (SonarQube Cloud solo analiza `main` y los PR hacia ella). Lo aprueba **otra integrante**, no quien lo abre (DoD 3).
- Commits con el correo noreply de GitHub del autor y **sin** `Co-Authored-By` ni líneas que atribuyan el commit a una IA.
- Sin force push ni rebase de ramas publicadas. Commit y push solo con aprobación explícita; antes, mostrar qué archivos entran y el mensaje.
- Antes de proponer un commit: lo que entra va al índice y se corre `uv run python scripts/verificar.py --antes-del-commit`; se muestra su veredicto.
- Nunca subir `.env`, `insumos/`, datos reales de estudiantes ni archivos de terceros. Solo `.env.example` sin valores.

## Datos

Solo datos ficticios. Datos de la I.E. no confirmados: `[DATO I.E. PENDIENTE]`.
