# Design: US-008 – Registrar la actividad de los usuarios

## Context

- Las decisiones de alcance están cerradas en `insumos/US-008/decisiones.md` (aprobado el 30-10, decisiones 1 a 12). Este design dice cómo se construyen y cierra lo que el propose debía decidir.
- La app `actividad` existe vacía. Escriben datos hoy:
  - `asistencia/servicios.py`: `marcar` (upsert con `ON CONFLICT`) y `marcar_restantes` (`ignore_conflicts`), ambos en `transaction.atomic()`; la jornada nace en `_jornada` con `get_or_create`.
  - `institucion/servicios.py`: `importar_lista`, `agregar_estudiante`, `editar_estudiante`, `quitar_estudiante`, `vaciar_lista`, `cargar_secciones`; `institucion/demo.py`: `cargar_demo`, `quitar_demo`, `descartar_seccion`. Todos con su `atomic()`.
  - Panel: `UsuarioAdmin` (alta, edición, cambio de contraseña, acción "Desbloquear cuenta"), `InstitucionAdmin` (alta, edición **y borrado**), `AnioEscolarAdmin`, `SeccionAdmin` (alta y ficha con docente), `AreaAdmin`, `CompetenciaAdmin`, `InstitucionAreaAdmin` (con `list_editable`). `Group` sigue registrado por `django.contrib.auth`.
  - Sesión: `IngresarView` (`LoginView`), `LogoutView` en `/salir/` y `InactividadMiddleware._cerrar_por_inactividad` (llama a `logout`).
