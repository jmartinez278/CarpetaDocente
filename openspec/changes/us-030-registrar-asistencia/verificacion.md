# Verificación: US-030 – Registrar la asistencia de una jornada

Se completa en 3.2. Hasta entonces, solo la evidencia por parte y los Minor.

## Evidencia por parte

- **Grupo 1, parte B (1.2 y 1.3):** pruebas en `institucion/tests/test_modelos_estudiante.py`, `asistencia/tests/test_modelos.py` y `institucion/tests/test_servicios_estudiantes.py` (con asistencia real). Vistas en rojo antes del código; `makemigrations --check` sin cambios; `sqlmigrate` de `institucion/0004` (valor por defecto y `ck_estudiante_estado`) y de `asistencia/0001` (`uq_jornada`, `uq_asistencia`, `ck_asistencia_estado`, `ck_asistencia_nota`). Revisión de la parte: sin Critical ni Important.
- **Grupo 1, parte C (1.5 y 1.6):** pruebas en `asistencia/tests/test_servicios.py` (con `hoy` fijo) y `cuentas/tests/test_inactividad.py` (reloj congelado en 29 s y 30 s). Rojo antes del código. Revisión de la parte: sin Critical; 3 Important (pruebas que no fallaban al quitar `actualizado_en` del upsert, el `atomic` ni el borde de 30 s) corregidos y comprobados quitando cada comportamiento a propósito.
- **Grupo 2, parte A (2.1 y 2.2):** pruebas en `asistencia/tests/test_vistas.py` (rutas, acceso, CSRF, `HX-Redirect`, 204/400/404/409 y el enlace del aviso), `cuentas/tests/test_pantallas.py` (saludo según la hora, fecha, tarjeta Asistencia y píldora) y `test_dimensiones.py`; rojo antes del código. E2E en `test_portada_e2e.py` (píldora una vez y quieta con "reducir movimiento", axe con y sin píldora en ambos temas a 360 y 1280 px, 320 px sin desplazamiento) y `test_estudiantes_e2e.py` (el aviso abre la asistencia como página completa, axe y 320 px). Pruebas de US-001, US-005 y US-006 que miraban "Hola," o la línea sin fecha, actualizadas. Capturas de portada (360 y 1280) y de la lista con el aviso comparadas con `decision-final/capturas/`: iguales, salvo el alto de la ventana (800 frente a 900 px) en la portada de PC. `uv run pytest --cov`: 908, 98 %; e2e: 185 en verde. Revisión de la parte: sin Critical ni Important.
- **Desviación de D10:** `Dimension` gana el campo `url` (opcional), porque `dataclasses.replace` no crea campos; la tarjeta solo lee `d.url`.

## Minor para la descripción del PR

- `institucion/tests/test_servicios_estudiantes.py`: la fixture `fecha_asistencia` repite la fixture `fecha` de `asistencia/tests/conftest.py`, y sus imports son locales.
- `asistencia/tests/conftest.py`: `from institucion.tests.conftest import *` acopla `asistencia` a otra app; mejor subir las fixtures compartidas a `src/backend/conftest.py`.
- `Asistencia.__str__` consulta `self.estudiante` en cada llamada (N+1 si se usa en listados o mensajes); revisar si la parte C lo usa.
- Sin prueba directa de `estudiante.delete()` con asistencia a nivel de modelo; la cubren las de servicios.
- `cierre-sesion` dice "cada petición reinicia la cuenta": con D9 la precisión es de 30 s (la sesión puede cerrarse hasta 30 s antes de los 60 minutos, nunca después). Sin delta de ese spec en este cambio; anotado aquí y en el design (D9).
- `InactividadMiddleware`: con el reloj retrocedido (diferencia negativa) la marca futura no se renueva hasta que el reloj la alcanza; `sesion_vencida` tampoco vence en ese caso. Improbable con un servidor.
- `servicios._completa_o_vacia`: el nombre no dice que "sin activos" cuenta como completa, y hace 2 consultas; se puede renombrar (`_sin_pendientes`) o juntar en una agregación.
- `servicios.marcar`: una nota de solo espacios se guarda y cuenta contra los 100; decidir en la vista (parte 2) si se recorta.
- `servicios.marcar_restantes`: los ids deben llegar como enteros (la vista, D10, los convierte); `"5"` y `5` contarían como dos.
- `servicios.marcar`: el estudiante activo se lee sin bloqueo; un retiro simultáneo podría dejar una fila de un RETIRADO, que ya no cuenta en totales ni avance.
- `MarcarView`: el 404 de un estudiante de otra sección lo da `get_object_or_404` del mixin y lleva la página 404 con cuerpo; los demás 404 de los guardados salen vacíos. El JS solo mira el código.
- `_lista.html`: "Tomar la asistencia de hoy" sale con cualquier mensaje de etiqueta `estudiantes` que llegue a la lista; hoy solo llega el de importados. Una etiqueta propia lo dejaría atado a ese aviso.
- Catálogo de rutas, nota "Guardados de la asistencia": describe el envío con `HX-Request` que hará `asistencia.js` (parte B); revisarla al cerrar 2.5 y 2.7.
