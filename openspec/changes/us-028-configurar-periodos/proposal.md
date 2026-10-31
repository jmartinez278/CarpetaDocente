# Propuesta: US-028 – Configurar los periodos del año escolar

## Why

Para registrar notas (US-020) el sistema tiene que saber en qué bimestre está, sin que la docente lo elija. US-028 (RF-028, prioridad Alta) le da al Administrador la forma de poner las fechas de los periodos del año escolar y de corregirlas si la I.E. las mueve. Es parte de la **dimensión 2 (registro y control de notas)**: no guarda todavía datos que mida la tesis, pero es la base de la nota por periodo (RN-002).

## What Changes

Las decisiones 1 a 9 de `insumos/US-028/decisiones.md` se aplican tal cual. Lo nuevo de este propose:

- **Ficha del año escolar con sus periodos** (solo en la ficha de un año guardado, no al crearlo): las N filas se guardan todas o ninguna; el número de cada fila lo pone el sistema y no se edita.
- **Mensajes de las validaciones** que decisiones.md no fija: ver el spec `periodos-anio-escolar`. Cuando un cruce es también un desorden, gana el mensaje del cruce (el texto exacto del criterio).
- **Restricción de exclusión diferida** (`DEFERRABLE INITIALLY DEFERRED`) y comprobada al final del guardado: así correr dos periodos a la vez no la dispara a medias, y un cruce real llega al formulario y no al `COMMIT` (design D3).
- **Todas las escrituras de periodos pasan por `servicios.guardar_periodos`**, también la demo, con el año y la institución bloqueados: el panel, la consola y la demo quedan en fila (design D4).
- **Demo:** crea los 4 bimestres de ejemplo solo si la organización es BIMESTRE y el año no tiene periodos; si no, lo dice en su resumen y sigue (ajuste a la decisión 9, en tasks.md).

**Fuera de alcance (deuda para la descripción del PR):**
- Mostrar el periodo en curso a la docente o la dirección → US-020 / US-029.
- Que la pantalla de notas use `periodo_vigente` → US-020 (aquí se prueba la función).
- Entrega y bloqueo de notas por periodo (RN-022) → historia de entrega de notas (US-026).
- KPI-03/04 con jornadas lectivas y cierre de periodo → US-040. Cierre del año (RF-009) → US-009.
- Fechas reales de los bimestres 2026 → Nayely con la I.E. [DATO I.E. PENDIENTE].

**Contradicciones que solo se mencionan (documentos congelados):**
- Doc 11, 3.1: "que no se crucen lo valida la aplicación" → también la base (decisión 5).
- Doc 11: la restricción de cruce no está en el DDL; tampoco la extensión `btree_gist`.

## Capabilities

### New Capabilities

- `periodos-anio-escolar`: periodos de un año escolar (número y fechas), su configuración y edición en la ficha del año del panel, la regla de organización de la institución, las validaciones (cruce, año calendario, orden), el año cerrado de solo lectura y `periodo_vigente` como única forma de obtener el periodo de una fecha.

### Modified Capabilities

- `registro-actividad`: "Catálogo cerrado de operaciones" suma PERIODOS_CONFIGURADOS y PERIODO_EDITADO, que no cuentan para KPI-01.
- `datos-demostracion`: "Cargar la demostración" crea los 4 bimestres de ejemplo si el año no tiene periodos; "Quitar la demostración" no los borra.

## Impact

- **Código:**
  - `src/backend/institucion/`: `models.py` (`Periodo`), migración `0005` (extensión `btree_gist` y tabla `periodo`), `servicios.py` (`validar_periodos`, `guardar_periodos`, `periodo_vigente`), `admin.py` (periodos en la ficha del año; organización de solo lectura con periodos), `demo.py` y pruebas.
  - `src/backend/actividad/`: `models.py` (dos operaciones; migración si cambian las `choices`), `servicios.py` (`DETALLE_PERMITIDO`) y `tests/test_catalogo.py`.
- **Dependencias:** ninguna de Python. Extensión de PostgreSQL `btree_gist` (viene con `postgres:17` y Neon la ofrece): se comprueba en local, en la CI y en la vista previa del PR antes de construir encima.
- **Rutas:** ninguna nueva (todo es el panel de Django). El README y el Catálogo de rutas de `docs/03` no cambian.
- **Requisitos:** US-028, RF-028, RN-002 (base), RN-006, RN-023, RNF-016, doc 11 (3.1). DoD 1 a 9.
- **Rama:** `feature/US-028-configurar-periodos-del-año-escolar`, desde `main`; el archivo de US-008 ya está en `main`.
