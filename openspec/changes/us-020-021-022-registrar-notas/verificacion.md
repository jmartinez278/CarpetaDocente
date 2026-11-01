# Verificación: US-020, US-021 y US-022 – Hoja de notas por área

## Minor para la descripción del PR

### Parte A: `Calificacion` y su migración

- `institucion/servicios.py`, docstring de `quitar_estudiante`: dice «hoy, `asistencia`»; `calificacion` también bloquea con RESTRICT.
- `notas/models.py`, `ck_calificacion_conclusion`: en B y C acepta diez o más espacios; la red es el `strip()` del servicio (D5, paso 4), que se prueba en la parte B.
- `notas/models.py`: el comentario «Escala de calificación (RN-001)» va sobre las constantes de longitud y no sobre `Nivel`, y los CHECK repiten la escala en vez de usar `Nivel.values`.

### Parte B: servicios de la hoja, actividad, indicadores y demo

- `notas/servicios.py`, `notas_faltantes`: ordena los pares por id de estudiante y no por apellidos como la hoja; si US-026 o US-042 recorren «la siguiente faltante» con ellos, conviene usar el orden de `estudiantes_ordenados`.
- `notas/servicios.py`, `hoja_de_notas`: un trasladado va a solo lectura si tiene nota en una columna marcada, no en cualquier competencia del área; hoy es lo mismo (una competencia con notas no se desmarca), pero una competencia desactivada en el catálogo oculta su nota.
- `notas/servicios.py`, docstring de `hoja_de_notas`: el número de consultas que nombra no coincide con lo que enumera; la cifra que vale es la de `test_la_hoja_se_lee_en_un_numero_fijo_de_consultas` (5).

### Parte C: vistas, rutas, permisos y bandera

- `notas/views.py`: la regla «área que la institución trabaja» se repite en `_area_inicial` y `_ir_a_competencias`; un solo helper evitaría que se desalineen en la parte 4.
- `notas/views.py`, `GuardarHojaView`: el 404 de periodo o área va sin cuerpo y los demás errores en JSON con `mensaje`; `notas.js` (parte 4) debe tratar el 404 aparte.
- `cuentas/tests/test_portada_e2e.py`: el `if ancho == 360` ata la prueba de la píldora a que Notas sea la primera tarjeta disponible.
