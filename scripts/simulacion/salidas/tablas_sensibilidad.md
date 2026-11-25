# Sensibilidad de la simulación (Datos simulados)

Nada de lo que sigue es una medición real.

**Tabla S14. Supuestos clave: cambian una decisión de la corrida principal o cruzan el 80 % de réplicas (Datos simulados)**

| Supuesto | Contexto | Extremo | Valor | HE que cambia | % HE1 | % HE2 | % HE3 | % HG |
|---|---|---|---|---|---|---|---|---|
| ruido.medicion_cv | base | máximo | 0,300 | HE1, HG | 51,0 | 100,0 | 99,6 | 50,8 |
| o1.sesion.elaboracion_mediana | base | máximo | 180,000 | HE1, HG | 49,8 | 100,0 | 99,6 | 49,6 |
| o1.sesion.entrega_mediana | base | mínimo | 5,000 | HE1, HG | 22,4 | 100,0 | 99,6 | 22,2 |
| autorregistro.sesiones_semana | base | máximo | 5,000 | HE1, HG | 96,1 | 100,0 | 99,5 | 95,6 |
| entrega_con_cola.ir_a_la_puerta | entrega_con_cola | máximo | 3,000 | HE1, HG | 63,6 | 100,0 | 99,6 | 63,4 |
| entrega_con_cola.espera_cola | entrega_con_cola | máximo | 30,000 | HE1, HG | 96,2 | 100,0 | 99,6 | 95,8 |
| entrega_con_cola.revision_presencial | entrega_con_cola | máximo | 15,000 | HE1, HG | 99,1 | 100,0 | 99,6 | 98,7 |

*Nota.* Datos simulados (semilla principal 2026; 1000 réplicas con semillas 1…1000 por variante). Un supuesto a la vez, en el mínimo y el máximo de su rango; parametros.yaml y escenarios.yaml no se modifican. Contexto: «base» es la corrida principal; los supuestos de un escenario se varían dentro de él. Regla propuesta para HE y HG (ajustes-cap3, punto 10). Clave: cambia la «Decisión estadística (datos simulados)» de la corrida principal en alguna HE o la HG, o su % de réplicas cruza el 80 %. Un supuesto que solo cambia cuántos números saca el generador (por ejemplo, autorregistro.sesiones_semana, que no entra en HE1) puede mover la corrida principal por azar; el % de réplicas muestra si el efecto es real.

**Tabla S15. Sensibilidad por supuesto: el menor % de réplicas que rechaza H₀ entre sus dos extremos (Datos simulados)**

