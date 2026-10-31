# Tasks

## 1. Modelo y catálogo (D1, D2)

### Parte A: `CompetenciaPeriodo`, `a_cargo_docente_curso` y migraciones (alto riesgo)

- [x] 1.1 Prueba primero, `notas/tests/test_modelos.py`: la misma sección, periodo y competencia dos veces → `IntegrityError` (`uq_competencia_periodo`); borrar el año borra sus periodos y las marcas; borrar una competencia con marcas → `RestrictedError`; `db_table` es `competencia_periodo`. Luego `CompetenciaPeriodo` (D1) y `notas/0001`. Verificar: rojo y luego verde; `makemigrations --check` sin cambios; `sqlmigrate notas 0001` muestra la UQ y las tres FK con su `ON DELETE`
- [x] 1.2 Prueba primero, `catalogo/tests/` (archivos de modelos y del panel de EN-06): al migrar y al crear una institución ninguna área está a cargo del docente de curso; el Administrador marca «a cargo del docente de curso» en Educación Física desde la lista y desde la ficha, y queda CATALOGO_EDITADO con el nombre del campo; docente y dirección no ven ni cambian la marca por POST. Luego el campo (D2), `catalogo/0003` y `InstitucionAreaAdmin`. Verificar: rojo y luego verde; `uv run pytest src/backend/catalogo` en verde
- [x] 1.3 Revisión de la parte (agente `revisor`) y commit

## 2. Reglas, guardado y demo (D3 a D7, D10, D11)

### Parte B: servicios de `notas`, actividad y demo (alto riesgo)

- [x] 2.1 Prueba primero, `notas/tests/test_servicios_universo.py`: `puede_marcar` es verdadero solo para la docente de la sección, en un área que se trabaja y no está a cargo del docente de curso (otra docente, dirección, Castellano como segunda lengua e Inglés a cargo → falso); `areas_de_la_seccion` da 10 áreas en orden SIAGIE con 27 competencias, transversales incluidas, sin las inactivas, con `a_cargo` y `marcable`, en dos consultas; `universo` tiene 21 id. Luego D3. Verificar: rojo y luego verde
- [x] 2.2 Prueba primero, `notas/tests/test_servicios_periodos.py`: el 30-10 el bimestre 3 es VIGENTE, el 1 y el 2 ANTERIOR, el 4 FUTURO y no editable; el 1-08 (hueco) no hay vigente y solo el 1 y el 2 son editables; el 2-03 ningún periodo es editable; sin periodos, lista vacía; año CERRADO: ninguno editable; con TRIMESTRE, nombres T1 a T3. Luego D4. Verificar: rojo y luego verde
- [x] 2.3 Prueba primero, `notas/tests/test_servicios_obligatorias.py`: en el bimestre 4, las del universo no marcadas en el 1 al 3 (escenario «Flujo alternativo válido»); en el 3, ninguna; año CERRADO, ninguna; las áreas del docente de curso nunca; con TRIMESTRE, el último es el 3. `tiene_notas` devuelve `False`. Luego D6 y D7. Verificar: rojo y luego verde
- [x] 2.4 Prueba primero, `notas/tests/test_servicios_guardar.py`: primer guardado de 7 competencias de Matemática y Comunicación crea esas 7 marcas (escenario «Camino ideal») y COMPETENCIAS_MARCADAS con usuario, sección, periodo y agregadas; corregir deja la quitada y su entrada; el mismo envío dos veces no cambia nada ni deja entrada; periodo futuro y año CERRADO → `PeriodoNoMarcable`; competencia de Inglés a cargo o de otra institución → `ValidationError(CONJUNTO_NO_VALIDO)`; vacío → `SIN_MARCAS`; en el bimestre 4 las obligatorias se agregan aunque falten en el envío; con `tiene_notas` parcheada en verdadero para una quitada → `CompetenciaConNotas` con `MENSAJE_CON_NOTAS` y nada guardado (escenario «Caso de error»); una marca de una competencia desactivada o de un área a cargo sigue tras guardar. Luego D5, `COMPETENCIAS_MARCADAS` y sus claves (D10), con su migración de `actividad`, y la prueba del catálogo de `actividad`. Verificar: rojo y luego verde; `uv run pytest src/backend/notas src/backend/actividad` en verde
- [x] 2.5 Prueba primero, `notas/tests/test_concurrencia.py` (`transaction=True`, como `test_demo_concurrencia.py`): dos `guardar_marcas` del mismo periodo con conjuntos distintos, en dos hilos → queda uno de los dos conjuntos completo y nunca un `IntegrityError`. Verificar: rojo (sin el bloqueo) y luego verde
- [x] 2.6 Prueba primero, `institucion/tests/test_demo.py` y `test_comandos_demo.py`: con los 4 bimestres de ejemplo y hoy 15-10 (entre el B3 y el B4 de ejemplo), cada sección demo queda con su universo marcado en el 1, 2 y 3 y nada en el 4; sin periodos, ninguna marca; volver a cargar crea solo las marcas que faltan; quitar la demo borra las marcas de las secciones demo y no las de 3.° A, y DEMO_QUITADA las cuenta; descartar 3.° A borra sus marcas y el resumen y SECCION_DESCARTADA las cuentan; la carga no cambia `a_cargo_docente_curso`. Luego D11. Verificar: rojo y luego verde; las pruebas de EN-06 y US-028 de `institucion` siguen en verde
- [x] 2.7 Revisión de la parte (agente `revisor`) y commit

