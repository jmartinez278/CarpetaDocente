# Tasks

**Reglas para todas las tareas:**
- Pruebas primero (TDD): cada prueba se escribe y se ve fallar antes del código. Ante una falla inesperada, depuración sistemática.
- Antes de usar una API de Django, HTMX, Tailwind o Playwright, se consulta Context7.
- Solo nombres ficticios (los del boceto). Ningún dato de la I.E. inventado.
- Pantallas: referencia en `insumos/US-006-bocetos/` (capturas en `capturas/`, vistas en `estudiantes.html`); estructura, clases y textos se toman de ahí sin copiar el boceto tal cual. Un intento de plantilla y una corrección; si pasa las pruebas y axe, se sigue. Solo clases de tokens en las plantillas; DESIGN.md no cambia (lo no cubierto, en design D8).
- Un commit por grupo; el grupo 2 va en tres partes, un commit por parte. Su casilla y su evidencia en `verificacion.md` van en ese commit. Antes de cada commit:
  - revisión (Superpowers `requesting-code-review`): Critical e Important se corrigen; los Minor van a `verificacion.md`, "## Minor para la descripción del PR";
  - lo que entra va al índice y se corre `uv run python scripts/verificar.py --antes-del-commit`;
  - se muestran los archivos y el mensaje, y se espera la aprobación. Sin push.

## 1. Modelo, lectura del texto pegado y servicios (D1 a D3, D9)

Tramo de alto riesgo (modelo y restricción): va solo y en modo normal.

- [x] 1.1 Prueba primero, `institucion/tests/test_modelos_estudiante.py`: `normalizar_nombre` (espacios de más, espacio duro U+00A0, mayúsculas con tildes y Ñ); `save()` guarda la forma normalizada; homónimo exacto rechazado por el ORM (`IntegrityError`) y por `full_clean` con su mensaje; mismo nombre en otra sección se guarda; borrar la sección borra a sus estudiantes. Luego `Estudiante` (D1) y la migración `institucion/0003`. Verificar: rojo y luego verde; `sqlmigrate institucion 0003` muestra `uq_estudiante` y la FK a `seccion`; `makemigrations --check` sin cambios pendientes
- [x] 1.2 Prueba primero, `institucion/tests/test_lectura_lista.py` (función pura, sin base de datos):
  - líneas en blanco ignoradas pero contadas en la numeración (al inicio, en medio y al final), incluida la línea de solo espacios o tabulaciones;
  - línea con tabulación → "pega solo la columna…", con y sin coma; sin coma; más de una coma; apellidos vacíos; nombres vacíos; un solo motivo por línea;
  - `\r\n`, `\r` y un U+2028 dentro de una línea no desfasan la numeración;
  - 61 líneas con texto → solo el error de 60.

  Luego `leer_lista_pegada` (D3). Verificar: rojo y luego verde
- [x] 1.3 Prueba primero, `institucion/tests/test_servicios_estudiantes.py`:
  - `importar_lista`: 25 líneas válidas → 25 estudiantes; con un error, ninguno guardado; 121 caracteres en apellidos y en nombres; repetidos agrupados ("Líneas 4 y 12", "Líneas 4, 9 y 12"), también con distintas mayúsculas o espacios; textos de D9 y singular;
  - Pegar lista solo con la sección vacía: con un estudiante, `SeccionConEstudiantes` y nada guardado, aunque el texto sea válido;
  - `estudiantes_ordenados`: "ÁLVAREZ" antes de "BRAVO", "NUÑEZ" después de "NUNEZ" y "ÑAUPA" antes de "OCHOA";
  - `agregar_estudiante` y `editar_estudiante`: normalizan, rechazan el homónimo con su texto y no cambian nada;
  - `quitar_estudiante` y `vaciar_lista`: borran sin registros; con `RestrictedError` simulado lanzan `ListaConRegistros` y no borran ninguno;
  - `secciones_docente` (año CERRADO excluido); `seccion_unica` (una sección con su cantidad; `None` con dos o ninguna); `texto_secciones_docente` sin cambios (sus pruebas de US-005 siguen en verde); `texto_seccion_corto` ("2.º A").

  Luego los servicios (D2). Verificar: rojo y luego verde; `uv run pytest --cov` en verde y con 80 % o más
- [x] 1.4 Revisión del grupo (sin DESIGN.md) y commit (reglas de arriba)

## 2. Rutas, diálogo y pantallas (D4 a D8)

### Parte A: rutas, portada y lista vacía

