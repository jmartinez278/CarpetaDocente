# CarpetaDocente — Design System

> Un aula cálida y ordenada: el café del uniforme, con sus franjas arena, y el dorado del escudo enmarcan la pantalla; el trabajo diario ocurre sobre papel casi blanco, tranquilo y legible.

**Theme:** light (sin modo oscuro por ahora; los tokens permiten agregarlo después)
**Estado:** propuesta 0.2 · 19-10-2026 · insumo para Impeccable (ruta B) y para el prototipo en `insumos/prototipo/`. Los colores salen de fotos y afiches de la I.E. (aproximados) y pasaron filtros WCAG 2.x, APCA y simulación de daltonismo. Este archivo es la referencia visual del proyecto (CLAUDE.md, sección Interfaz); la ratifica la aprobación, por otra integrante, del PR que lo incorpora (cierra C7).
**Cambios 0.2:** tarjetas café con franjas del uniforme y miniatura que desborda; botón principal en píldora; fuente de títulos por definir con `/impeccable typeset`; tuteo; títulos cortos con subtítulo formal; una sola librería de íconos; movimiento solo funcional; asistencia de 5 columnas en computadora; criterio de "listo para docentes".

CarpetaDocente (nombre provisional) es una aplicación web para docentes de primaria de la I.E. Virgen del Carmen (Huayucachi, Junín, Perú). Se usa sobre todo desde el celular, con datos móviles (referencia: 4G lento), dentro del aula o en el patio con sol; la dirección la usa en computadora. Debe sentirse institucional, cálida y confiable: ni plantilla genérica de SaaS ni sistema estatal antiguo.

**Regla de color "identidad en el marco, comodidad en el contenido":** café, arena y dorado viven en el marco (barra superior, inicio de sesión, portada, encabezados). Las zonas de trabajo (listas, formularios, asistencia, notas) van sobre superficies neutras casi blancas. Proporción 60 % neutro cálido · 30 % café y arena · 10 % dorado.

**Referencia de tono:** la página de base de conocimiento de Slite (lienzo cálido, mucho aire, el producto como ilustración, fichas que desbordan su contenedor). Solo para portada e inicio de sesión: las pantallas de trabajo son más calladas.

## Usuarios y principios

| Grupo | Necesita | Decisión de diseño |
|---|---|---|
| Escépticos | Que se vea oficial y serio | Sobrio, bordes finos, sin animaciones llamativas, nombre de la I.E. visible |
| Desinteresados | No aprender nada | Una sola acción principal por pantalla; tareas en 1–2 toques |
| Docentes promedio | Patrones conocidos | Formularios y listas como en apps de banca o mensajería; nada de gestos ocultos |
| Recién llegados | Saber qué hacer | Estados vacíos que explican el siguiente paso |
| Jóvenes | Rapidez y aspecto moderno | Pantallas livianas, píldoras, esquinas redondeadas |
| Dirección | Visión de conjunto | En computadora: más densidad y tablas; el mismo marco café |

## Voz y textos

- **Tuteo** en toda la interfaz: "Ingresa tu contraseña", "Tu sección aparecerá…".
- Frases cortas, verbo primero en botones ("Ingresar", "Marcar todos como Asistió").
- Errores: qué pasó y qué hacer, sin culpar. Sin signos de exclamación en mensajes del sistema.
- Nunca inventar funciones, servicios ni datos institucionales (ej.: no "¿Olvidaste tu clave?" con enlace propio, porque la clave la restablece el administrador; no textos sobre servidores o soporte que no existen).

## Tokens — Colors

| Name | Value | Token | Role |
|------|-------|-------|------|
| Café uniforme | `#5b2610` | `--color-primario` | Barra superior, tarjetas de dimensión, botón principal, enlaces, foco. Texto blanco encima: 12,1:1 |
| Tinta escudo | `#2c150c` | `--color-texto` | Texto principal y títulos. 15,7:1 sobre fondo |
| Café suave | `#7b422d` | `--color-texto-suave` | Etiquetas, ayudas, metadatos. 7,6:1 |
| Crema afiche | `#fcf4e1` | `--color-fondo` | Fondo del marco: inicio de sesión, portada, encabezados. También texto sobre café (10,4:1) |
| Crema de trabajo | `#faf6ef` | `--color-fondo-trabajo` | Fondo de pantallas de trabajo |
| Papel | `#fefcf9` | `--color-superficie` | Tarjetas, formularios, filas, campos, fichas de miniatura |
| Arena uniforme | `#e3d4ad` | `--color-arena` | Franjas del uniforme y separadores decorativos. Nunca borde de campo |
| Borde de campo | `#9f916a` | `--color-borde` | Bordes de campos y del círculo vacío. 3,05:1 sobre papel |
| Dorado escudo | `#e9b70b` | `--color-dorado` | Solo sobre café (franja bajo la barra, detalles) o como fondo de insignia con texto `#2c150c` |
| Dorado legible | `#976700` | `--color-dorado-texto` | Dorado cuando debe leerse sobre fondo claro. 4,5:1 |
| Error | `#c10007` | `--color-error` | Mensajes de error. Siempre con ícono y texto |
| Éxito | `#016630` | `--color-exito` | Confirmaciones. Siempre con ícono y texto |
| Aviso | `#976700` | `--color-aviso` | Pendientes, advertencias. Siempre con ícono y texto |

