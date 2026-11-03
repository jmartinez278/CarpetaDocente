# Design: US-020, US-021 y US-022 – Hoja de notas por área

## Context

- Decisiones cerradas en `insumos/US-020/decisiones.md` (1 a 18) y `insumos/US-022/decisiones.md` (1 a 11). Interfaz: boceto `C:\Proyectos\prototipos-cd\US-020\` (`README.md`, `notas.md`, `demo.html`, estados 01 a 21); su `localStorage` de demostración y su copia de Competencias no se copian. Lo nuevo de este propose está en `proposal.md`.
- `notas` (US-029) ya tiene `CompetenciaPeriodo`, `puede_marcar`, `areas_de_la_seccion`, `universo`, `periodos_de_la_seccion`, `marcas_por_periodo`, `tiene_notas` (devuelve `False`) y `competencias_obligatorias` (sin notas). `guardar_marcas` bloquea la fila de la sección (`select_for_update`).
- `Estudiante.estado` (ACTIVO, TRASLADADO, RETIRADO) existe desde US-030; quitar y vaciar ya atrapan `RestrictedError` (`ListaConRegistros`), así que una FK RESTRICT de `calificacion` los bloquea sin tocar `institucion`.
- `actividad.registrar` exige transacción abierta y valida el detalle contra `DETALLE_PERMITIDO`; agregar una operación obliga a migrar `ck_actividad_operacion`. `indicadores_por_semana` deja `secciones_con_notas` en `None`.
- Patrón de pantalla (US-029, US-030): JS propio sin HTMX ni Alpine, `fetch` con `X-CSRFToken` y `HX-Request` (para el `HX-Redirect` de la sesión vencida), clases en `src/frontend/css/app.css` con los tokens de `DESIGN.md`. Ningún guardado del repo usa aún cuerpo JSON.
- `menu.js` se carga en toda pantalla con el menú de la cuenta, que tiene el formulario POST de «Cerrar sesión».

## Riesgos y zonas delicadas (primero)

- **[Guardado parcial]** (RNF-011) → D5: una transacción por hoja; toda validación (estructura, escala, conclusión, cambios de otro dispositivo) termina antes de la primera escritura. Prueba con la escritura forzada a fallar a mitad.
- **[Dos guardados a la vez y notas frente a marcas]** → D5: el guardado bloquea la misma fila de sección que `guardar_marcas`. Dos guardados de notas van en fila, y desmarcar una competencia nunca se cruza con el primer guardado de sus notas (`tiene_notas` lee lo confirmado). Prueba con hilos (`transaction=True`).
- **[Pisar una nota cambiada desde otro dispositivo]** (zona de cuidado de US-020) → D7: cada celda viaja con la nota que la docente vio guardada; si la base ya es otra, 409 sin guardar nada.
- **[Datos de menores en el navegador]** (Ley 29733, RN-014/016, RNF-015) → D10: solo identificadores, niveles, conclusiones y fechas; clave por cuenta; se borran al guardar, descartar y cerrar sesión desde cualquier pantalla. Con la sesión vencida quedan en el dispositivo hasta que vuelva la misma cuenta (decisión 13): en una computadora compartida, la conclusión queda en el almacenamiento del navegador. Riesgo aceptado por la decisión; va a la descripción del PR.
- **[Conclusión que el modelo no acepta]** → D1: el CHECK de la base es la red final; el servicio da el error legible antes. Choque con RN-003 y `ck_calificacion_c` a la deuda.
- **[FK a estudiante]** → RESTRICT (D1), no CASCADE como el doc 11: quitar o vaciar con notas se bloquea; la demo y el descarte borran las notas antes (D14). A la deuda.
- **[Periodo CASCADE]** → reconfigurar periodos (US-028) no borra periodos (`guardar_periodos` solo crea y edita) y el panel no permite borrar años ni periodos (`has_delete_permission`, `can_delete=False`). Sin cambio.
- **[Rejilla con teclado]** → D12: patrón ARIA grid con `tabindex` itinerante; axe y lector en el pulido final. La hoja más grande (Personal Social, 5 columnas, 30 estudiantes) se prueba a 320 px y con Slow 4G.
- **[Tira de áreas con desplazamiento horizontal]** → decisión del equipo (proposal). Va en su propio contenedor; la página no se desplaza. Choque con RNF-005 y `plantillas.md` a la deuda.

## Choques resueltos (decisiones.md frente al boceto)

| # | Decisión | Boceto | Resolución |
|---|---|---|---|
| 1 | US-020 D8: el bimestre se elige en la pantalla de notas, con cápsulas como en US-029; «Competencias» es una píldora más de la tira | Notas muestra solo «B3 · Vigente»; el bimestre se elige en Competencias, que vuelve con «Registrar notas de B2»; «Competencias» es un botón arriba a la derecha | Manda el boceto (D3, D15) |
| 2 | US-020 D9: la conclusión va en su columna, junto a cada nivel | Una columna por competencia; B y C llevan un icono que abre un recuadro junto a la celda (Alt+Enter) | Manda el boceto (D12) |
| 3 | US-020 D8: tira de áreas con desplazamiento horizontal | Igual | Se mantiene por decisión del equipo; choque con RNF-005 a la deuda |
| 4 | US-020 D16: detalle con «cambiadas (de → a)» | — | Sin niveles, por la spec `registro-actividad` (decisión del equipo, D13) |
| 5 | Criterios de US-020 y US-021: textos exactos de red y de C sin conclusión | Textos propios, en tuteo y para B y C | Textos del boceto (decisión del equipo); a la deuda |

US-022 D-zona «decisiones.md de US-020 desfasado» queda resuelto con esta tabla; el archivo de `insumos/` no se edita.

## Goals / Non-Goals

**Goals:**
- Toda regla y toda escritura de notas en `notas/servicios.py`; las vistas leen la petición y llaman al servicio.
- Un guardado por hoja, todo o nada, idempotente y que no pisa cambios ajenos.
- Lo digitado sobrevive a la red, a la recarga y a la sesión vencida, sin nombres en el dispositivo.

**Non-Goals:**
- Aviso en vivo de cambios de otro dispositivo (solo al abrir y al guardar).
- Consulta de un año CERRADO (404, como US-029), entrega, exonerados, docentes de curso.
- Notas de ejemplo en la demostración.

## Decisions

### D1. Modelo `Calificacion` (`notas/models.py`, migración `0002`)

- `db_table="calificacion"`. `estudiante` FK `institucion.Estudiante` **RESTRICT** (`related_name="calificaciones"`); `competencia` FK `catalogo.Competencia` RESTRICT; `periodo` FK `institucion.Periodo` CASCADE; `registrado_por` FK usuario SET_NULL, nulo; `nivel` `CharField(2)` con choices AD, A, B, C; `conclusion_descriptiva` `TextField` con `default=""` (cadena vacía en vez de NULL, como `asistencia.nota_justificacion`); `creado_en` y `actualizado_en`.
- Restricciones: `uq_calificacion` (estudiante, competencia, periodo); `ck_calificacion_nivel` (nivel en la escala); `ck_calificacion_conclusion`: AD y A con conclusión vacía, B y C con 10 a 500 caracteres. La longitud en un `CheckConstraint` usa una expresión que el repo aún no usa: consultar Context7 (Django 5.2) en el apply. Índice `idx_calificacion_periodo` (periodo, competencia), del doc 11, para `tiene_notas` y los faltantes.
- La sección no se guarda (3FN, doc 11): sale de `estudiante.seccion`. Que estudiante, periodo y competencia sean de la misma sección, año y área lo comprueba el servicio (D5).
- **Alternativa descartada:** `conclusion_descriptiva` nula como el DDL del doc 11: dos formas de «vacío» complican el CHECK y la comparación de D7.

### D2. Lectura de la hoja: `hoja_de_notas(usuario, seccion, periodo, areas)`

- Con `areas_de_la_seccion` (dos consultas), las marcas del periodo (una) y las notas del periodo de la sección (una), arma por área marcable: columnas (competencias activas marcadas, con su número del catálogo: posición entre las activas del área), filas activas por `estudiantes_ordenados`, filas de solo lectura (trasladados y retirados con alguna nota del área en el periodo) y notas `{(estudiante, competencia): (nivel, conclusión)}`. Sin consultas por área ni por celda.
- Las áreas a cargo del docente de curso y las marcables sin columnas van sin datos de celdas; la plantilla dibuja sus estados vacíos.

### D3. Periodo y área de la hoja

- `periodo_de_la_hoja(periodos, pedido)`: el de `?periodo=N` si es `editable`; si no, el VIGENTE; si no, el ANTERIOR editable de número mayor; si no, ninguno (sin periodos o antes del primero: los textos de US-029).
- Sin marcas guardadas del periodo dentro del `universo` (`marcas_por_periodo` no lo trae): 302 a `competencias:pantalla?periodo=N&area=<código>&desde=notas`.
- `?area=<codigo_siagie>`; si falta o no es del catálogo de la institución, la primera área marcable con columnas, en orden SIAGIE. El JS cambia de área sin recargar y actualiza `?area=` con `history.replaceState`.

### D4. `notas_faltantes(usuario, seccion, periodo, area)` (US-022 D10)

- Si `puede_marcar` es falso, lista vacía. Si no, una consulta: estudiantes activos de la sección cruzados con las marcas del área en el periodo (por la relación sección → `competencias_periodo`), menos los que tienen `Calificacion` (`~Exists`). Devuelve los pares (estudiante, competencia) ordenados; la hoja usa su longitud y US-026/US-042 los pares.
- El cliente cuenta en vivo con la misma regla sobre lo guardado más el borrador; el servidor da el número al abrir la hoja y en la respuesta de cada guardado (US-022 D7).

### D5. Guardado: `guardar_hoja(usuario, seccion, numero, codigo_area, celdas, hoy=None)`

En `transaction.atomic()`, todo validado antes de escribir:

1. La sección con `select_for_update()` (el mismo bloqueo que `guardar_marcas`). Año CERRADO o periodo con `fecha_inicio > hoy` → `PeriodoNoEditable`; número inexistente → `Periodo.DoesNotExist`; código de área que no es de la institución → 404.
2. **Estructura:** área no marcable (`puede_marcar`), competencia que no es columna de la hoja (activa, del área, marcada en el periodo), estudiante que no es activo de la sección, celda repetida → `HojaCambiada` («La hoja cambió desde que la abriste. Recarga la página.»).
3. **Escala** (RN-001): `nivel.strip().upper()`; vacío o fuera de AD, A, B, C → celda en `no_validas`.
4. **Conclusión**: `strip()`; en B y C, de 10 a 500 caracteres o la celda va a `sin_conclusion`; en AD y A se guarda vacía. 3 y 4 juntos lanzan `HojaConErrores(no_validas, sin_conclusion)`; el mensaje es el de la escala si hay alguna no válida, si no el de la conclusión.
5. Lee las notas actuales de esas celdas (una consulta) y aplica D7. Choques → `NotasCambiadas(celdas con su nota actual)`.
6. Crea con `bulk_create` las nuevas y actualiza las que cambian (`bulk_update`, con `actualizado_en` puesto a mano: `bulk_update` no pasa por `auto_now`), con `registrado_por=usuario`. Una celda igual a la base no se escribe. Si hubo creadas o cambiadas, NOTAS_GUARDADAS (D13).

Devuelve `ResultadoHoja(creadas, cambiadas, faltantes)`, con `faltantes = len(notas_faltantes(...))` dentro de la transacción.

- **Una nota no vuelve a vacía** (RN-023): una celda con nivel vacío es un valor no válido (paso 3); el servidor nunca borra una nota.
- **Alternativa descartada:** validar celda por celda y guardar las válidas: rompe RNF-011 y la decisión 12.
- **Alternativa descartada:** enviar la hoja completa: con 30 × 5 celdas el cuerpo crece en Slow 4G y obliga a comparar celdas que no se tocaron. Se envían solo las celdas del borrador.

### D6. Idempotencia

- Una celda cuyo valor actual ya es el enviado no cuenta como cambio ni como choque (D7). Así un envío repetido (respuesta perdida y «Reintentar») no escribe ni deja otra entrada de actividad.

### D7. Nota cambiada desde otro dispositivo (mecanismo que la decisión deja abierto)

- Cada celda del borrador guarda `base`: la nota (nivel y conclusión) que la hoja tenía guardada cuando la docente la editó, o `null` si estaba vacía. El envío la incluye.
- **Al abrir la hoja** con un borrador, el JS compara cada `base` con la nota que trae la página. Si difieren, la celda muestra «Ahora guardada: <nivel>», un aviso lista las celdas, y la `base` pasa a la nota de ahora: el siguiente «Guardar» guarda lo que muestra la hoja, porque la docente ya lo vio.
- **Al guardar**, el servidor compara la `base` con la nota actual: si difieren y la actual no es la enviada, choque. 409 con las celdas y su nota actual, sin guardar nada. El JS marca las celdas, actualiza su `base` y dice «N notas cambiaron en otro dispositivo. Revisa las celdas marcadas y vuelve a guardar.». El segundo «Guardar» guarda.
- Comparar valores, no una versión ni `actualizado_en`: no agrega columnas y un cambio que vuelve al mismo valor no es un choque real.
- **Alternativa descartada:** el último guardado gana: pisa en silencio la corrección hecha en el celular.
- **Alternativa descartada:** columna `version` por nota: más migración y el mismo resultado.

### D8. Rutas y vistas (`notas/urls_hoja.py`, `notas/views.py`)

- En `config/urls.py`: `docente/secciones/<int:seccion_id>/notas/` → `include("notas.urls_hoja")`, namespace `notas`. `""` GET (`HojaView`, `hoja`) y `<int:numero>/<str:area>/` POST (`GuardarHojaView`, `guardar`), con `area` = código SIAGIE. Un módulo aparte porque `notas/urls.py` ya es el namespace `competencias`.
- Las dos vistas usan `SeccionDocenteMixin` (404 sección ajena o año CERRADO; otro rol y sin sesión, `RolRequeridoMixin` con `HX-Redirect`).
- POST: cuerpo JSON `{"celdas": [{"estudiante", "competencia", "nivel", "conclusion", "base"}]}` con `X-CSRFToken` y `HX-Request`; JSON mal formado o tipos que no son → 400 con `HojaCambiada`. Respuestas: 200 `{"faltantes"}`; 400 `{"mensaje", "no_validas", "sin_conclusion"}` o `{"mensaje"}` (estructura); 404 periodo o área; 409 `{"mensaje"}` (periodo no editable) o `{"mensaje", "cambiadas"}` (D7). Los mensajes son constantes del servicio, nunca `str(excepción)` (lección de CodeQL en US-029).
- **Alternativa descartada:** formulario con campos repetidos, como US-029: las conclusiones y la `base` anidada lo vuelven frágil.

### D9. Pantalla (`templates/notas/hoja.html`, `static/js/notas.js`)

- El servidor dibuja el marco: título, «B3 · Vigente», «Competencias», avisos de periodo, la tira de áreas (botones con `aria-pressed`, el punto de pendientes y su texto para el lector), el `<dialog>` de salida, la barra de guardar y las regiones `role="status"`/`aria-live`. Pasa en `json_script` las áreas con columnas, filas, notas y faltantes (D2, D4), la URL de guardado y la clave del borrador (D10). Sin JavaScript: «Activa JavaScript para registrar las notas.».
- `notas.js` dibuja la rejilla del área visible desde los datos: un solo dibujante para PC y celular, para el filtro y para el cambio de área sin recarga. **Alternativa descartada:** el servidor dibuja la tabla y el JS la reescribe: dos dibujantes que se desalinean.
- Textos y estados del boceto (estados 01 a 21), incluidas las variantes de `notas.md` (singulares, «Volver a la hoja», «✓ Completa» en la fila, el «·» solo entre datos en la misma línea).

### D10. Borradores en `localStorage` (decisión 13)

- Módulo `static/js/notas-borrador.js`, sin dependencias, que usan `notas.js` y `menu.js`. Clave `cd:notas:v1:u<usuario>:s<seccion>:p<numero>:a<codigo>`; valor `{v: 1, fecha, rev, celdas: {"<estudiante>-<competencia>": {nivel, conclusion, base}}}`. Sin nombres de estudiantes, de áreas ni de competencias.
- Toda lectura y escritura va en `try/catch`; sin almacenamiento la hoja funciona sin conservar borradores. Una celda igual a lo guardado sale del borrador; un borrador sin celdas borra su clave.
- Al abrir: las celdas de estudiantes que ya no son activos o de competencias que ya no son columnas se descartan (no se podrían guardar) y la hoja lo dice en el aviso del borrador.
- Se borran: al guardar (la clave del área), al «Descartar» y al cerrar sesión: el formulario de `menu_cuenta.html` lleva `data-usuario`, y `menu.js`, al enviarse, borra las claves `cd:notas:v1:u<usuario>:`. En la hoja, el diálogo de salida intercepta antes (D11).
- **Alternativa descartada:** `sessionStorage`: no sobrevive a cerrar el navegador ni a otra pestaña, que la decisión 13 exige.

### D11. Dos pestañas y salida

- Antes de escribir, la pestaña vuelve a leer la clave y combina celda por celda con lo suyo (`rev` evita releer sin cambios); el evento `storage` trae en vivo lo que cambió solo la otra. Misma celda en ambas: queda lo de esta pestaña y un aviso nombra las celdas hasta guardar o descartar. Guardar combina primero y, con un choque nuevo, se detiene (boceto, «Harden»).
- Salida: el `<dialog>` de US-029 adaptado, en los enlaces y formularios que salen de la pantalla, con las áreas pendientes de todos los periodos de la cuenta y la sección. Para «Cerrar sesión», la línea dice que los borradores se borrarán. `beforeunload` mientras haya borradores. Los botones de la tira no salen de la pantalla.

### D12. Rejilla, panel y conclusión

- PC: `role="grid"` con `tabindex` itinerante; cada celda con etiqueta «<estudiante>, <competencia>, <nivel>» y `aria-keyshortcuts`. Teclas, barra compacta, recuadro de conclusión no modal (acompaña a su celda al desplazar y se cierra conservando el texto si la celda sale de la vista) y ayuda de C1…Cn como en el boceto.
- Celular (`matchMedia`, como US-029): panel inferior (`<dialog>`) con niveles de 44 px, conclusión y «Siguiente ↓»; «Rellenar vacías» con su acceso propio; bajo 360 px, áreas de 5 o más competencias con el nombre en su línea.
- Filtro «Pendientes de registro», conteo y cierre del área como el boceto (US-022 D4 a D6); `#conteo-vivo` anuncia solo cuando el número cambia.

