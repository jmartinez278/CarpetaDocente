---
name: CarpetaDocente
description: Norma de diseño del rebrand cerrado, versión 1.1
---

# DESIGN.md · CarpetaDocente · 1.1

**Cerrado el 7 de noviembre de 2026 · versión 1.1.** Esta es la referencia normativa del diseño elegido para construir las pantallas en Django. «Debe» expresa un requisito. El cierre no significa que el prototipo o el producto ya cumplan toda la norma.

Notas toma como referencia visual `notas.html`: una columna NL por competencia, conclusión desde su icono y edición junto a la celda; en PC, hoja de ancho completo, nombre cerca del 40 % y competencias iguales en el resto. Inicio de sesión toma `ingreso.html`: Besley 600 solo para el nombre de la I.E.; el resto usa Instrument Sans. Estas decisiones del 7 de noviembre quedan integradas en esta versión.

Los antecedentes del proceso (LEEME, inventario visual, informes de Impeccable y de Emil, y el prototipo con sus CSS) están fuera del repositorio, en la carpeta de trabajo del equipo. No son norma: ante discrepancias, aplica este DESIGN.md. Los archivos *.html que nombran este documento y la sección «Pantallas» son las pantallas de ese prototipo.

## Usuarios y principios

Diseña para docentes de primaria, especialmente tutoras de aula, y dirección de una I.E. pública de Huayucachi, Huancayo. Prioriza el celular con 4G y conserva un trabajo eficiente en PC. Las tareas son registrar asistencia, trabajar notas por competencia y preparar o enviar sesiones a dirección.

- **Haz reconocible la tarea.** Mantén Asistencia como lista, Notas como hoja y Competencias como selección. La consistencia debe ayudar a trabajar sin borrar estas diferencias.
- **Haz visible el alcance.** Muestra fecha, área y bimestre donde determinan qué se edita o guarda. Una marca visible o un borrador recuperado no bastan para afirmar que algo quedó guardado.
- **Protege la continuidad.** Conserva los datos al fallar una validación, mantén el foco al cambiar de contexto y facilita corregir el problema desde su mensaje.
- **Usa la identidad con medida.** Conserva papel cálido, grafito, café y miniaturas esquemáticas. Reserva el acento para orientar; la legibilidad y los controles táctiles tienen prioridad sobre la densidad.
- **Representa solo hechos conocidos.** El prototipo contiene datos ficticios y almacenamiento local. No los conviertas en datos, servicios ni garantías de producción.

## Voz y textos

Escribe en español de Perú y usa tuteo: «Tu selección», «Revisa la conclusión», «Guarda los cambios». Emplea frases breves, verbos directos y nombres del trabajo docente. Mantén el mismo término para una misma acción; no alternes «guardar», «enviar» y «compartir» como si fueran equivalentes.

Los errores deben decir **qué pasó y qué hacer**, sin culpar y sin signos de exclamación. Usa el rechazo oficial «No se guardó nada», con la explicación y acción definidos en C-04. Conserva el borrador y ofrece «Ir a la primera conclusión pendiente» en ese rechazo. No prometas reintentos, sincronización, ayuda institucional o servicios que el producto no tenga.

No inventes funciones, servicios ni datos de la institución. Los nombres, fechas y cantidades de las plantillas de este documento son variables, nunca hechos del centro educativo. No conviertas «Compartida» o un contador de vistas en prueba de envío a dirección.

### Las seis reglas de contenido

1. **Niveles: solo AD · A · B · C.** No despliegues definiciones como «Logro destacado» o «Logro esperado». Mantén las siglas reconocibles en la hoja, los selectores y el panel.
2. **Asistió en verde y Faltó en rojo.** Conserva esta distinción por su reconocimiento inmediato. Tarde usa dorado y Justificado arena. Nunca comuniques el estado solo con color: usa ✓, ×, reloj o J, respectivamente, y el nombre completo para el lector de pantalla.
3. **Respeta el ciclo de RN-011:** Sin marcar → Asistió → Faltó → Tarde → Justificado → Asistió. Una marca ya guardada nunca vuelve a Sin marcar. Usa «Marcar los N restantes como Asistió» y, si queda uno, «Marcar el restante como Asistió». El lote debe ofrecer **Deshacer durante 5 s**: aplica el cambio provisional y **no lo guarda hasta que termina la cuenta**, salvo al ocultarse o cerrarse la página, cuando se guarda de inmediato. Deshacer cancela únicamente ese lote pendiente y restaura sus estados previos. Así no revierte marcas guardadas ni contradice RN-011.
4. **Exige conclusión en B y C, de 10 a 500 caracteres.** Si falta o no cumple el rango, no guardes nada del área; señala la celda y explica cómo corregirla.
5. **Una nota guardada no vuelve a vacía.** Permite cambiar el nivel, pero no borrar una nota ya guardada. «Rellenar vacías» solo actúa sobre vacías y ofrece AD o A.
6. **Usa botones con verbo y objeto o alcance inequívoco.** Conserva «Guardar», «Rellenar vacías» y «Marcar los N restantes como Asistió», con el singular de la regla 3. «Guardar» puede ser breve si la zona muestra de forma persistente el área o bimestre que abarca.

## Tokens — Colors

Usa un único valor por token y tema, definido en Quick Start. Los alias apuntan a ese valor; ningún componente debe redefinir un token global para cambiarle de significado. La portada y el trabajo interior deben consumir el mismo contrato, aunque hoy carguen CSS distintos.

