# Tasks

## 1. Modelos y catálogo de actividad (D2, D5, D11)

### Parte A: anexo, equivalencia de secciones y operación nueva [riesgo: alto]

- [x] 1.1 Prueba primero, `institucion/tests/` (el archivo de modelos) y `institucion/tests/test_admin.py` (o el del panel de la institución): escenarios de «Entidad Institución» (sin anexo queda 0; anexo 10 → `IntegrityError`); la ficha del panel muestra y guarda el anexo y deja INSTITUCION_EDITADA con `anexo` en `campos`. Luego `anexo` con `db_default=0` y su `CHECK`, la migración de `institucion` y el campo en `institucion/admin.py`. Verificar: rojo y luego verde; `makemigrations --check` sin cambios; `uv run pytest src/backend/institucion`
- [x] 1.2 Prueba primero, `exportaciones/tests/test_modelos.py` (nuevo): una equivalencia válida se guarda; la misma sección dos veces y la misma (año, grado, código, nombre) dos veces → `IntegrityError`; borrar la sección borra su equivalencia; el admin es de solo lectura (sin agregar, cambiar ni borrar) y pasa `test_cada_model_admin_que_escribe_usa_la_mezcla`. Luego `EquivalenciaSeccion`, `exportaciones/0001` y `exportaciones/admin.py`. Verificar: rojo y luego verde; `sqlmigrate exportaciones 0001` muestra las dos restricciones únicas
- [x] 1.3 Prueba primero, `actividad/tests/` (el archivo del catálogo): PLANTILLA_SIAGIE_COMPLETADA y EQUIVALENCIA_SECCION_BORRADA están en el catálogo y fuera de `CUENTAN_KPI_01`; `registrar` acepta las claves de D11 de cada una y rechaza `nombres`, `archivo`, `codigo_siagie` y `seccion_siagie`. Luego las dos operaciones (en `RESERVADAS` hasta la parte B), `DETALLE_PERMITIDO` y la migración de `actividad`. Verificar: rojo y luego verde; `uv run pytest src/backend/actividad`
- [x] 1.4 Revisión de la parte (agente `revisor`, flujo anterior), `verificar.py` y commit

## 2. Lectura y llenado del libro (D2, D5 a D9, D11)

### Parte B: reconocer, resolver la sección, cruzar y escribir [riesgo: alto]

- [x] 2.1 Agregar `openpyxl` y `defusedxml` con `uv add` y consultar en Context7 `load_workbook`, la escritura de celdas y las validaciones de openpyxl. Prueba primero, `exportaciones/tests/plantilla.py` (generador ficticio de D12) y `exportaciones/tests/test_siagie.py` (nuevo): leer Parametros (código como texto y como número, anexo, año, «B3», «SEGUNDO», código y nombre de sección); etiquetas cambiadas, hoja `Parametros` ausente, hoja con nombre sin código, número de competencia sin «NL» debajo, PDF renombrado, archivo vacío, zip que se infla por encima del límite, más de 300 partes y libro con macros → `PlantillaNoReconocida`; filas hasta la primera sin nombre; ida y vuelta: tras escribir, la hoja oculta, las validaciones y las celdas no tocadas siguen igual. Luego `exportaciones/siagie.py`. Verificar: rojo y luego verde; `uv run pytest src/backend/exportaciones`
- [x] 2.2 Prueba primero, `exportaciones/tests/test_servicios_reconocer.py` (nuevo): escenarios de «Archivo que no corresponde a la plantilla» (otra institución, otro anexo, institución sin código modular, año inexistente, «B5», institución por trimestres, área «0099», competencia «05» en Matemática con 4 activas, una competencia desactivada corre los números como en la hoja de notas) y de «Sección de la plantilla» (el nombre coincide sin tildes ni mayúsculas, equivalencia guardada de cualquier periodo, varias opciones → `EligeSeccion` sin las que ya tienen equivalencia, sin secciones del grado, sección de otra institución, año o grado → `SeccionNoValida`, la carrera de D5 con `IntegrityError`). Luego el reconocimiento y la resolución de la sección en `exportaciones/servicios.py`. Verificar: rojo y luego verde
- [x] 2.3 Prueba primero, `exportaciones/tests/test_servicios_llenar.py` (nuevo): escenarios de «Estudiantes de la plantilla» (tildes distintas, no está en la sección, sin parecidos, homónimo normalizado, trasladado con notas, el mismo no encontrado en varias hojas cuenta una vez), «Llenado de la plantilla» (camino ideal, columna por número, celda con otro valor y con fórmula cuentan como reemplazadas, mismo valor no cuenta, AD vacía la conclusión, nota que no tiene no toca la celda, sin «Pendiente»), «Sin notas en el periodo» (con y sin equivalencia nueva: ni archivo, ni equivalencia, ni entrada), faltantes con la regla de `notas_faltantes` (área a cargo del docente de curso no suma) y los cuatro conteos y el título de «Resumen del llenado»; «Plantilla del SIAGIE completada» (detalle exacto, `equivalencia` true/false, sin nombres) y «El archivo no se guarda» (sin archivos en el almacén ni nombres en la base). Luego el llenado, los conteos y `registrar` en `exportaciones/servicios.py`; PLANTILLA_SIAGIE_COMPLETADA sale de `RESERVADAS` con su fila en `actividad/tests/escenarios.py`. Verificar: rojo y luego verde; `uv run pytest src/backend/exportaciones src/backend/actividad`
- [x] 2.4 Prueba primero, `exportaciones/tests/test_servicios_equivalencia.py` (nuevo): escenarios de «Corregir la equivalencia» en servicio (borrar la propia deja EQUIVALENCIA_SECCION_BORRADA con `{"anio", "grado"}`; la siguiente plantilla vuelve a dar `EligeSeccion` con esa sección entre las opciones; de otra institución o ya borrada → `EquivalenciaInexistente` sin entrada; borrado repetido sin entrada nueva) y el resumen lleva el id de la equivalencia solo si la sección salió de una. Luego `borrar_equivalencia` (D13); la operación sale de `RESERVADAS` con su fila en `escenarios.py`. Verificar: rojo y luego verde; `uv run pytest src/backend/exportaciones src/backend/actividad`
- [x] 2.5 Revisión de la parte (agente `revisor`, flujo anterior), `verificar.py` y commit

