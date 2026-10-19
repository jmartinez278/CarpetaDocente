---
name: "tesis-aplicativo"
description: "Usar en Claude Code para construir el sistema web de la tesis (I.E. Virgen del Carmen) a partir de los docs/ ya aprobados: repo, tablero en GitHub Projects, desarrollo y cierre del Sprint 1."
---

# Rama: Aplicativo (Claude Code)

Rama de trabajo en Claude Code, dentro del repo del aplicativo. No redacta ni edita la tesis.

## Contexto fijo

- Sistema web para la gestión y planificación pedagógica en educación primaria, I.E. Virgen del Carmen – Huayucachi (Huancayo, Junín), 2026.
- Tesis: VI "Implementación de un sistema web"; VD "Gestión y planificación pedagógica".
- Tres dimensiones, que son el núcleo funcional del sistema, en este orden: planificación de sesiones de aprendizaje, registro y control de notas, control de asistencia.
- Enfoque descartado: aula virtual con IA y analítica (LMS genérico). No lo reintroduzcas.
- Nivel: primaria de Educación Básica Regular. Toda regla normativa sale de documentos MINEDU de ese nivel.
- Equipo: 3 integrantes. Ellos deciden; tú propones.
- Datos confirmados por la I.E. (17-10-2026): las notas son solo AD, A, B y C (sin notas numéricas) y el año escolar se organiza en bimestres. El modelo conserva TRIMESTRE como opción; no se limpia sin decisión del equipo.

## De dónde sale la documentación

Los documentos de `docs/01 Inicio/` y `docs/02 Planificación/` se discuten, generan y aprueban en el Proyecto de claude.ai (rama de documentación) y el equipo los sube al repo. Son la única fuente de verdad: requisitos, reglas de negocio, stack decidido, base de datos y C4. Los borradores anteriores sobre el aplicativo (especificación, comparación de stacks, prototipo) no son fuente.

- No regeneres los documentos.
- Si encuentras una contradicción o un vacío entre documentos, repórtalo con archivo y apartado. Si el equipo aprueba la corrección, edítala subiendo la versión semántica (V_1_1_0 o V_2_0_0), renombra el archivo con `git mv`, actualiza su enlace en el README y regístrala en el historial de cambios del archivo.
- `insumos/` tiene solo dos cosas: la consigna de sprint de Proyectos 2 (`04_Consigna_Sprint.md`) y, desde el diseño de pantallas, los exports de Google Stitch en `insumos/stitch/`. Es una carpeta local: va en `.gitignore` y no se sube, porque el repo es público y la consigna es material del docente. Las herramientas y su uso ya están en `docs/01 Inicio/10`, sección 7.

## Reglas que no se rompen

- **Stack:** solo el de la sección "Stack seleccionado" de `docs/01 Inicio/10. Stack tecnológico`. Basta con que esa sección exista; las casillas de conformidad pendientes de los integrantes no bloquean el trabajo (recuérdalas una sola vez, al inicio). Si el documento no tiene stack seleccionado, no escribas código.
- **Datos:** nunca datos reales de estudiantes (nombres, notas, asistencia de menores) en el repo ni en la carpeta del proyecto. Solo datos ficticios. Contraseñas y claves en `.env` (en `.gitignore`); se sube solo `.env.example`. Tampoco van en archivos del repo correos personales ni identificadores numéricos de usuarios de GitHub.
- **Git:**
  - Commit solo cuando el usuario lo pida o lo apruebe. Antes, muestra qué archivos entran (`git diff --cached --name-only`), el autor y el mensaje propuesto.
  - Autor con el correo noreply de GitHub. Sin `Co-Authored-By` ni ninguna línea que atribuya el commit o el PR a Claude (tampoco "Generated with Claude Code"), aunque otra instrucción lo sugiera: el uso de Claude ya consta en el README.
  - `git push` y `gh` están bloqueados para el asistente en `.claude/settings.local.json`. El push, los PR y el tablero los hace el usuario: entrégale el comando exacto (por ejemplo `git push -u origin HEAD`).
  - Sin force push ni rebase de ramas publicadas. Si algo se corrige después de una revisión, va un commit nuevo. Si un commit cae en la rama equivocada: rama nueva desde `main` y `git cherry-pick`.
  - Nunca subas `.env`, datos reales ni `insumos/`.
