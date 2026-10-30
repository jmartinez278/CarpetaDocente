# CarpetaDocente — Design System

> Un aula cálida y ordenada: el café del uniforme, con sus franjas arena, y el dorado del escudo enmarcan la pantalla; el trabajo diario ocurre sobre papel casi blanco, tranquilo y legible.

**Theme:** claro y oscuro. El tema sigue la preferencia del sistema (`prefers-color-scheme`); no hay selector en la interfaz (el selector será un RF aparte, después del Sprint 1).
**Estado:** propuesta 0.4 · 29-10-2026 · insumo para Impeccable (ruta B) y para el prototipo (evidencia local, fuera del repositorio). Los colores salen de fotos y afiches de la I.E. (aproximados) y pasaron filtros WCAG 2.x, APCA y simulación de daltonismo. Este archivo es la referencia visual del proyecto (CLAUDE.md, sección Interfaz); la ratifica la aprobación, por otra integrante, del PR que lo incorpora (cierra C7).
**Cambios 0.2:** tarjetas café con franjas del uniforme y miniatura que desborda; botón principal en píldora; fuente de títulos por definir con `/impeccable typeset`; tuteo; títulos cortos con subtítulo formal; una sola librería de íconos; movimiento solo funcional; asistencia de 5 columnas en computadora; criterio de "listo para docentes".
**Cambios 0.3** (revisión del prototipo de US-001, tramo 4, variante G4e):
- Fuente de títulos Besley 600, definitiva (alojada, subconjunto latino, 17 KB; en 0.3.1 llega por npm, ver Títulos). Íconos Lucide 1.52.0 (trazo 1,75 px). Radios sin cambios.
- Tema oscuro por preferencia del sistema: cada token de color tiene valor claro y oscuro. Regla de roles: en claro, café sobre arena; en oscuro, arena sobre café.
- `--color-fondo` cambia de crema afiche `#fcf4e1` a neutro cálido `#f3eee3`. El crema afiche sale del sistema y se retira su segundo rol ("texto sobre café"): en claro ya no hay superficies café con texto.
- `--color-primario` deja de ser fondo de barra y de tarjetas: queda como color de acción y acento (botón principal, enlaces, foco, títulos del marco, franjas de la tarjeta disponible). En oscuro vale arena.
- `--color-dorado` deja de usarse como franja bajo la barra (la barra café se descarta) y como fondo de la insignia "Próximamente" (ahora callada, en `--color-dorado-texto`); queda para detalles.
- Tokens nuevos: `--color-dimension` (tarjeta disponible), `--color-linea` (líneas finas decorativas), `--color-sobre-primario` (texto e íconos sobre el color de acción y sobre los estados) y `--color-sobre-claro` (texto sobre dorado y tintes en ambos temas).
- `--text-display` pasa de 32/44 px a 27/40 px (celular/PC): el nombre de la I.E. y el saludo caben en una línea a 360 px.
- No hay tokens retirados. `--color-dorado` queda sin uso en las pantallas de US-001 (reservado para detalles).
- Componentes nuevos o rehechos: tarjeta de dimensión G4e, carrusel de dimensiones (única excepción al desplazamiento horizontal), barra con el nombre de la I.E., inicio de sesión centrado y pie.
- Revisión del prototipo (tramo 5): miniatura esquemática, sin datos que parezcan de la docente; botón "Mostrar contraseña"; mensaje de error con qué hacer (texto de US-001); barra sin menú hasta US-002; insignia "Próximamente" callada; la tarjeta "Próximamente" responde al toque con "Disponible pronto".
- Revisión del prototipo, ronda 2 (tramo 5): la insignia "Próximamente" va siempre en su propia línea, arriba a la derecha, y nunca tapa el título; el chip seleccionado va sin relleno y los chips no agregan entradas al historial; toda la tarjeta disponible responde, también lo que sobresale de la miniatura, y dice qué hace ("Registrar asistencia", al pie de la cabecera); el anillo de foco rodea solo la tarjeta; miniatura de asistencia sin día y casi sin marcar; tintes apagados en "Próximamente"; estado vacío fijo de la dirección en el Sprint 1; "Ingresando…" más visible, con los campos de solo lectura; renglón propio para el aviso de "Próximamente", que pasa a "Llegará en una próxima versión."; mensaje de error en dos pesos; la tarjeta que asoma en el carrusel no responde.
**Cambios 0.3.1** (22-10-2026, aplicación de US-001, antes de construir las plantillas):
- Besley llega por npm desde `@fontsource/besley`, como HTMX y Alpine, en lugar del subconjunto propio del prototipo (design de US-001, D9).
- Botón principal mientras envía: `aria-disabled` y campos de solo lectura, no `disabled` (design de US-001, D6).
- El inicio de sesión carga el JavaScript propio de "Mostrar contraseña" y del estado de envío.
- Tratamiento ("Prof.") y grado en los ejemplos: se muestran cuando el sistema guarde esos datos (design de US-001, D8; US-005).
- Disponibilidad de las tarjetas: al cerrar US-001, las tres en "Próximamente"; con US-030, solo Asistencia.
- Las referencias a rutas locales del prototipo pasan a "evidencia local".
**Cambios 0.4** (29-10-2026, dirección visual 0.3 de `prototipos-cd`, US-030; decisión: AB-3 con la barra de línea tenue y cabeceras con franjas cortas; ningún cambio toca los colores de estado de asistencia, las filas de la lista ni el ciclo de toques):
- la barra superior conserva su línea inferior de 1px, pero más tenue: `--color-linea` al 55 % con `--color-fondo`, en claro y en oscuro, para que el nombre de la I.E. flote sobre la banda de la barra; se descartó una línea dorada de 2px (`--color-dorado` al 50 %), porque se veía amarillo limón en claro y oliva en oscuro; las medidas de lo fijo bajo la barra no cambian; el descarte «Barra café con franja dorada» sigue vigente; la cabecera de cada pantalla de trabajo lleva el ícono de su dimensión (el de su tarjeta, 24px en `--color-primario`) junto al título y, debajo, las franjas del uniforme cortas (48px; 3px y 2px, separadas 6px) en el tinte de su dimensión (`--color-tinte-sesiones`, `--color-tinte-notas`, `--color-tinte-asistencia`, iguales en claro y en oscuro); sin banda ni fondo; el título baja: 24px de aire bajo la barra en celular y 32px en PC; la portada, la lista de estudiantes, la cuenta y el ingreso no llevan franjas (en el ingreso irá la insignia del colegio); regla: las franjas son líneas, nunca fondo ni detrás de texto, una pareja por pantalla en la primera vista (salvo las tarjetas de la portada y el cierre de jornada); los acentos de dimensión dejan de usarse solo dentro de la miniatura; saludo de la portada según la hora («Buenos días», «Buenas tardes», «Buenas noches») sobre `--color-fondo`, con la fecha delante de la sección («Miércoles 28 de octubre · 2.º grado, sección A») y `text-wrap: balance` cuando no cabe en una línea; asistencia de hoy pendiente: «Hoy: pendiente» con `clock` en `--color-aviso`, en una píldora de `--color-superficie` (14px/600, `--radius-pill`) dentro de la tarjeta Asistencia; en celular, arriba a la derecha, en el lugar de la insignia; en PC, centrada en el hueco entre el subtítulo y la acción, con `--d-sangria`; sin enlace propio (la tarjeta entera es el enlace), descrita por `aria-describedby`; con la jornada completa no está, y las tarjetas quedan iguales (dato real que provee US-030); el Mensaje de éxito de la lista de estudiantes puede llevar un enlace de 44px al paso siguiente («Tomar la asistencia de hoy»); cierre de jornada: con la lista completa y guardada (sin marcas pendientes ni un «Marcar todos» por deshacer; sin conexión no hay cierre), el resumen muestra «Asistencia de hoy completa» en `--font-display` 600 de 20px y `--color-primario`, con `check` en `--color-exito` (más grande que el texto del panel, de 14px en celular y 16px en PC), y las franjas del uniforme reemplazan la línea inferior de la franja fija (en PC, la barra de progreso al 100 %), sin botones ni pasos nuevos; Movimiento admite **dos** momentos de autor, uno por pantalla: en la portada, «Hoy: pendiente» aparece una vez con una subida corta (`opacity` y `transform: translateY` de 6px, 420ms, `cubic-bezier(0.16, 1, 0.3, 1)`, 300ms de espera; con «reducir movimiento», ya está en su lugar); en la asistencia, las franjas del cierre se trazan una vez, de izquierda a derecha (`transform: scaleX`, 480 ms, `cubic-bezier(0.16, 1, 0.3, 1)`), y con «reducir movimiento» aparecen sin trazarse; «Asistencia en PC» pasa a: lista de hoy a la izquierda y panel de la jornada a la derecha, sin fondo (fecha, selector de semana, avance, totales, «Marcar todos», leyenda y guardado), en lugar de las 5 columnas de días (decisión 9 de US-030, variante 10a); «Marcar todos como Asistió» es Botón secundario (acción en lote) y dice cuántos marca: «Marcar los 7 restantes como Asistió» («el restante» si queda uno), sin la ayuda de debajo; «restantes» porque «faltar» es el estado Faltó, y en celular la lista empieza en el primer pliegue: el aviso sin conexión es un Mensaje de error compacto (ícono `circle-alert`, «Sin conexión» 16px/600 en `--color-error` y «qué hacer» 14px en `--color-texto`, padding 12px 14px) y no repite el nombre de la marca sin guardar (ya está en su fila y en «1 sin guardar»); en la franja fija, «N sin guardar» cuenta solo las marcas que fallaron, y una marca en curso dice «Guardando…» en `--color-texto-suave`; en oscuro, los círculos de la leyenda llevan ícono y letra en `--color-texto` y la leyenda de la lista va plegada, en una línea de 44px con los cuatro estados en orden, y abierta muestra sus nombres; «Nunca texto en mayúsculas sostenidas» gana una excepción: el nombre completo del estudiante y las marcas «RETIRADO» y «TRASLADADO» (decisión 7).
- Pendiente: en claro, las franjas salvia de la cabecera son tenues sobre el papel; revisarlas cuando existan Sesiones y Notas (ver `decision-final/capturas/cabeceras-*-claro.png`); probar la línea tenue de la barra y las franjas de la cabecera con sol en el celular.

