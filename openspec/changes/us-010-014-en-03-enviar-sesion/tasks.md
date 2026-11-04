# Tasks

## 1. Almacenamiento y modelo (D1, D2)

### Parte A: `STORAGES`, `Sesion` y su migración (alto riesgo)

- [x] 1.1 Prueba primero, `config/tests/test_settings.py` y `repositorio/tests/test_almacenamiento.py`: con `VERCEL=1` y sin cada una de las cuatro variables `AWS_*` → `ImproperlyConfigured` que nombra la variable y no muestra valores; con las cuatro (claves de prueba), `STORAGES["sesiones"]` es `S3Storage` con el endpoint, `region_name="auto"`, sin ACL y con firma; fuera de Vercel sin variables, `FileSystemStorage` en `media/`; en la suite, `InMemoryStorage` (escenario «Pruebas»); `check --deploy` con las variables de Vercel y R2 sigue sin advertencias; las pruebas de Vercel que ya existen reciben las variables de prueba. Luego `uv add "django-storages[s3]"`, D2 en `settings.py` (con Context7 para django-storages y R2) y el fixture en `src/backend/conftest.py`. Verificar: rojo y luego verde; `uv run pytest src/backend/config src/backend/repositorio`
- [x] 1.2 Prueba primero, `repositorio/tests/test_modelos.py`: grado 0 y 7, origen y estado fuera de su lista, `tipo_mime` de .doc, tamaño 0 y 4 194 305, título vacío, compartida sin fecha y no compartida con fecha → `IntegrityError` con el nombre de su `CHECK`; 4 194 304 bytes se guarda; `archivo_clave` repetida → `uq`; borrar la autora, el área o la institución con sesiones → `ProtectedError`; `db_table` es `sesion`. Luego `Sesion` (D1) y `repositorio/0001`. Verificar: rojo y luego verde; `makemigrations --check` sin cambios; `sqlmigrate repositorio 0001` muestra los siete `CHECK`, la UQ, los dos índices y las FK con su `ON DELETE`
- [x] 1.3 Revisión de la parte (agente `revisor`) y commit

## 2. Reglas del envío (D4 a D6, D10)

### Parte B: validación, envío todo o nada, actividad e indicadores (alto riesgo)

- [x] 2.1 Prueba primero, `repositorio/tests/test_validar_archivo.py`: PDF real y DOCX real pasan con su `tipo_mime`; un .exe llamado `sesion.pdf`, un DOCX llamado `.pdf`, un ZIP sin `word/document.xml`, un .docm renombrado a .docx, un .doc, un archivo vacío y uno de 4 194 305 bytes → su mensaje (escenarios «Tipo no permitido», «Archivo de más de 4 MB», «Justo 4 MB» y «Envío que salta el navegador»); `[Content_Types].xml` de más de 64 KB no se lee entero; nombre con ruta y de 300 caracteres → nombre limpio de 255 con su extensión. Luego D6. Verificar: rojo y luego verde
- [x] 2.2 Prueba primero, `repositorio/tests/test_servicios_enviar.py`: escenarios de «Sesión guardada», «Enviar sin compartir», «Aceptar y enviar» (fecha guardada), «Compartir sin aceptar», «Datos que faltan» (grado, área, título, área que la institución no trabaja, grado 7, título de 201, propósito de 1001), «Clave de un PDF», «Falla el almacenamiento» y «Falla la base después del archivo» (sin sesión, sin entrada y sin archivo); envío repetido con el mismo `id` → el mismo resultado, una sesión, un archivo y una entrada; `id` de otra autora o mal formado → error general sin escribir; `datos_del_formulario` (una sección → grado y «2.º A»; varias o ninguna → sin grado; áreas `se_trabaja` en orden SIAGIE). Luego D4, D5, el resto de D6 y SESION_ENVIADA (D10) con `actividad/0005` y la prueba del catálogo de `actividad` (escenarios de «Envío de sesiones»). Verificar: rojo y luego verde; `uv run pytest src/backend/repositorio src/backend/actividad`
- [x] 2.3 Prueba primero, `repositorio/tests/test_concurrencia.py` (`transaction=True`): dos `enviar_sesion` con el mismo `id` en dos hilos → una sesión, un archivo, una entrada y los dos con el mismo éxito, nunca un `IntegrityError`. Verificar: rojo (sin el manejo de la PK) y luego verde
- [x] 2.4 Prueba primero, `actividad/tests/test_indicadores.py`: escenarios «Sesiones cargadas», «Semana sin sesiones» y «Sesiones de la demostración»; «Columnas aún sin datos» pasa a esperar números, sin «—». Luego `sesiones` en `indicadores_por_semana` (D10). Verificar: rojo y luego verde; `uv run pytest src/backend/actividad`
- [x] 2.5 Revisión de la parte (agente `revisor`) y commit

