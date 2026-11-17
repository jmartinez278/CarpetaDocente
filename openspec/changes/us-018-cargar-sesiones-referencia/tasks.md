# Tasks

## 1. Modelo y catálogo de actividad (D1, D2, D7)

### Parte A: origen REFERENCIA, rango de grados, `CHECK` y operaciones nuevas (alto riesgo) (revisor)

- [x] 1.1 Prueba primero, `repositorio/tests/test_modelos.py`: una referencia válida (sin autora, `estado=""`, compartida, sin términos, con fuente y permiso, grados 3 a 5) se guarda; cada `CHECK` de D1 rechaza su caso con `IntegrityError` (referencia con autora, con términos, no compartida, sin fuente, sin permiso, con estado; propia sin autora, con estado vacío o con `grado_hasta ≠ grado`; `grado_hasta < grado`; `grado_hasta = 7`); la propia compartida sin fecha sigue rechazada y la no compartida con fecha aceptada; el proxy `SesionReferencia` solo devuelve referencias; `grados_texto` da «2.º grado» y «3.º–5.º grado». Luego D1 y `repositorio/0003` (con `grado_hasta` copiado de `grado`). Verificar: rojo y luego verde; `makemigrations --check` sin cambios; `sqlmigrate repositorio 0003` muestra los `CHECK`
- [x] 1.2 Prueba primero, `repositorio/tests/test_servicios_enviar.py` y la prueba de la demo en `institucion/tests/`: el envío de una docente y la sesión de ejemplo quedan con `grado_hasta = grado`. Luego el ajuste en `_guardar` y `ejemplos.cargar_sesiones`. Verificar: rojo y luego verde; `test_concurrencia.py` en verde
- [x] 1.3 Prueba primero, `actividad/tests/` (el archivo del catálogo): las tres operaciones de D7 están en el catálogo y fuera de `CUENTAN_KPI_01`; `registrar` acepta `{"campos"}` en SESION_REFERENCIA_EDITADA y rechaza `titulo`, `fuente`, `permiso_uso` o `archivo_nombre` en las tres. Luego las operaciones, `DETALLE_PERMITIDO` y la migración de `actividad`. Verificar: rojo y luego verde; `uv run pytest src/backend/actividad`
- [x] 1.4 Revisión de la parte (agente `revisor`), `verificar.py` y commit

## 2. Servicio y panel (D4, D5)

### Parte B: cargar, editar y eliminar en el panel, y borrado en `RegistraEnPanel` (alto riesgo) (revisor)

- [x] 2.1 Prueba primero, `repositorio/tests/test_servicios_referencia.py` (nuevo): escenarios de «Cargar una sesión de referencia» (camino ideal, «Equipo del proyecto», visible solo en su institución), «Fuente y permiso de uso obligatorios» (falta uno, solo espacios, sin archivo en el almacén), «Varios grados» (rango al revés), «Datos y archivo válidos» (área no trabajada por la institución elegida, archivo que no es PDF ni Word, sin archivo), «Texto para la búsqueda» (palabra del .docx, PDF escaneado) y «Registro de la carga» (CARGADA sin SESION_ENVIADA; EDITADA con nombres de campos; sin cambios, sin entrada; ELIMINADA); editar recalcula `texto_busqueda`; eliminar borra fila, vistas y, al confirmar, el archivo; si falla el almacén al cargar, ni fila ni entrada. Luego D4 (`validar_referencia`, `cargar_referencia`, `editar_referencia`, `eliminar_referencia`, `_guardar` generalizado) y las tres operaciones salen de `RESERVADAS` con su fila en `actividad/tests/escenarios.py` (entraron reservadas en la parte A, como INTENTO_SIN_PERMISO en US-008). Verificar: rojo y luego verde; `test_servicios_enviar.py` y `test_concurrencia.py` en verde
- [x] 2.2 Prueba primero, `actividad/tests/test_panel_instrumentado.py`: un `ModelAdmin` sin `operacion_al_borrar` sigue sin poder borrar (`log_deletions` lanza); `test_cada_model_admin_que_escribe_usa_la_mezcla` acepta el borrado solo con `operacion_al_borrar`. Luego D5 en `actividad/panel.py` (consultar con Context7 `log_deletions`, `delete_model` y `get_actions` de Django 5.2). Verificar: rojo y luego verde; `uv run pytest src/backend/actividad`
- [x] 2.3 Prueba primero, `repositorio/tests/test_admin.py` (nuevo, con el cliente del panel): cargar desde la ficha con archivo (escenario «Camino ideal»), el mensaje «Indique la fuente y el permiso de uso» en la ficha, los errores de campo, la institución elegida si hay una sola, editar sin archivo, eliminar con la confirmación del panel, sin la acción de borrado masivo, «Solo las sesiones de referencia en el panel» (la sesión de una docente no está en la lista y su ficha da 404) y «Otro rol» (docente y dirección no entran). Luego `SesionReferenciaAdmin` en `repositorio/admin.py`. Verificar: rojo y luego verde; `uv run pytest src/backend/repositorio`
- [x] 2.4 Revisión de la parte (agente `revisor`), `verificar.py` y commit

