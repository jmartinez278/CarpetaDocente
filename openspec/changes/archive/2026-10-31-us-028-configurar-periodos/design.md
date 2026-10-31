# Design: US-028 – Configurar los periodos del año escolar

## Context

- Decisiones de alcance cerradas en `insumos/US-028/decisiones.md` (1 a 9 y zonas de cuidado); el porqué está en `proposal.md`. Sin bocetos: es el panel de Django.
- `institucion` tiene `Institucion.organizacion_periodos` (BIMESTRE, TRIMESTRE o vacío) y `AnioEscolar` (sin periodos, design de US-005 D1). `AnioEscolarAdmin` usa `RegistraEnPanel` (US-008, D5): en un POST relee el año con `FOR UPDATE` dentro del `atomic()` de la ficha y registra ANIO_EDITADO solo con campos del año cambiados.
- `notas` está vacía: no hay calificaciones que apunten a un periodo. El "sin alterar las notas" se prueba por el id del periodo, que no cambia al editar sus fechas.
- Django 5.2 y PostgreSQL 17 en local y en la CI (`postgres:17`); Neon en Vercel, donde el build corre `migrate` (spec `despliegue`). El repo aún no usa `django.contrib.postgres` ni extensiones.
- En Django 5.2, `ModelForm` corre `full_clean()`, que valida cada `ExclusionConstraint` fila por fila contra lo que ya está en la base, también si es diferible (revisado en el código instalado).
- `TIME_ZONE = "America/Lima"`; "hoy" se obtiene con `timezone.localdate()`, como en `asistencia`.

## Riesgos y zonas delicadas (primero)

- **[`btree_gist` en Neon y en la CI]** → la extensión es de las "trusted" desde PostgreSQL 13: la crea el dueño de la base, sin superusuario. Viene en la imagen `postgres:17` y Neon la ofrece. Se comprueba **antes** del modelo (tarea 1.1): en local con `CREATE EXTENSION` en la base de pruebas, en la CI con la migración, y en Neon con el build de la vista previa del PR (el build falla si `migrate` falla). Si Neon la negara, el plan B es dejar la regla solo en el servicio con el año bloqueado (D4) y anotarlo en la deuda; no cambia los specs.
- **[Falso cruce al correr dos periodos]** → con una restricción inmediata, guardar el fin nuevo del bimestre 1 antes del inicio nuevo del bimestre 2 choca con la fecha vieja; y la validación por fila de `ModelForm` compara con las fechas viejas de las otras filas. D3: restricción diferida y la validación por fila del cruce apagada en el formulario de la fila; el cruce lo revisa el conjunto con las fechas nuevas de todas las filas.
- **[Cruce que estalla en el `COMMIT`]** → una restricción diferida se comprueba al confirmar, fuera del código de la ficha: daría un 500. D3: `SET CONSTRAINTS ex_periodo_cruce IMMEDIATE` al final de `guardar_periodos`, dentro de un punto de guardado, para que el error salga ahí y se traduzca al mensaje.
- **[Dos guardados a la vez]** → D4: `guardar_periodos` bloquea la institución y el año (`FOR UPDATE`, en ese orden) antes de validar; el panel, la consola y la demo esperan en fila. La restricción de la base queda como red para lo que no pase por el servicio.
- **[Organización que cambia con periodos guardados]** → D5: de solo lectura en la ficha de la institución y rechazada en el servicio; la institución bloqueada en D4 evita la carrera entre las dos fichas.
- **[Migración]** → `institucion/0005` crea la extensión y una tabla nueva, sin tocar datos existentes. Tramo de alto riesgo, solo (grupo 1, parte A).
- **[Demo en el año real, decisión 9]** → los bimestres de ejemplo no se marcan como demo (no hay campo en el doc 11); va a pendientes.md que hay que corregirlos con las fechas reales.

## Goals / Non-Goals

**Goals:**
- Toda regla y toda escritura de periodos en `institucion/servicios.py`; el panel solo arma los datos y llama al servicio.
- Que la base impida número repetido o fuera de 1–4, fin no posterior al inicio y cruce dentro del año.
- Una sola función para saber el periodo de una fecha (`periodo_vigente`), lista para US-020.

**Non-Goals:**
- Pantalla propia fuera del panel de Django, ni mostrar el periodo a la docente o a la dirección.
- Periodos al crear un año: se configuran en la ficha del año ya guardado.
- Cambiar la organización con periodos guardados (si la I.E. cambia de bimestres a trimestres, es otra historia).
- Registrar `Periodo` como pantalla propia del panel: solo vive dentro de la ficha del año.

