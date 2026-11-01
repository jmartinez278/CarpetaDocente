# Design: US-029 – Marcar las competencias desarrolladas en el periodo

## Context

- Decisiones de alcance cerradas en `insumos/US-029/decisiones.md` (1 a 17 y zonas de cuidado); lo nuevo está en `proposal.md`. Interfaz: prototipo aprobado `insumos/prototipo/US-029-bocetos/` (`demo.html`, `decisiones-no-cubiertas.md`, `notas.md`); su `localStorage` no se copia.
- `notas` existe en `INSTALLED_APPS`, vacía y sin migraciones. `calificacion` no existe.
- `catalogo`: `Area` (orden SIAGIE en `orden`), `Competencia` (`activa`, orden por `area__orden, orden`), `InstitucionArea` (`se_trabaja`). `InstitucionAreaAdmin` usa `RegistraEnPanel` (CATALOGO_EDITADO con los campos) y `list_editable`.
- `institucion`: `Periodo` (número 1–4, fechas, sin estado), `periodo_vigente(origen, fecha)` en hora de Lima, `secciones_docente` (solo año ABIERTO) y `SeccionDocenteMixin` (404 fuera de eso). `RolRequeridoMixin` responde `HX-Redirect` a una petición con `HX-Request` sin sesión.
- `actividad.servicios.registrar` exige una transacción abierta y valida el detalle contra `DETALLE_PERMITIDO`; la `CheckConstraint` de operaciones obliga a migrar al agregar una.
- Asistencia (US-030) es el patrón de pantalla: el servidor dibuja todo, un JS propio sin HTMX ni Alpine agrega el comportamiento, las vistas responden sin cuerpo y las clases viven en `src/frontend/css/app.css`.

## Riesgos y zonas delicadas (primero)

- **[Borrar marcas ajenas]** → un guardado del conjunto «completo» borraría las marcas de áreas del docente de curso (historia futura) o de competencias desactivadas. D5: el guardado compara y borra solo dentro del universo que la tutora puede marcar.
- **[Dos guardados a la vez]** → dos pestañas podrían mezclar conjuntos o chocar con la UQ. D5: la fila de la sección se bloquea (`FOR UPDATE`) antes de leer las marcas; la UQ queda como red. Prueba con hilos (`transaction=True`).
- **[Obligatorias que el cliente omite]** → D7: el servidor las calcula y las agrega siempre; el envío no decide.
- **[`tiene_notas` sin notas reales]** (zona de cuidado) → D6: devuelve `False`; las pruebas del caso de error la parchean. US-020 la completa.
- **[Año CERRADO]** → D8: la pantalla usa `SeccionDocenteMixin`, como asistencia: la sección de un año CERRADO es 404 en GET y POST. El servicio vuelve a rechazar el guardado (D5) como defensa. Consultar las marcas de un año cerrado va a la deuda (US-009 / historial).
- **[Migraciones]** → `notas/0001` (tabla nueva), `catalogo/0003` (columna booleana con valor por defecto, sin tocar datos) y la de `actividad` (choices y `ck_actividad_operacion`). La migración no sabe cuál es Virgen del Carmen: no pone `a_cargo_docente_curso` en ninguna fila (zona de cuidado).
- **[Desmarcar = DELETE]** (zona de cuidado) → la fila es una marca, no una nota ni una competencia (decisión 6). Contradicción con el doc 08 a la deuda.
- **[Borradores en memoria]** → recargar, cerrar o una sesión vencida los pierden; `beforeunload` y el diálogo de salida avisan (decisión 16). Guardarlos en `sessionStorage` va a la deuda.
- **[Demo y descarte borran marcas]** (decisión 11) → `_borrar` de `demo.py` las borra con lo demás, en la misma transacción; se cuentan en el resumen.

## Goals / Non-Goals

