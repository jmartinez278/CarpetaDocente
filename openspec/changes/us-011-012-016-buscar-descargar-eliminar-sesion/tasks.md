# Tasks

## 1. Modelo y catálogo de actividad (D1)

### Parte A: `Sesion`, `SesionVista`, `CHECK` y operaciones nuevas (alto riesgo) (revisor)

- [x] 1.1 Prueba primero, `repositorio/tests/test_modelos.py`: compartida sin fecha → `IntegrityError` de `ck_sesion_terminos`; no compartida con fecha se guarda (escenarios «Coherencia en la base» y «No compartida con fecha»); `texto` y `texto_busqueda` vacíos por defecto; `SesionVista` repetida para la misma sesión y usuario → `IntegrityError`; borrar la sesión borra sus vistas; borrar la cuenta con vistas → `ProtectedError`. Ajustar la prueba que esperaba el rechazo de «no compartida con fecha». Luego D1 y `repositorio/0002` (con `texto_busqueda` rellenado con título y propósito normalizados). Verificar: rojo y luego verde; `makemigrations --check` sin cambios; `sqlmigrate repositorio 0002` muestra el `CHECK` nuevo, `sesion_vista` y el índice
- [x] 1.2 Prueba primero, `actividad/tests/` (el archivo del catálogo): las cinco operaciones están en el catálogo, ninguna en `CUENTAN_KPI_01`; `registrar` acepta `{"compartida"}` en SESION_ELIMINADA y `{"modo", "propia"}` en SESION_DESCARGADA y rechaza `titulo` o `archivo_nombre` en cualquiera; el `CHECK` de la base rechaza una operación fuera del catálogo. Luego las operaciones, `DETALLE_PERMITIDO` y la migración de `actividad`. Verificar: rojo y luego verde; `uv run pytest src/backend/actividad`
- [x] 1.3 Revisión de la parte (agente `revisor`), `verificar.py` y commit

## 2. Texto transcrito (D2, D3, D4)

### Parte B: extracción en el envío y medición en la vista previa (alto riesgo)

- [x] 2.1 Prueba primero, `repositorio/tests/test_texto.py`: .docx con párrafos, tabulaciones y saltos → sus líneas; PDF con capa de texto → su texto; PDF sin texto, PDF cifrado, ZIP roto, `document.xml` con DOCTYPE y `document.xml` que declara más de 8 MB → `""` sin excepción; PDF de 60 páginas → solo las 40 primeras; texto de más de 100 000 caracteres → recortado; `\x00` y caracteres de control fuera; el archivo queda al principio. `normalizar`: «Recomendación», «ÁRBOL» y «niño», y el mismo resultado que `_normalizar` de `repositorio/0002` con título y propósito. Luego `pypdf` en `pyproject.toml` (consultar su documentación con Context7) y `repositorio/texto.py`; ampliar `tests/archivos.py` con un PDF con texto y uno de varias páginas. Verificar: rojo y luego verde
- [x] 2.2 Prueba primero, `repositorio/tests/test_servicios_enviar.py`: escenarios «Word», «PDF con texto», «PDF escaneado» y «Archivo que no se puede leer» (mismo éxito, sin texto); `texto_busqueda` lleva título, propósito y texto normalizados; un reintento con el mismo `id` no extrae otra vez; si `extraer_texto` lanzara, el envío sigue. Luego D3 en `enviar_sesion`, con la duración en el log. Verificar: rojo y luego verde; `test_concurrencia.py` sigue en verde
- [x] 2.3 Prueba primero, `repositorio/tests/test_comando_extraer.py`: escenario «Sesiones anteriores» (llena las de `texto` vacío, no toca las que tienen texto, un archivo que falta no detiene a las demás, segunda corrida sin cambios). Luego el comando `extraer_textos`. Verificar: rojo y luego verde
- [x] 2.4 `verificar.py` y commit
- [x] 2.5 (equipo) Push de la rama con aprobación. Medición D3 en la vista previa: enviar un .docx y un PDF de 4 MB con texto y leer la duración de la extracción en el log; tamaño del paquete en el build. Verificar: las dos sesiones se guardan con texto, la función no corta y la extracción toma menos de 5 s; resultado anotado para `verificacion.md`. **Si falla, se detiene el apply y decide el equipo**
  - Medición en la vista previa (16-11-2026): Word 29 ms (10 024 car.), PDF de unos 4 MB 1215 ms (20 597 car.), los dos con 201 y sin que la función cortara. Función `/django`: 42,8 MB, Python 3.13, tiempo máximo 300 s.

## 3. Lecturas y permisos (D5, D6, D7, D10)

