# Verificación: Competencias en el marco del rebrand

Rama `feature/rebrand` (paso 5 del PLAN del rebrand). La lógica de `competencias.js` (borradores, guardado, bloqueos, 400/409, red caída, sesión vencida, 403, salida) no cambió: sus e2e siguen en verde con las clases y los textos nuevos (D3).

## Escenarios de la spec delta sin prueba propia

- «Llega sin competencias confirmadas», segunda mitad: que tras guardar «Registrar notas del III bimestre» abra la hoja del bimestre 3 no tiene e2e propia. El aviso y el enlace con periodo y área se prueban en `test_plantilla.py` y la redirección desde la hoja en `test_vistas_hoja.py`. El enlace vuelve a las notas en `test_hoja_e2e.py::test_competencias_vuelve_a_las_notas_del_periodo_y_el_area`.
- «Con cambios sin guardar» desde «Registrar notas del III bimestre»: «¿Salir sin guardar?» se prueba al salir por el ☰ (`test_salir_por_el_menu_con_cambios_abre_el_dialogo_sobre_el_cajon`) y al cerrar sesión, con el mismo manejador de salida. No hay una e2e que use este enlace.
- Slow 4G (RNF-002, texto del requisito sin escenario): no hay prueba con la red limitada para Competencias; solo la tiene la hoja de notas.
- 44 px de alto por fila (texto del requisito): se retiró `test_las_filas_miden_al_menos_44_px` con aprobación de Marco; los comprueba la auditoría visual final («Workflow follow-up»).

## Minor para la descripción del PR

- Sin revisor: ninguna parte era de alto riesgo (`tasks.md`).
- A2 de Codex: aprobada sin hallazgos. Su sandbox no le dejó ejecutar Python; las suites se corrieron aquí.
- El `-m e2e` completo encontró tres fallas, todas de pruebas:
  - `notas/tests/test_hoja_e2e.py::test_competencias_vuelve_a_las_notas_del_periodo_y_el_area` buscaba «Registrar notas de B3» y el botón «B2»; ahora busca «Registrar notas del III bimestre» y «II bimestre». La hoja sigue con «B2» hasta el paso 6.
  - `test_con_tab_la_ultima_fila_queda_sobre_la_barra` era intermitente (2 de 6 corridas): `competencias-barra.js` pone el `scroll-margin-bottom` de una fila con un `ResizeObserver` cuando su área se hace visible, y la prueba hacía Tab antes. Ahora espera ese margen. Ninguna persona llega a hacer Tab en ese mismo cuadro.
  - `institucion/tests/test_estudiantes_e2e.py::test_cerrar_es_un_boton_con_borde_de_44_px_con_icono_y_texto` era intermitente (4 de 5 corridas): medía el botón durante la escala de apertura del diálogo (43,999996 px). Ahora espera a que termine la animación. Es de `rebrand-us-006`, no de esta historia.
  - Tras los ajustes: 8 de 8 corridas en verde de las dos intermitentes, y las e2e de competencias, hoja y Estudiantes en verde.

## DoD 1 a 9

1. Cobertura ≥ 80 %: local 98,53 % (2194 pruebas en verde, sin e2e, `verificar.py --completo`). Sonar way: pendiente del PR.
2. Análisis estático: Ruff en verde. A2 de Codex sin hallazgos. CodeQL y SonarQube Cloud: pendiente del PR.
3. Aprobación de otra integrante: pendiente del PR.
4. Vista previa de Vercel: pendiente del push.
5. Escenarios y e2e: `-m e2e` completo, 588 en verde y 3 rojas (arriba, ya ajustadas), 10 min 32 s. GitHub Actions: pendiente del PR.
6. Reglas de negocio: sin reglas nuevas; `servicios.py` solo suma `romano` y `nombre_romano` (D1). RN-005 (obligatorias del último periodo) sigue con sus pruebas.
7. Accesibilidad: axe en el estado principal y con «¿Salir sin guardar?», en claro y oscuro, a 360 px; foco en el botón del periodo tras Enter; la última fila sobre la barra fija con Tab. Pantalla vista por Marco en claro/oscuro y celular/escritorio (tarea 1.13).
8. Sin datos reales: estudiantes y competencias ficticios de las fixtures.
9. Documentación: spec delta, `design.md`, `tasks.md` y este archivo. Sin rutas nuevas: `docs/03` y README sin cambios. Deuda en «Workflow follow-up» de `tasks.md`.
