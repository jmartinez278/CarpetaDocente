# Spec Delta

## Purpose

Periodos del año escolar (bimestres o trimestres) con sus fechas, que el Administrador configura y corrige en el panel, para que el sistema sepa qué periodo está vigente en cada fecha y las notas caigan en él.

## ADDED Requirements

### Requirement: Periodos de un año escolar
Cada año escolar SHALL tener cero periodos (aún no configurados) o tantos como indique la organización de su institución: 4 con BIMESTRE y 3 con TRIMESTRE (RN-006). Cada periodo tiene un número único en su año, del 1 al 4, una fecha de inicio y una fecha de fin posterior al inicio. Ambas fechas cuentan como parte del periodo.

#### Scenario: Camino ideal
- **GIVEN** el Administrador y una institución organizada en bimestres con su año 2026 ABIERTO sin periodos
- **WHEN** configura en la ficha del año los 4 bimestres con sus fechas y guarda
- **THEN** el año queda con los periodos 1 a 4 y esas fechas, y `periodo_vigente` devuelve, para cada fecha, el periodo que la contiene

#### Scenario: Trimestres
- **WHEN** la institución está organizada en trimestres y el Administrador abre la ficha de un año sin periodos
- **THEN** la ficha muestra 3 filas, numeradas 1 a 3

#### Scenario: Fin antes del inicio
- **WHEN** una fila tiene la fecha de fin igual o anterior a la de inicio
- **THEN** no se guarda ningún periodo y la fila dice "La fecha de fin debe ser posterior a la de inicio."

#### Scenario: Número repetido o fuera de rango en la base
- **WHEN** se intenta guardar, fuera del panel, un segundo periodo 2 en el mismo año o un periodo 5
- **THEN** la base de datos lo rechaza

### Requirement: Se guardan todos juntos
Los periodos de un año SHALL guardarse y validarse juntos: o se guardan las N filas o ninguna. El número de cada fila lo pone el sistema según su posición y no se edita. Los periodos no se borran (RN-023): la ficha no tiene opción de borrar.

#### Scenario: Faltan filas
- **WHEN** el Administrador llena 3 de los 4 bimestres y guarda
- **THEN** no se guarda ningún periodo y la ficha dice "Completa las fechas de los 4 periodos."

#### Scenario: Sin borrar
- **WHEN** el Administrador abre la ficha de un año con periodos
- **THEN** ninguna fila tiene la opción de borrar, y un POST que intente borrar uno no lo borra

#### Scenario: Guardar el año sin tocar los periodos
- **WHEN** el Administrador edita el estado de un año sin periodos y deja las filas vacías
- **THEN** el año se guarda y sigue sin periodos

### Requirement: Organización definida antes
La ficha de un año SHALL pedir que se defina la organización de periodos de la institución cuando está vacía, sin mostrar filas. Una vez que algún año de la institución tiene periodos guardados, la organización de la institución ya no cambia.

#### Scenario: Organización vacía
- **WHEN** el Administrador abre la ficha de un año cuya institución no tiene organización de periodos
- **THEN** la ficha dice "Define la organización de periodos de la institución antes de configurar sus periodos." con un enlace a la institución, y no muestra filas de periodos

#### Scenario: Organización fija con periodos
- **WHEN** la institución tiene un año con periodos guardados y el Administrador abre su ficha
- **THEN** la organización de periodos se muestra de solo lectura, y un POST que la cambie no la cambia

### Requirement: Fechas que no se cruzan
Los periodos de un año MUST NOT cruzarse, ni al configurarlos ni al editarlos, y la base de datos SHALL impedirlo también. Un cruce, venga de la validación de la ficha o de la base de datos (dos guardados a la vez), se muestra con el mensaje "Las fechas se cruzan con otro periodo", sin error del servidor.

#### Scenario: Caso de error
- **GIVEN** el Administrador que configura un periodo
- **WHEN** sus fechas se cruzan con las de otro periodo
- **THEN** el sistema no lo guarda y muestra el mensaje "Las fechas se cruzan con otro periodo"

#### Scenario: Mismo día de borde
- **WHEN** el bimestre 1 termina el 15 de mayo y el bimestre 2 empieza el 15 de mayo
- **THEN** se cruzan (los bordes cuentan) y no se guarda ninguno

#### Scenario: Correr dos periodos a la vez
- **WHEN** el Administrador adelanta el fin del bimestre 1 y el inicio del bimestre 2 en el mismo guardado, y las fechas nuevas no se cruzan
- **THEN** se guardan las dos, aunque la fecha nueva del bimestre 1 se cruce con la vieja del bimestre 2

#### Scenario: Cruce que llega a la base
- **WHEN** entre la validación de la ficha y el guardado se guarda otro periodo del mismo año que se cruza
- **THEN** no se guarda ninguno de esta ficha y se muestra "Las fechas se cruzan con otro periodo", no un error 500