### Parte C: visibilidad, listas, búsqueda, página y entrega del archivo (alto riesgo) (revisor)

- [x] 3.1 Prueba primero, `repositorio/tests/test_servicios_consultas.py`: `sesion_visible` con la matriz de «Quién ve una sesión» (propia compartida o no, ajena compartida, ajena sin compartir, otra institución, inexistente); `mis_sesiones` (escenarios de «Mis sesiones»: orden, grupos «Hoy», «Ayer» y «lun 2 nov» en hora de Lima, solo las suyas, 25 en dos páginas, conteo de vistas); `buscar_repositorio` (escenarios de «Repositorio de la institución», «Búsqueda por palabra» y «Filtros de grado y área»: tildes, mayúsculas, varias palabras, `%` y `_`, 101 caracteres, grado 7 y área ajena ignorados); `conteos_por_area`; ninguna consulta carga `texto` completo (número de consultas acotado). Luego D5. Verificar: rojo y luego verde
- [x] 3.2 Prueba primero, en el mismo archivo y en `test_almacenamiento.py`: `registrar_vista` (escenarios de «Colegas que la vieron» y «Vistas y descargas de sesiones»: primera vez, repetida, autora) y `entregar_archivo` (descargar y ver; ver un Word rechazado; no visible sin entrada; detalle `modo` y `propia`); con un almacén que firma (doble de `S3Storage`), `.url()` recibe la clave, `expire=60` y el nombre original en la disposición. Luego D6 y D7 (confirmar la firma de `.url()` con Context7). Sacar SESION_VISTA y SESION_DESCARGADA de `RESERVADAS` y darles su fila en `actividad/tests/escenarios.py`. Verificar: rojo y luego verde
- [x] 3.3 Prueba primero, `repositorio/tests/test_vistas.py`: «Listas solo del rol Docente» y «Otro rol o sin sesión» en las cinco rutas GET (dirección, Administrador, sin sesión, con `HX-Request`); página 200 con sus datos, migas y sin la clave ni una dirección de R2 («La página no trae enlaces de R2»); no disponible → 404 con el mismo cuerpo en los cuatro casos; descarga local con tipo, nombre con tildes, `no-store` y `nosniff`; descarga con almacén que firma → 302; `<script>` en título y texto sale escapado; fragmento con `HX-Request` y `Vary`; `?pagina=2`; «Una lectura no deja entrada». Luego las vistas y rutas GET de D10. Verificar: rojo y luego verde
- [x] 3.4 Revisión de la parte (agente `revisor`), `verificar.py` y commit
  - Revisor (16-11-2026): sin Critical ni Important. Minor para `verificacion.md`: un archivo que falta en el almacén local da 500 en «Descargar» (sin entrada; no lo provoca la pantalla); `sesion_visible` no mira el rol, lo cuida `DocenteMixin` (la parte D debe ir también detrás de él); `AlmacenQueFirma.llamadas` es de clase y solo la reinicia su fixture.

## 4. Escrituras de la autora y demostración (D8, D11)

### Parte D: eliminar, compartir, dejar de compartir y demo (alto riesgo) (revisor)

- [x] 4.1 Prueba primero, `repositorio/tests/test_servicios_autora.py`: escenarios de «Eliminar una sesión propia», «Solo la autora elimina», «Dejar de compartir», «Compartir después», «El archivo se borra con su sesión» (falla la base → fila y archivo siguen; falla el almacén → sesión eliminada y la clave en el log, sin título) y «Operaciones sobre sesiones»; ajena visible → `SoloLaAutora` e INTENTO_SIN_PERMISO; ajena no visible → `SesionNoDisponible` e INTENTO_SIN_PERMISO; sin cambio → sin entrada; compartir sin aceptar. En `test_concurrencia.py`: dos `eliminar_sesion` a la vez → una entrada y ningún error; eliminar y compartir a la vez → nunca una sesión compartida sin fila. Luego D8; `RESERVADAS` queda vacía y las tres operaciones tienen su fila en `actividad/tests/escenarios.py`. Verificar: rojo y luego verde
- [x] 4.2 Prueba primero, `repositorio/tests/test_vistas.py`: los tres POST con su redirección 303 y su Mensaje («Sesión eliminada» desaparece al recargar), 403 con «Solo el autor puede eliminar esta sesión», 404, 400 de compartir sin aceptar, GET no permitido, y dirección, Administrador y sin sesión sin cambios en la base. Luego las vistas y rutas POST. Verificar: rojo y luego verde
- [x] 4.3 Prueba primero, `institucion/tests/` (el archivo de la demo): escenarios de «Sesiones de ejemplo» (PDF y Word que pasan `validar_archivo`, con texto buscable, un PDF sin texto, una sin compartir, sin SESION_ENVIADA, recarga sin duplicados ni archivos de más) y de «Sesiones al quitar la demostración» (sesiones y archivos demo fuera, la enviada a mano también, vistas demo fuera, sesiones reales intactas, `sesiones` en el resumen). Luego D11. Verificar: rojo y luego verde; `uv run pytest src/backend/institucion`
- [x] 4.4 Revisión de la parte (agente `revisor`), `verificar.py` y commit
  - Revisor (16-11-2026): sin Critical ni Important. Minor para `verificacion.md`: «Falla el almacenamiento al borrar» solo tiene prueba de servicio, no de vista; `compartir_sesion` revisa la aceptación antes que «ya compartida» (un POST sin aceptar sobre una compartida da 400, no «sin cambio»; la pantalla no lo provoca). El tercero (resumen de DEMO_QUITADA contado antes de borrar) se corrigió: cuenta las que borró.

