# Propuesta: US-020, US-021 y US-022 – Hoja de notas por área

## Why

La tutora pasa hoy sus niveles de logro al Excel del SIAGIE (RegNotas), área por área. US-020 (RF-020), US-021 (RF-021) y US-022 (RF-022), todas de prioridad Alta, llevan ese registro al sistema en una sola pantalla: la hoja de notas del área, con la conclusión descriptiva y el aviso de las notas faltantes. Es la **dimensión 2 (registro y control de notas)** y llena por primera vez dos datos que mide la tesis: los docentes activos (KPI-01) y las «secciones con notas» de Indicadores. Se libera junto con US-029: se activa la bandera de Notas en la portada.

## What Changes

Se aplican tal cual `insumos/US-020/decisiones.md` (que incluye US-021) y `insumos/US-022/decisiones.md`, con el boceto `C:\Proyectos\prototipos-cd\US-020\` (estados 01 a 21) como iteración más reciente. Donde chocan, manda el boceto (design, «Choques resueltos»). Lo nuevo de este propose:

- **El bimestre se elige en Competencias**, no en Notas (boceto, frente a D8 de US-020). Notas muestra el periodo («B3 · Vigente») y el botón «Competencias». Competencias suma «Registrar notas de B*n*» y el aviso de periodo sin competencias confirmadas. Sin vigente (vacaciones), Notas abre el último periodo pasado.
- **La conclusión va detrás de un icono junto a la celda**, no en una columna (boceto, frente a D9 de US-020).
- **Una nota cambiada desde otro dispositivo no se pisa sin aviso**: cada celda del borrador guarda lo que la docente vio guardado. Si al abrir la hoja o al guardar la nota de la base ya es otra, la celda lo avisa y el guardado no guarda nada hasta que la docente lo revisa (design D7).
- **Envío repetido idempotente**: si llega de nuevo un guardado que ya se aplicó, no cambia nada ni deja otra entrada de actividad (design D6).
- **NOTAS_GUARDADAS sin niveles en el detalle**: área, periodo, cuántas notas se crearon y qué celdas cambiaron (identificadores de estudiante y competencia), sin el nivel anterior ni el nuevo, por la regla «Detalle sin datos personales» de `registro-actividad` (decisión del equipo en este propose, frente a D16 de US-020).
- **Cerrar sesión borra los borradores de la cuenta** desde cualquier pantalla, y el diálogo de salida lo dice cuando la salida es «Cerrar sesión».
- **Textos del boceto** para el error de red y la conclusión faltante, no los del criterio (decisión del equipo en este propose). Los textos de US-022 van exactos.
- **La tira de áreas se desplaza en horizontal dentro de su contenedor**, como en el boceto (decisión del equipo en este propose), aunque RNF-005 solo exceptúa el carrusel de la portada.
- **Demo**: quitar la demostración y descartar una sección también borran sus notas. La carga no crea notas.

**Fuera de alcance (deuda para la descripción del PR):**
- Registro completo de solo lectura → US-023. Exportar → US-024/025. Entrega y bloqueo (RN-022) → US-026. Exonerados (RN-010) → US-035; hasta entonces cuentan como faltantes. Estado por docente → US-042. Docentes de curso → historia nueva, sin ID. Pegar desde Excel → Mejoras del flujo.
- Conteo y lista de faltantes de todo el bimestre, y aviso en la portada → si el piloto lo pide (US-022).
- Notas de ejemplo en la demostración → si el equipo lo pide.
- Una nota cambiada desde otro dispositivo se avisa al abrir la hoja o al guardar; no se avisa en vivo.

**Contradicciones que solo se mencionan (documentos congelados, van a la deuda):**
- RN-003, `ck_calificacion_c` (doc 11) y el criterio de US-021 piden la conclusión solo en C y opcional en AD, A y B; aquí es obligatoria en B y C y no se guarda en AD ni A (D2 de US-020).
- Doc 11, 3.5: `calificacion.estudiante_id` es CASCADE; aquí es RESTRICT, como la asistencia (D3 de US-020).
- Criterios de US-020 (red) y US-021 (C sin conclusión): textos exactos distintos de los del boceto.
- RNF-005 y `.claude/rules/plantillas.md`: la tira de áreas se desplaza en horizontal.
- D16 de US-020: el detalle sin «de → a».

## Capabilities

### New Capabilities

- `registro-notas`: la hoja de notas por área y periodo: acceso, columnas y filas, edición en PC y celular, conclusión en B y C, relleno de vacías, guardado todo o nada con validación de escala y conclusión, borradores en el dispositivo, cambios desde otro dispositivo, salida sin guardar y faltantes («Faltan N notas», «Pendientes de registro», área completa).

### Modified Capabilities

- `competencias-periodo`: el acceso ya no dice que nada enlaza la pantalla; «No desmarcar una competencia con notas» y «Competencias obligatorias en el último periodo» se calculan con las notas reales; nuevo requisito «Ir a las notas del periodo» («Registrar notas de B*n*» y el aviso de periodo sin competencias confirmadas).
- `pantallas-de-inicio`: «Disponibilidad de cada dimensión» suma Notas, con la misma regla de sección única que Asistencia.
- `registro-actividad`: «Catálogo cerrado de operaciones» suma NOTAS_GUARDADAS, que cuenta para KPI-01; nuevo requisito «Guardado de notas».
- `indicadores-adopcion`: «Jornadas registradas» deja de mostrar «—» en «secciones con notas».
- `datos-demostracion`: quitar la demostración y descartar una sección borran y cuentan las notas.

## Impact

- **Código:**
  - `src/backend/notas/`: `Calificacion` y su migración, servicios de la hoja (incluidos `notas_faltantes`, `tiene_notas` y `competencias_obligatorias` con notas), vistas, rutas nuevas y pruebas.
  - `src/backend/actividad/`: NOTAS_GUARDADAS, su detalle, `CUENTAN_KPI_01`, «secciones con notas» y su migración de `choices`.
  - `src/backend/cuentas/dimensiones.py`: bandera de Notas.
  - `src/backend/institucion/demo.py`: borrado y conteo de notas.
  - `config/urls.py`, `templates/notas/`, `templates/componentes/menu_cuenta.html`, `static/js/` (hoja y borrado de borradores al cerrar sesión), `src/frontend/` (CSS).
- **Rutas:** `/docente/secciones/<id>/notas/` (GET) y `/docente/secciones/<id>/notas/<N>/<área>/` (POST). Se actualiza el Catálogo de rutas de `docs/03`. El README no cambia.
- **Dependencias:** ninguna.
- **Requisitos:** US-020, US-021, US-022, RF-020 a RF-022, RN-001, RN-002, RN-004, RN-005, RN-015, RN-023, RN-027, RNF-002, RNF-005, RNF-011, RNF-015, doc 11 (3.5). DoD 1 a 9.
- **Rama:** `feature/us-020-021-022-registrar-notas`, desde `main`; su primer commit (archivo de US-029) ya está.
