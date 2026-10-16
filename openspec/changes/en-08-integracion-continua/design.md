# Design: EN-08 – Canal de integración continua

## Context

Motivación y alcance en `proposal.md`; comportamiento esperado en `specs/integracion-continua/spec.md`.

Estado actual (rama de EN-01, sobre la que sale esta):
- No existe `.github/`. Python 3.13 con uv (`uv.lock`), Django 5.2, pytest-django, pytest-cov y Ruff configurados en `pyproject.toml` (reglas `E W F I B UP DJ S`). Las pruebas viven en `src/backend/<app>/tests/` y necesitan PostgreSQL. La cobertura se mide sobre `src/backend` sin migraciones ni pruebas, y hoy no tiene umbral.
- `config/settings.py` exige `DJANGO_SECRET_KEY` y `DATABASE_URL` (falla con `ImproperlyConfigured`) y lee `.env` solo si existe.
- Frontend: Tailwind v4, HTMX y Alpine se compilan con `npm run build` en `src/frontend/` (con `package-lock.json`) hacia `src/backend/static/dist/`, que no se versiona. Compose usa `postgres:17` y `node:24-slim`.
- Repositorio público `jmartinez278/CarpetaDocente`: CodeQL y el plan gratuito de SonarQube Cloud no cuestan.

Restricciones:
- El token de SonarQube Cloud vive solo en los secretos de GitHub Actions (documento 02/01, manejo de claves). El asistente no lo escribe ni lo pide.
- Los workflows se disparan con `pull_request` hacia `main` y con `push` a `main`, por decisión del usuario. El push deja analizada `main` para que SonarQube Cloud compare el código nuevo de cada PR.
- Sin `gh` ni push desde el asistente: todo lo que se configura en GitHub o en SonarQube Cloud lo hace el equipo, con la guía del README. El *ruleset* de `main` es el paso B10 de la ruta del equipo y no se convierte en código.
- Plan gratuito de SonarQube Cloud: solo se puede usar la puerta **Sonar way**, que es de solo lectura; las puertas propias son de los planes Team y Enterprise (consultado en Context7, documentación de SonarQube Cloud).

## Goals / Non-Goals

**Goals:**
- Que la DoD 1, 2 y 5 se compruebe sola en cada PR, y que GitHub impida fusionar si algo falla.
- Que lo que revisa el canal se pueda reproducir en la laptop con los mismos comandos y umbrales.
- Dejar a US-001 lista la infraestructura de pruebas de punta a punta.

**Non-Goals:**
- Analizar ramas distintas de `main` ni PR hacia otras ramas.
- Medir la cobertura de las pruebas de punta a punta: la DoD 1 habla de pruebas unitarias.
- Probar en varios navegadores o tamaños de pantalla (EN-07).
- Desplegar (EN-02).

## Decisions

### D1. Un workflow con cuatro trabajos independientes

`.github/workflows/ci.yml`, con `name: CI` y estos trabajos. El nombre de cada trabajo es la verificación que pedirá el *ruleset* (D12), así que no se cambia sin actualizar el *ruleset*:

| Trabajo (`name:`) | Qué hace | Depende de |
|---|---|---|
| `Ruff` | `ruff check` y `ruff format --check` | — |
| `Pruebas y cobertura` | pytest sin `e2e` contra PostgreSQL, con cobertura ≥ 80 %, y sube `coverage.xml` como artefacto | — |
| `Playwright` | compila el CSS y corre `pytest -m e2e` en Chromium contra PostgreSQL | — |
| `SonarQube Cloud` | descarga `coverage.xml` y ejecuta el análisis | `Pruebas y cobertura` |

- Trabajos separados para que el PR muestre **qué** falló (spec: una verificación por herramienta) y para que corran en paralelo.
- **Alternativa descartada:** un solo trabajo con todos los pasos. Es más simple, pero un fallo de Ruff ocultaría el resultado de las pruebas, y en el PR solo se vería "CI falló".
- **Alternativa descartada:** un workflow por herramienta. Repite en cada archivo la instalación de uv y de PostgreSQL sin ganar nada.

