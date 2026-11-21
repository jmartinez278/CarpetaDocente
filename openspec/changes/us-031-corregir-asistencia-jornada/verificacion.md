# Verificación: US-031 – Corregir la asistencia de una jornada

## Veredictos (20-11-2026, sobre `62b60bf` más el catálogo de rutas y `tasks.md` del cierre)

- `uv run python scripts/verificar.py --completo`: Ruff y formato en verde; la suite pasa con cobertura 98,60 %. Solo marca el `git status` sin limpiar (el catálogo de rutas y `tasks.md`, que entran en el commit del cierre, y `docs/plan-poda-e2e.md`, que no es de la historia).
- `DJANGO_ALLOW_ASYNC_UNSAFE=true uv run pytest -m e2e --browser chromium -n 4 --dist loadfile --timeout=180` (el comando del CI): 619 pasan, en 3 min 41 s.

## Escenarios sin prueba automática

- «Caso de error» de «Periodo cerrado» (doc 02, RN-022): `periodo_cerrado` es solo un enganche que devuelve siempre falso; sus textos y el 409 se prueban parcheándolo, pero el cierre real por notas entregadas llega con US-026 (ver «Workflow follow-up» de `tasks.md`).

## DoD 1 a 9

1. Cobertura ≥ 80 %: 98,60 % local. Sonar way: pendiente del PR.
2. Análisis estático: Ruff y formato en verde. Codex: adversarial en el grupo 1, normal en el grupo 2 y en el cierre, con sus Critical e Important corregidos; los Minor y las dos observaciones del cierre (medianoche en la página sin fecha, lista vacía con «Fuera del registro») están en la deuda de `tasks.md` por decisión de Marco. CodeQL y SonarQube Cloud: pendiente del PR.
3. Aprobación de otra integrante: pendiente del PR.
4. Vista previa de Vercel: pendiente del PR; no hay migraciones nuevas.
5. Escenarios y e2e: `-m e2e` completo en verde, 619. GitHub Actions: pendiente del PR.
6. Reglas de negocio: fechas que se abren, activos del día, guardado de un día anterior y periodo cerrado en `asistencia/servicios.py`, con pruebas de servicios; `correccion` en el registro de actividad (`actividad/servicios.py`) y `update_fields` en `editar_estudiante`.
7. Accesibilidad: axe, 360 px y ancho del documento en e2e para el día pasado y el periodo cerrado, en ambos temas; pantallas vistas por Marco (tarea 3.5).
8. Sin datos reales: solo estudiantes ficticios en las pruebas.
9. Documentación: catálogo de rutas 1.12.0 con `/docente/secciones/<id>/asistencia/<fecha>/`; README sin cambios.