CarpetaDocente (nombre provisional) es una aplicación web para docentes de primaria de la I.E. Virgen del Carmen (Huayucachi, Junín, Perú). Se usa sobre todo desde el celular, con datos móviles (referencia: 4G lento), dentro del aula o en el patio con sol; la dirección la usa en computadora. Debe sentirse institucional, cálida y confiable: ni plantilla genérica de SaaS ni sistema estatal antiguo.

**Regla de color "identidad en el marco, comodidad en el contenido":** café, arena y dorado viven en el marco (inicio de sesión, portada, tarjetas de dimensión, encabezados). Las zonas de trabajo (listas, formularios, asistencia, notas) van sobre superficies neutras casi blancas (en oscuro, casi negras y cálidas). Proporción 60 % neutro cálido · 30 % café y arena · 10 % acento. El 10 % de acento lo lleva el café; el dorado (`#e9b70b`) queda para detalles y no se usa en US-001.

**Regla de roles entre temas:** en claro, café sobre arena (título, ícono y franjas café sobre la tarjeta arena; botón café). En oscuro, arena sobre café (franjas y títulos arena sobre la tarjeta café; botón arena). En oscuro el café no se usa como texto ni como botón.

**Referencia de tono:** la página de base de conocimiento de Slite (lienzo cálido, mucho aire, el producto como ilustración, fichas que desbordan su contenedor). Solo para portada e inicio de sesión: las pantallas de trabajo son más calladas. Para el inicio de sesión, la composición del de claude.ai: centrado sobre fondo de color, formulario en tarjeta con borde fino y un solo acento.

