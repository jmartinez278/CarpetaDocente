# Design: US-006 – Importar la lista de estudiantes de una sección

## Context

- Las decisiones de interfaz y de alcance están cerradas en `insumos/US-006-bocetos/decisiones-grill.md` (grill del 26-10 y revisión de bocetos del 27-10). Este design no las repite: agrega solo cómo se construyen y lo que quedaba abierto.
- `institucion` ya tiene `AnioEscolar`, `Seccion` y `servicios.py` (US-005). `texto_secciones_docente` arma la línea de la portada con " · ".
- `asistencia` y `notas` no tienen modelos todavía: hoy ningún estudiante puede tener registros.
- HTMX 2 ya se copia a `static/dist/vendor/` con `npm run build`, pero ninguna pantalla lo carga (`test_pantallas.py` lo comprueba en la portada). Context7 (htmx 2.0.4) confirma que no pinta respuestas 4xx sin `responseHandling` y que no procesa cabeceras `HX-*` en respuestas 3xx.
- `InactividadMiddleware` responde a una sesión vencida con un 302 a `/ingresar/`; `RolRequeridoMixin` hereda de `LoginRequiredMixin`.
- El boceto (`estudiantes.html`, `estudiantes.css`) es referencia de estructura, clases y textos; su CSS ya usa los tokens. Las capturas de referencia son las de `insumos/US-006-bocetos/capturas/`.

## Goals / Non-Goals

**Goals:**
- Separar la **lectura** del texto pegado (texto → filas) de la **validación y escritura** (filas → estudiantes, todo o nada), para que un lector de Excel futuro entregue las mismas filas (decisión 7b).
- Toda escritura pasa por `institucion/servicios.py`; las vistas no tocan el ORM para escribir.
- Un solo juego de plantillas para el diálogo y la página completa.

**Non-Goals:**
- Campos `estado`, `fecha_estado` y `codigo_estudiante` del doc 11 (US-030 y RF-025).
- Registrar al Estudiante en el panel de Django.
- Un lector de Excel, números de línea con enlace y "Atrás" que vuelve a la vista anterior (deuda del grill).

## Decisions

### D1. Modelo `Estudiante` en `institucion/models.py`

- `db_table = "estudiante"`; `seccion` FK `CASCADE` (doc 11; el cierre del año borra en cascada, RN-017), `related_name="estudiantes"`; `apellidos` y `nombres` `CharField(120)`.
- `UniqueConstraint(fields=["seccion", "apellidos", "nombres"], name="uq_estudiante")` con `violation_error_message`. El índice de `seccion` lo da la FK (`idx_estudiante_seccion`).
- `save()` normaliza con `servicios.normalizar_nombre` (importado dentro del método, como en `Seccion`): así la restricción compara siempre la forma guardada, por cualquier vía.
- `normalizar_nombre(texto)`: `" ".join(texto.split()).upper()`. `split()` también quita espacios duros (U+00A0) que trae Excel; `upper()` conserva tildes y Ñ (decisión 5).
- Sin `ordering` en `Meta`: el orden lo da D2.
- **Alternativa descartada:** crear ya `estado` y `fecha_estado` con ACTIVO por defecto. Se dejan a US-030, que define su regla (RN-027); agregar una columna con valor por defecto es una migración simple.
- **Para las tablas futuras** (calificación, asistencia, exoneración): FK a estudiante con `models.RESTRICT`, no `CASCADE` como el doc 11 (decisión del grill). Se anota en el docstring del modelo y en la deuda.

### D2. Servicios en `institucion/servicios.py`

