# Propuesta: US-030 – Registrar la asistencia de una jornada

## Why

Con la lista de estudiantes cargada (US-006), la docente aún pasa lista en papel. US-030 (RF-030, prioridad Alta) y US-032 (RF-032) le dejan registrar la asistencia de hoy desde el celular, en el aula y con datos móviles inestables, con un toque por estudiante que se guarda solo y sin jornadas duplicadas. Es la primera pantalla de trabajo de la **dimensión 3 (control de asistencia)** y la primera que guarda datos que mide la tesis (VD – D3: exactitud del control de asistencia).

## What Changes

- **DESIGN.md a la versión 0.4 (dirección visual 0.3)**, en un commit propio y antes de las pantallas (decisión 18). La propuesta de `prototipos-cd` pasa casi tal cual; la corrección de una frase repetida y las secciones que se alinean se explican en design D11.
- **Modelos `Jornada` y `Asistencia`** en `asistencia` (doc 11, 3.6): una jornada por sección y fecha, que nace con el primer toque guardado del día; un estado por estudiante y jornada, con la nota de justificación. La FK hacia estudiante es `RESTRICT` (no `CASCADE` como el doc 11), así que "Quitar" y "Vaciar" de US-006 quedan bloqueados con asistencia real.
- **Estado del estudiante (RN-027):** `estado` (ACTIVO, TRASLADADO, RETIRADO) y `fecha_estado` en `Estudiante`, ACTIVO por defecto. Sin pantalla para cambiarlo.
- **Pantalla "Asistencia" de hoy** (`/docente/secciones/<id>/asistencia/`): ciclo de toques, "Marcar los N restantes como Asistió" con deshacer de 5 s, nota de justificación, avance "N de M marcados", totales, cierre de jornada, fin de semana, sección sin estudiantes, retirados y trasladados al final. Celular en una columna; PC con lista y panel (opción D).
- **Guardado por toque idempotente (RNF-011):** cada toque envía el estado de destino; una sola petición por fila a la vez; reintentos con espera creciente; aviso "Sin conexión" tras 3 fallos seguidos; el lote se envía al ocultar la página; aviso al salir con marcas pendientes; sesión vencida sin perder las marcas en silencio.
- **Marca de actividad de la sesión (Minor 5 de US-002):** se reescribe como mucho cada 30 s, no en cada toque (design D9).
- **Pantallas existentes con la dirección 0.3:** barra con línea tenue (todas); portada con saludo según la hora, fecha delante de la sección, tarjeta Asistencia disponible y la píldora "Hoy: pendiente"; el aviso de éxito de la lista de estudiantes enlaza a "Tomar la asistencia de hoy". El comportamiento de US-001 y US-006 no cambia.

**Fuera de alcance (deuda para la descripción del PR):**
- Días anteriores, registrar un día olvidado, periodo cerrado y registro de actividad (RF-008) → US-031. Deslizar entre días → US-031.
- Historial, totales por periodo e ingresos tardíos (RN-012) → US-033. Exportación → US-034.
- Pantalla para cambiar el estado de un estudiante → según lo que confirme la I.E. (Nayely).
- Cabeceras con franjas de Sesiones y Notas → cuando existan esas pantallas.
- Dos dispositivos marcando la misma fila a la vez: gana el último que llega (design D3).

**Contradicciones que solo se mencionan (documentos congelados):**
- Doc 11: `asistencia.estudiante_id` en cascada → `RESTRICT`.
- `asistencia.actualizado_en`: no está en el doc 11; se agrega para medir la duración de la toma (design, Datos para la tesis).
- Doc 06 / doc 02 (US-030): el criterio dice "Marcar todos como Asistió"; el texto es "Marcar los N restantes como Asistió" y marca solo a los Sin marcar (decisión 3).
- Doc 06 (RF-031): la nota de justificación es de US-031; entra en US-030 (decisión 1).

## Capabilities

### New Capabilities

- `asistencia-jornada`: registro de la asistencia de hoy de una sección: jornada única por sección y fecha, ciclo de estados, "Marcar los N restantes" con deshacer, nota de justificación, avance y totales, cierre de jornada, guardado por toque tolerante a cortes, fin de semana, estudiantes no activos y acceso solo a su sección.

### Modified Capabilities

- `pantallas-de-inicio`: "Portada del docente" (saludo según la hora, fecha y la píldora "Hoy: pendiente") y "Disponibilidad de cada dimensión" (Asistencia disponible con una sola sección).
- `estudiantes-seccion`: "Estudiantes de una sección" (estado y fecha de estado, RN-027), "Pegar lista" (el aviso de éxito enlaza a la asistencia de hoy). "Quitar y vaciar" no cambia: su bloqueo pasa a probarse con asistencia real.

## Impact

- **Código:**
  - `src/backend/asistencia/`: `models.py`, migración `0001`, `servicios.py`, `views.py`, `urls.py` (nuevo), plantillas en `templates/asistencia/` y pruebas.
  - `src/backend/institucion/`: `models.py` (estado del estudiante), migración `0004`, `servicios.py` (activos e inactivos).
  - `src/backend/cuentas/`: `dimensiones.py` y `views.py` (tarjeta Asistencia, saludo, píldora), `middleware.py` (D9), `portada_docente.html` y `tarjeta_dimension.html`; `templates/marco.html` (barra); `_lista.html` de estudiantes (enlace del aviso).
  - `src/backend/static/js/asistencia.js` (nuevo) y `src/frontend/css/app.css`. Íconos nuevos en `templates/iconos/` (`chevron-left`, `chevron-right`).
- **Dependencias:** ninguna nueva. La pantalla de asistencia no carga HTMX ni Alpine (design D4).
- **Migraciones:** `institucion/0004` (estado del estudiante) y `asistencia/0001` (jornada y asistencia).
- **Rutas:** tres nuevas bajo `/docente/secciones/<id>/asistencia/`; se actualiza el Catálogo de rutas de `docs/03`. El README no cambia.
- **Documentos:** `DESIGN.md` sube de versión (D11).
- **Requisitos:** US-030, US-032, RF-030, RF-032, RN-011, RN-012, RN-023, RN-025, RN-026, RN-027, RNF-005, RNF-008, RNF-011, doc 11 (3.2 y 3.6). DoD 1 a 9.
- **Rama:** `feature/US-030-registrar-asistencia`, desde `main`. Su primer commit ya es el archivo de US-006.
