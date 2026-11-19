# Design: US-024 + US-025 – Completar la plantilla de notas del SIAGIE

## Context

- Decisiones cerradas en `insumos/US-024/decisiones.md` (1 a 13) y bocetos aprobados en `C:\Proyectos\prototipos-cd\US-024\` (sección A, resumen B). Lo nuevo de este propose está en `proposal.md`.
- La muestra es `insumos/RegNotas_SIAGIE.xlsx` (vaciada, fuera del repo): hojas `Generalidades`, `Parametros` (oculta) y una por área con nombre `<código>-<abreviatura>` (`0001-ART Y CULT`, `031-EFIS`, `063-MATE`, `0006-DESEN TIC`…). En cada hoja de área: fila 1 «ID», «Cód. Estudiante», «Nombres» y el número de competencia («01», «02»…) sobre dos columnas combinadas; fila 2 «NL» y «Conclusión descriptiva de la competencia»; estudiantes desde la fila 3; leyenda desde la fila 18. Validaciones: lista `"A,AD,B,C"` en NL y longitud de 10 a 500 en la conclusión. `Parametros`: B1 código modular («0370031», texto), B2 anexo (0), B4 año, B6 periodo («B3») y C6 su texto, C7 el grado en texto («SEGUNDO», B7 = «05» no se usa), B8 y C8 código y nombre de la sección («01», «TRIUNFADORES»).
- Prueba de ida y vuelta con openpyxl sobre la muestra (en el scratchpad, sin datos al repo): abre en 0,3 s y guarda en 0,6 s; conserva las validaciones, la hoja oculta, las celdas combinadas y las fórmulas (incluso las que apuntan a un libro externo roto, `'[2]0004-CIENC TEC'!F3`); pierde solo partes vacías (13 `drawings` sin contenido y una lista de personas vacía) y agrega `docProps`. El archivo pasa de 218 KB a 176 KB.
- `Institucion` tiene `codigo_modular` (nulo, único) y no tiene anexo. `Seccion` tiene `grado` (1 a 6) y `nombre`, únicas por año. `Area.codigo_siagie` ya es el código del nombre de la hoja (EN-06). La hoja de notas numera las competencias como C1, C2… por su posición entre las activas del área (`notas.servicios._columnas`).
- `notas_faltantes(usuario, seccion, periodo, area_institucion)` devuelve vacío si `usuario` no marca el área (docente de curso o no es la docente de la sección).
- `exportaciones` existe vacía y está en `INSTALLED_APPS`. `direccion` tiene solo el inicio (`RolRequeridoMixin`, rol DIRECCION).
- La subida de US-010 (`static/js/sesiones.js`) usa `XMLHttpRequest` por el avance: 2xx pinta un fragmento, 400 pinta los errores del JSON.

## Riesgos y zonas delicadas (primero)

- **[El SIAGIE rechaza el archivo]** (zona de cuidado) → D8 y D9: solo se escriben valores en celdas que ya existen; no se crean hojas, estilos ni validaciones; se conserva el nombre del archivo. La aceptación real solo se confirma cargando una plantilla llena: antes del piloto, abrirla en Excel y LibreOffice (RNF-006) y que la dirección la cargue una vez (Workflow follow-up). Una prueba de ida y vuelta fija lo que openpyxl conserva.
- **[Datos de menores]** (RN-015, Ley 29733, zona de cuidado) → D3, D4 y D11: el archivo vive solo en la memoria de la petición; ni se guarda ni se registra. Los nombres de «No encontrados» van solo en la respuesta. Ningún `logger` ni mensaje de excepción lleva celdas del libro. Las pruebas generan plantillas ficticias (D12); la muestra de `insumos/` nunca entra al repo.
- **[Archivo hostil]** → D9: un .xlsx es un zip con XML. Límite de 3 MB (para que la respuesta en base64 quepa en Vercel), límite del tamaño descomprimido y de la cantidad de partes antes de abrirlo, `defusedxml` (la documentación de openpyxl lo pide para *billion laughs* y *quadratic blowup*), sin macros. Cualquier fallo al abrir da el mensaje de D3, nunca un 500.
- **[Escribir la nota de otro estudiante o de otra sección]** (notas) → D5 a D7: la sección sale de la institución de la dirección y del año y grado de la plantilla; las notas, de una consulta filtrada por esa sección y ese periodo; los nombres se cruzan exactos tras normalizar, sin parecidos, y un homónimo no se toca.
- **[Equivalencia mal elegida]** → D5 y D13: queda guardada y dirige las siguientes plantillas. La señal visible es el resumen (sección de la I.E. y muchos «no encontrados»); «¿No es esta sección?» la borra y oculta la descarga del archivo equivocado. La alerta automática por muchos «no encontrados» queda en la deuda.
- **[Permisos de la primera pantalla de la dirección]** (zona de cuidado) → D1: la vista usa `RolRequeridoMixin` con DIRECCION y toma la institución del usuario, nunca de la petición. Pruebas de la matriz para la ruta nueva.
- **[RNF-003: 5 s con Slow 4G, subida incluida]** (zona de cuidado) → D4: subir 220 KB a ~750 kb/s son ~2,4 s; procesar, ~1 s; bajar el resumen con el archivo en base64 (~240 KB) a ~1,6 Mb/s, ~1,2 s. Ajustado: se mide en la vista previa de Vercel antes de la parte D. Si no alcanza, el plan B es devolver el archivo sin base64 y el resumen en cabeceras (D4, alternativa).
- **[Trimestres]** (zona de cuidado) → D2: la letra del periodo en trimestres no se conoce; con organización TRIMESTRE se rechaza la plantilla. Deuda hasta confirmarlo.

## Goals / Non-Goals

**Goals:**
- Reglas y escrituras en `exportaciones/servicios.py`; el acceso al libro en `exportaciones/siagie.py`, sin base de datos; la vista solo lee la petición y llama al servicio.
- Ningún archivo ni nombre de la plantilla persiste.
- Una sola lectura de las notas de la sección y el periodo, sin consultas por celda.

**Non-Goals:**
- Hoja propia de la docente; varias plantillas a la vez; trimestres; estado de entrega.
- Validar las notas contra las reglas del SIAGIE más allá de lo que ya exige CarpetaDocente (RN-001, RN-002).
- Leer el código de grado («05») o el número final del nombre del archivo (sin confirmar).

## Decisions

### D1. Módulo, ruta y permisos
- `exportaciones/siagie.py`: abrir el libro, leer `Parametros`, recorrer las hojas de área (código, columnas por número, filas con su nombre) y escribir celdas. No importa modelos.
- `exportaciones/servicios.py`: `completar_plantilla(usuario, archivo, seccion_id=None)` reconoce, resuelve la sección, cruza, llena, cuenta y registra; devuelve un resultado (`Resumen` con conteos, nombres, sección, periodo y bytes) o lanza `PlantillaNoReconocida`, `SinSeccionesDelGrado`, `EligeSeccion` (con las opciones), `SeccionNoValida` o `SinNotasEnElPeriodo`.
- Ruta `POST /direccion/plantilla-siagie/` (`exportaciones/urls.py`, namespace `plantilla_siagie`, incluida desde `config/urls.py` antes de `direccion/`). Vista con `RolRequeridoMixin` y `rol_requerido = DIRECCION`; GET responde 405. La institución es `request.user.institucion`.
- *Alternativa descartada:* la vista en `direccion` (decisión 12 pone el llenado en `exportaciones`; `direccion` queda para los consolidados).

### D2. Reconocer la plantilla
- `Parametros` debe existir; se leen B1, B2, B4, B6, C7, B8 y C8, y se comprueba que las etiquetas de la columna A digan «Código Modular», «Anexo», «Año Académico», «Periodo», «Grado» y «Sección» (normalizadas), para no aceptar un libro con otra forma.
- Código modular: texto sin espacios; si llega como número, se completa a 7 dígitos con ceros. Debe ser igual al `codigo_modular` de la institución (nulo → no se reconoce). Anexo: entero igual a `Institucion.anexo`.
- `Institucion.anexo`: `PositiveSmallIntegerField`, 0 por defecto con `db_default=0` (el despliegue anterior inserta sin la columna mientras Vercel migra, como en US-029), `CHECK 0 <= anexo <= 9`; en el panel de la institución, junto al código modular (INSTITUCION_EDITADA ya registra los campos).
- Año: `AnioEscolar(institucion, anio)` existente, abierto o cerrado. Periodo: `^B([1-4])$` con organización BIMESTRE → `Periodo(anio_escolar, numero)` existente; TRIMESTRE o nula → no se reconoce.
- Grado: PRIMERO… SEXTO → 1… 6.
- Hojas: toda hoja que no es `Generalidades` ni `Parametros` debe llamarse `^(\d{3,4})-` con un código de `Area`; cada número de la fila 1 debe tener «NL» debajo y su columna siguiente; el número debe existir en el área (D6). Si una sola hoja falla, se rechaza todo el libro.

### D3. Dos pasos sin guardar el archivo
- Primer envío: `archivo`. Si la sección se resuelve (D5), se completa. Si no, la respuesta es el paso «Elige la sección» con las opciones.
- Segundo envío: el mismo `archivo` (el navegador conserva el `File` del campo) más `seccion`. El servidor vuelve a reconocer todo desde cero: no confía en nada del primer paso.
- Las secciones ofrecidas son las del grado y año de la plantilla sin otra equivalencia. Una `seccion` fuera de esa lista → `SeccionNoValida`.
- *Alternativas descartadas:* guardar el archivo en la sesión, la caché o R2 entre pasos (contradice la decisión 2); pedir la sección antes de subir (la dirección no sabe qué nombre trae la plantilla).

### D4. Respuesta y descarga
- 200 con un fragmento HTML cuyo elemento raíz lleva `data-paso="seccion"` o `data-paso="resumen"`; 400 con JSON `{"error": "...", "ayuda_siagie": true|false}` para los rechazos, la sección no válida y el periodo sin notas (en ese caso sin ayuda del SIAGIE).
- El resumen lleva el archivo en base64 en `data-archivo` del enlace «Descargar plantilla» y el nombre original en `download` (solo el nombre base, sin rutas). `plantilla-siagie.js` lo convierte en un `Blob` con el tipo de .xlsx y un `URL.createObjectURL`.
- El resumen reemplaza el contenido de `<main>` sin cambiar la URL; recargar pide `/direccion/` y muestra el inicio. «Inicio de dirección» es un enlace a `/direccion/`.
- *Alternativas descartadas:* `data:` en el `href` (los navegadores limitan su tamaño y Safari lo maneja peor); responder el .xlsx con los conteos en cabeceras (plan B si RNF-003 no alcanza: los nombres de «No encontrados» no caben bien en cabeceras); una segunda petición para descargar (obliga a guardar el archivo).

### D5. Sección y equivalencia
- Modelo `EquivalenciaSeccion` (`exportaciones`, tabla `equivalencia_seccion`): `seccion` `OneToOneField` (CASCADE), `anio_escolar` FK (CASCADE), `grado`, `codigo_siagie` (`CharField(4)`), `nombre_siagie` (`CharField(60)`, normalizado), `creado_por` FK (SET_NULL), `creado_en`. `UniqueConstraint(anio_escolar, grado, codigo_siagie, nombre_siagie)`. El servicio comprueba que la sección sea de ese año y grado.
- Orden: 1) equivalencia guardada; 2) una sola sección del grado cuyo nombre normalizado es el de la plantilla; 3) elegir. Sin secciones del grado → `SinSeccionesDelGrado`.
- Guardar la equivalencia, comprobar que hay notas, medir la completada (D9) y registrar van en un `transaction.atomic()`: sin notas, o si la completada no cabe en la respuesta, no queda la equivalencia. Una carrera (dos sesiones guardan a la vez) da `IntegrityError` dentro de un *savepoint*: si la existente apunta a la misma sección se sigue; si no, `SeccionNoValida`.
- Admin de solo lectura (sin agregar, cambiar ni borrar), para ver qué está guardado.

### D6. Competencias por número
- El número «0n» de la fila 1 es la n-ésima competencia activa del área por `(orden, pk)`: la misma regla que da C1, C2… en la hoja de notas. Un número mayor que las activas → no se reconoce.
- *Alternativa descartada:* `Competencia.orden == n` (el panel puede intercambiar órdenes y no son únicos).

### D7. Cruce de estudiantes
- `clave_nombre(texto)`: NFKD, sin marcas diacríticas, mayúsculas, espacios colapsados, sin espacios junto a la coma. La plantilla «APELLIDOS, NOMBRES» se parte en la primera coma; sin coma, se compara contra «APELLIDOS NOMBRES».
- Índice de los estudiantes de la sección (todos los estados) por clave; una clave con dos estudiantes es ambigua y su fila va a «No encontrados».
- Filas: desde la 3 mientras «Nombres» tenga texto (máximo 60). «Encontrados» = estudiantes distintos cruzados en alguna hoja; «No encontrados» = nombres distintos sin cruce, en el orden en que aparecen, como vienen en la plantilla.

### D8. Escritura y conteos
- Una consulta: `Calificacion` de la sección y el periodo → `{(estudiante_id, competencia_id): (nivel, conclusión)}`.
- Por fila encontrada y competencia de la hoja: si hay nota, NL = nivel y conclusión = texto, o vacía (`None`) con AD o A; si no, nada.
- Reemplazada: celda que tenía un valor no vacío distinto del nuevo (una fórmula cuenta). Una celda que ya tenía el mismo valor no cuenta.
- Faltantes: suma de `notas_faltantes(seccion.docente, seccion, periodo, ia)` sobre las `InstitucionArea` que se trabajan (decisión 8 y US-022). Sin docente de aula, 0 (y sin notas, D13 ya corta antes).
- Sin ninguna `Calificacion` de la sección en el periodo → `SinNotasEnElPeriodo`, antes de escribir.
- Observaciones (título): no encontrados > 0 o faltantes > 0.

### D9. Seguridad y límites del archivo
- De 1 byte a 3 145 728 bytes (3 MB): el libro vuelve en base64 (×4/3, ~4,2 MB) y una respuesta de Vercel admite 4,5 MB (hallazgo de Codex, parte D). La completada tiene el mismo tope: se mide dentro del `atomic()` de D5, antes de registrar, y si lo pasa → `CompletadaDemasiadoGrande` (400, sin ayuda del SIAGIE) sin equivalencia ni entrada; `zipfile.is_zipfile`; suma de `file_size` de las partes ≤ 40 MB y ≤ 300 partes; tipo de contenido del libro .xlsx (no `macroEnabled`).
- `load_workbook(..., data_only=False, keep_vba=False)`; `defusedxml` instalado (openpyxl lo usa solo). Cualquier excepción al abrir o leer → `PlantillaNoReconocida`, sin registrar su texto.
- `openpyxl` y `defusedxml` en `pyproject.toml` (Context7 para la API de openpyxl en la parte B).

### D10. Pantalla
- Inicio de la dirección: bloque «Plantilla de notas del SIAGIE» encima de «Consolidados», marcado del boceto `index.html`, con el diálogo en la misma plantilla (sin carga extra).
- Diálogo: el de US-010 (`dialog--hoja`, campo de archivo, pie con avance y acciones); el paso «Elige la sección» reemplaza el cuerpo y el pie del mismo `<dialog>`, con radios (boceto `seccion-a.html`) y «Guardar y completar».
- Resumen: boceto `resumen-b.html` / `resumen-b-limpio.html`, con «estudiantes encontrados» en vez de «completados» (decisión 9).
- `static/js/plantilla-siagie.js`: abre y cierra el diálogo, bloquea mientras procesa, envía con `XMLHttpRequest` (avance de subida), pinta el paso o el resumen, mueve el foco (título del paso, mensaje de error, `h1` del resumen), crea el `Blob` y maneja el corte de red. Sin Alpine: sigue el patrón de `sesiones.js`.
- El botón de tema del boceto es de T-04; el doble borde rojo y la ruta repetida de `error.html` van al pulido.

### D11. Actividad
- `Operacion.PLANTILLA_SIAGIE_COMPLETADA`, fuera de `CUENTAN_KPI_01`; `DETALLE_PERMITIDO`: `periodo`, `anio`, `encontrados`, `no_encontrados`, `faltantes`, `reemplazadas`, `equivalencia`. Entidad `seccion` y su id.
- `Operacion.EQUIVALENCIA_SECCION_BORRADA`, fuera de `CUENTAN_KPI_01`; `DETALLE_PERMITIDO`: `anio`, `grado`. Entidad `seccion` y su id (D13).
- Datos para la tesis: ninguno nuevo. La tesis mide la D2 con RF-024 en la lista de cotejo; la entrada de actividad deja constancia de cada uso.

### D13. Corregir la equivalencia
- El resumen lleva el id de la equivalencia solo si la sección salió de una (D5, pasos 1 o 3). «¿No es esta sección?» es un `<button>` de un formulario `POST /direccion/plantilla-siagie/equivalencias/<id>/borrar/` con CSRF; `plantilla-siagie.js` lo envía y reemplaza el panel «Archivo de salida» con el aviso y «Subir plantilla otra vez» (que abre el diálogo vacío), y suelta el `Blob` (`URL.revokeObjectURL`). Sin JS, la respuesta redirige (303) a `/direccion/`.
- `servicios.borrar_equivalencia(usuario, equivalencia_id)`: en un `atomic()`, `select_for_update` de la equivalencia filtrada por la institución del usuario; si no está, `EquivalenciaInexistente` («Esta equivalencia ya no existe.», 404) sin entrada; si está, la borra y registra EQUIVALENCIA_SECCION_BORRADA (entidad `seccion`, detalle `anio` y `grado`).
- Sin diálogo de confirmación: borrar no pierde datos de la docente y la próxima plantilla vuelve a preguntar (filtro anti-sobrepulido).
- El admin sigue de solo lectura: el único camino de borrado es este, con su registro.

### D12. Pruebas
- `exportaciones/tests/plantilla.py`: genera con openpyxl una plantilla ficticia con la forma de la muestra (Parametros oculta, hojas de área con filas 1 y 2, validaciones, leyenda), con parámetros para variar código modular, anexo, año, periodo, grado, sección, hojas y nombres. Código modular ficticio; nombres ficticios. Ningún archivo binario en el repo.
- Una prueba de ida y vuelta: tras llenar, el libro conserva la hoja oculta, las validaciones y las celdas no tocadas.
- e2e (6, en `exportaciones/tests/test_plantilla_siagie_e2e.py`): flujo principal con la descarga (`expect_download`) y la vuelta del foco; elegir la sección y completar sin volver a elegir el archivo; rechazo con el foco en el mensaje y el nombre conservado; corte de red (`page.route` que aborta) con el archivo conservado; 360 px del resumen; axe en ambos temas del diálogo con error, el paso de la sección y el resumen.

## Migration Plan

- `institucion/00NN_institucion_anexo` (columna con `db_default=0` y `CHECK`), `exportaciones/0001_initial` (tabla de equivalencias), `actividad/00NN` (choices). Se aplican antes de publicar el código; la versión anterior no lee las columnas nuevas.
- Vuelta atrás: borrar la tabla y la columna; las entradas PLANTILLA_SIAGIE_COMPLETADA quedan como texto.
- Antes del piloto: el Administrador carga el código modular y el anexo reales de la I.E. en el panel [DATO I.E. PENDIENTE].

## Open Questions

- Letra del periodo en trimestres (US-028) y nombres reales de las secciones en el SIAGIE (pregunta a Nayely; no bloquea).