### D2. Disparador, concurrencia y permisos

- `on: pull_request: branches: [main]`, con los tipos por defecto (`opened`, `synchronize`, `reopened`), que cubren el escenario "nuevo commit".
- `on: push: branches: [main]`: cada fusión vuelve a correr los cuatro trabajos sobre `main`. Así SonarQube Cloud actualiza el análisis de la rama principal, que es la referencia del código nuevo de los PR siguientes, y se confirma que `main` sigue en verde.
- `concurrency: group: ci-${{ github.event.pull_request.number || github.ref }}`, porque en un push no hay número de PR. `cancel-in-progress: ${{ github.event_name == 'pull_request' }}`: un commit nuevo cancela la ejecución anterior del mismo PR, pero una ejecución de `main` nunca cancela otra.
- `permissions: contents: read` a nivel del workflow; ningún trabajo necesita escribir. CodeQL no usa este workflow (D8).
- `actions/checkout` con `persist-credentials: false`. `SonarQube Cloud` usa `fetch-depth: 0`, porque SonarQube necesita el historial para saber qué código es nuevo.
- `timeout-minutes` en cada trabajo (15 en general), para que un proceso colgado no gaste minutos.

### D3. Python con uv, igual que en local

- `astral-sh/setup-uv` con caché, y `uv sync --locked`, que falla si `uv.lock` no coincide con `pyproject.toml`. La versión de Python sale de `.python-version` (3.13), como en la laptop.
- Las herramientas se llaman con `uv run`, así que Ruff, pytest y Playwright usan exactamente las versiones de `uv.lock`.
- **Alternativa descartada:** `actions/setup-python` + `pip install`. Ignora `uv.lock` y abre la puerta a versiones distintas de las locales.

### D4. PostgreSQL de servicio, temporal y sin contraseña

- `services: postgres: image: postgres:17`, la misma versión que el compose (D8 de EN-01; se iguala a Neon en EN-02). Lleva `POSTGRES_HOST_AUTH_METHOD: trust`, `POSTGRES_DB: carpetadocente`, un *health check* con `pg_isready` y el puerto 5432.
- `trust` evita escribir una contraseña en el YAML, por ficticia que fuera. El contenedor vive solo dentro del ejecutor de GitHub y se destruye al terminar el trabajo.
- pytest-django crea y borra su propia base de prueba (`test_carpetadocente`). Los únicos datos son los ficticios que crean las pruebas; EN-06 traerá el juego de datos ficticios.
- Lo usan `Pruebas y cobertura` y `Playwright`.

### D5. Variables de entorno en el canal

- `DATABASE_URL=postgres://postgres@localhost:5432/carpetadocente`, sin contraseña por D4. `DJANGO_DEBUG=False` y `DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1`.
- `DJANGO_SECRET_KEY` se genera en cada trabajo con `secrets.token_urlsafe(50)`: se enmascara con `::add-mask::` y se pasa a `$GITHUB_ENV`. No es un secreto de GitHub ni aparece en el repositorio, y cambia en cada ejecución.
- No hay `.env` en el ejecutor. `settings.py` ya tolera su ausencia y toma las variables del entorno.
- `.env.example` no cambia: `SONAR_TOKEN` no es una variable de la aplicación.

### D6. Cobertura: 80 % en `pyproject.toml`, el mismo umbral en local y en CI

- `[tool.coverage.report] fail_under = 80`. pytest-cov lo lee, así que `uv run pytest --cov` falla en la laptop igual que en CI (spec: "Mismo umbral en local").
- `[tool.coverage.run] relative_files = true`. Sin esto, `coverage.xml` guarda rutas absolutas del ejecutor y SonarQube Cloud no las encuentra: mostraría 0 % (documentación de SonarQube Cloud para Python).
- Cobertura de **líneas**, como en EN-01. La DoD habla de "cobertura de pruebas", y cobertura de líneas es lo que reporta pytest-cov por defecto. **Alternativa:** `branch = true`, más estricta; se puede activar después sin cambiar la spec.
- En CI: `uv run pytest --cov --cov-report=term-missing --cov-report=xml`. `coverage.xml` se sube como artefacto de corta duración (1 día) para el trabajo `SonarQube Cloud`.
- Dos medidas que se complementan: el canal exige el 80 % del **total**, y SonarQube Cloud exige el 80 % del **código nuevo** del PR (Sonar way). Esta segunda es la que corresponde a la DoD 1 ("del código del cambio").