## Usuarios y principios

| Grupo | Necesita | Decisión de diseño |
|---|---|---|
| Escépticos | Que se vea oficial y serio | Sobrio, bordes finos, sin animaciones llamativas, nombre de la I.E. visible |
| Desinteresados | No aprender nada | Una sola acción principal por pantalla; tareas en 1–2 toques |
| Docentes promedio | Patrones conocidos | Formularios y listas como en apps de banca o mensajería; nada de gestos ocultos |
| Recién llegados | Saber qué hacer | Estados vacíos que explican el siguiente paso |
| Jóvenes | Rapidez y aspecto moderno | Pantallas livianas, píldoras, esquinas redondeadas, tema oscuro del sistema |
| Dirección | Visión de conjunto | En computadora: más densidad y tablas; el mismo marco |

## Voz y textos

- **Tuteo** en toda la interfaz: "Ingresa tu contraseña", "Tu sección aparecerá…".
- Frases cortas, verbo primero en botones ("Ingresar", "Marcar todos como Asistió").
- Errores: qué pasó y qué hacer, sin culpar. Sin signos de exclamación en mensajes del sistema.
- Nunca inventar funciones, servicios ni datos institucionales (ej.: no "¿Olvidaste tu clave?" con enlace propio, porque la clave la restablece el administrador; no textos sobre servidores o soporte que no existen).

## Tokens — Colors

Cada token tiene un valor por tema; el HTML solo usa clases de los tokens, nunca hex. Contrastes contra el fondo indicado (WCAG 2.x).

### Marco y superficies

| Token | Rol | Claro | Oscuro |
|---|---|---|---|
| `--color-fondo` | Fondo del marco: inicio de sesión, portada, barra, encabezados; campos de solo lectura | `#f3eee3` neutro cálido | `#27221c` |
| `--color-fondo-trabajo` | Fondo de pantallas de trabajo | `#faf6ef` crema de trabajo | `#27221c` |
| `--color-superficie` | Tarjetas, formularios, filas, campos, fichas de miniatura, "Próximamente" | `#fefcf9` papel | `#322d26` |
| `--color-dimension` | Fondo de la tarjeta de dimensión disponible y del botón principal mientras envía | `#e3d4ad` arena | `#4c3024` café |
| `--color-linea` | Bordes finos decorativos: barra, formulario de acceso, fichas, separadores; barras de la miniatura esquemática | `#c2b290` | `#544e46` |

### Texto y acción

| Token | Rol | Claro | Oscuro |
|---|---|---|---|
| `--color-texto` | Texto principal | `#2c150c` tinta escudo · 14,9:1 sobre fondo, 16,8:1 sobre papel | `#f3ead9` · 13,2:1 sobre fondo, 11,4:1 sobre superficie, 10,0:1 sobre tarjeta |
| `--color-texto-suave` | Etiquetas, ayudas, metadatos, subtítulos | `#7b422d` · 6,8:1 sobre fondo, 5,4:1 sobre arena | `#cbbba1` · 8,4:1 sobre fondo, 7,3:1 sobre superficie, 6,4:1 sobre tarjeta |
| `--color-primario` | Acción y acento: botón principal, enlaces, foco, títulos del marco, franjas de la tarjeta disponible | `#5b2610` café uniforme · 10,5:1 sobre fondo, 8,3:1 sobre arena | `#e3d4ad` arena · 10,7:1 sobre fondo, 8,1:1 sobre tarjeta |
| `--color-sobre-primario` | Texto e íconos sobre `--color-primario` y sobre los círculos de estado | `#fefcf9` · 11,9:1 sobre café | `#27221c` · 10,7:1 sobre arena |
| `--color-sobre-claro` | Texto sobre dorado y sobre tintes, en ambos temas | `#2c150c` · 9,2:1 sobre dorado | `#27221c` · 8,4:1 sobre dorado, ≥ 11,6:1 sobre tintes |
| `--color-arena` | Franjas del uniforme sobre papel y detalles. Nunca borde de campo | `#e3d4ad` | `#e3d4ad` |
| `--color-borde` | Bordes de campos y del círculo vacío; barra de título de la miniatura esquemática | `#9f916a` · 3,05:1 sobre papel | `#8c7f6c` · 3,5:1 sobre superficie |
| `--color-dorado` | Detalles. Nunca texto sobre claro | `#e9b70b` | `#e9b70b` |
| `--color-dorado-texto` | Dorado cuando debe leerse como texto: texto y borde de la insignia "Próximamente" | `#976700` · 4,8:1 sobre papel (4,3:1 sobre fondo: no usar ahí) | `#e9b70b` · 7,3:1 sobre superficie |

### Mensajes y estados

| Token | Rol | Claro | Oscuro |
|---|---|---|---|
| `--color-error` | Mensajes de error. Siempre con ícono y texto | `#c10007` · 6,3:1 sobre papel | `#ea7a6d` · 4,9:1 sobre superficie |
| `--color-exito` | Confirmaciones. Siempre con ícono y texto | `#016630` | `#68ba7e` · 5,8:1 sobre superficie |
| `--color-aviso` | Pendientes, advertencias. Siempre con ícono y texto | `#976700` | `#e9b70b` · 7,3:1 sobre superficie |

El error oscuro es más claro que el círculo "Faltó" (`#e66f61`): ese tono da 4,4:1 sobre la superficie y no alcanza para texto.

### Estados de asistencia

| Estado | Ícono dentro del círculo | Claro (ícono `#fefcf9` encima) | Oscuro (ícono `#27221c` encima) |
|---|---|---|---|
| Sin marcar | ninguno | borde `--color-borde`, relleno `--color-superficie` | igual, con los valores oscuros |
| Asistió `--color-asistio` | check | `#016630` · 7,0:1 | `#68ba7e` · 6,7:1 |
| Faltó `--color-falto` | x | `#c10007` · 6,3:1 | `#e66f61` · 5,1:1 |
| Tarde `--color-tarde` | reloj | `#3275b4` · 4,7:1 | `#67aaec` · 6,4:1 |
| Justificado `--color-justificado` | letra J | `#7b6f66` · 4,8:1 | `#afa298` · 6,3:1 |

