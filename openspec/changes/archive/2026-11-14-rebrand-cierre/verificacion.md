# Verificación: cierre del rebrand (inicio de la dirección y retiro de lo viejo)

Rama `feature/rebrand` (pasos 7 y 8 del PLAN del rebrand). Parte A, normal: la dirección en el marco del rebrand (`bdfd9c2`). Partes B (`e328c78`, retiro de lo viejo) y C (`007b256`, nombres finales), de alto riesgo y sin revisor: tocan el build, no modelos, permisos ni datos personales.

## Escenarios de la spec delta sin prueba propia

Ninguno. El inicio de la dirección con la cuenta cerrada y abierta está en `test_accesibilidad_e2e.py` (`direccion` y `direccion-menu-abierto`, claro y oscuro, 360 y 1280 px); el resto del escenario ya tenía sus pruebas.

## Minor para la descripción del PR

Ninguno. La A2 de Codex aprobó sin hallazgos. Sus dos próximos pasos ya están cubiertos: el axe de la dirección corre en las e2e de aquí, y los builds de Vercel y Docker quedan para la vista previa y el CI del PR (DoD 4 y 5).

## DoD 1 a 9

1. Cobertura ≥ 80 %: local 98,53 % (2208 pruebas en verde, sin e2e, `verificar.py --completo`, veredicto PASA). Sonar way: pendiente del PR.
2. Análisis estático: Ruff en verde. A2 de Codex: aprueba, sin hallazgos. CodeQL y SonarQube Cloud: pendiente del PR.
3. Aprobación de otra integrante: pendiente del PR.
4. Vista previa de Vercel: pendiente del push. Confirma que `npm run build` compila una sola hoja, `dist/app.css`, como aquí.
5. Escenarios y e2e: `-m e2e` completo, 590 en verde, 10 min 54 s. GitHub Actions: pendiente del PR.
6. Reglas de negocio: sin reglas nuevas ni cambios en `servicios.py`, vistas, rutas o modelos.
7. Accesibilidad: axe en claro y oscuro, a 360 y 1280 px, con la cuenta de la dirección cerrada y abierta; la cuenta abierta no desborda la ventana. Pantalla vista por Marco en claro/oscuro y celular/escritorio (tarea 1.4).
8. Sin datos reales: la directora de las pruebas («Rosa Huamán») es ficticia.
9. Documentación: spec delta, `design.md`, `tasks.md` y este archivo. Sin rutas nuevas: `docs/03` y README sin cambios. Deuda en «Workflow follow-up» de `tasks.md`.