## 5. Pantallas (normal)

- [ ] 5.1 Prueba primero, `cuentas/tests/test_dimensiones.py` y `test_pantallas.py`: escenarios «Sesiones con o sin sección», «Abrir el ☰», «Destino no disponible» y «Ubicación actual en Sesiones»; ajustar los que esperaban «Próximamente». Luego la bandera en `cuentas/dimensiones.py` (`sesiones:inicio`). Verificar: rojo y luego verde; `uv run pytest src/backend/cuentas`
- [ ] 5.2 Prueba primero, `repositorio/tests/test_plantillas.py`: cabecera sin subtítulo, botón con nombre accesible «Subir una sesión», `tablist` con sus contadores y la pestaña actual; tarjeta (un solo enlace «Abrir …», página dibujada con `aria-hidden`, etiqueta PDF o Word, variante sin texto, chips, «La vieron N colegas» y «La vio 1 colega», nada con 0); título de resultados en singular y plural; grupo «Filtros activos» solo con filtros; área de 0 deshabilitada; estados «Sin envíos», «Repositorio vacío» y «Sin coincidencias»; página de la sesión (escenarios de «Página de la sesión» y «Tarjeta "Tu sesión"», «Ver» solo en PDF, diálogo de eliminar y términos con «Acepto y comparto»); ninguna plantilla con `style=` ni hex. Ajustar las pruebas de la cabecera anterior. Luego las plantillas de `templates/repositorio/`, los íconos Lucide que falten y el CSS en `src/frontend/`. Verificar: rojo y luego verde
- [ ] 5.3 Prueba primero, `repositorio/tests/test_repositorio_e2e.py` (360 px): (1) buscar una palabra del texto, filtrar por grado y área, ver «Sin coincidencias», «Borrar filtros» y abrir una sesión; (2) pestañas con las flechas, foco en la pestaña y «atrás»; (3) el buscador conserva el foco y lo escrito mientras la lista cambia, y el total se anuncia; (4) panel «Filtrar»: abre con foco dentro, aplica al tocar, Esc lo cierra, foco de vuelta y contador; (5) tras enviar una sesión la lista y el contador se actualizan; (6) sin desplazamiento horizontal, con un título de 200 caracteres, y axe en «Mis sesiones», «Repositorio» y el panel abierto, en claro y oscuro. Luego el JS (`static/js/`) y los atributos de HTMX de D10. Verificar: e2e de ese archivo en verde
- [ ] 5.4 Prueba primero, `repositorio/tests/test_detalle_e2e.py` (360 px): (7) eliminar: el diálogo abre con el foco en «Cancelar», cancelar devuelve el foco a «Eliminar», confirmar lleva a «Mis sesiones» con «Sesión eliminada»; (8) «Compartir» abre los términos, «Volver» devuelve el foco, «Acepto y comparto» deja el chip, y «Dejar de compartir» lo quita; (9) sin desplazamiento horizontal, con una línea de 300 caracteres, y axe en la página propia, el diálogo de eliminar y los términos, en claro y oscuro. Luego lo que falte de JS y CSS, el retiro y la reducción de la lista «e2e a retirar» (con sus pruebas de vista en `test_vistas.py`), y las filas de las rutas nuevas en el Catálogo de rutas de `docs/03`. Verificar: e2e de ese archivo y `test_sesiones_e2e.py` en verde
- [ ] 5.5 Pantallas vistas en claro/oscuro y celular/escritorio (las marca Marco). `verificar.py` y commit
- [ ] 5.6 (equipo) En la vista previa: «Descarga en Vercel» (nombre original con tildes), «Ver» en pestaña nueva y «Enlace vencido» a los 60 s. Verificar: resultado anotado para `verificacion.md`; si R2 no respeta el nombre o el modo, se aplica la alternativa de D7 con su prueba

