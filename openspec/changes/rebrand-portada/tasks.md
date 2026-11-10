# Tasks

Ninguna parte es de alto riesgo: no toca modelos, permisos, transacciones ni notas, y decisiones.md no marca zonas de cuidado. Los nombres de estudiantes (RN-015) solo cambian de contenedor. El primer commit de la rama (archivo de `rebrand-us-006`) ya está hecho (`6120162`).

## 1. Portada en el marco del rebrand

### Parte A: Portada y diálogo de Estudiantes (normal)

- [x] 1.1 Prueba primero, `cuentas/tests/test_dimensiones.py`: `DIMENSIONES` va en el orden Asistencia, Sesiones y Notas con `titulo`, `frase` y `verbo` (frases de decisiones.md, punto 5); el ☰ sigue en Inicio, Sesiones, Asistencia y Notas; se borran las pruebas de `tarjeta_inicial`. Luego `dimensiones.py`: orden, `subtitulo` → `frase`, sin `tarjeta_inicial` (D2). Verificar: rojo y luego verde; `uv run pytest src/backend/cuentas/tests/test_dimensiones.py`
- [x] 1.2 Prueba primero, `cuentas/tests/test_marco_rebrand.py`: el bloque `clase_barra` vacío no cambia el HTML de «sin permiso»; con `appbar--portada`, la barra la lleva. Luego el bloque en `marco_rebrand.html` y `.appbar--portada { position: static }` en `rebrand/marco.css` (D1). Verificar: rojo y luego verde; `uv run pytest src/backend/cuentas/tests/test_marco_rebrand.py`
- [x] 1.3 Prueba primero, `cuentas/tests/test_pantallas.py`: la portada carga solo `dist/rebrand.css`, `portada.js`, `htmx.min.js` y `estudiantes.js`, sin `alpine.min.js`; un solo `<main>`; sin ☰ y con `appbar--portada`; el `<h1>` con saludo y nombre, la línea de fecha y secciones fuera del `<h1>`, «Ver estudiantes» con `id`, `hx-get` y `data-abrir-estudiantes`; `<nav aria-label="Tus accesos">`; sin `chip`, `punto`, `data-carrusel`, `x-data` ni `carrusel__`. Las pruebas por `.portada`, `.chips` y `dimension__*` pasan a ganchos e `id`; se borran las de chips, puntos, tarjeta inicial y orden de scripts con Alpine. Luego `portada_docente.html` y `PortadaDocenteView` sin `inicial` (D1, D2). Verificar: rojo y luego verde; `uv run pytest src/backend/cuentas/tests/test_pantallas.py`
- [x] 1.4 Prueba primero, `test_pantallas.py`: las tres tarjetas en el orden Asistencia, Sesiones y Notas en el HTML, cada una con `c-`, `dim-`, su frase y su miniatura `aria-hidden`, sin «Planificación de sesiones de aprendizaje», «Registro y control de notas» ni «Control de asistencia» (escenario «Portada al entrar»); disponible: enlace con `aria-describedby="acc-<clave>"` (más `pend-asistencia` con la píldora) y el verbo de la spec; «Próximamente»: botón `aria-disabled` con `data-proxima`, `ins-<clave>` y región `aria-live` vacía, sin enlace. Las pruebas de disponibilidad, Asistencia, Notas y píldora existentes siguen en verde. Luego `rb/tarjeta_dimension.html` y borrar `componentes/tarjeta_dimension.html` (D3). Verificar: rojo y luego verde; `uv run pytest src/backend/cuentas`
- [x] 1.5 Prueba primero, `test_pantallas.py`: cada miniatura es `aria-hidden`, no trae nombres, fechas ni cifras de registro; la de Notas trae AD, A, B y C. Luego `rb/miniatura_{asistencia,sesiones,notas}.html` desde el boceto y borrar `componentes/miniatura_*.html` (D4). Verificar: rojo y luego verde; mismo archivo
- [x] 1.6 `rebrand/pantallas/portada.css` (rejilla de 12 columnas, tarjeta café en Asistencia, compactas hasta 699 px, miniaturas con `--preview-*`, aviso con renglón reservado), su `@import` y el `@source` de la portada en `rebrand.css` (D4). Prueba primero, `cuentas/tests/test_portada_e2e.py`: a 1280 px Asistencia ocupa la columna principal y Sesiones y Notas van a su lado, una sobre otra; a 360 px las tres apiladas en el orden del DOM y Sesiones y Notas con la miniatura junto al texto; las miniaturas con el mismo fondo de papel en claro y oscuro; los tokens se leen de `rebrand.css`. Se borran las e2e del carrusel. Verificar: rojo y luego verde; `uv run pytest -m e2e src/backend/cuentas/tests/test_portada_e2e.py --browser chromium` con el CSS compilado y `DJANGO_ALLOW_ASYNC_UNSAFE=true`
- [x] 1.7 Prueba primero, `test_portada_e2e.py`: tocar Sesiones en «Próximamente» no cambia la dirección y muestra «Llegará en una próxima versión.» en la región `aria-live` sin mover la miniatura; dos toques seguidos vuelven a escribir el aviso; a los 3 s se vacía. Luego `portada.js` sin Alpine (D5). Verificar: rojo y luego verde; mismo comando
- [x] 1.8 Prueba primero, `test_portada_e2e.py`: la píldora «Hoy: pendiente» no tiene `animation` (D7); se borran las dos e2e de su subida. Luego el CSS de la píldora en `portada.css`. Verificar: rojo y luego verde; mismo comando
- [x] 1.9 Prueba primero, `test_portada_e2e.py`: a 320 y 360 px, en ambos temas, con la píldora y con el aviso de la sección sin estudiantes, ni el documento ni `.accesos` se desplazan en horizontal (escenario «Portada sin desplazamiento interno»). Luego los ajustes de CSS. Verificar: rojo y luego verde; mismo comando
- [x] 1.10 Prueba primero, `cuentas/tests/test_accesibilidad_e2e.py`: axe sobre la portada con una sección, varias, ninguna, sección sin estudiantes, «Hoy: pendiente», Sesiones «Próximamente» con su aviso, menú de la cuenta abierto y diálogo de Estudiantes abierto, en claro y oscuro, a 360 y 1280 px (escenario «Revisión de cada pantalla»). Luego los ajustes de contraste o foco en `portada.css`. Verificar: rojo y luego verde; `uv run pytest -m e2e src/backend/cuentas --browser chromium`
- [x] 1.11 `<dialog id="estudiantes">` con `dialog dialog--lista` (D6). Prueba primero, `institucion/tests/test_estudiantes_e2e.py`: se borran `SALTO_DIALOGO` y sus 10 marcas; nueva e2e con 40 estudiantes: a 360 y 1280 px el último «Editar» se alcanza desplazando `#modal-cuerpo` y la página de atrás no se mueve. Verificar: rojo y luego verde; `uv run pytest -m e2e src/backend/institucion --browser chromium`
- [x] 1.12 E-2e de conducta en verde sin cambios de lógica: «Ver estudiantes» abre el diálogo, el aviso desaparece al importar sin recargar, la tarjeta Asistencia lleva a la asistencia de hoy, Notas a la hoja, y la cuenta abre y cierra. Verificar: e2e de `cuentas` e `institucion` en verde
- [x] 1.13 Pantalla vista en claro/oscuro y celular/escritorio, con el diálogo abierto (la marca Marco). `verificar.py` y commit