### D13. Actividad e indicadores

- `Operacion.NOTAS_GUARDADAS` («Notas guardadas»), en `CUENTAN_KPI_01`. `DETALLE_PERMITIDO`: `{"area", "periodo", "creadas", "cambiadas"}`: código SIAGIE del área, número del periodo, cantidad creada y lista de pares `[estudiante, competencia]` cambiados. Entidad `seccion` y su id. Migración de `ck_actividad_operacion`.
- `indicadores_por_semana`: `secciones_con_notas` cuenta `entidad_id` distintos de NOTAS_GUARDADAS por semana, de cuentas reales no demo.
- **Datos de la tesis:** KPI-01 sale de `registro_actividad` (`usuario`, `fecha_hora`, `operacion` = NOTAS_GUARDADAS); «secciones con notas», de su `entidad_id`. Las notas mismas quedan en `calificacion` (`nivel`, `conclusion_descriptiva`, `registrado_por`, `creado_en`, `actualizado_en`).

### D14. Servicios de US-029 con notas (US-020 D17) y demo

- `competencias_con_notas(seccion, periodo)`: los id con al menos una `Calificacion` de estudiantes de la sección en el periodo, en una consulta. `tiene_notas` la usa; `CompetenciasView` la llama una vez por periodo editable y `guardar_marcas` una vez, en vez de una por competencia.
- `competencias_obligatorias`: el `universo` menos las competencias con alguna nota de la sección en cualquier periodo del año (una consulta). Una marcada antes sin notas vuelve a ser obligatoria.
- Las pruebas de US-029 que parchean `tiene_notas` pasan a usar notas reales.
- Demo: `_borrar` borra las `Calificacion` de los estudiantes de las secciones antes que los estudiantes; `Conteos.notas`; `DEMO_QUITADA` y `SECCION_DESCARTADA` suman la clave `notas`.

### D15. Portada y Competencias

- `dimensiones.py`: Notas con `url_name="notas:hoja"`, `disponible=True`, y `"notas"` en `POR_SECCION`. La hoja resuelve el periodo vigente o lleva a Competencias (D3).
- Competencias: acepta `?area=` (abre esa área en la cápsula y la pasa al volver) y `?desde=notas` (aviso de periodo sin competencias confirmadas). Suma el enlace «Registrar notas de B*n*» del periodo visible, que pasa por el diálogo de salida de US-029.

## Migration Plan

- Dos migraciones sin datos: `notas/0002` (tabla, restricciones e índice) y `actividad/0004` (choices y `ck_actividad_operacion`). Se aplican en local, en la CI y en el build de la vista previa de Vercel (Neon).
- Reversión: se revierten sin pérdida, salvo las notas guardadas; la bandera de Notas vuelve a `False` en el mismo revert.

## Open Questions

- Norma que exige la conclusión en B (US-020, pregunta abierta) → Marco / rama de Referencias. No cambia el diseño.
- ¿El SIAGIE acepta el Excel con celdas de nivel vacías? (US-022) → Nayely. No cambia este cambio; importa en US-024/025.
