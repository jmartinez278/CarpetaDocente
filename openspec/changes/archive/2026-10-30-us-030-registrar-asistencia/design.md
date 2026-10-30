# Design: US-030 – Registrar la asistencia de una jornada

## Context

- Las decisiones de alcance e interfaz están cerradas en `insumos/US-030/decisiones.md` (aprobado el 29-10, decisiones 1 a 18 y zonas de cuidado). Este design no las repite: dice cómo se construyen y cierra lo que el propose debía decidir (RNF-011, JavaScript, sesión vencida, Minor 5, tiempos de reintento).
- Bocetos: `C:\Proyectos\prototipos-cd\decision-final\` (dirección 0.3, ronda 4). `asistencia/asistencia.html` (`#vista-1` a `#vista-6` y `#vista-10`), `portada.html`, `estudiantes/estudiantes.html?estado=5`, `variante.css` y las capturas de `capturas/`. Son referencia de estructura, clases y textos; su `asistencia.js` es un prototipo estático y no se copia. Una diferencia: el boceto muestra "Sin conexión" con el primer fallo; vale la decisión 16 (tras 3).
- La app `asistencia` existe vacía (sin modelos ni rutas). `institucion` tiene `Estudiante` sin `estado`; `servicios.quitar_estudiante` y `vaciar_lista` ya traducen `RestrictedError` a `ListaConRegistros`, a la espera de una FK `RESTRICT`.
- `InactividadMiddleware` escribe la marca de actividad en la sesión en cada petición; con `HX-Request: true`, la sesión vencida responde 200 con `HX-Redirect` (US-006, D7). `RolRequeridoMixin` hace lo mismo sin sesión.
- La tarjeta de dimensión arma su enlace con `{% url d.url_name %}`, sin argumentos; la ruta de asistencia necesita el id de la sección.
- `TIME_ZONE = "America/Lima"`, `USE_TZ = True`, `LANGUAGE_CODE = "es-pe"`.

## Riesgos y zonas delicadas (primero)

- **[Toque perdido o duplicado con red inestable, RNF-011]** → D3: estado de destino, inserción con `ON CONFLICT`, una sola petición en curso por fila y nunca abortada, reintentos con espera creciente. Prueba de 10 cortes en Playwright (`context.set_offline`) que cuenta filas en la base.
- **[Respuesta vieja que pisa una nueva]** → D3: como la petición en curso no se aborta, la siguiente de esa fila sale solo cuando la anterior terminó. Queda un caso, que va a la deuda: si la red se corta después de que el servidor aceptó un POST, el cliente lo da por fallido y reintenta, y el POST original puede terminar después del reintento y dejar la marca vieja mientras la pantalla dice "Guardado" (revisión A2). La solución es un `origen` por pestaña y una `secuencia` por fila, y que el servidor rechace las anteriores. Con dos pestañas o dos equipos, gana la última que llega (fuera de alcance).
- **[El lote se pierde al cerrar la pestaña]** → D5: `fetch` con `keepalive` en `pagehide` y en `visibilitychange` (oculta). La prueba e2e cierra la página durante la cuenta y revisa la base.
- **[Sesión vencida a medio pasar lista]** → D6: el guardado recibe `HX-Redirect`; las marcas pendientes se guardan en `sessionStorage` y se reenvían al volver a abrir la asistencia de ese día.
- **[Migraciones]** → `institucion/0004` agrega columnas con valor por defecto (ACTIVO) a una tabla con datos; `asistencia/0001` crea tablas nuevas. Tramo de alto riesgo: grupo 1, solo.
- **[DESIGN.md cambia pantallas ya archivadas]** → D11 y grupo 2 parte A: el commit de DESIGN.md va primero y solo; las pruebas de US-001 y US-006 que miran textos ("Hola,") se actualizan en la misma rama y el PR lo dice.
- **[Marca de actividad cada 30 s, D9]** → la sesión puede cerrarse hasta 30 s antes de los 60 minutos exactos sin peticiones; nunca después. Los escenarios de `cierre-sesion` (59 y 60 minutos) siguen valiendo. Aceptado por Marco el 29-10-2026.
- **[Hora de Lima]** → `timezone.localdate()` en todo cálculo de "hoy"; los servicios reciben `hoy` (D2) y las pruebas de vistas parchean `timezone.localdate`/`localtime`, sin dependencias nuevas.

## Goals / Non-Goals

