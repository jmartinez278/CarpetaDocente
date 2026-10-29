# Verificación: US-030 – Registrar la asistencia de una jornada

Se completa en 3.2. Hasta entonces, solo la evidencia por parte y los Minor.

## Evidencia por parte

- **Grupo 1, parte B (1.2 y 1.3):** pruebas en `institucion/tests/test_modelos_estudiante.py`, `asistencia/tests/test_modelos.py` y `institucion/tests/test_servicios_estudiantes.py` (con asistencia real). Vistas en rojo antes del código; `makemigrations --check` sin cambios; `sqlmigrate` de `institucion/0004` (valor por defecto y `ck_estudiante_estado`) y de `asistencia/0001` (`uq_jornada`, `uq_asistencia`, `ck_asistencia_estado`, `ck_asistencia_nota`). Revisión de la parte: sin Critical ni Important.

## Minor para la descripción del PR

- `institucion/tests/test_servicios_estudiantes.py`: la fixture `fecha_asistencia` repite la fixture `fecha` de `asistencia/tests/conftest.py`, y sus imports son locales.
- `asistencia/tests/conftest.py`: `from institucion.tests.conftest import *` acopla `asistencia` a otra app; mejor subir las fixtures compartidas a `src/backend/conftest.py`.
- `Asistencia.__str__` consulta `self.estudiante` en cada llamada (N+1 si se usa en listados o mensajes); revisar si la parte C lo usa.
- Sin prueba directa de `estudiante.delete()` con asistencia a nivel de modelo; la cubren las de servicios.
