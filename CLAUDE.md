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
- No regenerar esos documentos. Contradicciones o vacíos entre documentos: reportar con archivo y apartado; si el equipo aprueba, editar subiendo versión (V_1_1_0 / V_2_0_0) con historial de cambios.
- Contradicciones del aplicativo con la tesis (variables, dimensiones, alcance): no resolverlas, anotarlas en `docs/PENDIENTES_TESIS.md`.
- El equipo (3 integrantes) decide; Claude propone.

## Stack (decidido, documento 10)

Django (LTS) + PostgreSQL (Docker Compose en local) + plantillas de Django con HTMX, Tailwind CSS y Alpine.js. Pruebas con pytest / pytest-django; estilo con Ruff. Despliegue posterior: Vercel + Neon (EN-02). Archivos de sesiones en Cloudflare R2: **EN-03, no EN-02**.

Reglas de diseño: las reglas de negocio van en una capa de servicios (las vistas no escriben directo en la BD); la entidad Institución existe desde el inicio.

## Flujo de trabajo

- La propuesta y las tareas las genera **OpenSpec** (`/opsx:propose`, luego `/opsx:apply`), no Superpowers.
- **No** usar las habilidades `brainstorming` ni `writing-plans` de Superpowers.
- De Superpowers usar solo: ejecución con pruebas primero (TDD), debugging sistemático y revisión antes de cerrar.
- Para Django, HTMX y Tailwind consultar **Context7**, no la memoria.
- Alcance actual: solo las historias y enablers del Sprint 1.

## Interfaz

- **Referencia visual:** `DESIGN.md` de la raíz (propuesta 0.2), ratificada por el equipo al aprobar otra integrante el PR que la incorporó (cierra C7).
- **Flujo de diseño:** Impeccable (instalación global, con `--no-hooks` y la telemetría apagada) → prototipo estático en `insumos/prototipo/` (local, no se sube) → el diseño ganador se pasa a plantillas de Django. Google Stitch queda descartado por ahora.
- **Playwright MCP** (navegador manejado por el asistente) se usa solo al final, en el pulido; no durante la construcción de cada historia.
- En las plantillas **no se escriben colores hex**: solo clases de los tokens de `DESIGN.md`.
- **Prohibido el desplazamiento horizontal** en páginas y componentes (RNF-005).
- Sin logo ni escudo de la I.E. hasta tener su autorización; el nombre va en texto.
- El `PRODUCT.md` que genere Impeccable remite a los documentos 03 y 08 y no entra al repo hasta que el equipo lo revise.

## Git y Pull Requests

- Una rama y un PR por issue: `feature/<ID>-<descripcion>` desde `main`.
- Todo PR se abre **hacia `main`**: el plan gratuito de SonarQube Cloud solo analiza `main` y los PR dirigidos a ella.
- Cada PR lo aprueba **otra integrante**, no quien lo abre (DoD, criterio 3).
- Commits con el correo noreply de GitHub del autor y **sin** `Co-Authored-By`.
- Sin force push. Commit y push solo con aprobación explícita; antes, mostrar qué archivos entran y el mensaje propuesto.
- Antes de proponer un commit, deja en el índice lo que va a entrar, corre `uv run python scripts/verificar.py --antes-del-commit` y muestra su veredicto.
- Nunca subir `.env`, `insumos/`, datos reales de estudiantes ni archivos de terceros. Solo `.env.example` sin valores.

## Datos

Solo datos ficticios. Datos de la I.E. no confirmados: `[DATO I.E. PENDIENTE]`.
