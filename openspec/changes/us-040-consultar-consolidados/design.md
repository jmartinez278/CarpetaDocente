# Design: US-040 – Consultar los consolidados (+ T-04, Pizarra neutra, portada aprobada y DESIGN.md 1.2)

## Context

- Decisiones cerradas en `insumos/US-040/decisiones.md` (1 a 19); bocetos aprobados en `prototipos-cd/US-040-final` (LEEME.md y `enmienda-design.md` mandan sobre el CSS compilado). Lo nuevo de este propose está en `proposal.md`.
- `direccion/` solo tiene `InicioDireccionView` (`RolRequeridoMixin`, rol Dirección) y la plantilla con el estado vacío; no tiene `servicios.py`.
- El ☰ sale de `cuentas.dimensiones.navegacion_docente` y la etiqueta `menu_docente`; `marco.html` deja vacío el lugar del tema. `menu_navegacion.html` solo pinta destinos y su enlace sin JS apunta fijo a `docente:portada`.
- Tokens en `src/frontend/css/rebrand/tokens.css`: el oscuro va en `html[data-theme=dark]` y en `@media (prefers-color-scheme: dark) :root:not([data-theme=light])`. Nadie escribe `data-theme` todavía.
- `notas.servicios.notas_faltantes(usuario, seccion, periodo, area)` aplica la regla de faltantes con `puede_marcar` (la tutora, área no a cargo del docente de curso). `periodos_de_la_seccion` y `periodo_de_la_hoja` resuelven Anterior / Vigente / Futuro.
- `asistencia.servicios` tiene `es_dia_de_clases`, `activos_del_dia`, `lista_del_dia` (avance de hoy) y la semana del selector.
- `repositorio.servicios.sesion_visible` es la única puerta de la página, la descarga y la vista; `registrar_vista` exige que la sesión esté compartida. `Sesion` guarda `autor`, `grado`/`grado_hasta`, `area`, `origen` (PROPIA o REFERENCIA), `compartida` y `creado_en`; no guarda sección. `InstitucionArea.a_cargo_docente_curso` marca las áreas del docente de curso.
- `Seccion.docente` es la tutora (docente de aula); no hay docente de curso asignado a secciones.

## Riesgos y zonas delicadas (primero)

- **[La dirección ve sesiones no compartidas]** (permisos, RN-019) → D7: una función aparte, `sesion_visible_direccion`, no un `if rol` dentro de `sesion_visible`; las rutas de la docente siguen negando a la dirección. Matriz con dirección de otra institución.
- **[Números distintos entre el mapa y el detalle]** (RNF-017, zona de cuidado) → D3: una sola función por cifra, usada por el mapa, el café de la I.E., la portada y el detalle. Pruebas que comparan el mapa con el detalle y los totales con el recuento de filas.
- **[Faltantes de la dirección ≠ faltantes de la hoja]** → D3: la versión por lote se prueba contra `notas_faltantes` con la tutora en los mismos datos.
- **[Rendimiento del mapa]** (24 secciones × ~40 días × 10 áreas) → D3: consultas por lote para todo el año, no por sección; tope de consultas probado con `django_assert_max_num_queries`.
- **[Deudas de US-031 en los totales]** (`fecha_estado` vacía, ingresos tardíos RN-012) → se heredan; D5 usa `activos_del_dia`, la misma regla que la pantalla de asistencia, para no sumar una tercera versión.
- **[La semana usa la fecha de envío]** (zona de cuidado) → D6: fecha de `creado_en` en Lima; una sesión subida tarde cae en el día que se subió. Se dice en el recuadro («Por día de envío»).
- **[Pizarra neutra cambia todas las pantallas en oscuro]** → D1: los tokens cambian en un solo lugar; el axe en oscuro de todas las pantallas lo cubre el `-m e2e` completo del cierre; Marco ve las pantallas principales en oscuro al cerrar el bloque 1.
- **[Destello del tema al cargar]** → D1: script bloqueante y mínimo en `<head>`, antes de la hoja de estilos.
- **[Tamaño del cambio]** (decisión 1) → cuatro bloques, cada uno verde antes del siguiente; los bloques 3 y 4 se parten en grupos por riesgo.

## Goals / Non-Goals

**Goals:**
- Todo lo de la dirección funciona con GET y sin JavaScript (pestañas, tira, filtro, semana y día); el JS solo pone el tema y el ☰.
- Sin migraciones ni campos nuevos.
- Un servicio de totales de asistencia por periodo que US-033 pueda reutilizar.

