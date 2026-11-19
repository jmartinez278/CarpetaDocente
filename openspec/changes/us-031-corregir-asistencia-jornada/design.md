# Design: US-031 – Corregir la asistencia de una jornada

## Context

- Decisiones cerradas en `insumos/US-031/decisiones.md` (1 a 9); sin bocetos. Lo nuevo de este propose está en `proposal.md`.
- `asistencia/servicios.py` ya recibe la fecha en `marcar` y `marcar_restantes` (D10 de US-030); `_validar_fecha` exige `fecha == hoy` y día de semana; `FechaNoValida` se traduce a 409 en `GuardadoMixin`. Las rutas de los guardados ya llevan `<fecha:fecha>`; `FechaConverter` da 404 a una fecha inexistente.
- `_activos(seccion)` filtra `estado=ACTIVO` y lo usan `marcar`, `marcar_restantes`, `_completa_o_vacia` y `_registrar_si_completa`. `lista_de_hoy` separa activos y no activos por `estado`. `pendiente_hoy` (portada) usa `_completa_o_vacia` con hoy.
- `Estudiante.fecha_estado` existe (nula) y nadie la llena todavía (zona de cuidado de decisiones.md).
- `AnioEscolar` no tiene fecha de inicio; `Periodo` tiene `numero`, `fecha_inicio` y `fecha_fin` (US-028). `Seccion.anio_escolar` apunta al año.
- `asistencia.js` se engancha a `[data-asistencia]`, guarda las marcas pendientes en `sessionStorage` con clave por fecha y anuncia «Asistencia de hoy completa» con texto fijo.
- `actividad.servicios` tiene una lista de claves permitidas por operación; ASISTENCIA_CAMBIADA admite `estudiante`, `anterior`, `nuevo`, `nota_cambiada` y `origen`.

## Riesgos y zonas delicadas (primero)

- **[Corregir un día ajeno o fuera de rango]** (permisos y datos) → D1 y D2: el acceso de la sección se comprueba antes que la fecha (`SeccionDocenteMixin` en `dispatch`), así una sección ajena da 403 aunque la fecha no valga. La fecha se valida en el servicio para los guardados (409) y en la vista para abrir (404), con la misma función.
- **[Activos de un día con `fecha_estado` vacía]** (zona de cuidado) → D4: un trasladado o retirado sin fecha no es activo en ningún día pasado; sale de la lista y del cálculo de completa. Si la I.E. registra los traslados sin fecha, sus jornadas pasadas se ven completas sin él. Deuda hasta saber quién registra los traslados.
- **[Una copia vieja revierte `fecha_estado`]** (deuda de US-008) → D9: `editar_estudiante` guarda solo apellidos y nombres.
- **[JORNADA_COMPLETA de un día pasado]** (registro) → D4: completa se calcula con los activos de la fecha de la jornada, no con los de hoy; si no, un retirado después dejaría la jornada pasada completa antes de tiempo o un activo nuevo la volvería incompleta (ingresos tardíos, RN-012: deuda a US-033).
- **[Periodo cerrado sin regla real]** (zona de cuidado) → D6: el enganche devuelve siempre falso; las pruebas lo parchean. La prueba real del caso de error va con US-026.
- **[Hoy antes del inicio del año]** → D1: hoy siempre se abre, como en US-030; el rango solo limita los días anteriores. Así un año ABIERTO cuyo periodo 1 empieza después de hoy no bloquea la asistencia de hoy.
- **[Marcas pendientes de un día pasado con la sesión vencida]** → D8: se mantiene D6 de US-030; deuda.

## Goals / Non-Goals

**Goals:**
- Una sola función decide qué fechas se abren y se guardan; la vista y los servicios la comparten.
- Ningún cambio de modelo ni migración.
- La pantalla de un día pasado es la misma plantilla que la de hoy, con sus textos.

**Non-Goals:**
- Bloqueo real por notas entregadas (US-026); historial e ingresos tardíos (US-033); feriados y sábados de recuperación; deslizar entre días.

## Decisions

### D1. Fechas que se abren
- `inicio_del_anio(anio_escolar)`: `fecha_inicio` del periodo 1 si existe; si no, el 1 de enero de `anio_escolar.anio`.
- `se_puede_abrir(seccion, fecha, hoy)`: `fecha == hoy` y día de clases, o día de clases con `inicio_del_anio(...) <= fecha < hoy`.
- `_validar_fecha` usa `se_puede_abrir`; sigue lanzando `FechaNoValida` (409).
- **Por qué hoy siempre**: conserva la conducta de US-030 aunque el año aún no empiece según sus periodos.

### D2. Ruta y vista
- `asistencia/<fecha:fecha>/` (GET, nombre `asistencia:dia`) y `asistencia/` (hoy) comparten una vista base que arma el contexto con `fecha` y `hoy`. Si la fecha no se puede abrir, `Http404`. Un sábado o domingo en la ruta da 404; «Hoy no hay clases» queda solo para `asistencia/` en fin de semana.
- `asistencia/<hoy>/` muestra lo mismo que `asistencia/`, sin redirección; el selector enlaza hoy a `asistencia/`.
- `url_marcar` y `url_restantes` del contexto llevan la fecha abierta.
- **Por qué sin redirección**: no hay dos pantallas que mantener y la URL con fecha sigue siendo válida al pasar la medianoche.

