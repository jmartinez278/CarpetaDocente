# Verificación: Notas en el marco del rebrand

Rama `feature/rebrand` (paso 6 del PLAN del rebrand). Dos partes de alto riesgo sin revisor (no tocan modelos, migraciones, permisos ni datos personales): A, estructura y CSS de la hoja; B, conducta de `notas.js` (D1–D5).

## Escenarios de la spec delta sin prueba propia

- «Vacaciones» y «Sin periodos», en axe: se retiraron `test_axe_en_vacaciones` y `test_axe_sin_periodos` con aprobación de Marco (son estados sin boceto). Sus textos y el selector siguen probados en `test_plantilla_hoja.py` y `test_vistas_hoja.py`.
- «Lector de pantalla en una celda»: se prueba el `aria-label` de la celda, no un lector real. Sigue la deuda P3 de US-020/021/022 para el pulido final.

## Minor para la descripción del PR

- A2 de Codex (needs-attention, un hallazgo, clasificado Minor por Marco por ser un caso raro): con dos pestañas de la misma hoja, cambiar de periodo puede perder un borrador sin aviso. Si la otra pestaña cambió la misma celda, `sincronizar()` deja en pantalla lo de esta pero el dispositivo guarda lo de la otra; si la otra guardó o descartó, lo de esta vive solo en memoria. El interceptor de `[data-periodo]` (`notas.js`, D1) deja pasar sin `persistir()`, y al volver se recupera lo del dispositivo. Arreglo propuesto: `persistir()` cada área pendiente antes de dejar pasar el enlace y, si la escritura falla, `pedirSalida`; con una e2e de dos páginas (conflicto A/AD y descarte en la otra).
- Su sandbox no ejecutó Python ni las e2e; las suites se corrieron aquí.

## DoD 1 a 9

1. Cobertura ≥ 80 %: local 98,53 % (2208 pruebas en verde, sin e2e, `verificar.py --completo`, veredicto PASA). Sonar way: pendiente del PR.
2. Análisis estático: Ruff en verde. A2 de Codex con un hallazgo, pasado a Minor (arriba). CodeQL y SonarQube Cloud: pendiente del PR.
3. Aprobación de otra integrante: pendiente del PR.
4. Vista previa de Vercel: pendiente del push.
5. Escenarios y e2e: `-m e2e` completo, 590 en verde, 14 min 40 s. GitHub Actions: pendiente del PR.
6. Reglas de negocio: sin reglas nuevas. El periodo futuro sigue sin poder elegirse ni guardarse; RN-005 sigue con sus pruebas.
7. Accesibilidad: axe en claro y oscuro con notas, panel, rechazo y diálogos a 360 px, y recuadro y vista previa a 1280 px; sin desplazamiento de la página a 320 y 360 px; áreas táctiles de 44 px. Pantalla vista por Marco en claro/oscuro y celular/escritorio (tareas 1.8 y 1.16).
8. Sin datos reales: estudiantes y competencias ficticios de las fixtures.
9. Documentación: spec delta, `design.md`, `tasks.md`, RNF-005 1.3.0 (`3ba491c`) y este archivo. Sin rutas nuevas: `docs/03` y README sin cambios. Deuda en «Workflow follow-up» de `tasks.md`.
