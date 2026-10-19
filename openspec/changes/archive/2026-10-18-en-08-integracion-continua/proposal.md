# Propuesta: EN-08 – Canal de integración continua

## Why

La DoD (`docs/02 Planificación/01 Transformando a ágil`, sección 7) exige en sus criterios 1, 2 y 5 una cobertura de al menos 80 %, un análisis estático sin vulnerabilidades críticas ni altas y pruebas de punta a punta con Playwright, y dice que todo eso se verifica "en GitHub Actions (EN-08)". Hoy el repositorio no tiene `.github/`: esos criterios se revisan a mano y, en el PR de EN-01, quedan pendientes. Además, US-001 y las demás historias del Sprint 1 necesitan el canal desde su primer PR para poder cerrarse según la DoD.

## What Changes

- **Workflow de GitHub Actions** (`.github/workflows/ci.yml`) que se dispara con `pull_request` hacia `main` y con `push` a `main`. El push deja analizada `main`, que SonarQube Cloud usa para comparar el código nuevo de cada PR. Tiene cuatro trabajos:
  - **Ruff:** `ruff check` y `ruff format --check`, con las reglas que ya fija `pyproject.toml` (incluye `S`, de Bandit).
  - **Pruebas y cobertura:** pytest contra un **PostgreSQL 17 de servicio**, temporal y sin contraseña. La base solo tiene datos ficticios, creados por las propias pruebas. La clave secreta de Django se genera en cada ejecución. El trabajo falla si la cobertura baja de **80 %** y genera `coverage.xml` para SonarQube Cloud.
  - **Playwright:** compila el CSS (`npm ci && npm run build`) y corre las pruebas de punta a punta en Chromium.
  - **SonarQube Cloud:** análisis en CI con `SonarSource/sonarqube-scan-action`, que lee la cobertura de `coverage.xml` y se autentica con el secreto de GitHub `SONAR_TOKEN`. El equipo pega el token en GitHub; el asistente nunca lo escribe ni lo pide.
- **CodeQL con la configuración por defecto de GitHub**, que se activa en *Settings*, sin workflow propio. Detecta Python, JavaScript y los propios workflows, y analiza cada PR hacia `main`.
- **Playwright entra en este cambio:** dependencia `pytest-playwright`, marcador `e2e` (excluido del `pytest` local por defecto) y una prueba de punta a punta de la página inicial. Así US-001 llega con el andamiaje listo para el criterio 5 de la DoD.
- **Configuración en `pyproject.toml`:** `fail_under = 80` y `relative_files = true` en la cobertura, y el marcador `e2e` en pytest.
- **`sonar-project.properties`:** organización, clave del proyecto, carpetas de código y de pruebas, y ruta de la cobertura. Solo tiene identificadores públicos, sin el token.
- **Bloqueo de la fusión:** tarea del equipo, documentada en el README y fuera del código de este cambio (paso B10 de la ruta del equipo). Un *ruleset* de GitHub sobre `main` exige las verificaciones anteriores y el resultado de CodeQL (alertas de severidad alta o mayor). En el mismo paso B10, el equipo agrega la aprobación de otra integrante (DoD 3) y el bloqueo de force push, que no son parte de EN-08.
- **README:** sección "Integración continua": qué revisa cada verificación, cómo reproducirla en local y los pasos manuales en GitHub y en SonarQube Cloud.

**Fuera de alcance:** vista previa de Vercel (DoD 4, EN-02); revisión automática de accesibilidad y pruebas en Firefox o WebKit (EN-07); protección contra subida de secretos (EN-04); actualización automática de dependencias (Dependabot).

## Capabilities

### New Capabilities

- `integracion-continua`: verificaciones automáticas que cada Pull Request hacia `main` debe pasar para fusionarse (pruebas, cobertura, Ruff, CodeQL, puerta de calidad de SonarQube Cloud y pruebas de punta a punta), el análisis de `main` tras cada fusión y cómo se ejecutan sin claves reales.

### Modified Capabilities

_(ninguna: `openspec/specs/` todavía está vacío porque EN-01 no se ha archivado. La exclusión de las pruebas `e2e` del `pytest` local se especifica en `integracion-continua`.)_

## Impact

- **Archivos nuevos:** `.github/workflows/ci.yml`, `sonar-project.properties`, `src/backend/cuentas/tests/test_inicio_e2e.py`.
- **Archivos modificados:** `pyproject.toml` (cobertura, marcador `e2e`, dependencia de desarrollo `pytest-playwright`), `uv.lock`, `README.md`.
- **Fuera del repositorio**, en manos del equipo: proyecto en SonarQube Cloud con el análisis automático desactivado, secreto `SONAR_TOKEN`, configuración por defecto de CodeQL y *ruleset* de `main` (paso B10).
- **Rama:** sale de `feature/EN-01-proyecto-django`. El PR de EN-08 se abre cuando EN-01 esté fusionado; antes se integra `main` con `git merge`, sin rebase ni force push.
- **Requisitos:** EN-08; RNF-018; DoD 1, 2 y 5. Cada PR posterior queda sujeto a este canal.
