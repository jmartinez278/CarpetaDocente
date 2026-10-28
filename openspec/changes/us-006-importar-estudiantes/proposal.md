# Propuesta: US-006 – Importar la lista de estudiantes de una sección

## Why

Desde US-005 la docente ve su sección, pero la sección no tiene estudiantes: la asistencia (US-030) y las notas no tienen a quién registrar. US-006 (RF-006, prioridad Alta) deja a la docente cargar la lista de su sección una sola vez, pegándola desde su Excel o agregando a cada estudiante, y corregirla después.

## What Changes

- **Modelo `Estudiante`** en `institucion` (doc 11, 3.2; doc 12: `institucion` atiende RF-006): sección, apellidos y nombres (120 caracteres), con la restricción única (sección, apellidos, nombres). Los nombres se guardan en mayúsculas y sin espacios de más.
- **Diálogo "Estudiantes de 2.º A"** abierto desde "Ver estudiantes →" en la portada, con sus vistas: lista vacía, lista, Agregar, Editar, Pegar lista, Revisar lista y las confirmaciones de quitar y vaciar. Cada vista tiene su dirección y, sin JavaScript, se abre como página completa. Primera pantalla con HTMX.
- **Pegar lista:** una línea por estudiante, "APELLIDOS, NOMBRES", hasta 60. Con cualquier error no se guarda nada, se conserva el texto y se lista cada línea con su motivo. Las líneas en blanco se ignoran; una línea con tabulaciones es un error.
- **Agregar, editar, quitar y vaciar.** Quitar y vaciar solo si ningún estudiante afectado tiene asistencia ni notas.
- **Portada:** con una sola sección en el año ABIERTO, "Ver estudiantes →" junto a su línea y el aviso "Tu sección aún no tiene estudiantes" mientras falte la lista. Con varias secciones (no existe en la I.E., C8) no hay enlace; la línea de US-005 no cambia.
- **Pegar lista solo con la sección vacía:** con estudiantes, los que falten se agregan uno por uno.
- **Sesión vencida con el diálogo abierto:** la pantalla completa va a `/ingresar/`; el diálogo no muestra el formulario de ingreso adentro.
- **Escenarios del criterio:** "importa una hoja de cálculo" pasa a "pega las filas copiadas de una hoja de cálculo" (decisión del grill; se explica en "Para quien revise").

**Fuera de alcance (deuda para la descripción del PR):**
- Estados Retirado y Trasladado (RN-027) → US-030; historial de cambios → RF-008; OCR y subir un archivo de Excel → después; código de estudiante (RN-015) → cuando el formato de la UGEL lo pida.
- Números de línea con enlace que seleccionan la línea en el cuadro de texto (boceto, `estudiantes.js`).
- "Atrás" vuelve a la vista anterior del diálogo (solo si EN-07 lo pide).
- Denegación con mensaje y registro al pedir la sección de otra docente → US-004 (aquí, 404).

**Contradicciones que solo se mencionan (documentos congelados):**
- RF-006 y doc 02/01: "importa una hoja de cálculo con la estructura de columnas indicada"; el spec dice "pega las filas copiadas". El dato pendiente "Columnas de la nómina" (doc 06, 5) deja de bloquear: basta una columna.
- Doc 11: `ON DELETE CASCADE` de calificación, asistencia y exoneración hacia estudiante; cuando se creen esas tablas, la FK será `RESTRICT`. `estado`, `fecha_estado` y `codigo_estudiante` no se crean en US-006.
- DESIGN.md: no define el diálogo ni la excepción de mayúsculas para los nombres de estudiantes.

## Capabilities

### New Capabilities

- `estudiantes-seccion`: lista de estudiantes de la sección de la docente: pegar lista con su validación por línea, agregar, editar, quitar, vaciar, el diálogo y sus vistas, el acceso solo a sus secciones y la sesión vencida con el diálogo abierto.

### Modified Capabilities

- `pantallas-de-inicio`: "Portada del docente" agrega, con una sola sección, "Ver estudiantes →" y el aviso de la sección sin estudiantes; sus escenarios de US-005 no cambian.

## Impact

- **Código:**
  - `src/backend/institucion/`: `models.py` (`Estudiante`), migración `0003`, `servicios.py` (lectura del texto pegado, validación y escritura), `views.py`, `urls.py` (nuevo), plantillas en `templates/institucion/estudiantes/` y pruebas.
  - `src/backend/cuentas/`: `views.py` (contexto de la portada), `middleware.py` y `acceso.py` (sesión vencida en una petición de HTMX), `portada_docente.html`.
  - `src/backend/config/urls.py`, `src/backend/static/js/estudiantes.js` (nuevo) y `src/frontend/css/app.css` (componentes del diálogo).
- **Dependencias:** ninguna nueva. HTMX 2 ya se copia con `npm run build`; la portada lo carga por primera vez.
- **Migraciones:** `institucion/0003` (tabla `estudiante`).
- **Rutas:** seis nuevas bajo `/docente/secciones/<id>/estudiantes/`; se actualiza el Catálogo de rutas de `docs/03`. El README no cambia.
- **Requisitos:** US-006, RF-006, RN-014, RN-015, RN-023, doc 11 (3.2), RNF-005 y RNF-008. DoD 1 a 9.
- **Rama:** `feature/US-006-importar-estudiantes`, desde `main`. Su primer commit ya es el archivo de EN-02.
