# Propuesta: US-040 – Consultar los consolidados (+ T-04, Pizarra neutra, portada aprobada y DESIGN.md 1.2)

## Why

Hoy la dirección entra a un inicio con «Consolidados» en estado vacío: para saber qué secciones van atrasadas en notas, asistencia o sesiones tiene que pedir documentos físicos. Con este cambio la dirección ve, por bimestre, el estado de las secciones del año ABIERTO y entra al detalle de cada una en solo lectura (RF-040, transversal: **dirección**; mira las tres dimensiones de la tesis: planificación de sesiones, registro de notas y control de asistencia). En el mismo PR, por la decisión 1 de `insumos/US-040/decisiones.md` (excepción a «una rama por historia», declarada en el PR): el botón de tema (T-04), el oscuro Pizarra neutra, la portada aprobada de la docente y DESIGN.md 1.2.

## What Changes

Se aplican tal cual las decisiones 1 a 19 de `insumos/US-040/decisiones.md` y los bocetos de `prototipos-cd/US-040-final` (LEEME.md y `enmienda-design.md` mandan sobre el CSS compilado). Lo nuevo de este propose:

- **Rutas de la dirección** (design D2): `direccion/consolidados/`, `direccion/consolidados/secciones/<id>/{notas,asistencia,sesiones}/` y la página de una sesión con su descarga y vista en `direccion/sesiones/<uuid>/…`. Periodo, área, filtro, semana, día y docente van como parámetros GET: todo funciona sin JavaScript.
- **Qué sesiones son de una sección** (design D6): las de la tutora para el grado de la sección, sin el material de referencia. Las del docente de curso (áreas a su cargo, para ese grado) van aparte, bajo «Docentes de curso de <grado> · <día>», y nunca se atribuyen a la sección: no suman en la semana ni en el café. Es provisional: el docente de curso no tiene sección asignada en el modelo y se reconoce por el área de la sesión. Sin chips por docente.
- **Página de la sesión de la dirección** (design D2, D7): una plantilla parcial compartida con la página de la docente (datos, propósito, vista previa, Descargar y Ver), sin Eliminar ni Compartir.
- **«Días sin completar»** (design D5): días de lunes a viernes del bimestre hasta **ayer** (o hasta su fin, si ya terminó) con estudiantes activos ese día y la jornada incompleta o sin tomar. Hoy no cuenta como atrasado mientras se toma; sí cuenta en los «días de clase» del detalle y de Sesiones.
- **La dirección ve todas las sesiones propias de su institución**, compartidas o no (RN-019: «visible para todos los docentes y la dirección»); su visita no suma a «Colegas que la vieron» (design D7).
- **Bimestre futuro**: en la tira no se elige; pedirlo abre el vigente, como en la hoja de notas. Antes del primer bimestre, Consolidados y la banda dicen cuándo empieza, sin mapa ni café (design D4).
- **0 secciones atrasadas**: la banda va sin pastilla (design D9).
- **Totales de asistencia por periodo** en un servicio nuevo de `asistencia` que US-033 reutilizará (zona de cuidado).
- **Reglas de plantillas** (`.claude/rules/plantillas.md`): se actualizan con DESIGN.md 1.2 (Besley en cuatro lugares; T-04 ya existe).

**Fuera de alcance:**
- Marcar las notas como entregadas, estado de entrega y habilitar correcciones → US-026 + US-042 (la tarjeta Entregas y la opción del ☰ quedan en «Próximamente»).
- Descarga de consolidados → US-041.
- Tipo de documento al subir y el bloque «Plan anual y unidades»; la regla de semanas para «Mis sesiones» (`decision-sesiones.md`) → historia nueva, después de la respuesta de Nayely.
- Días exactos de las faltas de un estudiante → historia futura.
- Material de referencia en el detalle de la dirección → no entra.

**Contradicciones que solo se mencionan (van a la deuda):**
- T-04 no tiene RF en el doc 06 (congelado): pasada de docs.
- El escenario «Caso de error» de US-040 («intenta modificar una nota o una asistencia») no tiene interfaz: se cubre con la matriz de permisos (los guardados de la dirección no se guardan).
- Los totales heredan las deudas de US-031 (`fecha_estado` vacía, ingresos tardíos RN-012).

## Capabilities

### New Capabilities

- `consolidados-direccion`: Consolidados (mapa de secciones por bimestre, resumen de la I.E.), detalle de sección en solo lectura (Notas, Asistencia, Sesiones), reglas de datos (al día, atrasada, % de asistencia, días sin completar), acceso solo de la dirección de la institución, accesibilidad y 360 px.

### Modified Capabilities

- `pantallas-de-inicio`: «Portada del docente» (nombre en Besley, miniatura calendario de Asistencia), «Inicio de la dirección» (portada nueva), «Marco común» (☰ en los interiores de la dirección, tema en todas las barras), «Temas claro y oscuro» (T-04 y Pizarra neutra), «Accesibilidad en ambos temas» (pantallas nuevas y repaso del oscuro en todas); ADDED «Navegación de la dirección».
- `detalle-sesion`: «Quién ve una sesión» y «Colegas que la vieron» suman a la dirección; ADDED «Sesión abierta por la dirección».
- `repositorio-sesiones`: «Listas solo del rol Docente» dice dónde ve la dirección las sesiones.
- `envio-sesiones`: «Solo el rol Docente» dice que la sesión enviada queda visible para la dirección (RN-019).
- `acceso-secciones`: «Matriz de permisos de lo construido» suma las rutas de la dirección.

## Impact

- **Código:**
  - `DESIGN.md` 1.2 y `.claude/rules/plantillas.md`.
  - `src/frontend/css/rebrand/` (tokens oscuros, papel atenuado, botón de tema, portada y pantallas de la dirección) y un `static/js/tema.js` nuevo, cargado en `<head>` antes del CSS.
  - `templates/base.html`, `marco.html`, `cuentas/ingresar.html`, `cuentas/portada_docente.html`, `rb/miniatura_asistencia.html`; `templates/direccion/` (portada, consolidados, detalle y página de sesión).
  - `cuentas/dimensiones.py` (`navegacion_direccion`) y `cuentas/templatetags/marco.py`; `cuentas/views.py` (contexto de la miniatura).
  - `direccion/servicios.py` (nuevo: estado de las secciones, resumen de la I.E., sesiones de la sección), `direccion/views.py`, `direccion/urls.py`.
  - `notas/servicios.py` (faltantes y distribución por sección sin usuario), `asistencia/servicios.py` (totales y días sin completar por periodo), `repositorio/servicios.py` (visibilidad para la dirección).
- **Rutas:** las de D2 (GET). Cambia el Catálogo de rutas de `docs/03`.
- **Base de datos:** sin migraciones.
- **Requisitos:** US-040, RF-040, RN-019, RNF-005, RNF-008, RNF-013, RNF-017, T-04. DoD 1 a 9.
- **Rama:** `feature/us-040-consultar-consolidados`, desde `main` con US-031 archivada.