| Tokens | Claro | Oscuro | Qué hacer y por qué |
| --- | --- | --- | --- |
| `--g-main` | `#F3EEE3` | `#202020` | Fondo de página; conserva el grafito aprobado en oscuro. |
| `--g-alt` | `#FAF6EF` | `#202020` | Fondo alterno; en oscuro no introduzcas otro grafito. |
| `--card` | `#FEFCF9` | `#342D27` | Hoja y tarjetas de trabajo. |
| `--sand` | `#E3D4AD` | `#E3D4AD` | Arena fija de esquemas y Justificado; no sustituye la superficie oscura. |
| `--folder` | `#E3D4AD` | `#4C4033` | Cabeceras y agrupaciones seleccionadas. |
| `--ink` | `#30271F` | `#F4EDE4` | Texto principal sobre las superficies del tema. |
| `--muted` | `#6E5746` | `#D1C2AD` | Texto secundario legible; no lo atenúes más mediante opacidad. |
| `--action` / `--action-ink` | `#76543E` / `#FEFCF9` | `#E0BF9C` / `#202020` | Acción sólida y su texto. El texto oscuro del botón se unifica en `#202020`. |
| `--line` / `--line-strong` | `#C2B290` / `#9F916A` | `#65584A` / `#9D8A73` | División de superficies / borde de controles. |
| `--gold` / `--gold-ink` | `#E9B70B` / `#976700` | `#E9B70B` / `#E9B70B` | Progreso y marca de cambios / indicador sobre el fondo del tema. No uses el dorado como texto sobre papel claro. |
| `--cocoa` / `--cocoa-line` | `#76543E` / `#76543E` | `#574A3E` / `#9D8A73` | Única zona café y su borde. |
| `--cocoa-ink` / `--cocoa-muted` | `#FEFCF9` / `#EADFCB` | `#F4EDE4` / `#E3D6C4` | Texto principal / secundario sobre café, común a todas las pantallas. |
| `--asistio` / `--asistio-ink` | `#2E7D4F` / `#FFFFFF` | `#5CB87F` / `#0E2016` | Estado Asistió y su símbolo. |
| `--falto` / `--falto-ink` | `#B3261E` / `#FFFFFF` | `#EE8379` / `#2A0B08` | Estado Faltó y su símbolo. |

Los puntos normales de asistencia deben seguir `--asistio` y `--falto`. Sobre café, usa los roles separados `--asistio-punto-cocoa` (`#8FD6A6`) y `--falto-punto-cocoa` (`#F7A39A`), iguales en ambos temas; así no se cambia el significado del token del estado.

Para Tarde, usa fondo `--gold`, texto fijo `#30271F` y borde fijo `#976700`; para Justificado, fondo `--sand`, texto fijo `#76543E` y borde fijo `#9F916A`. Quick Start los nombra como tokens `--tarde-*` y `--justificado-*`: el contraste del símbolo no debe invertirse por herencia del tema.

### Hoja, selección y validación

| Token | Claro | Oscuro | Uso obligatorio |
| --- | --- | --- | --- |
| `--grid-line` | `#E4D9C6` | `#4B4138` | Líneas internas de la matriz. |
| `--grid-head` | `#F3ECDF` | `#3D352E` | Cabeceras de la hoja. |
| `--grid-hatch` | `#ECE3D3` | `#433A32` | Trama de zonas no editables, con explicación textual. |
| `--row-hover` | `#FAF5EC` | `#3A312A` | Orientación de fila con puntero. |
| `--sel-bg` | `#EFE4D1` | `#463B31` | Selección de celda, junto con contorno. |
| `--warn-bg` / `--warn-ink` | `#FBEFC9` / `#6B4A00` | `#4A3C17` / `#F2D27A` | Advertencia o borrador recuperado, siempre con texto. |
| `--error` | `#B3261E` | `#FFB4AB` | Contorno y señal de error. |
| `--error-bg` / `--error-ink` | `#FBE8E6` / `#8C1D18` | `#4D2723` / `#FFDAD5` | Mensaje y celda inválida. |
| `--changed` | `#76543E` | `#E0BF9C` | Triángulo de cambios, acompañado del estado de guardado. |

Las miniaturas conservan una **paleta de papel fija en ambos temas**: `--preview-paper` `#FAF6EF`, `--preview-card` `#FEFCF9`, `--preview-ink` `#30271F`, `--preview-muted` `#6E5746`, `--preview-line` `#C2B290`, `--preview-action` `#76543E` y `--preview-sand` `#E3D4AD`. Usa estos roles para los esquemas y su sombra desplazada. El verde y rojo de las marcas esquemáticas sí siguen los tokens de asistencia del tema. Elimina `--coffee-light` y `--coffee-dark` como fuentes paralelas: el acento real usa `--cocoa`; la tinta sobre papel usa `--preview-action`.

## Tokens — Typography

**Decisión cerrada: Instrument Sans, normal 400 y 500, una sola familia.** Usa 400 para lectura y 500 para títulos, acciones y niveles. No introduzcas una familia de display, monoespaciada ni otra sans. `--font-display` debe ser alias de `--font-text`; Arial y sans-serif son únicamente respaldo ante un fallo de carga. No simules negritas o cursivas. **Única excepción (enmienda del 7 de noviembre):** el nombre de la I.E. en el inicio de sesión usa Besley 600 (`'Besley', Georgia, serif`), 40 px / 1,12 en PC y 30 px en celular, con tracking −0,01em y color `--action`. No uses Besley en ninguna otra pantalla, título ni componente.