### D7. Ruff con anotaciones en el PR

- `uv run ruff check --output-format=github .` muestra cada problema como anotación en la línea del PR. Después, `uv run ruff format --check .`.
- Mismas reglas que en local, porque las lee de `pyproject.toml`. No se agregan reglas en este cambio.
- **Alternativa descartada:** `astral-sh/ruff-action`. Trae su propia versión de Ruff, que podría diferir de la de `uv.lock`.

### D8. CodeQL: configuración por defecto de GitHub, sin workflow propio

- Se activa en *Settings → Code security → Code scanning → CodeQL analysis → Set up → Default*, con el conjunto de consultas **Default**.
- GitHub detecta los lenguajes (Python, JavaScript del script de `src/frontend/` y los workflows de Actions) y analiza los PR hacia `main`, los push a `main` y una vez por semana. Esto lo gestiona GitHub, no `ci.yml`.
- Por qué la configuración por defecto:
  - No hace falta personalizar nada: Python no se compila, y la consulta de inyección SQL (`py/sql-injection`, severidad alta) ya está en el conjunto Default. Con eso se cumple el escenario de la spec.
  - CodeQL incluye la consulta `actions/unnecessary-use-of-advanced-config`, que marca un workflow avanzado sin ajustes propios y recomienda la configuración por defecto (consultado en Context7). Un `codeql.yml` copiado de la plantilla generaría esa alerta.
  - GitHub mantiene las versiones de la acción y de las consultas.
- **Alternativa descartada:** un workflow propio (`codeql.yml`). Su ventaja es que queda versionado en el repositorio, pero exige mantenerlo, choca con la configuración por defecto (no pueden estar activas las dos) y no aporta ajustes. Se puede volver a él si un día hace falta un conjunto de consultas propio o excluir rutas.
- Como la configuración no queda en un archivo, el README la documenta paso a paso y `verificacion.md` guarda la evidencia (captura de la configuración y de la alerta de prueba).
- El bloqueo de la fusión lo pone el *ruleset* (D12) con la regla *Require code scanning results*: herramienta CodeQL, alertas de seguridad "High or higher" y alertas "Errors".

### D9. SonarQube Cloud: análisis en CI, con la cobertura de `coverage.xml`

- El análisis automático de SonarQube Cloud no importa cobertura de Python. Por eso se usa el **análisis en CI** y el automático se apaga en *Administration → Analysis Method* (documentación de SonarQube Cloud). Si quedan los dos activos, el análisis en CI falla.
- Acción `SonarSource/sonarqube-scan-action`, la que la documentación muestra hoy en su v7. Va fijada por SHA (D11) con `env: SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}`.
- `sonar-project.properties` en la raíz:
  - `sonar.organization` y `sonar.projectKey`: identificadores públicos que SonarQube Cloud asigna al importar el repositorio. **No se inventan**: los da el equipo después de importarlo (tarea 1.x).
  - `sonar.sources=src`, `sonar.tests=src/backend`, `sonar.test.inclusions=**/tests/**` y `sonar.exclusions=**/migrations/**,**/tests/**,**/static/dist/**,**/node_modules/**`.
  - `sonar.python.version=3.13` y `sonar.python.coverage.reportPaths=coverage.xml`.