## 3. Lecturas y pantallas (D2, D3, D6)

### Parte C: filtro por rango, tarjeta, página e intentos sobre la referencia (alto riesgo)

- [ ] 3.1 Prueba primero, `repositorio/tests/test_servicios_consultas.py`: escenarios «Con material de referencia» (la cuenta en lista, título y contador; no la de otra institución), «Filtrar por un grado del rango» (4.º sí, 6.º no), «Conteo por área» (suma 1), «No está en Mis sesiones», «Material de referencia» de «Quién ve una sesión» (`sesion_visible`) y «Una docente la descarga» (SESION_VISTA y SESION_DESCARGADA con `"propia": false`). Luego el filtro de D2 en `buscar_repositorio` y `conteos_por_area`, y `datos_de_la_pagina` de D3. Verificar: rojo y luego verde
- [ ] 3.2 Prueba primero, `repositorio/tests/test_servicios_autora.py` y `test_vistas.py`: escenarios de «Una docente no cambia el material de referencia» (eliminar, compartir y dejar de compartir → 403 con «Solo el autor puede eliminar esta sesión», INTENTO_SIN_PERMISO con `sesion_ajena`, sesión y archivo intactos). Verificar: rojo y luego verde (sin código nuevo si D3 se cumple)
- [ ] 3.3 Prueba primero, `repositorio/tests/test_plantillas.py`: escenarios «Tarjeta» y «Un solo grado» de «Material de referencia en las listas» (sin nombre de persona); «Fuente y permiso» y «Sin acciones» de «Página del material de referencia» (sin «Autora», con «Fecha de carga», chip «Material de referencia» y no «Compartida», `aside` con fuente y permiso escapados, sin «Tu sesión»); la sesión de una docente sigue igual; ninguna plantilla con `style=` ni hex. Luego D6 en `_lista.html` y `sesion.html` (y la clase en `src/frontend/` si hace falta). Verificar: rojo y luego verde; `test_detalle_e2e.py` y `test_repositorio_e2e.py` en verde
- [ ] 3.4 Pantallas vistas por Marco: repositorio con una referencia y su página, en claro/oscuro y 360/1280 px; la ficha del panel. `verificar.py` y commit

## 4. Cierre

### Parte D: A2 y verificación

- [ ] 4.1 Con la A2 que corre el usuario (`/codex:adversarial-review --base main --background`, con foco en los specs del cambio y en la parte C), corregir los Critical e Important, con la prueba primero. Verificar: `uv run python scripts/verificar.py --completo` y `-m e2e` completo en verde; la vista previa aplica las dos migraciones en Neon y carga y elimina una referencia ficticia desde el panel
- [ ] 4.2 `verificacion.md`: DoD 1 a 9, la carga en la vista previa, los escenarios sin prueba con su motivo y los Minor. Verificar: el archivo existe y cada escenario sin prueba tiene motivo; commit

## e2e a retirar

Ninguna: las e2e de `repositorio` ya cumplen las reglas vigentes (design D8).

## Ajustes del propose a decisiones.md

- Decisión 4: varios grados como rango contiguo (grado inicial y final); el filtro la encuentra con cualquiera del rango.
- Decisión 2: la ficha pide la institución; editar no cambia el archivo ni la institución.
- Decisión 6: el panel borra solo la referencia, desde su ficha, sin acción masiva.
- Zona `idx_sesion_busqueda`: se conserva; el filtro por rango lo usa (design D2).

## Workflow follow-up

- **(deuda, pasada de docs)** Doc 11, tabla `sesion`: `grado_hasta`, `estado` vacío en la referencia, los `CHECK` nuevos y `compartida` como «en el repositorio». Criterio de US-018: «tipo de permiso» es texto libre.
- **(deuda)** La dirección ve el material de referencia cuando tenga su pantalla de sesiones (bloque 2).
- **(deuda)** Comando de conciliación de archivos huérfanos (ya anotado en US-010/US-011): ahora también por un fallo del panel después de guardar.
- **(equipo)** Push y PR hacia `main` (`Closes #N` de US-018, verificando el número) cuando US-011/012/016 esté fusionada; si no, `git merge main` en la rama. En «Para quien revise»: el panel permite borrar un modelo (D5) y `compartida` cambia de sentido para la referencia (D1).
- **(equipo)** Después de la fusión: Marco carga por el panel las sesiones reales anonimizadas, con su permiso de uso.
- **(verificacion.md, Minor del revisor, parte B)** El escenario «Eliminar» («La sesión ya no está disponible» en la página) se prueba en servicio, no en la vista: cubrirlo en la parte C o anotarlo. Con un POST manipulado (`area` o `grado` fuera de la lista), la ficha muestra el mensaje genérico de Django junto al del servicio. Un `ValidationError` en `save_model` (el área deja de trabajarse entre `clean` y el guardado) da 500: carrera improbable, a la deuda.