| Rol y token | PC | Celular, hasta 699 px | Aplicación |
| --- | --- | --- | --- |
| Portada, `--text-home` | 42 px / 1,16 | 30 px / 1,18 | Título de bienvenida, 500; no trasladarlo a pantallas de trabajo. |
| Página de trabajo, `--text-page` | 36 px / 1,17 | 28 px / 1,2 | Título principal, 500. |
| Detalle de sesión, `--text-session` | 32 px / 1,2 | 26 px / 1,2 | Título de documento, 500; limita su medida a 24ch. |
| Sección, `--text-section` | 24 px / 1,3 | 20 px / 1,3 | Agrupación dentro de la página, 500. |
| Subsección, `--text-subsection` | 18 px / 1,4 | Igual | Subtítulos, 500. |
| Barra, `--text-toolbar` | 20 px / 1,3 | 18 px / 1,3 | Título compacto de orientación, 500. |
| Saludo de apoyo, `--text-greeting` | 24 px / 1,4 | 20 px / 1,4 | Línea anterior al nombre en portada, 400. |
| Principal, `--text-body` | 16 px / 1,5 | Igual | Nombres, contenido, campos, notas y texto completo del editor, 400; nivel de nota, 500. |
| Etiqueta importante, `--text-label` | 14 px / 1,5 | Igual | Cabeceras, acciones compactas, nombre de competencia, estado de asistencia y guardado. Es el mínimo, no un motivo para reducir texto de 16 px. |
| Apoyo, `--text-support` | 13 px / 1,5 | Igual | Solo datos auxiliares: número de fila, fecha o contador secundario. Nunca instrucciones, errores, estados decisivos ni botones. |

La vista previa de conclusión usa 14 px / 1,4 y hasta tres líneas junto al icono. El editor usa 16 px / 1,5. Conserva 26 px / 1 para los cuatro niveles del panel táctil (`--text-level`) y 36 px / 1,2 para el número principal del resumen (`--text-count`). El texto largo de la sesión mantiene 16 px / 1,8. No reduzcas tamaños para evitar desplazamiento.

Los nombres de estudiantes se almacenan y representan en **MAYÚSCULAS**, con tildes y nombres completos. Permite varias líneas y filas de altura adaptable para apellidos compuestos y dos nombres; no dependas de elipsis, hover o una fuente menor para identificarlos. En consulta de trasladados, conserva el nombre completo y presenta los campos como solo lectura, sin instrucciones de edición o borrador.

Usa tracking normal en lectura y etiquetas; reserva −0,035em para portada y título de página, −0,025em para sección y barra, y −0,015em para subsección y saludo. Activa `font-variant-numeric: tabular-nums` en números de fila, niveles y conteos. Conserva tildes, mayúsculas de nombres y signos propios del español.

En producción sirve **dos WOFF2 locales, 400 y 500, con subconjunto latino que incluya español**: áéíóú, ü, ñ/Ñ, ¿¡, º, ·, cifras y puntuación. Conserva la licencia OFL, `font-display: swap`, las funciones de cifras tabulares y caché de archivos estáticos. Los TTF actuales son un antecedente del prototipo: preparar WOFF2 sigue pendiente. La recomendación de Source Sans 3 del informe queda descartada por esta decisión. Para el inicio de sesión sirve además `besley-600-latin.woff2` (OFL, copiada de US-001), con `font-display: optional` y precarga solo en esa pantalla.

## Tokens — Spacing & Shapes

Usa la escala `--s-1…--s-8`: **4, 8, 12, 16, 24, 32, 48 y 64 px**. Aplica 8 px entre icono y etiqueta, 12–16 px dentro de controles y grupos pequeños, 24 px entre zonas de trabajo y 32–48 px entre bloques de página. No introduzcas un espaciado literal equivalente a un token existente.

El margen lateral `--gut` es **32 px**, y **20 px hasta 699 px**. La altura común de barra `--bar-height` es **72/64 px**. Las cifras 20 px de margen y 44 px de toque son medidas funcionales explícitas, no nuevos pasos de la escala.

| Token | Valor final | Cuándo usarlo |
| --- | --- | --- |
| `--r-sm`, `--r-btn` | 8 px | Botones, campos, editor y miniaturas; `--r-btn` es alias. |
| `--r-md` | 12 px | Cuenta, avisos, listas de opciones, cápsula de Competencias y tarjetas de listado. Reemplaza la cápsula de 14 px. |
| `--r-lg` | 20 px | Tarjeta café, bloques de Competencias y diálogos. |
| `--r-sheet` | 20 px; 16 px hasta 699 px | Hojas `.paper` y `.hoja`; esta adaptación debe ser un token, no una excepción dispersa. |
| `--r-pill` | 999 px | Píldoras de navegación y conteos. |
| `--r-round` | 50% | Cuenta y estados circulares. |
| `--touch-min` | 44 px en ambos ejes | Toda área interactiva, en PC y celular. |

Usa borde de 1 px para superficies y campos; 2 px para el círculo de asistencia. El foco general tiene 2 px de contorno y 4 px de separación, en `--focus-ring`. La celda conserva contorno interior de 2 px y de 3 px con foco visible, para que el recorte de la hoja no lo oculte. No confundas el diámetro del icono o checkbox con el tamaño del área que recibe el toque.

## Components

**Botones.** Usa 44 × 44 px como mínimo, padding habitual 10 × 16 px, separación de 8 px y radio de 8 px. El principal usa `--action`/`--action-ink`; el secundario, borde `--line-strong`; la acción de texto conserva área táctil completa. Dentro de café, invierte explícitamente con `--cocoa-ink` de fondo y `--cocoa` de texto, sin redefinir los tokens globales.

**Campos y mensajes.** Los campos usan `--card`, `--ink`, borde fuerte, mínimo 48 px de alto y texto de 16 px. Textarea permite varias líneas y crecimiento o desplazamiento interno. Asocia etiqueta, instrucción y error al control. No uses placeholder como única etiqueta ni opacidad como única explicación de un bloqueo.