## 3. Rutas y acceso (D7, D3)

### Parte C: vistas, rutas, permisos y medición en la vista previa (alto riesgo)

- [x] 3.1 Prueba primero, `repositorio/tests/test_vistas.py`: escenarios de «Solo el rol Docente» (GET y POST: docente con y sin sección, dirección, Administrador y sin sesión; con `HX-Request` → `HX-Redirect`; nada guardado en los de error); «Primera visita» (cabecera, botón, estado vacío, sin lista, áreas y grado en el contexto); POST 201 con el fragmento y su resumen («PDF · 1,2 MB» con `filesizeformat`), 400 con `{"errores": …}` sin el texto de una excepción, 201 repetido con el mismo `id`; «Portada sin cambio» sigue en verde (`cuentas/tests/test_dimensiones.py`). Luego `SesionesView`, `EnviarSesionView`, `repositorio/urls.py`, su `include` y una plantilla mínima. Verificar: rojo y luego verde; `uv run pytest src/backend/repositorio src/backend/cuentas`
- [x] 3.2 Revisión de la parte (agente `revisor`) y commit
- [ ] 3.3 (equipo) Bucket privado de R2 y las cuatro variables en Vercel (Preview); push de la rama con aprobación. Medición D3: PDF de 4 194 304 bytes con la subida limitada a Slow 4G contra la vista previa; escenarios «4 MB con Slow 4G en la vista previa» y «Archivo no público»; tamaño del paquete en el log del build. Verificar: la sesión y el objeto existen, la función no cortó; resultado anotado para `verificacion.md`. **Si falla, se detiene el apply y decide el equipo**

## 4. Pantalla (normal)

- [ ] 4.1 Prueba primero, `repositorio/tests/test_plantillas.py`: la pantalla dibuja la cabecera con franjas de Sesiones, «Subir una sesión», el estado vacío, el `<noscript>`, los dos `<dialog>` con sus títulos y descripciones, los campos con sus ayudas y regiones de error asociadas (`aria-describedby`), la casilla desmarcada con su ayuda, los términos literales del doc 09 §4, el `<progress>` y la región `aria-live`, y el `id` oculto; «Grado por defecto» (una sección, varias, ninguna); el fragmento de éxito dice «Sesión enviada a la dirección» o «… y compartida en el repositorio». Luego las plantillas de D9 y las clases en `src/frontend/css/app.css`. Verificar: rojo y luego verde
- [ ] 4.2 Prueba primero, `repositorio/tests/test_sesiones_e2e.py`: escenarios de «Popup "Subir una sesión"» (abrir, tocar afuera, Cancelar con foco de vuelta y formulario nuevo, orden de botones a 360 y 1280 px), «Campos del formulario», «Datos que faltan» (foco al primer error), «Tipo no permitido» y «Archivo de más de 4 MB» en el navegador, «Enviar sin compartir», «Aceptar y enviar», «Volver», «Datos incompletos con la casilla marcada», «Éxito sin compartir» (anuncio y foco), «Éxito compartida», «Subir otra» y «Recargar después del éxito». Luego `static/js/sesiones.js` (D5, D7, D8). Verificar: e2e de `repositorio` en verde con el CSS compilado y `DJANGO_ALLOW_ASYNC_UNSAFE=true`
- [ ] 4.3 Prueba primero, en el mismo archivo e2e: «Atrás en el formulario», «Atrás en los términos» (campos, casilla y archivo intactos), «Atrás mientras sube», «Subiendo» (barra, campos, Enviar y Cancelar bloqueados, Esc no cierra; subida retenida con `page.route`), «Recargar mientras sube» (`beforeunload`), «Se corta y reintenta» (`page.route` que aborta una vez; «Reintentar envío»; una sola sesión) y «Se guardó pero no llegó la respuesta» (respuesta abortada después de guardar; el reintento da el mismo éxito y una sola sesión). Luego lo que falte en `sesiones.js`. Verificar: e2e de `repositorio` en verde
- [ ] 4.4 Prueba primero, en el mismo archivo e2e: escenarios de «Pantalla accesible y sin desplazamiento horizontal» (axe en los estados 1, 2, 3, 4a, 5, 6a, 6b, 7, 8, 9 y 10, en claro y oscuro, a 360 y 1280 px; objetivos de 44 px; «Pantalla baja» con los términos a 360 × 560) y la carga de Sesiones con Slow 4G. Luego los ajustes de CSS que falten y las filas de las dos rutas en el Catálogo de rutas de `docs/03`. Verificar: e2e de `repositorio` en verde
- [ ] 4.5 Pantalla vista en claro/oscuro y celular/escritorio (la marca Marco). `verificar.py` y commit

