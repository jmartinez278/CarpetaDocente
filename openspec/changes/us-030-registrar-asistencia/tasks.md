# Tasks

**Reglas para todas las tareas:**
- Pruebas primero (TDD): cada prueba se escribe y se ve fallar antes del código. Ante una falla inesperada, depuración sistemática.
- Antes de usar una API de Django, HTMX, Tailwind o Playwright (y `fetch` con `keepalive`), se consulta Context7.
- Solo nombres ficticios (los del boceto). Ningún dato de la I.E. inventado.
- Pantallas: referencia en `C:\Proyectos\prototipos-cd\decision-final\` (capturas en `capturas/`); estructura, clases y textos se toman de ahí sin copiar el boceto ni su `asistencia.js`. Un intento de plantilla y una corrección; si pasa las pruebas y axe, se sigue. Solo clases de tokens en las plantillas, contra DESIGN.md 0.4.
- Un commit por parte. Su casilla y su evidencia en `verificacion.md` van en ese commit. Antes de cada commit:
  - revisión (Superpowers `requesting-code-review`): Critical e Important se corrigen; los Minor van a `verificacion.md`, "## Minor para la descripción del PR";
  - lo que entra va al índice y se corre `uv run python scripts/verificar.py --antes-del-commit`;
  - se muestran los archivos y el mensaje, y se espera la aprobación. Sin push.

## 1. DESIGN.md, modelos y servicios (D1, D2, D9, D11)

### Parte A: DESIGN.md 0.4 (commit propio, antes de cualquier plantilla)

- [x] 1.1 Prueba primero: no aplica (documento). Aplicar `DESIGN-0.3-propuesta.md` como "Cambios 0.4 (dirección visual 0.3, US-030)", con la corrección de la frase repetida, y alinear las secciones que lista D11; actualizar `.claude/rules/plantillas.md` a 0.4. Mostrar el diff a Marco antes del commit. Verificar: el encabezado dice 0.4 y 29-10-2026; ninguna sección sigue diciendo "Apellido, inicial.", "5 columnas" ni "Hola," como regla; `verificar.py --antes-del-commit` pasa; commit solo con DESIGN.md y la regla

### Parte B: modelos y migraciones (alto riesgo, solo)

- [x] 1.2 Prueba primero, `institucion/tests/test_modelos_estudiante.py`: estudiante nuevo ACTIVO y `fecha_estado` nulo; estado fuera de los tres rechazado por la base (`IntegrityError`); `importar_lista` y `agregar_estudiante` dejan ACTIVO. Luego `estado`, `fecha_estado`, `ck_estudiante_estado` y `institucion/0004`. Verificar: rojo y luego verde; `sqlmigrate institucion 0004` muestra el valor por defecto y la restricción
- [x] 1.3 Prueba primero, `asistencia/tests/test_modelos.py`: segunda jornada de la misma sección y fecha rechazada; segundo estado del mismo estudiante en la jornada rechazado; estado fuera de los cuatro rechazado; nota con estado distinto de JUSTIFICADO rechazada (`ck_asistencia_nota`); borrar la sección borra jornadas y asistencias; `actualizado_en` cambia al actualizar. Y en `institucion/tests/test_servicios_estudiantes.py`, con asistencia real (sin simular): `quitar_estudiante` y `vaciar_lista` lanzan `ListaConRegistros` y no borran ninguno. Luego `Jornada`, `Asistencia` (D1) y `asistencia/0001`. Verificar: rojo y luego verde; `makemigrations --check` sin cambios pendientes; `sqlmigrate asistencia 0001` muestra `uq_jornada`, `uq_asistencia`, `ck_asistencia_estado` y `ck_asistencia_nota` (el `RESTRICT` lo aplica Django al borrar; la prueba con asistencia real es la que lo comprueba)
- [x] 1.4 Revisión de la parte (sin DESIGN.md) y commit (reglas de arriba)

### Parte C: servicios y marca de actividad

- [x] 1.5 Prueba primero, `asistencia/tests/test_servicios.py` (con `hoy` fijo):
  - `marcar`: crea la jornada con el primer toque y una sola con dos toques; el mismo guardado dos veces deja una fila; dos estados seguidos dejan el último; nota guardada solo con JUSTIFICADO y borrada al pasar a otro; nota de 101 caracteres, estado inválido, fecha que no es hoy, sábado, estudiante de otra sección y estudiante RETIRADO rechazados sin crear jornada;
  - `marcar_restantes`: solo los Sin marcar; no pisa a los ya marcados; un id ajeno hace fallar todo el lote;
  - `lista_de_hoy`: sin jornada no la crea; orden, numeración 1..M solo de activos, no activos aparte, avance "18 de 25" y totales; completa cuando los activos tienen estado;
  - `pendiente_hoy`, `es_dia_de_clases`, `texto_fecha` ("Miércoles 28 de octubre") y `saludo` (11:59, 12:00, 18:59, 19:00, 4:00).

  Luego `asistencia/servicios.py` (D2). Verificar: rojo y luego verde
- [x] 1.6 Prueba primero, `cuentas/tests/test_inactividad.py`: dos peticiones a 10 s no modifican la sesión; a 30 s, sí; los escenarios de 59 y 60 minutos siguen en verde. Luego D9 en `InactividadMiddleware`. Verificar: rojo y luego verde; `uv run pytest --cov` en verde y con 80 % o más
- [x] 1.7 Revisión de la parte y commit (reglas de arriba)

## 2. Pantallas y guardado (D3 a D8, D10, D12)

### Parte A: rutas, barra, portada y aviso de la lista de estudiantes

- [x] 2.1 Prueba primero, `asistencia/tests/test_vistas.py` y `cuentas/tests/test_pantallas.py`:
  - las tres rutas de D10: docente de la sección 200/204; otra docente y año CERRADO 404; otro rol a su inicio; sin sesión a `/ingresar/?next=…`; con `HX-Request` y sesión vencida, `HX-Redirect`; POST sin CSRF rechazado; respuestas 400, 404 y 409 de D3;
  - portada: "Buenos días," según la hora; fecha delante de la sección; tarjeta Asistencia con "Registrar asistencia" y enlace a `asistencia:hoy` solo con sección única, "Próximamente" sin ella; píldora "Hoy: pendiente" con `aria-describedby`, ausente con la jornada completa, en sábado y sin estudiantes;
  - el aviso "N estudiantes importados" con "Tomar la asistencia de hoy".

  Luego `asistencia/urls.py` con el conversor `fecha`, las vistas, `config/urls.py`, la portada (D10), `tarjeta_dimension.html`, la barra de `marco.html` y `_lista.html`; actualizar en la misma rama las pruebas de US-001 y US-006 que miran "Hola," y el Catálogo de rutas de `docs/03` (versión y fecha). Verificar: rojo y luego verde; `test_dimensiones.py` en verde
- [x] 2.2 Portada y lista de estudiantes con la dirección 0.4. Capturas `portada-360-claro.png`, `portada-1280-claro.png`, `estudiantes-360-claro.png` y `detalle-barra-*`. E2E: la píldora aparece una vez (sin movimiento con "reducir movimiento"); el enlace del aviso abre la asistencia como página completa; axe de la portada (con y sin píldora) y de la lista con el aviso en ambos temas a 360 y 1280 px; 320 px sin desplazamiento horizontal. Verificar: e2e en verde, `npm run build` sin errores y ningún hexadecimal ni `style=` en las plantillas
- [x] 2.3 Pantallas de la parte vistas en claro/oscuro y celular/escritorio (la marca Marco). Revisión de la parte (con las secciones de DESIGN.md que usa: Barra, Saludo, Tarjeta de dimensión, Mensaje, Movimiento) y commit (reglas de arriba)

### Parte B: pantalla de asistencia y guardado por toque

- [x] 2.4 Prueba primero, `asistencia/tests/test_vistas.py` (HTML de `hoy`): fecha y selector con hoy como único día activo y los demás con `aria-disabled` y su etiqueta; "0 de 25 marcados"; filas con nombre completo, estado en palabras y círculo con nombre accesible "NOMBRE: Faltó. Cambiar a Tarde"; no activos al final con su marca; nota visible solo en Justificado con `maxlength="100"`; "Marcar los N restantes" (y "el restante") solo con Sin marcar; sábado ("Hoy no hay clases"); sin estudiantes (aviso y "Ver estudiantes"); jornada completa dibujada con el cierre; `<noscript>`. Luego `templates/asistencia/` y el CSS (D10, D12). Capturas `asistencia-marcando-360-*`, `asistencia-pc-1280-*` y `asistencia-completa-*`; HTML `#vista-1` a `#vista-6` y `#vista-10`. Verificar: rojo y luego verde
- [x] 2.5 Prueba primero, `asistencia/tests/test_asistencia_e2e.py`: escenario "Camino ideal" (25 toques hasta "Asistió: 21 · Tarde: 1 · Faltó: 2 · Justificado: 1", contados en la base); "Volver a abrir"; "Toques rápidos mientras se guarda" (con la ruta demorada por `page.route`); "Guardado sano" ("Guardando…" y "✓ Guardado"); nota guardada al salir del campo; Intro y espacio en el círculo; axe de la lista a medio marcar en ambos temas y anchos. Luego `static/js/asistencia.js`: ciclo, cola por fila sin abortar, franja de guardado, avance, totales y nota (D3, D4, D7). Verificar: rojo y luego verde
- [x] 2.6 Pantallas de la parte vistas (la marca Marco). Revisión de la parte (Fila de asistencia, Asistencia en PC, Estados de asistencia, Campo de texto y Botón secundario de DESIGN.md) y commit (reglas de arriba)