**Goals:**
- Toda escritura y toda regla (jornada única, ciclo, nota, activos, solo hoy, fin de semana) en `asistencia/servicios.py`; las vistas solo leen la petición y llaman al servicio.
- Que la base de datos impida lo que el spec dice que no puede pasar: dos jornadas de la misma sección y fecha, dos estados de un estudiante en una jornada, un estado fuera de los cuatro y una nota sin Justificado.
- Una pantalla liviana: sin HTMX ni Alpine, un solo JS propio.

**Non-Goals:**
- Días anteriores, periodo cerrado y registro de actividad (US-031); la ruta ya lleva la fecha para que US-031 la abra a otros días.
- Funcionar sin JavaScript: sin JS, la pantalla muestra la lista y un `<noscript>` "Activa JavaScript para registrar la asistencia." (marcar exige guardar por toque).
- Coordinar dos pestañas o dos equipos sobre la misma fila.
- Registrar a `Jornada` y `Asistencia` en el panel de Django.

## Decisions

### D1. Modelos (`asistencia/models.py`, `institucion/models.py`)

- **`Estudiante`** (migración `institucion/0004`): `estado` `CharField(12)`, `choices` ACTIVO/TRASLADADO/RETIRADO, `default="ACTIVO"`, con `CheckConstraint` `ck_estudiante_estado`; `fecha_estado` `DateField(null=True, blank=True)`. Los estudiantes existentes quedan ACTIVO.
- **`Jornada`** (`db_table="jornada"`): `seccion` FK `CASCADE` (doc 11; el cierre del año borra en cascada), `fecha` `DateField`, `registrado_por` FK a `Usuario` `PROTECT` (las cuentas se desactivan, no se borran), `creado_en` `auto_now_add`. `UniqueConstraint(seccion, fecha)` `uq_jornada`.
- **`Asistencia`** (`db_table="asistencia"`): `jornada` FK `CASCADE`, `estudiante` FK **`RESTRICT`** (decisión de US-006; doc 11 dice cascada), `estado` `CharField(12)` con ASISTIO/FALTO/TARDE/JUSTIFICADO, `nota_justificacion` `CharField(100, blank=True, default="")`, `actualizado_en` `auto_now`. Restricciones: `uq_asistencia (jornada, estudiante)`, `ck_asistencia_estado` y `ck_asistencia_nota` (`nota_justificacion = '' OR estado = 'JUSTIFICADO'`, como el DDL del doc 11 con cadena vacía en vez de NULL, que es la convención de Django para texto).
- Con `RESTRICT`, borrar un estudiante con asistencia lanza `RestrictedError` → `ListaConRegistros` (ya existe). Borrar la sección entera sigue funcionando: Django permite el `RESTRICT` cuando la asistencia cae en la misma cascada.
- **Datos para la tesis (VD – D3):** la exactitud se lee de `asistencia.estado` por estudiante y jornada, y de la jornada completa o incompleta, que se calcula (doc 11). Para el **tiempo** del control (que mide la ficha de observación externa), `jornada.creado_en` guarda el primer toque y `asistencia.actualizado_en` el último cambio de cada fila: la duración de una toma es `max(actualizado_en) − creado_en`. `actualizado_en` no está en el doc 11; va a la deuda como agregado.
- **Alternativa descartada:** guardar "completa" en la jornada. El doc 11 lo descarta (dato derivable).

### D2. Servicios (`asistencia/servicios.py`)

Cada función recibe `hoy` (por defecto `timezone.localdate()`), así las pruebas fijan el día sin parchear el reloj.

- `es_dia_de_clases(fecha)`: lunes a viernes.
- `lista_de_hoy(seccion, hoy)`: la jornada de hoy si existe (sin crearla), los activos ordenados con `institucion.servicios.estudiantes_ordenados` y su estado, los no activos aparte, el avance (marcados, total) y los totales por estado. Una consulta para los estudiantes y una para las asistencias.
- `marcar(seccion, estudiante_id, fecha, estado, nota, usuario)`: valida que `fecha == hoy`, día de clases, estudiante ACTIVO de la sección, estado de los cuatro y nota ≤ 100; si el estado no es JUSTIFICADO, la nota se guarda vacía. Dentro de `transaction.atomic`: `Jornada.objects.get_or_create(seccion, fecha, defaults={registrado_por})` (Django reintenta el `get` si dos peticiones chocan en la restricción) y luego un **upsert** de una fila con `Asistencia.objects.bulk_create([...], update_conflicts=True, unique_fields=["jornada", "estudiante"], update_fields=["estado", "nota_justificacion", "actualizado_en"])`, que en PostgreSQL es un `INSERT … ON CONFLICT DO UPDATE` atómico.
- `marcar_restantes(seccion, estudiante_ids, fecha, usuario)`: mismas validaciones; ASISTIO solo para los ids que aún no tienen fila hoy (`bulk_create(..., ignore_conflicts=True)`): nunca pisa un estado puesto por otro toque (decisión 3). Un id que no es un estudiante activo de la sección hace fallar todo el lote (404) sin guardar ninguno.
- `pendiente_hoy(seccion, hoy)`: para la píldora de la portada: día de clases, con activos y la jornada sin completar.
- `texto_fecha(fecha)`: "Miércoles 28 de octubre", con nombres en español escritos en el módulo (no depende del locale del servidor). `saludo(hora)`: "Buenos días" (hasta 11:59), "Buenas tardes" (12:00 a 18:59), "Buenas noches".
- Errores del servicio: `FechaNoValida` (no es hoy o fin de semana) y `ValidationError` (estado o nota). El estudiante que no es activo de la sección es `Estudiante.DoesNotExist`.
- **Alternativa descartada:** `update_or_create` para la asistencia: hace `SELECT … FOR UPDATE` y luego `INSERT`, y dos peticiones iguales a la vez pueden chocar en `uq_asistencia`; el upsert lo resuelve en una sentencia.