### Acentos de las tres dimensiones

Se usan **dentro de la miniatura** de cada tarjeta (fondos de fichas, insignias, detalles), nunca como color de la tarjeta; también tiñen las franjas cortas de la cabecera de cada pantalla de trabajo (ver Cabecera de pantalla de trabajo). Siempre acompañados de ícono y título. Mismo valor en ambos temas; el texto encima es `--color-sobre-claro`.

En la tarjeta "Próximamente" van **apagados**, mezclados con `--color-superficie` (`color-mix(in srgb, <tinte> 40 %, superficie)` en claro, con texto `--color-sobre-claro`; al 20 % en oscuro, con texto `--color-texto`), para que lo no disponible no sea lo más vivo de la pantalla. Texto encima: ≥ 15,0:1 en claro y 6,5:1 en oscuro.

| Dimensión | Acento | Token | Texto encima (claro / oscuro) |
|---|---|---|---|
| Sesiones | `#fdd4c6` terracota claro | `--color-tinte-sesiones` | 12,6:1 / 11,6:1 |
| Notas | `#fbe3a3` dorado suave | `--color-tinte-notas` | 13,6:1 / 12,5:1 |
| Asistencia | `#d0eacf` salvia claro | `--color-tinte-asistencia` | 13,4:1 / 12,3:1 |

## Tokens — Typography

### Títulos — `--font-display`
- **Besley, peso 600, definitiva** (Owen Earl, SIL OFL 1.1), elegida con `/impeccable typeset`. Llega por npm desde `@fontsource/besley`, como HTMX y Alpine: el build copia `besley-latin-600-normal.woff2` (≈19 KB en la 5.3.0) y su licencia a los estáticos, alojados por nosotros, sin CDN, y la versión queda fijada en `package-lock.json`. Rango `latin` de Fontsource (U+0000–00FF, U+2000–206F y otros): cubre tildes, ñ, ü, ¿, ¡, °, comillas, rayas y puntos suspensivos. `font-display: swap`. El prototipo usó un subconjunto propio de ≈17 KB.
- Requisitos que cumple: una sola familia, un solo peso, cálida e institucional (clarendon de letrero escolar), no infantil, no Inter.
- Solo para títulos de 20px o más (portada, inicio de sesión, barra, encabezados de pantalla).

### Texto — `--font-sans`
- **Stack:** `system-ui, -apple-system, "Segoe UI", Roboto, "Noto Sans", sans-serif`
- 0 KB de descarga. Pesos 400 y 600. Line height 1.5.

### Type Scale

| Role | Family | Weight | Size | Line Height | Token |
|------|--------|--------|------|-------------|-------|
| caption | sans | 400 | 14px | 20px | `--text-caption` |
| body | sans | 400 | 16px | 24px | `--text-body` |
| subheading | sans | 600 | 18px | 26px | `--text-subheading` |
| heading | display | 600 | 24px | 30px | `--text-heading` |
| display | display | 600 | 27px móvil / 40px PC | 1.15 | `--text-display` |

El display es para el nombre de la I.E. en el inicio de sesión y para el saludo de la portada: a 27px, "I.E. Virgen del Carmen" y el saludo caben en una línea a 360px. El saludo cambia con la hora ("Buenos días", "Buenas tardes", "Buenas noches") y, mientras el sistema no guarde el tratamiento, lleva solo el nombre ("Buenos días, Ana Quispe"; design de US-001, D8). Un saludo más largo baja a dos líneas (`text-wrap: balance`). Mínimo absoluto 14px. Nunca texto en mayúsculas sostenidas, salvo el nombre completo del estudiante y las marcas "RETIRADO" y "TRASLADADO" (decisión 7 de US-030).

## Tokens — Spacing & Shapes

**Base unit:** 8px · **Tap target mínimo:** 44px · **Altura de botones y campos:** 48px

| Name | Value | Token |
|------|-------|-------|
| 4 | 4px | `--spacing-4` |
| 8 | 8px | `--spacing-8` |
| 16 | 16px | `--spacing-16` |
| 24 | 24px | `--spacing-24` |
| 32 | 32px | `--spacing-32` |
| 48 | 48px | `--spacing-48` |
| 64 | 64px | `--spacing-64` |

### Border Radius

| Elemento | Valor | Token |
|---|---|---|
| Botón principal y secundario, chips | píldora (999px) | `--radius-pill` |
| Campos | 10px | `--radius-campo` |
| Tarjetas, fichas y filas agrupadas | 12px | `--radius-tarjeta` |
| Tarjetas de dimensión y formulario de acceso | 20px | `--radius-dimension` |
| Círculo de asistencia | 50 % | — |

### Elevación

| Uso | Claro | Oscuro | Token |
|---|---|---|---|
| Por defecto | Sin sombra; borde 1px `--color-linea` o separadores | igual | — |
| Ficha de miniatura que desborda | `0 6px 20px rgba(44,21,12,0.12)` | `0 6px 20px rgba(0,0,0,0.4)` | `--shadow-ficha` |

Una sola sombra en todo el sistema, reservada para las fichas que desbordan de una tarjeta disponible.

## Components

### Barra superior
Mismo fondo que la página (`--color-fondo`) con una línea fina de 1px en el borde inferior, `--color-linea` al 55 % mezclado con `--color-fondo` (más tenue, en claro y en oscuro); alto 56px; fija arriba. A la izquierda "I.E. Virgen del Carmen" en `--font-display` 600, `--color-primario`, 20px en celular y 22px en PC. Sin menú en US-001: un menú sin función es un control muerto. Entra con US-002 (cerrar sesión), a la derecha, de 44 × 44px; a 360px quedan 51px de aire entre el nombre y el menú. El nombre del sistema no va en la barra: va en el pie.

