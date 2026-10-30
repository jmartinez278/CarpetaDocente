# Tasks

**Reglas para todas las tareas:**
- Pruebas primero (TDD): cada prueba se escribe y se ve fallar antes del código. Ante una falla inesperada, depuración sistemática.
- Antes de usar una API de Django (señales de sesión, `ModelAdmin.log_*`, `ChangeList`, `TruncWeek`, `JSONField`) o Playwright, se consulta Context7.
- Solo nombres ficticios. Ningún dato de la I.E. inventado.
- Plantillas del panel: extienden las del panel de Django; sin hex ni `style=`. Un intento y una corrección; si pasa las pruebas y axe, se sigue.
- Un commit por parte. Su casilla y su evidencia en `verificacion.md` van en ese commit. Antes de cada commit:
  - revisión (Superpowers `requesting-code-review`): Critical e Important se corrigen; los Minor van a `verificacion.md`, "## Minor para la descripción del PR";
  - lo que entra va al índice y se corre `uv run python scripts/verificar.py --antes-del-commit`;
  - se muestran los archivos y el mensaje, y se espera la aprobación. Sin push.

## 1. Registro y consulta (D1 a D3, D7 a D11)

### Parte A: modelo, migración y `registrar` (alto riesgo, solo)

- [x] 1.1 Prueba primero, `actividad/tests/test_modelos.py`: operación fuera del catálogo rechazada por la base (`IntegrityError`, `ck_actividad_operacion`); `usuario` vacío permitido; borrar el usuario deja la entrada con usuario vacío; `save()` de una entrada existente y `delete()` lanzan `PermissionDenied` y la entrada queda igual; orden de la más reciente a la más antigua. Luego `Operacion`, `CUENTAN_KPI_01`, `RESERVADAS`, `RegistroActividad` (D1, D3, D8) y `actividad/0001`. Verificar: rojo y luego verde; `makemigrations --check` sin cambios; `sqlmigrate actividad 0001` muestra la tabla `registro_actividad`, la restricción y los tres índices
- [x] 1.2 Prueba primero, `actividad/tests/test_registrar.py`: guarda usuario, operación, entidad, id como texto y detalle; usuario anónimo → vacío; fuera de una transacción, `RuntimeError`; operación fuera del catálogo o clave de detalle no permitida, `ValueError` sin guardar nada; si la operación de la misma transacción falla, no queda entrada, y si `registrar` falla, la operación no se guarda (escenarios "La operación falla" y "El registro falla"). Luego `actividad/servicios.py` con `registrar` y `DETALLE_PERMITIDO` (D2, D7). Verificar: rojo y luego verde
- [x] 1.3 Revisión de la parte y commit (reglas de arriba)

### Parte B: panel de solo lectura, exportación e indicadores

- [ ] 1.4 Prueba primero, `actividad/tests/test_panel.py`: el Administrador ve la lista y la ficha sin campos editables ni botones de agregar, guardar o eliminar; POST a agregar, cambiar y borrar → 403 sin cambios; sin acciones; docente y dirección no entran a la lista, la ficha, `exportar/` ni `indicadores/` (Ruta Infeliz); filtros por usuario, operación y rango de fechas (escenario "Filtrar"), con hora de Lima en la lista. Luego `actividad/admin.py` y el filtro de rango (D8, D11). Verificar: rojo y luego verde
- [ ] 1.5 Prueba primero, `actividad/tests/test_exportar.py`: con un filtro puesto, el CSV trae solo esas filas, con BOM, columnas de D10 y hora de Lima; una celda que empieza con `=`, `+`, `-`, `@` o espacio + `=` sale con `'`; queda REGISTRO_EXPORTADO con filtros y número de filas; GET → 405; otro rol, sin CSV. Luego el botón, `change_list.html` y la vista `exportar/` (D10). Verificar: rojo y luego verde
- [ ] 1.6 Prueba primero, `actividad/tests/test_indicadores.py` (entradas creadas con `registrar` y `fecha_hora` fija):
  - semanas de lunes a domingo, todas con 0 si no hay actividad; domingo 23:30 de Lima en su semana; rango que corta una semana la muestra entera; rango al revés con su mensaje y sin filas; rango por defecto del 1 de enero del año ABIERTO a hoy;
  - participantes: Docente activa con sección en año ABIERTO; fuera la desactivada, la sin sección, la de un año CERRADO y la demo;
  - activos: solo inicio y cierre de sesión no cuenta; dos días de asistencia cuentan una vez; "3 / 5 (60 %)" y "0 / 0 (—)";
  - jornadas: cuenta REGISTRO_ASISTENCIA y no las de cuentas demo ni las de usuario vacío; "Demo cargada" → "1 / 1 (100 %)" y 1 jornada;
  - sesiones y secciones con notas: "—".

  Luego `indicadores_por_semana`, la URL `indicadores/`, la plantilla y el enlace desde la lista del registro (D9). Verificar: rojo y luego verde