## 3. Rutas y acceso (D8)

### Parte C: vistas, rutas y permisos (alto riesgo)

- [x] 3.1 Prueba primero, `notas/tests/test_vistas_acceso.py`: la docente abre la pantalla de su sección (200); su sección de un año CERRADO y la sección de otra docente → 404 en GET y POST, sin marcas; dirección → su inicio; sin sesión → ingreso, y con `HX-Request` → `HX-Redirect`; la portada sigue con Notas en «Próximamente». Luego las vistas con `SeccionDocenteMixin`, `notas/urls.py` y su `include`. Verificar: rojo y luego verde
- [x] 3.2 Prueba primero, `notas/tests/test_vistas.py`: el contexto y el `json_script` de cada caso (vigente, hueco, antes del primero, sin periodos, `?periodo=1`, `?periodo=4` futuro abre el vigente), con los textos exactos del spec; POST 204 con las marcas; 400 con `competencia=x`, con conjunto no válido y con vacío (con su `mensaje`); 404 número de periodo inexistente; 409 futuro; 409 con notas (con `tiene_notas` parcheada) con `mensaje` y `competencias`. Luego `CompetenciasView` y `GuardarView`. Verificar: rojo y luego verde; `uv run pytest src/backend/notas` en verde
- [x] 3.3 Revisión de la parte (agente `revisor`) y commit

## 4. Pantalla (normal)

- [x] 4.1 Prueba primero, `notas/tests/test_plantilla.py`: la página dibuja las 10 áreas con sus competencias y contadores, las áreas a cargo atenuadas con «A cargo del docente de curso» y casillas deshabilitadas, los botones de periodo con `aria-pressed`, fechas y estado, el futuro deshabilitado, los motivos de bloqueo en su fila, el `<dialog>` de salida, las regiones `role="status"` y `role="alert"`, el `<noscript>`, y en los estados vacíos sin instrucción ni Guardar. Luego `templates/notas/competencias.html`, sus parciales y las clases en `src/frontend/css/app.css` (D9). Verificar: rojo y luego verde
- [x] 4.2 Prueba primero, `notas/tests/test_competencias_e2e.py`: desmarcar y guardar persiste al recargar (escenario «Camino ideal»); cápsula a 360 px (flechas, «2 de 10», extremo deshabilitado, selector, guardar desde otra área); borradores entre periodos con «Sin guardar» en el botón; «Deshacer cambios» no aparece en el bimestre 4 sin cambios; competencia obligatoria con Espacio no cambia y anuncia su motivo; con `tiene_notas` parcheada, desmarcar muestra «La competencia tiene notas registradas en este periodo»; red caída → «No se pudo guardar» y «Tus cambios siguen aquí. Reintenta.», y un guardado después lo quita; diálogo de salida (foco en «Seguir editando», Escape, «Salir sin guardar» sin aviso nativo) y `beforeunload` al recargar. Luego `static/js/competencias.js` (D9). Verificar: e2e de `notas` en verde con el CSS compilado y `DJANGO_ALLOW_ASYNC_UNSAFE=true`
- [x] 4.3 Prueba primero, en el mismo archivo e2e: axe sin infracciones graves en claro y oscuro, a 360 y 1280 px, con marcas, con bloqueos, con el diálogo, sin periodos y en vacaciones; sin desplazamiento horizontal a 320 y 360 px; filas de al menos 44 px. Luego los ajustes de CSS que falten y la fila de las dos rutas en el Catálogo de rutas de `docs/03`. Verificar: e2e de `notas` en verde
- [x] 4.4 Pantalla vista en claro/oscuro y celular/escritorio (la marca Marco). `verificar.py` y commit