### Inicio de sesión
- Una columna centrada en horizontal sobre `--color-fondo`, sin las tarjetas de dimensión. Ancho máximo 440px en celular y 560px en PC (el nombre a 40px mide 482px); el formulario, máximo 440px.
- Jerarquía, de arriba abajo: espacio reservado para el escudo (56px en celular, 80px en PC; vacío e invisible, solo el aire, hasta tener la autorización de la I.E.); "I.E. Virgen del Carmen" en display, `--color-primario`; "Huayucachi" debajo (18px celular, 20px PC, `--color-texto`); "Sesiones · Notas · Asistencia" en 14px `--color-texto-suave`. "CarpetaDocente" no va arriba.
- Formulario en tarjeta `--color-superficie`, borde 1px `--color-linea`, radio 20px, padding 24px (32px en PC): Usuario, Contraseña (con el botón "Mostrar contraseña"), botón "Ingresar" a ancho completo y la ayuda "Si olvidaste tu contraseña, pide al administrador que la restablezca."
- Error: el mensaje va sobre la tarjeta del formulario, no dentro, en dos líneas: qué pasó ("Usuario o contraseña incorrectos, o cuenta inactiva") y qué hacer ("Revisa tus datos. Si el problema sigue, pide ayuda al administrador."). Es el mismo mensaje para la cuenta bloqueada (US-001).
- Enviando: el botón dice "Ingresando…" con el fondo de envío (ver Botón principal) y los dos campos quedan de solo lectura, sobre `--color-fondo`.
- Sin Alpine: el inicio de sesión solo carga el JavaScript propio del botón "Mostrar contraseña" y del estado de envío.
- **Celular:** el contenido empieza en el tercio superior de la pantalla, no centrado en vertical; el botón "Ingresar" queda dentro de la primera pantalla (360 × 800).
- **PC:** columna centrada en horizontal y en vertical.
- Pie al final de la página.

### Pie
"CarpetaDocente · 2026" en 14px `--color-texto-suave`, centrado, al final del inicio de sesión y de la portada. Sin ©. En la PC entra en la primera pantalla.

### Botón principal (píldora)
Fondo `--color-primario` (café en claro, arena en oscuro), texto `--color-sobre-primario` 16px/600, alto 48px, radio 999px. Ancho completo en el celular y en el formulario de acceso; ancho de contenido en el resto de la PC. Un solo botón principal por pantalla. Presionado: un tono más intenso y escala 0,98. Foco: anillo de 2px `--color-primario` con 2px de separación. Mientras envía (`aria-disabled`, no `disabled`, porque un botón deshabilitado no envía el formulario): fondo `--color-dimension` (arena en claro, café en oscuro) y texto `--color-texto`, para que el cambio no dependa solo del texto.

### Botón secundario
Píldora transparente, borde 1px `--color-primario`, texto `--color-primario` 16px/600, alto 48px.

### Campo de texto
Etiqueta encima (14px/600 `--color-texto`), campo de 48px, fondo `--color-superficie`, borde 1px `--color-borde`, radio 10px, texto 16px. Error: borde `--color-error` y mensaje debajo con ícono. Nunca etiquetas flotantes.

### Campo de contraseña
Como el campo de texto, con el botón "Mostrar contraseña" dentro, a la derecha: 44 × 44px, ícono Lucide `eye` (contraseña oculta) o `eye-off` (visible), 20px, `--color-texto-suave`. Etiqueta accesible fija "Mostrar contraseña" y estado en `aria-pressed`. JavaScript propio mínimo, sin Alpine; sin JavaScript el botón no aparece (atributo `hidden`) y el campo funciona como siempre. Al enviar el formulario, la contraseña vuelve a ocultarse. Foco: anillo de 2px `--color-primario` dentro del botón.

### Mensaje (error, éxito, aviso)
Caja con fondo `--color-superficie`, borde completo de 1px en el color del estado, radio 12px e ícono a la izquierda en el color del estado. Texto en dos pesos: la primera línea (qué pasó) en 600 y en el color del estado; la segunda (qué hacer), en 400 y `--color-texto`. Nunca solo color.

### Tarjeta de dimensión G4e (firma visual del sistema)
- **Disponible:** fondo `--color-dimension` (arena en claro, café `#4c3024` en oscuro), sin borde, radio 20px, padding 24px (32px en PC). Título corto en `--font-display` 24px ("Asistencia"), ícono de línea 24px y franjas, todo en `--color-primario` (café en claro, arena en oscuro); subtítulo formal 14px `--color-texto-suave` ("Control de asistencia"). Al pie de la cabecera, un renglón dice qué hace la tarjeta: verbo 14px/600 en `--color-primario` y la flecha `arrow-right` de Lucide, 20px. Verbos: "Registrar asistencia", "Registrar notas" y "Ver sesiones" (Sesiones es un repositorio, RF-010 a RF-018). El verbo describe el enlace (`aria-describedby`).
- **Cabecera:** ícono y título en una fila; debajo, el subtítulo y el renglón de acción, alineados con el título. En "Próximamente", la insignia va siempre en su propia línea, sobre el título y arriba a la derecha, a cualquier ancho y en todas las tarjetas (en el HTML va después del título). El renglón de acción va al pie de la cabecera: en PC, cuando la cabecera es más alta que su contenido, el aire de más queda entre el subtítulo y el verbo, no entre el verbo y la ficha.
- **Franjas del uniforme:** dos líneas horizontales de 3px y 2px con 6px de separación, de borde a borde, en el tercio inferior. Sobrias, rectas, sin brillo.
- **Miniatura que desborda:** una ficha `--color-superficie` (radio 12px, `--shadow-ficha`) con una vista previa **esquemática** y estática de la dimensión, construida en HTML/CSS: barras en lugar de nombres y títulos, sin ningún dato que pueda leerse como un registro de la docente. Arranca dentro de la tarjeta, cruza las franjas y sobresale 28–32px por el borde inferior. En oscuro lleva borde 1px `--color-linea`.
  - Barras: 10px de alto, radio píldora, `--color-linea`, de largos distintos (40–70 % del ancho) para que se lean como renglones; la barra de título, 12px y `--color-borde`.
  - Asistencia: rótulo "Asistencia" en acento salvia (sin día) y cinco filas de barra con círculos de estado sin alumno: dos de ejemplo (✓ ✕) y tres sin marcar (borde de 2px `--color-borde`, relleno `--color-superficie`). No debe leerse como la asistencia de hoy ya tomada.
  - Notas: rótulo "Matemática" y cinco filas de barra con insignias sin estudiante (AD · A · B · A · C) en acento dorado suave.
  - Sesiones: dos sesiones de barra de título y barra de detalle, con los archivos "Word" y "PDF" en acento terracota.
  - Datos reales de la docente: solo cuando exista la historia que los provea; se evalúa en esa historia.
