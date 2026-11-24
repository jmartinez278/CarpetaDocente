# Tasks

Cuatro bloques (zona de cuidado «Tamaño»), cada uno en verde antes del siguiente. Los bloques 3 y 4 se parten en grupos por riesgo; cada grupo es un commit.

# Bloque 1 · DESIGN.md 1.2, Pizarra neutra y botón de tema

## 1. DESIGN.md 1.2, tokens y T-04 [riesgo: alto]

- [x] 1.1 Aplicar `prototipos-cd/US-040-final/enmienda-design.md` a `DESIGN.md` (1.1 → 1.2, fecha 23-11-2026, café oscuro `#493B34`) y actualizar `.claude/rules/plantillas.md` (Besley en los cuatro lugares de 1.2; el botón de tema ya existe; referencia a 1.2) (D1). Verificar: el diff de `DESIGN.md` coincide con la enmienda sección por sección y ninguna línea de `plantillas.md` contradice 1.2
- [x] 1.2 Prueba primero, `cuentas/tests/test_plantillas.py`: `base.html` carga `js/tema.js` en `<head>` antes de `dist/app.css` y sin `defer`; `marco.html` pinta el botón `[data-tema]` antes del menú de la cuenta, con «Cambiar a tema oscuro»; `ingresar.html` lo lleva; una página de `/admin/` no; ninguna plantilla con hex ni `style=`. Luego `static/js/tema.js`, `rb/boton_tema.html` (íconos sol y luna de Lucide en `templates/iconos/`) y su lugar en `base.html`, `marco.html` e `ingresar.html` (D1). Verificar: rojo y luego verde; `uv run pytest src/backend/cuentas`
- [x] 1.3 Tokens de Pizarra neutra en `src/frontend/css/rebrand/tokens.css` (los dos bloques oscuros), `--tipografia-nombre`, papel atenuado limitado a miniaturas y vistas previas, y estilos del botón de tema (44 px, hover `--sel-bg`, foco pegado) y del ingreso (arriba a la derecha) (D1). Verificar: `npm run build` sin errores y Marco ve ingreso, portada, Asistencia, Notas y Sesiones en oscuro a 360 y 1280 px
- [x] 1.4 Prueba primero, `cuentas/tests/test_tema_e2e.py` (nuevo): con el sistema en claro, «Cambiar a tema oscuro» pone `data-theme=dark`, el botón pasa a «Cambiar a tema claro» y tras recargar sigue oscuro sin pasar por claro (primer `data-theme` antes de `DOMContentLoaded`); sin elección, emular `prefers-color-scheme: dark` cambia el nombre del botón; con dos páginas del mismo contexto, la elección en una llega a la otra. Verificar: rojo y luego verde; solo este archivo e2e
- [x] 1.5 Borrar las 8 e2e de «e2e retiradas» y quitar la pantalla `direccion` de `test_el_documento_no_se_desplaza_en_horizontal` y `test_el_menu_abierto_no_desborda_la_ventana` (pasa a 4.3). El repaso de axe en oscuro de todas las pantallas (Pizarra neutra, zona de cuidado) va en el `-m e2e` completo del cierre (8.1). `verificar.py` y commit. Verificar: `uv run pytest src/backend/cuentas` y el e2e de 1.4 en verde

# Bloque 2 · Portada aprobada de la docente

## 2. Portada de la docente con el calendario de Asistencia [riesgo: alto]