- **Sin `sonar.qualitygate.wait`.** SonarQube Cloud publica la puerta de calidad en el PR como la verificación `SonarCloud Code Analysis`, por medio de su aplicación de GitHub, y esa verificación es la que exige el *ruleset*. La documentación desaconseja usar la espera para informar la puerta en un PR: alarga el trabajo y duplica la señal. Así, el trabajo `SonarQube Cloud` solo falla si el análisis no se pudo subir (por ejemplo, si falta el token).
- Condición `if: github.event_name == 'push' || github.event.pull_request.head.repo.full_name == github.repository`: siempre corre en push a `main`, y se salta en los PR desde *forks*, que no reciben secretos. El equipo trabaja en el mismo repositorio, así que en la práctica siempre corre.
- **Puerta de calidad: Sonar way.** Es la única disponible en el plan gratuito. Pide en el código nuevo: cobertura de 80 % o más, duplicación de 3 % o menos, calificaciones A en fiabilidad, seguridad y mantenibilidad, y todos los *security hotspots* revisados. Es **más estricta** que el texto de la DoD ("sin críticas ni altas"): bloquea también problemas menores nuevos. Se anota en "Pendientes de documentación".

### D10. Playwright entra en EN-08, con una prueba de punta a punta de la página inicial

**Decisión:** EN-08 deja la infraestructura y una primera prueba. Las pruebas de cada pantalla llegan con su historia, desde US-001.

- Por qué ahora y no con las primeras pantallas:
  - EN-08 nombra Playwright en su redacción y en su título, y la DoD 5 lo exige "en GitHub Actions (EN-08)".
  - Si se deja para US-001, esa historia mezcla tres cosas (pantalla de login, autenticación y la infraestructura del navegador en CI), y su PR crece.
  - La página inicial ya existe y alcanza para probar la cadena completa: compilación del CSS, servidor en vivo, navegador y PostgreSQL.
- Dependencia de desarrollo `pytest-playwright`, que trae `playwright`.
- Marcador `e2e` registrado en `[tool.pytest]` (`markers`) y `addopts = ["-m", "not e2e"]`. `uv run pytest` no las ejecuta, y `uv run pytest -m e2e` sí, porque el último `-m` manda. Spec: "Pruebas de punta a punta separadas en local".
- Prueba `src/backend/cuentas/tests/test_inicio_e2e.py` (`pytestmark = pytest.mark.e2e`), con los *fixtures* `live_server` (pytest-django) y `page` (pytest-playwright). Comprueba que:
  - se ven el nombre y las tres dimensiones en orden;
  - `app.css` responde 200;
  - `typeof htmx` y `typeof Alpine` no son `undefined`.

  Complementa a `test_inicio.py`, que solo mira el HTML.
- Trabajo `Playwright`:
  1. `actions/setup-node` con Node 24 (igual que el compose) y caché de `src/frontend/package-lock.json`.
  2. `npm ci && npm run build` en `src/frontend/`.
  3. `uv run playwright install --with-deps chromium`.
  4. `uv run pytest -m e2e --browser chromium --tracing retain-on-failure`.
  5. Si falla, sube `test-results/` como artefacto para ver la traza.
- `live_server` sirve los estáticos cuando `django.contrib.staticfiles` está instalado (pytest-django). Se confirma en Context7 al implementar.
- Playwright síncrono corre un bucle de eventos en el hilo de la prueba, y Django puede rechazar el acceso a la base desde ahí (`SynchronousOnlyOperation`). Se activa `DJANGO_ALLOW_ASYNC_UNSAFE=true` **solo** en el trabajo `Playwright` y en el comando local de `e2e` documentado en el README, previa confirmación en Context7.
- **Alternativa descartada:** postergar Playwright a US-001 (ver arriba).
- **Alternativa descartada:** compilar el CSS en un trabajo aparte y pasarlo como artefacto. Agrega un trabajo sin ganar tiempo real.

### D11. Acciones fijadas y revisión de los workflows

- Las acciones de terceros (`astral-sh/setup-uv`, `SonarSource/sonarqube-scan-action`) se fijan por SHA completo, con un comentario de la versión. Las de GitHub (`actions/*`) van por versión mayor. En un repositorio público, una etiqueta movida en una acción de terceros ejecutaría código ajeno con acceso a `SONAR_TOKEN`.
- Los SHA y las versiones vigentes se confirman al implementar (`git ls-remote`, Context7), no se toman de memoria.
- Revisión local antes del commit, sin agregar dependencias al proyecto:
  - `uvx --from actionlint-py actionlint` (sintaxis y expresiones);
  - `uvx zizmor .github/workflows/` (permisos, credenciales persistidas, acciones sin fijar, inyección en expresiones).

