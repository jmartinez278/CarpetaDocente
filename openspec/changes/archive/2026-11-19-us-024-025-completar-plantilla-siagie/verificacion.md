# Verificación: US-024/025 – Completar la plantilla de notas del SIAGIE

## Veredictos (19-11-2026, sobre `eeee6ea`)

- `uv run python scripts/verificar.py --completo`: Ruff y formato en verde; 2908 pruebas pasan; cobertura 98,54 %. Solo marca el `git status` sin limpiar (este archivo y el catálogo de rutas, que entran en el commit del cierre, y `docs/plan-poda-e2e.md`, que no es de la historia).
- `uv run pytest -m e2e --browser chromium -n 4 --dist loadfile --timeout=180` (el comando del CI): 609 pasan, en 3 min 33 s.

## Escenarios sin prueba automática

- «En tiempo» (RNF-003, tarea 4.1): sin medir, pasó a la deuda por decisión de Marco (19-11-2026). La vista previa no tiene notas ni una plantilla con los nombres de la demo; cómo medirlo está en el «Workflow follow-up» de `tasks.md`.
- «Se abre en Excel y LibreOffice» (RNF-006): manual. El equipo abre una plantilla completada en los dos antes del piloto (ver «Workflow follow-up» de `tasks.md`).
- Las tres migraciones en Neon (tarea 5.1): comprobado en la rama de Neon de la vista previa con `django_migrations`. `institucion/0006_institucion_anexo`, `exportaciones/0001_initial` y `actividad/0008_operaciones_plantilla_siagie` quedaron aplicadas el 19-11-2026 a las 01:22 UTC; los builds siguientes dicen «No migrations to apply».

## DoD 1 a 9

1. Cobertura ≥ 80 %: 98,54 % local. Sonar way: pendiente del PR.
2. Análisis estático: Ruff y formato en verde. Codex: adversarial en la parte C y normal en la parte D y en el cierre, con sus Critical e Important corregidos (`31f617c` y `eeee6ea`). CodeQL y SonarQube Cloud: pendiente del PR.
3. Aprobación de otra integrante: pendiente del PR.
4. Vista previa de Vercel: build en verde y migraciones aplicadas en Neon; RNF-003 sin medir, en la deuda.
5. Escenarios y e2e: `-m e2e` completo en verde, 609. GitHub Actions: pendiente del PR.
6. Reglas de negocio: reconocimiento por contenido, equivalencia por sección, cruce de nombres, llenado y conteos en `exportaciones/servicios.py`, con pruebas de servicios.
7. Accesibilidad: axe en ambos temas (diálogo con error, paso de la sección y resumen) y 360 px en e2e; pantallas vistas por Marco (tarea 4.4).
8. Sin datos reales: las plantillas se generan ficticias en cada prueba (`exportaciones/tests/plantilla.py`); ningún .xlsx entra al repo.
9. Documentación: catálogo de rutas 1.11.0 con `/direccion/plantilla-siagie/` y su borrado; README sin cambios.