## 6. Cierre

### Parte E: A2 y verificación

- [ ] 6.1 Con la A2 que corre el usuario (`/codex:adversarial-review --base main --background`, con foco en los specs del cambio y en la parte B), corregir los Critical e Important, con la prueba primero. Verificar: `uv run python scripts/verificar.py --completo` y `-m e2e` completo en verde; la vista previa aplica las dos migraciones en Neon
- [ ] 6.2 `verificacion.md`: DoD 1 a 9, las mediciones de 2.5 y 5.6, los escenarios sin prueba con su motivo y los Minor. Verificar: el archivo existe y cada escenario sin prueba tiene motivo; commit

## e2e a retirar (aprobado por Marco el 15-11-2026; se hace en la tarea 5.4)

De `repositorio/tests/test_sesiones_e2e.py`, por las reglas vigentes de e2e:

- `test_los_estados_del_boceto_son_accesibles_y_sin_desplazamiento`: matriz de estados × temas × anchos → reducir a 360 px, ambos temas, estado principal y cada diálogo abierto.
- `test_en_la_pc_el_popup_es_una_ventana_centrada_de_480_px_o_menos`, `test_en_el_celular_el_popup_es_una_hoja_abajo_a_todo_el_ancho`, `test_con_el_teclado_el_popup_abre_y_cierra_sin_transicion`, `test_con_movimiento_reducido_el_popup_no_se_desplaza` y `test_a04_al_cerrar_con_el_mouse_el_popup_sale_en_columna`: valores de CSS.
- `test_las_areas_son_las_que_trabaja_la_institucion_en_orden_siagie` y `test_el_grado_viene_con_el_de_su_seccion`: los cubre una prueba de vista.

## Ajustes del propose a decisiones.md

- Decisión 7: varias palabras se buscan todas (Y); un grado y un área a la vez.
- Decisión 8: texto hasta 100 000 caracteres y 40 páginas de PDF; las ya enviadas, con el comando `extraer_textos`.
- Decisión 9: la página es `/docente/sesiones/<id>/`.
- Decisión 12: una ajena visible responde «Solo el autor puede eliminar esta sesión»; una no visible, «La sesión ya no está disponible».
- Decisión 13: volver a compartir pide aceptar otra vez y guarda la fecha nueva; el botón de los términos dice «Acepto y comparto».
- Decisión 14: se cuenta la primera vez que cada colega abre la página; «Ver» cuenta como descarga en el registro.
- Decisión 15: SESION_VISTA, SESION_DESCARGADA, SESION_COMPARTIDA, SESION_DESCOMPARTIDA y SESION_ELIMINADA.
- Zona KPI-01: no se resta (design D9).

## Workflow follow-up

- **(equipo)** Push y PR hacia `main` (`Closes #N` de US-011, US-012 y US-016, verificando los números). En «Para quien revise»: la extracción corre dentro del envío (medición 2.5); las descargas van por enlace firmado de 60 s (5.6); abrir y descargar escriben en `GET`; eliminar borra la fila y luego el archivo.
- **(equipo)** Después de la fusión: `uv run python src/backend/manage.py extraer_textos` contra producción, una vez.
- **(equipo)** Aprobación del PR por otra integrante (DoD 3).
- T-04 (botón de tema): su propio cambio OpenSpec en esta rama, después de este.
- Deuda para la descripción del PR:
  - contradicciones para la pasada de docs: RF-015 (retirado) frente a «Dejar de compartir»; RF-016 y US-016 («la retira del repositorio») frente a eliminar para todos; RF-011 y RF-012 incluyen a la dirección; doc 11, tabla `sesion` (`texto`, `texto_busqueda`, `sesion_vista`, `CHECK`, sin `pg_trgm`); DESIGN.md («sin tarjeta café en Sesión») frente a «Tu sesión» → las de la tesis, también a `docs/PENDIENTES_TESIS.md`, junto con «sesiones cargadas» neto de eliminadas (D9);
  - bandeja, visto bueno, búsqueda y descarga de la dirección, y bloqueo de Eliminar tras el visto bueno → bloque 2; guardadas → historia futura; adaptada, entregada y repositorio inicial → US-013, US-017, US-018;
  - índice `pg_trgm` sobre `texto_busqueda` si la búsqueda se vuelve lenta; comando de conciliación de objetos huérfanos de R2; «Ver más» puede repetir una tarjeta si llega una sesión nueva entre páginas;
  - lector de pantalla y panel de filtros en un Android físico → pulido final.
- Después de la fusión: `/opsx:archive` con «Sync now», como primer commit de la rama siguiente.
