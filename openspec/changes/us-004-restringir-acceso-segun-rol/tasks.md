# Tasks

## 1. Verificación, registro y respuesta (D1 a D5, D9)

### Parte A: la regla en el mixin, el registro y la página (alto riesgo)

- [x] 1.1 Prueba primero, `institucion/tests/test_servicios_acceso.py`: `seccion_de_la_docente` devuelve la sección (y el estudiante) de la docente en el año ABIERTO; `SinPermiso` con `inexistente` (id que no existe), `ajena` (de otra docente, también con su año CERRADO), `anio_cerrado` (suya, año CERRADO) y `estudiante` (de otra sección o inexistente); la dirección nunca llega aquí. Luego D1 y el orden de D4. Verificar: rojo y luego verde; `uv run pytest src/backend/institucion -k acceso`
- [x] 1.2 Prueba primero, el mismo archivo y `actividad/tests/test_modelos.py` y `test_catalogo.py`: `registrar_intento_sin_permiso` deja una entrada INTENTO_SIN_PERMISO con usuario, `entidad="seccion"`, el id pedido y `{"ruta", "motivo"}`; tres llamadas, tres entradas; una clave de más en el detalle → `ValueError`; `RESERVADAS` vacía y el catálogo sin operación saltada. Luego D5 (`DETALLE_PERMITIDO`, `RESERVADAS`). Verificar: rojo y luego verde; `uv run pytest src/backend/actividad src/backend/institucion -k "acceso or catalogo or modelos"`
- [x] 1.3 Prueba primero, `cuentas/tests/test_sin_permiso.py`: `/docente/sin-permiso/` responde 200 a la docente con «No tienes permiso para ver esta sección», «Vuelve a tu inicio para abrir tu sección.» y «Volver a tu inicio» hacia `/docente/`, sin crear entrada; la dirección va a `/direccion/` y sin sesión a `/ingresar/?next=…`; `sin_permiso(request)` da 403 con la plantilla sin `HX-Request`, y 403 sin cuerpo con `HX-Redirect` a `/docente/sin-permiso/` con ella. Luego D3 (`cuentas/acceso.py`, `SinPermisoView`, ruta, plantilla con las clases del Mensaje de error). Verificar: rojo y luego verde; `uv run pytest src/backend/cuentas -k sin_permiso`
- [x] 1.4 Prueba primero, `institucion/tests/test_vistas_estudiantes.py`: otra docente en lista, pegar, agregar, editar, quitar y vaciar → 403 con el mensaje, sin nombres, nada cambiado y una entrada `ajena`; año CERRADO → 403 `anio_cerrado`; sección inexistente → 403 `inexistente`; estudiante de otra sección en editar y quitar (GET y POST) → 403 `estudiante`; con `HX-Request`, 403 con `HX-Redirect`; el estudiante quitado entre la carga y el guardado sigue en 404. Luego D2 en `SeccionDocenteMixin` y el docstring. Verificar: rojo y luego verde; `uv run pytest src/backend/institucion`
- [x] 1.5 Prueba primero, `asistencia/tests/test_vistas.py`, `notas/tests/test_vistas_acceso.py` y `notas/tests/test_vistas_hoja_acceso.py` (D9): otra docente, año CERRADO e inexistente → 403 en GET y en cada guardado, sin guardar y con su entrada; `marcar` con un estudiante de otra sección → 403 `estudiante`; siguen en 404 sin entrada el retirado en `marcar`, los «restantes» con id ajeno y el periodo o el área que no existen; las pruebas renombradas y los docstrings de `asistencia/views.py` y `notas/views.py`. Verificar: rojo y luego verde; `uv run pytest src/backend/asistencia src/backend/notas`
- [x] 1.6 Revisión de la parte (agente `revisor`) y commit

## 2. Guardados por `fetch` y matriz (D6, D8)

### Parte B: 403 en los guardados de asistencia, competencias y notas, y matriz de permisos (alto riesgo)