**Hoja de Notas.** Presenta una columna NL por competencia. Junto a B o C muestra el icono de conclusión escrita o faltante. La faltante usa símbolo de error y color, con nombre accesible. AD y A se presentan sin ese icono. Usa 16 px para nombres y niveles, 14 px para cabeceras y vista previa. En PC la hoja ocupa todo el ancho: el nombre, cerca del 40 %, y las competencias se reparten el resto por igual. No centres el bloque ni dejes huecos a los lados. El nombre completo en MAYÚSCULAS debe ocupar una línea o dos como máximo en PC. En celular reserva 44 px a cada NL y asigna el resto al nombre. Mantén las filas adaptables y resáltalas con puntero y foco para conservar la orientación.

**Bimestre y áreas.** Muestra I–IV dentro de Notas y conserva el bimestre vigente al entrar. Mantén las áreas en orden SIAGIE y el área activa dentro del tramo visible. El acceso a Competencias debe quedar disponible fuera del tramo desplazable (C-03). Distingue selección con forma, texto y estado accesible; el punto dorado acompaña el mensaje de cambios pendientes.

Fijar Competencias no cambia su presentación: conserva el icono de checklist a la izquierda, el separador vertical y el espaciado original del botón. Solo las áreas se desplazan en el carrusel.

**Selección de Competencias.** Haz clicable la etiqueta completa del checkbox, con mínimo 44 × 44 px; el dibujo puede medir 22 px. Explica por qué no se puede desmarcar una competencia con notas o por qué queda forzada al cierre anual. Al cambiar de bimestre conserva o devuelve el foco al botón elegido, sin enviarlo a BODY (C-02).

**Menú, panel y diálogo.** El menú ☰ abre la navegación Inicio, Sesiones, Asistencia y Notas; marca la ubicación actual. Usa apertura por teclado y toque, Escape para cerrar y retorno de foco al disparador. El panel de notas del celular presenta AD/A/B/C en controles de al menos 64 px de alto, conclusión y «Siguiente ↓». No ocultes campos o acciones detrás del teclado virtual. Los filtros de Repositorio deben tener una agrupación semántica que admita nombre accesible; corrige `#active-filters` según C-01.

**Inicio de sesión.** Pantalla centrada, sin barra superior. Sigue este orden: espacio reservado del escudo (56 px en PC, 48 px en celular; vacío y sin contorno visible hasta que haya autorización de uso; conserva el espacio), nombre de la I.E. en Besley, filete corto de 40 px en `--line-strong`, lugar a 18 px y «Sesiones · Notas · Asistencia» a 14 px en `--muted`. Debajo va la ficha `--card` de hasta 440 px con radio `--r-lg`, que contiene Usuario, Contraseña, Ingresar a todo el ancho y la ayuda «Si olvidaste tu contraseña, pide al administrador que la restablezca.». No hay enlace de recuperación. Los campos miden 52 px, con fondo `--g-alt` y etiqueta visible. «Mostrar contraseña» es un botón de ojo de 44 × 44 px dentro del campo, con ese nombre accesible y `aria-pressed`. El error genérico va encima de la ficha con `role="alert"` y recibe el foco; no indica cuál campo falló, conserva el usuario y vacía la contraseña. Usa los textos oficiales de US-001. «Ingresando…» lleva indicador de giro y fondo `--folder` con `--ink`, no opacidad. Los campos quedan en solo lectura con borde punteado y el formulario anuncia `aria-busy`. El botón de tema va junto al pie «CarpetaDocente · 2026». Referencia: `ingreso.html`.

### Patrones

1. **Tarjeta café una sola vez por pantalla.** Usa ese único acento para Asistencia en portada, resumen del día en Asistencia, barra de guardado en Notas y «Tu selección» en Competencias. En la variante compacta de Competencias, la barra inferior sustituye al panel: no presentes ambos acentos a la vez. No añadas tarjetas café a Repositorio o Sesión para llenar una cuota; conserva su estructura de lectura y resultados. Nunca repitas el acento en dos zonas visibles de una pantalla.
2. **Un botón principal por zona.** Define la zona por su tarea —edición, guardado o diálogo—, no por cada fila. Las acciones auxiliares usan borde o texto. No dupliques Guardar en versiones simultáneamente visibles del mismo alcance.
3. **Miniaturas esquemáticas sin fotos.** Representa listas, hojas o niveles con líneas, formas y las siglas necesarias. No agregues fotos ni ilustraciones. No coloques información imprescindible en texto microscópico de miniatura: su nombre y metadatos deben estar fuera del dibujo.
4. **Barra de trabajo común.** En interiores coloca ☰, título, tema y cuenta, en ese orden funcional. La portada lleva solo tema y cuenta en su barra. Aplica la misma altura 72/64 px y las mismas áreas táctiles. El tema conserva sol/luna y nombre accesible de la acción.
5. **A-01: toda área de toque mide al menos 44 × 44 px.** Incluye códigos de competencia, Rellenar, Guardar/Descartar del borrador, filtros, días, cierres y enlaces de acción. Amplía la caja real sin solaparla con otro control; no basta agrandar el icono ni dibujar un pseudoelemento que tape una acción vecina.
6. **C-04: estado de guardado común.** Todo mensaje debe indicar **qué se hizo, qué abarca y si falta guardar**. Usa un lugar estable próximo a la acción o al resumen, con texto visible y anuncio accesible moderado. El icono o punto es complementario. Distingue edición, borrador local, guardado en curso, guardado confirmado y fallo; solo confirma después de que la operación tenga éxito.
7. **T-02. Icono, vista previa y editor de conclusión.** En PC, el icono junto a B/C abre una vista previa de dos a tres líneas con puntero y foco. Cumple WCAG 1.4.13 permitiendo recorrerla con el puntero, cerrarla con Escape y mantenerla visible mientras el puntero o el foco permanezcan en el disparador o su contenido. No uses temporizador. Clic o Enter sobre el icono y Alt+Enter en la celda abren el recuadro junto a ella. Elegir B o C abre directamente ese recuadro. Titúlalo «Conclusión anotada» y muestra estudiante · Cn, textarea multilínea de hasta 500 caracteres, «De 10 a 500 caracteres.», contador y «Listo». La lectura completa y la edición deben estar disponibles con teclado y toque. Al cerrar, devuelve el foco a la celda de origen. Retira «Leer y editar» de la cabecera en PC porque el icono cubre ese acceso. En celular conserva el panel inferior y el acceso a una conclusión existente al cambiar de nivel. Conserva ese texto en el borrador hasta aplicar las reglas de guardado.