## 5. Cierre

- [ ] 5.1 Con la A2 que corre el usuario (`/codex:adversarial-review --base main --background`, con foco en los specs del cambio, D4, D5, D6 y D8), corregir los Critical e Important, con la prueba primero. Verificar: `uv run pytest --cov` (80 % o más), las e2e y `verificar.py --antes-del-commit` en verde; la vista previa aplica `repositorio/0001` y `actividad/0005` en Neon y envía una sesión de punta a punta
- [ ] 5.2 `verificacion.md`: tabla escenario → prueba de los cuatro specs del cambio, la medición de D3 y la DoD 1 a 9. Verificar: cada escenario tiene su prueba o una nota de por qué no aplica; commit

## Ajustes del propose a decisiones.md

- Decisión 4: Esc también cierra el popup (como «Cancelar»), salvo mientras sube; en los términos, Esc es «Volver».
- Decisión 5: título hasta 200 caracteres (doc 11) y propósito hasta 1000 (nuevo).
- Decisión 6: la extensión y el contenido deben coincidir; un .docm renombrado se rechaza.
- Decisión 7: la clave es `sesiones/<UUID>.pdf` o `.docx`.
- Decisión 9: el reintento no duplica la sesión (UUID del navegador, design D5).
- Decisión 11: la dirección y el Administrador que abren la ruta van a su inicio, sin registro de intento (no es una ruta de sección).

## Workflow follow-up

- **(equipo)** Antes de la parte C: bucket privado de R2 y variables `AWS_*` en Vercel (Preview y Production); sin ellas el despliegue no arranca.
- **(equipo)** Push de `feature/us-010-014-en-03-enviar-sesion` y PR hacia `main` (`Closes #N` de US-010, US-014 y EN-03, verificando los números), con las verificaciones de EN-08 en verde y la vista previa aplicando las migraciones. La tarjeta Sesiones sigue en «Próximamente»: la pantalla se revisa escribiendo `/docente/sesiones/` en la vista previa. En «Para quien revise»: el archivo pasa por la función de Vercel (medición D3); el envío es idempotente por el UUID del navegador (D5); el término 3 es una declaración que el sistema no verifica. En «## Deuda»:
  - contradicciones para la pasada de docs: decisión 1 frente a doc 06 §1, RF-010, RF-014, RF-015 y RF-017, doc 08 §3.1, RN-019 y los criterios de US-010 y US-014 («Sesión publicada», «debe aceptar»); doc 11, tabla `sesion` (`estado`, `compartida`, `terminos_aceptados_en` opcional, sin `application/msword`, 4 MB, PROTECT); 4 MB frente a 10 MB en RN-021, RNF-004, docs 10, 11 y 12 y los escenarios de EN-03; EN-03 pedía enlace firmado de subida (decisión 7) → también a `docs/PENDIENTES_TESIS.md`;
  - bandeja de la dirección, visto bueno, observaciones, estado que ve la docente, lista de Sesiones, tarjeta de la portada, unidad de aprendizaje y panel de sesiones → bloque 2 (preguntas a Nayely); compartir después → bloque 2 o 3; buscar, descargar, vista previa, eliminar y enlaces firmados de descarga → US-011, US-012, US-016; competencias de la sesión → después del Sprint 3; adaptada, entregada y de referencia → US-013, US-017, US-018;
  - sesiones y archivos de cuentas demo al quitar la demostración → bloque 3, con eliminar;
  - P2 y P3 del boceto (`notas.md`): lector de pantalla y gesto «atrás» en un Android físico; compartir bajo el pliegue tras el error de red; vacío redundante junto al éxito → pulido final.
- **(equipo)** Aprobación del PR por otra integrante (DoD 3).
- Después de la fusión: `/opsx:archive` con «Sync now». La siguiente historia sale de `main` y su primer commit es este archivo.