### Estados de asistencia

| Estado | Color | Ícono dentro del círculo | Blanco encima |
|---|---|---|---|
| Sin marcar | borde `#9f916a`, relleno `#fefcf9` | ninguno | — |
| Asistió | `#016630` | check | 7,1:1 |
| Faltó | `#c10007` | x | 6,4:1 |
| Tarde | `#3275b4` | reloj | 4,8:1 |
| Justificado | `#7b6f66` | letra J | 4,9:1 |

### Acentos de las tres dimensiones

Se usan **dentro de la miniatura** de cada tarjeta café (fondos de fichas, insignias, detalles), nunca como color de la tarjeta. Siempre acompañados de ícono y título.

| Dimensión | Acento | Token | Texto `#2c150c` encima |
|---|---|---|---|
| Sesiones | `#fdd4c6` terracota claro | `--color-tinte-sesiones` | 12,6:1 |
| Notas | `#fbe3a3` dorado suave | `--color-tinte-notas` | 13,6:1 |
| Asistencia | `#d0eacf` salvia claro | `--color-tinte-asistencia` | 13,4:1 |

## Tokens — Typography

### Títulos — `--font-display`
- **Por definir con `/impeccable typeset`.** Requisitos: una sola familia, **un solo peso**, alojada por nosotros (no Google Fonts por CDN), subconjunto latino con tildes y ñ, `font-display: swap`. No usar Inter ni fuentes genéricas. Debe verse cálida e institucional, no infantil.
- Solo para títulos de 22px o más (portada, inicio de sesión, encabezados de pantalla).

### Texto — `--font-sans`
- **Stack:** `system-ui, -apple-system, "Segoe UI", Roboto, "Noto Sans", sans-serif`
- 0 KB de descarga. Pesos 400 y 600. Line height 1.5.

### Type Scale

| Role | Family | Weight | Size | Line Height | Token |
|------|--------|--------|------|-------------|-------|
| caption | sans | 400 | 14px | 20px | `--text-caption` |
| body | sans | 400 | 16px | 24px | `--text-body` |
| subheading | sans | 600 | 18px | 26px | `--text-subheading` |
| heading | display | — | 24px | 30px | `--text-heading` |
| display | display | — | 32px móvil / 44px PC | 1.15 | `--text-display` |

Mínimo absoluto 14px. Nunca texto en mayúsculas sostenidas.

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

### Border Radius (valores iniciales; Impeccable puede ajustarlos)

| Elemento | Valor | Token |
|---|---|---|
| Botón principal y secundario | píldora (999px) | `--radius-pill` |
| Campos | 10px | `--radius-campo` |
| Tarjetas, fichas y filas agrupadas | 12px | `--radius-tarjeta` |
| Tarjetas de dimensión | 20px | `--radius-dimension` |
| Círculo de asistencia | 50 % | — |

### Elevación

| Uso | Valor | Token |
|---|---|---|
| Por defecto | Sin sombra; borde 1px `#e3d4ad` o separadores | — |
| Ficha de miniatura que desborda | `0 6px 20px rgba(44,21,12,0.12)` | `--shadow-ficha` |

Una sola sombra en todo el sistema, reservada para las fichas que desbordan.

## Components

### Barra superior
Fondo `#5b2610`, alto 56px, "CarpetaDocente" en crema `#fcf4e1` a la izquierda, menú a la derecha. Franja dorada `#e9b70b` de 3px en el borde inferior.

### Botón principal (píldora)
Fondo `#5b2610`, texto blanco 16px/600, alto 48px, radio 999px. Ancho completo en el celular, ancho de contenido en PC. Un solo botón principal por pantalla. Presionado: un tono más oscuro y escala 0,98. Foco: anillo de 2px `#5b2610` con 2px de separación.