- [ ] 1.7 Prueba primero, `actividad/tests/test_panel_e2e.py`: axe de la lista del registro y de "Indicadores por semana" en ambos temas a 360 y 1280 px; la descarga del CSV desde el botón. Verificar: e2e en verde con el CSS compilado y `DJANGO_ALLOW_ASYNC_UNSAFE=true`
- [ ] 1.8 Pantallas del panel vistas en claro/oscuro y celular/escritorio (la marca Marco). Revisión de la parte y commit (reglas de arriba); actualizar el Catálogo de rutas de `docs/03` (versión y fecha) en este commit

## 2. Instrumentación de lo ya construido (D4 a D6)

### Parte A: sesión y asistencia

- [ ] 2.1 Prueba primero, `actividad/tests/test_sesion.py`: ingreso correcto → INICIO_SESION; "Cerrar sesión" → CIERRE_SESION con motivo `boton`; cierre por inactividad → motivo `inactividad`; ingreso rechazado no deja entrada (EN-04); abrir la portada no deja entrada. Luego `actividad/signals.py`, `ActividadConfig.ready()`, `atomic()` en `IngresarView.form_valid` y la marca en `InactividadMiddleware` (D4). Verificar: rojo y luego verde; `inicio-sesion` y `cierre-sesion` siguen en verde
- [ ] 2.2 Prueba primero, `asistencia/tests/test_actividad.py`: "Camino ideal" (primer toque → REGISTRO_ASISTENCIA con usuario, fecha, hora y jornada, y ASISTENCIA_CAMBIADA con anterior vacío y origen `toque`); cambio de estado con anterior y nuevo; mismo estado y nota otra vez → sin entrada; nota cambiada → `nota_cambiada` sin el texto; lote → una por cada Sin marcar, origen `lote`; JORNADA_COMPLETA una sola vez (también con el último marcado por el lote); toque rechazado (otra sección, fecha que no es hoy) → sin entrada; abrir la asistencia de hoy → sin entrada. Luego `asistencia/servicios.py` (D6). Verificar: rojo y luego verde; las pruebas de US-030 (unitarias y e2e) siguen en verde
- [ ] 2.3 Revisión de la parte y commit (reglas de arriba)

### Parte B: estudiantes, panel y comandos

- [ ] 2.4 Prueba primero, `institucion/tests/test_actividad.py`: ESTUDIANTES_IMPORTADOS (con cantidad), ESTUDIANTE_AGREGADO, ESTUDIANTE_EDITADO (sin nombres), ESTUDIANTE_QUITADO y LISTA_VACIADA desde las vistas; quitar o vaciar bloqueado por `ListaConRegistros` → sin entrada; `cargar_secciones` → SECCION_CREADA por sección nueva con usuario vacío; `cargar_demo`, `quitar_demo` y `descartar_seccion` → DEMO_CARGADA, DEMO_QUITADA y SECCION_DESCARTADA con usuario vacío y sus conteos; las entradas de asistencia de la sección descartada siguen ("Conservación"). Luego los servicios de `institucion/servicios.py` y `demo.py`, y las claves de los conteos de DEMO_CARGADA, DEMO_QUITADA y SECCION_DESCARTADA en `DETALLE_PERMITIDO` (hoy esas tres no admiten detalle). Verificar: rojo y luego verde
- [ ] 2.5 Prueba primero, `actividad/tests/test_panel_instrumentado.py`: CUENTA_CREADA, CUENTA_EDITADA (campos sin valores; contraseña; desbloqueo; reactivar), CUENTA_DESACTIVADA; INSTITUCION_CREADA, INSTITUCION_EDITADA; ANIO_CREADO, ANIO_EDITADO; SECCION_CREADA, SECCION_EDITADA, SECCION_ASIGNADA (elegir y cambiar, con anterior y nuevo), SECCION_LIBERADA; CATALOGO_EDITADO desde la ficha y desde `list_editable`; el `LogEntry` de Django sigue apareciendo; borrar una institución → 403; `Group` fuera del panel; cada `ModelAdmin` que escribe usa la mezcla (D5). Luego `actividad/panel.py` y los `admin.py` de `cuentas`, `institucion` y `catalogo` (D4, D5). Verificar: rojo y luego verde; las pruebas de US-003, US-005 y EN-06 siguen en verde
- [ ] 2.6 Prueba primero, `actividad/tests/test_catalogo.py`: tabla operación → escenario (que llama a la prueba real de 1.5, 2.1, 2.2, 2.4 o 2.5); su conjunto es igual a `Operacion` menos `RESERVADAS`; y en todas las entradas generadas por esos escenarios no aparece ningún nombre ficticio de estudiante ni texto de nota (RN-015). Verificar: rojo con una operación sin escenario, verde con la tabla completa; `uv run pytest --cov` en verde y con 80 % o más
- [ ] 2.7 Revisión de la parte y commit (reglas de arriba)

