# Verificación: US-040 – Consultar los consolidados

## Veredictos (24-11-2026, sobre `983a038` más el catálogo de rutas, `tasks.md` y el arreglo de una e2e del cierre)

- `uv run python scripts/verificar.py --completo`: Ruff y formato en verde; la suite pasa con cobertura 98,65 %. Solo marca el `git status` sin limpiar (el catálogo de rutas, `tasks.md`, `verificacion.md` y la e2e corregida, que entran en el commit del cierre).
- `DJANGO_ALLOW_ASYNC_UNSAFE=true uv run pytest -m e2e --browser chromium -n 4 --dist loadfile --timeout=180` (el comando del CI): la primera corrida dio 468 pasan y 2 fallan. Las dos eran de `institucion/tests/test_asignar_seccion_e2e.py` y seguían esperando la fecha en la línea de la sección, que la tarea 2.1 quitó; se actualizaron a «2.º grado, sección A». Segunda corrida: 470 pasan, en 2 min 56 s.

## Escenarios sin prueba automática

- «Caso de error» de US-040 (guardados de notas, competencias y asistencia enviados por la dirección): la dirección no tiene interfaz que los provoque; la matriz de permisos los envía a mano y comprueba que no guardan nada (deuda US-026 en `tasks.md`).
- «Mapa de secciones», una fila por grado de 1.º a 6.º: el mapa omite un grado sin secciones; con 1.º a 6.º completos no se nota. Sin prueba del grado vacío; va a la deuda de `tasks.md`.
- Lo visual (Pizarra neutra, calendario, colores del mapa, claro/oscuro a 360 y 1280 px): lo vio Marco pantalla por pantalla (tareas 1.3, 2.2, 4.4, 6.4 y 7.3); las e2e miden axe y el ancho del documento, no el aspecto.

## DoD 1 a 9

1. Cobertura ≥ 80 %: 98,65 % local. Sonar way: pendiente del PR.
2. Análisis estático: Ruff y formato en verde. Revisor (subagente) en los grupos 3 y 5 y en el cierre, sin Critical ni Important abiertos; sus Minor están en la deuda de `tasks.md`. CodeQL y SonarQube Cloud: pendiente del PR.
3. Aprobación de otra integrante: pendiente del PR.
4. Vista previa de Vercel: pendiente del PR; no hay migraciones nuevas.
5. Escenarios y e2e: `-m e2e` completo en verde (470). GitHub Actions: pendiente del PR.
6. Reglas de negocio: estado de las secciones, periodo elegido, notas faltantes y días sin completar por lote, totales de asistencia y visibilidad de sesiones para la dirección en `direccion/servicios.py`, `notas/servicios.py`, `asistencia/servicios.py` y `repositorio/servicios.py`, con pruebas de servicios; las vistas solo leen.
7. Accesibilidad: axe, 360 px y ancho del documento en e2e para las pantallas nuevas y el botón de tema, en ambos temas; pantallas vistas por Marco.
8. Sin datos reales: solo estudiantes y docentes ficticios en las pruebas.
9. Documentación: catálogo de rutas 1.13.0 con las rutas de `/direccion/`; README sin cambios (no cambia cómo se instala, se corre ni se prueba).