- [x] 2.1 Prueba primero, `institucion/tests/test_vistas_estudiantes.py` y `cuentas/tests/test_inactividad.py`:
  - las seis rutas de D4: docente de la sección 200; otra docente y año CERRADO 404; estudiante de otra sección 404; dirección a `/direccion/`; sin sesión a `/ingresar/?next=…`;
  - con `HX-Request` responde el parcial con el aviso fuera de banda; sin ella, la página completa con `h1`;
  - POST correcto → 303 y el aviso de éxito una sola vez; POST con errores → 200 con el formulario;
  - sesión vencida y sin sesión con `HX-Request` → 200 con `HX-Redirect` a `/ingresar/?next=/docente/` y el aviso de inactividad; sin `HX-Request`, el 302 de siempre.
  - **Nota (decidido con Marco, 2026-10-27):** "POST correcto → 303 y el aviso de éxito una sola vez; POST con errores → 200 con el formulario" y "estudiante de otra sección 404" pasan a 2.4 y 2.7 (las primeras vistas con POST y con estudiante). Aquí quedaron las rutas, el acceso, parcial frente a página completa y la sesión vencida; las cinco rutas restantes llevan una vista temporal con 404 (`PendienteView`) que las partes B y C reemplazan.

  Luego `institucion/urls.py`, las vistas con su mixin, `pagina.html` y el parcial base (cabecera, cuerpo y pie), el helper `redirigir` en `cuentas/acceso.py` y su uso en el middleware y en `RolRequeridoMixin` (D4, D5, D7). Actualizar el Catálogo de rutas de `docs/03` (versión y fecha). Verificar: rojo y luego verde
- [x] 2.2 Portada y diálogo con la lista vacía. Capturas `estado-1-360-claro.png`, `estado-1-1280-claro.png` y `estado-2-360-claro.png`; HTML: `.seccion-entrada` y `.aviso-portada` (portada), el `<dialog class="modal-estudiantes">` y `#vista-2`.
  - Prueba primero en `cuentas/tests/test_pantallas.py`: con una sección, "Ver estudiantes" (44 px) junto a su línea, que sigue siendo texto; aviso con la sección vacía y sin él con estudiantes; con dos secciones y sin sección, la línea de US-005 igual y sin enlace ni aviso; scripts de la portada con HTMX y `estudiantes.js`.
  - Luego la portada, `estudiantes.js` (D6), el CSS del diálogo (D8) y el parcial de la lista vacía.
  - E2E en `institucion/tests/test_estudiantes_e2e.py`: abrir con "Ver estudiantes"; Esc y "Cerrar" devuelven el foco al enlace; Atrás cierra el diálogo y la portada sigue; volver a abrir funciona; axe de la portada (con aviso) y de la lista vacía en ambos temas a 360 y 1280 px; 320 px sin desplazamiento horizontal.

  Verificar: pruebas en verde, `npm run build` sin errores y ningún hexadecimal ni `style=` en las plantillas
- [x] 2.3 Pantallas de la parte vistas en claro y oscuro, celular y escritorio (la marca Marco). Revisión de la parte (con las secciones de DESIGN.md que usa: Botón principal, Botón secundario, Mensaje, Campo de texto, Estado vacío, Movimiento) y commit (reglas de arriba)

### Parte B: pegar lista y la lista con estudiantes

- [x] 2.4 Pegar lista y Revisar lista. Capturas `estado-3-360-claro.png`, `estado-3-1280-claro.png`, `estado-4-360-claro.png`, `estado-4-1280-oscuro.png` y `estado-4-final-cuerpo-360-claro.png`; HTML `#vista-3` y `#vista-4`, con el número de línea como texto, sin los botones `.localizar-linea` (deuda).
  - Prueba primero en `test_vistas_estudiantes.py` (además, lo diferido de 2.1: POST correcto → 303 y el aviso de éxito una sola vez, POST con errores → 200 con el formulario, con `{% csrf_token %}` en cada formulario): el texto pegado vuelve intacto con `aria-invalid`, cada error con su número, motivo y ayuda; "No se guardó ningún estudiante"; Pegar lista solo con la sección vacía: la lista con estudiantes no ofrece "Pegar lista", el GET muestra el aviso sin el cuadro y el POST no guarda nada.
  - E2E: escenario "Camino ideal" (25 líneas con líneas en blanco → "25 estudiantes importados" y "25 estudiantes" en la cabecera); escenario "Caso de error" (línea sin apellidos y dos repetidas → nada guardado y el texto intacto); sesión vencida al tocar "Importar" → la página completa en `/ingresar/` con el aviso; axe de las dos vistas en ambos temas y anchos.

  Verificar: rojo y luego verde
- [x] 2.5 Lista con estudiantes. Captura `estado-5-360-claro.png`; HTML `#vista-5`.
  - Prueba primero: orden y número calculado, nombre completo sin "…", "Editar" con el nombre en su etiqueta accesible, "Agregar estudiante" arriba, "Vaciar lista" al final, el aviso de éxito con `role="status"` que no se va solo.
  - E2E: tras importar y cerrar, la portada ya no muestra el aviso, sin recargar; un nombre de 120 + 120 caracteres se lee completo a 320 px sin desplazamiento horizontal; axe en ambos temas y anchos.

  Verificar: rojo y luego verde