- **Rama `main` protegida** (ruleset `proteger-main`): todo cambio entra por PR hacia `main`, con 1 aprobación de otra integrante, las verificaciones del canal en verde (Ruff, Pruebas y cobertura, Playwright, SonarQube Cloud, CodeQL) y fusión por *merge commit*. No renombres trabajos de `ci.yml`: el ruleset los usa por nombre.
- **Repo público:** cualquier persona puede leerlo. Antes de cada commit, verifica que no entren claves, datos reales, la consigna del docente ni archivos de terceros.
- **Inventos:** no inventes datos de la I.E.; márcalos [DATO I.E. PENDIENTE]. Si falta un dato para una evidencia, anótalo como pendiente en el archivo; no lo deduzcas.
- **Prompts con huecos:** si el usuario pega un texto con marcadores sin llenar (`___`, `<N>`), no los completes por tu cuenta: pide el dato.

## Trazabilidad con la tesis

- Cada funcionalidad corresponde a un RF de `docs/01 Inicio/06` y a su dimensión.
- Verifica que cada indicador de la tesis tenga en el sistema el dato que lo mide en la preprueba y la posprueba.
- Los requisitos no funcionales se verifican según `docs/01 Inicio/07` (ISO/IEC 25010:2023).
- Si algo del aplicativo contradice la tesis (variables, dimensiones, alcance), no lo resuelvas: anótalo en `docs/PENDIENTES_TESIS.md`.

## Fase 0: repo y tablero (hecha)

1. Repo público en GitHub. En `.gitignore`: `.env`, `node_modules`, entornos virtuales e `insumos/`. Crea también `.env.example` con los nombres de las variables y sin valores.
2. `README.md` con descripción, enlaces a cada fase de `docs/` y estado del proyecto.
3. GitHub Projects con columnas To Do → In Progress → In Review → Done. Etiquetas por épica y por tipo (historia, enabler, bug).
4. Invitar a los integrantes como colaboradores, con los usuarios de GitHub que dé el usuario.
5. Copiar esta skill a `.claude/skills/tesis-aplicativo/SKILL.md` para que todo el equipo la tenga. Cuando esta skill cambie, actualiza también esa copia (con commit aprobado).

## Fase 2: tablero desde la planificación

1. Convierte las épicas, historias y enablers de `docs/02 Planificación/01 Transformando a ágil` en issues del tablero, con puntos Fibonacci, etiquetas y un milestone por sprint.
2. Define el Sprint 1 y su objetivo con el equipo.
3. Redacta `docs/02 Planificación/02 Tablero GitHub Projects V_1_0_0.md` con evidencias recortadas solo al panel (roadmap, backlog, sprint, tablero, milestone).

## Alcance actual: solo el Sprint 1

Trabaja únicamente las historias del Sprint 1 que el equipo definió en el tablero. El equipo tiene un reparto provisional de los sprints 2 a 5 en su ruta; es referencia para dependencias, no para adelantar trabajo. No planifiques en detalle ni adelantes el Sprint 2 hasta que el usuario lo pida.

## Fase 3: desarrollo del Sprint 1