- [x] 2.1 Prueba primero, `cuentas/tests/test_pantallas.py`: la línea de la sección ya no lleva la fecha («2.º grado, sección A»; varias; sin sección); la miniatura dice «Lunes», «23», «noviembre» y la fecha completa una sola vez para el lector; «18 de 25 estudiantes marcados» con `<progress>`; «Día sin clases» en sábado; «Sin estudiantes»; «Registro no disponible» con varias secciones o ninguna; «Hoy: pendiente» sigue igual. Luego el contexto de `PortadaDocenteView` y `rb/miniatura_asistencia.html` (D10). Verificar: rojo y luego verde; `uv run pytest src/backend/cuentas`
- [x] 2.2 Saludo con el nombre en Besley 600 (`--tipografia-nombre`) y precarga de Besley en la portada; estilos de la miniatura calendario según `miniatura-asistencia-exploracion` (D10). Verificar: `npm run build` y Marco ve la portada en claro/oscuro a 360 y 1280 px
- [x] 2.3 Prueba primero, `cuentas/tests/test_portada_e2e.py`: axe y ancho del documento de la portada con el calendario (con avance y sin sección) en ambos temas a 360 px. `verificar.py` y commit. Verificar: rojo y luego verde; solo este archivo e2e

# Bloque 3 · Portada y ☰ de la dirección

## 3. Estado de las secciones y asistencia por periodo [riesgo: alto · opus]

Razón: el estado cruza notas faltantes (competencias marcadas, áreas del docente de curso, estudiantes activos), días sin completar (días de clase, hoy, activos del día con `fecha_estado`) y el periodo elegido (anterior, vigente, futuro, sin periodos); de él dependen el mapa, el resumen, la portada y el detalle (RNF-017).

- [x] 3.1 Prueba primero, `notas/tests/test_servicios.py`: `faltantes_por_seccion` da lo mismo que la suma de `notas_faltantes` con la tutora en cada área, en una sección con faltantes, un trasladado, un área del docente de curso y una competencia inactiva; sección sin docente → 0; total de celdas para «N de M registradas»; distribución AD/A/B/C por área. Luego las funciones por lote en `notas/servicios.py` (D3). Verificar: rojo y luego verde; `uv run pytest src/backend/notas`
- [x] 3.2 Prueba primero, `asistencia/tests/test_servicios.py`: `dias_de_clase`; `dias_sin_completar_por_seccion` con día sin jornada, jornada incompleta, jornada completa, hoy incompleto (no cuenta), un retirado antes del día (no cuenta), periodo terminado (hasta su fin); `totales_por_estudiante` y `totales_de_la_seccion` (8/0/2/1 → 72,7 %; sin marcas → «—»); promedio ponderado (25 × 90,0 y 15 × 100,0 → 93,8); el escenario RNF-017 con 3 secciones y un periodo completo comparado con el recuento de filas. Luego las funciones (D5). Verificar: rojo y luego verde; `uv run pytest src/backend/asistencia`
- [x] 3.3 Prueba primero, `direccion/tests/test_servicios.py` (nuevo, con `conftest.py`): `periodos_del_anio` y el periodo elegido (vigente; anterior pedido; futuro pedido → vigente; entre periodos; antes del primero; sin periodos); `estado_de_las_secciones` con los cuatro estados y su prioridad, orden por grado y nombre, solo año ABIERTO de la institución; `resumen_de_la_ie` (9 de 22, nota del pie, «Faltan N días para el cierre» / «Terminado»); tope de consultas con 24 secciones. Luego `direccion/servicios.py` (D3, D4). Verificar: rojo y luego verde; `uv run pytest src/backend/direccion src/backend/notas src/backend/asistencia`
- [x] 3.4 `verificar.py` y commit; luego el revisor (subagente, contexto limpio, con modelo opus al llamarlo) sobre `<commit del grupo 2>..HEAD`

## 4. Portada de la dirección y ☰ [riesgo: alto]