- `secciones_docente(usuario)`: secciones del año ABIERTO con `docente=usuario`, ordenadas por grado y nombre. `texto_secciones_docente` pasa a usarla, sin cambiar su resultado: la línea de la portada sigue igual que en US-005.
- `seccion_unica(usuario)`: la sección del año ABIERTO si la docente tiene exactamente una, con su cantidad de estudiantes (`annotate(Count)`); si tiene varias o ninguna, `None`. La portada muestra "Ver estudiantes" y el aviso solo cuando no es `None`. Con varias secciones (no existe en la I.E., C8) no hay enlace: elegir una daría acceso parcial sin avisar. Las rutas igual funcionan para cada sección propia; solo falta la entrada.
- `texto_seccion_corto(seccion)`: "2.º A", para el título "Estudiantes de 2.º A".
- `estudiantes_ordenados(seccion)`: lista ordenada en Python con una clave que quita las tildes y pone la Ñ después de la N (`unicodedata`, NFD). Con 60 estudiantes como máximo no cuesta nada y no depende de la *collation* de PostgreSQL, que en local y en Neon puede ordenar "Á" después de "Z".
- `importar_lista(seccion, texto)`: lectura (D3) + validación + `bulk_create` dentro de `transaction.atomic`, con la fila de la sección bloqueada (`select_for_update`). **Pegar lista solo con la sección vacía:** dentro de ese bloqueo comprueba que la sección no tiene estudiantes y, si tiene, lanza `SeccionConEstudiantes` sin leer el texto. Así dos pestañas que importan a la vez no suman dos listas. Devuelve la cantidad importada o los errores; con errores no escribe nada.
- `agregar_estudiante(seccion, apellidos, nombres)` y `editar_estudiante(estudiante, apellidos, nombres)`: normalizan, validan con `full_clean()` (que aplica `uq_estudiante` con su mensaje) y guardan; un `IntegrityError` por carrera se traduce al mismo error.
- `quitar_estudiante(estudiante)` y `vaciar_lista(seccion)`: borran dentro de `transaction.atomic`. Si Django lanza `RestrictedError` o `ProtectedError` (un registro que apunta al estudiante), no se borra nada y el servicio lanza `ListaConRegistros`. Así la regla "solo sin asistencia ni notas" no depende de consultar tablas que aún no existen: aparece sola cuando US-030 cree `asistencia` con `RESTRICT`. Hoy el bloqueo se prueba simulando la excepción.

### D3. Lectura del texto pegado (`leer_lista_pegada`)

Función pura, sin base de datos. Recibe el texto tal como llegó y devuelve las filas `(linea, apellidos, nombres)` y los errores de formato.

1. Une los finales de línea (`\r\n` y `\r` → `\n`) y separa por `\n`. La línea se numera por su posición en el texto, contando las líneas en blanco, para que "Línea 7" sea la séptima línea que la docente ve en el cuadro. No se usa `splitlines()`, que también corta en caracteres como U+2028 y desfasaría la numeración.
2. **Confirmado: las líneas en blanco se ignoran.** Una línea en blanco es la que no tiene ningún carácter visible (solo espacios o tabulaciones, como la fila vacía que copia Excel); no da error y no cuenta como estudiante.
3. Si quedan más de 60 líneas con texto, devuelve solo ese error y no revisa línea por línea.
4. Cada línea con texto, un solo motivo, en este orden:
   - **Confirmado: una línea con tabulaciones es un error** ("pega solo la columna de apellidos y nombres"), tenga o no coma. Excel separa columnas con tabulaciones, así que es la señal de que se copió más de una columna.
   - Sin coma → "falta la coma entre apellidos y nombres"; más de una coma → "tiene más de una coma".
   - Se parte en la coma y cada lado se normaliza (D1); apellidos vacíos → "faltan los apellidos"; nombres vacíos → "faltan los nombres".
5. La validación (en `importar_lista`) revisa después las filas sin error de formato: más de 120 caracteres tras normalizar (primero apellidos) y repetidos, agrupados por la forma normalizada ("Líneas 4 y 12"; con tres o más, "Líneas 4, 9 y 12").
6. Los errores se ordenan por su primera línea. Cada uno lleva su ayuda (qué hacer), como en `#vista-4` del boceto.

El formulario usa `CharField(required=False, strip=False)`: con `strip=True`, Django quitaría las líneas en blanco del inicio y correría la numeración.

### D4. Rutas, en `institucion/urls.py` (`app_name = "estudiantes"`)

Incluidas en `config/urls.py` bajo `docente/secciones/<int:seccion_id>/estudiantes/`:

| Ruta | Métodos | Nombre | Vista (`#vista-N` del boceto) |
|---|---|---|---|
| `` | GET | `estudiantes:lista` | lista o vacía (2, 5) |
| `agregar/` | GET, POST | `estudiantes:agregar` | Agregar (6) |
| `pegar/` | GET, POST | `estudiantes:pegar` | Pegar lista y Revisar lista (3, 4); con estudiantes, el aviso sin el cuadro |
| `<int:estudiante_id>/editar/` | GET, POST | `estudiantes:editar` | Editar (7) |
| `<int:estudiante_id>/quitar/` | GET, POST | `estudiantes:quitar` | Quitar (8) y su bloqueo |
| `vaciar/` | GET, POST | `estudiantes:vaciar` | Vaciar (9) y bloqueo (9b) |

- Un mixin carga la sección con `get_object_or_404(servicios.secciones_docente(request.user), pk=seccion_id)` y el estudiante con `get_object_or_404(seccion.estudiantes, pk=estudiante_id)`. Otra docente o un año CERRADO dan 404 (la denegación con mensaje y registro es de US-004). Hereda de `RolRequeridoMixin` (Docente).
- Se actualiza el Catálogo de rutas de `docs/03`.

