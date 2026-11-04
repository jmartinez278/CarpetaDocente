# Propuesta: US-004 – Restringir el acceso según el rol

## Why

Hoy una docente que abre una sección que no es suya recibe un 404 mudo y nadie se entera del intento. US-004 (RF-004, prioridad Alta) convierte esa negación en un 403 con un mensaje claro y una salida a su inicio, y deja constancia de cada intento en el registro de actividad (RNF-013, RNF-016). Es transversal (usuarios y acceso): protege los datos de las tres dimensiones de la tesis —por ahora, los de asistencia y de notas ya construidos— y llena por primera vez la operación `INTENTO_SIN_PERMISO`, que estaba reservada.

## What Changes

Se aplica tal cual `insumos/US-004/decisiones.md` (sin bocetos: marco + Mensaje de DESIGN.md). Lo nuevo de este propose:

- **Una página propia de «sin permiso»** en `/docente/sin-permiso/`, solo para el rol Docente, que no registra nada. La navegación normal recibe el 403 con la página en la misma dirección; HTMX y los `fetch` de asistencia, competencias y notas reciben el 403 con `HX-Redirect` a esa página (design D3).
- **`competencias.js` y `asistencia.js` también distinguen el 403** del «Tu sesión venció»: los tres guardados por `fetch` mandan `HX-Request` y hoy tratan cualquier `HX-Redirect` como sesión vencida. Con 403 van a la página de «sin permiso» y no guardan borradores ni pendientes de una sección ajena (design D6).
- **El motivo se decide en una sola consulta** sobre la sección sin filtrar por docente; si la sección es de otra docente, el motivo es `ajena` aunque su año esté cerrado (design D4).
- **La entrada lleva `entidad="seccion"` y el id pedido**, además de `ruta` y `motivo` en el detalle, para filtrar los intentos por sección en el panel (design D5).
- **Los ids que viajan en el cuerpo** (los «restantes» de asistencia y las celdas de la hoja de notas) siguen con su respuesta de hoy (404 y 400), sin registro: la regla vive solo en el mixin, que ve la ruta (design D7).

**Fuera de alcance:**
- La dirección ve los consolidados en solo lectura (escenario 2 del criterio) → US-040 (y US-033 para asistencia).
- Docentes de curso (asignación área × sección) → historia nueva de docentes de curso.
- Resto de EN-04 (HTTPS, hash, inactividad, CSRF, secretos, trigger contra UPDATE/DELETE) → EN-04.
- Contar o alertar intentos repetidos → si el piloto lo pide.

**Contradicciones que solo se mencionan (documentos congelados, van a la deuda):**
- Criterio de US-004 (doc 02/01): «No tiene permiso…» en usted; manda el tuteo de DESIGN.md.
- Doc 08 y RNF-016 piden registrar «operaciones sin permiso»; el registro cubre las rutas de sección de la docente, no las de otros roles (decisión 7).

## Capabilities

### New Capabilities

- `acceso-secciones`: la regla común de las rutas `/docente/secciones/<id>/…`: 403 igual para sección ajena, inexistente o de año cerrado y para un estudiante de otra sección; página «sin permiso»; respuesta a HTMX y `fetch`; una entrada `INTENTO_SIN_PERMISO` por intento; matriz de permisos de lo construido.

### Modified Capabilities

- `estudiantes-seccion`: «Acceso solo a sus secciones» pasa de 404 a 403 con registro.
- `asistencia-jornada`: «Acceso solo a la asistencia de su sección» pasa de «página no encontrada» a 403 con registro.
- `competencias-periodo`: «Acceso a las competencias de su sección» pasa a 403 con registro.
- `registro-notas`: «Acceso a la hoja de notas» pasa a 403 con registro.
- `registro-actividad`: `INTENTO_SIN_PERMISO` deja de estar reservada; un intento sin permiso es la única lectura que deja entrada.

## Impact

- `institucion/views.py` (`SeccionDocenteMixin`) e `institucion/servicios.py` (verificación y registro); `cuentas/` (vista y ruta de «sin permiso», plantilla); `actividad/models.py` y `actividad/servicios.py` (`RESERVADAS` vacía, detalle permitido).
- `static/js/notas.js`, `competencias.js` y `asistencia.js`.
- Pruebas que hoy esperan 404 en US-006, US-030, US-029 y US-020/021/022; prueba nueva de la matriz.
- `docs/03 Implementación/Catálogo de rutas.md`: ruta nueva y columna «Acceso» de las rutas de sección.
- Sin migraciones: la operación ya está en el catálogo y en `ck_actividad_operacion`.