### Parte C: lote, cortes de red, sesión vencida y cierre

- [x] 2.7 Prueba primero, en `test_asistencia_e2e.py`:
  - lote: "Flujo alternativo válido"; "Deshacer" (nada en la base); "Fin de la cuenta" con su anuncio; "Toque durante la cuenta"; cerrar la página durante la cuenta (la base tiene los N); pausa con el puntero;
  - RNF-011: 10 cortes de red con `context.set_offline` durante los toques → 0 toques perdidos o duplicados en la base y cada fila fallida con "sin guardar. Reintentando…"; "N sin guardar"; "Sin conexión" solo al tercer fallo seguido y una vez; se va al volver la red;
  - aviso al salir con una marca pendiente (`beforeunload`);
  - sesión vencida: toque → `/ingresar/` con el aviso; al volver a entrar y abrir la asistencia de hoy, la marca queda guardada;
  - cierre: aparece tras el último "Guardado", no con la última marca sin guardar ni durante la cuenta, y desaparece si se deshace; axe de las vistas con barra, sin conexión y completa, en ambos temas y anchos; 320 px sin desplazamiento horizontal con un nombre de 120 + 120.

  Luego el lote, reintentos, `sessionStorage`, aviso al salir y cierre en `asistencia.js` (D3, D5, D6, D8). Verificar: rojo y luego verde; `uv run pytest --cov` (80 % o más) y `uv run pytest -m e2e --browser chromium` en verde, con el CSS compilado y `DJANGO_ALLOW_ASYNC_UNSAFE=true`