## 3. Revisión final y verificación

- [ ] 3.1 Con la revisión final A2 que corre el usuario (`/codex:adversarial-review --base main --background`, con foco en los specs del cambio y en RNF-016), corregir los Critical e Important, con la prueba primero en cada caso. Los Minor van a `verificacion.md`. Verificar: `uv run pytest --cov`, las e2e y `verificar.py --antes-del-commit` en verde
- [ ] 3.2 `verificacion.md` corto: tabla escenario → prueba de los dos specs del cambio y la DoD 1 a 9. Verificar: cada escenario tiene su prueba o una nota de por qué no aplica; commit del grupo (reglas de arriba)

## Ajustes del propose a decisiones.md

- Decisión 2: se agregan INSTITUCION_CREADA, INSTITUCION_EDITADA, ANIO_CREADO, ANIO_EDITADO, SECCION_CREADA y SECCION_EDITADA (escrituras ya existentes que la lista no cubría, decisión 12). Desbloquear, reactivar y cambiar la contraseña desde el panel son CUENTA_EDITADA.
- Decisión 3: el origen `deshacer` no llega al servidor (el "Deshacer" de US-030 es del navegador); quedan `toque` y `lote`. "Una por estudiante y cambio": un reintento con el mismo estado y nota no deja entrada.
- Decisión 2: JORNADA_CERRADA se renombra JORNADA_COMPLETA (US-030 no tiene cierre de jornada; su spec habla de "jornada completa"). Se registra la primera vez que todos los activos quedan marcados.
- Decisión 9: las cuentas demo se reconocen por `es_demo`, no por prefijo (corrección de EN-06 en el PR #66).
- Dos caminos del panel se cierran en vez de registrarse: borrar instituciones y gestionar grupos (D4).

## Workflow follow-up

- **(equipo)** Push de `feature/US-008-registrar-actividad` y PR hacia `main` (`Closes #N` de US-008, verificando el número), con las verificaciones de EN-08 en verde. En "Para quien revise": el registro se escribe solo desde `actividad.servicios.registrar` dentro de la transacción de cada operación; se agregan seis operaciones al catálogo; el panel deja de permitir borrar instituciones y gestionar grupos; US-030 (servicios), US-001/002 (ingreso y cierre) y los admin de US-003, US-005 y EN-06 se tocan solo para registrar. En "## Deuda":
  - inicios fallidos y trigger que bloquee UPDATE/DELETE de `registro_actividad` en PostgreSQL → EN-04;
  - INTENTO_SIN_PERMISO en uso → US-004;
  - columnas "sesiones cargadas" y "secciones con notas" → US-010 y US-020 (agregan sus operaciones y su marca KPI-01); KPI-02 a KPI-04 → US-028 / US-040;
  - plazo de conservación → US-009;
  - participantes contados con el estado de hoy, no el de cada semana (no hay historial de asignaciones); indicadores por institución si entra una segunda I.E.;
  - US-031 reutiliza ASISTENCIA_CAMBIADA (días anteriores), sin operación nueva;
  - contradicciones para la pasada de docs: RNF-016 (catálogo, lecturas fuera, consola con usuario vacío, conservación, transacción); doc 06 RF-008 Ruta Infeliz (docente y dirección no entran al panel); doc 11 3.7 (`entidad`/`entidad_id` como cadena vacía en vez de NULL, índice extra por operación y fecha).
- **(equipo)** Aprobación del PR por otra integrante (DoD 3).
- Después de la fusión: `/opsx:archive` con "Sync now". La siguiente historia sale de `main` y su primer commit es este archivo.
