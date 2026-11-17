# Design: US-018 – Cargar sesiones del repositorio inicial

## Context

- Decisiones cerradas en `insumos/US-018/decisiones.md` (1 a 8); sin bocetos: se reutilizan `_lista.html` y `sesion.html`. Lo nuevo de este propose está en `proposal.md`.
- `Sesion` hoy: `autor` obligatorio, `origen` solo PROPIA, `estado` solo ENVIADA, `grado` único, `ck_sesion_terminos` (compartida ⇒ fecha), `idx_sesion_busqueda (institucion, grado, area)`.
- Las lecturas de US-011 se apoyan en `compartida=True` y `institucion_id`: `sesion_visible`, `_compartidas` (lista, conteos, contadores) y `registrar_vista`. «Mis sesiones» filtra por `autor_id`. `_bloquear_de_la_autora` filtra por `autor_id` y, si la sesión es visible y ajena, responde `SoloLaAutora` con INTENTO_SIN_PERMISO.
- El panel: todo `ModelAdmin` que escribe usa `RegistraEnPanel` (registra AGREGAR y CAMBIAR con los nombres de los campos) y ninguno borra; `test_cada_model_admin_que_escribe_usa_la_mezcla` lo exige. La ficha y la lista con POST corren dentro de `atomic()`.
- El Administrador de `createsuperuser` no tiene institución (`ck` de `cuentas`).
- «Sesiones cargadas» cuenta entradas SESION_ENVIADA; KPI-01 cuenta solo participantes (docentes con sección). El Administrador no es participante.

## Riesgos y zonas delicadas (primero)

- **[CHECK de `Sesion`]** (zona de cuidado) → D1: los `CHECK` nuevos se definen antes que el código y la migración `0003` los reemplaza en un paso; las filas actuales (todas PROPIA) cumplen todos. La vuelta atrás falla si ya hay una sesión de referencia: se acepta (se borran antes a mano).
- **[Fuga entre instituciones]** → D3: la referencia reusa la puerta única `sesion_visible` y `_compartidas`, que filtran por la institución del usuario; no se agrega otro camino de lectura. La institución de la sesión la fija el Administrador en la ficha y no se edita.
- **[Vistas y descarga que asumen una autora]** (zona de cuidado) → D3 y D6: cada lugar que lee `autor` se revisa (tarjeta, página, `datos_de_la_pagina`, `registrar_vista`, `entregar_archivo`, `_bloquear_de_la_autora`, demo). Con `autor_id = None`, las comparaciones con `usuario.pk` dan «ajena», que es lo correcto; las plantillas dejan de leer `autor.get_full_name` en la referencia.
- **[El panel ve sesiones de docentes]** (RN-015) → D4: el `ModelAdmin` es de un modelo proxy cuyo gestor filtra `origen=REFERENCIA`; la ficha de una sesión de docente da 404 en el panel.
- **[Borrar en el panel]** (RN-023, permisos) → D5: se abre el borrado solo para la referencia, desde la ficha, con su operación; `RegistraEnPanel` sigue fallando si otro `ModelAdmin` intenta borrar sin declarar su operación. Sin acción masiva.
- **[Archivo huérfano]** → D4: la escritura del archivo va dentro del `try` del servicio, como en `_guardar`; el borrado, al confirmar. Si algo falla **después** de `save_model` (el `LogEntry` del panel), el archivo queda en el bucket privado: se acepta, como en US-010 (comando de conciliación en la deuda).
- **[Extracción dentro del `atomic()` del panel]** → D4: la ficha corre en una transacción; la extracción (1,2 s medido con un PDF de 4 MB en US-011) la alarga. La fila es nueva y nadie más la bloquea; se acepta.
- **[Datos personales]** (RN-015) → fuente, permiso, título y texto no van al registro ni a los logs; el detalle de editar lleva solo nombres de campos.

## Goals / Non-Goals

**Goals:**
- Reglas y escrituras en `repositorio/servicios.py`; `admin.py` solo arma la ficha y llama al servicio.
- Las listas, la búsqueda, la página y la descarga de US-011 sirven la referencia sin una consulta nueva.

**Non-Goals:**
- Reemplazar el archivo de una referencia (se elimina y se carga de nuevo).
- Cambiar su institución.
- Descargar o previsualizar el archivo desde el panel.
- Grados no contiguos (1.º y 3.º sin 2.º).

## Decisions

