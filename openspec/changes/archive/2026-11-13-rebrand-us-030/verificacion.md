# Verificación: Asistencia en el marco del rebrand

Rama `feature/rebrand` (paso 4 del PLAN del rebrand). Los dos escenarios de la spec delta de `asistencia-jornada` tienen prueba. La lógica de `asistencia.js` (cola, reintentos, lote, cierre, sesión vencida) no cambió: sus e2e siguen en verde con los selectores nuevos (D3).

Pruebas en `src/backend/asistencia/tests/`: `vis` = `test_vistas.py`, `e2e` = `test_asistencia_e2e.py`.

## Escenarios de la spec delta

- **Caso de error** (18 de 25): `vis::test_caso_de_error_el_conteo_visible_y_el_accesible`; el enlace «7 sin marcar» lleva a la primera fila Sin marcar sin que la tape el resumen: `e2e::test_n_sin_marcar_lleva_a_la_primera_fila_sin_marcar`.
- **Revisión de cada vista**: `e2e::test_la_lista_a_medio_marcar_pasa_axe`, `test_el_fin_de_semana_pasa_axe`, `test_la_seccion_sin_estudiantes_pasa_axe` y `test_las_vistas_de_la_parte_c_pasan_axe` (con barra, sin conexión, completa), en ambos temas a 360 y 1280 px; sin desplazamiento horizontal: esas mismas y `test_nombre_de_120_mas_120_a_320_px`.

## Sin prueba

- «Los círculos miden 44 px» (texto del requisito, sin escenario propio): ninguna prueba mide la caja del círculo; se vio en pantalla (tarea 1.13). No se agregó una prueba en el cierre.

## Minor para la descripción del PR

- Sin revisor: ninguna parte era de alto riesgo (`tasks.md`).
- La A2 encontró un [medium] (Important): el `scroll-padding-top` de `html` usaba `--asistencia-margen-fila`, definida solo en `.asistencia-hoy`, y quedaba sin efecto; con el teclado, un control podía quedar bajo el resumen fijo del celular. Corregido definiendo la variable en `html:has(.asistencia-rejilla)`; prueba nueva `e2e::test_ninguna_parada_del_foco_queda_bajo_el_resumen` (Shift+Tab por toda la lista, nota de justificación incluida, y Tab hacia adelante), vista en rojo antes del arreglo.
- `institucion/tests/test_estudiantes_e2e.py::test_tomar_la_asistencia_abre_la_asistencia_como_pagina_completa` esperaba el `<h1>` anterior y ningún `<dialog>`; ahora espera «Asistencia de hoy» y que no esté `dialog#estudiantes` (el ☰ del marco es un `<dialog>`).

## DoD 1 a 9

1. Cobertura ≥ 80 %: local 98,53 % (2180 pruebas en verde, sin e2e, `verificar.py --completo`). Sonar way: pendiente del PR.
2. Análisis estático: Ruff en verde. A2 de Codex: un hallazgo, corregido. CodeQL y SonarQube Cloud: pendiente del PR.
3. Aprobación de otra integrante: pendiente del PR.
4. Vista previa de Vercel: pendiente del push.
5. Escenarios y e2e: `-m e2e` completo, 602 en verde y 1 roja (la prueba desactualizada de Estudiantes, ya ajustada), 11 min 48 s. Tras los arreglos, las 63 e2e de asistencia (incluida la nueva y la ajustada) en verde. GitHub Actions: pendiente del PR.
6. Reglas de negocio: sin reglas nuevas; `servicios.py` y modelos sin cambios. RN-012 (jornada incompleta) sigue con sus pruebas.
7. Accesibilidad: axe en las seis vistas, ambos temas, 360 y 1280 px; foco nunca bajo el resumen fijo. Pantalla vista por Marco en claro/oscuro y celular/escritorio (tarea 1.13).
8. Sin datos reales: estudiantes ficticios de las fixtures.
9. Documentación: spec delta, `design.md`, `tasks.md` y este archivo. Sin rutas nuevas: `docs/03` y README sin cambios. Deuda en «Workflow follow-up» de `tasks.md`.