### D5. Una respuesta para el diálogo y para la página completa

- Cada vista renderiza el mismo parcial de contenido (`institucion/estudiantes/_<vista>.html`: cabecera con título, contador y "Cerrar"; cuerpo; pie). Con la cabecera `HX-Request: true` responde ese parcial más el aviso de la portada fuera de banda; sin ella, `pagina.html`, que extiende `marco.html` y lo envuelve en un panel de 640 px sin "Cerrar" y con el título como `h1` (en el diálogo, `h2`). Sin dependencia nueva: se lee la cabecera.
- **Precisión de la decisión técnica** ("las vistas internas reemplazan el cuerpo… contador por `hx-swap-oob`"): el pie y la acción de la cabecera cambian en cada vista, así que la respuesta reemplaza todo el contenido del diálogo, contador incluido. Solo el aviso de la portada (`#aviso-portada`), que está fuera del diálogo, va por `hx-swap-oob`. El resultado visible es el mismo que pide la decisión.
- **Éxito:** Post/Redirect/Get con 303 hacia la vista siguiente y el aviso de éxito por `django.contrib.messages` (una sola vez). El XHR de HTMX sigue la redirección y conserva `HX-Request` (mismo origen), así que el diálogo recibe el parcial; sin JavaScript, la página completa. "Guardar y agregar otro" redirige a Agregar con "Estudiante agregado".
- **Errores:** 200 con el formulario y sus mensajes (la decisión admite responder 200; evita configurar `responseHandling`).

### D6. Diálogo en la portada (`static/js/estudiantes.js`, sin Alpine)

- La portada tiene un `<dialog id="estudiantes" hx-target="this" hx-swap="innerHTML">` vacío; sus hijos heredan el destino. "Ver estudiantes" es un enlace real (`href` a la lista) con `hx-get`, sin `hx-push-url`.
- `estudiantes.js` (en `htmx:afterSwap` sobre el diálogo): si está cerrado, cierra el menú de la cuenta, bloquea el desplazamiento de la página y llama a `showModal()`; recuerda el enlace que lo abrió; lleva el foco al elemento `[data-foco]` del parcial (Apellidos en Agregar y Editar, el cuadro en Pegar, el título de la vista en las demás, con `tabindex="-1"`). El modal nativo deja la portada inerte; no se agrega una trampa de foco propia.
- **Cerrar:** "Cerrar" (`data-cerrar`) y Esc cierran; en `close`, el foco vuelve al enlace y se libera el desplazamiento.
- **Atrás cierra el diálogo (decisión 2c):** al abrir se agrega una entrada con `history.pushState` en la misma dirección; `popstate` con el diálogo abierto lo cierra; cerrar con Esc o "Cerrar" consume esa entrada con `history.back()`. HTMX ignora esa entrada porque no lleva su marca. Se prueba junto a `bfcache.js`.
- La portada carga HTMX (`dist/vendor/`) y `estudiantes.js` con `defer`; `test_pantallas.py` cambia su comprobación de scripts.

### D7. Sesión vencida con el diálogo abierto

- Helper `cuentas.acceso.redirigir(request, destino)`: si la petición trae `HX-Request`, responde 200 vacío con `HX-Redirect: <destino>` (HTMX no procesa cabeceras en un 3xx); si no, el 302 de siempre.
- Lo usan `InactividadMiddleware._cerrar_por_inactividad` (el aviso de inactividad se deja igual), `RolRequeridoMixin` sin sesión (`handle_no_permission`) y con otro rol. Con HTMX, `next` es la portada (`/docente/`), no la dirección del parcial.

### D8. Lo que DESIGN.md no cubre

DESIGN.md 0.3.1 no se toca. Va a `src/frontend/css/app.css`, en `@layer components`, con los tokens, tomado de `estudiantes.css` y de `notas.md` ("Reutilización y puntos no cubiertos por DESIGN.md"):

- Diálogo de 640 px en PC y hoja desde abajo en el celular (16 px de aire arriba), con grilla cabecera/cuerpo/pie y solo el cuerpo desplazable; fondo atenuado al 72 %, sin desenfoque ni sombra nueva.
- "Cerrar" como botón con el borde del botón secundario (1 px `--color-primario`, cápsula), ícono `x` y texto, de 44 px de alto como mínimo (decisión del grill; el "sin cápsula" de `notas.md` no aplica); "Volver a la lista", "Editar" y las acciones de riesgo (texto en `--color-error`) como enlaces de 44 px.
- `.boton-secundario` y `.mensaje--exito` (DESIGN.md los define; el CSS aún no los tiene).
- Fila de estudiante (número, nombre que baja de línea, "Editar"); cuadro de texto derivado de Campo.
- Foco de 2 px con `--color-primario` en los títulos que reciben foco (P2 de foco).
- Aparición de mensajes ≤200 ms solo con `opacity`; sin animación con "reducir movimiento".
- **Excepción de mayúsculas:** solo los nombres de estudiantes (y sus citas, como "¿Quitar a QUISPE MAMANI, ANA LUCÍA?") van en mayúsculas, como el SIAGIE. Títulos y demás textos, en escritura normal. Va también a "Para quien revise" del PR.

