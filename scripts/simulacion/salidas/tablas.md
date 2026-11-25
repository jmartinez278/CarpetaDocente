# Tablas de la simulación (Datos simulados)

Nada de lo que sigue es una medición real: es el ensayo del plan de análisis de 3.5 con datos simulados (plan.md, decisión 1). Numeradas «S» para no confundirlas con las tablas de la tesis.

- Semilla principal: 2026. Réplicas: 1000 (semillas 1…1000).
- parametros.yaml: blob 84c6706 (último commit 6a8e1ea); no se modifica.
- NumPy 2.5.5, SciPy 1.18.1, matplotlib 3.11.2.
- Figuras: `figuras/<indicador>.png` (diagramas de cajas pre/post, 3.5.1).

**Tabla S1. Descriptivos del pretest y el postest por indicador (Datos simulados)**

| Indicador | Unidad | Pre: media (DE) | Pre: mediana | Pre: mín.–máx. | Post: media (DE) | Post: mediana | Post: mín.–máx. | Variación (%) |
|---|---|---|---|---|---|---|---|---|
| Tiempo empleado en elaborar una sesión | min | 105,83 (21,72) | 101,53 | 59,72–148,49 | 93,81 (20,83) | 93,47 | 58,23–138,16 | −11,4 |
| Tiempo de registro de notas | min por sección | 19,59 (7,67) | 18,87 | 10,07–38,86 | 2,77 (0,68) | 2,71 | 1,45–4,22 | −85,8 |
| Exactitud del registro de notas | % de registros sin error | 94,19 (2,42) | 94,16 | 89,66–98,41 | 98,73 (0,67) | 98,91 | 97,04–99,59 | 4,8 |
| Tiempo del control de asistencia | min por jornada | 7,21 (3,18) | 6,05 | 2,65–14,13 | 0,70 (0,18) | 0,76 | 0,34–0,97 | −90,2 |
| Exactitud del control de asistencia | % de registros sin error | 92,45 (12,41) | 96,77 | 55,00–100,00 | 98,30 (4,20) | 99,22 | 78,86–100,00 | 6,3 |
| Percepción del docente (puntaje global, Anexo 4) | puntaje (15 a 75) | 45,58 (6,94) | 46,00 | 31,00–61,00 | 58,62 (7,75) | 59,00 | 44,00–73,00 | 28,6 |

*Nota.* Datos simulados (semilla 2026; n = 24 docentes). No son mediciones reales. Variación (%) = (media post − media pre) ÷ media pre × 100 (3.5.1).

**Tabla S2. Prueba de normalidad de Shapiro-Wilk sobre las diferencias (Datos simulados)**

| Indicador | W | p | Prueba elegida |
|---|---|---|---|
| Tiempo empleado en elaborar una sesión | 0,981 | 0,912 | t de Student (relacionadas) |
| Tiempo de registro de notas | 0,878 | 0,008 | Wilcoxon (rangos con signo) |
| Exactitud del registro de notas | 0,973 | 0,735 | t de Student (relacionadas) |
| Tiempo del control de asistencia | 0,921 | 0,061 | t de Student (relacionadas) |
| Exactitud del control de asistencia | 0,669 | < 0,001 | Wilcoxon (rangos con signo) |
| Percepción del docente (puntaje global, Anexo 4) | 0,903 | 0,025 | Wilcoxon (rangos con signo) |

*Nota.* Datos simulados (semilla 2026; n = 24 docentes). No son mediciones reales. Diferencia = postest − pretest. Con p ≥ 0,05 se usa t de Student; si no, Wilcoxon (3.5.2 a y b).

**Tabla S3. Prueba de hipótesis por indicador (Datos simulados)**

