# Design: US-004 – Restringir el acceso según el rol

## Context

- Decisiones de alcance cerradas en `insumos/US-004/decisiones.md` (1 a 9 y zonas de cuidado); lo nuevo está en `proposal.md`. Sin bocetos: marco (`templates/marco.html`) + Mensaje de error (clases `mensaje mensaje--error` que ya usan las plantillas de estudiantes y asistencia).
- `institucion/views.py`: `SeccionDocenteMixin(RolRequeridoMixin)` carga `self.seccion` con `get_object_or_404(secciones_docente(usuario), pk=…)` y, si la ruta trae `estudiante_id`, `self.estudiante` desde `self.seccion.estudiantes`. Cubre las 4 rutas: `institucion`, `asistencia` (`MarcarView` trae `estudiante_id` en la ruta), `notas` (competencias y hoja). Otro rol y sin sesión los resuelve antes `RolRequeridoMixin`, sin consultar la sección.
- `cuentas/acceso.py`: `redirigir()` responde 200 con `HX-Redirect` a una petición `HX-Request`; `es_htmx()`.
- Los tres guardados por `fetch` (`asistencia.js`, `competencias.js`, `notas.js`) mandan `HX-Request: true` y leen `HX-Redirect`: asistencia lo sigue guardando antes sus pendientes en `sessionStorage`; competencias y notas lo muestran como «Tu sesión venció» con un enlace.
- HTMX 2.0.x (`handleAjaxResponse`) procesa `HX-Redirect` antes de mirar el código de estado: un 403 con la cabecera navega igual (verificado en `node_modules/htmx.org/dist/htmx.js`).
- `actividad`: `INTENTO_SIN_PERMISO` ya está en `Operacion` y en `ck_actividad_operacion`; `RESERVADAS = {INTENTO_SIN_PERMISO}` y `test_catalogo.py` la salta; `DETALLE_PERMITIDO` no tiene entrada para ella; `registrar()` exige una transacción abierta. Sin `ATOMIC_REQUESTS`.
- No hay `handler403` propio; el panel usa el 403 de Django para un ADMINISTRADOR sin `is_staff` (`cuentas/views.py`).

## Riesgos y zonas delicadas (primero)

- **[Registrar dos veces]** (zona de cuidado) → D3: el registro va en la petición original, dentro del mixin; la página `/docente/sin-permiso/` es una `TemplateView` que no llama al servicio. Prueba: un guardado `fetch` con 403 seguido del GET de la página deja una sola entrada.
- **[El 403 leído como «sesión vencida»]** → D6: `competencias.js` y `notas.js` miran el código antes que la cabecera; solo un 200 con `HX-Redirect` es sesión vencida.
- **[El aviso de salida bloquea la redirección]** → competencias y notas piden confirmación al salir con cambios (`beforeunload` y el diálogo de salida). D6: el 403 desarma ese aviso antes de `location.assign`, como ya hace asistencia con `saliendo`.
- **[Datos de una sección ajena en el dispositivo]** → D6: con 403, notas borra los borradores de esa sección y asistencia no guarda pendientes y borra los que hubiera.
- **[Cambiar 404 por 403 en las pruebas]** (zona de cuidado) → D9 lista los archivos y qué 404 se quedan: periodo o área que no existen, estudiante retirado o trasladado en asistencia, «restantes» con un id ajeno y el estudiante quitado entre la carga y el guardado (`test_editar_un_estudiante_quitado_mientras_se_enviaba_da_404_sin_recrearlo`).
- **[Estudiante quitado en otra pestaña]** → con la decisión 2, abrir después «Editar» de un estudiante propio ya quitado es 403 con motivo `estudiante`, no 404. Se acepta (misma respuesta para «inexistente»); va a la deuda por si el piloto lo nota.
- **[Volumen del registro]** → una entrada por intento sin agrupar (decisión 4): un script que repite intentos llena `registro_actividad`. Limitar la frecuencia es de EN-04; va a la deuda.
- **[El 403 global]** → D2: el mixin devuelve la respuesta en vez de lanzar `PermissionDenied`, para no cambiar el 403 del panel ni de otras vistas.