## Decisions

### D1. Modelo `Periodo` (`institucion/models.py`, migración `0005`)

- `db_table="periodo"`; `anio_escolar` FK `CASCADE`, `related_name="periodos"`; `numero` `PositiveSmallIntegerField`; `fecha_inicio` y `fecha_fin` `DateField`; `ordering = ["numero"]`.
- Restricciones: `uq_periodo (anio_escolar, numero)`, `ck_periodo_numero` (1 a 4), `ck_periodo_fechas` (`fecha_fin > fecha_inicio`) y `ex_periodo_cruce` (D3).
- La migración empieza con `BtreeGistExtension()` (de `django.contrib.postgres.operations`). `django.contrib.postgres` se agrega a `INSTALLED_APPS` solo si Django lo exige para la restricción (se ve en la tarea 1.2).
- **Alternativa descartada:** `DateRangeField` en lugar de dos fechas: se aparta del doc 11 y del formulario de dos campos.

### D2. Reglas de los periodos (`servicios.validar_periodos`)

`validar_periodos(anio, filas)` recibe el año y las filas nuevas (número, inicio, fin) y lanza `ValidationError` con el error en la fila que corresponde. En este orden:

1. Año CERRADO → "El año escolar está cerrado: sus periodos no cambian." (no debería llegar desde el panel, que la muestra de solo lectura).
2. Organización vacía → el aviso de "Organización definida antes".
3. Todas vacías → nada que guardar (válido). Algunas llenas → "Completa las fechas de los N periodos.".
4. Por fila: fin ≤ inicio → "La fecha de fin debe ser posterior a la de inicio."; fuera del año → "Las fechas deben estar dentro de AAAA.".
5. Cruce entre cualquier par (rangos con bordes incluidos) → "Las fechas se cruzan con otro periodo" en la fila de número mayor.
6. Orden: el periodo n+1 empieza después del fin del n → si no, "El periodo n+1 debe empezar después de que termina el periodo n.". Va después del cruce para que un cruce siempre muestre su texto exacto.

Los textos quedan como constantes del módulo (`MENSAJE_CRUCE`, etc.) y las pruebas los comparan.

### D3. Cruce en la base: diferido y comprobado al final del guardado

- `ExclusionConstraint(name="ex_periodo_cruce", expressions=[(Func(F("fecha_inicio"), F("fecha_fin"), Value("[]"), function="DATERANGE", output_field=DateRangeField()), RangeOperators.OVERLAPS), ("anio_escolar", RangeOperators.EQUAL)], deferrable=Deferrable.DEFERRED, violation_error_message=MENSAJE_CRUCE)`. `'[]'` hace los dos bordes inclusivos (decisión de los bordes).
- **Diferida** para que el orden de los `UPDATE` de un mismo guardado no importe. Al final de `guardar_periodos`, dentro de `transaction.atomic()` (punto de guardado): `SET CONSTRAINTS ex_periodo_cruce IMMEDIATE`; un `IntegrityError` con ese nombre se traduce a `ValidationError(MENSAJE_CRUCE)`. Ningún otro `IntegrityError` se traduce.
- El formulario de la fila no corre la validación de `ex_periodo_cruce` (compararía con las fechas viejas de las otras filas): se excluye en la validación de restricciones del formulario de la fila; el cruce lo revisa el conjunto con `validar_periodos`.
- **Alternativa descartada:** borrar y volver a crear los periodos al editar: cambiaría sus id, y las notas (US-020) apuntan al periodo.
- **Alternativa descartada:** solo validación en la aplicación (doc 11): decisión 5.

### D4. Escritura única: `servicios.guardar_periodos(anio, filas, usuario)`

- En `transaction.atomic()`: `Institucion` y `AnioEscolar` con `select_for_update()` (en ese orden, el mismo que usa la ficha de la institución), `validar_periodos` con lo releído, luego crear o actualizar por número (`update_fields=["fecha_inicio", "fecha_fin"]` solo en los cambiados), `SET CONSTRAINTS … IMMEDIATE` (D3) y el registro de actividad (D6).
- La usan el panel (D5) y la demo (D7). Devuelve lo que cambió (creados o editados con sus fechas antes y después), para el registro y para el resumen de la demo.
- Si el servicio lanza `ValidationError` en el guardado (carrera que la validación del formulario no vio), `AnioEscolarAdmin` lo atrapa fuera del `atomic()` de la ficha, ya revertido, y vuelve a mostrar la ficha con el POST y el mensaje como error del conjunto de periodos. No hay 500.
- **Alternativa descartada:** `formset.save()` del panel: escribiría sin bloqueo, sin el registro en la misma llamada y fuera de la regla de "las vistas no escriben".

