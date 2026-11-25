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

## Análisis (G4)

`analisis.py` sigue 3.5 de la tesis sobre la corrida principal (semilla 2026) y las réplicas
(semillas 1…1000), que no tocan la base:

    uv run --group simulacion python -m simulacion.analisis principal [--replicas N] [--procesos N]

- Descriptivos y variación %, Shapiro-Wilk sobre las diferencias (post − pre), luego t de Student
  (con d de Cohen) o Wilcoxon (con biserial de rangos; descarta los ceros y corrige por continuidad,
  como Jamovi), **unilaterales** en el sentido de H₁ (ajustes-cap3, punto 9), α = 0,05.
- HE y HG con la **regla propuesta** (ajustes-cap3, punto 10): una HE rechaza H₀ si la rechazan
  todos sus indicadores; la HG, si la rechazan las tres HE. El puntaje global del cuestionario se
  contrasta como apoyo y no entra en la regla. La columna se llama «Decisión estadística (datos
  simulados)».
- **Punto de quiebre (DEC-2):** un factor f multiplica solo los tiempos de O1 propios de cada tarea
  (en sesión, la entrega). Corrida principal: el menor f desde el cual todos los f mayores dan
  p < 0,05 (barrido de 0,01). Réplicas: el menor f con el que al menos 80 % rechaza H₀ (bisección).
- `parametros.yaml` no se modifica (congelado en 6a8e1ea): las variantes son copias en memoria y una
  prueba comprueba su hash.
- **«Entrega con cola» va junto a la corrida principal** (Tabla S4b de `tablas.md`): es el único
  escenario con el mecanismo anclado (testimonio de Nayely, 25-11). Con él, HE1 rechaza H₀ en el
  57 % de las réplicas, frente al 96 % de la corrida principal. Sus cifras siguen siendo SUPUESTO y la
  definición de la entrega sigue abierta (ajustes-cap3, punto 15). La Tabla S4b se copió a mano
  desde `tablas_escenarios.md`: `principal` no la regenera (pendientes.md, PEND-4).

Salidas en `salidas/` (todas con `origen = Datos simulados` en cada fila o «Datos simulados» en el
título): `tablas.md` (tablas S1–S10, coma decimal), `figuras/<indicador>.png` (cajas pre/post) y los
CSV (coma como separador, punto decimal): `simulados_principal_filas.csv` (una fila por docente y
momento), `simulados_principal_jamovi.csv` (pre y post lado a lado, para Jamovi),
`simulados_principal_contrastes.csv`, `simulados_replicas_resumen.csv` y `simulados_quiebre.csv`.
`simulados_replicas.csv` (una fila por semilla e indicador) no se versiona: sale con el comando.

## Escenarios (G4)

    uv run --group simulacion python -m simulacion.analisis escenarios [--solo NOMBRE ...]

Corre «base» (la corrida principal) y cada escenario con la semilla principal y las mismas réplicas;
escribe `salidas/simulados_escenarios.csv` y `salidas/tablas_escenarios.md` (tablas S11 y S12).
Cada escenario cambia una copia de los valores o de las rutas, nunca `parametros.yaml` ni `rutas/`.

- **«Sin marcado masivo»**: se quita el paso del marcado masivo de las rutas de asistencia y los
  pasos `por_excepcion` pasan a `por_estudiante`, como lo haría quien no encuentra el botón. No
  cuenta un segundo toque para quien no asistió: es una cota inferior del tiempo.
- **«La tutora marca todas»**: también Inglés y Educación Física (`areas_de_docente_de_curso` = []).
  Como suma competencias, cambia cuántos números saca el generador: las demás mediciones de ese
  escenario varían por azar, no por efecto del escenario.
- **«Entrega con cola»** (y sus variantes n = 2, n = 4 y «con impresión»): la dirección está en el
  mismo local; en O1 la entrega es diaria: ir a la puerta + esperar el turno (una vez al día) +
  estar presente mientras revisan cada sesión. En O2 se sube y envía (KLM); la revisión ocurre sin
  la docente. Se reporta HE1 por sesión (`sesion_min`, la de la Tabla 5) y por día
  (`sesion_dia_min`, complementario). n sale al azar entre 2 y 4 por docente y día. La impresión
  va solo como variante: la docente imprime igual las fichas de sus estudiantes.
- **«Con banco de sesiones»**: en O2, quien no tiene una sesión propia adecuada y encuentra una en
  el repositorio la descarga y la adapta (una fracción del tiempo de elaborarla). La funcionalidad
  existe (US-011/012/016), pero **la descarga va como SUPUESTO** (1 min) y no por KLM: la ruta del
  agente queda pendiente (`insumos/simulacion/pendientes.md`, PEND-1). Se agrega el barrido
  cobertura × fracción con el % de rechazo de HE1 (Tabla S13, `simulados_banco_barrido.csv`).

Los supuestos de estos dos escenarios están en `escenarios.yaml` (mismo formato y validador que
`parametros.yaml`, que no se toca). Su azar sale de un quinto generador hijo de la semilla: no
cambia docentes, O1, O2 ni la carga.

## Sensibilidad (G4)

    uv run --group simulacion python -m simulacion.analisis sensibilidad [--solo SUPUESTO ...]

Un supuesto a la vez, en el mínimo y el máximo de su rango, con la corrida principal y las mismas
réplicas; los de `escenarios.yaml` (cola y descarga) se varían dentro de su escenario. Quedan fuera
los cortes del Likert (una lista), las n de la cola (escenarios n = 2 y n = 4), la impresión (una
variante) y las proporciones del banco (su barrido). Un supuesto es **clave** si cambia una
decisión de la corrida principal o si el % de réplicas de alguna HE o de la HG cruza el 80 %.
Salidas: `simulados_sensibilidad.csv` y `tablas_sensibilidad.md` (tablas S14 y S15).