- [x] 2.8 Pantallas de la parte vistas (la marca Marco). Revisión de la parte (Mensaje de error, Movimiento y Fila de asistencia de DESIGN.md) y commit (reglas de arriba)

## 3. Revisión final y verificación

- [ ] 3.1 Con la revisión final A2 que corre el usuario (`/codex:adversarial-review --base main --background`, con foco en los specs del cambio y en RNF-011), corregir los Critical e Important, con la prueba primero en cada caso. Los Minor van a `verificacion.md`. Verificar: `uv run pytest --cov`, las e2e y `verificar.py --antes-del-commit` en verde
- [ ] 3.2 `verificacion.md` corto: tabla escenario → prueba de los tres specs del cambio y la DoD 1 a 9. Verificar: cada escenario tiene su prueba o una nota de por qué no aplica; commit del grupo (reglas de arriba)

## Workflow follow-up

- **(equipo)** Push de `feature/US-030-registrar-asistencia` y PR hacia `main` (`Closes #N` de US-030 y de US-032, verificando los números), con las verificaciones de EN-08 en verde. En "Para quien revise": DESIGN.md pasa a 0.4 (dirección visual 0.3, decisión 18 de Marco por tiempo); cambian la portada (saludo, fecha, píldora, tarjeta Asistencia), la barra y el aviso de la lista de estudiantes, sin cambiar el comportamiento de US-001 ni US-006; pruebas de esas historias actualizadas; "Marcar los N restantes" en lugar de "Marcar todos"; la marca de actividad cada 30 s (D9). En "## Deuda":
  - días anteriores, día olvidado, periodo cerrado y registro de actividad → US-031; deslizar entre días → US-031;
  - historial, totales por periodo e ingresos tardíos (RN-012) → US-033; exportación → US-034;
  - pantalla para cambiar el estado del estudiante → según la I.E. (Nayely); cabeceras con franjas de Sesiones y Notas;
  - dos pestañas o equipos sobre la misma fila (gana la última); sin JavaScript no se marca;
  - P2 F de la crítica r3 (bloque de guardado junto al avance en PC) → pulido;
  - recomendación de pulido (US-006, idea de Marco del 29-10): "Quitar estudiante" y "Vaciar lista" como **popup de confirmación** (preferido por Marco: más rápido e intuitivo), con el bloqueo "No se puede quitar…" como resultado dentro del mismo popup. Variante: al pie del popup, una nota en `--color-texto-suave` con "*" ("* No puedes quitar ni vaciar si ya hay registros"). Implica: diálogo encima del diálogo de la lista (Esc, Atrás y foco en `estudiantes.js`), `alertdialog`, el componente en DESIGN.md (solo en el pulido) y conservar la vista actual sin JavaScript. Hoy Editar y Vaciar ya dicen la condición en texto de ayuda; revisar que no se repita;
  - contradicciones: doc 11 (`asistencia.estudiante_id` en cascada → `RESTRICT`; `actualizado_en` agregado); doc 06/02 ("Marcar todos como Asistió"; nota de justificación de RF-031 en US-030).
- **(equipo)** Aprobación del PR por otra integrante (DoD 3).
- Después de la fusión: `/opsx:archive` con "Sync now". La siguiente historia sale de `main` y su primer commit es este archivo.