### D3. Guardado por toque idempotente (RNF-011)

- **Estado de destino:** la página guarda el estado de cada fila; el toque calcula el siguiente en el ciclo y envía ese estado. Repetir la petición deja lo mismo.
- **Una petición por fila, sin abortar:** cada fila tiene `enviado` y `deseado`. Un toque cambia `deseado` y la pantalla al instante. Si no hay petición en curso, se envía; si la hay, se espera a que termine (bien o mal) y, si `deseado ≠ enviado`, se envía `deseado`. No se aborta una petición en curso: así nunca hay dos de la misma fila en la red, y el último toque gana.
- **Respuestas:** 204 = guardado. Red caída, 5xx, 408 y 429 = fallo que se reintenta. 400, 404 y 409 = no se reintenta: la página se recarga para mostrar lo que hay en la base (por ejemplo, cambió el día). 200 con `HX-Redirect` = sesión vencida (D6).
- **Reintentos (decisión 16):** 1 s, 2 s, 4 s, 8 s y luego cada 15 s, por fila; el evento `online` reintenta todas de inmediato. Un guardado bueno reinicia la espera de su fila.
- **"Sin conexión":** un contador de fallos seguidos de la pantalla (cualquier fila); al llegar a 3 aparece el Mensaje de error una sola vez; el primer guardado bueno lo quita y pone el contador en 0.
- **La fila con fallo** muestra "<Estado> · sin guardar. Reintentando…" desde el primer fallo; "N sin guardar" cuenta las filas cuyo último intento falló.
- **Alternativas descartadas:** `hx-sync="this:queue last"` de HTMX da la cola por fila, pero no reintentos ni la interfaz optimista, que igual exigen JS propio; un número de versión por toque en la base resolvería también dos pestañas y el POST viejo que termina después del reintento (riesgo anterior), pero agrega campos y su prueba; va a la deuda (decisión de Marco tras la A2, 29-10).

### D4. JavaScript: un `static/js/asistencia.js` propio, sin HTMX ni Alpine

- La pantalla se dibuja completa en el servidor (lista, estados, avance, totales, nota). `asistencia.js` hace: ciclo y estado optimista, cola por fila y reintentos (D3), avance, totales, "Marcar los N restantes" y su barra (D5), nota con guardado (D7), franja de guardado, "Sin conexión", cierre (D8), aviso al salir, `sessionStorage` (D6) y teclado.
- Peticiones con `fetch`, `X-CSRFToken` (de la cookie `csrftoken`) y `HX-Request: true`, para que el middleware y `RolRequeridoMixin` respondan con `HX-Redirect` sin código nuevo.
- Sin HTMX: la pantalla no reemplaza fragmentos; cargarlo sumaría ~16 KB sin usar. Sin Alpine: el estado vive en un objeto por fila; Alpine no aporta a la cola ni a los reintentos.
- `<details>` nativo para la leyenda plegada del celular.
- **Teclado:** el círculo es un `<button>`: Intro y espacio ya lo activan. En PC la fila con el foco se resalta con `:focus-within`.
- **Aviso al salir:** `beforeunload` con `preventDefault()` solo mientras haya filas con `deseado ≠ guardado` o un lote en cuenta.

### D5. "Marcar los N restantes" y su barra (decisiones 3, 13 y 14)