### D3. Selector
- `semana(abierto, hoy, inicio)` devuelve los cinco `Dia` con `es_hoy`, `elegido`, `disponible` y su URL, y las dos flechas con su URL o `None`.
- Cada día disponible es un `<a>`; uno no disponible sigue como hoy (atenuado, `aria-disabled`, «no disponible» en su nombre). Hoy conserva `aria-current="date"`; el día elegido usa el mismo resaltado y su nombre accesible termina en «abierto» (o «hoy» si es hoy).
- Flecha anterior: el mismo día de la semana una semana antes; si cae antes del inicio, el primer día de clases desde el inicio; sin días disponibles en la semana anterior, desactivada. Flecha siguiente: el mismo día una semana después, o hoy si se pasa; desactivada en la semana de hoy.
- En fin de semana (`asistencia/` un sábado o domingo) la semana es la que acaba de pasar, sin día elegido, y las flechas toman el viernes como día de referencia.
- Se quita «Solo puedes marcar hoy.».

### D4. Activos de un día
- `activos_del_dia(seccion, fecha)`: `estado=ACTIVO` o (`estado` en TRASLADADO o RETIRADO y `fecha_estado > fecha`). Reemplaza a `_activos` en `marcar`, `marcar_restantes`, `_completa_o_vacia` y `_registrar_si_completa` (este con `jornada.fecha`).
- `lista_de_hoy` pasa a `lista_del_dia(seccion, fecha)`: filas con los activos del día y `no_activos` con el resto, en el orden de `estudiantes_ordenados`.
- `pendiente_hoy` sigue con hoy; cambia solo porque usa la misma regla de activos.

### D5. Textos del día abierto
- `texto_dia(fecha)` → «lunes 16 de noviembre». Con `fecha != hoy`: título «Asistencia del lunes 16 de noviembre», `<title>` y `aria-label` de la lista con el mismo texto, cabecera «Lunes 16», «Fuera del registro del lunes 16» y cierre «Asistencia del lunes 16 completa».
- El JS lee el texto del anuncio del cierre de `data-texto-cierre` en la raíz; deja de tenerlo fijo.
- **Por qué «del lunes 16» en «Fuera del registro»**: decisiones.md no lo fija; se usa la misma forma corta que el cierre.

### D6. Periodo cerrado (enganche)
- `periodo_cerrado(seccion, fecha)` en `asistencia/servicios.py` devuelve `False`; US-026 le pone la regla. `marcar` y `marcar_restantes` lanzan `PeriodoCerrado` (subclase de `FechaNoValida`) si es verdadero, antes de tocar la base: el guardado responde 409 y el JS recarga, como con una fecha no válida.
- La vista pasa `periodo_cerrado` a la plantilla: filas con número, nombre y estado en palabras (y la nota si la hay), sin círculo, sin «Marcar los N restantes», sin campo de nota, con el aviso del spec, y sin `data-asistencia`, así el JS no se engancha.
- **Por qué subclase**: el 409 y la recarga ya existen; US-026 no toca el JS.

### D7. Corrección en el registro de actividad
- `_registrar_cambio` agrega `correccion: True` al detalle solo si `jornada.fecha != hoy`; de hoy no lleva la clave. `correccion` entra en la lista permitida de ASISTENCIA_CAMBIADA.
- **Dato de la tesis**: `RegistroActividad.detalle["correccion"]` de ASISTENCIA_CAMBIADA cuenta las correcciones de días pasados (D3); `Asistencia.actualizado_en` guarda cuándo.

### D8. Marcas pendientes en el dispositivo
- Sin cambios: la clave ya lleva la fecha; abrir un día descarta las de otros días (D6 de US-030). Con la sesión vencida en un día pasado, si la docente no vuelve a ese mismo día, se pierden: deuda.

### D9. `editar_estudiante` con `update_fields`
- `_guardar_estudiante` recibe los campos a guardar; `editar_estudiante` pasa `["apellidos", "nombres"]`. `save(update_fields=...)` sin filas afectadas lanza `DatabaseError`, que ya se traduce a `Estudiante.DoesNotExist`.

### D10. Pruebas en navegador
- Tres e2e nuevas: el flujo de un día pasado (abrir desde el selector, Faltó a Justificado con nota, cierre con el texto del día y su anuncio), axe del día pasado y axe del periodo cerrado, ambas en los dos temas a 360 y 1280 px por la decisión 9 de decisiones.md. Rutas, enlaces, flechas, textos, 404 y 409 van como pruebas de vista.

## Risks / Trade-offs

- [Un trasladado con `fecha_estado` vacía desaparece de los días pasados] → se acepta (decisión 6); deuda hasta que la I.E. diga quién registra los traslados.
- [Un estudiante agregado después aparece en días anteriores y deja esas jornadas incompletas] → se acepta; US-033 (RN-012).
- [El axe a 1280 de las vistas nuevas va contra la regla de un ancho] → lo pide la decisión 9 y el spec; las e2e de 1280 existentes se listan como «a retirar» para que Marco decida junto con el spec.