#### Contrato del estado de guardado (C-04)

Los textos de la interfaz los fijan las specs del producto; DESIGN.md fija **forma, lugar y jerarquía**. El contexto visible (fecha, área o bimestre) completa el alcance sin alargar los textos oficiales. No redactes variantes libres para sustituirlos.

| Contexto | Conducta y alcance | Textos oficiales |
| --- | --- | --- |
| Asistencia individual | Guardado automático de la marca del estudiante y fecha activos. Estado estable en el resumen y estado pendiente junto al estudiante; no exige pulsar Guardar. | «Guardando…», «✓ Guardado»; fallo de marca: «Asistió · sin guardar. Reintentando…»; conteo: «N sin guardar». |
| Asistencia sin conexión | Aviso persistente próximo al resumen, conserva las marcas pendientes. | «Sin conexión» / «Tus marcas se guardarán cuando vuelva la señal. No cierres esta pantalla.» |
| Lote de Asistencia | Solo quienes estaban Sin marcar en la fecha visible. Lote provisional durante la cuenta, con las excepciones de ocultación y cierre descritas debajo. | «N marcados como Asistió · Deshacer (5)». |
| Asistencia completa | Cierre junto al resumen, únicamente con todas las marcas confirmadas y sin lote ni guardados pendientes. | «✓ Asistencia de hoy completa». |
| Notas | Guardado manual **por área y bimestre**, en la barra al pie de la hoja. El borrador local no confirma guardado. | «Sin cambios · Faltan N notas», «N cambios sin guardar · Sin notas faltantes», «✓ <área> completa». |
| Notas: rechazo | Validación atómica por área; mensaje junto a la hoja, conserva los cambios y permite llegar al primer error. | «No se guardó nada» + «Faltan N conclusiones en B y C. Escríbelas con 10 a 500 caracteres y vuelve a guardar <área>. Tus cambios siguen en la hoja.» Con una sola: «Falta 1 conclusión en B y C. Escríbela con 10 a 500 caracteres y vuelve a guardar <área>. Tus cambios siguen en la hoja.» Botón: «Ir a la primera conclusión pendiente». |
| Competencias | Guardado manual **por bimestre**, todas sus áreas. Estado en «Tu selección» o su sustituto móvil, junto al alcance y a Guardar. Conserva los textos actuales del prototipo. | «Sin guardar · confirma la selección», «Cambios sin guardar», «Guardando…», «Guardado», «Guardado a las <hora>»; confirmación «Competencias del <bimestre> guardadas.»; fallo «No se pudo guardar. Tus cambios siguen aquí. Reintenta.» |

Mantén el estado visible en un lugar estable; anuncia con una región `polite` al comenzar el guardado y al confirmar o fallar, sin duplicar el anuncio en dos regiones ni anunciar cada pulsación. Mientras otra área de Notas tenga cambios, conserva su indicador y no anuncies que todo está guardado.

En el lote, la cuenta de 5 s se **pausa con el puntero encima o con el foco de teclado** dentro del aviso, y continúa con el tiempo restante al salir ambos. Tocar un estudiante del lote lo saca de él: su nueva marca se guarda aparte y Deshacer ya no la afecta. Si la página se oculta o se cierra durante la cuenta, el lote se guarda de inmediato. No mezcles lotes pendientes. El lector anuncia una sola vez «N marcados como Asistió. Puedes deshacer durante 5 segundos»; no lee la cuenta regresiva. Deshacer restaura solo los integrantes todavía provisionales. El plazo no cambia con movimiento reducido.

## Iconografía

Usa SVG inline de una misma familia visual: viewBox 24 × 24, trazo de 1,6, `currentColor`, sin relleno y extremos/uniones redondos. El tamaño general es **22 px**; conserva 24–30 px solo en los accesos de portada y 18 px junto a mensajes. El área interactiva sigue siendo de 44 × 44 px como mínimo.

Usa tres líneas para ☰ y sol/luna para tema. Los iconos decorativos llevan `aria-hidden`; los controles sin texto visible deben tener nombre accesible que describa la acción. Conserva ✓, ×, reloj y J para asistencia con sus nombres completos. No uses emojis como sustituto de los SVG ni añadas otra biblioteca de iconos para un control aislado.

## Movimiento

Usa movimiento únicamente para responder a una acción y orientar el cambio de estado. Aplica entrada de color de **140 ms**, salida de **200 ms**, pulsación de **90 ms**, panel de **200 ms** y desplazamiento de menú de **240 ms**, con `cubic-bezier(.2,.8,.2,1)`. Los indicadores de navegación usan `cubic-bezier(.65,0,.35,1)`.

Con puntero fino, permite a botones subir 1 px al hover y bajar 1 px con escala 0,985 al pulsar. No muevas filas o celdas de una hoja al pasar el puntero. Cambia borde o texto para explicar un bloqueo; elimina el rebote de Competencias en favor del mensaje y el foco estables. No actives bucles automáticos de miniaturas, animaciones de fotos o contadores que retrasen leer el dato: los tokens heredados `--m-image`, `--m-cycle` y `--m-lift` no pertenecen al contrato 1.1.

Con movimiento reducido: sin desplazamiento, escala ni rebote; se permiten fundidos de opacidad y color de hasta 200 ms.