- [x] 2.1 Prueba primero, `notas/tests/test_hoja_e2e.py`: con la hoja abierta y una nota escrita, la sección pasa a otra docente; «Guardar» lleva a la página de «sin permiso», sin «Tu sesión venció», sin el aviso de salida y sin borradores de esa sección en `localStorage`; queda una sola entrada. Luego D6 en `notas.js`. Verificar: rojo y luego verde; e2e de `notas` del archivo
- [x] 2.2 Prueba primero, `notas/tests/test_competencias_e2e.py` y `asistencia/tests/test_asistencia_e2e.py`: el mismo caso en «Guardar» de competencias (sin «Tu sesión venció» ni aviso de salida) y al marcar en asistencia (sin pendientes de esa sección en `sessionStorage`), una entrada cada uno. Luego D6 en `competencias.js` y `asistencia.js`. Verificar: rojo y luego verde; esos dos e2e
- [x] 2.3 Prueba primero, `institucion/tests/test_estudiantes_e2e.py`: con el diálogo de la portada abierto, la sección pasa a otra docente; «Agregar» lleva a la página completa de «sin permiso», sin nada pintado en el diálogo. Verificar: rojo si el diálogo pinta el 403, y luego verde
- [x] 2.4 Prueba primero, `cuentas/tests/test_matriz_permisos.py` (D8): la tabla de rutas × perfiles × método; propia entra; ajena 403 con una entrada más y nada escrito; dirección y Administrador a su inicio; sin sesión al ingreso; solo la propia guarda; ninguna entrada para los otros perfiles. Verificar: verde (la regla ya está; se ve fallar quitando el registro del mixin en local)
- [x] 2.5 Revisión de la parte (agente `revisor`) y commit

## 3. Pantalla y catálogo de rutas

### Parte C: accesibilidad de la página y documentación (normal)

- [x] 3.1 Prueba primero, `cuentas/tests/test_accesibilidad_e2e.py`: la página de «sin permiso» sin infracciones graves de axe en claro y oscuro, a 360 y 1280 px; sin desplazamiento horizontal a 320 y 360 px; «Volver a tu inicio» de al menos 44 px. Luego los ajustes de CSS que falten en `src/frontend/`. Verificar: e2e de `cuentas` del archivo en verde
- [x] 3.2 Catálogo de rutas (D10): fila de `/docente/sin-permiso/` y la columna «Acceso» de las rutas de sección con 403 y registro. Verificar: cada ruta de `config/urls.py` y `cuentas/urls.py` tiene su fila
- [x] 3.3 Pantalla vista en claro/oscuro y celular/escritorio (la marca Marco). `verificar.py` y commit

## 4. Cierre

- [ ] 4.1 Con la A2 que corre el usuario (`/codex:adversarial-review --base main --background`, con foco en los specs del cambio, el registro único por intento y los 404 que se quedan), corregir los Critical e Important, con la prueba primero. Verificar: `uv run pytest --cov` (80 % o más), las e2e y `verificar.py --antes-del-commit` en verde
- [ ] 4.2 `verificacion.md`: tabla escenario → prueba de los seis specs del cambio y la DoD 1 a 9. Verificar: cada escenario tiene su prueba o una nota de por qué no aplica; commit

## Contradicciones

- Criterio de US-004 (doc 02/01): «No tiene permiso para ver esta sección» en usted; manda el tuteo de DESIGN.md: «No tienes permiso para ver esta sección» (decisión 5).
- Criterio de US-004, escenario 2 (la dirección ve los consolidados): no entra; es de US-040 (decisión 7).
- Doc 08 y RNF-016 («operaciones sin permiso»): el registro cubre las rutas de sección de la docente; otros roles van a su inicio sin entrada (decisión 7).
- Design de US-006 (D4), US-029 (D8) y US-020 (acceso): el 404 de sección ajena pasa a 403 (decisión 1).

## Workflow follow-up

- **(equipo)** Push de `feature/us-004-restringir-acceso-segun-rol` y PR hacia `main` (`Closes #N` de US-004, verificando el número), con las verificaciones de EN-08 en verde. En «Para quien revise»: la regla vive solo en `SeccionDocenteMixin`; la página de «sin permiso» no registra; los 404 que se quedan (periodo, área, retirado, restantes). En «## Deuda»:
  - lectura de la dirección → US-040 (y US-033); docentes de curso → historia nueva, sin ID;
  - resto de EN-04 (HTTPS, hash, inactividad, CSRF, secretos, trigger contra UPDATE/DELETE) y limitar la frecuencia de intentos → EN-04; EN-04 remite a US-004 para «Intento de abrir una sección ajena»;
  - ids ajenos en el cuerpo («restantes», celdas de la hoja) siguen en 404/400 sin registro (D7) → si el equipo lo pide;
  - un estudiante propio quitado en otra pestaña da «sin permiso» al editarlo después → si el piloto lo nota;
  - contar o alertar intentos repetidos → si el piloto lo pide.
- **(equipo)** Aprobación del PR por otra integrante (DoD 3).
- Después de la fusión: `/opsx:archive` con «Sync now». La siguiente historia sale de `main` y su primer commit es este archivo.