- [x] 4.1 Prueba primero, `cuentas/tests/test_dimensiones.py` y `test_marco_rebrand.py`: `navegacion_direccion` (orden, Entregas sin URL, Consolidados actual en `direccion:*` salvo inicio); el ☰ de un interior de la dirección enlaza sin JS a `/direccion/`; el de la docente sigue igual. Luego `navegacion_direccion`, la etiqueta `menu_navegacion` y `url_inicio` en `menu_navegacion.html` (D8). Verificar: rojo y luego verde; `uv run pytest src/backend/cuentas`
- [x] 4.2 Prueba primero, `direccion/tests/test_vistas.py`: escenarios de «Inicio de la dirección» (saludo, línea con el bimestre o con la I.E., banda enlazada entera a Consolidados, «13 secciones por revisar» / «1 sección por revisar» / sin pastilla con 0, sin bimestres, antes del primero, miniatura con la fecha y una casilla por sección con su estado, Entregas sin enlace, botón con `data-abrir-plantilla` y `aria-haspopup="dialog"`); barra sin ☰ con tema y cuenta. Luego la vista, `direccion/inicio.html` y los estilos `dir-` de la portada, con Besley en el nombre y en el día (D9). Reemplaza las pruebas del estado vacío del inicio de la dirección. Verificar: rojo y luego verde; `uv run pytest src/backend/direccion src/backend/cuentas src/backend/exportaciones`
- [x] 4.3 Prueba primero, `direccion/tests/test_direccion_e2e.py` (nuevo): axe y ancho de la portada de la dirección (con y sin bimestres) y del ☰ de la dirección abierto, en ambos temas a 360 px; `exportaciones/tests/test_plantilla_siagie_e2e.py` abre el diálogo desde «Completar plantilla del SIAGIE». Verificar: rojo y luego verde; solo estos archivos e2e
- [x] 4.4 Pantallas vistas por Marco: portada de la dirección (con y sin bimestres) y ☰ abierto, claro/oscuro, 360/1280 px. `verificar.py` y commit (con los Critical e Important del revisor del grupo 3)

# Bloque 4 · Consolidados y detalle de sección

## 5. Acceso de la dirección y sesiones visibles [riesgo: alto]

- [ ] 5.1 Prueba primero, `repositorio/tests/test_servicios.py`: `sesion_visible_direccion` (propia no compartida de su institución → sí; de otra institución, de referencia, inexistente, id no UUID → `None`; una docente con esa función → `None`); `entregar_archivo` con la puerta de la dirección deja SESION_DESCARGADA con `propia: false`; `sesion_visible` sigue negando a la dirección. Luego las funciones (D7). Verificar: rojo y luego verde; `uv run pytest src/backend/repositorio`
- [ ] 5.2 Prueba primero, `direccion/tests/test_servicios.py`: `sesiones_de_la_seccion` (tutora para su grado; tutora para otro grado, fuera; sesión de varios grados que cubre el de la sección; sesión de Inglés del grado, fuera; colega tutora de otra sección del mismo grado, fuera; material de referencia, fuera; fecha de envío de Lima al borde de medianoche; fuera del periodo, fuera) y días con sesión de la tutora («9 de 11»); `sesiones_de_curso_del_grado` (Inglés del grado, dentro; Inglés de otro grado, fuera; área que no es del docente de curso, fuera) con autor, área y «N días con sesión · Última: <fecha>»; semana, flechas y día por defecto solo con las de la sección (un día con solo una sesión de curso no es el día por defecto) (D6). Luego las dos funciones. Verificar: rojo y luego verde; `uv run pytest src/backend/direccion`
- [ ] 5.3 Prueba primero, `direccion/tests/test_vistas.py` y `cuentas/tests/test_matriz_permisos.py`: `DireccionMixin` y `seccion_de_la_direccion` (otra institución, año CERRADO o inexistente → 404); las filas de la dirección en la matriz (dirección propia, de otra institución, docente, Administrador, sin sesión; solo GET) y su prueba de cobertura de rutas; los guardados de notas, competencias y asistencia enviados por la dirección no guardan nada (Caso de error de US-040). Prueba primero, `repositorio/tests/test_vistas.py` (o el archivo de la página de la sesión): la página de la docente conserva sus datos, migas, total de vistas y acciones de autora. Luego extraer `repositorio/_pagina_sesion.html` de la página de la docente (sin copiar marcado), `direccion/urls.py` con las rutas de D2 (vistas mínimas) y la página de la dirección que incluye la parcial, sin Eliminar ni Compartir, sin `registrar_vista` y con «Volver a Consolidados» (D2, D7). Verificar: rojo y luego verde; `uv run pytest src/backend/direccion src/backend/cuentas src/backend/repositorio`
- [ ] 5.4 `verificar.py` y commit; luego el revisor (subagente, contexto limpio) sobre `<commit del grupo 4>..HEAD`

