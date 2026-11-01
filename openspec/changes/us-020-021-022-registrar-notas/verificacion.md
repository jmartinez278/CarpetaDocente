# Verificación: US-020, US-021 y US-022 – Hoja de notas por área

## Minor para la descripción del PR

### Parte A: `Calificacion` y su migración

- `institucion/servicios.py`, docstring de `quitar_estudiante`: dice «hoy, `asistencia`»; `calificacion` también bloquea con RESTRICT.
- `notas/models.py`, `ck_calificacion_conclusion`: en B y C acepta diez o más espacios; la red es el `strip()` del servicio (D5, paso 4), que se prueba en la parte B.
- `notas/models.py`: el comentario «Escala de calificación (RN-001)» va sobre las constantes de longitud y no sobre `Nivel`, y los CHECK repiten la escala en vez de usar `Nivel.values`.