### D1. Modelo (`repositorio/models.py`, migración `0003`)
- `Origen.REFERENCIA`. `autor` pasa a `null=True` (sigue `PROTECT`). `estado` admite `""` (cadena vacía, como el resto del modelo).
- Campos nuevos: `grado_hasta` (`SmallIntegerField`, rellenado con `grado` en las filas actuales); `fuente` y `permiso_uso` (`CharField(300)`, `""` por defecto, con `db_default`, como `texto`).
- **La referencia se guarda con `compartida=True`**: «compartida» pasa a significar «está en el repositorio de su institución». Así sirven sin cambios `sesion_visible`, `_compartidas` y `registrar_vista`.
- `CHECK` (reemplazan o se suman):
  - `ck_sesion_origen`: `origen IN ('PROPIA', 'REFERENCIA')`.
  - `ck_sesion_grado`: `1 <= grado <= grado_hasta <= 6`.
  - `ck_sesion_un_grado`: `origen = 'REFERENCIA' OR grado_hasta = grado` (decisión 4).
  - `ck_sesion_estado`: `(origen = 'REFERENCIA' AND estado = '') OR (origen <> 'REFERENCIA' AND estado IN ('ENVIADA'))`.
  - `ck_sesion_autor`: `(origen = 'REFERENCIA') = (autor_id IS NULL)`.
  - `ck_sesion_referencia`: `origen <> 'REFERENCIA' OR (compartida AND terminos_aceptados_en IS NULL AND fuente <> '' AND permiso_uso <> '')`.
  - `ck_sesion_terminos`: `compartida = false OR terminos_aceptados_en IS NOT NULL OR origen = 'REFERENCIA'`.
- Proxy `SesionReferencia(Sesion)` con un gestor que filtra `origen=REFERENCIA`; `verbose_name` «sesión de referencia». Solo lo usa el panel.
- Propiedad `Sesion.grados_texto`: «2.º grado» o «3.º–5.º grado». Reemplaza `dict(GRADOS)[sesion.grado]` en `datos_de_la_pagina`.
- *Alternativas descartadas:* `compartida=False` con `OR origen = REFERENCIA` en cada consulta (cinco lugares que olvidar); `autor` = el Administrador (la tarjeta y «Mis sesiones» lo tratarían como autora y la decisión 2 dice «sin autora»).

### D2. Varios grados como rango
- `grado` es el inicial y `grado_hasta` el final; la docente envía `grado_hasta = grado` (lo pone `_guardar` y la demo).
- El filtro de grado pasa a `grado <= g AND grado_hasta >= g` en `buscar_repositorio` y `conteos_por_area`; el conteo por área sigue siendo de filas, así que la referencia cuenta una vez.
- `idx_sesion_busqueda (institucion, grado, area)` sigue sirviendo: la institución es igualdad y `grado <= g` un rango sobre la segunda columna. Con decenas o cientos de filas por institución no hace falta otro índice.
- *Alternativas descartadas:* `ArrayField` de grados con índice GIN (admite grados sueltos, que nadie pidió, y obliga a un índice nuevo); tabla `sesion_grado` (una junta en cada lista y en cada conteo).

### D3. Lecturas
- `sesion_visible`, `_compartidas`, `registrar_vista` y `entregar_archivo` no cambian (D1). `mis_sesiones` y `contadores["mis_sesiones"]` filtran por `autor_id`, así que la referencia nunca entra.
- `datos_de_la_pagina` agrega `referencia` (bool) y el texto de grados; la miga va al «Repositorio» porque no es propia.
- `_bloquear_de_la_autora` no cambia: una docente sobre la referencia visible recibe `SoloLaAutora` con INTENTO_SIN_PERMISO (`sesion_ajena`), como pide el spec.

### D4. Servicio y ficha del panel
- `servicios.validar_referencia(datos, archivo, al_crear)`: institución, grados (inicial y final, final ≥ inicial), área que la institución trabaja (`se_trabaja`, RN-007; reutiliza la consulta de `_validar_area` con la institución elegida, no la del usuario), título, propósito, fuente y permiso (sin espacios en los bordes; si falta alguno, «Indique la fuente y el permiso de uso» como error de la ficha), y el archivo con `validar_archivo` solo al crear. Mensajes de campo: los de `envio-sesiones`.
- `servicios.cargar_referencia(administrador, datos, archivo)`: valida, transcribe con `_transcribir` y guarda con la misma lógica de `_guardar` (fila primero, archivo después, borrado del archivo si algo falla), con `origen=REFERENCIA`, `autor=None`, `subido_por=administrador`, `estado=""`, `compartida=True`, sin términos; registra SESION_REFERENCIA_CARGADA. `_guardar` se generaliza para recibir los campos que cambian entre los dos orígenes; la operación de actividad va como parámetro.
- `servicios.editar_referencia(administrador, sesion, datos)`: valida sin archivo, recalcula `texto_busqueda` con el texto guardado, `save(update_fields=...)` y SESION_REFERENCIA_EDITADA con los nombres de los campos cambiados; sin cambios, sin entrada.
- `admin.py`, `SesionReferenciaAdmin` sobre el proxy: formulario con `archivo` (`FileField`, solo al crear) y los campos de D1; `clean()` llama a `validar_referencia` y reparte sus errores por campo; `save_model` llama a `cargar_referencia` o a `editar_referencia`. Lectura de `archivo_nombre`, tipo y tamaño en la ficha. `list_display`: título, grados, área, institución, fuente, fecha. Búsqueda por título.
- Registro: como el servicio ya registra, el `ModelAdmin` no usa el registro de `RegistraEnPanel` para esta ficha; usa la mezcla solo por su `FOR UPDATE` y su regla de borrado (D5) y su `operacion_del_panel` devuelve `[]`. *Alternativa descartada:* registrar en `log_addition` (fuera del `try` del archivo, y el servicio no sabría si registrar cuando lo llama otra cosa).
- `institucion` en la ficha: obligatoria; si hay una sola institución, viene elegida.
- Antes de usar `ModelAdmin.log_deletions`, `delete_model` y `get_actions`, confirmar su firma en Django 5.2 con Context7: el repo solo usa `log_deletions` para impedir el borrado.