### Botón secundario
Píldora transparente, borde 1px `#5b2610`, texto `#5b2610` 16px/600, alto 48px.

### Campo de texto
Etiqueta encima (14px/600 `#2c150c`), campo de 48px, fondo `#fefcf9`, borde 1px `#9f916a`, radio 10px, texto 16px. Error: borde `#c10007` y mensaje debajo con ícono. Nunca etiquetas flotantes.

### Mensaje (error, éxito, aviso)
Caja con fondo `#fefcf9`, borde completo de 1px en el color del estado, radio 12px, ícono a la izquierda y texto en el color del estado. Nunca solo color.

### Tarjeta de dimensión (firma visual del sistema)
- **Bloque café** `#5b2610`, radio 20px, padding 24px. Título corto en `--font-display` 24px color crema `#fcf4e1` ("Asistencia"), subtítulo formal 14px crema con 80 % de presencia visual mediante color `#e3d4ad` ("Control de asistencia"), ícono de línea 24px crema.
- **Franjas del uniforme:** dos líneas horizontales color arena `#e3d4ad`, de 3px y 2px con 6px de separación, cruzan el bloque café en su tercio inferior, de borde a borde. Sobrias, rectas, sin brillo.
- **Miniatura que desborda:** una ficha `#fefcf9` (radio 12px, `--shadow-ficha`) con una vista previa real y estática de la dimensión, construida en HTML/CSS con datos ficticios. Arranca dentro del bloque café, cruza las franjas y sobresale 24–32px por el borde inferior hacia el fondo crema.
  - Asistencia: tres filas "Quispe, A. / Huamán, L. / Rojas, M." con círculos ✓ ✕ reloj, acento salvia.
  - Notas: nombres ficticios con insignias AD · A · B en acento dorado suave.
  - Sesiones: dos fichas de archivo ("Resolvemos problemas de suma · 3.° · Matemática", Word y PDF) con acento terracota.
- Toda la tarjeta es pulsable. Una dimensión no disponible lleva insignia "Próximamente" (fondo `#e9b70b`, texto `#2c150c`) y menos énfasis, nunca oculta.
- **Celular:** tarjetas apiladas a ancho completo, grandes, con 48px entre ellas para que la ficha que desborda no choque con la siguiente.
- **PC:** las tres tarjetas en fila, centradas, ocupando el ancho útil (máx. 1120px), con título editorial encima.

### Fila de asistencia (celular)
Una fila por estudiante sobre `#fefcf9`: "Apellido, inicial." 16px a la izquierda y círculo de estado a la derecha (36px visibles, área táctil 44px). Tocar el círculo cicla: Sin marcar → Asistió → Faltó → Tarde → Justificado → Asistió (una vez guardado ya no vuelve a "Sin marcar"). Sin menús ni ventanas emergentes. Cada toque se guarda solo; si queda sin conexión, la fila lo indica y reintenta.

### Selector de día (celular)
Fila de 5 chips (Lun a Vie) de ancho fijo sobre la lista. Estados del chip: registrado (check), hoy (punto café relleno), sin clase (guion gris), futuro (atenuado). Por defecto, hoy. En el celular siempre se ve un solo día a la vez.

### Asistencia en PC
La semana completa: columna de nombres y **5 columnas de días** (Lun a Vie) con los mismos círculos, y una columna final de totales. El día de hoy resaltado con encabezado café. Un día sin clase se muestra como columna atenuada "Sin clase" y no afecta los totales. Nunca desplazamiento horizontal: si el ancho no alcanza, se vuelve al modo de un día con selector.

### Resumen de jornada
Fijo arriba de la lista: "18 de 25 marcados" mientras falten; al completar "Asistió: 21 · Tarde: 1 · Faltó: 2 · Justificado: 1". Indicador "Guardado" con check a la derecha.

### Nota de justificación
Al marcar Justificado, aparece debajo de la fila un campo opcional de una línea (máximo 100 caracteres), ejemplo: "Ej.: constancia entregada a la docente".

### Estado vacío
Ícono de línea y una frase que explica qué falta y qué pasará: "Tu sección aparecerá cuando el administrador la asigne."

## Iconografía

Una sola librería de íconos de línea (trazo 1,5–2px), elegida en `/impeccable shape`, incrustada como SVG: solo se incluyen los íconos usados; sin fuentes de íconos. Nunca un ícono dentro de un cuadrado redondeado de color sobre un título.