### D9. Textos nuevos (no estaban en el grill)

| Caso | Texto |
|---|---|
| Más de una coma | "Línea 6: tiene más de una coma" / "Deja una sola coma, entre apellidos y nombres." |
| Lado vacío | "Línea 5: faltan los apellidos" (o "los nombres") / "Escribe apellidos y nombres separados por una coma." |
| Más de 60 | "La lista tiene 61 líneas; el máximo es 60" / "Pega solo los estudiantes de tu sección." |
| Texto vacío | "Pega al menos un estudiante" / "Copia la columna de apellidos y nombres de tu Excel y pégala aquí" |
| Sección con estudiantes | "Tu sección ya tiene estudiantes" / "Agrega a los que falten con Agregar estudiante." |
| Homónimo (Agregar, Editar) | "Este estudiante ya está en la lista" / "Si son personas distintas, escribe el segundo nombre completo." |
| Quitar bloqueado | "No se puede quitar: el estudiante ya tiene registros" / "Si es un error, pide ayuda al administrador" |
| Contador e importados en singular | "1 estudiante", "1 estudiante importado" |

### D10. Pruebas

- **Unitarias, primero la prueba:** `institucion/tests/test_modelos_estudiante.py` (normalización, `uq_estudiante` por ORM y por `full_clean`, CASCADE desde la sección); `test_lectura_lista.py` (D3, función pura); `test_servicios_estudiantes.py` (importar todo o nada, sección con estudiantes, orden con tildes y Ñ, agregar, editar, quitar y vaciar con `RestrictedError` simulado, `seccion_unica`); `test_vistas_estudiantes.py` (acceso, parcial frente a página, PRG, errores con 200, Pegar lista con estudiantes, aviso fuera de banda, `HX-Redirect`).
- `cuentas/tests/test_pantallas.py` (enlace y aviso con una sección; sin ellos con varias o ninguna; la línea de US-005 sin cambios; scripts) y `test_inactividad.py` (`HX-Redirect`).
- **Punta a punta** (`institucion/tests/test_estudiantes_e2e.py`): los escenarios del criterio, diálogo (abrir, Esc, Cerrar, foco de vuelta, Atrás), sin JavaScript, sesión vencida, axe en ambos temas a 360 y 1280 px por vista, y 320 px sin desplazamiento horizontal. Solo nombres ficticios (los del boceto).

## Risks / Trade-offs

- **["JOSE" y "JOSÉ" son dos estudiantes]** → La restricción compara la forma guardada; las tildes cuentan. Se acepta: la docente ve los dos en la lista y corrige con Editar. Se anota para "Para quien revise".
- **[El bloqueo de quitar y vaciar no se puede probar con registros reales]** → Hoy se simula `RestrictedError`; US-030 debe agregar la prueba con una asistencia real (va a la deuda).
- **[`HX-Request` al seguir la redirección]** → El navegador conserva la cabecera en una redirección del mismo origen; la e2e lo confirma. Si fallara, la vista renderiza el parcial directamente en lugar de redirigir.
- **[Entrada de historial para "Atrás"]** → Puede chocar con `bfcache.js` o dejar una entrada de más; la e2e prueba abrir, Atrás, Esc y volver a abrir.
- **[Texto pegado enorme]** → `DATA_UPLOAD_MAX_MEMORY_SIZE` (2,5 MB por defecto) acota la petición, y la lectura corta en el error de 60 antes de revisar línea por línea.
- **[Docente con varias secciones: sin "Ver estudiantes"]** → No existe en la I.E. (C8). Se acepta como Minor: va a la deuda y a "Para quien revise". Si aparece, la entrada se diseña en otra historia.
- **[`update()`, `bulk_update` y `bulk_create` no llaman a `save()`]** → Solo `importar_lista` usa `bulk_create`, con filas ya normalizadas; se anota en su docstring.

## Migration Plan

- `institucion/0003` solo crea la tabla `estudiante`; se revisa con `sqlmigrate` antes del commit. En producción corre con el despliegue de EN-02. Reversión: `migrate institucion 0002`, que borra la tabla (en el Sprint 1 solo hay datos ficticios).
