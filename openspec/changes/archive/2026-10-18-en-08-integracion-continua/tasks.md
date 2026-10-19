# Tasks

Ejecución con pruebas primero (TDD) donde hay comportamiento: la prueba se escribe y se ve fallar antes del código o la configuración. Antes de usar pytest-django, pytest-playwright, GitHub Actions, CodeQL o SonarQube Cloud, consultar Context7 o la documentación oficial vigente, no la memoria. El asistente nunca escribe, pide ni lee el token de SonarQube Cloud, no hace push y no usa `gh`. Lo marcado **(equipo)** lo hace una integrante en GitHub o en SonarQube Cloud.

## 1. Preparación fuera del repositorio (equipo)

- [x] 1.1 **(equipo)** Importar `jmartinez278/CarpetaDocente` en SonarQube Cloud (plan gratuito), apagar *Automatic Analysis* en *Administration → Analysis Method* y comunicar al asistente `sonar.organization` y `sonar.projectKey`, que son públicos. Verificar: *Analysis Method* muestra el análisis automático en OFF
- [x] 1.2 **(equipo)** Generar el token en SonarQube Cloud y pegarlo como secreto de repositorio `SONAR_TOKEN` en *Settings → Secrets and variables → Actions*. Verificar: la lista de secretos muestra `SONAR_TOKEN` (el valor no se comparte con nadie)
- [x] 1.3 **(equipo)** Activar CodeQL con la configuración por defecto (D8): *Settings → Code security → Code scanning → CodeQL analysis → Set up → Default*, con consultas *Default*. Verificar: la página muestra "Default setup" con Python entre los lenguajes y el primer análisis de `main` terminado

## 2. Cobertura con umbral de 80 %

- [x] 2.1 Con `db` levantado, medir la cobertura actual (`uv run pytest --cov`) antes de poner el umbral. Verificar: el total queda anotado en `verificacion.md`; si es menor que 80 %, detenerse y reportarlo al equipo, sin bajar el umbral
- [x] 2.2 Agregar `fail_under = 80` en `[tool.coverage.report]` y `relative_files = true` en `[tool.coverage.run]` de `pyproject.toml` (D6). Verificar en rojo: con el umbral puesto de forma temporal en 90, `uv run pytest --cov` falla por cobertura aunque las pruebas pasen (una sola prueba no baja de 80 %, porque al arrancar Django se importa casi todo el código; el rojo con 80 % se muestra en 6.4). Verificar en verde: con el umbral en 80, `uv run pytest --cov --cov-report=xml` pasa y `coverage.xml` no tiene rutas absolutas: `<source>src/backend</source>` y cada archivo relativo a esa carpeta
- [x] 2.3 Actualizar en el README la sección "3. Pruebas y calidad del código": el umbral de 80 % y que `coverage.xml` no se versiona (agregarlo a `.gitignore`). Verificar: `git status` no lista `coverage.xml` después de 2.2

## 3. Playwright y pruebas de punta a punta

- [x] 3.1 Consultar Context7 (pytest-playwright, `live_server` de pytest-django y su manejo de estáticos, `DJANGO_ALLOW_ASYNC_UNSAFE`) y agregar `pytest-playwright` al grupo `dev` con `uv add --dev pytest-playwright`. Verificar: `uv.lock` actualizado y `uv sync --locked` termina sin errores
- [x] 3.2 Registrar el marcador `e2e` en `[tool.pytest]` y agregar `addopts = ["-m", "not e2e"]` (D10). Verificar: `uv run pytest` ejecuta las mismas pruebas que antes y termina en verde sin navegadores instalados
- [x] 3.3 Prueba primero: `src/backend/cuentas/tests/test_inicio_e2e.py`, con docstring y `pytestmark = pytest.mark.e2e`. Comprueba el nombre y las tres dimensiones en orden, que `app.css` responde 200 y que `htmx` y `Alpine` están definidos en la página. Verificar en rojo: con `src/backend/static/dist/` vacío, `uv run playwright install chromium` y luego `uv run pytest -m e2e --browser chromium` falla por el CSS y los scripts ausentes
- [x] 3.4 Ajustar lo necesario según 3.1 (variable de entorno para Playwright síncrono, si hace falta) sin tocar `settings.py` para producción. Verificar en verde: `npm run build` en `src/frontend/` y luego `uv run pytest -m e2e --browser chromium` pasa
- [x] 3.5 Documentar en el README cómo correr las pruebas de punta a punta en la laptop: instalar Chromium una vez, compilar el CSS y el comando de 3.4. Verificar: los comandos del README, ejecutados tal cual, dan el resultado de 3.4