- El "Deshacer" de US-030 vive en `asistencia.js`: el lote no se envía hasta que acaba la cuenta, así que el servidor no ve deshaceres.
- Las cuentas demo se reconocen por `Usuario.es_demo` (EN-06, corrección del PR #66).
- Django 5.2, `TIME_ZONE = "America/Lima"`, `USE_TZ = True`, sin `ATOMIC_REQUESTS`.

## Riesgos y zonas delicadas (primero)

- **[Una escritura sin entrada, RNF-016 al 100 %]** → D2 y D5: `registrar` se llama dentro del `atomic()` de cada servicio; el panel registra desde una sola mezcla. Dos pruebas de cierre: cada operación del catálogo (salvo la reservada) tiene una prueba que la genera, y cada `ModelAdmin` registrado que permite escribir usa la mezcla (D5).
- **[Entrada sin operación o al revés]** → D2: `registrar` exige estar dentro de una transacción (`connection.in_atomic_block`) y falla si no; así una llamada fuera de lugar se ve en la prueba y no en producción.
- **[Datos personales en el detalle, RN-015]** → D7: el detalle se arma con claves permitidas por operación; `registrar` rechaza claves que no están en la lista. Prueba que recorre las entradas generadas y busca los nombres ficticios usados.
- **[Migración]** → `actividad/0001` crea una tabla nueva sin datos; tramo de alto riesgo solo (grupo 1, parte A).
- **[Solo lectura]** → D8: en el panel, sin permisos de agregar, cambiar ni borrar para nadie; en el modelo, `save()` sobre una entrada existente y `delete()` lanzan error. `QuerySet.update()`/`delete()` no pasan por ahí: el bloqueo en la base es EN-04 (trigger), fuera de alcance.
- **[CSV abierto en una hoja de cálculo]** → D10: las celdas que empiezan con `=`, `+`, `-` o `@` (también tras espacios o tabulación) llevan un apóstrofo delante.
- **[Semanas en hora de Lima]** → D9: agrupar con `TruncWeek(..., tzinfo=ZoneInfo("America/Lima"))`; PostgreSQL toma el lunes como inicio de semana. Prueba del domingo a las 23:30.
- **[Asistencia: estado anterior en un upsert]** → D6: dentro del `atomic()`, leer el estado actual con `select_for_update()` antes del upsert. Dos toques simultáneos del mismo estudiante se ordenan por el bloqueo; el primer toque (sin fila) no tiene fila que bloquear y se ordena por la jornada (D6).

## Goals / Non-Goals

**Goals:**
- Una sola puerta de escritura al registro (`actividad.servicios.registrar`), en la transacción de la operación.
- Consulta, exportación e indicadores en el panel, sin pantallas nuevas fuera de él.
- Instrumentar lo ya construido sin cambiar su comportamiento observable.

**Non-Goals:**
- Inicios fallidos, trigger en PostgreSQL (EN-04); INTENTO_SIN_PERMISO en uso (US-004); KPI-02 a KPI-04 (US-028/US-040); plazo de conservación (US-009); indicadores por institución.

## Decisions

### D1. Modelo `RegistroActividad` (doc 11, 3.7)

`db_table = "registro_actividad"`; campos del doc 11: `usuario` (FK a `Usuario`, `null=True`, `on_delete=SET_NULL`, `related_name="actividad"`), `fecha_hora` (`default=timezone.now`, no `auto_now_add`, para poder fijarla en las pruebas de semanas), `operacion` (`CharField(40, choices=Operacion)`), `entidad` (`CharField(60, blank=True)`), `entidad_id` (`CharField(40, blank=True)`), `detalle` (`JSONField(default=dict, blank=True)`). Restricción `ck_actividad_operacion` (operación dentro del catálogo) generada desde las choices; índices `idx_actividad_fecha` y `idx_actividad_usuario_fecha` del doc 11, y uno más por `(operacion, fecha_hora)` para los indicadores. `entidad` es el `db_table` del modelo afectado ("jornada", "estudiante", "seccion"…). `ordering = ["-fecha_hora", "-id"]`.

Por qué: el doc 11 lo trae casi listo; la restricción en la base convierte "catálogo cerrado" en algo que no depende del código. Cadena vacía en vez de NULL, como en US-030.

### D2. `registrar(usuario, operacion, entidad="", entidad_id="", detalle=None)`

En `actividad/servicios.py`, única función que crea entradas. Acepta el objeto afectado o su id (`entidad_id` se guarda como texto). Si `usuario` no está autenticado, lo deja vacío. Falla con `RuntimeError` si no hay una transacción abierta (`connection.in_atomic_block`), con `ValueError` si la operación no es del catálogo o el detalle trae claves no permitidas (D7). Las vistas nunca la llaman: la llaman los servicios, la mezcla del panel (D5) y los receptores de sesión (D4).

### D3. Catálogo `Operacion` y marca KPI-01

`Operacion(models.TextChoices)` en `actividad/models.py`, con la lista del spec. La marca "cuenta para KPI-01" es un `frozenset` junto al catálogo (`CUENTAN_KPI_01 = {REGISTRO_ASISTENCIA, ASISTENCIA_CAMBIADA, JORNADA_COMPLETA}`); US-010 y US-020 agregan las suyas. `RESERVADAS = {INTENTO_SIN_PERMISO}` sirve a la prueba de cobertura.

Operaciones agregadas a la lista inicial de la decisión 2 (escrituras que ya existen): INSTITUCION_CREADA, INSTITUCION_EDITADA, ANIO_CREADO, ANIO_EDITADO, SECCION_CREADA, SECCION_EDITADA. Desbloquear y reactivar son CUENTA_EDITADA (campos `desbloqueo` e `is_active`); cambiar la contraseña desde el panel, CUENTA_EDITADA con el campo `password`.

### D4. Sesión: señales `user_logged_in` y `user_logged_out`

`actividad/signals.py`, conectado en `ActividadConfig.ready()`. INICIO_SESION se registra en `user_logged_in`; `IngresarView.form_valid` se envuelve en `transaction.atomic()` para que `last_login` y la entrada vayan juntos. El reinicio de intentos de RN-024 no entra en esa transacción: lo confirma antes `intentar_ingreso`, dentro de `authenticate()` y con su propio `atomic()`. Si la entrada falla, la contraseña era correcta y el contador queda en 0, que es lo que deja un ingreso correcto. CIERRE_SESION en `user_logged_out`, con `detalle = {"motivo": "boton" | "inactividad"}`: el middleware marca `request._cierre_por_inactividad = True` antes de `logout()`. El receptor abre su propio `atomic()` (el cierre no tiene otra escritura de datos que acompañar).

Caminos que se cierran en vez de registrarse: `InstitucionAdmin.has_delete_permission → False` (borrar una institución arrastra en cascada todo; RN-023, como los demás modelos) y `admin.site.unregister(Group)` (el sistema no usa grupos; RF-003 ya los esconde de la ficha de la cuenta).

### D5. Panel: mezcla `RegistraEnPanel` (copia del `LogEntry`)

En `actividad/panel.py`. Sobrescribe `log_addition`, `log_change` y `log_deletions` de `ModelAdmin`: llama a `super()` (el `LogEntry` de Django sigue igual) y luego a `registrar` con lo que devuelve `operacion_del_panel(request, obj, accion, campos)`, que cada `ModelAdmin` define: una lista de `(operación, detalle)`, porque un guardado puede dejar dos entradas. `campos` son los nombres de `form.changed_data`, que la mezcla toma en `construct_change_message` (el mismo dato con que Django arma su `change_message`), nunca los valores; un guardado sin cambios no deja entrada. Para que `changed_data` compare con lo guardado, en un POST la mezcla relee la fila con `FOR UPDATE` (la ficha, el cambio de contraseña y las filas de `list_editable`, cuyo POST envuelve en `atomic()`): así un guardado que revierte un cambio ajeno deja su entrada (A2). Django llama a `log_addition`/`log_change` dentro del `atomic()` de `changeform_view` y del de `changelist_view` con `list_editable`, pero `user_change_password` no abre transacción: `UsuarioAdmin` la envuelve en `atomic()`. La acción "Desbloquear cuenta" ya abre el suyo. Ningún modelo con la mezcla permite borrar, así que `log_deletions` solo falla con `NotImplementedError` si alguien lo habilita sin pensarlo.

Asignar y liberar: `SeccionAdmin.save_model` guarda en `request` el `docente_id` anterior (de `form.initial`) antes de `super()`; `operacion_del_panel` devuelve SECCION_ASIGNADA (docente nuevo no vacío) o SECCION_LIBERADA (vacío), con `{"docente_anterior": id, "docente_nuevo": id}`. Si cambian a la vez el grado o el nombre y el docente, quedan dos entradas (SECCION_EDITADA y la del docente). Cambiar de docente se hace en dos pasos (US-005, D3: vaciar la sección y luego elegir a la otra docente), así que deja SECCION_LIBERADA y luego SECCION_ASIGNADA; por eso SECCION_ASIGNADA trae `docente_anterior` vacío. Cuentas: `is_active` pasa a falso → CUENTA_DESACTIVADA, y si cambian otros campos en el mismo guardado, también CUENTA_EDITADA con esos campos; otro cambio → CUENTA_EDITADA (contraseña: `password`; desbloqueo: `desbloqueo`).

Prueba de cierre: recorre `admin.site._registry`; cada `ModelAdmin` que no sea el del registro y que permita agregar o cambiar debe heredar de la mezcla.

### D6. Asistencia: estado anterior, origen y jornada completa

- `_jornada` devuelve también si la creó; si sí, REGISTRO_ASISTENCIA con `entidad="jornada"` y `{"seccion": id, "fecha": "AAAA-MM-DD"}`.
- `marcar`: antes del upsert, `Asistencia.objects.select_for_update().filter(jornada, estudiante).first()` da el estado y la nota anteriores; si estado y nota son iguales, no se registra (reintento, RNF-011). Si no, ASISTENCIA_CAMBIADA con `entidad="asistencia"`, `entidad_id=jornada.pk` y `{"estudiante": id, "anterior": estado | None, "nuevo": estado, "nota_cambiada": bool, "origen": "toque"}`.
- `marcar_restantes`: dentro del `atomic()`, lee los ids que ya tienen estado (con `select_for_update`) antes del `bulk_create(ignore_conflicts=True)`; registra una ASISTENCIA_CAMBIADA con origen `lote` por cada estudiante que no lo tenía.
- JORNADA_COMPLETA: al final de `marcar` y `marcar_restantes`, si todos los activos tienen estado y la jornada aún no tiene esa entrada (consulta al registro), se registra. `_jornada` toma la jornada con `select_for_update()` para que dos toques finales simultáneos no dejen dos.
- Sin origen `deshacer`: el servidor no lo recibe (Context).

### D7. Detalle permitido por operación

`DETALLE_PERMITIDO: dict[Operacion, frozenset[str]]` junto al catálogo; `registrar` rechaza claves fuera de su lista. Los valores son ids, códigos, cantidades, fechas, estados o listas de nombres de campos. Así un `detalle={"nombres": …}` falla en la prueba. Nombres ficticios fijos en las pruebas de instrumentación y una prueba que busca esos nombres en `detalle` de todas las entradas.

### D8. Solo lectura

- `RegistroActividadAdmin`: `has_add_permission`, `has_change_permission` y `has_delete_permission` devuelven `False` para todos; `has_view_permission` solo para el rol Administrador. Sin acciones (sin `delete_selected`). Con permiso de solo ver, Django muestra la ficha sin campos editables.
- Modelo: `save()` con `pk` existente y `delete()` lanzan `PermissionDenied`; `registrar` es el único que crea.
- Docente y dirección no entran al panel (`IngresoPanelView`, `is_staff`); la prueba de la Ruta Infeliz lo comprueba en las URLs del registro, de la exportación y de los indicadores (redirección o 403, sin cambios en la base).

### D9. Indicadores por semana

Vista del panel en `RegistroActividadAdmin.get_urls()` (`indicadores/`, envuelta en `admin_site.admin_view` y con la comprobación de rol Administrador), plantilla `admin/actividad/indicadores.html` que extiende `admin/base_site.html` (estilos del panel, que ya tiene tema claro y oscuro). El cálculo, en `actividad/servicios.py` (`indicadores_por_semana(desde, hasta)`), devuelve una lista de filas:
- semanas: del lunes de la semana de `desde` al domingo de la de `hasta`, todas (con 0 si no hay actividad);
- `participantes`: cuentas Docente activas, sin `es_demo`, con sección en un año ABIERTO; se calculan una vez, con el estado de hoy (no hay historial de asignaciones);
- `activos`: participantes distintos con una operación de `CUENTAN_KPI_01` en la semana (`TruncWeek` con la zona de Lima);
- `jornadas`: entradas REGISTRO_ASISTENCIA de la semana con usuario no demo y no vacío;
- `sesiones` y `secciones_con_notas`: `None`, que la plantilla muestra como "—".
Rango por defecto: 1 de enero del año ABIERTO a hoy (si hay más de uno, el más reciente; sin año abierto, el año en curso; si el año abierto aún no empieza, porque se abrió antes de enero, también el año en curso, para que la página no abra con el rango al revés). Formulario `GET` con dos campos de fecha.

Datos para la tesis: KPI-01 sale de `registro_actividad.operacion` (marcada en `CUENTAN_KPI_01`), `usuario_id` y `fecha_hora`; las jornadas, de `operacion = REGISTRO_ASISTENCIA`. El tiempo de toma (VD – D3) sigue en `jornada.creado_en` y `asistencia.actualizado_en` (US-030).

### D10. Exportar

Botón "Exportar CSV" en la lista del registro (plantilla `admin/actividad/registroactividad/change_list.html` que extiende la del panel), que hace `POST` a `exportar/` con la cadena de filtros actual. La vista reconstruye la `ChangeList` del panel para usar los mismos filtros, escribe el CSV con `csv.writer` (UTF-8 con BOM, para que Excel muestre las tildes), en orden de la lista, y en un `atomic()` registra REGISTRO_EXPORTADO con `{"filtros": {…}, "filas": N}`. Columnas: fecha y hora (Lima, `dd-mm-aaaa hh:mm:ss`), usuario (nombre de usuario o vacío), operación, entidad, identificador, detalle (JSON). Las celdas peligrosas llevan `'` delante (Riesgos). Por qué un botón y no una acción del panel: las acciones exigen marcar filas, y la decisión 10 pide "el registro filtrado".

### D11. Filtros de la consulta

`list_display`: fecha y hora, usuario, operación, entidad, identificador. `list_filter`: operación, `usuario` (`RelatedOnlyFieldListFilter`) y `fecha_hora` con un filtro de rango propio de dos fechas (`desde`, `hasta`), porque el `DateFieldListFilter` de Django solo ofrece "hoy, últimos 7 días, este mes, este año". `date_hierarchy` no se usa (consulta por mes pesada en Slow 4G). `list_select_related = ["usuario"]`, 50 por página.

## Migration Plan

`actividad/0001_initial`: tabla, restricción e índices. Sin datos. Reversible (borra la tabla). En Neon se aplica con el despliegue normal (EN-02).

## Open Questions

Ninguna. Marco aprobó el 30-10-2026 los dos caminos que se cierran (D4) y las seis operaciones agregadas (D3); se anotan en la descripción del PR para que el equipo los vea.