## 6. Consolidados y detalle Notas y Asistencia [riesgo: alto]

- [ ] 6.1 Prueba primero, `direccion/tests/test_vistas.py`: escenarios de «Mapa de secciones», «Resumen de la I.E.» y «Bimestre de los consolidados» (celdas con texto, nombre accesible y enlace o sin enlace; 6.º D a Sesiones; tira con enlaces GET, futuro sin enlace; sin bimestres y antes del primero sin mapa ni café; barra con ☰ y «Consolidados»). Luego la vista y `direccion/consolidados.html` con sus estilos (D3, D4). Verificar: rojo y luego verde; `uv run pytest src/backend/direccion`
- [ ] 6.2 Prueba primero, `direccion/tests/test_vistas.py`: «Detalle de una sección» y «Pestaña Notas» (cabecera, pestañas como enlaces con la activa marcada, tabla por área con «Ninguna» y «Sin competencias marcadas», tira de áreas, hoja sin campos ni «Guardar», «Todos / Pendientes N» por GET con el título «Pendientes · <área>», café con «N de M registradas», mismos números que la celda del mapa; sin estudiantes → 302 a Sesiones con las pestañas desactivadas). Luego la vista y la plantilla de Notas (D2, D3). Verificar: rojo y luego verde; `uv run pytest src/backend/direccion`
- [ ] 6.3 Prueba primero, `direccion/tests/test_vistas.py`: «Pestaña Asistencia» (días de clase, totales y % por estudiante, café con los cuatro totales y «Todos los días completos» / «N días sin completar», mismos días que la celda). Luego la vista y la plantilla (D5). Verificar: rojo y luego verde; `uv run pytest src/backend/direccion`
- [ ] 6.4 Pantallas vistas por Marco: Consolidados (con y sin bimestres) y Notas (Todos y Pendientes) y Asistencia del detalle, claro/oscuro, 360/1280 px. `verificar.py` y commit (con los Critical e Important del revisor del grupo 5)

## 7. Detalle Sesiones y navegador [riesgo: medio]

- [ ] 7.1 Prueba primero, `direccion/tests/test_vistas.py`: «Pestaña Sesiones» (semana y días con el número de la sección y «sin sesiones», flechas por GET, día por defecto, sin chips, tarjetas de US-011 que enlazan a `direccion:sesion` sin «Mis sesiones», café solo de la tutora; 6.º D con su café que explica la sección sin estudiantes) y «Docentes de curso del grado» (título «Docentes de curso de 2.º grado · lunes 23» con el día elegido, docente con área y «N días con sesión · Última», sus tarjetas del día, sin bloque si no hay; «No se atribuye a la sección»: día punteado con tarjeta de curso debajo y café sin cambio). Luego la vista y la plantilla, reutilizando `repositorio/_tarjeta` con el `href` de la dirección (D6). Verificar: rojo y luego verde; `uv run pytest src/backend/direccion src/backend/repositorio`
- [ ] 7.2 Prueba primero, `direccion/tests/test_direccion_e2e.py`: flujo principal (portada → banda → Consolidados → celda de 2.º A → Notas → Pendientes → Asistencia → Sesiones → abrir una sesión); axe y ancho del documento de Consolidados y del detalle en Notas, Asistencia y Sesiones, en ambos temas a 360 px (D11). Verificar: rojo y luego verde; solo este archivo e2e
- [ ] 7.3 Pantallas vistas por Marco: Sesiones del detalle, 6.º D y la página de una sesión de la dirección, claro/oscuro, 360/1280 px. `verificar.py` y commit

## 8. Cierre