| Indicador | H₁ | Prueba | Estadístico | p (unilateral) | Tamaño del efecto | Dif. de medias [IC 95 %] | Decisión estadística (datos simulados) |
|---|---|---|---|---|---|---|---|
| Tiempo empleado en elaborar una sesión | post < pre | t de Student (relacionadas) | −3,24 | 0,002 | d de Cohen = −0,66 | −12,02 [−19,68; −4,36] | Se rechaza H₀ (datos simulados) |
| Tiempo de registro de notas | post < pre | Wilcoxon (rangos con signo) | 0,00 | < 0,001 | biserial de rangos = −1,00 | −16,82 [−19,94; −13,70] | Se rechaza H₀ (datos simulados) |
| Exactitud del registro de notas | post > pre | t de Student (relacionadas) | 10,28 | < 0,001 | d de Cohen = 2,10 | 4,55 [3,63; 5,46] | Se rechaza H₀ (datos simulados) |
| Tiempo del control de asistencia | post < pre | t de Student (relacionadas) | −10,20 | < 0,001 | d de Cohen = −2,08 | −6,50 [−7,82; −5,18] | Se rechaza H₀ (datos simulados) |
| Exactitud del control de asistencia | post > pre | Wilcoxon (rangos con signo) | 172,00 | 0,001 | biserial de rangos = 0,81 | 5,85 [0,23; 11,47] | Se rechaza H₀ (datos simulados) |
| Percepción del docente (puntaje global, Anexo 4) | post > pre | Wilcoxon (rangos con signo) | 298,50 | < 0,001 | biserial de rangos = 0,99 | 13,04 [10,57; 15,51] | Se rechaza H₀ (apoyo; no entra en HE ni HG; datos simulados) |

*Nota.* Datos simulados (semilla 2026; n = 24 docentes). No son mediciones reales. α = 0,05. Pruebas unilaterales en el sentido de H₁ (ajustes-cap3, punto 9). Wilcoxon descarta las diferencias en cero y corrige por continuidad, como Jamovi; su estadístico es la suma de rangos positivos. El IC 95 % de la diferencia de medias es bilateral (t). El puntaje global del cuestionario es evidencia de apoyo.

**Tabla S4. Decisión por hipótesis con la regla propuesta (Datos simulados)**

| Hipótesis | Indicadores | Decisión estadística (datos simulados) |
|---|---|---|
| HE1 | Tiempo empleado en elaborar una sesión | Se rechaza H₀ en todos sus indicadores (regla propuesta, punto 10; datos simulados) |
| HE2 | Tiempo de registro de notas; Exactitud del registro de notas | Se rechaza H₀ en todos sus indicadores (regla propuesta, punto 10; datos simulados) |
| HE3 | Tiempo del control de asistencia; Exactitud del control de asistencia | Se rechaza H₀ en todos sus indicadores (regla propuesta, punto 10; datos simulados) |
| HG | HE1, HE2 y HE3 | HE1, HE2 y HE3 rechazan H₀ (regla propuesta, punto 10; datos simulados) |

*Nota.* Datos simulados (semilla 2026; n = 24 docentes). No son mediciones reales. Regla propuesta, pendiente de decisión del equipo (ajustes-cap3, punto 10): una HE rechaza H₀ si la rechazan todos sus indicadores; la HG, si la rechazan las tres HE. El puntaje global del cuestionario no entra en la regla.

**Tabla S5. Cuestionario de percepción (Anexo 4) por dimensión (Datos simulados)**

| Dimensión | Pre: media (DE) | Pre: D/R/F | Post: media (DE) | Post: D/R/F |
|---|---|---|---|---|
| Planificación de sesiones | 15,50 (2,00) | 0/23/1 | 19,79 (2,80) | 0/8/16 |
| Registro y control de notas | 15,12 (3,55) | 4/15/5 | 19,33 (3,36) | 0/10/14 |
| Control de asistencia | 14,96 (4,28) | 8/10/6 | 19,50 (3,48) | 1/6/17 |
| Global (15 ítems) | 45,58 (6,94) | 1/21/2 | 58,62 (7,75) | 0/9/15 |

*Nota.* Datos simulados (semilla 2026; n = 24 docentes). No son mediciones reales. D/R/F: docentes en nivel desfavorable, regular y favorable según los cortes del Anexo 4. Solo el puntaje global se contrasta (Tabla S3).

**Tabla S6. Instrumentos complementarios: SUS y autorregistro (Datos simulados)**

| Instrumento | Pre: media (DE) | Post: media (DE) |
|---|---|---|
| SUS (solo postest, 0 a 100) | — | 65,5 (12,9) |
| Autorregistro: sesiones planificadas en la semana | 3,0 (1,9) | 3,0 (1,7) |
| Autorregistro: minutos totales en la semana | 282,7 (197,6) | 272,7 (172,6) |

*Nota.* Datos simulados (semilla 2026; n = 24 docentes). No son mediciones reales. Complementarios (3.4.2 d y e): no contrastan hipótesis.

**Tabla S7. Réplicas: % que rechaza H₀ por indicador (Datos simulados)**

