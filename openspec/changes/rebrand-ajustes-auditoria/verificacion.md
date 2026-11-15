# Verificación: ajustes de la auditoría visual del rebrand

Rama `feature/us-011-012-016-buscar-descargar-eliminar-sesion`. Parte A (Notas, alto riesgo, sin revisor: no toca modelos, permisos ni datos personales), parte B (Asistencia, Estudiantes y Sesiones, normal) y parte C (cierre).

## Descartado o sin aplicar

- A-05 (rótulo de Competencias en el celular): descartado (D3, decisión de Marco del 15-11-2026). Con el rótulo, la píldora de 147 px no cabe en la tira de 124 px a 360 px. Va a la deuda de `tasks.md`.
- A-06: descartado. `registro-notas:150` y `:161` definen que la conclusión se oculta y se borra con A/AD; la app cumple.
- A-08: no aplica. `registro-notas:169` fija «Rellena la conclusión».

## Sin prueba automática (CSS, vistos por Marco)

- A-03 (numeración de Estudiantes), A-07, A-09, A-10 (Notas) y A-15 (pie de los diálogos). En el cierre, la e2e de Estudiantes a 320 px con el texto al 200 % falló por A-03 (el nombre quedó en 11,6 px) y se arregló con `column-gap: var(--s-1)` bajo 700 px; la prueba existente fue la guarda.

## Minor para la descripción del PR

- A2 de Codex (`/codex:adversarial-review --base main`, foco en la parte A): approve, sin hallazgos. Su sandbox no ejecutó las e2e ni la suite; se corrieron aquí.

## DoD 1 a 9

1. Cobertura ≥ 80 %: local 98,53 % (2209 pruebas sin e2e, `verificar.py --completo`). Sonar way: pendiente del PR.
2. Análisis estático: Ruff en verde; A2 sin hallazgos. CodeQL y SonarQube Cloud: pendiente del PR.
3. Aprobación de otra integrante: pendiente del PR.
4. Vista previa de Vercel: pendiente del push.
5. Escenarios y e2e: `-m e2e` completo, 595 (594 en la primera corrida y la que falló, corregida, en verde: 107 de Estudiantes). GitHub Actions: pendiente del PR.
6. Reglas de negocio: sin reglas nuevas ni cambios en los servicios.
7. Accesibilidad: axe en claro y oscuro con las e2e de cada pantalla; áreas táctiles de 44 px (A-01); foco fuera de la barra «Deshacer» (A-14). Pantallas vistas por Marco en claro/oscuro, a 360 y 1280 px.
8. Sin datos reales: fixtures ficticias.
9. Documentación: `tasks.md` y este archivo. Sin rutas nuevas: `docs/03` y README sin cambios. Deuda en «Workflow follow-up».