### D5. Panel (`institucion/admin.py`)

- `PeriodoInline` (`TabularInline`) solo en la ficha de un año guardado (`get_inlines` vacío al crear), con `can_delete = False`, `extra` y `max_num` = N según la organización, el número de solo lectura y puesto por posición (el formset lo asigna a las filas nuevas). Sin organización, no hay inline y la ficha muestra el aviso con el enlace a la institución (campo de solo lectura del año).
- `BaseInlineFormSet` propio: `clean()` llama a `validar_periodos` con las filas del POST; `AnioEscolarAdmin.save_formset` llama a `guardar_periodos` en vez de `formset.save()`.
- Año CERRADO: el inline sin permiso de agregar ni de cambiar (solo lectura). Docente y dirección ya no entran al panel (spec `asignacion-secciones`); se prueba igual con un POST.
- `InstitucionAdmin`: `organizacion_periodos` de solo lectura cuando algún año de la institución tiene periodos; el servicio repite la regla para el POST que la fuerce.
- **Alternativa descartada:** una pantalla propia con HTMX: el usuario es el Administrador y el resto de su trabajo ya está en el panel.

### D6. Registro de actividad

- `Operacion.PERIODOS_CONFIGURADOS` (entidad `anio_escolar`, detalle `{"periodos": N}`) cuando el año pasa de cero a N periodos; `Operacion.PERIODO_EDITADO` (entidad `periodo`, detalle `{"numero", "inicio_antes", "fin_antes", "inicio_despues", "fin_despues"}` en ISO) por periodo cambiado. Las claves van a `DETALLE_PERMITIDO`; no son datos personales (RN-015). Ninguna va a `CUENTAN_KPI_01`.
- Las escribe `guardar_periodos`, no `RegistraEnPanel`: el inline no pasa por `log_change` del año. Si en el mismo POST cambia también el estado del año, queda además ANIO_EDITADO, como hoy.
- `test_catalogo.py` suma los dos escenarios.

### D7. Demo (`institucion/demo.py`)

- `cargar_demo`, dentro de su transacción y después de las secciones, llama a `guardar_periodos(anio, BIMESTRES_EJEMPLO(anio), None)` solo si la organización es BIMESTRE y el año no tiene periodos. Fechas de ejemplo fijas por año: 16-03 a 15-05, 25-05 a 24-07, 10-08 a 09-10 y 19-10 a 18-12 (ficticias; las reales son [DATO I.E. PENDIENTE]).
- `PlanDemo` gana `periodos` (creados, ya tenía o por qué no) y `texto()` lo dice. "Volver a cargar" con las secciones listas y sin periodos crea solo los periodos.
- `quitar_demo` y `descartar_seccion` no cambian: no tocan `periodo`; una prueba lo fija.

### D8. `servicios.periodo_vigente(origen, fecha=None)`

- `origen` es una `Seccion` o un `AnioEscolar`; `fecha` por defecto `timezone.localdate()`. Devuelve el `Periodo` con `fecha_inicio <= fecha <= fecha_fin` o `None`. Una consulta.
- Es la única forma de obtenerlo: US-020 la usa. Las pruebas cubren dentro, los dos bordes, hueco, antes del primero, sin periodos y "hoy en Lima" con el reloj parcheado.

### Datos para la tesis

Esta historia no guarda datos que mida la tesis. `periodo` es la base de RN-002 (una nota por estudiante, competencia y periodo) que US-020 usará para la dimensión 2.

## Migration Plan

- `institucion/0005`: `CREATE EXTENSION IF NOT EXISTS btree_gist` y la tabla `periodo` con sus restricciones. Sin datos que migrar.
- En Vercel, el build corre `migrate` sobre la rama de Neon de la vista previa; si la extensión falla, el build falla y no se publica.
- Vuelta atrás: revertir la migración borra la tabla; la extensión puede quedar (no estorba).

## Open Questions

- Fechas reales de los bimestres 2026 → Nayely con la I.E.; no cambian el diseño (pendientes.md).