### D5. Borrar en el panel
- `RegistraEnPanel` suma `operacion_al_borrar = None`. Si un `ModelAdmin` la declara, `log_deletions` llama a `super()` (el `LogEntry`) y no lanza; si no, sigue lanzando como hoy.
- `SesionReferenciaAdmin`: `has_delete_permission` verdadero; `operacion_al_borrar = SESION_REFERENCIA_ELIMINADA`; `delete_model` llama a `servicios.eliminar_referencia(administrador, sesion)`, que usa `borrar_sesiones` (fila y vistas en la transacción, archivo al confirmar) y registra la operación; `get_actions` quita `delete_selected`. `delete_queryset` lanza, por si alguien vuelve a poner la acción.
- `test_cada_model_admin_que_escribe_usa_la_mezcla` pasa a exigir: ningún `ModelAdmin` borra salvo los que declaran `operacion_al_borrar`.

### D6. Plantillas
- `_lista.html`: con `s.origen == "REFERENCIA"`, «Material de referencia» en lugar de `s.autor.get_full_name`, y `s.grados_texto` en ambos casos.
- `sesion.html`: chip de grados con `grados_texto`; en la referencia, chip «Material de referencia» en lugar de «Compartida», sin la fila «Autora», «Fecha de carga» en lugar de «Fecha de envío», y un `aside` «Material de referencia» con la misma forma que «Tu sesión» y un `dl` de fuente y permiso de uso; sin botones. Fuente y permiso pasan por el autoescape.
- Sin JS, sin CSS nuevo salvo que el `aside` necesite una clase; sin colores nuevos.

### D7. Actividad
- `SESION_REFERENCIA_CARGADA`, `SESION_REFERENCIA_EDITADA` (detalle `{"campos"}`) y `SESION_REFERENCIA_ELIMINADA`, fuera de `CUENTAN_KPI_01`; migración del `CHECK` de `actividad`; cada una con su fila en `actividad/tests/escenarios.py`.
- Dato de la tesis: no cambia. El uso del repositorio sigue en SESION_VISTA, SESION_DESCARGADA y `sesion_vista`; para separar el uso del material de referencia basta unir por `entidad_id` con `sesion.origen`.

### D8. Pruebas e2e
- Ninguna nueva: la tarjeta y la página son HTML del servidor sin conducta de JS, y la referencia es una variante de datos de pantallas que ya tienen su e2e de axe y de 360 px. Lo comprueban pruebas de plantilla y de vista. Las e2e de `repositorio` cumplen las reglas vigentes: no hay e2e a retirar.

## Migration Plan

1. `repositorio/0003`: `AddField` de `grado_hasta` (con valor provisional), `RunPython` que copia `grado` a `grado_hasta`, `AlterField` de `autor` y `estado`, `AddField` de `fuente` y `permiso_uso`, reemplazo de los `CHECK` y proxy. `actividad`: migración del `CHECK` de operaciones.
2. La vista previa de Vercel aplica las dos en Neon; se carga una sesión de referencia de prueba ficticia (RN-018) y se borra.
3. Después de la fusión, Marco carga por el panel las sesiones reales anonimizadas, con su texto de permiso de uso.
4. Vuelta atrás: revertir las migraciones solo si no hay sesiones de referencia.

## Open Questions

- Texto exacto del permiso de uso de las sesiones de Marco y consentimiento de su madre (decisiones.md; no bloquea: el campo es texto libre).
- ¿La I.E. tiene aulas multigrado? (Nayely; no bloquea esta historia).