- Tocarlo pone en Asistió (pendiente) a los Sin marcar, sin enviar nada, y abre la barra "N marcados como Asistió · Deshacer (5)". La franja dice "Pendiente de deshacer".
- La cuenta corre con `setInterval` de 1 s; se pausa con `pointerenter` sobre la barra y con el foco en ella si `:focus-visible` (`matches(':focus-visible')`), no con el foco que pone el sistema.
- Tocar una fila del lote la saca del lote y sigue el ciclo desde Asistió (pasa a Faltó) con su guardado normal.
- "Deshacer": las filas del lote vuelven a Sin marcar y la barra se cierra. Al acabar la cuenta: una petición a `restantes/` con los ids que quedan en el lote; con 204, "N guardados como Asistió" en la región de anuncios. El lote fallido se reintenta como una fila (D3).
- `pagehide` y `visibilitychange` (oculta): si hay lote en cuenta, se envía en ese momento con `fetch(..., {keepalive: true})` y la barra se cierra. Se usa `keepalive` y no `sendBeacon` porque permite la cabecera `X-CSRFToken` y leer la respuesta cuando la página sigue viva (`visibilitychange`).
- Foco: al cerrarse la barra, si el foco estaba en "Deshacer" vuelve al botón "Marcar…" o, si ya no está, al primer círculo; si estaba en una fila, no se mueve.
- **Anuncios:** la barra no es región viva. Una región `aria-live="polite"` fija y vacía recibe "N marcados como Asistió. Puedes deshacer durante 5 segundos" al abrir y "N guardados como Asistió" al confirmar; el número visible de la cuenta lleva `aria-hidden`.

### D6. Sesión vencida durante los toques

- La respuesta con `HX-Redirect` detiene la cola. Antes de ir a esa dirección, `asistencia.js` guarda en `sessionStorage` (clave `asistencia:<seccion>:<fecha>`) las marcas no guardadas y el lote, quita el aviso al salir y navega.
- Al abrir la asistencia de la misma sección y fecha en esa pestaña, si la clave existe, se aplican esas marcas a la pantalla y se envían por la cola normal; la clave se borra cuando todas se guardan. Si la fecha ya pasó, la clave se descarta (US-031 se ocupará de otros días).
- `sessionStorage` puede fallar (modo privado): todo acceso va en `try/catch` y, si falla, la marca se pierde como hasta ahora, pero la docente vio el aviso de inactividad.
- El `next` sigue siendo la portada (US-006, D7); desde ahí la tarjeta Asistencia lleva de vuelta.

### D7. Nota de justificación

- El campo aparece en la fila al llegar a Justificado (sin mover el foco del círculo). Se guarda junto con el estado, en la misma petición de la fila (D3), al perder el foco (`change`) y tras 800 ms sin escribir; el contador "N/100" se actualiza al escribir. `maxlength="100"` en el campo y la validación en el servicio.
- Al pasar a Asistió, el campo se oculta y la petición envía nota vacía; el servicio la borra igual (doc 11).

### D8. Avance, totales y cierre de jornada

- El servidor dibuja avance y totales; el JS los recalcula con cada cambio de la pantalla (incluido el lote pendiente, que cuenta como marcado mientras dura la cuenta, como en el boceto).
- **Cierre:** visible solo si todos los activos tienen estado guardado, sin filas en cola ni lote en cuenta, y sin "Sin conexión". Al abrir una jornada ya completa, el servidor lo dibuja sin trazo. Cuando se cumple en la pantalla, se anuncia después del último "Guardado" y se trazan las franjas una vez (`prefers-reduced-motion: no-preference`). Si se deshace un lote, se quita sin rastro.

### D9. Marca de actividad cada 30 s (Minor 5 de US-002)

- `InactividadMiddleware` reescribe `ultima_actividad` solo si la guardada tiene 30 s o más. Si no, la sesión no se modifica y Django no la escribe.
- Por qué 30 s: con cualquier valor menor que 60 s, una petición a los 59 minutos de la última sigue dentro de la sesión y una a los 60 queda fuera, como piden los escenarios de `cierre-sesion`. La sesión puede cerrarse hasta 30 s antes; nunca dura más de 60 minutos sin peticiones (RN-025). Confirmado por Marco el 29-10-2026.
- Prueba nueva en `test_inactividad.py`: dos peticiones a 10 s no modifican la sesión; a 30 s, sí.

### D10. Rutas, vistas y portada

- Rutas (`asistencia/urls.py`, `app_name="asistencia"`, bajo `docente/secciones/<int:seccion_id>/asistencia/`):
  - `""` → `hoy` (GET): la pantalla.
  - `<fecha:fecha>/estudiantes/<int:estudiante_id>/` → `marcar` (POST: `estado`, `nota`). Conversor `fecha` (AAAA-MM-DD) propio.
  - `<fecha:fecha>/restantes/` → `restantes` (POST: `estudiante` repetido).