**Goals:**
- Toda regla y toda escritura de marcas en `notas/servicios.py`; las vistas leen la petición y llaman al servicio.
- `puede_marcar`, `tiene_notas` y `competencias_obligatorias` como únicos puntos que US-020 y la historia de docentes de curso cambian, sin tocar el modelo.
- La pantalla del prototipo con la persistencia real: un POST por guardado, todo o nada.

**Non-Goals:**
- Tarjeta o enlace desde la portada (la bandera de Notas no cambia).
- Marcas de los docentes de curso, ni una pantalla para ellos.
- Recuperar borradores después de recargar o de una sesión vencida.
- Reglas de entrega (RN-022) o exoneración (RN-010).

## Decisions

### D1. Modelo `CompetenciaPeriodo` (`notas/models.py`, migración `0001`)

- `db_table="competencia_periodo"`; `seccion` FK `institucion.Seccion` `CASCADE` y `periodo` FK `institucion.Periodo` `CASCADE`, ambas con `related_name="competencias_periodo"`; `competencia` FK `catalogo.Competencia` `RESTRICT`. `UniqueConstraint(fields=["seccion", "periodo", "competencia"], name="uq_competencia_periodo")`, que también sirve de índice para leer las marcas de una sección y periodo.
- Que la sección y el periodo sean del mismo año lo comprueba el servicio (D5): la base no puede sin una FK compuesta.
- **Alternativa descartada:** una fila «periodo guardado» por sección y periodo para distinguir «nunca guardado» de «guardado vacío»: el doc 11 no la tiene; se resuelve con D5.

### D2. `a_cargo_docente_curso` (`catalogo/models.py`, migración `0003`)

- `BooleanField("a cargo del docente de curso", default=False, db_default=False)` en `InstitucionArea`: el `DEFAULT false` queda en la base, así el despliegue anterior inserta sin la columna mientras Vercel migra (A2). `asegurar_areas` no cambia (el valor por defecto basta).
- Panel: el campo entra en `fields`, `list_display` y `list_editable` de `InstitucionAreaAdmin`; `RegistraEnPanel` ya deja CATALOGO_EDITADO con el nombre del campo.
- No hay restricción con `se_trabaja`: un área que no se trabaja no aparece, tenga o no la marca.

### D3. Lo que ve y marca la tutora (`notas/servicios.py`)

- `puede_marcar(usuario, seccion, area_institucion)`: cuenta con rol Docente, docente de la sección, área que la institución trabaja y no a cargo del docente de curso. Es lo único que decide (decisión 13); no mira el año ni el periodo (eso es D4 y D5).
- `areas_de_la_seccion(usuario, seccion)`: las `InstitucionArea` con `se_trabaja` de la institución del año, por `area__orden`, con sus competencias activas (`Prefetch` ordenado por `orden`), y por área `a_cargo` y `marcable` (de `puede_marcar`). Dos consultas.
- `universo(usuario, seccion)`: los id de las competencias activas de las áreas marcables. Es el conjunto que el guardado compara, valida y borra (D5).

### D4. Periodos (`periodos_de_la_seccion(seccion, hoy)`)

- Todos los periodos del año por número, cada uno con `estado` (VIGENTE si `periodo_vigente` es él; ANTERIOR si `fecha_fin < hoy`; FUTURO si `fecha_inicio > hoy`), su nombre corto (B o T según `organizacion_periodos`, y el número) y `editable` = año ABIERTO y `fecha_inicio <= hoy` (con año CERRADO, ninguno; la pantalla no llega a pedirlos, D8).
- Casos de la pantalla (spec «Sin periodo para marcar»): sin periodos; sin vigente con algún anterior (hueco); sin vigente ni anterior (antes del primero, con la fecha de inicio del periodo 1).
- `hoy` es `timezone.localdate()` en la vista; el servicio lo recibe para que las pruebas fijen la fecha.

### D5. Guardado: `guardar_marcas(usuario, seccion, numero, ids, *, visto)`

En `transaction.atomic()`:

1. La sección con `select_for_update()` y su año. Año CERRADO → `PeriodoNoMarcable`.
2. El periodo del año por `numero` (`Periodo.DoesNotExist` si no hay). `fecha_inicio > hoy` → `PeriodoNoMarcable`.
3. `visto` (el universo que mostró la pantalla, que el JS devuelve en el POST) distinto del `universo` de ahora, o `ids` fuera del `universo` → `ValidationError(CONJUNTO_NO_VALIDO)`. Sin esa comparación, una competencia reactivada con la pantalla abierta no viene en el envío y el paso 5 borraría su marca (A2).
4. `nuevo = ids ∪ competencias_obligatorias(...)` (D7). Vacío → `ValidationError(SIN_MARCAS)` («Marca al menos una competencia para guardar.»): sin una fila de «periodo guardado» (D1), guardar vacío dejaría el periodo como si nunca se hubiera guardado y volvería a abrir con todo marcado (decisión 4).
5. `existentes` = las marcas del periodo dentro del `universo`. `quitadas = existentes − nuevo`; si alguna `tiene_notas` → `CompetenciaConNotas(ids)` con `MENSAJE_CON_NOTAS`, sin guardar nada.
6. `agregadas = nuevo − existentes`: `bulk_create`; `quitadas`: `delete()`. Si hubo cambios, COMPETENCIAS_MARCADAS (D10).

Devuelve `CambiosMarcas(agregadas, quitadas)`. Repetir el envío da conjuntos vacíos y no registra (idempotente). Las marcas fuera del `universo` no se leen ni se borran (riesgo «Borrar marcas ajenas»).

- **Alternativa descartada:** borrar todas las marcas del periodo y crear el conjunto: borra marcas ajenas, deja entradas de actividad aunque nada cambie y abre una ventana sin marcas.
- **Alternativa descartada:** un POST por casilla (como asistencia): la decisión 5 pide un solo envío con el conjunto.

### D6. `tiene_notas(seccion, periodo, competencia)`

- Devuelve `False` (decisión 7) y es el único lugar que lo sabe: la usan el guardado (D5) y la pantalla para el motivo «Con notas registradas». Las pruebas la parchean para el caso de error.
- La pantalla la llama una vez por competencia y periodo editable (hasta 4 × 21): hoy sin consultas. Si con `calificacion` pesa, US-020 la resuelve dentro de la función (por ejemplo, con una lectura por periodo en caché de la petición), sin cambiar quién la llama.

### D7. Obligatorias del último periodo: `competencias_obligatorias(usuario, seccion, periodo)`

- Si el año está ABIERTO y `periodo.numero` es el mayor de los periodos del año: `universo − {marcadas en la sección en periodos de número menor}`. Si no, vacío. Una consulta más el `universo`.
- Las usa la pantalla (marcadas y bloqueadas, «Debe tener nivel al cerrar el año») y el guardado (se agregan siempre).
- US-020 la afina con las notas («sin nivel en ningún periodo», decisión 8) sin cambiar quién la llama.

### D8. Rutas y vistas (`notas/urls.py`, `notas/views.py`)

- En `config/urls.py`: `docente/secciones/<int:seccion_id>/competencias/` → `include("notas.urls")`, namespace `competencias`. `""` GET (`CompetenciasView`, nombre `pantalla`) y `<int:numero>/` POST (`GuardarView`, nombre `guardar`).
- Las dos vistas usan `SeccionDocenteMixin` (US-006, D4), como asistencia: sección de otra docente o de un año CERRADO → 404 en GET y POST, antes de llegar al servicio; otro rol y sin sesión, `RolRequeridoMixin`.
- GET acepta `?periodo=N` para abrir un periodo elegible; si no lo es, abre el vigente (o ninguno). La vista arma el contexto con D3, D4, D6 y D7 y lo pasa también como `json_script` por periodo: número, nombre, estado, fechas, `editable`, `marcadas` (o `null` si el periodo no tiene marcas dentro del universo), `con_notas` y `obligatorias`.
- POST: `competencia` repetido (enteros; si no, 400), con CSRF y `HX-Request` (para el `HX-Redirect` de sesión vencida). Respuestas: 204 guardado; 400 con `{"mensaje"}` (conjunto no válido o vacío); 404 periodo o sección; 409 con `{"mensaje"}` (periodo futuro) o `{"mensaje", "competencias"}` (con notas).
- **Alternativa descartada:** una página por periodo con recarga: los borradores por periodo de la decisión 15 se perderían al cambiar de bimestre.