- [ ] 8.1 Correr el revisor (subagente, contexto limpio) solo sobre `views.py`, `urls.py` y `servicios.py` de los grupos sin revisor (1, 2, 4, 6 y 7), buscando permisos; corregir sus Critical e Important con la prueba primero, en un commit corto. Verificar: `uv run python scripts/verificar.py --completo` y `-m e2e` completo, una sola vez, en verde
- [ ] 8.2 Catálogo de rutas de `docs/03` con las rutas de D2 y el cambio de `/direccion/`. `verificacion.md`: DoD 1 a 9 y los escenarios sin prueba con su motivo. Verificar: el archivo existe y cada escenario sin prueba tiene motivo; commit

## e2e retiradas (aprobadas por Marco el 23-11-2026)

Se borran en la tarea 1.5. Todas miden valores de CSS o repiten 1280 px sin cambio de conducta (rules de tasks).

- `cuentas/tests/test_portada_e2e.py`: `test_las_miniaturas_llevan_el_mismo_papel_en_los_dos_temas` (además contradice el papel atenuado de 1.2), `test_los_tokens_aplicados_toman_su_valor_del_tema`, `test_el_saludo_hereda_la_altura_de_linea_del_titulo`, `test_la_pildora_no_tiene_animacion`, `test_en_asistencia_el_boton_va_debajo_de_la_miniatura`, `test_la_barra_de_la_portada_no_es_una_franja_ni_se_queda_fija`, `test_a_1280_asistencia_ocupa_la_columna_principal`.
- `cuentas/tests/test_accesibilidad_e2e.py`: `test_el_nombre_de_la_ie_mide_40_px_en_pc_y_30_en_celular`.
- La pantalla `direccion` de `test_el_documento_no_se_desplaza_en_horizontal` y `test_el_menu_abierto_no_desborda_la_ventana` pasa a las e2e nuevas de la portada de la dirección (4.3).

## Workflow follow-up

- **(deuda, docs)** T-04 sin RF en el doc 06 (congelado): pasada de docs.
- **(deuda, US-026)** El «Caso de error» de US-040 no tiene interfaz: se prueba con los guardados enviados a mano (matriz).
- **(deuda, US-033)** Totales con los activos de hoy (un trasladado sale de la tabla del detalle) e ingresos tardíos (RN-012); `fecha_estado` vacía (US-031).
- **(deuda, I.E.)** Sin asignación de docentes de curso a secciones: sus sesiones van en el bloque «Docentes de curso de <grado>», repetido en las secciones del grado y sin sumar a ninguna (D6, provisional). Cuando exista la asignación, pasan a la sección.
- **(historia nueva)** Tipo de documento al subir, «Plan anual y unidades» y la regla de semanas en «Mis sesiones» (`decision-sesiones.md`), después de la respuesta de Nayely.
- **(US-041 / US-042)** Botón de descarga en la cabecera de Consolidados; Entregas y la opción del ☰ pasan a enlaces.
- **(equipo)** Push y PR hacia `main` (`Closes #N` de US-040 y de T-04, verificando los números). En «Para quien revise»: el PR junta US-040, T-04, Pizarra neutra, la portada de la docente y DESIGN.md 1.2 (decisión 1); hoy no cuenta como «sin completar» (D5); la dirección no suma a «Colegas que la vieron» (D7).
- **(revisor grupo 3, Minor → grupos 4 y 6)** `periodo_de_la_consulta` devuelve `PeriodoDeLaSeccion` y `estado_de_las_secciones` / `resumen_de_la_ie` esperan el `Periodo` del modelo: las vistas pasan `elegido.periodo`, con una prueba que encadene las dos.
- **(revisor grupo 3, Minor)** `_celdas_de_la_hoja` no exige el rol Docente de la tutora (`puede_marcar` sí); hoy la asignación (`validar_asignacion`) ya lo impide.
- **(revisor grupo 3, Minor)** El tope de consultas de 24 secciones no marca competencias ni mide `resumen_de_la_ie` (+2 consultas).