## Goals / Non-Goals

**Goals:**
- Un solo punto (`SeccionDocenteMixin`) que decide, registra y responde; ninguna vista repite la verificación.
- La verificación y el registro en servicios; el mixin solo lee la petición y elige la respuesta.
- Misma respuesta para ajena, inexistente, año cerrado y estudiante de otra sección; el motivo solo en el registro.

**Non-Goals:**
- La lectura de la dirección (US-040, US-033) y los docentes de curso.
- Registrar intentos de otros roles o de rutas fuera de `/docente/secciones/`.
- Revisar los ids que viajan en el cuerpo de un guardado (D7).
- Limitar la frecuencia de intentos (EN-04).

## Decisions

### D1. Verificación en `institucion/servicios.py`

- `class SinPermiso(Exception)` con `motivo` (uno de `AJENA`, `INEXISTENTE`, `ANIO_CERRADO`, `ESTUDIANTE`, constantes del módulo con los códigos `ajena`, `inexistente`, `anio_cerrado`, `estudiante`).
- `seccion_de_la_docente(usuario, seccion_id, estudiante_id=None)` → `(seccion, estudiante | None)` o `SinPermiso`. Solo lee: una consulta `Seccion.objects.select_related("anio_escolar").filter(pk=seccion_id).first()` y, si hay `estudiante_id`, `seccion.estudiantes.filter(pk=estudiante_id).first()`.
- `secciones_docente()` no cambia (la usa la portada).
- **Alternativa descartada:** seguir con `get_object_or_404` sobre `secciones_docente` y consultar de nuevo para el motivo: dos caminos para la misma regla.

### D2. `SeccionDocenteMixin` responde, no lanza

- En `dispatch`, para la docente: llama a `seccion_de_la_docente`; con `SinPermiso`, llama a `registrar_intento_sin_permiso` (D5) y devuelve `sin_permiso(request)` (D3) sin pasar a la vista. Sin error, deja `self.seccion` y `self.estudiante` como hoy.
- Otro rol y sin sesión siguen en `RolRequeridoMixin`, antes, sin consulta ni registro (decisión 7).
- **Por qué no `PermissionDenied`:** cambiaría el 403 de todas las vistas y del panel, y obligaría a un `handler403` que distinga HTMX. El mixin ya decide la respuesta para otro rol del mismo modo.

### D3. Respuesta 403 y página «sin permiso» (`cuentas`)

- `cuentas/acceso.py`: `sin_permiso(request)`. Con `HX-Request`: `HttpResponse(status=403)` con `HX-Redirect` a `reverse("docente:sin_permiso")`. Sin ella: `render(request, "cuentas/sin_permiso.html", status=403)`, en la misma dirección.
- `cuentas/views.py`: `SinPermisoView(RolRequeridoMixin, TemplateView)`, rol Docente, misma plantilla, 200, sin registro. Ruta `/docente/sin-permiso/` en `cuentas/urls.py`, nombre `docente:sin_permiso`.
- `templates/cuentas/sin_permiso.html` extiende `marco.html`: un `main` con el Mensaje de error (`h1` con «No tienes permiso para ver esta sección», párrafo «Vuelve a tu inicio para abrir tu sección.») y el enlace-botón principal «Volver a tu inicio» a `docente:portada`. Título de pestaña «Sin permiso · CarpetaDocente». Sin contexto de la sección.
- **Por qué 200 en la página de destino:** el 403 ya lo recibió la petición que se negó; la página es solo el destino de la navegación.

### D4. Orden del motivo

1. No existe la sección → `inexistente`.
2. `seccion.docente_id != usuario.pk` → `ajena` (aunque su año esté CERRADO: lo que importa es que no es suya).
3. Año distinto de ABIERTO → `anio_cerrado`.
4. Hay `estudiante_id` y no es de la sección → `estudiante`.

### D5. Registro (`registrar_intento_sin_permiso` en `institucion/servicios.py`)

