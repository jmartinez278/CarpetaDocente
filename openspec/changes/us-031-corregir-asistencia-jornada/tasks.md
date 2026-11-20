# Tasks

## 1. Fechas, activos del día y registro [riesgo: alto · opus]

Razón: la fecha válida cruza día de semana, hoy de Lima, inicio del año (con o sin periodos) y periodo cerrado; los activos del día cruzan estado y `fecha_estado`, y de ellos dependen guardar, completa y JORNADA_COMPLETA.

- [x] 1.1 Prueba primero, `asistencia/tests/test_servicios.py`: `inicio_del_anio` (periodo 1 o 1 de enero) y `se_puede_abrir` (hoy aunque sea antes del inicio; día anterior dentro del rango; inicio exacto; día anterior al inicio; mañana; sábado; 23:30 de Lima). Luego las dos funciones y `_validar_fecha` con ellas (D1). Verificar: rojo y luego verde; `uv run pytest src/backend/asistencia`
- [x] 1.2 Prueba primero, `asistencia/tests/test_servicios.py`: `activos_del_dia` y `lista_del_dia` con «Retirado después del día abierto», «Retirado sin fecha», retirado el mismo día (fuera), y «Día anterior con un retirado después» (24/25, incompleta). Luego `activos_del_dia`, `lista_del_dia` en lugar de `lista_de_hoy`, y `_completa_o_vacia` con la fecha (D4). Verificar: rojo y luego verde; `uv run pytest src/backend/asistencia`
- [x] 1.3 Prueba primero, `asistencia/tests/test_servicios.py`: `marcar` y `marcar_restantes` en un día anterior (Faltó → Tarde; «Día anterior olvidado» crea una jornada con los 25; un retirado después se guarda; uno retirado antes da `Estudiante.DoesNotExist`); fechas que no se abren → `FechaNoValida` sin crear nada; con `periodo_cerrado` parcheado a verdadero → `PeriodoCerrado` sin crear nada; JORNADA_COMPLETA de un día pasado con sus activos. Luego `periodo_cerrado`, `PeriodoCerrado` y los activos del día en los dos guardados (D4, D6). Verificar: rojo y luego verde; `uv run pytest src/backend/asistencia`
- [x] 1.4 Prueba primero, `asistencia/tests/test_actividad.py`: escenarios «Corrección de un día anterior», «Cambio de hoy» (sin la clave) y «Día anterior olvidado» (REGISTRO_ASISTENCIA de esa fecha y `correccion: true`, también con origen `lote`). Luego `correccion` en `_registrar_cambio` y en la lista permitida de `actividad/servicios.py` (D7). Verificar: rojo y luego verde; `uv run pytest src/backend/asistencia src/backend/actividad`
- [x] 1.5 Prueba primero, `institucion/tests/` (el archivo de servicios de estudiantes): una copia vieja con otro `estado` y `fecha_estado` editada en nombre no revierte esos campos; un estudiante borrado sigue dando `Estudiante.DoesNotExist`. Luego `update_fields` en `editar_estudiante` (D9). Verificar: rojo y luego verde; `uv run pytest src/backend/institucion`
- [x] 1.6 `verificar.py` y commit; luego `/codex:adversarial-review --base main --background`

## 2. Abrir un día y selector de la semana [riesgo: medio]

- [x] 2.1 Prueba primero, `asistencia/tests/test_vistas.py`: `asistencia/<fecha>/` de un día anterior responde 200 sin crear jornada; mañana, sábado, antes del inicio y fecha inexistente → 404; de otra docente → 403 aunque la fecha no valga; `asistencia/<hoy>/` igual que `asistencia/`; `url_marcar` y `url_restantes` llevan la fecha abierta; guardados de un día anterior → 204 y de una fecha que no se abre → 409 (reemplaza `test_un_guardado_de_otro_dia_responde_409` y `test_restantes_de_otro_dia_responde_409`). Luego la ruta `dia`, la vista base compartida y el `Http404` (D2). Verificar: rojo y luego verde; `uv run pytest src/backend/asistencia`
- [x] 2.2 Prueba primero, `asistencia/tests/test_servicios.py`: `semana(abierto, hoy, inicio)` con los escenarios «Selector un jueves», «Selector en un día pasado», «Primera semana del año», flecha anterior que cae antes del inicio y flecha siguiente que se pasa de hoy, y el fin de semana con el viernes de referencia (D3). Luego `semana` y `Dia` con `elegido`, `disponible` y URL. Verificar: rojo y luego verde; `uv run pytest src/backend/asistencia`
- [x] 2.3 Prueba primero, `asistencia/tests/test_vistas.py`: el selector dibuja `<a>` en los días disponibles con su `href`, `aria-current="date"` solo en hoy, el elegido con su resaltado y «abierto» en su nombre, «no disponible» en los demás, las flechas con o sin `href`, sin «Solo puedes marcar hoy.»; «Abrir el viernes desde el sábado» (reemplaza `test_el_selector_tiene_hoy_como_unico_dia_activo`). Luego `_selector.html` (D3). Verificar: rojo y luego verde; `uv run pytest src/backend/asistencia`
- [x] 2.4 `verificar.py` y commit (con los Critical e Important de Codex del grupo 1); luego `/codex:review --base <commit del grupo 1> --background`