## 5. Cierre

- [ ] 5.1 Con la A2 que corre el usuario (`/codex:adversarial-review --base main --background`, con foco en los specs del cambio, el universo del guardado y la concurrencia), corregir los Critical e Important, con la prueba primero. Verificar: `uv run pytest --cov` (80 % o más), las e2e y `verificar.py --antes-del-commit` en verde; la vista previa de Vercel aplica las tres migraciones en Neon
- [ ] 5.2 `verificacion.md`: tabla escenario → prueba de los cuatro specs del cambio y la DoD 1 a 9. Verificar: cada escenario tiene su prueba o una nota de por qué no aplica; commit

## Ajustes del propose a decisiones.md

- Decisión 3 (año CERRADO: solo lectura) se pospone: la sección de un año CERRADO es 404, como en asistencia; el servicio sigue rechazando el guardado (design D5 y D8).
- Decisión 3: antes del primer periodo, «Hoy no hay un periodo vigente» con la fecha de inicio del primero; «Bimestre» o «Trimestre» según la organización.
- Decisión 5: un conjunto vacío no se guarda («Marca al menos una competencia para guardar.»), porque sin marcas el periodo vuelve a abrir con todo marcado (design D5).
- Decisiones 5 y 13: el guardado compara y borra solo dentro de lo que la tutora puede marcar; las marcas de áreas a cargo o de competencias desactivadas no cambian (design D5).
- Decisión 8: las obligatorias se agregan en el servidor aunque el envío no las traiga.
- Decisión 11: la demo no pone `a_cargo_docente_curso`; volver a cargar marca solo los periodos sin marcas; quitar y descartar cuentan las marcas borradas.
- P2 de `notas.md` (borrador de otro bimestre): el botón del periodo dice «Sin guardar». P3 (instrucción en los estados vacíos): no se muestra.

## Workflow follow-up

- **(equipo)** Push de `feature/us-029-marcar-competencias-desarrolladas` y PR hacia `main` (`Closes #N` de US-029, verificando el número), con las verificaciones de EN-08 en verde y la vista previa de Vercel aplicando las migraciones. En «Para quien revise»: el guardado solo toca el universo de la tutora; las obligatorias del último periodo las pone el servidor; `tiene_notas` es `False` hasta US-020; la pantalla se abre solo por su dirección. En «## Deuda»:
  - enlace desde la tarjeta Notas, periodo sin marcas en el registro de notas, `tiene_notas` con `calificacion` y su costo por competencia → US-020; completitud → US-022; exonerados → US-035; bloqueo por entrega (RN-022) → historia de entrega;
  - docentes de curso (sus marcas, `puede_marcar`, asistencia y Computación) → historia nueva, sin ID; pregunta abierta a Nayely (pendientes.md);
  - consultar las marcas de un año CERRADO (decisión 3) → US-009 / historial;
  - borradores que se pierden al recargar o con la sesión vencida (`sessionStorage`) → si el piloto lo pide;
  - P3 de `notas.md` (palabra sola en la última línea a 320–360 px) y la repetición del motivo con lector real → pulido final;
  - después de la fusión, el Administrador marca Educación Física e Inglés de Virgen del Carmen como «a cargo del docente de curso» (decisión 12);
  - contradicciones para la pasada de docs: doc 08 (la docente tiene CU; desmarcar es DELETE); doc 11, 3.3 (`institucion_area` sin `a_cargo_docente_curso`, que amplía lo editable de EN-06); criterio de US-029 («al abrir el registro de notas» se cumple en la pantalla de marcado y en el servicio).
- **(equipo)** Aprobación del PR por otra integrante (DoD 3).
- Después de la fusión: `/opsx:archive` con «Sync now». La siguiente historia sale de `main` y su primer commit es este archivo.