## 2. Cierre

### Parte B: A2 y verificacion.md

- [ ] 2.1 Con la A2 que corre el usuario (`/codex:adversarial-review --base main --background`, con foco en la spec `pantallas-de-inicio` del cambio, D3, D5 y D6), corregir los Critical e Important, con la prueba primero. Verificar: `uv run pytest --cov` (80 % o más), las e2e de todas las apps y `verificar.py --antes-del-commit` en verde
- [ ] 2.2 `verificacion.md`: tabla escenario → prueba de la spec delta (incluido el requisito retirado y su migración) y de las e2e de `estudiantes-seccion` que vuelven a correr, y la DoD 1 a 9. Verificar: cada escenario tiene su prueba o su nota; commit

## Ajustes del propose a decisiones.md

- «Se conserva» `dimensiones.py`: cambian el orden de `DIMENSIONES` y `subtitulo` → `frase`; se borra `tarjeta_inicial`. La regla de disponibilidad (punto 10) no cambia (D2).
- «Se conserva» la vista: pierde `inicial`, que solo usaba el carrusel (D2).
- Punto 9: `portada.js` queda sin Alpine y la portada deja de cargar `alpine.min.js` (D5).
- Punto 5: se conservan los verbos de la spec en `acc-<clave>`, no los «Tomar asistencia» / «Abrir…» del boceto (D3).
- Punto 1: la barra de la portada no es fija, con el bloque `clase_barra` del marco (D1).
- «Hoy: pendiente» pierde la subida de entrada de US-030 (D7).
- `id` conservados todos; ninguno pierde sentido sin el carrusel (`c-<clave>` sigue sirviendo de ancla).

## Workflow follow-up

- **(push)** Al cerrar este cambio, push de `feature/rebrand` con `rebrand-us-006` y `rebrand-portada`, con aprobación; sigue el PR borrador único hacia `main`.
- **(T-04)** El lugar del botón de tema en la barra de la portada queda vacío.
- **(paso 7)** El inicio de la dirección sigue en `marco.html`; su escenario de axe no cambia aquí.
- **(paso 8)** Borrar `alpine.min.js` del vendor si ninguna pantalla lo usa, `app.css` (chips, carrusel, `.portada`, `.dimension__*`, `.ficha`, `.pildora-pendiente`) y `componentes/` que ya no use nadie.
- **(tesis)** Las tarjetas ya no muestran los nombres formales de las dimensiones: anotar en `docs/PENDIENTES_TESIS.md` si un capítulo describe la portada con esos subtítulos.
- **(rebrand-notas)** La actualización de RNF-005 para Notas sigue pendiente; quitar la excepción del carrusel no la necesita.
- Al proponer el paso 4 (Asistencia), su primer commit archiva este con `/opsx:archive` y «Sync now».
