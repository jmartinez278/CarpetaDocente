# Tasks

## 1. Modelo y base de datos (D1, D3)

### Parte A: `btree_gist`, `Periodo` y migración (alto riesgo)

- [x] 1.1 Prueba primero, `institucion/tests/test_modelos_periodo.py`: una prueba que crea la extensión y consulta `pg_extension` (marcada para correr primero). Antes de escribir el modelo: `SELECT name, installed_version FROM pg_available_extensions WHERE name = 'btree_gist'` en la base de Docker y documentación de Neon (Context7 o web) sobre `btree_gist` y extensiones "trusted". Verificar: la extensión está disponible en `postgres:17`; Neon la lista como compatible; si no, parar y avisar a Marco (plan B del design)
- [x] 1.2 Prueba primero, `institucion/tests/test_modelos_periodo.py`: número repetido en el año y número 0 o 5 → `IntegrityError`; fin igual o anterior al inicio → `IntegrityError` (`ck_periodo_fechas`); dos periodos del mismo año que se cruzan (también por un mismo día de borde) → `IntegrityError` al confirmar o con `SET CONSTRAINTS ex_periodo_cruce IMMEDIATE`; el mismo rango en dos años distintos se permite; correr el fin del 1 y el inicio del 2 en dos `UPDATE` seguidos dentro de una transacción no falla (diferida); borrar el año borra sus periodos; orden por número. Luego `Periodo` (D1, D3), `institucion/0005` con `BtreeGistExtension` y, si Django lo pide, `django.contrib.postgres` en `INSTALLED_APPS`. Verificar: rojo y luego verde; `makemigrations --check` sin cambios; `sqlmigrate institucion 0005` muestra `CREATE EXTENSION`, `uq_periodo`, `ck_periodo_numero`, `ck_periodo_fechas` y `ex_periodo_cruce … DEFERRABLE INITIALLY DEFERRED`
- [x] 1.3 Revisión de la parte (agente `revisor`) y commit. Push temprano de la rama (con aprobación) y PR en borrador hacia `main`, solo para que la vista previa de Vercel corra `institucion/0005` en Neon. Verificar: el build de la vista previa muestra la migración aplicada; si falla por la extensión, parar antes de la parte 2 (plan B del design)

## 2. Reglas, guardado y panel (D2, D4 a D6, D8)

### Parte A: servicios, registro de actividad y periodo vigente (alto riesgo)

- [x] 2.1 Prueba primero, `institucion/tests/test_servicios_periodos.py`, `validar_periodos`: los textos exactos de D2 en su fila (fin antes del inicio; fuera del año, también el 1 de enero del año siguiente; "Completa las fechas de los 4 periodos."; "Las fechas se cruzan con otro periodo" en la fila de número mayor, también por un día de borde; orden); cruce y desorden a la vez → mensaje del cruce; hueco de vacaciones válido; todas vacías válido; 3 filas con TRIMESTRE; año CERRADO y organización vacía rechazados. Luego `validar_periodos` y las constantes de los mensajes. Verificar: rojo y luego verde
- [x] 2.2 Prueba primero, en el mismo archivo, `guardar_periodos`: crea los N con PERIODOS_CONFIGURADOS (`{"periodos": 4}`, usuario y entidad año); editar dos periodos deja dos PERIODO_EDITADO con número y fechas antes y después, y los id de los periodos no cambian (escenario "Flujo alternativo válido"); sin cambios, sin entradas; correr el fin del 1 y el inicio del 2 a la vez se guarda; un cruce que solo ve la base (validación parcheada para pasar) → `ValidationError(MENSAJE_CRUCE)`, sin periodos ni entradas; cambiar la organización con periodos guardados → rechazado. Luego `guardar_periodos` (D4), `PERIODOS_CONFIGURADOS`, `PERIODO_EDITADO` y sus claves en `DETALLE_PERMITIDO` (D6), con su migración de `actividad` si cambian las `choices`. Verificar: rojo y luego verde
- [x] 2.3 Prueba primero, `institucion/tests/test_servicios_periodos.py` (o `test_concurrencia_periodos.py`, con `transaction=True` como `test_demo_concurrencia.py`): dos `guardar_periodos` del mismo año a la vez, en dos hilos → van en fila: el primero crea los periodos y el segundo, al releer, edita lo del primero (4 PERIODO_EDITADO); nunca un `IntegrityError` sin traducir. Verificar: rojo (sin el bloqueo) y luego verde
- [x] 2.4 Prueba primero, `institucion/tests/test_periodo_vigente.py`: desde una sección y desde un año; 16-03, 20-04 y 15-05 → bimestre 1; día entre el 2 y el 3, fecha anterior al 1 y posterior al 4 → `None`; año sin periodos → `None`; sin fecha, con `timezone.localdate` y `timezone.now` parcheados (15-05 21:00 en Lima, 16-05 en UTC) → bimestre 1; una sola consulta (`django_assert_num_queries`). Luego `periodo_vigente` (D8). Verificar: rojo y luego verde; `uv run pytest src/backend/institucion src/backend/actividad` en verde
- [x] 2.5 Revisión de la parte (agente `revisor`) y commit

### Parte B: ficha del año y de la institución en el panel (alto riesgo)