## 4. Workflow de integración continua

- [x] 4.1 Confirmar las versiones vigentes de `actions/checkout`, `actions/setup-node`, `actions/upload-artifact`, `actions/download-artifact`, `astral-sh/setup-uv` y `SonarSource/sonarqube-scan-action`, y el SHA completo de las dos de terceros, con `git ls-remote` y la documentación (D11). Verificar: versiones y SHA anotados en `verificacion.md` con la fecha de consulta
- [x] 4.2 Crear `.github/workflows/ci.yml` con los disparadores (`pull_request` hacia `main` y `push` a `main`), la concurrencia por PR o por rama, sin cancelar ejecuciones de `main`, y los permisos (D2), el servicio PostgreSQL (D4), las variables y la clave generada (D5), y los trabajos `Ruff` (D7) y `Pruebas y cobertura` (D6), que sube `coverage.xml` como artefacto. Incluir un comentario que advierta que los nombres de los trabajos los usa el *ruleset*. Verificar: `uvx --from actionlint-py actionlint` y `uvx zizmor .github/workflows/` sin hallazgos
- [x] 4.3 Agregar el trabajo `Playwright` (D10): Node 24 con caché, `npm ci && npm run build`, `playwright install --with-deps chromium`, `pytest -m e2e` con traza en caso de fallo y subida de `test-results/` si falla. Verificar: actionlint y zizmor sin hallazgos
- [x] 4.4 Crear `sonar-project.properties` (D9) con los identificadores de 1.1 y agregar el trabajo `SonarQube Cloud`: depende de `Pruebas y cobertura`, descarga `coverage.xml`, usa `fetch-depth: 0`, la acción fijada por SHA, `SONAR_TOKEN` desde `secrets` y la condición de D9 (siempre en push a `main`; se salta en PR desde *forks*). Verificar: actionlint y zizmor sin hallazgos, y `git grep -n -i "sonar_token\|token"` solo muestra la referencia `${{ secrets.SONAR_TOKEN }}` y textos de documentación
- [x] 4.5 Agregar al README la sección "Integración continua". Debe incluir: tabla de verificaciones (qué revisa cada una y cómo reproducirla en local), los pasos de 1.1 a 1.3, la guía del *ruleset* de D12 como tarea del equipo (paso B10), separando lo que exige EN-08 de lo que se agrega en ese paso, el aviso de no renombrar trabajos y que el token solo vive en los secretos de GitHub. Verificar: cada comando local de la tabla, ejecutado tal cual, termina en verde
- [x] 4.6 Revisión local completa antes del commit: `uv run ruff check .`, `uv run ruff format --check .`, `uv run pytest --cov` y `uv run pytest -m e2e --browser chromium`, más una revisión del diff contra la DoD 8 (sin datos reales) y contra claves en el repositorio. Verificar: todo en verde y salida pegada en `verificacion.md`

## 5. Commit (con aprobación)

- [x] 5.1 Mostrar al usuario los archivos que entran y el mensaje propuesto. Tras su aprobación explícita, hacer el commit con el correo noreply del autor y sin `Co-Authored-By`. Sin push. Verificar: `git log -1 --stat` coincide con lo aprobado y `git status` queda limpio
  - Evidencia: commits `afe0f63`, `28fba2c`, `2c0ee5c` y `2d1bba1` en `feature/EN-08-integracion-continua`, fusionados en `main` con el PR #52 (merge `de0c5b0`).

## 6. Puesta en marcha y evidencia de los escenarios

- [x] 6.1 Cuando EN-01 esté fusionado en `main`, y con aprobación del usuario, integrar `main` en esta rama con `git merge main` (sin rebase ni force push) y repetir 4.6. Verificar: `git log --oneline main..HEAD` solo muestra commits de EN-08
  - Hecho: merge de `main` en la rama (`4518e0b`), sin rebase ni force push.
  - Repetición de 4.6 el 17/10/2026: `ruff check`, `ruff format --check`, `pytest --cov` (87,10 %) y `pytest -m e2e --browser chromium` en verde. Salidas en `verificacion.md`, 6.1.