| Indicador | % que rechaza H₀ | p mediano | Dif. de medias: media [2,5 %; 97,5 %] | % t / % Wilcoxon |
|---|---|---|---|---|
| Tiempo empleado en elaborar una sesión | 96,1 | 0,001 | −14,39 [−23,04; −6,53] | 88,4 / 11,6 |
| Tiempo de registro de notas | 100,0 | < 0,001 | −16,18 [−18,48; −14,05] | 65,2 / 34,8 |
| Exactitud del registro de notas | 100,0 | < 0,001 | 4,15 [2,90; 5,52] | 33,7 / 66,3 |
| Tiempo del control de asistencia | 100,0 | < 0,001 | −5,83 [−7,24; −4,61] | 4,6 / 95,4 |
| Exactitud del control de asistencia | 99,6 | < 0,001 | 4,49 [1,08; 8,83] | 2,2 / 97,8 |
| Percepción del docente (puntaje global, Anexo 4) | 100,0 | < 0,001 | 13,87 [11,08; 16,58] | 94,6 / 5,4 |

*Nota.* Datos simulados: 1000 réplicas con semillas 1…1000, cada una con nuevas docentes, O1 y O2, y la misma regla de 3.5.2 (Shapiro-Wilk, luego t o Wilcoxon, unilateral, α = 0,05). El intervalo 2,5–97,5 % es el de la diferencia de medias entre réplicas.

**Tabla S8. Réplicas: % en que cada hipótesis rechaza H₀ con la regla propuesta (Datos simulados)**

| Hipótesis | % de réplicas |
|---|---|
| HE1 | 96,1 |
| HE2 | 100,0 |
| HE3 | 99,6 |
| HG | 95,7 |

*Nota.* Datos simulados: 1000 réplicas con semillas 1…1000, cada una con nuevas docentes, O1 y O2, y la misma regla de 3.5.2 (Shapiro-Wilk, luego t o Wilcoxon, unilateral, α = 0,05). El intervalo 2,5–97,5 % es el de la diferencia de medias entre réplicas. Regla propuesta (ajustes-cap3, punto 10).

**Tabla S9. Punto de quiebre por tarea (Datos simulados)**

| Tarea | O1 media hoy (min) | O2 media (min) | % réplicas que rechaza hoy | Factor f: corrida principal | O1 media en f (min) | Factor f: 80 % de réplicas | O1 media en f (min) |
|---|---|---|---|---|---|---|---|
| sesion | 105,83 | 93,81 | 96,1 | 0,62 | 99,99 | 0,76 | 102,15 |
| notas | 19,59 | 2,77 | 100,0 | 0,17 | 3,33 | 0,19 | 3,63 |
| asistencia | 7,21 | 0,70 | 100,0 | 0,12 | 0,86 | 0,16 | 1,13 |

*Nota.* Datos simulados. f multiplica solo los tiempos de O1 propios de la tarea (sesión: la entrega; la elaboración es igual en O1 y O2). Corrida principal: el menor f desde el cual todos los f mayores dan p < 0,05 (barrido de 0,01 en 0,01 hasta 5). Réplicas: el menor f con el que al menos 80 % de las réplicas rechaza H₀ (bisección, tolerancia 0,01). «—»: no se alcanza con f ≤ 5. La O1 media en f es la de la corrida principal.

**Tabla S10. ¿El punto de quiebre cae dentro de los rangos de DEC-1? Conclusión por tarea (Datos simulados)**

| Tarea | Parámetros evaluados | f: corrida principal | Conclusión (corrida principal) | f: 80 % de réplicas | Conclusión (80 % de réplicas) |
|---|---|---|---|---|---|
| sesion | 1 | 0,62 | depende del supuesto | 0,76 | depende del supuesto |
| notas | 5 | 0,17 | robusta | 0,19 | robusta |
| asistencia | 2 | 0,12 | robusta | 0,16 | robusta |

*Nota.* Datos simulados. Cada parámetro de O1 de la tarea se multiplica por f (Tabla S9) y se compara con su rango de DEC-1. «Depende del supuesto»: todos los parámetros evaluados siguen dentro de su rango, así que el quiebre se alcanza sin salir de lo que el equipo consideró plausible. «Robusta»: al menos uno sale de su rango. Un rango que empieza en 0 no cuenta como «dentro del rango» (contiene cualquier valor reducido, así que no informa) y ese parámetro no se evalúa. El detalle por parámetro está en simulados_quiebre.csv. parametros.yaml no se modifica.