- [x] 2.6 Pantallas de la parte vistas (la marca Marco). Revisión de la parte (Mensaje, Campo de texto, Movimiento de DESIGN.md) y commit (reglas de arriba)

### Parte C: agregar, editar, quitar y vaciar

- [x] 2.7 Agregar y Editar. Capturas `estado-6-360-claro.png` y `estado-7-360-claro.png`; HTML `#vista-6` y `#vista-7`.
  - Prueba primero (además, lo diferido de 2.1: estudiante de otra sección → 404 en editar y quitar; al terminar, quitar `PendienteView` de `institucion/views.py` y de `urls.py`): campos obligatorios con `maxlength="120"`, errores en el campo, homónimo con la sugerencia y lo escrito conservado, "Guardar y agregar otro" con los campos vacíos y "Estudiante agregado", "Guardar cambios" vuelve a la lista.
  - E2E: escenario "Flujo alternativo válido" (de 25 a 26 en la cabecera, foco en Apellidos); corregir "ANA LUCIA" a "ana lucía" → "QUISPE MAMANI, ANA LUCÍA"; axe en ambos temas y anchos.

  Verificar: rojo y luego verde
- [x] 2.8 Quitar, Vaciar y sus bloqueos. Capturas `estado-8-360-claro.png`, `estado-9-360-claro.png` y `estado-9b-360-claro.png`; HTML `#vista-8`, `#vista-9` y `#vista-9b` (y el bloqueo de quitar con el mismo molde que `#vista-9b`).
  - Prueba primero: confirmaciones con el nombre y la cantidad; con `RestrictedError` simulado, los bloqueos con sus textos, solo "Volver a la lista" y nada borrado.
  - E2E: quitar uno (la cabecera baja en uno); vaciar 25 → lista vacía y el aviso vuelve a la portada; sin JavaScript, desde "Ver estudiantes" como página completa: agregar, pegar, editar y vaciar; axe de las tres vistas en ambos temas y anchos.

  Verificar: rojo y luego verde; `uv run pytest --cov` (80 % o más) y `uv run pytest -m e2e --browser chromium` en verde, con el CSS compilado y `DJANGO_ALLOW_ASYNC_UNSAFE=true`
- [x] 2.9 Pantallas de la parte vistas (la marca Marco). Revisión de la parte (Botón principal, Mensaje y Campo de texto de DESIGN.md) y commit (reglas de arriba)

## 3. Revisión final y verificación

- [x] 3.1 Con la revisión final A2 que corre el usuario (`/codex:adversarial-review --base main --background`, con foco en los specs del cambio), corregir los Critical e Important, con la prueba primero en cada caso. Los Minor van a `verificacion.md`. Verificar: `uv run pytest --cov`, las e2e y `verificar.py --antes-del-commit` en verde
- [x] 3.2 `verificacion.md` corto: tabla escenario → prueba de los dos specs del cambio y la DoD 1 a 9. Verificar: cada escenario tiene su prueba o una nota de por qué no aplica (el bloqueo con registros reales: simulado hasta US-030); commit del grupo (reglas de arriba)

## Workflow follow-up

- **(equipo)** Push de `feature/US-006-importar-estudiantes` y PR hacia `main` (`Closes #N`, verificando el número), con las verificaciones de EN-08 en verde. En "Para quien revise": criterio "importa una hoja de cálculo" → "pega las filas copiadas"; excepción de mayúsculas para los nombres de estudiantes; "JOSE" y "JOSÉ" son dos estudiantes; una docente con varias secciones no tiene "Ver estudiantes" (Minor: no existe en la I.E., C8); la página completa agrega un enlace "Volver a la portada" (sin JavaScript no habría cómo salir de la lista; aprobado por Marco). En "## Deuda":
  - Retirado y Trasladado (RN-027) → US-030; historial → RF-008; OCR y subir Excel; código de estudiante (RN-015);
  - números de línea con enlace en los errores de Pegar lista; Atrás que vuelve a la vista anterior (si EN-07 lo pide);
  - 404 en vez de la denegación con registro → US-004;
  - US-030 debe crear `asistencia` con FK `RESTRICT` y probar el bloqueo de quitar y vaciar con registros reales;
  - entrada a la lista para una docente con varias secciones (Minor);
  - contradicciones: RF-006 y doc 02/01 ("importa una hoja de cálculo con la estructura de columnas"); doc 11 (CASCADE hacia estudiante en calificación, asistencia y exoneración; `estado`, `fecha_estado` y `codigo_estudiante` sin crear); DESIGN.md sin el diálogo ni la excepción de mayúsculas.
- **(equipo)** Aprobación del PR por otra integrante (DoD 3).
- Después de la fusión: `/opsx:archive` con "Sync now". La siguiente historia sale de `main` y su primer commit es este archivo.