**Non-Goals:**
- Bloque «Plan anual y unidades», tipo de documento al subir y la regla de semanas en «Mis sesiones».
- Guardar algo nuevo para la tesis: la historia solo lee; los datos que mide la tesis (notas, asistencia, sesiones, registro de actividad) ya se guardan. Abrir y descargar una sesión deja SESION_DESCARGADA como hoy.

## Decisions

### D1. DESIGN.md 1.2, Pizarra neutra y botón de tema (bloque 1)
- DESIGN.md recibe la enmienda tal cual, con la fecha del propose; el café oscuro queda en `#493B34` (decisión 14). `.claude/rules/plantillas.md` cambia las líneas de Besley y de T-04.
- `tokens.css`: los valores oscuros de 1.2 en los dos bloques (`data-theme=dark` y `prefers-color-scheme`); `--tipografia-nombre` en `:root`. El papel atenuado va en selectores de miniaturas y vistas previas, sin tocar tokens globales.
- `static/js/tema.js` (nuevo), cargado en `<head>` de `base.html` sin `defer`, antes de `app.css`: lee `localStorage` (en `try`) y, si hay elección, pone `data-theme` en `<html>`. El mismo archivo, al cargar el DOM, conecta los botones `[data-tema]`: alterna, guarda, actualiza ícono y `aria-label`; escucha `storage` (otras pestañas) y `matchMedia('(prefers-color-scheme: dark)')` (sin elección) para actualizar el nombre del botón.
- **Por qué un solo archivo bloqueante**: evita el destello y no hace falta un `<script>` en línea (la CSP futura no lo exigirá). Es pequeño (< 1 KB).
- **Alternativa descartada**: cookie y tema en el servidor; obliga a tocar cada vista y no sigue `prefers-color-scheme` en vivo.
- El botón es una inclusión `rb/boton_tema.html` en `marco.html` (antes de `{% menu_cuenta %}`) y en `ingresar.html`. `/admin/` no extiende `marco.html`: no lo lleva.
- Besley se precarga en el bloque `precargas` de ingreso y de las dos portadas.

### D2. Rutas de la dirección
| Ruta | Nombre | Parámetros GET |
|---|---|---|
| `direccion/consolidados/` | `direccion:consolidados` | `periodo` |
| `direccion/consolidados/secciones/<id>/notas/` | `direccion:notas` | `periodo`, `area`, `filtro=pendientes` |
| `direccion/consolidados/secciones/<id>/asistencia/` | `direccion:asistencia` | `periodo` |
| `direccion/consolidados/secciones/<id>/sesiones/` | `direccion:sesiones` | `periodo`, `dia`, `docente` |
| `direccion/sesiones/<uuid>/` | `direccion:sesion` | — |
| `direccion/sesiones/<uuid>/descargar/`, `…/ver/` | `direccion:descargar`, `direccion:ver` | — |
- Todas con `DireccionMixin(RolRequeridoMixin)`. La sección se resuelve con `seccion_de_la_direccion(usuario, id)`: año ABIERTO de la institución del usuario; si no, `Http404` (no 403 ni registro: la dirección no tiene secciones «ajenas» en su institución y otra institución es «inexistente» para ella).
- Un parámetro que no vale (periodo inexistente, área que no es de la tutora, día fuera del periodo, docente que no está en la sección) se ignora y se usa el valor por defecto, como `periodo_de_la_hoja`. Un periodo futuro abre el vigente.
- Notas o Asistencia de una sección sin estudiantes redirige (302) a Sesiones.
- **Por qué rutas propias para la sesión**: la página de la docente lleva su ☰, migas y acciones de autora; la dirección necesita su ☰ y otra regla de visibilidad (aprobado por Marco el 23-11-2026).
- **Plantilla parcial compartida**: se extrae `repositorio/_pagina_sesion.html` (tipo, título, chips, «Compartida», autora, fecha, formato, tamaño, propósito, vista previa, «Descargar» y «Ver») de la página de la docente; la incluyen las dos páginas con las URL de descarga y vista como variables. Las migas, el total de vistas y las acciones de autora (Eliminar, Compartir, Dejar de compartir) quedan solo en la plantilla de la docente. Sin copias del marcado. `entregar_archivo` recibe la puerta como parámetro (D7).

### D3. Estado de las secciones (servicio, bloque 3)
- `direccion/servicios.py`:
  - `periodos_del_anio(institucion, hoy)` → periodos con estado (reutiliza la lógica de `periodos_de_la_seccion`, extraída a una función por año escolar si hace falta) y el elegido (`periodo_de_la_consulta`).
  - `estado_de_las_secciones(institucion, periodo, hoy)` → lista ordenada por grado y nombre de `EstadoSeccion(seccion, tutora, estudiantes, notas_faltan, notas_total, dias_sin_completar, estado)`.
  - `resumen_de_la_ie(estados, periodo, hoy)` → al día N de M, totales, % ponderado, sesiones del periodo, días para el cierre o «Terminado».