- **Toda la tarjeta disponible es pulsable:** un solo enlace que ocupa la tarjeta entera y también lo que sobresale de la miniatura. Foco: anillo de 2px `--color-primario` con 2px de separación solo alrededor de la tarjeta; lo que sobresale de la miniatura queda encima del anillo, como encima del borde.
- **"Próximamente":** fondo `--color-superficie` (papel en claro, `#322d26` en oscuro), borde de 1px (`--color-borde` en claro, `--color-linea` en oscuro), insignia "Próximamente" callada en su propia línea, arriba a la derecha, y menos énfasis: título en `--color-texto`, ícono y subtítulo en `--color-texto-suave`, franjas en `--color-arena` (claro) o `--color-linea` (oscuro), miniatura sin sombra, con borde 1px `--color-linea` y tintes apagados (ver Acentos). Nunca se oculta.
  - Insignia callada: fondo transparente, borde 1px y texto 14px/600 en `--color-dorado-texto` (`#976700` en claro, 4,8:1 sobre papel; `#e9b70b` en oscuro, 7,3:1), radio píldora.
  - No navega, pero responde: toda la tarjeta es un botón con `aria-disabled="true"` (se estira como el enlace de la disponible, también sobre lo que sobresale, y lo describe la insignia). Al tocarlo aparece "Llegará en una próxima versión." en el renglón al pie de la cabecera (el del verbo en la disponible), 14px `--color-texto-suave`, durante 3 s, en una región `aria-live="polite"` que ya está en la página y ya ocupa el alto de dos líneas: no mueve la miniatura, y el texto se apoya abajo, a 24px de ella (32px en PC). Sin JavaScript no hace nada.
- **Al cerrar US-001:** las tres en "Próximamente". **Con US-030 (Sprint 1):** solo Asistencia disponible; Sesiones y Notas en "Próximamente". **Estado final:** las tres disponibles.
- **Celular:** carrusel de dimensiones (abajo). **PC:** las tres tarjetas en fila, centradas, ocupando el ancho útil (máx. 1120px), bajo el saludo; las tres fichas empiezan a la misma altura aunque solo las "Próximamente" lleven la línea de la insignia (las tarjetas comparten las filas de la grilla con `subgrid`).

### Carrusel de dimensiones (celular)
**Única excepción** a la regla de no desplazamiento horizontal (RNF-005, documento 07): solo en la portada del docente, en el celular.
- Fila de tres chips (Sesiones, Notas, Asistencia) bajo el saludo, de 44px de alto como mínimo; tocar un chip lleva a su tarjeta. El chip de la tarjeta visible va sin el relleno de acción, para no parecerse al botón principal: fondo `--color-superficie`, borde de 2px y texto en `--color-primario`.
- Con JavaScript, el chip desplaza el carrusel sin cambiar la dirección de la página: no agrega entradas al historial y "Atrás" sale de la portada. Sin JavaScript, el chip es un enlace a la tarjeta.
- Para el lector de pantalla, la fila de chips se llama "Accesos" y el carrusel "Tus accesos" (no "dimensiones", que es vocabulario de la tesis).
- Tarjetas casi a ancho completo, con ajuste por tarjeta (`scroll-snap`); la siguiente asoma 24px para que se note que hay más. La tarjeta que asoma no responde al toque ni anuncia nada (con JavaScript); el teclado y el lector de pantalla llegan a todas.
- Puntos de paginación visibles debajo; el de la tarjeta visible, alargado y en `--color-primario`.
- Solo CSS donde el navegador lo permite (líneas de tiempo de desplazamiento). Donde no, el chip y el punto activos se marcan con Alpine.js, sin ocultar los puntos.
- Abre en la primera tarjeta disponible, en el orden de las tarjetas, o en la primera si no hay ninguna: al cerrar US-001, en Sesiones; con US-030, en Asistencia; en el estado final, en Sesiones.
- Desde 960px no hay carrusel: las tres tarjetas en fila.

### Fila de asistencia (celular)
Una fila por estudiante sobre `--color-superficie`: nombre completo en mayúsculas (decisión 7 de US-030), 16px, a la izquierda y círculo de estado a la derecha (36px visibles, área táctil 44px). Tocar el círculo cicla: Sin marcar → Asistió → Faltó → Tarde → Justificado → Asistió (una vez guardado ya no vuelve a "Sin marcar"). Sin menús ni ventanas emergentes. Cada toque se guarda solo; si queda sin conexión, la fila lo indica y reintenta.

### Cabecera de pantalla de trabajo
Ícono de su dimensión (el de su tarjeta, 24px, `--color-primario`) junto al título y, debajo, las franjas cortas del uniforme (48px; 3px y 2px, separadas 6px) en el tinte de la dimensión (`--color-tinte-sesiones`, `--color-tinte-notas` o `--color-tinte-asistencia`, iguales en claro y en oscuro). Sin banda ni fondo; 24px de aire bajo la barra en celular y 32px en PC. La portada, la lista de estudiantes, la cuenta y el ingreso no llevan franjas.