## 3. Textos del día, periodo cerrado y navegador [riesgo: bajo]

- [ ] 3.1 Prueba primero, `asistencia/tests/test_vistas.py`: escenarios «Título de un día pasado» (título, `<title>`, `aria-label` de la lista, cabecera «Lunes 16»), «Fuera del registro del lunes 16», cierre «Asistencia del lunes 16 completa» con la jornada completa y `data-texto-cierre` en la raíz; hoy sigue con sus textos. Luego `texto_dia`, `hoy.html` y `_tarjeta.html` (D5). Verificar: rojo y luego verde; `uv run pytest src/backend/asistencia`
- [ ] 3.2 Prueba primero, `asistencia/tests/test_vistas.py` con `periodo_cerrado` parcheado: la lista con número, nombre, estado en palabras y nota, sin círculos, sin «Marcar los N restantes», sin campo de nota, sin `data-asistencia`, con «El periodo está cerrado. Solicita a la dirección que habilite la corrección»; marcar y restantes → 409 sin guardar. Luego la vista y la plantilla del periodo cerrado (D6). Verificar: rojo y luego verde; `uv run pytest src/backend/asistencia`
- [ ] 3.3 Prueba primero, `asistencia/tests/test_asistencia_e2e.py`: flujo de un día pasado (24 marcados en la base; abrir el lunes desde el selector, tocar al Faltó hasta Justificado, escribir «Constancia entregada a la docente», ver «✓ Asistencia del lunes 16 completa» y su anuncio una vez; en la base, la jornada del lunes con el estado y la nota). Luego `asistencia.js` lee `data-texto-cierre` (D5). Verificar: rojo y luego verde; solo este archivo e2e
- [ ] 3.4 Prueba primero, `asistencia/tests/test_asistencia_e2e.py`: axe y ancho del documento de las vistas «día pasado» y «periodo cerrado» (parcheado), en ambos temas a 360 y 1280 px (decisión 9). Verificar: verde; solo este archivo e2e
- [ ] 3.5 Pantallas vistas por Marco: día pasado, día olvidado, periodo cerrado y selector en la primera semana, en claro/oscuro y 360/1280 px. `verificar.py` y commit (con los Critical e Important de Codex del grupo 2)

## 4. Cierre

- [ ] 4.1 Recoger el resultado de Codex del grupo 2 y, como hay 3 grupos, correr `/codex:review --base main --background`; corregir sus Critical e Important con la prueba primero, en un commit corto. Verificar: `uv run python scripts/verificar.py --completo` y `-m e2e` completo, una sola vez, en verde
- [ ] 4.2 Catálogo de rutas de `docs/03` con `docente/secciones/<id>/asistencia/<fecha>/`. `verificacion.md`: DoD 1 a 9 y los escenarios sin prueba con su motivo (el «Caso de error» real va con US-026). Verificar: el archivo existe y cada escenario sin prueba tiene motivo; commit

## e2e a retirar

Para que Marco apruebe; no se borran sin su visto bueno. Retirar la variante de 1280 px exige cambiar también el requisito «Asistencia accesible y sin desplazamiento horizontal», que hoy pide los dos anchos.

- `test_la_lista_a_medio_marcar_pasa_axe`, `test_el_fin_de_semana_pasa_axe`, `test_la_seccion_sin_estudiantes_pasa_axe` y `test_las_vistas_de_la_parte_c_pasan_axe`: axe por variante a 360 y 1280 px; la regla pide un ancho (360) salvo que cambie la conducta (plan de poda: 28 casos → 14).

## Workflow follow-up

- **(deuda, US-026)** `periodo_cerrado` devuelve siempre falso: el «Caso de error» de US-031 (doc 02) y RN-022 se prueban de verdad con US-026.
- **(deuda, I.E.)** Nadie llena `fecha_estado`: un trasladado o retirado sin fecha sale de todos los días pasados. Pregunta a Nayely: quién registra traslados y retiros, y si hay sábados de recuperación.
- **(deuda, US-033)** Ingresos tardíos (RN-012, doc 09 §6): un estudiante agregado después aparece en días anteriores y deja esas jornadas incompletas. Codex (grupo 1, Minor): además se le puede guardar asistencia de esos días, por toque o con «Marcar los N restantes»; sin fecha de ingreso no se puede rechazar.
- **(deuda, Codex grupo 1, Minor)** Un reintento pendiente que cruza la medianoche ahora se acepta (el día anterior se abre) y puede pisar una marca más nueva de otra pestaña: es el «gana el último» que ya existe en el mismo día. Rechazarlo exige una versión de la marca en cada guardado.
- **(deuda, Codex grupo 2, Minor)** `se_puede_abrir` consulta el inicio del año (`inicio_del_anio`) en cada guardado de hoy aunque solo lo necesitan los días anteriores: una consulta de más por guardado. Hacerlo perezoso, solo para fechas anteriores a hoy.
- **(deuda)** Marcas pendientes de un día pasado con la sesión vencida: se pierden si la docente no vuelve a ese mismo día (D8).
- **(pulido final)** Deslizar entre días en el celular.
- **(equipo)** Push y PR hacia `main` (`Closes #N` de US-031, verificando el número). En «Para quien revise»: hoy se abre aunque sea antes del inicio del año (D1) y el periodo cerrado es solo un enganche (D6).