- Por lote: `notas.servicios.faltantes_por_seccion(secciones, periodo)` (una consulta agregada: competencias marcadas activas de áreas no a cargo del docente de curso × estudiantes activos − calificaciones) y `asistencia.servicios.dias_sin_completar_por_seccion(secciones, periodo, hoy)` (D5). Sección sin docente: `notas_faltan = 0` y `dias = 0` sin calcular.
- **Por qué no llamar `notas_faltantes` por área y sección**: 24 × 10 consultas. Una prueba compara las dos versiones con los mismos datos para que la regla no se separe.
- La portada usa `estado_de_las_secciones` del vigente: cuenta las atrasadas y arma la miniatura.

### D4. Periodo elegido
- Vigente si hoy cae en un periodo; si no, el último pasado; antes del primero, ninguno (estado «Hoy no hay un bimestre vigente» con la fecha del primero); sin periodos, el estado vacío. Es la regla de la hoja de notas sin la parte de edición.
- El café dice «Faltan N días para el cierre» (días de calendario hasta `fecha_fin`) en el vigente; en uno anterior, «Terminado» y la fecha de término. Entre periodos, el último pasado ya es «Terminado».

### D5. Asistencia por periodo (zona de cuidado; US-033 lo reutiliza)
- `asistencia.servicios.dias_de_clase(periodo, hasta)` → lunes a viernes entre `fecha_inicio` y `min(fecha_fin, hasta)`.
- `dias_sin_completar_por_seccion(secciones, periodo, hoy)`: días de `dias_de_clase(periodo, hoy - 1 día)`; por sección, en Python sobre dos consultas (estudiantes con `estado`/`fecha_estado`; marcas por jornada y estudiante del rango), un día cuenta si hay activos ese día (`_activo_el`) y alguno sin marca.
- `totales_por_estudiante(seccion, periodo, hoy)` y `totales_de_la_seccion(...)`: conteos de los cuatro estados de las jornadas del periodo hasta hoy, por estudiante activo hoy; % = (Asistió + Tarde) / marcas, redondeo «mitad hacia arriba» con `Decimal` a un decimal, coma decimal en la plantilla; sin marcas, `None` → «—».
- % de la I.E.: promedio de los % de las secciones con marcas, ponderado por sus estudiantes activos.
- **Por qué hoy no cuenta como «sin completar»** (aprobado por Marco el 23-11-2026, sin hora de corte): la jornada de hoy se toma durante la mañana; contarla pondría todas las secciones en «Atrasada» hasta terminar. Sí entra en «días de clase» (detalle de Asistencia y M de Sesiones), como en el boceto («11 días de clase, del 9 al 23 de noviembre»).

### D6. Sesiones de una sección y docentes de curso del grado
- Base común: `origen=PROPIA`, institución de la sección, fecha de envío (fecha de `creado_en` en Lima) dentro del periodo, `grado <= seccion.grado <= coalesce(grado_hasta, grado)`. Compartida o no.
- `sesiones_de_la_seccion(seccion, periodo)`: la base con `autor = seccion.docente`. Solo esta consulta alimenta la semana, los números por día, el día por defecto y el café (tutora contra `dias_de_clase(periodo, hoy)`).
- `sesiones_de_curso_del_grado(institucion, grado, periodo)`: la base con `area` a cargo del docente de curso en la institución. Alimenta solo el bloque «Docentes de curso de <grado> · <día elegido>»: por autor (por apellidos), su área, días con sesión y última fecha, y sus tarjetas del día elegido. No depende de la sección: es el mismo en las secciones del grado.
- Semana: lunes a viernes de la semana del día elegido; flechas a la semana anterior o siguiente mientras tengan días dentro del periodo (y no después de hoy). Día por defecto: hoy si hoy es de clase, está en el periodo y la tutora tiene sesiones ese día; si no, el último día con sesiones de la sección; sin ninguna, el último día de clase del periodo hasta hoy (así lo piden el escenario «Semana de la sección» y el boceto: hoy sin sesiones abre el viernes anterior).
- Sin chips por docente: la semana es de una sola docente y el bloque de curso agrupa por docente (aprobado por Marco el 23-11-2026; ajusta la decisión 8).
- El título del bloque lleva el día elegido para que un día punteado («sin sesiones» de la sección) con tarjetas de curso debajo no parezca un error.
- **Supuesto provisional** (aprobado por Marco el 23-11-2026): sin asignación de docentes de curso a secciones, sus sesiones se reconocen por área y grado y nunca se atribuyen a una sección. Deuda hasta que exista esa asignación.
- La tarjeta es la de US-011 con el `href` a `direccion:sesion`; sin «Mis sesiones» ni total de vistas.