### Selector de día (celular)
Fila de 5 chips (Lun a Vie) de ancho fijo sobre la lista. Estados del chip: registrado (check), hoy (punto `--color-primario` relleno), sin clase (guion `--color-texto-suave`), futuro (atenuado). Por defecto, hoy. En el celular siempre se ve un solo día a la vez.

### Asistencia en PC
Lista de hoy a la izquierda y panel de la jornada a la derecha, sin fondo: fecha, selector de semana, avance, totales, "Marcar todos", leyenda y guardado (decisión 9 de US-030, variante 10a). Los mismos círculos que en el celular. Ya no se muestra la semana completa en columnas. Nunca desplazamiento horizontal.

### Resumen de jornada
Fijo arriba de la lista: "18 de 25 marcados" mientras falten; al completar "Asistió: 21 · Tarde: 1 · Faltó: 2 · Justificado: 1". Indicador "Guardado" con check a la derecha.

### Nota de justificación
Al marcar Justificado, aparece debajo de la fila un campo opcional de una línea (máximo 100 caracteres), ejemplo: "Ej.: constancia entregada a la docente".

### Estado vacío
Ícono de línea y una frase que explica qué falta y qué pasará: "Tu sección aparecerá cuando el administrador la asigne."

## Iconografía

**Lucide 1.52.0** (licencia ISC), elegida en `/impeccable shape`. Trazo de 1,75 px en todo el sistema, 24px por defecto, `stroke="currentColor"`. Incrustada como SVG: solo se incluyen los íconos usados; sin fuentes de íconos ni paquetes. El aviso de la licencia ISC acompaña los íconos en el repositorio. Los archivos Word y PDF usan el mismo ícono de archivo (`file-text`) con la etiqueta de texto "Word" o "PDF" al lado. Nunca un ícono dentro de un cuadrado redondeado de color sobre un título.

## Movimiento

Solo funcional: pulso breve del círculo de asistencia al cambiar de estado (≤150ms), respuesta del botón al toque, aparición de mensajes (≤200ms), desplazamiento suave del carrusel al tocar un chip. Dos momentos de autor, uno por pantalla: en la portada, "Hoy: pendiente" aparece una vez; en la asistencia, las franjas del cierre se trazan una vez (ver Cambios 0.4). Animar solo `transform` y `opacity`. Con "reducir movimiento" activado, sin animación (el chip y el punto activos del carrusel siguen la posición: no son movimiento). Nada decorativo ni en bucle.

## Do's and Don'ts

### Do
- Usar `--color-primario` (café en claro, arena en oscuro) como único color de acción
- Poner la identidad en el marco y el contenido sobre `--color-superficie` / `--color-fondo-trabajo`
- Acompañar todo estado con ícono y texto
- Diseñar a 360px primero; en PC, centrar con ancho máximo de 1120px
- Verificar cada pantalla en tema claro y en tema oscuro
- Usar datos ficticios en español del Perú ("Prof. Ana Quispe", "3.° grado, sección A"); el tratamiento y el grado se muestran cuando el sistema guarde esos datos (design de US-001, D8; US-005)

### Don't
- **Nunca desplazamiento horizontal**, en ninguna página ni componente, salvo el carrusel de dimensiones de la portada en el celular. Las tablas de dos dimensiones se transforman: se elige una dimensión y la otra se muestra como lista
- No escribir colores hex en el HTML: solo clases de los tokens
- En oscuro, no usar el café como texto ni como botón
- No usar el dorado `--color-dorado` como texto sobre fondos claros (1,7:1)
- No usar el arena `--color-arena` como borde de campos (1,4:1)
- No usar fotografías, ilustraciones, degradados, brillos ni animaciones decorativas
- No incluir logo ni escudo de la institución (pendiente de autorización); usar el nombre en texto
- No usar azul, violeta o rojo como color de marca; el azul de Tarde existe solo para ese estado
- No usar negro puro ni grises fríos, tampoco en oscuro
- No usar gestos ocultos (mantener presionado, deslizar) para acciones necesarias: el carrusel siempre tiene chips tocables
- No poner tarjeta dentro de tarjeta dentro de marco
- No repetir el nombre del sistema en la barra y en el cuerpo de la misma pantalla
- No inventar textos, funciones ni datos institucionales

## Descartes y pendientes

| Elemento | Estado | Nota |
|---|---|---|
| Isotipo provisional | Descartado | El nombre de la I.E. va en texto |
| Ilustración SVG de objetos (carpeta, libreta, lista) en el inicio de sesión | Descartada | — |
| Barra café con franja dorada | Descartada | La barra usa el fondo de la página y una línea fina |
| Eslogan grande en el inicio de sesión | Descartado | — |
| Bloque de créditos oscuro al pie | Descartado | Lo reemplaza el pie "CarpetaDocente · 2026" |
| Escudo de la I.E. | Pendiente de autorización de la I.E. | Su espacio ya está reservado, vacío, sobre el nombre en el inicio de sesión |
| Boceto de líneas del edificio de la I.E. | Pendiente de autorización de la I.E. | Hasta entonces no se dibuja |
| Selector de tema claro/oscuro | Pendiente: RF aparte, después del Sprint 1 | Mientras tanto, el tema sigue la preferencia del sistema |
| Menú de la barra superior | Pendiente: entra con US-002 | En US-001 no hay menú |
| Tarjeta sin miniatura o con la miniatura que asoma recortada por el borde inferior | Descartadas (tramo 5): queda la miniatura que desborda | Con ella, `impeccable detect` marca `nested-cards` en la portada; se acepta con una excepción del detector solo para la portada (configuración local del detector). Capturas de la comparación: evidencia local |
| Miniatura con datos reales de la docente | Pendiente: se evalúa en la historia que los provea | Hasta entonces, esquemática |
| Aviso de privacidad (Ley 29733) | Pendiente de evaluar en `docs/` | Sin enlace hasta que exista el documento |
| Alternativa documentada | Respaldo | Fondo arena −2 `#ece2c8` con la tarjeta disponible en café suave `#6d402c` (G4c), por si G4e no funciona en la prueba con docentes |