| Supuesto | Contexto | % HE1 | % HE2 | % HE3 | % HG |
|---|---|---|---|---|---|
| entrega_con_cola.revision_presencial | entrega_con_cola | 22,0 | 100,0 | 99,6 | 21,8 |
| o1.sesion.entrega_mediana | base | 22,4 | 100,0 | 99,6 | 22,2 |
| entrega_con_cola.espera_cola | entrega_con_cola | 24,8 | 100,0 | 99,6 | 24,6 |
| o1.sesion.elaboracion_mediana | base | 49,8 | 100,0 | 99,6 | 49,6 |
| ruido.medicion_cv | base | 51,0 | 100,0 | 99,6 | 50,8 |
| entrega_con_cola.ir_a_la_puerta | entrega_con_cola | 55,0 | 100,0 | 99,6 | 54,8 |
| errores_o1.asistencia.E1_momento | base | 96,1 | 100,0 | 91,2 | 87,3 |
| errores_o1.asistencia.E3_momento | base | 96,1 | 100,0 | 91,2 | 87,3 |
| errores_o2.asistencia.E1 | base | 96,1 | 100,0 | 93,5 | 89,7 |
| errores_o2.asistencia.olvida_dia | base | 96,1 | 100,0 | 93,7 | 90,0 |
| errores_o2.asistencia.E4_diferido | base | 96,1 | 100,0 | 96,4 | 92,7 |
| errores_o2.asistencia.E3 | base | 96,1 | 100,0 | 97,2 | 93,3 |
| poblacion.estudiantes_centro | base | 94,1 | 100,0 | 99,2 | 93,9 |
| rasgos.ritmo_cv | base | 94,6 | 100,0 | 99,6 | 94,2 |
| errores_o1.asistencia.E4_diferido | base | 96,1 | 100,0 | 98,2 | 94,3 |
| o2.operadores_klm.K | base | 94,7 | 100,0 | 99,6 | 94,3 |
| errores_o1.asistencia.E2 | base | 96,1 | 100,0 | 98,3 | 94,4 |
| autorregistro.sesiones_semana | base | 95,1 | 100,0 | 99,4 | 94,5 |
| rasgos.proporcion_diferido | base | 96,1 | 100,0 | 98,6 | 94,7 |
| poblacion.estudiantes_amplitud | base | 95,1 | 100,0 | 99,6 | 94,8 |
| errores_o1.asistencia.E3_diferido | base | 96,1 | 100,0 | 99,0 | 95,1 |
| o2.factor_no_experto_p2 | base | 95,5 | 100,0 | 99,6 | 95,1 |
| o2.factor_no_experto_p1 | base | 95,6 | 100,0 | 99,6 | 95,2 |
| o2.operadores_klm.P | base | 95,6 | 100,0 | 99,6 | 95,2 |
| rasgos.proporcion_p1 | base | 95,6 | 100,0 | 99,6 | 95,2 |
| errores_o1.asistencia.E1_diferido | base | 96,1 | 100,0 | 99,2 | 95,3 |
| errores_o1.asistencia.olvida_dia | base | 96,1 | 100,0 | 99,2 | 95,3 |
| errores_o2.notas.E4 | base | 96,1 | 99,6 | 99,6 | 95,3 |
| o2.operadores_klm.R_domestica | base | 95,7 | 100,0 | 99,6 | 95,3 |
| errores_o1.notas.E1 | base | 96,1 | 99,7 | 99,6 | 95,4 |
| o2.operadores_klm.B | base | 95,8 | 100,0 | 99,6 | 95,4 |
| o2.operadores_klm.H | base | 95,8 | 100,0 | 99,6 | 95,4 |
| o2.operadores_klm.M | base | 95,8 | 100,0 | 99,6 | 95,4 |
| errores_o1.asistencia.E4_momento | base | 96,1 | 100,0 | 99,4 | 95,5 |
| o2.factor_no_experto_p3 | base | 95,9 | 100,0 | 99,6 | 95,5 |
| rasgos.proporcion_p3 | base | 95,9 | 100,0 | 99,6 | 95,5 |
| errores_o1.notas.E2_cuaderno | base | 96,1 | 100,0 | 99,6 | 95,7 |
| errores_o1.notas.E2_excel | base | 96,1 | 100,0 | 99,6 | 95,7 |
| errores_o1.notas.E3_cuaderno | base | 96,1 | 100,0 | 99,6 | 95,7 |
| errores_o1.notas.E3_excel | base | 96,1 | 100,0 | 99,6 | 95,7 |
| errores_o1.notas.E4 | base | 96,1 | 100,0 | 99,6 | 95,7 |
| errores_o2.notas.E1 | base | 96,1 | 100,0 | 99,6 | 95,7 |
| errores_o2.notas.E3 | base | 96,1 | 100,0 | 99,6 | 95,7 |
| likert.carga_actitud | base | 96,1 | 100,0 | 99,6 | 95,7 |
| likert.efecto_post | base | 96,1 | 100,0 | 99,6 | 95,7 |
| likert.media_pre | base | 96,1 | 100,0 | 99,6 | 95,7 |
| likert.ruido_docente | base | 96,1 | 100,0 | 99,6 | 95,7 |
| likert.ruido_item | base | 96,1 | 100,0 | 99,6 | 95,7 |
| o1.asistencia.por_estudiante | base | 96,1 | 100,0 | 99,6 | 95,7 |
| o1.asistencia.transcripcion_apertura | base | 96,1 | 100,0 | 99,6 | 95,7 |
| o1.asistencia.transcripcion_por_estudiante | base | 96,1 | 100,0 | 99,6 | 95,7 |
| o1.corregir_nota.costo | base | 96,1 | 100,0 | 99,6 | 95,7 |
| o1.corregir_nota.probabilidad | base | 96,1 | 100,0 | 99,6 | 95,7 |
| o1.notas.apertura | base | 96,1 | 100,0 | 99,6 | 95,7 |
| o1.notas.por_caracter_conclusion | base | 96,1 | 100,0 | 99,6 | 95,7 |
| o1.notas.por_estudiante_cuaderno | base | 96,1 | 100,0 | 99,6 | 95,7 |
| o1.notas.por_estudiante_excel | base | 96,1 | 100,0 | 99,6 | 95,7 |
| o2.operadores_klm.R_slow_4g | base | 96,1 | 100,0 | 99,6 | 95,7 |
| o2.ventana_semanas | base | 96,1 | 100,0 | 99,6 | 95,7 |
| poblacion.caracteres_conclusion | base | 96,1 | 100,0 | 99,6 | 95,7 |
| poblacion.proporcion_conclusion_notas | base | 96,1 | 100,0 | 99,6 | 95,7 |
| poblacion.tasa_excepciones_asistencia | base | 96,1 | 100,0 | 99,6 | 95,7 |
| rasgos.correlacion_destreza_actitud | base | 96,1 | 100,0 | 99,6 | 95,7 |
| rasgos.proporcion_excel | base | 96,1 | 100,0 | 99,6 | 95,7 |
| sus.carga_destreza | base | 96,1 | 100,0 | 99,6 | 95,7 |
| sus.media_latente | base | 96,1 | 100,0 | 99,6 | 95,7 |
| rasgos.cuidado_cv | base | 96,1 | 100,0 | 99,8 | 95,9 |
| con_banco.descarga | con_banco | 98,6 | 100,0 | 99,6 | 98,2 |

*Nota.* Datos simulados (semilla principal 2026; 1000 réplicas con semillas 1…1000 por variante). Un supuesto a la vez, en el mínimo y el máximo de su rango; parametros.yaml y escenarios.yaml no se modifican. Contexto: «base» es la corrida principal; los supuestos de un escenario se varían dentro de él. Regla propuesta para HE y HG (ajustes-cap3, punto 10). Ordenada de menor a mayor % de la HG.
