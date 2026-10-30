# Propuesta: EN-06 – Catálogo curricular y datos ficticios

## Why

Las notas (US-020 a US-022), los periodos (US-028) y la pantalla del catálogo (US-027) necesitan que existan las áreas y competencias de primaria tal como la docente las ve en el registro de notas del SIAGIE. Además, el equipo necesita mostrar el aplicativo con secciones llenas sin usar datos reales (RN-018) y poder liberarlas cuando cada docente de la muestra cargue su propia lista. EN-06 cubre la base de RF-027 (dimensión 2: registro y control de notas) y prepara las demostraciones de la dimensión 3 (control de asistencia).

## What Changes

- **Modelos `Area`, `Competencia` e `InstitucionArea`** en la app `catalogo` (doc 11, 3.3), con el campo nuevo `area.codigo_siagie`.
- **Migración de datos** que carga las 11 áreas del SIAGIE y sus 30 competencias, con `es_transversal` y `admite_exoneracion` (design D2, D3).
- **Áreas de cada institución:** al migrar y al crear una institución nacen sus filas de `institucion_area`; todas «se trabaja» salvo Castellano como segunda lengua (design D4).
- **Panel de administración** del catálogo, sin agregar ni borrar (design D5).
- **Tres comandos de datos ficticios** (design D6 a D9): `cargar_demo` (8 secciones con docente demo, 25 estudiantes y 10 días de asistencia), `quitar_demo` (su inverso) y `descartar_seccion` (borra lo cargado en una sección del piloto).
- `.env.example`: variable `DEMO_CLAVE`, sin valor.

**Fuera de alcance:**
- Pantalla del catálogo y alta de áreas o competencias → US-027. Periodos → US-028. Notas → US-020/021/022.
- Periodos y notas en los comandos de la demo y del descarte → US-028 y US-020 (va en sus tareas).
- Desactivar la cuenta del piloto → US-003. Exportar al SIAGIE → historia de exportación de notas.
- Conclusión descriptiva en B frente a la RN-003 → US-021.

**Contradicciones que solo se mencionan (documentos congelados):**
- Doc 09 §3 y doc 11 §6: 10 áreas del Anexo 03 → 11 bloques del SIAGIE, con sus nombres, su orden y el texto de sus competencias; `codigo_siagie` no está en el doc 11.
- Doc 02 (EN-06): «se ejecuta la carga de datos iniciales» → el catálogo lo carga la migración.
- Doc 11 §6: `institucion_area` [DATO I.E. PENDIENTE] → cerrado por la decisión 5.
- Doc 11: `competencia` dice «UQ con area_id» pero no `orden`; no se agrega restricción de orden (design D2).

## Capabilities

### New Capabilities

- `catalogo-curricular`: áreas y competencias de primaria del SIAGIE, cargadas al migrar; áreas que trabaja cada institución; mantenimiento en el panel sin borrar.
- `datos-demostracion`: secciones de demostración con docente, estudiantes y asistencia ficticios, su retiro, y el descarte de lo cargado en una sección del piloto.

### Modified Capabilities

Ninguna. «Quitar y vaciar» de `estudiantes-seccion` sigue bloqueado con registros; el descarte es un comando del equipo, no de la docente.

## Impact

- **Código:**
  - `src/backend/catalogo/`: `models.py`, migraciones `0001` (esquema) y `0002` (datos), `servicios.py`, `signals.py`, `apps.py`, `admin.py` y pruebas.
  - `src/backend/institucion/`: `demo.py` (servicios de datos ficticios) y los comandos `cargar_demo`, `quitar_demo` y `descartar_seccion` en `management/commands/`.
  - `.env.example` (`DEMO_CLAVE`).
- **Dependencias:** ninguna nueva.
- **Migraciones:** `catalogo/0001` y `catalogo/0002`; se aplican también en el build de Vercel.
- **Rutas:** ninguna nueva (solo el panel). El README cambia: cómo cargar y quitar la demo.
- **Requisitos:** EN-06, RF-027 (base), RN-007, RN-008, RN-010, RN-018, RN-023, doc 11 (3.3 y 6). DoD 1 a 9.
- **Rama:** `feature/EN-06-datos-iniciales`, desde `main`. Su primer commit ya es el archivo de US-030.