### D7. Visibilidad de una sesión para la dirección
- `repositorio.servicios.sesion_visible_direccion(usuario, id_sesion, con_texto=True)`: rol Dirección, misma institución, `origen=PROPIA`; si no, `None`.
- `entregar_archivo` recibe la puerta (`visible=sesion_visible` por defecto); la dirección la llama con `sesion_visible_direccion`. Deja SESION_DESCARGADA con `propia: false`.
- La página de la dirección no llama a `registrar_vista`: la dirección no es colega y la sesión puede no estar compartida. La dirección ve todas las propias de su institución, compartidas o no (aprobado por Marco el 23-11-2026).

### D8. Navegación de la dirección
- `cuentas.dimensiones.navegacion_direccion(vista_actual)` → `Destino` Inicio (`direccion:inicio`), Consolidados (`direccion:consolidados`) y Entregas (sin URL). Consolidados es la actual en cualquier vista `direccion:*` salvo `direccion:inicio`.
- `menu_navegacion.html` recibe `url_inicio` para el enlace sin JS; la etiqueta `menu_docente` pasa a `menu_navegacion`, que elige la lista por rol. Las plantillas de la dirección dejan el bloque `navegacion` por defecto; las portadas lo vacían como hoy.

### D9. Portada de la dirección
- Reemplaza `direccion/inicio.html`. La pastilla cuenta las atrasadas del vigente; con 0 no va (aprobado por Marco el 23-11-2026). La miniatura pinta la fecha de hoy y la rejilla 6 × 4 desde `estado_de_las_secciones` (casillas `aria-hidden`; la banda tiene un nombre accesible con el título y la pastilla).
- «Completar plantilla del SIAGIE» lleva `data-abrir-plantilla` y `aria-haspopup="dialog"`; `plantilla-siagie.js` y el diálogo no cambian.
- Saludo con `asistencia.servicios.saludo`, como la docente.

### D10. Portada de la docente
- `PortadaDocenteView` agrega `fecha_miniatura`, `hay_clases` y el avance de `lista_del_dia(seccion, hoy)` (solo con sección única); la línea de la sección deja la fecha. `rb/miniatura_asistencia.html` pasa a la miniatura calendario aprobada.

### D11. Pruebas en navegador
- Nuevas (8, más de 6 por el tamaño de la historia y porque T-04 es conducta de JS): T-04 elección y nombre del botón tras recargar; T-04 sin elección sigue el cambio del sistema y otra pestaña recibe la elección; portada de la dirección (banda → Consolidados → celda → detalle) ; axe y ancho de la portada de la dirección (con y sin bimestres) en ambos temas a 360; axe y ancho de Consolidados; axe y ancho del detalle en sus tres pestañas; axe del ☰ de la dirección abierto; axe y ancho de la portada de la docente con el calendario.
- Pestañas, tira, filtro, semana, bloque de docentes de curso, textos, enlaces, permisos y 302 van como pruebas de vista.

## Risks / Trade-offs

- [El bloque de docentes de curso se repite en las secciones del grado] → se acepta (D6): va aparte y no suma a ninguna sección; deuda hasta que exista la asignación de docentes de curso.
- [Extraer la parcial cambia la página de la docente] → prueba primero de que la página de la docente conserva migas, total de vistas y acciones de autora (tarea 5.3).
- [Hoy no cuenta como «sin completar»] → una sección que nunca toma la asistencia de hoy aparece atrasada recién mañana; se acepta (D5).
- [El % y los totales usan los activos de hoy por estudiante] → un trasladado sale de la tabla del detalle aunque tenga marcas en el periodo; sus marcas sí cuentan en el % de la sección. Deuda a US-033.
- [El mapa es costoso en un año grande] → consultas por lote y tope de consultas en prueba; sin caché.
- [Las e2e existentes que miden valores de CSS de la portada fallan con Pizarra neutra] → Marco aprobó retirarlas (23-11-2026); se borran en la tarea 1.5.

## Migration Plan

Sin migraciones. Despliegue normal: `npm run build` para el CSS y `collectstatic`. Si hay que volver atrás, se revierte el PR; `localStorage` con `data-theme` queda sin efecto.