- [x] 2.6 Prueba primero, `institucion/tests/test_admin_periodos.py`: la ficha de un año con BIMESTRE muestra 4 filas numeradas 1 a 4, sin casilla de borrar, y la de TRIMESTRE 3; al crear un año no hay filas; sin organización, el aviso con el enlace y sin filas; guardar las 4 crea los periodos y PERIODOS_CONFIGURADOS (escenario "Camino ideal" por el panel); cada mensaje de D2 aparece en la ficha y no se guarda nada (escenario "Caso de error"); editar el estado del año con las filas vacías lo guarda sin periodos; un POST con `DELETE` no borra; año CERRADO: fechas de solo lectura y un POST que las cambie no las cambia; con `guardar_periodos` lanzando `ValidationError(MENSAJE_CRUCE)` en el guardado → 200 con el mensaje, sin 500 y sin cambios; ficha de la institución con periodos: organización de solo lectura y un POST que la cambie no la cambia; docente y dirección no ven la ficha ni cambian periodos por POST. Luego `PeriodoInline`, el formset, `save_formset`, el manejo del `ValidationError` del guardado y la organización de solo lectura (D5). Verificar: rojo y luego verde; `test_admin.py` y `actividad/tests/test_panel_instrumentado.py` siguen en verde
- [x] 2.7 Revisión de la parte (agente `revisor`) y commit

## 3. Demo y pantalla (normal)

- [x] 3.0 Prueba primero, `test_admin_periodos.py`: en la ficha de un año con periodos, `institucion` es de solo lectura, y un POST que la cambia no la cambia. Luego `get_readonly_fields` de `AnioEscolarAdmin`. Verificar: rojo y luego verde (resuelve el Minor de la Parte 2B)
- [x] 3.1 Prueba primero, `institucion/tests/test_demo.py` y `test_comandos_demo.py`: con BIMESTRE y año sin periodos, la carga crea los 4 bimestres de ejemplo, el resumen los nombra y queda PERIODOS_CONFIGURADOS con usuario vacío; año con periodos → no cambian; organización vacía o TRIMESTRE → sin periodos y el resumen dice que se configuran en el panel; volver a cargar sin periodos crea solo los periodos; `quitar_demo` y `descartar_seccion` no tocan los periodos; si la carga falla después de los periodos, no queda ninguno (todo o nada). Luego D7 en `demo.py`. Verificar: rojo y luego verde; las pruebas de EN-06 siguen en verde
- [x] 3.2 Prueba primero, `institucion/tests/test_periodos_e2e.py`: el Administrador llena los 4 bimestres en la ficha y guarda; un cruce muestra el mensaje junto a la fila; axe de la ficha con filas vacías, con el error y de solo lectura (año CERRADO), en ambos temas a 360 y 1280 px; 360 px sin desplazamiento horizontal de la página. Verificar: e2e en verde con el CSS compilado y `DJANGO_ALLOW_ASYNC_UNSAFE=true`
- [x] 3.3 Ficha vista en claro/oscuro y celular/escritorio (la marca Marco). `verificar.py` y commit

## 4. Cierre

- [x] 4.1 Con la A2 que corre el usuario (`/codex:adversarial-review --base main --background`, con foco en los specs del cambio y en el cruce bajo concurrencia), corregir los Critical e Important, con la prueba primero. Verificar: `uv run pytest --cov` (80 % o más), las e2e y `verificar.py --antes-del-commit` en verde; la vista previa de Vercel del PR aplica `institucion/0005` en Neon
- [x] 4.2 `verificacion.md`: tabla escenario → prueba de los tres specs del cambio y la DoD 1 a 9. Verificar: cada escenario tiene su prueba o una nota de por qué no aplica; commit

## Ajustes del propose a decisiones.md

- Decisión 2: los periodos se configuran en la ficha de un año ya guardado, no al crearlo; las N filas se guardan todas o ninguna, y todas vacías es válido (año sin configurar).
- Decisión 4: mensajes de las reglas (b) y (c), de filas incompletas y de fin no posterior al inicio, escritos en el spec. Si un cruce también es desorden, gana el texto del cruce.
- Decisión 5: la restricción es diferida y se comprueba al final del guardado (design D3); dos guardados a la vez se ordenan con el bloqueo de la institución y del año (D4).
- Decisión 5: `validar_organizacion` rechaza cambiar la organización de la institución si ya tiene periodos guardados (design D5).
- Decisión 2: en un año que ya tiene periodos, vaciar todas las filas se rechaza con "Completa las fechas de los N periodos."; todas vacías solo es válido en un año sin periodos.
- Decisión 8: PERIODOS_CONFIGURADOS también lo deja la demo, con usuario vacío.
- Decisión 9: la demo crea los bimestres solo si la organización es BIMESTRE; con organización vacía o TRIMESTRE no crea periodos y lo dice.

## Workflow follow-up

- **(equipo)** Push de `feature/US-028-configurar-periodos-del-año-escolar` y PR hacia `main` (`Closes #N` de US-028, verificando el número), con las verificaciones de EN-08 en verde y la vista previa de Vercel aplicando la migración en Neon. En "Para quien revise": primera extensión de PostgreSQL (`btree_gist`) y primera restricción de exclusión, diferida; todas las escrituras de periodos pasan por `guardar_periodos`; la organización de la institución queda fija con periodos. En "## Deuda":
  - mostrar el periodo en curso a la docente y la dirección → US-020 / US-029; que notas use `periodo_vigente` → US-020;
  - entrega y bloqueo por periodo (RN-022) → US-026; KPI-03/04 → US-040; cierre del año (RF-009) → US-009;
  - cambiar de bimestres a trimestres con periodos guardados: hoy no se puede;
  - fechas reales de los bimestres 2026 → Nayely; los bimestres de la demo viven en el año real y no se marcan (pendientes.md);
  - contradicciones para la pasada de docs: doc 11, 3.1 ("que no se crucen lo valida la aplicación" → también la base, decisión 5); DDL del doc 11 sin `ex_periodo_cruce` ni `btree_gist`.
- **(equipo)** Aprobación del PR por otra integrante (DoD 3).
- Después de la fusión: `/opsx:archive` con "Sync now". La siguiente historia sale de `main` y su primer commit es este archivo.
