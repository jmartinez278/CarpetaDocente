# Simulación de datos (Tesis 2) — borrador de G2

Datos simulados: nada de lo que sale de aquí es una medición real. El plan completo está en
`insumos/simulacion/plan.md` (local); G6 completa este README (comando, semillas, versiones,
salidas, parámetros).

## Cómo salen los tiempos de O2

- Los agentes usan la app local con Playwright y dejan su **ruta** en `rutas/<persona>_<tarea>.yaml`
  (éxito, errores, confusiones y pasos). Nunca registran tiempos: un campo de reloj se rechaza.
- `klm.py` convierte la ruta ideal a operadores KLM (K, P, B, H, M, R) con los valores de
  `o2.operadores_klm` en `parametros.yaml` (SUPUESTO «sin ancla» hasta abrir la fuente original de
  KLM) y arma `klm/tabla.yaml`, que lee `medicion.py`.
- Solo cuenta la ruta ideal. Los desvíos y las confusiones se registran como hallazgos de
  usabilidad y no suman tiempo. El recargo por no ser experto es `factor_no_experto_*`, una sola vez.
- Asistencia: la ruta ideal es el marcado masivo («Marcar los N restantes como Asistió») y luego
  corregir a quienes no asistieron (`por_excepcion`), según `poblacion.tasa_excepciones_asistencia`,
  el mismo parámetro de O1. Si una persona no encuentra el botón masivo, queda como hallazgo.

- Notas: la ruta ideal es «Rellenar vacías» con A y luego, solo para B y C, tocar la celda, escribir
  el nivel y la conclusión (`por_conclusion`). La conclusión es obligatoria en B y C: lo exige la
  spec `registro-notas` («Conclusión en B y C», de 10 a 500 caracteres), con RN-003 y la RVM
  094-2020, 5.1.1.3, num. 7, lit. c); está en `reglas_app`, no es SUPUESTO. Lo que sí es SUPUESTO,
  compartido por O1 y O2, es la proporción de estudiantes con B o C
  (`poblacion.proporcion_conclusion_notas`) y los caracteres de una conclusión
  (`poblacion.caracteres_conclusion`); en O1 se suma su costo con `o1.notas.por_caracter_conclusion`.
  El choque con el Anexo 1 está en `insumos/simulacion/ajustes-cap3.md`, punto 8.
- Rutas: `corregir_nota` cambia un nivel de A a AD; `sesion_entrega` sube un Word ficticio con la
  consigna fija (Matemática, 3.º, título de 32 caracteres y propósito de 53), sin compartir.
- Tabla: `cd scripts && uv run python -m simulacion.klm` la rehace en `klm/tabla.yaml` desde las
  rutas y `parametros.yaml`. Con las rutas ideales, P1, P2 y P3 dan la misma tabla: las personas
  se distinguen por `factor_no_experto_*` y por sus confusiones, que no suman tiempo.

## Base propia

`preparar_rutas.py` arma una sola vez la institución «I.E. Simulada (datos simulados)» (año ABIERTO
2026, 4 bimestres, áreas, 24 secciones) y deja a `sim01` en 3.º A con 30 estudiantes ficticios.
No toca la institución 1 ni la demo. Solo con `DEBUG`. G3 reutiliza esa base.

    SIM_CLAVE='<clave>' uv run python scripts/simulacion/preparar_rutas.py preparar
    uv run python scripts/simulacion/preparar_rutas.py quitar

`quitar` borra estudiantes, asistencia, notas y sesiones de la simulación, libera las secciones y
desactiva las cuentas `simNN`; la base armada queda. Se niega si la institución simulada tiene
datos que no son de la simulación.

## Carga en la app (G3)

`carga.py` lleva a la base local la ventana O2 (`o2.ventana_semanas` semanas que terminan en
`o2.fecha_fin`) de las 24 docentes `sim01…sim24` de la corrida principal (semilla principal, los
mismos rasgos que `medicion.simular`). Todo pasa por los servicios (`asistencia.marcar_restantes`
y `marcar`, `notas.guardar_hoja`, `repositorio.enviar_sesion`) con `hoy` simulado; cada entrada
del registro de actividad y las marcas de tiempo quedan en la fecha simulada, así que
«Indicadores por semana» cuenta esas semanas.

    SIM_CLAVE='<clave>' uv run python scripts/simulacion/carga.py cargar --confirmar
    uv run python scripts/simulacion/carga.py quitar --confirmar

- La base muestra **conductas** (modalidad, olvidos del diferido, excepciones de asistencia, B y C
  con conclusión, corrección A → AD, sesiones por semana), **no los errores E1–E4**: las tablas
  del Cap. IV salen de `medicion.py`.
- Las constantes de relleno de `carga.py` (horas, retraso del diferido, reparto de las
  excepciones, AD/A y B/C) **no entran al análisis**.
- Usa su propio generador (cuarto hijo de la semilla): no cambia O1, O2 ni las réplicas.
- Solo con `DEBUG` y `--confirmar`. Se niega si la institución simulada tiene datos ajenos, si ya
  hay una carga (también la de `preparar_rutas.py`: primero `quitar`) o si una `simNN` existe en
  otra institución. Si falla, no deja nada, tampoco archivos.
- `quitar` limpia como `preparar_rutas.py quitar` y además borra el registro de actividad de las
  `simNN` (también el de los agentes de G2).

## Limitaciones

- **Un solo agente interpretó a las tres personas, en secuencia** (P1, P2 y P3 en cada tarea, uno
  tras otro). Sus confusiones son indicativas, no evidencia de usabilidad.
- En asistencia en el momento, **P2 fue primero** (piloto), antes que P1 y P3: ya conocía la pantalla
  de ese día.
- Los operadores KLM y la tasa de excepciones son SUPUESTO sin ancla; los valores se reemplazan
  cuando se abra la fuente de KLM.

## Pendiente para G4 (sensibilidad)

- Escenario **«sin marcado masivo»**: la asistencia se marca estudiante por estudiante
  (`por_estudiante` en vez de `por_excepcion`), como lo haría quien no encuentra el botón.