Reglas de interacción (enmienda del 8-11-2026, auditoría de Emil Kowalski, `INFORME-EMIL.md`):

1. No animes lo que se hace con el teclado (foco, navegación con flechas): el cambio es inmediato.
2. Una animación interrumpida continúa desde el estado visible, sin saltos (p. ej., cerrar el menú ☰ a medio abrir).
3. El efecto de pulsación (subida de 1 px, escala 0,985) solo con puntero fino y activación por puntero.
4. No animes `width` ni `height`; solo `transform` y `opacity`, además de color y borde con los tiempos de esta sección.

## Do's and Don'ts

| Haz | Evita | Motivo |
| --- | --- | --- |
| Usa el rol de título de cada superficie y una sola familia 400/500, salvo el nombre de la I.E. en el inicio de sesión (Besley 600). | Cambiar de fuente para silenciar el detector o crear tamaños por página sin rol. | La jerarquía ya queda cerrada. |
| Mantén texto principal de 16 px y etiquetas importantes de al menos 14 px. | Reducir nombres, errores, acciones o estados a 13 px para que quepan. | La densidad debe resolverse con layout y desplazamiento. |
| Muestra acción, alcance y estado real de guardado. | Dar por guardado un borrador local o un lote dentro de su cuenta. | El docente necesita saber qué queda pendiente. |
| Conserva café como un solo acento y miniaturas de papel esquemáticas. | Duplicar el panel café o introducir fotos. | La atención debe permanecer en el trabajo. |
| Abre un editor completo y accesible para conclusiones. | Depender de hover, tooltip o elipsis para leer el texto completo. | La lectura y edición deben funcionar con toque y teclado. |
| Usa icono, texto y color para estado y bloqueo. | Comunicar únicamente con color, opacidad o movimiento. | Debe comprenderse en ambos temas y con ayudas técnicas. |
| Usa datos reales del producto y ejemplos identificados como ficticios. | Inventar datos institucionales, sincronización, soporte o garantías de envío. | El diseño no crea capacidades de producto. |

## Surfaces

Usa `--g-main` como suelo de página, `--card` como superficie de trabajo y `--folder` para agrupación. Separa con borde antes que con sombra. En oscuro conserva el papel claro únicamente dentro de miniaturas; hojas, campos y diálogos usan las superficies oscuras.

La única tarjeta café usa `--cocoa-ink` y `--cocoa-muted` en todos sus textos, incluidos contadores y pie. No mantengas las redefiniciones locales de `--muted` o literales arena de `.cocoa .small`. Los enlaces y botones sobre café deben usar roles explícitos del acento.

Reserva sombras para elementos superpuestos: cuenta `0 12px 32px rgb(48 39 31 / .10)`, editor `0 16px 40px rgb(48 39 31 / .18)`, diálogo `0 24px 80px rgb(48 39 31 / .16)` y aviso `0 8px 24px rgb(48 39 31 / .12)`. El editor oscuro usa `0 16px 40px rgb(0 0 0 / .45)`. Las miniaturas usan sombra sólida `4px 4px 0 var(--preview-sand)`. No apliques estas sombras a todas las tarjetas. El panel inferior conserva radio de 20 px solo arriba; el menú lateral, solo en el borde derecho.

## Layout

Centra el contenido en **1120 px** como máximo y la hoja de Notas en **1280 px**, descontando dos márgenes `--gut`. Barra y pie deben alinear sus bordes con el contenido de la pantalla. Hasta 699 px cambia las variables de celular dentro de su media query; no las declares globalmente al final de la cascada.

- **Asistencia y Sesión:** contenido flexible más lateral de 304 px, separación 24 px; entre 700 y 960 px, lateral de 256 px y separación 20 px. Hasta 699 px, una columna. En Asistencia, el resumen precede a la lista y permanece accesible bajo la barra sin tapar filas ni foco.
- **Repositorio:** filtros de 208 px y resultados flexibles, separación 32 px; entre 700 y 960 px, 184 px y 24 px. Hasta 699 px, filtros en panel y búsqueda accesible. No permitas desplazamiento horizontal global.
- **Competencias:** lista más resumen de 320 px, separación 24 px; hasta 1100 px, resumen de 280 px. Hasta 899 px presenta un área a la vez y reemplaza el lateral por navegación compacta y guardado inferior. Este cambio estructural no reduce tipografía ni márgenes de celular antes de 699 px.
- **Notas.** Usa un único desplazamiento vertical de página. La hoja crece con sus filas y la cabecera C1…Cn queda sticky con `top: var(--bar-height)`. La barra café de Guardar permanece fija al pie y tiene compensación de espacio calculada con su altura real y `safe-area-inset-bottom`, para dejar visible la última fila. Usa `overflow: clip` para el redondeo de la hoja y conserva sus ancestros sin contenedores de scroll vertical. En PC la hoja ocupa todo el ancho: el nombre, cerca del 40 %, y las competencias se reparten el resto por igual. No centres el bloque ni dejes huecos a los lados. En celular usa NL de 44 px y el resto para el nombre. Cuando falte ancho, permite desplazamiento horizontal de competencias con nombre fijo y cabecera sincronizada, manteniendo la altura natural de la hoja. El detalle móvil se abre en el panel inferior.
- **Portada:** conserva la composición de 12 columnas: Asistencia ocupa 7 y dos filas; Sesiones y Notas, 5 cada una. Hasta 899 px apila los accesos. Hasta 699 px compacta las tarjetas secundarias con miniatura junto al texto. La barra comparte 72/64 px con el interior, aunque no sea sticky.

Mantén filas de Asistencia de al menos 76 px en PC y 80 px en celular. Conserva nombres legibles sin desplazar el botón de estado fuera de la pantalla. El scroll de una hoja densa está permitido; reducir texto o blancos táctiles para eliminarlo no lo está.