### D9. Pantalla (`templates/notas/competencias.html`, `static/js/competencias.js`)

- El servidor dibuja la lista una vez (las competencias son las mismas en todos los periodos) con el estado del periodo inicial; sin JavaScript se ve la lista y el aviso «Activa JavaScript para guardar las competencias.», como asistencia.
- `competencias.js` (sin HTMX ni Alpine) lee el `json_script` y guarda por periodo `{guardado, borrador}`. Hace: cambio de periodo sin recarga (`aria-pressed` y «Sin guardar» en el botón con borrador distinto), cápsula de áreas bajo 960 px (`matchMedia`; recuerda el área al cambiar de periodo y de ancho), casillas bloqueadas con `aria-disabled` que anuncian el motivo en `role="alert"`, «Deshacer cambios» contra lo guardado o el estado inicial (las obligatorias no cuentan), Guardar con `fetch` y los estados del prototipo (anuncio en `role="status"`, error junto al botón), el `<dialog>` «¿Salir sin guardar?» en los enlaces y formularios que salen de la pantalla (incluido «Cerrar sesión») y `beforeunload` mientras haya borradores.
- Con 409 «con notas», las competencias de la respuesta vuelven a marcarse y quedan bloqueadas con su mensaje. Con `HX-Redirect`, el aviso de sesión vencida con el enlace al ingreso.
- Textos tal como el prototipo (`decisiones-no-cubiertas.md`). Clases en `src/frontend/css/app.css` con los tokens de `DESIGN.md`, sin colores nuevos: el gris de las áreas de curso es el token de Justificado (decisión del prototipo).

### D10. Registro de actividad

- `Operacion.COMPETENCIAS_MARCADAS` («Competencias marcadas»), fuera de `CUENTAN_KPI_01`. `DETALLE_PERMITIDO`: `{"periodo", "agregadas", "quitadas"}` (número del periodo y listas ordenadas de id de competencia: RN-015). Entidad `seccion` y el id de la sección.
- `DEMO_QUITADA` y `SECCION_DESCARTADA` suman la clave `marcas` (D11).

### D11. Demo (`institucion/demo.py`)

- `notas.servicios.marcar_todo_sin_registro(seccion, periodos)`: para cada periodo sin marcas de la sección, crea las del `universo` de su docente. Sin entrada propia: la carga deja su DEMO_CARGADA (como `importar_lista_sin_registro`).
- `cargar_demo` la llama al final, después de `guardar_periodos`, para las secciones cargadas y las ya cargadas, con los periodos de `fecha_inicio <= hoy`. No toca `a_cargo_docente_curso` (proposal).
- `_borrar` borra las marcas de las secciones antes que los estudiantes; `Conteos` suma `marcas` y su texto las nombra.

### D12. Datos de la tesis

- No hay indicador que se mida con esta historia: COMPETENCIAS_MARCADAS no cuenta para KPI-01. Las marcas quedan en `competencia_periodo` (sección, periodo, competencia), que US-020 y US-022 leen para «secciones con notas» y completitud.

## Migration Plan

- Tres migraciones sin datos: `notas/0001`, `catalogo/0003` y la siguiente de `actividad`. Se aplican en local, en la CI y en el build de la vista previa de Vercel (Neon).
- Después de la fusión, el Administrador marca Educación Física e Inglés de Virgen del Carmen como «a cargo del docente de curso» en el panel (fuente: decisión 12). Reversión: las migraciones se revierten sin pérdida, salvo las marcas guardadas.