### D12. *Ruleset* de `main`: tarea del equipo documentada (paso B10), no código

El *ruleset* no se versiona ni se crea con scripts: lo configura el equipo en GitHub como paso B10 de su ruta. Este cambio solo deja la guía en el README: *Settings → Rules → Rulesets → New branch ruleset*, con destino la rama por defecto y estado *Active*.

Lo que EN-08 necesita (spec "Fusión solo con verificaciones en verde"):

| Regla | Valor |
|---|---|
| *Require status checks to pass* | `Ruff`, `Pruebas y cobertura`, `Playwright`, `SonarQube Cloud`, `SonarCloud Code Analysis`; *Require branches to be up to date* |
| *Require code scanning results* | CodeQL: *Security alerts* "High or higher", *Alerts* "Errors" |

Lo que el equipo agrega en el mismo paso B10, fuera del alcance de EN-08:

| Regla | Valor |
|---|---|
| *Require a pull request before merging* | 1 aprobación; *Dismiss stale approvals*; *Require approval of the most recent push* (DoD 3: aprueba otra integrante) |
| *Block force pushes* y *Restrict deletions* | Activas |

- GitHub solo deja elegir verificaciones que ya corrieron en el repositorio, así que el *ruleset* se crea **después** de la primera ejecución del canal en el PR de EN-08 (orden en D13).
- Se recomienda no tener lista de excepciones (*bypass list*), para que ni el administrador fusione sin cumplir. Lo decide el equipo en el paso B10.

### D13. Orden de puesta en marcha

1. Equipo: importar el repositorio en SonarQube Cloud, apagar el análisis automático y comunicar la organización y la clave del proyecto. Crear el token en SonarQube Cloud y pegarlo como secreto `SONAR_TOKEN` en GitHub.
2. Equipo: activar la configuración por defecto de CodeQL.
3. Asistente (tras aprobación): workflow, `sonar-project.properties`, configuración de pytest y cobertura, prueba de punta a punta, README y revisión local.
4. Equipo: cuando EN-01 se fusione, integrar `main` en esta rama (`git merge main`, sin rebase ni force push), hacer push y abrir el PR de EN-08 hacia `main`. Es la primera ejecución del canal.
5. Equipo: crear el *ruleset* (D12, paso B10 de su ruta).
6. Equipo, con apoyo del asistente: PR de demostración (D14) para la evidencia de los escenarios en rojo.
7. Equipo: tras fusionar EN-08, el push a `main` ejecuta el canal por primera vez sobre la rama principal y deja su análisis en SonarQube Cloud.

### D14. Evidencia de los escenarios

| Escenario de EN-08 | Cómo se demuestra |
|---|---|
| Pull Request que cumple | El propio PR de EN-08, con todo en verde |
| Prueba fallida o cobertura insuficiente | Rama `demo/EN-08-rojo` (no se fusiona): una prueba que falla y una función sin pruebas que baja el total de 80 % |
| Alerta crítica de seguridad | En la misma rama de demostración, una vista con `cursor.execute(f"... {request.GET['q']}")` |
| Puerta de calidad no superada | La misma rama: código nuevo sin cubrir |
| Canal sin claves reales | Revisión de `ci.yml` y del registro de ejecución: base `trust` temporal, clave generada y ningún secreto fuera de `SONAR_TOKEN` |

- La rama de demostración se cierra sin fusionar y se borra después de guardar las capturas en `openspec/changes/en-08-integracion-continua/verificacion.md`.
- Las alertas de CodeQL de un PR cerrado no llegan a `main`.
- El código de demostración no tiene datos reales y no se fusiona.

### D15. Cierre según la DoD