## Pantallas

| Pantalla | Qué debe conservar y resolver el pulido |
| --- | --- |
| `index.html` · Inicio | Tres accesos, saludo y contexto de aula; miniaturas esquemáticas; un solo acento en Asistencia; barra solo tema/cuenta. |
| `asistencia.html` · Asistencia | RN-011, fecha visible, lista con estados reconocibles, pendientes y resumen; guardado automático con excepción provisional del lote y Deshacer de 5 s. En celular, el lote va debajo del resumen y antes de la lista. En celular, el resumen muestra siempre «N/M · K sin marcar» junto al estado de guardado: N es el número de marcados, M el total y K los pendientes, también cuando K es cero. |
| `notas.html` · Notas | Bimestre dentro de la pantalla, área visible en tira SIAGIE, botón estable de Competencias y hoja por área. Una columna NL por competencia, icono de conclusión junto a B/C, vista previa y editor completo. Desplazamiento vertical de página, cabecera sticky y Guardar fijo. Borrador diferenciado de guardado manual. Trasladados al final en solo lectura y vacío con acceso a Competencias cuando falten selecciones. |
| `competencias.html` · Competencias | Selección por bimestre, transversales y orden SIAGIE; Inglés y Educación Física atenuadas sin marcar ni contar, conforme al contexto existente. Bloqueos explicados; un Guardar para todo el bimestre; foco estable al cambiarlo. |
| `repositorio.html` · Repositorio | Pestañas, búsqueda, filtros activos semánticos, resultados y miniaturas; filtros laterales en PC y panel en celular. |
| `ingreso.html` · Inicio de sesión | Identidad de la I.E. con Besley, ficha centrada sin barra, error genérico sobre la ficha y estado «Ingresando…» de solo lectura, sin recuperación de contraseña. |
| `sesion.html` · Sesión | Lectura completa de archivo, propósito y texto; metadatos próximos al título; distinguir edición, compartir y envío a dirección. Mostrar confirmación de envío solo si el estado real lo acredita. |

Estas siete pantallas delimitan el sistema documentado. No deduzcas una bandeja de dirección, estados remotos ni otras funciones por una referencia visual del prototipo.

## Decisiones cerradas

| Decisión normativa | Estado frente al producto |
| --- | --- |
| Selector de bimestre dentro de Notas. | **requiere cambio de spec en el repo** |
| Una columna NL por competencia, icono de conclusión escrita o faltante junto a B/C, vista previa y recuadro completo junto a la celda. Panel inferior en celular. | **Coincide con la spec actual del repo. No requiere cambio de spec**, por decisión del usuario del 7 de noviembre de 2026. |
| Deshacer de 5 s del lote de Asistencia; guarda al vencer la cuenta o de inmediato al ocultar/cerrar la página. | **requiere cambio de spec en el repo** |
| Botón de tema en la barra; en el producto entra como requisito aparte **T-04**. | **requiere cambio de spec en el repo** |
| Menú ☰ como acceso a la navegación interior. | **requiere cambio de spec en el repo** |

Instrument Sans 400/500 (con la única excepción de Besley en el nombre de la I.E. del inicio de sesión), paleta, roles de títulos, escala de formas y los patrones A-01, C-04 y T-02 quedan cerrados por esta versión. No reabras estas decisiones durante el pulido. Actualizar specs y construir en Django son tareas posteriores; no se han ejecutado como parte de este cierre.

## Quick Start

Este bloque contiene los **tokens finales compartidos**. Sin elección explícita, el tema sigue `prefers-color-scheme`, también cuando cambia el sistema. `html[data-theme=dark]` conserva la elección oscura y `data-theme=light` excluye el oscuro del sistema. El botón de tema es el requisito aparte **T-04**. No es una transcripción de la cascada actual. Copia un solo contrato compartido por portada e interiores; mantén la única variación de cada token en su tema o media query. Los aliases conservan su significado en todos los componentes. Los valores de celular están exclusivamente dentro de `@media (max-width:699px)`.

