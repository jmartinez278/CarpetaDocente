# Propuesta: US-008 – Registrar la actividad de los usuarios

## Why

Hoy nada deja constancia de quién hizo cada cosa: si una docente dice "yo sí marqué la asistencia", no hay cómo comprobarlo, y el equipo no puede medir en el piloto si las docentes usan el sistema (KPI-01 del documento 03). US-008 (RF-008, prioridad Media; RNF-016) guarda quién, qué y cuándo en cada operación que crea, modifica o elimina datos, y da al Administrador la consulta, la exportación y los indicadores por semana en el panel. Es **transversal (usuarios y acceso)**; sus datos alimentan los indicadores de adopción y sirven de apoyo a la **dimensión 3 (control de asistencia)**.

## What Changes

Las decisiones de `insumos/US-008/decisiones.md` (1 a 12) se aplican tal cual. Lo nuevo de este propose:

- **Catálogo ampliado para cumplir la decisión 12 con lo ya construido:** el panel hoy permite dar de alta y editar instituciones, años escolares y secciones (grado y nombre), y `cargar_secciones` crea secciones; ninguna de esas escrituras estaba en la lista inicial. Se agregan `INSTITUCION_CREADA`, `INSTITUCION_EDITADA`, `ANIO_CREADO`, `ANIO_EDITADO`, `SECCION_CREADA` y `SECCION_EDITADA` (design D3).
- **Dos caminos de escritura del panel que se cierran en vez de registrarse:** borrar una institución (hoy permitido, borra en cascada; los demás modelos ya lo prohíben por RN-023) y los grupos de Django (el sistema no los usa, RF-003 los esconde). Design D4.
- **Desbloquear una cuenta** queda como `CUENTA_EDITADA` con el campo "desbloqueo", sin una operación propia. **Reactivar** una cuenta también es `CUENTA_EDITADA`.
- **Origen "deshacer" de ASISTENCIA_CAMBIADA:** el "Deshacer" de US-030 ocurre en el navegador, antes de enviar el lote; al servidor nunca llega. El origen queda en `toque` o `lote` (design D6).
- **JORNADA_COMPLETA** se registra cuando la jornada pasa a tener a todos los activos marcados, una sola vez por jornada (US-030 no tiene botón de cierre).
- **Cuentas demo:** se excluyen por la marca `es_demo` (EN-06, corrección del PR #66), no por prefijo.
- **Indicadores:** "docentes activos / participantes" se muestra como "3 / 5 (60 %)". Los participantes se cuentan con el estado de hoy, no con el de cada semana (design D9).

**Fuera de alcance (deuda para la descripción del PR):**
- Inicios de sesión fallidos y bloqueo del UPDATE/DELETE en PostgreSQL con un trigger → EN-04.
- INTENTO_SIN_PERMISO en uso → US-004 (queda en el catálogo, reservada).
- Porcentajes de KPI-02 a KPI-04 → US-028 / US-040. Columnas de sesiones cargadas y secciones con notas → US-010 y US-020 (hoy "—").
- Plazo de conservación del registro → US-009 (el cierre del año no lo borra).
- Vista de actividad para la dirección → no la pide el doc 08.
- Indicadores por institución → con una sola I.E. en el piloto no hace falta; se anota.

**Contradicciones que solo se mencionan (documentos congelados):**
- RNF-016 se precisa: catálogo cerrado, lecturas fuera, consola con usuario vacío, conservación hasta US-009 y misma transacción.
- Decisiones 3 y 9 frente al código: origen "deshacer" y "prefijo" de las cuentas demo (arriba).
- Doc 06 (RF-008, Ruta Infeliz): la docente y la dirección no entran al panel; el "no lo permite" se cumple sin pantalla, y el modelo también lo rechaza.

## Capabilities

### New Capabilities

- `registro-actividad`: qué se registra (catálogo, lecturas fuera, consola), cómo (misma transacción, sin datos personales en el detalle), solo lectura para todos, consulta con filtros y exportación CSV en el panel, conservación y la regla para historias futuras.
- `indicadores-adopcion`: página "Indicadores por semana" del panel: semanas de lunes a domingo en hora de Lima, docentes activos / participantes (KPI-01), jornadas registradas, sesiones y secciones con notas reservadas; la demostración fuera de todo cálculo.

### Modified Capabilities

Ninguna. Las pantallas y servicios de US-001, 002, 003, 005, 006, 030 y EN-06 se instrumentan sin cambiar su comportamiento observable, salvo los dos caminos que se cierran (D4), que no tienen escenario en sus specs.

## Impact

- **Código:**
  - `src/backend/actividad/`: `models.py`, migración `0001`, `servicios.py` (nuevo: `registrar`, indicadores, CSV), `admin.py`, `panel.py` (nuevo: mezcla para los `ModelAdmin`), `signals.py` (inicio y cierre de sesión), plantilla `templates/admin/actividad/indicadores.html` y pruebas.
  - Instrumentación: `asistencia/servicios.py`, `institucion/servicios.py` y `demo.py`, `cuentas/views.py` y `middleware.py` (motivo del cierre), los `admin.py` de `cuentas`, `institucion` y `catalogo`.
- **Dependencias:** ninguna nueva (CSV con la biblioteca estándar).
- **Migraciones:** `actividad/0001` (tabla nueva, sin datos).
- **Rutas:** solo dentro del panel (`/admin/actividad/registroactividad/` con `indicadores/` y `exportar/`). Se actualiza el Catálogo de rutas de `docs/03`. El README no cambia.
- **Requisitos:** US-008, RF-008, RNF-016, RN-015, RN-023, KPI-01 del doc 03, doc 08 (exportación del registro), doc 11 (3.7). DoD 1 a 9.
- **Rama:** `feature/US-008-registrar-actividad`, desde `main`. Su primer commit ya es el archivo de EN-06.