## 3. Ruta y permisos (D1, D3, D4)

### Parte C: vista `POST /direccion/plantilla-siagie/` [riesgo: alto]

- [x] 3.1 Prueba primero, `exportaciones/tests/test_vistas.py` (nuevo): escenarios de «Solo la dirección completa la plantilla» (docente y Administrador a su inicio, sin sesión al ingreso, GET 405, sin entrada), 200 con `data-paso="seccion"` y con `data-paso="resumen"`, el archivo en base64 en `data-archivo` y el nombre base en `download` (un nombre con ruta queda sin ella), 400 con el JSON de cada rechazo (más de 4 MB con su mensaje propio; periodo sin notas sin la ayuda del SIAGIE; sección no válida), los nombres no encontrados escapados y «Recargar el resumen» (GET `/direccion/` sin resumen). Luego `exportaciones/views.py`, `exportaciones/urls.py` y la inclusión en `config/urls.py`. Verificar: rojo y luego verde; `uv run pytest src/backend/exportaciones`
- [x] 3.2 Prueba primero, `exportaciones/tests/test_vistas.py`: `POST …/equivalencias/<id>/borrar/` de la dirección propia (200 con el aviso y «Subir plantilla otra vez», sin «Descargar plantilla»; sin `HX`/JS, 303 a `/direccion/`), de otra institución o ya borrada (404 con «Esta equivalencia ya no existe.»), docente y Administrador a su inicio sin borrar, sin CSRF rechazado, GET 405. Luego la vista y la ruta de D13. Verificar: rojo y luego verde
- [x] 3.3 `verificar.py` y commit; luego `/codex:adversarial-review --base 46ded14 --background`. Sus Critical e Important se corrigen en el commit de la parte D

## 4. Pantallas (D10)

### Parte D: inicio de la dirección, diálogo, elección de sección y resumen [riesgo: medio]

- [ ] 4.1 Medir RNF-003 en la vista previa de Vercel con una plantilla ficticia de 30 estudiantes del tamaño de la muestra y el perfil Slow 4G (subida + resumen ≤ 5 s). Verificar: el tiempo queda anotado para `verificacion.md`; si pasa de 5 s, plan B de D4 antes de seguir
- [x] 4.2 Prueba primero, `exportaciones/tests/test_plantillas.py` (nuevo) y la prueba del inicio de la dirección en `cuentas/tests/`: escenarios de «Inicio de la dirección» (bloque con su ayuda y «Subir plantilla» entre el saludo y «Consolidados»), textos de «Diálogo “Sube la plantilla del SIAGIE”», del paso «Elige la sección» (tarjeta «2.º TRIUNFADORES · Tercer bimestre 2026», radios sin marcar, ayuda, «Guardar y completar») y del resumen con y sin observaciones (cuatro conteos en cero, sin lista de nombres; «¿No es esta sección?» solo con equivalencia); sin `style=` ni hex. Luego `templates/direccion/inicio.html` y `templates/exportaciones/` (`_dialogo.html`, `_seccion.html`, `_resumen.html`) según los bocetos, con las clases que falten en `src/frontend/`. Verificar: rojo y luego verde
- [x] 4.3 Prueba primero, `exportaciones/tests/test_plantilla_siagie_e2e.py` (nuevo, las 6 de D12): flujo principal con la descarga y el foco de vuelta a «Subir plantilla» al cancelar; elegir 2.º B y completar sin volver a elegir el archivo, y luego «¿No es esta sección?» cambia el panel del archivo y quita la descarga; rechazo con el foco en el mensaje y el nombre conservado; corte de red con el archivo conservado; 360 px del resumen con un nombre largo; axe en ambos temas (diálogo con error, paso de la sección, resumen). Luego `static/js/plantilla-siagie.js`. Verificar: rojo y luego verde; solo este archivo e2e
- [ ] 4.4 Pantallas vistas por Marco: inicio, subida, procesando, error, elegir sección y resumen (con y sin observaciones), en claro/oscuro y 360/1280 px. `verificar.py` y commit (con los arreglos de Codex de la parte C); luego `/codex:review --base <commit de la parte C> --background`

