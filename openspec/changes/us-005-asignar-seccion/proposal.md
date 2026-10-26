# Propuesta: US-005 – Asignar grado y sección a un docente

## Why

Hoy no existen el año escolar ni las secciones: la portada del docente no sabe qué aula le toca y US-006 (importar estudiantes) no tiene dónde colgar a los estudiantes. US-005 (RF-005, prioridad Alta) deja al Administrador asignar a cada docente su grado y sección, para que el docente la vea al iniciar sesión.

## What Changes

- **Modelos nuevos** en `institucion` (doc 11, 3.1 y 3.2; doc 12: el módulo `institucion` atiende RF-005):
  - `AnioEscolar`: institución, año y estado (ABIERTO o CERRADO). Sin los campos de cierre de RF-009 ni los periodos. Un solo año ABIERTO por institución, con restricción en la base de datos (D5).
  - `Seccion`: año escolar, grado (1 a 6), nombre y docente de aula opcional.
- **Panel de Django** para el año escolar y las secciones (D1). El docente se elige en la ficha de la sección, con la etiqueta "Docente de aula", entre las cuentas activas con rol Docente de la institución del año.
- **Regla de D3:** si la sección ya tiene otro docente guardado, se muestra "La sección ya tiene un docente asignado" y no se guarda nada. Vale para cualquier vía (panel, servicio u ORM). El cambio de sección se hace en dos pasos: dejar vacía la sección anterior y asignar la nueva. Un docente puede tener varias secciones.
- **Comando `cargar_secciones`** (D4): recibe el año y la institución, crea el año ABIERTO si no existe y los grados 1 a 6 con las secciones A, B, C y D. Es idempotente: si se repite, no duplica e informa que no creó nada. Sin docentes ni datos personales.
- **Portada del docente** (D2): una línea bajo el saludo, fuera del `h1`, con "2.º grado, sección A". Varias secciones: separadas por " · ", por grado y nombre. Sin sección: "Tu sección aparecerá cuando el administrador la asigne." Solo cuenta el año ABIERTO. Las tarjetas no cambian.
- **Escenarios del criterio:** el ejemplo "2.° grado, sección única" pasa a "2.º grado, sección A" (datos de C8: grados 1 a 6, secciones A a D, sin multigrado).
- **Pruebas primero (TDD)** para los tres escenarios del criterio y los que agrega el spec `asignacion-secciones`.

**Fuera de alcance (deuda para la descripción del PR):**
- Docentes de área (Educación Física, Inglés, Computación): su relación por área queda para otra historia. Mientras tanto no se crean cuentas para ellos.
- Campos de cierre del año (RF-009) y periodos (RF-028).
- La prueba de que los estudiantes siguen en la sección original al cambiar de docente queda para US-006.

**Contradicciones que solo se mencionan (documentos congelados):**
- Doc 02/01 y RF-005 usan "2.° grado, sección única" (signo de grado U+00B0); el spec usa "2.º grado, sección A" (ordinal U+00BA). DESIGN.md también escribe "3.° grado" en sus ejemplos.
- DESIGN.md, "Estado vacío", pide ícono de línea y frase; D2 fija solo la línea de texto bajo el saludo.
- Doc 11: `anio_escolar` no tiene la restricción de un solo año ABIERTO, y la sección 8.1 no lista las tablas nuevas.

## Capabilities

### New Capabilities

- `asignacion-secciones`: año escolar abierto único por institución, secciones del año con su docente de aula, la regla de un docente por sección, el panel del Administrador y la carga inicial con `cargar_secciones`.

### Modified Capabilities

- `pantallas-de-inicio`: "Portada del docente" agrega la línea de la sección bajo el saludo.

## Impact

- **Código:**
  - `src/backend/institucion/`: `models.py`, migración `0002`, `servicios.py` (nuevo: regla de D3, carga y texto de las secciones), `admin.py`, `management/commands/cargar_secciones.py` y pruebas.
  - `src/backend/cuentas/views.py` y `templates/cuentas/portada_docente.html` (línea de la sección).
- **Dependencias:** ninguna. **Migraciones:** `institucion/0002` (tablas `anio_escolar` y `seccion`).
- **Rutas:** ninguna nueva ni cambiada; el Catálogo de rutas no se toca. El README suma `cargar_secciones` en "Configuración local", porque cambia cómo se preparan los datos.
- **Requisitos:** US-005, RF-005, doc 11 (3.1 y 3.2), RNF-005. DoD 1 a 9, con la DoD 4 sin aplicar hasta EN-02.
- **Rama:** `feature/US-005-asignar-seccion`, desde `main`. Su primer commit ya es el archivo de US-003.