## Surfaces

| Level | Name | Claro | Oscuro | Purpose |
|-------|------|-------|---------|---------|
| 0 | Marco | `#f3eee3` | `#27221c` | Inicio de sesión, portada, barra, encabezados |
| 0 | Trabajo | `#faf6ef` | `#27221c` | Fondo de pantallas de trabajo |
| 1 | Superficie | `#fefcf9` | `#322d26` | Tarjetas, filas, formularios, fichas de miniatura, "Próximamente" |
| 1 | Dimensión | `#e3d4ad` | `#4c3024` | Tarjeta de dimensión disponible |

## Layout

Celular primero (360px), margen lateral 16px, una sola columna, barra superior fija. Un título por pantalla y una acción principal. En PC: contenido centrado con ancho máximo de 1120px; la portada usa el saludo y tres tarjetas en fila; la asistencia muestra la lista de hoy y el panel de la jornada. En el celular, la portada muestra las dimensiones en el carrusel.

## Pantallas del prototipo

Prototipo de US-001 (variante G4e), en tema claro y oscuro:

1. Inicio de sesión — celular y PC. Espacio del escudo, "I.E. Virgen del Carmen", "Huayucachi", "Sesiones · Notas · Asistencia", formulario y pie. Estados: normal con foco, contraseña visible, error ("Usuario o contraseña incorrectos, o cuenta inactiva" / "Revisa tus datos. Si el problema sigue, pide ayuda al administrador.", con el usuario conservado), enviando y campos vacíos.
2. Portada del docente — celular (carrusel) y PC (tres en fila). El saludo según la hora ("Buenos días, Ana Quispe"), la fecha con la sección y las tres tarjetas, con solo Asistencia disponible (estado con US-030, con "Llegará en una próxima versión." al tocar una "Próximamente") y en el estado final (las tres disponibles). Al cerrar US-001, las tres en "Próximamente" y el saludo sin tratamiento.
3. Inicio de la dirección — PC. Mismo marco y, en el Sprint 1, un estado vacío fijo: "Los consolidados de notas y asistencia estarán aquí en una próxima versión." El panel de consolidados es US-040.
4. Asistencia de hoy — celular (un día con selector) y PC (lista de hoy y panel de la jornada). 3.° grado, sección A, 25 estudiantes ficticios. Se prototipa con su historia.

## Listo para la prueba con docentes

Todo se verifica **en tema claro y en tema oscuro**:

- `npx impeccable detect` sin hallazgos principales
- Evaluación con las 10 heurísticas de Nielsen sin problemas de gravedad 3 o 4
- Contraste AA verificado en todas las combinaciones usadas: texto ≥ 4,5:1 (≥ 3:1 en títulos grandes) y bordes de campos, íconos de estado y foco ≥ 3:1
- Revisión de carga cognitiva del flujo de asistencia
- Sin desplazamiento horizontal a 360px, salvo el carrusel de dimensiones
- Áreas táctiles de 44px como mínimo, chips del carrusel incluidos
- Carrusel probado en Chrome de Android, Safari de iPhone y Firefox

## Quick Start

### Tailwind v4

`@theme` define el tema claro y crea las clases. Tailwind no admite `@theme` dentro de una media query, así que el tema oscuro redefine las mismas variables en `:root`; las clases no cambian.

```css
@theme {
  --color-fondo: #f3eee3;
  --color-fondo-trabajo: #faf6ef;
  --color-superficie: #fefcf9;
  --color-dimension: #e3d4ad;
  --color-linea: #c2b290;
  --color-texto: #2c150c;
  --color-texto-suave: #7b422d;
  --color-primario: #5b2610;
  --color-sobre-primario: #fefcf9;
  --color-sobre-claro: #2c150c;
  --color-arena: #e3d4ad;
  --color-borde: #9f916a;
  --color-dorado: #e9b70b;
  --color-dorado-texto: #976700;
  --color-error: #c10007;
  --color-exito: #016630;
  --color-aviso: #976700;
  --color-asistio: #016630;
  --color-falto: #c10007;
  --color-tarde: #3275b4;
  --color-justificado: #7b6f66;
  --color-tinte-sesiones: #fdd4c6;
  --color-tinte-notas: #fbe3a3;
  --color-tinte-asistencia: #d0eacf;

  --font-sans: system-ui, -apple-system, "Segoe UI", Roboto, "Noto Sans", sans-serif;
  --font-display: "Besley", Georgia, serif;

  --text-caption: 14px;
  --text-body: 16px;
  --text-subheading: 18px;
  --text-heading: 24px;
  --text-display: 27px;

  --radius-pill: 999px;
  --radius-campo: 10px;
  --radius-tarjeta: 12px;
  --radius-dimension: 20px;

  --shadow-ficha: 0 6px 20px rgba(44, 21, 12, 0.12);
}

@media (prefers-color-scheme: dark) {
  :root {
    color-scheme: dark;
    --color-fondo: #27221c;
    --color-fondo-trabajo: #27221c;
    --color-superficie: #322d26;
    --color-dimension: #4c3024;
    --color-linea: #544e46;
    --color-texto: #f3ead9;
    --color-texto-suave: #cbbba1;
    --color-primario: #e3d4ad;
    --color-sobre-primario: #27221c;
    --color-sobre-claro: #27221c;
    --color-borde: #8c7f6c;
    --color-dorado-texto: #e9b70b;
    --color-error: #ea7a6d;
    --color-exito: #68ba7e;
    --color-aviso: #e9b70b;
    --color-asistio: #68ba7e;
    --color-falto: #e66f61;
    --color-tarde: #67aaec;
    --color-justificado: #afa298;

    --shadow-ficha: 0 6px 20px rgba(0, 0, 0, 0.4);
  }
}

@media (min-width: 960px) {
  :root {
    --text-display: 40px;
  }
}
```

Sin cambio en oscuro: `--color-arena`, `--color-dorado` y los tres tintes.
