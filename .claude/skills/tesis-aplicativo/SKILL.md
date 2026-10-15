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

## De dónde sale la documentación

Los documentos de `docs/01 Inicio/` y `docs/02 Planificación/` se discuten, generan y aprueban en el Proyecto de claude.ai (rama de documentación) y el equipo los sube al repo. Son la única fuente de verdad: requisitos, reglas de negocio, stack decidido, base de datos y C4. Los borradores anteriores sobre el aplicativo (especificación, comparación de stacks, prototipo) no son fuente.

- No regeneres los documentos.
- Si encuentras una contradicción o un vacío entre documentos, repórtalo con archivo y apartado. Si el equipo aprueba la corrección, edítala subiendo la versión semántica (V_1_1_0 o V_2_0_0) y regístrala en el historial de cambios del archivo.
- `insumos/` tiene solo dos cosas: la consigna de sprint de Proyectos 2 (`04_Consigna_Sprint.md`) y, desde el diseño de pantallas, los exports de Google Stitch en `insumos/stitch/`. Es una carpeta local: va en `.gitignore` y no se sube, porque el repo es público y la consigna es material del docente. Las herramientas y su uso ya están en `docs/01 Inicio/10`, sección 7.

## Reglas que no se rompen

- **Stack:** solo el de la sección "Stack seleccionado" de `docs/01 Inicio/10. Stack tecnológico`. Basta con que esa sección exista; las casillas de conformidad pendientes de los integrantes no bloquean el trabajo (recuérdalas una sola vez, al inicio). Si el documento no tiene stack seleccionado, no escribas código.
- **Datos:** nunca datos reales de estudiantes (nombres, notas, asistencia de menores) en el repo ni en la carpeta del proyecto. Solo datos ficticios. Contraseñas y claves en `.env` (en `.gitignore`); se sube solo `.env.example`.
- **Git:**
  - Commit solo cuando el usuario lo pida o lo apruebe. Antes, muestra qué archivos entran y propone el mensaje.
  - Push solo con confirmación explícita.
  - Nunca subas `.env`, datos reales ni `insumos/`.
- **Repo público:** cualquier persona puede leerlo. Antes de cada commit, verifica que no entren claves, datos reales, la consigna del docente ni archivos de terceros.
- **Inventos:** no inventes datos de la I.E.; márcalos [DATO I.E. PENDIENTE].

## Trazabilidad con la tesis

- Cada funcionalidad corresponde a un RF de `docs/01 Inicio/06` y a su dimensión.
- Verifica que cada indicador de la tesis tenga en el sistema el dato que lo mide en la preprueba y la posprueba.
- Los requisitos no funcionales se verifican según `docs/01 Inicio/07` (ISO/IEC 25010:2023).
- Si algo del aplicativo contradice la tesis (variables, dimensiones, alcance), no lo resuelvas: anótalo en `docs/PENDIENTES_TESIS.md`.

## Fase 0: repo y tablero

1. Repo público en GitHub. En `.gitignore`: `.env`, `node_modules`, entornos virtuales e `insumos/`. Crea también `.env.example` con los nombres de las variables y sin valores.
2. `README.md` con descripción, enlaces a cada fase de `docs/` y estado del proyecto.
3. GitHub Projects con columnas To Do → In Progress → In Review → Done. Etiquetas por épica y por tipo (historia, enabler, bug).
4. Invitar a los integrantes como colaboradores, con los usuarios de GitHub que dé el usuario.
5. Copiar esta skill a `.claude/skills/tesis-aplicativo/SKILL.md` para que todo el equipo la tenga.

Para usar `gh`, pide permiso en cada comando.

## Fase 2: tablero desde la planificación

1. Convierte las épicas, historias y enablers de `docs/02 Planificación/01 Transformando a ágil` en issues del tablero, con puntos Fibonacci, etiquetas y un milestone por sprint.
2. Define el Sprint 1 y su objetivo con el equipo.
3. Redacta `docs/02 Planificación/02 Tablero GitHub Projects V_1_0_0.md` con evidencias recortadas solo al panel (roadmap, backlog, sprint, tablero, milestone).

## Alcance actual: solo el Sprint 1

Trabaja únicamente las historias del Sprint 1 que el equipo definió en el tablero. No planifiques ni adelantes el Sprint 2 hasta que el usuario lo pida.

## Fase 3: desarrollo del Sprint 1

1. **Estructura de código:** la consigna pide carpetas independientes `src/frontend/` y `src/backend/`. Con el stack elegido (Django con plantillas, HTMX y Tailwind) no hay una aplicación de frontend aparte, así que propón al equipo la división antes de crearla; por ejemplo: `src/backend/` con el proyecto Django (modelos, servicios, vistas y plantillas) y `src/frontend/` con las fuentes de Tailwind, Alpine.js y HTMX y su compilación hacia los estáticos. Más `.gitignore` en la raíz con dependencias (`node_modules`, entornos virtuales), temporales, compilados y `.env`.
2. **Especificación:** con OpenSpec, convierte en `openspec/specs` solo los RF de las historias del Sprint 1 (los escenarios Gherkin pasan casi directo). Un cambio por historia: `/opsx:propose`.
3. **Pantallas:** con la skill `stitch-design-taste`, prepara los prompts para Google Stitch de las pantallas del Sprint 1. El usuario las genera en Stitch y guarda el export (HTML y Tailwind) en `insumos/stitch/`; tú lo conviertes en plantillas de Django.
4. **Código:** con Superpowers, ejecuta los `tasks.md` de OpenSpec: pruebas primero, revisión entre tareas y cierre de rama. No uses sus skills `brainstorming` ni `writing-plans`, porque duplican la especificación. Usa Context7 para la documentación del stack elegido.
5. **Pulido y pruebas:** Impeccable para la interfaz; Playwright MCP para pruebas de punta a punta y capturas para la demo.
6. **Tablero al día:** mueve los issues según avancen y enlaza cada commit o PR con su issue.

Instala las herramientas por etapas, cuando la fase las necesite.

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
- **Coherencia:** antes de cerrar, revisa qué documentos de `01 Inicio` y `02 Planificación` cambiaron por decisiones del sprint. Propón la actualización con subida de versión (V_1_1_0 o V_2_0_0) e historial de cambios; aplícala solo con aprobación.
- **README:** sección de la fase 03 con enlaces relativos a los 4 documentos, y en cada documento el enlace de retorno `[← Volver al README Principal](../../../README.md)` (ajusta los `../` a la profundidad de la carpeta).

## Al cerrar cada sesión

- Qué quedó listo y qué falta.
- Archivos modificados sin commit.
- Pendientes que van a la tesis, ya anotados en `docs/PENDIENTES_TESIS.md`.