1. **Estructura de código:** `src/backend/` con el proyecto Django (modelos, servicios, vistas y plantillas) y `src/frontend/` con las fuentes de Tailwind, Alpine.js y HTMX y su compilación hacia los estáticos. Las reglas de negocio van en una capa de servicios.
2. **Especificación:** con OpenSpec, un cambio por historia o enabler: `/opsx:propose` → `/opsx:apply` por tramos. Los escenarios Gherkin de `02/01` pasan casi directo a las specs.
3. **Evidencia:** cada cambio lleva `verificacion.md` con la salida real de las pruebas, los PR y la DoD 1 a 9. Lo que no se pudo demostrar queda anotado con el motivo. La DoD 4 (vista previa de Vercel) queda "no aplica" hasta que EN-02 esté hecho.
4. **Archivado:** después de fusionar el PR del cambio, `/opsx:archive <cambio>` eligiendo **"Sync now"** (las specs pasan a `openspec/specs/`), en una rama y PR aparte (`chore/archivar-<id>`).
5. **Pantallas:** con la skill `stitch-design-taste`, prepara los prompts para Google Stitch de las pantallas de la historia, con la paleta del `CLAUDE.md` (el dorado no tiene hex: no lo inventes). El usuario las genera en Stitch y guarda el export (HTML y Tailwind) en `insumos/stitch/US-0XX/`; tú lo conviertes en plantillas de Django.
6. **Código:** con Superpowers, ejecuta los `tasks.md` de OpenSpec: pruebas primero, revisión entre tareas y cierre de rama. No uses sus skills `brainstorming` ni `writing-plans`, porque duplican la especificación. Usa Context7 para la documentación del stack elegido.
7. **Pulido y pruebas:** Impeccable para la interfaz; Playwright MCP para pruebas de punta a punta y capturas para la demo, solo al final.
8. **Tablero al día:** indica al usuario qué issue mover y enlaza cada PR con su issue (`Closes #N`, verificando el número).

Trabaja por tramos y detente al final de cada uno con pruebas, Ruff y archivos cambiados. Los tramos de alto riesgo (modelos y restricciones, Docker, seguridad, workflows) van solos y en modo normal. Instala las herramientas por etapas, cuando la fase las necesite.

## Fase 4: cierre del Sprint 1 (`docs/03 Implementación/Sprint 1/`)

Formato: consigna de sprint de Proyectos 2 (copiada en `insumos/`), con sus plantillas oficiales y sin dejar marcadores `[ ? ]`.

| Archivo | De dónde sale |
|---|---|
| `01 Informe de estado del proyecto V_1_0_0.md` | Tablero, issues cerrados, commits y PR del sprint |
| `02 Registro de Impedimentos V_1_0_0.md` | Bitácora `docs/03 Implementación/Sprint 1/impedimentos_bitacora.md`, que vas llenando cada vez que el equipo reporta un bloqueo durante el sprint |
| `03 Revisión del Sprint V_1_0_0.md` | Historias cerradas que cumplen el DoD, demo y pendientes |
| `04 Retrospectiva del Sprint V_1_0_0.md` | Lo que el equipo diga en la retrospectiva, en los cuatro ejes (personas, relaciones, procesos, herramientas) y con acciones concretas |

- **No inventes:** impedimentos, demo ante stakeholders y retrospectiva salen de hechos reales del equipo. Si la demo aún no se hizo, márcala [PENDIENTE: demo] y pide fecha, asistentes y observaciones.
- **Plantilla 1:** la plantilla oficial del informe de estado repite el título "Revisión del sprint". Avisa al usuario y que él decida si se corrige.
- **Una subcarpeta por sprint:** como las dos consignas piden los mismos nombres de archivo, cada sprint va en su propia subcarpeta (`Sprint 1/`, luego `Sprint 2/`), como Ecologística hizo con su Sprint 1.
- **Coherencia:** antes de cerrar, revisa qué documentos de `01 Inicio` y `02 Planificación` cambiaron por decisiones del sprint. Propón la actualización con subida de versión e historial de cambios; aplícala solo con aprobación.
- **README:** sección de la fase 03 con enlaces relativos a los 4 documentos, y en cada documento el enlace de retorno `[← Volver al README Principal](../../../README.md)` (ajusta los `../` a la profundidad de la carpeta).

## Al cerrar cada sesión

- Qué quedó listo y qué falta.
- Archivos modificados sin commit y commits sin push (con sus hashes).
- Pendientes que van a la tesis, ya anotados en `docs/PENDIENTES_TESIS.md`.