## Movimiento

Solo funcional: pulso breve del círculo de asistencia al cambiar de estado (≤150ms), respuesta del botón al toque, aparición de mensajes (≤200ms). Animar solo `transform` y `opacity`. Con "reducir movimiento" activado, sin animación. Nada decorativo ni en bucle.

## Do's and Don'ts

### Do
- Usar el café `#5b2610` como único color saturado de acción
- Poner la identidad en el marco y el contenido sobre `#fefcf9` / `#faf6ef`
- Acompañar todo estado con ícono y texto
- Diseñar a 360px primero; en PC, centrar con ancho máximo de 1120px
- Usar datos ficticios en español del Perú ("Prof. Ana Quispe", "3.° grado, sección A")

### Don't
- **Nunca desplazamiento horizontal**, en ninguna página ni componente. Las tablas de dos dimensiones se transforman: se elige una dimensión y la otra se muestra como lista
- No usar el dorado `#e9b70b` como texto sobre fondos claros (1,7:1)
- No usar el arena `#e3d4ad` como borde de campos (1,4:1)
- No usar fotografías, degradados, brillos ni animaciones decorativas
- No incluir logo ni escudo de la institución (pendiente de autorización); usar el nombre en texto
- No usar azul, violeta o rojo como color de marca; el azul `#3275b4` existe solo para el estado Tarde
- No usar negro puro ni grises fríos
- No usar gestos ocultos (mantener presionado, deslizar) para acciones necesarias
- No poner tarjeta dentro de tarjeta dentro de marco
- No repetir el nombre del sistema en la barra y en el cuerpo de la misma pantalla
- No inventar textos, funciones ni datos institucionales

## Surfaces

| Level | Name | Value | Purpose |
|-------|------|-------|---------|
| 0 | Marco | `#fcf4e1` | Inicio de sesión, portada, encabezados |
| 0 | Trabajo | `#faf6ef` | Fondo de pantallas de trabajo |
| 1 | Papel | `#fefcf9` | Tarjetas, filas, formularios, fichas de miniatura |
| 1 | Café | `#5b2610` | Tarjetas de dimensión, barra superior |

## Layout

Celular primero (360px), margen lateral 16px, una sola columna, barra superior fija. Un título por pantalla y una acción principal. En PC: contenido centrado con ancho máximo de 1120px; la portada usa título editorial y tres tarjetas en fila; la asistencia muestra la semana completa.

## Pantallas del prototipo

1. Inicio de sesión — celular y PC. "CarpetaDocente" grande en `--font-display`, debajo "I.E. Virgen del Carmen – Huayucachi"; una línea con las tres dimensiones en orden; campos Usuario y Contraseña; botón "Ingresar". Variante con error: "Usuario o contraseña incorrectos, o cuenta inactiva", con el usuario conservado. Sin las tres tarjetas.
2. Portada del docente — celular y PC. "Hola, Prof. Ana Quispe" y las tres tarjetas de dimensión. En el prototipo las tres se ven completas; en la aplicación real del Sprint 1, Sesiones y Notas llevan "Próximamente".
3. Asistencia de hoy — celular (un día con selector) y PC (5 columnas). 3.° grado, sección A, 25 estudiantes ficticios.
4. Portada de la dirección — PC. Mismo marco, vista de conjunto por sección.

## Listo para la prueba con docentes

- `npx impeccable detect` sin hallazgos principales
- Evaluación con las 10 heurísticas de Nielsen sin problemas de gravedad 3 o 4
- Contraste AA verificado en todas las combinaciones usadas
- Revisión de carga cognitiva del flujo de asistencia
- Sin desplazamiento horizontal a 360px

## Quick Start

### Tailwind v4

```css
@theme {
  --color-primario: #5b2610;
  --color-texto: #2c150c;
  --color-texto-suave: #7b422d;
  --color-fondo: #fcf4e1;
  --color-fondo-trabajo: #faf6ef;
  --color-superficie: #fefcf9;
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
  --font-display: "POR-DEFINIR", var(--font-sans);

  --text-caption: 14px;
  --text-body: 16px;
  --text-subheading: 18px;
  --text-heading: 24px;
  --text-display: 32px;

  --radius-pill: 999px;
  --radius-campo: 10px;
  --radius-tarjeta: 12px;
  --radius-dimension: 20px;

  --shadow-ficha: 0 6px 20px rgba(44, 21, 12, 0.12);
}
```