```css
:root {
  color-scheme: light;
  --g-main: #F3EEE3;
  --g-alt: #FAF6EF;
  --bg: var(--g-main);
  --card: #FEFCF9;
  --sand: #E3D4AD;
  --folder: #E3D4AD;
  --ink: #30271F;
  --muted: #6E5746;
  --action: #76543E;
  --action-ink: #FEFCF9;
  --line: #C2B290;
  --line-strong: #9F916A;
  --gold: #E9B70B;
  --gold-ink: #976700;
  --cocoa: #76543E;
  --cocoa-line: #76543E;
  --cocoa-ink: #FEFCF9;
  --cocoa-muted: #EADFCB;
  --focus-ring: var(--action);

  --asistio: #2E7D4F;
  --asistio-ink: #FFFFFF;
  --falto: #B3261E;
  --falto-ink: #FFFFFF;
  --asistio-punto: var(--asistio);
  --falto-punto: var(--falto);
  --asistio-punto-cocoa: #8FD6A6;
  --falto-punto-cocoa: #F7A39A;
  --tarde-bg: var(--gold);
  --tarde-ink: #30271F;
  --tarde-line: #976700;
  --justificado-bg: var(--sand);
  --justificado-ink: #76543E;
  --justificado-line: #9F916A;

  --grid-line: #E4D9C6;
  --grid-head: #F3ECDF;
  --grid-hatch: #ECE3D3;
  --row-hover: #FAF5EC;
  --sel-bg: #EFE4D1;
  --warn-bg: #FBEFC9;
  --warn-ink: #6B4A00;
  --error: #B3261E;
  --error-bg: #FBE8E6;
  --error-ink: #8C1D18;
  --changed: #76543E;

  /* Papel de miniaturas: fijo en claro y oscuro. */
  --preview-paper: #FAF6EF;
  --preview-card: #FEFCF9;
  --preview-ink: #30271F;
  --preview-muted: #6E5746;
  --preview-line: #C2B290;
  --preview-action: #76543E;
  --preview-sand: #E3D4AD;

  --font-text: 'Instrument Sans', Arial, sans-serif;
  --font-display: var(--font-text);
  --weight-body: 400;
  --display-weight: 500;
  --text-home: 42px;
  --text-page: 36px;
  --text-session: 32px;
  --text-section: 24px;
  --text-subsection: 18px;
  --text-toolbar: 20px;
  --text-greeting: 24px;
  --text-body: 16px;
  --text-label: 14px;
  --text-support: 13px;
  --text-level: 26px;
  --text-count: 36px;
  --leading-home: 1.16;
  --leading-page: 1.17;
  --leading-session: 1.2;
  --leading-section: 1.3;
  --leading-subsection: 1.4;
  --leading-toolbar: 1.3;
  --leading-greeting: 1.4;
  --leading-text: 1.5;
  --leading-preview: 1.4;
  --leading-session-text: 1.8;
  --leading-level: 1;
  --leading-count: 1.2;
  --tracking-page: -.035em;
  --tracking-section: -.025em;
  --tracking-subsection: -.015em;

  --s-1: 4px;
  --s-2: 8px;
  --s-3: 12px;
  --s-4: 16px;
  --s-5: 24px;
  --s-6: 32px;
  --s-7: 48px;
  --s-8: 64px;
  --r-sm: 8px;
  --r-btn: var(--r-sm);
  --r-md: 12px;
  --r-lg: 20px;
  --r-sheet: var(--r-lg);
  --r-pill: 999px;
  --r-round: 50%;
  --touch-min: 44px;
  --gut: 32px;
  --bar-height: 72px;
  --content-max: 1120px;
  --sheet-max: 1280px;

  --shadow-account: 0 12px 32px rgb(48 39 31 / .10);
  --shadow-editor: 0 16px 40px rgb(48 39 31 / .18);
  --shadow-dialog: 0 24px 80px rgb(48 39 31 / .16);
  --shadow-toast: 0 8px 24px rgb(48 39 31 / .12);
  --shadow-preview: 4px 4px 0 var(--preview-sand);
  --m-in: 140ms;
  --m-out: 200ms;
  --m-press: 90ms;
  --m-panel: 200ms;
  --m-slide: 240ms;
  --m-ease: cubic-bezier(.2,.8,.2,1);
  --m-ease-io: cubic-bezier(.65,0,.35,1);
}

html[data-theme=dark] {
  color-scheme: dark;
  --g-main: #202020;
  --g-alt: #202020;
  --card: #342D27;
  --folder: #4C4033;
  --ink: #F4EDE4;
  --muted: #D1C2AD;
  --action: #E0BF9C;
  --action-ink: #202020;
  --line: #65584A;
  --line-strong: #9D8A73;
  --gold-ink: #E9B70B;
  --cocoa: #574A3E;
  --cocoa-line: #9D8A73;
  --cocoa-ink: #F4EDE4;
  --cocoa-muted: #E3D6C4;
  --asistio: #5CB87F;
  --asistio-ink: #0E2016;
  --falto: #EE8379;
  --falto-ink: #2A0B08;
  --grid-line: #4B4138;
  --grid-head: #3D352E;
  --grid-hatch: #433A32;
  --row-hover: #3A312A;
  --sel-bg: #463B31;
  --warn-bg: #4A3C17;
  --warn-ink: #F2D27A;
  --error: #FFB4AB;
  --error-bg: #4D2723;
  --error-ink: #FFDAD5;
  --changed: #E0BF9C;
  --shadow-editor: 0 16px 40px rgb(0 0 0 / .45);
}

@media (prefers-color-scheme: dark) {
  :root:not([data-theme=light]) {
  color-scheme: dark;
  --g-main: #202020;
  --g-alt: #202020;
  --card: #342D27;
  --folder: #4C4033;
  --ink: #F4EDE4;
  --muted: #D1C2AD;
  --action: #E0BF9C;
  --action-ink: #202020;
  --line: #65584A;
  --line-strong: #9D8A73;
  --gold-ink: #E9B70B;
  --cocoa: #574A3E;
  --cocoa-line: #9D8A73;
  --cocoa-ink: #F4EDE4;
  --cocoa-muted: #E3D6C4;
  --asistio: #5CB87F;
  --asistio-ink: #0E2016;
  --falto: #EE8379;
  --falto-ink: #2A0B08;
  --grid-line: #4B4138;
  --grid-head: #3D352E;
  --grid-hatch: #433A32;
  --row-hover: #3A312A;
  --sel-bg: #463B31;
  --warn-bg: #4A3C17;
  --warn-ink: #F2D27A;
  --error: #FFB4AB;
  --error-bg: #4D2723;
  --error-ink: #FFDAD5;
  --changed: #E0BF9C;
  --shadow-editor: 0 16px 40px rgb(0 0 0 / .45);
  }
}

@media (max-width:699px) {
  :root {
    --gut: 20px;
    --bar-height: 64px;
    --r-sheet: 16px;
    --text-home: 30px;
    --text-page: 28px;
    --text-session: 26px;
    --text-section: 20px;
    --text-toolbar: 18px;
    --text-greeting: 20px;
    --leading-home: 1.18;
    --leading-page: 1.2;
  }
}
```

Al aplicar los tokens, usa `font-synthesis: none`, herencia de fuente en controles y los roles de texto anteriores. Conecta `--touch-min` a **min-width y min-height**, y `--r-sheet` a las hojas. Añade la regla de movimiento reducido al implementar las transiciones; el bloque de tokens no implementa los componentes ni las reglas de guardado.