- [x] 6.2 **(equipo)** Hacer push y abrir el PR de EN-08 hacia `main`. Verificar: el PR muestra `Ruff`, `Pruebas y cobertura`, `Playwright`, `SonarQube Cloud`, `SonarCloud Code Analysis` y CodeQL en verde, y SonarQube Cloud muestra la cobertura del código nuevo (no 0 %). Escenario "Pull Request que cumple", en `verificacion.md`
  - Evidencia: PR #52 de EN-08 fusionado (merge `de0c5b0`); en ese PR, las 8 verificaciones en verde: `CodeQL / Analyze (javascript-typescript)`, `CodeQL / Analyze (python)`, `CodeQL`, `CI / Playwright`, `CI / Pruebas y cobertura`, `CI / Ruff`, `SonarCloud Code Analysis` y `CI / SonarQube Cloud`. Análisis de SonarQube Cloud en `main` sobre `de0c5b0` con cobertura de 83,3 %. Detalle en `verificacion.md`, 6.2.
- [x] 6.3 **(equipo, paso B10)** Crear el *ruleset* de `main` con la guía del README (D12), ahora que las verificaciones ya corrieron una vez. No se convierte en código. Verificar: GitHub muestra las verificaciones de EN-08 como obligatorias y la fusión bloqueada mientras falte una (se confirma en rojo en 6.5). Captura en `verificacion.md`
  - Evidencia: *ruleset* "proteger-main" activo, con 1 aprobación, fusión por *merge commit*, verificaciones requeridas y *code scanning*. La fusión bloqueada se confirmó en el PR de demostración (6.5).
  - Captura: consta en el documento de pruebas del equipo; no se copia al repositorio (`verificacion.md`, 6.3).
- [ ] 6.4 Preparar en local, con aprobación del usuario, la rama `demo/EN-08-rojo` desde esta rama (D14): una prueba que falla, código sin pruebas que baja la cobertura de 80 % y una vista con SQL armado con texto del usuario, todo con datos ficticios. Verificar: en local, `uv run pytest --cov` falla por la prueba y por la cobertura
  - La salida local de `uv run pytest --cov` con la prueba fallando no se guardó; consta el PR #53 (6.5).
  - **Pendiente:** evidencia local de la falla.
- [x] 6.5 **(equipo)** Hacer push de `demo/EN-08-rojo` y abrir su PR hacia `main`. Verificar: `Pruebas y cobertura` en rojo, alerta de CodeQL alta o crítica, puerta de SonarQube Cloud fallida y fusión bloqueada. Guardar las capturas en `verificacion.md`, cerrar el PR sin fusionar y borrar la rama
  - Evidencia: PR #53, cerrado sin fusionar, con la rama borrada. Tres verificaciones en rojo, entre ellas `Code scanning results / CodeQL`, con 1 alerta de seguridad alta. Fusión bloqueada porque falta 1 aprobación y por la alerta de CodeQL. Capturas en `merge_fallido.docx` (documento del equipo, 17/10/2026). Detalle en `verificacion.md`, 6.5.
  - Diferencia con lo pedido: `CI / SonarQube Cloud` se omitió porque falló `Pruebas y cobertura`, así que la puerta de calidad fallida no quedó demostrada.
  - En rojo: `Code scanning results / CodeQL`, `CI / Pruebas y cobertura` y `CI / Ruff`. Alerta de CodeQL: "SQL query built from user-controlled sources", *High*, `src/backend/cuentas/demo_vista_sql.py:15`.
- [x] 6.6 Completar `verificacion.md`: evidencia de los cinco escenarios de EN-08 (incluido "Canal sin claves reales": `ci.yml` y el registro de la ejecución), el estado de la DoD 1 a 9 según D15 y los pendientes de documentación del design. Verificar: cada escenario de `specs/integracion-continua/spec.md` tiene su evidencia o una nota de por qué no aplica
  - Hecho: `verificacion.md` tiene los cinco escenarios, la DoD 1 a 9 según D15 y los pendientes de documentación.
  - Escenario "Puerta de calidad no superada": sin demostrar, con la nota del motivo (D9) en `verificacion.md`, 6.6. DoD 4: no aplica hasta EN-02; el cuerpo del PR #52 no menciona Vercel.
  - DoD 6: no aplica; EN-08 no implementa reglas de negocio del documento 09 ni agrega código de servicios (decisión del equipo, 18/10/2026).

## Workflow follow-up

- Aprobación del PR de EN-08 por otra integrante (DoD 3) y fusión en `main`.
- Después de la fusión, comprobar que el push a `main` ejecuta el canal en verde y que SonarQube Cloud muestra `main` analizada (spec "Análisis de la rama principal"). Anotarlo en `verificacion.md`.
- Archivar el cambio (`/opsx:archive`) después de la fusión, para que `integracion-continua` pase a `openspec/specs/`.
- Proponer al equipo, aparte y con subida de versión, los ajustes de "Pendientes de documentación" del design (documento 07, RNF-018; documento 02/01, DoD 1 y 2, escenario 4 de EN-08 y nota sobre CodeQL).
