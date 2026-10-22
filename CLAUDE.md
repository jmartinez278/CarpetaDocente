# CLAUDE.md

Guía para Claude Code en este repositorio. El repo es **público**: aquí no van claves, correos personales ni datos reales.

## Proyecto

Sistema web de gestión y planificación pedagógica para primaria (EBR), I.E. Virgen del Carmen – Huayucachi (Huancayo, Junín). Proyecto de tesis: VI "Implementación de un sistema web"; VD "Gestión y planificación pedagógica".

Tres dimensiones, en este orden:
1. Planificación de sesiones de aprendizaje
2. Registro y control de notas
3. Control de asistencia

Enfoque descartado: aula virtual / LMS con IA y analítica. No reintroducirlo.

## Fuente de verdad

- `docs/01 Inicio/` y `docs/02 Planificación/`: requisitos (06, 07), usuarios (08), reglas de negocio (09), stack (10), base de datos (11), C4 (12), historias y enablers (02/01).
- No regenerar esos documentos. Contradicciones o vacíos entre documentos: reportar con archivo y apartado; si el equipo aprueba, editar subiendo versión (V_1_1_0 / V_2_0_0) con historial de cambios (`scripts/subir_version.py`, ver README).
- El equipo (3 integrantes) decide; Claude propone.

## Stack (decidido, documento 10)

Django (LTS) + PostgreSQL (Docker Compose en local) + plantillas de Django con HTMX, Tailwind CSS y Alpine.js. Pruebas con pytest / pytest-django; estilo con Ruff. Despliegue posterior: Vercel + Neon (EN-02). Archivos de sesiones en Cloudflare R2: **EN-03, no EN-02**.

Reglas de diseño: las reglas de negocio van en una capa de servicios (las vistas no escriben directo en la BD); la entidad Institución existe desde el inicio.

## Estructura y comandos

- `src/backend/`: proyecto Django (`config/` y una app por módulo del documento 12), plantillas en `templates/` y estáticos en `static/`.
- `src/frontend/`: fuentes de Tailwind; `npm run build` compila el CSS y copia HTMX y Alpine a `src/backend/static/dist/`.
- `scripts/`: `verificar.py` (verificación antes de un commit o PR), `hooks.py` y `reglas.py` (hooks de `.githooks/`) y `subir_version.py`.
- `openspec/`: un cambio por historia o enabler en `changes/` (propuesta, design, specs, tasks y `verificacion.md`); al fusionar se archiva y sus specs pasan a `specs/`.
- Comandos de cada día (detalle en el README, "Configuración local" y "Pruebas y calidad del código"):
  - `docker compose up -d db`
  - `uv run pytest --cov` (mínimo 80 %)
  - `uv run pytest -m e2e --browser chromium`, con el CSS compilado y `DJANGO_ALLOW_ASYNC_UNSAFE=true` (README, "Pruebas de punta a punta")
  - `uv run ruff check .` y `uv run ruff format --check .`

## Flujo de trabajo

- La propuesta y las tareas de cada historia o enabler se trabajan como un cambio de **OpenSpec** (`openspec/`).
- Alcance actual: solo las historias y enablers del Sprint 1.

## Interfaz

- **Referencia visual:** `DESIGN.md` de la raíz.
- En las plantillas **no se escriben colores hex**: solo clases de los tokens de `DESIGN.md`.
- **Prohibido el desplazamiento horizontal** en páginas y componentes (RNF-005). Única excepción: el carrusel de dimensiones de la portada en el celular (`DESIGN.md`); la página no se desplaza.
- **Temas claro y oscuro** según la preferencia del sistema (`prefers-color-scheme`), con los mismos tokens (`DESIGN.md`). Cada pantalla se verifica en ambos temas. El selector de tema es un RF futuro, después del Sprint 1: no se agrega antes.
- Sin logo ni escudo de la I.E. hasta tener su autorización; el nombre va en texto.
- El `PRODUCT.md` que genere Impeccable remite a los documentos 03 y 08 y no entra al repo hasta que el equipo lo revise.

## Git y Pull Requests

- Una rama y un PR por issue: `feature/<ID>-<descripcion>` desde `main`.
- Todo PR se abre **hacia `main`**: el plan gratuito de SonarQube Cloud solo analiza `main` y los PR dirigidos a ella.
- Cada PR lo aprueba **otra integrante**, no quien lo abre (DoD, criterio 3).
- Commits con el correo noreply de GitHub del autor y **sin** `Co-Authored-By`.
- Sin force push. Commit y push solo con aprobación explícita; antes, mostrar qué archivos entran y el mensaje propuesto.
- Antes de proponer un commit, deja en el índice lo que va a entrar, corre `uv run python scripts/verificar.py --antes-del-commit` y muestra su veredicto (README, "Verificación antes de un commit o PR").
- Nunca subir `.env`, `insumos/`, datos reales de estudiantes ni archivos de terceros. Solo `.env.example` sin valores.

## Datos

Solo datos ficticios. Datos de la I.E. no confirmados: `[DATO I.E. PENDIENTE]`.