- Vistas con el `SeccionDocenteMixin` de `institucion` (404 para otra docente o año CERRADO; otro rol y sin sesión, por `RolRequeridoMixin`). Las vistas POST responden 204, 400, 404 o 409 sin cuerpo HTML.
- **Plantillas** en `templates/asistencia/`: `hoy.html` (extiende `marco.html`), con parciales `_fila.html`, `_panel.html`, `_fin_de_semana.html` y `_sin_estudiantes.html`. Celular y PC son la misma lista; el panel de PC es el mismo bloque que la franja fija del celular, ubicado con CSS (`min-[960px]:`).
- **Portada:** `Dimension` no cambia de forma; la vista arma la lista de tarjetas con `dataclasses.replace`: Asistencia con `url` a `asistencia:hoy` de `seccion_unica` y `disponible=True` solo si hay sección única; sin ella, la misma `Dimension` con `disponible=False` ("Próximamente", confirmado por Marco el 29-10-2026). `tarjeta_dimension.html` usa `d.url` en vez de `{% url d.url_name %}`. `test_dimensiones.py` sigue exigiendo que `asistencia:hoy` resuelva.
- **Píldora:** `pendiente_hoy` en el contexto; la tarjeta Asistencia agrega `<p class="pildora-pendiente" id="pend-asistencia">` y el enlace pasa a `aria-describedby="acc-asistencia pend-asistencia"`.
- **Saludo y fecha:** `saludo(timezone.localtime().hour)` y `texto_fecha(hoy)` en el contexto de la portada.
- **Aviso de éxito de la lista de estudiantes:** el enlace "Tomar la asistencia de hoy" va a `asistencia:hoy`; es un `<a href>` normal, sin atributos `hx-*`, así que también dentro del diálogo navega la página completa.

### D11. DESIGN.md a la dirección visual 0.3: versión **0.4**

- DESIGN.md ya usa los números 0.3 ("Cambios 0.3") y 0.3.1 (estado actual); "0.3" de `prototipos-cd` es el nombre de la dirección visual. Para no repetir número, el archivo pasa a **propuesta 0.4 · 29-10-2026** y el bloque nuevo se titula **"Cambios 0.4 (dirección visual 0.3, US-030)"**, con el texto de `DESIGN-0.3-propuesta.md` y su "Pendiente".
- Se corrige la frase repetida de la propuesta ("dato real que provee US-030); dato real que provee US-030);").
- Además del bloque, se alinean las secciones que el bloque contradice, sin agregar reglas: "Fila de asistencia (celular)" (nombre completo en mayúsculas, decisión 7), "Asistencia en PC" (opción D), "Movimiento" (los dos momentos de autor), "Layout" (la asistencia en PC ya no muestra la semana completa), la lista de pantallas (saludo según la hora; asistencia en PC con lista y panel), "nunca mayúsculas sostenidas" (su excepción), la barra superior (línea tenue) y los tokens/clases de las franjas de cabecera.
- En el mismo commit, `.claude/rules/plantillas.md` pasa de "0.3.1, fijo hasta el pulido final" a "0.4": la regla de cambiar DESIGN.md solo con el diff y aprobación se cumple mostrando el diff antes del commit.
- Commit propio, el primero después del archivo de US-006, antes de cualquier plantilla. Número 0.4 confirmado por Marco el 29-10-2026.

### D12. CSS

- Las clases nuevas salen de `variante.css` y `asistencia/asistencia.css` del boceto, reescritas con los tokens de `app.css` (sin hexadecimales en plantillas). Se miden con el mismo límite del boceto: la pantalla no suma fuentes ni imágenes; el CSS crece unos KB comprimidos.
- La barra con línea tenue: `border-bottom` con `color-mix(in srgb, var(--color-linea) 55%, var(--color-fondo))`, en `marco.html` para todas las pantallas con barra.

## Migration Plan

1. `institucion/0004`: `estado` con `default="ACTIVO"` y `fecha_estado` nulo; restricción `ck_estudiante_estado`. En Neon, `AddField` con valor por defecto es inmediato para 60 filas por sección.
2. `asistencia/0001`: tablas `jornada` y `asistencia` con sus restricciones. Depende de `institucion/0004` y de `cuentas`.
3. Vuelta atrás: `migrate asistencia zero` y `migrate institucion 0003` (se pierden la asistencia y los estados; en el Sprint 1 solo hay datos ficticios).

## Open Questions

- Quién registra traslados y retiros en la I.E. (Nayely). No cambia US-030: no hay pantalla.
