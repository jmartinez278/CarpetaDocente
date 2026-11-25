# Simulación de datos (Tesis 2)

**Datos simulados: nada de lo que sale de aquí es una medición real.** Es un ensayo del plan de
análisis del Cap. III (diseño preexperimental O1 → X → O2 con 24 docentes): O1 sale de supuestos
declarados y O2 de KLM sobre las rutas reales de la app. Nada da el pretest ni el postest por
aplicado. El plan completo está en `insumos/simulacion/plan.md` (local, no versionado).

No es un cambio de OpenSpec: es una herramienta de la tesis, no una funcionalidad del sistema.
Escribe en la base solo por los servicios de la app (como cualquier docente) y solo en la base
local, en su propia institución.

## Requisitos y versiones

| Qué | Versión (de `uv.lock`) |
|---|---|
| Python | 3.13 (`.python-version`) |
| Grupo `simulacion` de uv | numpy 2.5.5 · scipy 1.18.1 · matplotlib 3.11.2 · pyyaml 6.0.4 |
| App (para `preparar_rutas.py` y `carga.py`) | Django 5.2.18 y PostgreSQL de `docker compose up -d db` |
| Agentes de G2 | Playwright MCP con Edge (`--browser msedge`) |

El grupo `simulacion` no se instala en el CI: sus pruebas se saltan allí y su código no cuenta para
la cobertura (`pyproject.toml`). El análisis no necesita la base; la carga y la base propia, sí.

## Orden de ejecución

Desde la raíz del repo, salvo el análisis, que corre desde `scripts/`:

    # 1. Tabla KLM desde las rutas (solo si cambian rutas/ o parametros.yaml)
    cd scripts && uv run python -m simulacion.klm

    # 2. Análisis: corrida principal + 1000 réplicas + quiebre + figuras, luego escenarios y sensibilidad
    cd scripts && uv run --group simulacion python -m simulacion.analisis principal
    cd scripts && uv run --group simulacion python -m simulacion.analisis escenarios
    cd scripts && uv run --group simulacion python -m simulacion.analisis sensibilidad

    # 3. Opcional: llevar la ventana O2 de la corrida principal a la base local (G3)
    docker compose up -d db
    SIM_CLAVE='<clave>' uv run python scripts/simulacion/carga.py cargar --confirmar
    uv run python scripts/simulacion/carga.py quitar --confirmar

    # Pruebas de la simulación (las de base y carga necesitan la base levantada)
    uv run --group simulacion pytest scripts/simulacion

Opciones de `analisis`: `--replicas N` (por omisión, las de `parametros.yaml`), `--procesos N`,
`--salida RUTA` (por omisión, `salidas/`), `--paso-quiebre` (solo `principal`, 0,01) y `--solo`
(escenarios o supuestos). `SIM_CLAVE` va siempre en la línea de comando, nunca en un archivo.

**Ojo:** `principal` reescribe `tablas.md` y borra la Tabla S4b, que se copió a mano (PEND-4).

## Semillas

| Uso | Semilla | Generadores |
|---|---|---|
| Corrida principal (Cap. IV y carga) | 2026 (`semillas.principal`) | `SeedSequence(2026).spawn(3)`: docentes, O1 y O2 |
| Réplicas | 1 … 1000 (`semillas.replicas`) | Las mismas tres por semilla; no tocan la base |
| Carga en la app (G3) | la principal | Cuarto hijo (`spawn(4)[3]`): no cambia docentes, O1 ni O2 |
| Escenarios | la principal y las réplicas | Quinto hijo (`spawn(5)[4]`): no cambia docentes, O1, O2 ni la carga |

La misma semilla da la misma salida. Cambiar la tabla KLM no cambia O1 (generadores separados).

## Parámetros

- **`parametros.yaml`**: cada parámetro lleva `valor` y su origen: `fuente` (tesis, anexo, dato de
  la I.E., spec o código) o `supuesto: true` con `ancla` («sin ancla» si no la tiene) y `rango` para
  la sensibilidad. `parametros.py` rechaza un parámetro sin fuente ni SUPUESTO, y un SUPUESTO sin
  rango o con el valor fuera de él. Bloques: `poblacion`, `reglas_app`, `catalogo`, `rasgos`,
  `ruido`, `o1`, `errores_o1`, `o2`, `errores_o2`, `likert`, `sus`, `autorregistro` y `semillas`.
- **Congelado** en 6a8e1ea (blob `84c6706`) tras aprobar los rangos de O1 (DEC-1). Una prueba
  comprueba su hash y que cada valor cae en su rango; las variantes del análisis son copias en
  memoria.