## 5. Cierre

### Parte E: cierre

- [ ] 5.1 Recoger el resultado de Codex de la parte D y, como hay 4 grupos, correr `/codex:review --base main --background`; corregir sus Critical e Important con la prueba primero, en un commit corto. Verificar: `uv run python scripts/verificar.py --completo` y `-m e2e` completo, una sola vez, en verde; la vista previa aplica las tres migraciones en Neon
- [ ] 5.2 Catálogo de rutas de `docs/03` con `/direccion/plantilla-siagie/`. `verificacion.md`: DoD 1 a 9, la medición de RNF-003, los escenarios sin prueba con su motivo («Se abre en Excel y LibreOffice» es manual). Verificar: el archivo existe y cada escenario sin prueba tiene motivo; commit

## e2e a retirar

Ninguna: la pantalla del inicio de la dirección solo tiene la e2e parametrizada de `test_portada_e2e.py`, que ya cumple las reglas.

## Ajustes del propose a decisiones.md

- Decisión 3: el anexo se compara con un campo nuevo de la institución, que el Administrador edita en el panel.
- Decisión 4: la equivalencia es una por sección de la I.E.; la elección vuelve a enviar el archivo, que no se guarda entre pasos.
- Decisión 6: «01» es la primera competencia activa del área, como C1 en la hoja de notas.
- Decisión 5: los homónimos normalizados van a «No encontrados»; se cruzan estudiantes de cualquier estado.
- Decisión 9: «estudiantes encontrados» en vez de «completados» del boceto; título «con observaciones» si hay no encontrados o faltantes.
- Copia nueva: «Tu I.E. no tiene secciones de 2.º grado en 2026.», «La sección elegida no es válida. Elige una de la lista.», el mensaje de corte de red y los textos de «¿No es esta sección?».
- Corrección de la equivalencia (decidida por Marco el 18-11-2026): «¿No es esta sección?» en el resumen la borra y registra EQUIVALENCIA_SECCION_BORRADA.

## Workflow follow-up

- **(deuda, pasada de docs)** RF-024/RF-025, US-024/US-025 (doc 02), SUP-12 (doc 04): «docente», «hoja propia», «formato de la UGEL» y su mensaje. Doc 11: `institucion.anexo` y la tabla `equivalencia_seccion`. Doc 10: `defusedxml`.
- **(deuda)** Alerta automática cuando un llenado tiene muchos «no encontrados» (posible equivalencia equivocada).
- **(deuda)** Trimestres: letra del periodo del SIAGIE (US-028).
- **(pulido)** Doble borde rojo y ruta del SIAGIE repetida en `error.html`.
- **(equipo, antes del piloto)** El Administrador carga el código modular y el anexo reales [DATO I.E. PENDIENTE]; abrir una plantilla llena en Excel y LibreOffice (RNF-006) y que la dirección la cargue una vez en el SIAGIE. Preguntas a Nayely: nombres de las secciones en el SIAGIE y si la dirección usa «Periodo por Excel».
- **(equipo)** Push y PR hacia `main` (`Closes #N` de US-024 y US-025, verificando los números). En «Para quien revise»: el archivo no se guarda (D3, D4) y openpyxl descarta partes vacías del libro (design, Context).
- **(Deuda del PR, Minor del revisor, parte A)** La prueba de anexo 10 en la ficha no fija el texto «El anexo va de 0 a 9.». `RESERVADAS` debe quedar vacío al terminar la parte B (escenario «Cada operación tiene su prueba»). `grado` y `anio_escolar` de la equivalencia no tienen `CHECK` contra la sección: la parte B prueba el rechazo en el servicio (D5).
- **(Deuda del PR, Minor del revisor, parte B)** Con todas las secciones del grado con equivalencia y ninguna coincidente, `EligeSeccion` sale sin opciones (decidir en la parte C/D un mensaje propio). Una sección que coincide por nombre se usa aunque ya sea la equivalencia de otra del SIAGIE (nota para «Para quien revise»). Una celda NL o de conclusión combinada en una fila de datos daba `AttributeError` (500) en `Libro.escribir`: corregido sin prueba (decisión de Marco), ahora es `PlantillaNoReconocida`.