- `registrar_intento_sin_permiso(usuario, seccion_id, ruta, motivo)`: `transaction.atomic()` propio y `registrar(usuario, Operacion.INTENTO_SIN_PERMISO, entidad="seccion", entidad_id=seccion_id, detalle={"ruta": ruta, "motivo": motivo})`. Una entrada por llamada, sin agrupar.
- `ruta` es `request.path` (sin la consulta): en estas rutas solo hay ids, fechas y códigos SIAGIE (RN-015).
- `actividad/servicios.py`: `DETALLE_PERMITIDO[INTENTO_SIN_PERMISO] = {"ruta", "motivo"}`. `actividad/models.py`: `RESERVADAS = frozenset()` (se conserva el nombre, ya vacío, para la próxima operación reservada); `test_modelos.py` y el escenario de `test_catalogo.py` se actualizan.
- **Dato que mide la tesis:** ningún indicador nuevo. Los intentos quedan en `registro_actividad` (`operacion`, `usuario`, `fecha_hora`, `detalle.motivo`) como evidencia de RNF-013 y RNF-016; no cuentan para KPI-01.

### D6. Guardados por `fetch` con 403

- `notas.js`: si `respuesta.status === 403` y trae `HX-Redirect`, borra los borradores de la sección (las claves de `NotasBorrador` con el prefijo de `clave_borrador` hasta `:s<id>:`), desarma el aviso de salida y hace `location.assign(redireccion)`. El resto (200 con `HX-Redirect` = sesión vencida) no cambia.
- `competencias.js`: igual, sin borradores (los cambios viven en memoria).
- `asistencia.js` (`resolver`): con 403, borra los pendientes de la sección en `sessionStorage` en vez de `recordarPendientes()` y sigue la redirección.
- La lista de estudiantes del diálogo de la portada usa HTMX: el `HX-Redirect` del 403 basta (contexto).

### D7. Ids en el cuerpo, sin cambio

- «Restantes» (`estudiante` repetido) sigue en 404 sin guardar ninguno; las celdas de la hoja con un estudiante ajeno siguen en 400 `HojaCambiada`. Ninguno registra. La regla vive en el mixin, que ve la ruta (decisión 3); el servicio ya rechaza el cuerpo.

### D8. Matriz de permisos (`cuentas/tests/test_matriz_permisos.py`)

- Rutas: `estudiantes:lista` (GET), `estudiantes:agregar` (POST), `estudiantes:editar` (GET y POST, con estudiante), `asistencia:hoy` (GET), `asistencia:marcar` (POST), `competencias:pantalla` (GET), `competencias:guardar` (POST), `notas:hoja` (GET), `notas:guardar` (POST JSON).
- Perfiles: docente propia, docente ajena, dirección, Administrador, anónimo. Esperado: propia, sin 302 ni 403; ajena, 403 y una entrada más; dirección y Administrador, 302 a su inicio; anónimo, 302 a `/ingresar/?next=…`. En escritura, solo la propia cambia datos (se cuentan las filas afectadas).
- Una tabla de filas en el módulo; cada historia futura agrega las suyas.

### D9. Pruebas que cambian de 404 a 403

- `institucion/tests/test_vistas_estudiantes.py` (otra docente en lista, pegar, agregar, vaciar; año cerrado; sección inexistente; estudiante de otra sección), `asistencia/tests/test_vistas.py` (otra docente, año cerrado, estudiante de otra sección en `marcar`), `notas/tests/test_vistas_acceso.py` y `notas/tests/test_vistas_hoja_acceso.py` (otra docente, año cerrado, inexistente).
- Se quedan en 404: periodo o área que no existen (`test_vistas.py`, `test_vistas_hoja.py`), retirado en asistencia, restantes con id ajeno, estudiante quitado entre la carga y el guardado.
- Se renombran las que dicen `404` en el nombre y se actualizan los docstrings de `institucion/views.py`, `asistencia/views.py`, `notas/views.py` y `cuentas/acceso.py`.

### D10. Catálogo de rutas

- `docs/03 Implementación/Catálogo de rutas.md`: fila de `/docente/sin-permiso/` y, en la columna «Acceso» de `estudiantes:lista` (y las que dicen «Como…»), «403 con registro» en vez de 404. `asistencia:marcar` aclara que el 404 es para el estudiante de la sección que no está activo.