- **`escenarios.yaml`**: supuestos de los escenarios (cola de la entrega, descarga del banco), con el
  mismo formato y validador.
- **`rutas/`** y **`agentes/`**: las rutas de P1, P2 y P3 en cada tarea y la descripción de cada
  persona. **`klm/tabla.yaml`**: la tabla KLM que lee `medicion.py`.

Los supuestos que deciden el resultado: la entrega de O1 en la sesión (`o1.sesion.entrega_mediana`,
15 min, sin ancla; el quiebre de HE1 está en unos 11,4 min) y los operadores KLM
(`o2.operadores_klm`, sin ancla hasta abrir la fuente original).

## Salidas

Todo en `salidas/`, con «Datos simulados» en el título o `origen = Datos simulados` en cada fila.
Tablas en Markdown con coma decimal; CSV con coma como separador y punto decimal.

| Archivo | Lo escribe | Contenido |
|---|---|---|
| `tablas.md` | `principal` | Tablas S1–S10 (y S4b, a mano) |
| `figuras/*.png` | `principal` | Cajas pre/post por indicador (sesión, notas, asistencia, exactitud, Likert) |
| `simulados_principal_filas.csv` | `principal` | Una fila por docente y momento |
| `simulados_principal_jamovi.csv` | `principal` | Pre y post lado a lado, para Jamovi |
| `simulados_principal_contrastes.csv` | `principal` | Pruebas, p, tamaño del efecto y decisión |
| `simulados_replicas_resumen.csv` | `principal` | % de réplicas que rechaza H₀ e IC de la diferencia |
| `simulados_quiebre.csv` | `principal` | Punto de quiebre por tarea |
| `simulados_replicas.csv` | `principal` | Una fila por semilla e indicador (**no se versiona**) |
| `tablas_escenarios.md`, `simulados_escenarios.csv`, `simulados_banco_barrido.csv` | `escenarios` | Tablas S11–S13 |
| `tablas_sensibilidad.md`, `simulados_sensibilidad.csv` | `sensibilidad` | Tablas S14–S15 |

Resultado en una línea (datos simulados): HE2 y HE3 se sostienen en todos los supuestos; HE1
depende de cómo se defina la entrega (96 % de réplicas en la corrida principal, 57 % con la
entrega con cola).

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

## Limitaciones

**De los datos**
- Todo es simulado. Los tiempos de O1 son SUPUESTO (la mayoría «sin ancla»); los de O2 salen de KLM
  con operadores también SUPUESTO hasta abrir la fuente original. Las tablas sirven para ensayar el
  análisis, no para afirmar que la app ahorra tiempo.
- Los errores E1–E4 de O1 y los residuales de O2 son tasas supuestas; los que la app impide salen de
  las specs (`reglas_app`). El Likert y el SUS salen de un rasgo latente supuesto.
- O1 y O2 son el mismo modelo con otra fuente de tiempos: no hay aprendizaje, cansancio ni efecto
  de la medición entre momentos.

**De HE1 (sesión)**
- La app no redacta la sesión: la elaboración tiene la misma distribución en O1 y O2 y la diferencia
  sale solo de la entrega. El resultado de HE1 depende de cómo se defina la entrega (quiebre cerca de
  11,4 min; 96 % frente a 57 % con la cola). Ver `ajustes-cap3.md`, puntos 1, 13 y 15.
- En «entrega con cola», n (sesiones por día) sale al azar por separado en O1 y O2: HE1 por día no
  es comparable (PEND-2). En «con banco de sesiones», la descarga es SUPUESTO (PEND-1).

**De los agentes y KLM**
- Un solo agente interpretó a las tres personas, en secuencia (P1, P2 y P3 en cada tarea). Sus
  confusiones son indicativas, no evidencia de usabilidad.
- En asistencia en el momento, P2 fue primero (piloto), antes que P1 y P3: ya conocía la pantalla.
- Solo cuenta la ruta ideal; desvíos y confusiones no suman tiempo. P1, P2 y P3 dan la misma tabla
  KLM y se distinguen solo por `factor_no_experto_*`.

**Del código**
- La Tabla S4b se copió a mano y `principal` la borra (PEND-4).
- `es_clave()` cuenta también un cambio de decisión de la corrida principal y deja pasar falsos
  claves por azar (PEND-3).
- Los pendientes PEND-1 a PEND-4 están en `insumos/simulacion/pendientes.md` (local).

**Del instrumento**
- Los indicadores y unidades siguen la Tabla 5 de la tesis y los Anexos 1 a 5. Donde chocan con la
  app, el choque va a `insumos/simulacion/ajustes-cap3.md`; la simulación no lo resuelve.