- 1 (cobertura) y 2 (análisis): los verifica el propio canal en el PR de EN-08. EN-08 casi no agrega código Python: solo la prueba de punta a punta.
- 3: aprobación de otra integrante, que el equipo exige en el *ruleset* (paso B10, fuera de EN-08).
- 4 (vista previa de Vercel): no aplica hasta EN-02; se indica en el PR.
- 5: la prueba de punta a punta de la página inicial corre en el canal.
- 7: no hay pantallas nuevas.
- 8: sin datos reales, ni en el canal ni en la demostración.
- 9: README ("Integración continua"), este cambio en OpenSpec y docstrings en la prueba nueva. El catálogo de rutas no cambia.

## Pendientes de documentación (para el equipo)

No se editan en este cambio. Si el equipo aprueba, se proponen aparte con subida de versión:

- **Documento 07, RNF-018 (medida) frente al documento 02/01, DoD 2:** RNF-018 pide "0 hallazgos críticos" y la DoD pide "sin vulnerabilidades críticas ni altas". Es una inconsistencia entre documentos y no bloquea este cambio: el canal sigue la DoD, que es la más estricta, y bloquea las alertas altas y críticas. Convendría alinear RNF-018 con la DoD.
- **Documento 02/01, DoD 1 y 2 y escenario 4 de EN-08, frente a Sonar way:** el texto dice "cobertura menor a 80 % o un problema crítico o alto". La única puerta del plan gratuito, Sonar way, bloquea también cualquier error o vulnerabilidad nueva de menor severidad, la duplicación mayor a 3 % y los *hotspots* sin revisar. Convendría que el texto dijera "la puerta de calidad Sonar way".
- **Documento 02/01, sección 7, "Sobre los criterios 1 y 2":** conviene registrar que CodeQL usa la configuración por defecto de GitHub, sin workflow en el repositorio.

## Risks / Trade-offs

- [La configuración por defecto de CodeQL no queda versionada y un cambio en *Settings* no deja rastro en el repositorio] → El README la documenta, `verificacion.md` guarda la captura y el *ruleset* exige el resultado de CodeQL: si alguien lo apaga, ningún PR se puede fusionar.
- [Sonar way es más estricta que la DoD y puede bloquear un PR por un problema menor] → Se acepta: es la única opción gratuita y el bloqueo apunta a código nuevo. Un falso positivo se marca como tal en SonarQube Cloud, con justificación. Se propone alinear el texto de la DoD.
- [El PR de EN-08 es el primero y `main` todavía no tiene análisis en SonarQube Cloud, así que ese PR no tiene referencia contra la cual comparar] → Se acepta para ese único PR. Desde su fusión, el push a `main` deja la referencia para todos los siguientes.
- [`DJANGO_ALLOW_ASYNC_UNSAFE` relaja una protección de Django] → Solo en el trabajo `Playwright` y en el comando local de `e2e`, nunca en `settings.py` ni en producción.
- [Instalar Chromium suma 1 o 2 minutos por PR] → Se acepta: es una vez por PR y corre en paralelo con los otros trabajos. Si crece, se cachean los navegadores.
- [El umbral de 80 % total puede bloquear un PR que no tocó la parte poco cubierta] → La cobertura actual de EN-01 se mide antes de activar el umbral (tarea 2.x). Si estuviera debajo, se reporta antes de seguir; no se baja el umbral.
- [Renombrar un trabajo de `ci.yml` rompe el *ruleset*, que queda esperando una verificación que ya no existe] → Se documenta en un comentario en `ci.yml` y en el README.
- [Esta rama contiene los commits de EN-01 hasta que EN-01 se fusione] → El PR se abre después de esa fusión, tras integrar `main` con merge.

## Migration Plan

- No hay datos ni producción afectados.
- Para volver atrás: revertir el commit de `ci.yml` y desactivar o borrar el *ruleset*. CodeQL se desactiva en *Settings*, y en SonarQube Cloud se puede volver al análisis automático.

## Open Questions

- **Organización y clave del proyecto en SonarQube Cloud:** se conocen al importar el repositorio (D13, paso 1).