#### Scenario: Cruce fuera del panel
- **WHEN** se intenta guardar desde la consola un periodo que se cruza con otro del mismo año
- **THEN** la base de datos lo rechaza

### Requirement: Dentro del año y en orden
Las fechas de cada periodo SHALL caer dentro del año calendario de su año escolar, y el periodo n+1 SHALL empezar después de que termina el periodo n. Se permiten días entre un periodo y el siguiente (vacaciones). Si unas fechas se cruzan y además están fuera de orden, se muestra el mensaje del cruce.

#### Scenario: Fuera del año
- **WHEN** en el año 2026 el bimestre 4 termina el 5 de enero de 2027
- **THEN** no se guarda ningún periodo y la fila dice "Las fechas deben estar dentro de 2026."

#### Scenario: Fuera de orden
- **WHEN** el bimestre 2 va de marzo a mayo y el bimestre 1 de junio a julio, sin cruzarse
- **THEN** no se guarda ningún periodo y la fila del bimestre 2 dice "El periodo 2 debe empezar después de que termina el periodo 1."

#### Scenario: Vacaciones entre bimestres
- **WHEN** el bimestre 2 termina el 24 de julio y el bimestre 3 empieza el 10 de agosto
- **THEN** se guardan

### Requirement: Corregir las fechas
Mientras el año esté ABIERTO, el Administrador SHALL poder cambiar las fechas de sus periodos, con las mismas validaciones, aunque haya notas registradas: las notas siguen en el periodo al que pertenecen. Con el año CERRADO, los periodos son de solo lectura.

#### Scenario: Flujo alternativo válido
- **GIVEN** un periodo configurado cuyas fechas cambian por disposición de la institución
- **WHEN** el Administrador las modifica
- **THEN** el sistema actualiza las fechas sin alterar las notas ya registradas (cada nota sigue en su periodo, con el mismo id de periodo)

#### Scenario: Año cerrado
- **WHEN** el Administrador abre la ficha de un año CERRADO con periodos
- **THEN** ve las fechas de solo lectura, y un POST que las cambie no las cambia

### Requirement: Periodo vigente
El periodo vigente de una sección o de un año escolar en una fecha SHALL ser el periodo de ese año que contiene la fecha, con ambos bordes incluidos; si la fecha cae entre dos periodos, fuera de todos o el año no tiene periodos, no hay periodo vigente. Sin fecha, se usa la de hoy en hora de Lima. Es la única forma en que el sistema obtiene el periodo de una fecha.

#### Scenario: Dentro y en el borde
- **WHEN** el bimestre 1 va del 16 de marzo al 15 de mayo y se pide el vigente del 16 de marzo, del 20 de abril y del 15 de mayo
- **THEN** las tres veces es el bimestre 1

#### Scenario: En un hueco
- **WHEN** se pide el vigente de un día de vacaciones entre el bimestre 2 y el 3, o de una fecha anterior al bimestre 1
- **THEN** no hay periodo vigente

#### Scenario: Sin periodos
- **WHEN** se pide el vigente de una sección cuyo año no tiene periodos
- **THEN** no hay periodo vigente

#### Scenario: Hoy en Lima
- **WHEN** en UTC ya es 16 de mayo pero en Lima todavía es 15 de mayo a las 21:00, y se pide el vigente sin fecha
- **THEN** es el bimestre 1

### Requirement: Periodos en el registro de actividad
Configurar los periodos de un año SHALL registrar PERIODOS_CONFIGURADOS una vez, con el año y la cantidad de periodos; cambiar las fechas de un periodo SHALL registrar PERIODO_EDITADO por cada periodo cambiado, con su número y sus fechas antes y después. Un guardado sin cambios en los periodos no deja entrada de periodos.

#### Scenario: Configurados
- **WHEN** el Administrador guarda por primera vez los 4 bimestres de un año
- **THEN** queda una entrada PERIODOS_CONFIGURADOS con su usuario, la entidad año escolar y la cantidad 4

#### Scenario: Editado
- **WHEN** cambia la fecha de fin del bimestre 1 y la de inicio del bimestre 2
- **THEN** quedan dos entradas PERIODO_EDITADO, cada una con el número y las fechas antes y después

#### Scenario: Rechazado
- **WHEN** el guardado se rechaza por un cruce
- **THEN** no queda ninguna entrada de periodos

### Requirement: Solo el Administrador
Solo el Administrador SHALL configurar o editar periodos desde el panel.

#### Scenario: Otro rol
- **WHEN** un docente o la dirección intenta abrir la ficha de un año escolar o enviar sus periodos
- **THEN** no la ve y no cambia ningún periodo
