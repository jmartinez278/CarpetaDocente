[← Volver al README Principal](../../README.md)

# 01. Transformando a ágil

| Campo | Detalle |
|---|---|
| **Proyecto** | Sistema web para la gestión y planificación pedagógica en educación primaria – I.E. Virgen del Carmen, Huayucachi |
| **Producto** | CarpetaDocente (nombre temporal) |
| **Integrantes** | Cuicapuza Remigio Nayely Nilda · Martinez Llanos Marco Jhair · Vera Zea Jhoanna Hade |
| **Asesor** | Ing. Elvis Wilfredo Carmen Delgadillo |
| **Fecha** | 24/11/2026 |
| **Versión** | 1.6.0 |

---

## 1. Metodología de transformación

La línea base de requisitos de `docs/01 Inicio/` se transforma en trabajo ágil con tres reglas:

| Origen | Destino | Regla |
|---|---|---|
| Requisito funcional (documento 06) | **Épica → Historia de usuario** | Cada RF activo da una historia con el mismo número (RF-010 → US-010). Los escenarios Gherkin salen de las rutas Gold, Feliz e Infeliz del RF |
| Requisito no funcional (documento 07) | **Enabler** o **criterio de aceptación / DoD** | Los RNF que exigen trabajo propio de infraestructura, seguridad o rendimiento pasan a enablers. Los que se cumplen dentro de una historia quedan en sus criterios de aceptación o en el DoD |
| Regla de negocio (documento 09) | Criterio de aceptación | Cada RN se verifica en los escenarios de la historia que la implementa (matriz del documento 09, sección 5) |

## 2. Épicas

| ID | Épica | Requisitos funcionales | Historias |
|---|---|---|---|
| EP-01 | Usuarios y acceso (transversal) | RF-001 a RF-009, RF-036 | 10 (con US-036) |
| EP-02 | Repositorio de sesiones (dimensión 1: planificación de sesiones de aprendizaje) | RF-010 a RF-016, RF-018 | 8 |
| EP-03 | Registro y control de notas (dimensión 2) | RF-020 a RF-029, RF-035 | 11 |
| EP-04 | Control de asistencia (dimensión 3) | RF-030 a RF-034 | 5 |
| EP-05 | Dirección (consolidados de las tres dimensiones) | RF-040 a RF-042 | 3 |
| | **Total** | | **37** |

RF-015 se retiró en la versión 1.2.0 del documento 06 y se repuso en la 1.7.0, con su historia US-015. RF-017 se retiró en la 1.7.0 y su historia US-017 queda como retirada. Dos excepciones a la regla «mismo número»: RF-036 (cambiar el tema) se implementó dentro de US-040 y no tiene historia propia, y US-036 (docentes de curso) todavía no tiene RF.

## 3. Transformación de los requisitos no funcionales

| RNF | Destino | Dónde |
|---|---|---|
| RNF-001, RNF-002, RNF-003 (rendimiento) | Enabler | EN-07 |
| RNF-004 (archivos de hasta 4 MB) | Enabler | EN-03 |
| RNF-005 (navegadores y celulares) | Enabler | EN-07 |
| RNF-006 (archivos que abren en Excel y LibreOffice) | Criterio de aceptación | US-024, US-025, US-034, US-041 |
| RNF-007 (aprendizaje en ≤ 30 min) | Criterio de aceptación | Demo del Sprint 1 y piloto |
| RNF-008 (accesibilidad AA) | DoD y enabler | DoD 7; EN-07 |
| RNF-009 (disponibilidad) | Enabler | EN-02 |
| RNF-010 (respaldo y restauración) | Enabler | EN-05 |
| RNF-011 (cortes de conexión) | Criterio de aceptación | US-020, US-030, US-032 |
| RNF-012 a RNF-015 (seguridad) | Enabler | EN-04 |
| RNF-016 (registro de actividad) | Criterio de aceptación | US-008 |
| RNF-017 (exactitud de totales) | Criterio de aceptación | US-033, US-040 |
| RNF-018 (cobertura y análisis estático) | DoD y enabler | DoD 1 y 2; EN-08 |
| RNF-019 (instalación en servidor nuevo) | Enabler | EN-05 |

## 4. Resumen de historias de usuario

| ID | Título | Épica | Origen | Prioridad |
|---|---|---|---|---|
| US-001 | Iniciar sesión | EP-01 | RF-001 | Alta |
| US-002 | Cerrar sesión | EP-01 | RF-002 | Alta |
| US-003 | Gestionar cuentas de usuario | EP-01 | RF-003 | Alta |
| US-004 | Restringir el acceso según el rol | EP-01 | RF-004 | Alta |
| US-005 | Asignar grado y sección a un docente | EP-01 | RF-005 | Alta |
| US-006 | Importar la lista de estudiantes de una sección | EP-01 | RF-006 | Alta |
| US-007 | Restablecer la contraseña de un usuario | EP-01 | RF-007 | Media |
| US-008 | Registrar la actividad de los usuarios | EP-01 | RF-008 | Media |
| US-009 | Cerrar el año escolar | EP-01 | RF-009 | Baja |
| US-036 | Trabajar como docente de curso | EP-01 | Sin RF todavía | Por definir (equipo) |
| US-010 | Enviar una sesión a la dirección | EP-02 | RF-010 | Alta |
| US-011 | Buscar y filtrar sesiones | EP-02 | RF-011 | Alta |
| US-012 | Descargar una sesión | EP-02 | RF-012 | Alta |
| US-013 | Subir una versión adaptada de una sesión | EP-02 | RF-013 | Media |
| US-014 | Aceptar los términos de publicación | EP-02 | RF-014 | Alta |
| US-015 | Dejar de compartir una sesión | EP-02 | RF-015 | Media |
| US-016 | Eliminar una sesión propia | EP-02 | RF-016 | Media |
| US-017 | *Retirada* (RF-017 retirado: el docente envía cada sesión a la dirección) | EP-02 | — | — |
| US-018 | Cargar sesiones del repositorio inicial | EP-02 | RF-018 | Media |
| US-020 | Registrar el nivel de logro | EP-03 | RF-020 | Alta |
| US-021 | Exigir la conclusión descriptiva en los niveles B y C | EP-03 | RF-021 | Alta |
| US-022 | Validar la escala y la completitud de las notas | EP-03 | RF-022 | Alta |
| US-023 | Consultar el registro de notas | EP-03 | RF-023 | Alta |
| US-024 | Completar la plantilla de notas del SIAGIE | EP-03 | RF-024 | Alta |
| US-025 | Reconocer la plantilla del SIAGIE y a sus estudiantes | EP-03 | RF-025 | Media (se hizo junto con US-024) |
| US-026 | Marcar las notas del periodo como entregadas | EP-03 | RF-026 | Media |
| US-027 | Mantener el catálogo de áreas y competencias | EP-03 | RF-027 | Alta |
| US-028 | Configurar los periodos del año escolar | EP-03 | RF-028 | Alta |
| US-029 | Marcar las competencias desarrolladas en el periodo | EP-03 | RF-029 | Alta |
| US-035 | Registrar la exoneración de un estudiante en un área | EP-03 | RF-035 | Media |
| US-030 | Registrar la asistencia de una jornada | EP-04 | RF-030 | Alta |
| US-031 | Corregir la asistencia de una jornada | EP-04 | RF-031 | Alta |
| US-032 | Impedir el registro duplicado de una jornada | EP-04 | RF-032 | Alta |
| US-033 | Consultar el historial de asistencia | EP-04 | RF-033 | Alta |
| US-034 | Exportar la asistencia a hoja de cálculo | EP-04 | RF-034 | Alta |
| US-040 | Consultar los consolidados | EP-05 | RF-040 | Alta |
| US-041 | Descargar los consolidados en el formato de la dirección | EP-05 | RF-041 | Media (el formato de la dirección es [DATO I.E. PENDIENTE]) |
| US-042 | Ver el estado de entrega por docente | EP-05 | RF-042 | Media |
Las historias de prioridad Alta forman el incremento funcional del piloto. La selección por sprint y la estimación en puntos de historia se hacen en el tablero de GitHub Projects; el detalle de cada historia terminada está en `openspec/changes/archive/`.

## 5. Historias de usuario

### EP-01: Usuarios y acceso

#### US-001: Iniciar sesión

| Campo | Detalle |
|---|---|
| **ID** | US-001 |
| **Título** | Iniciar sesión |
| **Épica relacionada** | EP-01 Usuarios y acceso |
| **Requisito de origen** | RF-001 |
| **Prioridad** | Alta |

**Redacción:** Como **usuario del sistema**, quiero **iniciar sesión con mi usuario y contraseña**, para **acceder solo a las funciones de mi rol**.

**Criterios de aceptación:**

```gherkin
  Escenario: Camino ideal
    Dado un docente con una cuenta activa
    Cuando ingresa su usuario y su contraseña correctos
    Entonces el sistema le da acceso y le muestra la pantalla de inicio de su rol

  Escenario: Flujo alternativo válido
    Dado un usuario de la dirección con una cuenta activa
    Cuando ingresa su usuario y su contraseña correctos
    Entonces el sistema le da acceso y le muestra el panel de consolidados

  Escenario: Caso de error
    Dado un usuario que ingresa una contraseña incorrecta o tiene la cuenta desactivada
    Cuando intenta iniciar sesión
    Entonces el sistema niega el acceso y muestra el mensaje "Usuario o contraseña incorrectos, o cuenta inactiva" con la indicación "Revisa tus datos. Si el problema sigue, pide ayuda al administrador.", sin indicar cuál de los datos falló

  Escenario: Cuenta bloqueada
    Dado una cuenta bloqueada tras 5 intentos fallidos consecutivos de inicio de sesión (RN-024)
    Cuando su usuario ingresa incluso la contraseña correcta antes de que pasen 15 minutos
    Entonces el sistema niega el acceso y muestra el mismo mensaje "Usuario o contraseña incorrectos, o cuenta inactiva" con la misma indicación "Revisa tus datos. Si el problema sigue, pide ayuda al administrador.", sin indicar que la cuenta está bloqueada
```

#### US-002: Cerrar sesión

| Campo | Detalle |
|---|---|
| **ID** | US-002 |
| **Título** | Cerrar sesión |
| **Épica relacionada** | EP-01 Usuarios y acceso |
| **Requisito de origen** | RF-002 |
| **Prioridad** | Alta |

**Redacción:** Como **usuario del sistema**, quiero **cerrar mi sesión, y que se cierre sola si dejo el sistema sin uso**, para **que nadie use mi cuenta en un celular o computadora compartidos**.

**Criterios de aceptación:**

```gherkin
  Escenario: Camino ideal
    Dado un docente con la sesión iniciada
    Cuando elige cerrar sesión
    Entonces el sistema termina la sesión y muestra la pantalla de inicio de sesión

  Escenario: Flujo alternativo válido
    Dado un usuario con la sesión iniciada que no realiza ninguna acción durante el tiempo máximo de inactividad definido en el documento 07
    Cuando se cumple ese tiempo
    Entonces el sistema termina la sesión automáticamente

  Escenario: Caso de error
    Dado un usuario que ya cerró sesión
    Cuando intenta volver a una pantalla interna con el botón "atrás" del navegador
    Entonces el sistema no muestra la información y lo redirige a la pantalla de inicio de sesión
```

#### US-003: Gestionar cuentas de usuario

| Campo | Detalle |
|---|---|
| **ID** | US-003 |
| **Título** | Gestionar cuentas de usuario |
| **Épica relacionada** | EP-01 Usuarios y acceso |
| **Requisito de origen** | RF-003 |
| **Prioridad** | Alta |

**Redacción:** Como **administrador**, quiero **crear, editar y desactivar cuentas de docentes y de la dirección**, para **que solo el personal autorizado use el sistema**.

**Criterios de aceptación:**

```gherkin
  Escenario: Camino ideal
    Dado el administrador con la sesión iniciada
    Cuando registra una cuenta nueva con nombres, apellidos, usuario y rol "Docente"
    Entonces el sistema crea la cuenta activa y muestra el mensaje "Cuenta creada"

  Escenario: Flujo alternativo válido
    Dado un docente que ya no trabaja en la institución
    Cuando el administrador desactiva su cuenta
    Entonces el sistema impide nuevos accesos con esa cuenta y conserva los registros que el docente hizo

  Escenario: Caso de error
    Dado un usuario que ya existe en el sistema
    Cuando el administrador intenta crear otra cuenta con el mismo usuario
    Entonces el sistema no crea la cuenta y muestra el mensaje "El usuario ya existe"
```

#### US-004: Restringir el acceso según el rol

| Campo | Detalle |
|---|---|
| **ID** | US-004 |
| **Título** | Restringir el acceso según el rol |
| **Épica relacionada** | EP-01 Usuarios y acceso |
| **Requisito de origen** | RF-004 |
| **Prioridad** | Alta |

**Redacción:** Como **docente**, quiero **ver únicamente la información de mis secciones**, para **que los datos de otros estudiantes estén protegidos**.

**Criterios de aceptación:**

```gherkin
  Escenario: Camino ideal
    Dado un docente asignado a "3.° grado, sección A"
    Cuando consulta las notas
    Entonces el sistema muestra solo las notas de los estudiantes de esa sección

  Escenario: Flujo alternativo válido
    Dado un usuario de la dirección o el administrador
    Cuando abre una pantalla de sección de la docente
    Entonces el sistema lo lleva a su propia pantalla de inicio, sin datos de la sección (la dirección consulta las notas en los consolidados, US-040)

  Escenario: Caso de error
    Dado un docente asignado a "3.° grado, sección A"
    Cuando intenta abrir las notas de "4.° grado, sección B"
    Entonces el sistema niega el acceso (403), muestra el mensaje "No tienes permiso para ver esta sección" y registra el intento (RF-008)
```

#### US-005: Asignar grado y sección a un docente

| Campo | Detalle |
|---|---|
| **ID** | US-005 |
| **Título** | Asignar grado y sección a un docente |
| **Épica relacionada** | EP-01 Usuarios y acceso |
| **Requisito de origen** | RF-005 |
| **Prioridad** | Alta |

**Redacción:** Como **administrador**, quiero **asignar grado y sección a cada docente**, para **que cada docente vea al iniciar sesión la sección que le corresponde**.

**Criterios de aceptación:**

```gherkin
  Escenario: Camino ideal
    Dado un docente con una cuenta activa y sin sección asignada
    Cuando el administrador le asigna "2.° grado, sección única"
    Entonces el sistema registra la asignación y el docente ve esa sección al iniciar sesión

  Escenario: Flujo alternativo válido
    Dado un docente con una sección asignada que cambia de sección
    Cuando el administrador registra la nueva asignación
    Entonces el sistema cambia la sección del docente y conserva los registros anteriores asociados a la sección original

  Escenario: Caso de error
    Dado una sección que ya tiene un docente asignado
    Cuando el administrador intenta asignarla a otro docente
    Entonces el sistema no registra la asignación y muestra el mensaje "La sección ya tiene un docente asignado"
```

#### US-006: Importar la lista de estudiantes de una sección

| Campo | Detalle |
|---|---|
| **ID** | US-006 |
| **Título** | Importar la lista de estudiantes de una sección |
| **Épica relacionada** | EP-01 Usuarios y acceso |
| **Requisito de origen** | RF-006 |
| **Prioridad** | Alta |

**Redacción:** Como **docente**, quiero **pegar una sola vez la lista de estudiantes de mi sección, copiada de una hoja de cálculo**, para **no volver a escribir sus nombres en cada registro**.

**Criterios de aceptación:**

```gherkin
  Escenario: Camino ideal
    Dado un docente con una sección asignada y sin estudiantes registrados
    Cuando pega las filas copiadas de una hoja de cálculo, 25 líneas "APELLIDOS, NOMBRES", y toca "Importar"
    Entonces el sistema registra los 25 estudiantes en la sección y muestra el mensaje "25 estudiantes importados"

  Escenario: Flujo alternativo válido
    Dado un docente con la lista ya importada
    Cuando agrega manualmente a un estudiante que se incorporó después
    Entonces el sistema registra al estudiante en la sección

  Escenario: Caso de error
    Dado un texto pegado con una línea sin apellidos y dos líneas con el mismo estudiante
    Cuando el docente toca "Importar"
    Entonces el sistema no importa ninguna línea, muestra "No se guardó ningún estudiante" con cada línea con error y su motivo, y conserva el texto pegado
```

#### US-007: Restablecer la contraseña de un usuario

| Campo | Detalle |
|---|---|
| **ID** | US-007 |
| **Título** | Restablecer la contraseña de un usuario |
| **Épica relacionada** | EP-01 Usuarios y acceso |
| **Requisito de origen** | RF-007 |
| **Prioridad** | Media |

**Redacción:** Como **administrador**, quiero **restablecer la contraseña de un usuario que la olvidó**, para **que pueda volver a usar el sistema sin perder sus registros**.

**Criterios de aceptación:**

```gherkin
  Escenario: Camino ideal
    Dado un docente que olvidó su contraseña y lo comunica al administrador
    Cuando el administrador restablece la contraseña de esa cuenta
    Entonces el sistema genera una contraseña temporal y se la muestra al administrador una sola vez

  Escenario: Flujo alternativo válido
    Dado un docente que inicia sesión con una contraseña temporal
    Cuando ingresa al sistema
    Entonces el sistema le exige definir una contraseña nueva antes de continuar

  Escenario: Caso de error
    Dado un docente que define una contraseña nueva
    Cuando esta no cumple la política definida en el documento 07
    Entonces el sistema no la guarda y muestra los requisitos que no se cumplieron
```

#### US-008: Registrar la actividad de los usuarios

| Campo | Detalle |
|---|---|
| **ID** | US-008 |
| **Título** | Registrar la actividad de los usuarios |
| **Épica relacionada** | EP-01 Usuarios y acceso |
| **Requisito de origen** | RF-008 |
| **Prioridad** | Media |

**Redacción:** Como **administrador**, quiero **que el sistema registre quién hizo cada operación y cuándo**, para **atender incidencias y calcular los indicadores de adopción**.

**Criterios de aceptación:**

```gherkin
  Escenario: Camino ideal
    Dado un docente con la sesión iniciada
    Cuando registra la asistencia de una jornada
    Entonces el sistema guarda una entrada de actividad con su usuario, la fecha, la hora y la operación "registro de asistencia"

  Escenario: Flujo alternativo válido
    Dado el administrador
    Cuando consulta la actividad de un periodo
    Entonces el sistema muestra el número de docentes activos por semana (con al menos un uso en la semana, KPI-01), de sesiones cargadas, de jornadas registradas y de secciones con notas registradas (KPI, documento 07, sección 5)

  Escenario: Caso de error
    Dado un docente o un usuario de la dirección
    Cuando intenta modificar o borrar una entrada del registro de actividad
    Entonces el sistema no lo permite, porque el registro de actividad es de solo lectura para todos los roles
```

#### US-009: Cerrar el año escolar

| Campo | Detalle |
|---|---|
| **ID** | US-009 |
| **Título** | Cerrar el año escolar |
| **Épica relacionada** | EP-01 Usuarios y acceso |
| **Requisito de origen** | RF-009 |
| **Prioridad** | Baja |

**Redacción:** Como **administrador**, quiero **cerrar el año escolar después de que la dirección descargue los consolidados**, para **no conservar datos de estudiantes más tiempo del necesario**.

**Criterios de aceptación:**

```gherkin
  Escenario: Camino ideal
    Dado un año escolar terminado cuyos consolidados la dirección ya descargó y confirmó
    Cuando el administrador ejecuta el cierre del año y lo confirma
    Entonces el sistema elimina las listas de estudiantes, las notas y la asistencia de ese año, conserva las sesiones del repositorio y registra la operación en el registro de actividad (RF-008)

  Escenario: Flujo alternativo válido
    Dado un año escolar terminado
    Cuando la dirección pide conservar los datos hasta una fecha posterior
    Entonces el administrador registra esa fecha y el sistema no permite ejecutar el cierre antes de ella

  Escenario: Caso de error
    Dado un año escolar cuyos consolidados la dirección aún no confirmó haber descargado
    Cuando el administrador intenta ejecutar el cierre
    Entonces el sistema no elimina ningún dato y muestra el mensaje "La dirección debe descargar y confirmar los consolidados antes del cierre"
```


#### US-036: Trabajar como docente de curso

| Campo | Detalle |
|---|---|
| **ID** | US-036 |
| **Título** | Trabajar como docente de curso |
| **Épica relacionada** | EP-01 Usuarios y acceso |
| **Requisito de origen** | Sin RF todavía: se redacta en el documento 06 cuando el equipo la priorice |
| **Prioridad** | Por definir (equipo) |

**Redacción:** Como **docente de curso** (por ejemplo, Educación Física o Inglés), quiero **que el administrador me asigne mi área en varias secciones**, para **registrar las notas de mi área y enviar mis sesiones sin depender de la tutora**.

Datos de la I.E. que faltan: cuántos docentes de curso hay, qué áreas dictan, si llevan asistencia y dónde van las notas de Computación, que no es un área del SIAGIE [DATO I.E. PENDIENTE].

**Criterios de aceptación:**

```gherkin
  Escenario: Camino ideal
    Dado un docente de curso al que el administrador asignó Inglés en "2.º A" y "2.º B"
    Cuando inicia sesión
    Entonces el sistema le muestra esas secciones con su área, sin la tarjeta de asistencia, y la lista de estudiantes en solo lectura

  Escenario: Flujo alternativo válido
    Dado un área marcada "a cargo del docente de curso" en la institución
    Cuando el docente de curso abre las competencias de una de sus secciones
    Entonces puede marcar las competencias de su área, y la tutora de la sección ya no puede marcarlas

  Escenario: Caso de error
    Dado un docente de curso
    Cuando intenta abrir las notas de un área que no tiene asignada
    Entonces el sistema niega el acceso (403) y registra el intento (RF-008)
```

### EP-02: Repositorio de sesiones (D1)

#### US-010: Enviar una sesión a la dirección

| Campo | Detalle |
|---|---|
| **ID** | US-010 |
| **Título** | Enviar una sesión a la dirección |
| **Épica relacionada** | EP-02 Repositorio de sesiones (D1) |
| **Requisito de origen** | RF-010 |
| **Prioridad** | Alta |

**Redacción:** Como **docente**, quiero **enviar mis sesiones a la dirección indicando grado, área y título, y si quiero compartirlas en el repositorio**, para **entregarlas sin papel y que otros docentes puedan reutilizarlas**.

**Criterios de aceptación:**

```gherkin
  Escenario: Camino ideal
    Dado un docente con la sesión iniciada
    Cuando adjunta el archivo de una sesión, ingresa "3.º grado", "Matemática" y el título "Resolvemos problemas de suma" y toca "Enviar a la dirección" sin marcar la casilla de compartir
    Entonces el sistema guarda la sesión, que solo ven el docente y la dirección, y muestra el mensaje "Sesión enviada a la dirección"

  Escenario: Flujo alternativo válido
    Dado un docente que envía una sesión
    Cuando marca "Compartir también en el repositorio" y acepta los términos de publicación (RF-014)
    Entonces el sistema guarda la sesión compartida y muestra "Sesión enviada a la dirección y compartida en el repositorio"

  Escenario: Caso de error
    Dado un docente que adjunta un archivo que no es PDF ni Word (.docx) o que pesa más de 4 MB, o que deja vacío el grado, el área o el título
    Cuando intenta enviar la sesión
    Entonces el sistema no la guarda y muestra el motivo en cada campo, por ejemplo "Falta indicar el área."
```

#### US-011: Buscar y filtrar sesiones

| Campo | Detalle |
|---|---|
| **ID** | US-011 |
| **Título** | Buscar y filtrar sesiones |
| **Épica relacionada** | EP-02 Repositorio de sesiones (D1) |
| **Requisito de origen** | RF-011 |
| **Prioridad** | Alta |

**Redacción:** Como **docente**, quiero **buscar sesiones por grado, área o palabra clave**, para **encontrar rápido una sesión que pueda adaptar**.

**Criterios de aceptación:**

```gherkin
  Escenario: Camino ideal
    Dado un repositorio con sesiones de varios grados y áreas
    Cuando el docente filtra por "3.° grado" y "Comunicación"
    Entonces el sistema lista solo las sesiones del repositorio que cumplen ambos filtros

  Escenario: Flujo alternativo válido
    Dado un docente que busca la palabra "fracciones"
    Cuando no aplica ningún otro filtro
    Entonces el sistema lista las sesiones del repositorio cuyo título o datos contienen esa palabra

  Escenario: Caso de error
    Dado una búsqueda sin coincidencias
    Cuando el docente aplica los filtros
    Entonces el sistema muestra el mensaje "No se encontraron sesiones con esos filtros"
```

#### US-012: Descargar una sesión

| Campo | Detalle |
|---|---|
| **ID** | US-012 |
| **Título** | Descargar una sesión |
| **Épica relacionada** | EP-02 Repositorio de sesiones (D1) |
| **Requisito de origen** | RF-012 |
| **Prioridad** | Alta |

**Redacción:** Como **docente**, quiero **descargar el archivo de una sesión**, para **adaptarla en mi procesador de textos o subirla al canal que indique la UGEL**.

**Criterios de aceptación:**

```gherkin
  Escenario: Camino ideal
    Dado una sesión publicada por otro docente
    Cuando el docente elige descargarla
    Entonces el sistema entrega el archivo original para que lo adapte en su procesador de textos

  Escenario: Flujo alternativo válido
    Dado una sesión propia
    Cuando su autor elige descargarla
    Entonces el sistema entrega el archivo, por ejemplo para subirlo al canal que indique la UGEL

  Escenario: Caso de error
    Dado una sesión que su autor eliminó del repositorio
    Cuando un docente intenta descargarla mediante un enlace guardado
    Entonces el sistema no entrega el archivo y muestra el mensaje "La sesión ya no está disponible"
```

#### US-013: Subir una versión adaptada de una sesión

| Campo | Detalle |
|---|---|
| **ID** | US-013 |
| **Título** | Subir una versión adaptada de una sesión |
| **Épica relacionada** | EP-02 Repositorio de sesiones (D1) |
| **Requisito de origen** | RF-013 |
| **Prioridad** | Media |

**Redacción:** Como **docente**, quiero **subir la versión que adapté de una sesión del repositorio**, para **que mi adaptación quede registrada como sesión propia vinculada a la original**.

**Criterios de aceptación:**

```gherkin
  Escenario: Camino ideal
    Dado un docente que descargó y adaptó una sesión del repositorio
    Cuando sube el archivo adaptado desde la sesión original y acepta los términos de publicación
    Entonces el sistema publica una sesión propia que indica "Adaptada de: [título de la sesión de origen]"

  Escenario: Flujo alternativo válido
    Dado un docente que adaptó una sesión propia
    Cuando sube la nueva versión desde esa misma sesión
    Entonces el sistema reemplaza el archivo y conserva la fecha de la última modificación

  Escenario: Caso de error
    Dado una sesión de origen que su autor eliminó
    Cuando un docente intenta subir una versión adaptada desde ella
    Entonces el sistema no permite la operación y muestra el mensaje "La sesión de origen ya no está disponible"
```

#### US-014: Aceptar los términos de publicación

| Campo | Detalle |
|---|---|
| **ID** | US-014 |
| **Título** | Aceptar los términos de publicación |
| **Épica relacionada** | EP-02 Repositorio de sesiones (D1) |
| **Requisito de origen** | RF-014 |
| **Prioridad** | Alta |

**Redacción:** Como **docente**, quiero **aceptar los términos de publicación cuando comparto una sesión en el repositorio**, para **saber con claridad qué autorizo al compartirla**.

**Criterios de aceptación:**

```gherkin
  Escenario: Camino ideal
    Dado un docente que completó los datos de una sesión y marcó "Compartir también en el repositorio" (RF-010 o RF-013)
    Cuando toca "Enviar a la dirección" y luego "Acepto y envío" en los términos
    Entonces el sistema envía la sesión, la comparte, guarda la fecha y la hora de la aceptación y la muestra en las búsquedas del repositorio

  Escenario: Flujo alternativo válido
    Dado un docente con una sesión enviada que no compartió
    Cuando toca "Compartir" en la página de la sesión y luego "Acepto y comparto"
    Entonces el sistema la comparte con la fecha y la hora de esa aceptación y muestra "Sesión compartida en el repositorio"

  Escenario: Caso de error
    Dado un docente que completó los datos de una sesión
    Cuando pide compartirla sin aceptar los términos de publicación
    Entonces el sistema no guarda la sesión ni el archivo y responde "Para compartirla en el repositorio debes aceptar los términos."; si toca "Volver", los términos se cierran y el formulario conserva sus datos
```

#### US-015: Dejar de compartir una sesión

| Campo | Detalle |
|---|---|
| **ID** | US-015 |
| **Título** | Dejar de compartir una sesión |
| **Épica relacionada** | EP-02 Repositorio de sesiones (D1) |
| **Requisito de origen** | RF-015 (repuesto en el documento 06, V_1_7_0) |
| **Prioridad** | Media (se implementó junto con US-011, US-012 y US-016) |

**Redacción:** Como **docente**, quiero **dejar de compartir una sesión sin quitársela a la dirección**, para **decidir qué sesiones ven mis colegas**.

**Criterios de aceptación:**

```gherkin
  Escenario: Camino ideal
    Dado una sesión propia compartida en el repositorio
    Cuando el docente toca "Dejar de compartir"
    Entonces el sistema la saca del repositorio, la sesión sigue enviada a la dirección y la página muestra "Dejaste de compartir la sesión"

  Escenario: Flujo alternativo válido
    Dado una sesión que su autor dejó de compartir
    Cuando vuelve a tocar "Compartir" y acepta los términos (RF-014)
    Entonces el sistema la vuelve a mostrar en el repositorio

  Escenario: Caso de error
    Dado una sesión compartida de otro docente
    Cuando un docente intenta dejar de compartirla
    Entonces el sistema no lo permite y registra el intento sin permiso (RF-008)
```

#### US-016: Eliminar una sesión propia

| Campo | Detalle |
|---|---|
| **ID** | US-016 |
| **Título** | Eliminar una sesión propia |
| **Épica relacionada** | EP-02 Repositorio de sesiones (D1) |
| **Requisito de origen** | RF-016 |
| **Prioridad** | Media |

**Redacción:** Como **docente**, quiero **eliminar una sesión que envié**, para **quitarla del sistema, también para la dirección y el repositorio**.

**Criterios de aceptación:**

```gherkin
  Escenario: Camino ideal
    Dado una sesión propia
    Cuando el docente elige eliminarla y confirma la acción
    Entonces el sistema la elimina con su archivo para todos, también para la dirección, y muestra el mensaje "Sesión eliminada"

  Escenario: Flujo alternativo válido
    Dado un docente que elige eliminar una sesión
    Cuando cancela la confirmación
    Entonces el sistema conserva la sesión sin cambios

  Escenario: Caso de error
    Dado una sesión de otro docente
    Cuando un docente intenta eliminarla
    Entonces el sistema no lo permite y muestra el mensaje "Solo el autor puede eliminar esta sesión"
```

#### US-017: Retirada

Esta historia ("Subir sesiones entregadas por docentes") se retiró junto con RF-017 (documento 06, V_1_7_0): el docente envía cada sesión directamente a la dirección (US-010), así que la dirección ya no las sube por él. El identificador no se reutiliza.

#### US-018: Cargar sesiones del repositorio inicial

| Campo | Detalle |
|---|---|
| **ID** | US-018 |
| **Título** | Cargar sesiones del repositorio inicial |
| **Épica relacionada** | EP-02 Repositorio de sesiones (D1) |
| **Requisito de origen** | RF-018 |
| **Prioridad** | Media |

**Redacción:** Como **administrador**, quiero **cargar sesiones de referencia con su fuente y permiso de uso**, para **que el repositorio tenga contenido desde el inicio**.

**Criterios de aceptación:**

```gherkin
  Escenario: Camino ideal
    Dado una sesión cuyo uso está permitido
    Cuando el administrador la sube con el grado inicial y el final (puede abarcar varios grados), el área, el título, la fuente y el permiso de uso, escrito como texto libre
    Entonces el sistema la guarda como "Material de referencia", visible para todos los docentes de la institución

  Escenario: Flujo alternativo válido
    Dado una sesión elaborada por el propio equipo del proyecto
    Cuando el administrador la sube e indica como fuente "Equipo del proyecto"
    Entonces el sistema la guarda como material de referencia

  Escenario: Caso de error
    Dado una sesión de terceros
    Cuando el administrador intenta subirla sin indicar la fuente o el permiso de uso
    Entonces el sistema no la guarda y muestra el mensaje "Indique la fuente y el permiso de uso"
```


### EP-03: Registro y control de notas (D2)

#### US-020: Registrar el nivel de logro

| Campo | Detalle |
|---|---|
| **ID** | US-020 |
| **Título** | Registrar el nivel de logro |
| **Épica relacionada** | EP-03 Registro y control de notas (D2) |
| **Requisito de origen** | RF-020 |
| **Prioridad** | Alta |

**Redacción:** Como **docente**, quiero **registrar el nivel de logro de cada estudiante por competencia y periodo**, para **tener el registro auxiliar sin transcribir en hojas de cálculo**.

**Criterios de aceptación:**

```gherkin
  Escenario: Camino ideal
    Dado un docente con su lista de estudiantes importada y un periodo abierto
    Cuando registra el nivel "A" para la estudiante ficticia "Ana Quispe" en una competencia de Matemática
    Entonces el sistema guarda la nota y la muestra en el registro de la sección

  Escenario: Flujo alternativo válido
    Dado una nota ya registrada en un periodo que aún no se marcó como entregado
    Cuando el docente la cambia de "B" a "A"
    Entonces el sistema actualiza la nota y guarda la modificación en el registro de actividad (RF-008)

  Escenario: Caso de error
    Dado un docente que registra notas
    Cuando se interrumpe la conexión antes de confirmar el guardado
    Entonces el sistema no guarda registros parciales y muestra "No se pudo guardar" con "Revisa tu conexión y reintenta. Tus datos siguen en pantalla y el borrador queda en este dispositivo. No se guardó nada."; el botón "Guardar" cambia a "Reintentar"
```

#### US-021: Exigir la conclusión descriptiva en los niveles B y C

| Campo | Detalle |
|---|---|
| **ID** | US-021 |
| **Título** | Exigir la conclusión descriptiva en los niveles B y C |
| **Épica relacionada** | EP-03 Registro y control de notas (D2) |
| **Requisito de origen** | RF-021 |
| **Prioridad** | Alta |

**Redacción:** Como **docente**, quiero **que el sistema me pida la conclusión descriptiva cuando registro el nivel B o C**, para **cumplir la norma de evaluación y la práctica de la I.E. sin olvidarla** (RN-003).

**Criterios de aceptación:**

```gherkin
  Escenario: Camino ideal
    Dado un docente que registra el nivel "C" para un estudiante
    Cuando escribe la conclusión descriptiva y guarda
    Entonces el sistema guarda el nivel y la conclusión

  Escenario: Flujo alternativo válido
    Dado un docente que cambia un nivel de "B" a "A" o "AD"
    Cuando guarda la hoja del área
    Entonces el sistema guarda el nivel y borra la conclusión, que en A y AD no se registra

  Escenario: Caso de error
    Dado un docente que registra el nivel "C"
    Cuando intenta guardar sin conclusión descriptiva
    Entonces el sistema no guarda ninguna nota de la hoja, marca la celda con "Falta conclusión" y muestra "No se guardó nada"
```

#### US-022: Validar la escala y la completitud de las notas

| Campo | Detalle |
|---|---|
| **ID** | US-022 |
| **Título** | Validar la escala y la completitud de las notas |
| **Épica relacionada** | EP-03 Registro y control de notas (D2) |
| **Requisito de origen** | RF-022 |
| **Prioridad** | Alta |

**Redacción:** Como **docente**, quiero **que el sistema rechace valores fuera de la escala y me avise de los registros pendientes**, para **entregar notas completas y sin errores**.

**Criterios de aceptación:**

```gherkin
  Escenario: Camino ideal
    Dado un docente que registra una nota
    Cuando elige un nivel de la escala vigente definida en el documento 09
    Entonces el sistema la acepta

  Escenario: Flujo alternativo válido
    Dado una competencia marcada como desarrollada en el periodo, con 3 estudiantes sin nivel registrado
    Cuando el docente revisa las notas del periodo
    Entonces el sistema lista esos 3 casos como "Pendientes de registro" y no lista las competencias que no se trabajaron en el periodo

  Escenario: Caso de error
    Dado un docente que ingresa un valor que no pertenece a la escala, por ejemplo "15" o "A+"
    Cuando intenta guardarlo
    Entonces el sistema no lo guarda y muestra el mensaje "Valor no válido. Use un nivel de la escala de calificación"
```

#### US-023: Consultar el registro de notas

| Campo | Detalle |
|---|---|
| **ID** | US-023 |
| **Título** | Consultar el registro de notas |
| **Épica relacionada** | EP-03 Registro y control de notas (D2) |
| **Requisito de origen** | RF-023 |
| **Prioridad** | Alta |

**Redacción:** Como **docente**, quiero **consultar las notas por sección, estudiante, competencia o periodo**, para **revisar el progreso de mis estudiantes**.

**Criterios de aceptación:**

```gherkin
  Escenario: Camino ideal
    Dado un docente con notas registradas
    Cuando consulta el registro de su sección en el periodo actual
    Entonces el sistema muestra a cada estudiante con su nivel de logro por competencia

  Escenario: Flujo alternativo válido
    Dado un docente
    Cuando consulta a un solo estudiante
    Entonces el sistema muestra los niveles de logro de ese estudiante en todas las competencias y periodos registrados

  Escenario: Caso de error
    Dado un periodo sin notas registradas
    Cuando el docente lo consulta
    Entonces el sistema muestra el mensaje "No hay notas registradas en este periodo"
```

#### US-024: Completar la plantilla de notas del SIAGIE

| Campo | Detalle |
|---|---|
| **ID** | US-024 |
| **Título** | Completar la plantilla de notas del SIAGIE |
| **Épica relacionada** | EP-03 Registro y control de notas (D2) |
| **Requisito de origen** | RF-024 |
| **Prioridad** | Alta |

**Redacción:** Como **dirección**, quiero **subir la plantilla de notas que descargo del SIAGIE y recibirla llena con las notas registradas**, para **cargarla en el SIAGIE sin volver a digitar las notas**.

**Criterios de aceptación:**

```gherkin
  Escenario: Camino ideal
    Dado un usuario de la dirección y una sección con las notas del periodo registradas
    Cuando sube la plantilla de notas del SIAGIE de esa sección y ese periodo
    Entonces el sistema devuelve el mismo archivo con el nivel de logro y la conclusión de cada estudiante en cada competencia, y un resumen con los encontrados, los no encontrados, las notas faltantes y las celdas reemplazadas

  Escenario: Flujo alternativo válido
    Dado una sección con estudiantes sin nivel en alguna competencia del periodo
    Cuando la dirección sube la plantilla
    Entonces el sistema completa lo registrado, deja esas celdas como venían y titula el resumen "Plantilla completada con observaciones"

  Escenario: Caso de error
    Dado un docente o el administrador
    Cuando intenta subir una plantilla del SIAGIE
    Entonces el sistema lo lleva a su pantalla de inicio y no procesa nada
```

#### US-025: Reconocer la plantilla del SIAGIE y a sus estudiantes

| Campo | Detalle |
|---|---|
| **ID** | US-025 |
| **Título** | Reconocer la plantilla del SIAGIE y a sus estudiantes |
| **Épica relacionada** | EP-03 Registro y control de notas (D2) |
| **Requisito de origen** | RF-025 |
| **Prioridad** | Media (se hizo junto con US-024) |

**Redacción:** Como **dirección**, quiero **que el sistema reconozca la sección y a los estudiantes de la plantilla del SIAGIE**, para **no tener que emparejarlos a mano**.

**Criterios de aceptación:**

```gherkin
  Escenario: Camino ideal
    Dado una plantilla con el código modular y el anexo de la institución, y una sola sección de ese grado en la I.E.
    Cuando la dirección la sube
    Entonces el sistema la completa con esa sección sin preguntar

  Escenario: Flujo alternativo válido
    Dado una plantilla cuya sección del SIAGIE no se reconoce sola y un grado con varias secciones en la I.E.
    Cuando la dirección elige la sección en el diálogo
    Entonces el sistema guarda esa equivalencia para el año, completa la plantilla en el mismo paso y la próxima vez no vuelve a preguntar

  Escenario: Caso de error
    Dado un archivo que no es la plantilla del SIAGIE, o de otra institución, año o periodo
    Cuando la dirección lo sube
    Entonces el sistema no lo procesa y muestra "El archivo no corresponde a la plantilla de notas del SIAGIE"
```

#### US-026: Marcar las notas del periodo como entregadas

| Campo | Detalle |
|---|---|
| **ID** | US-026 |
| **Título** | Marcar las notas del periodo como entregadas |
| **Épica relacionada** | EP-03 Registro y control de notas (D2) |
| **Requisito de origen** | RF-026 |
| **Prioridad** | Media |

**Redacción:** Como **docente**, quiero **marcar como entregadas las notas de un periodo**, para **que la dirección sepa que ya están listas**.

**Criterios de aceptación:**

```gherkin
  Escenario: Camino ideal
    Dado un docente con todas las notas del periodo registradas
    Cuando confirma la entrega
    Entonces el sistema registra la fecha de entrega, bloquea la edición de esas notas y la dirección ve el estado "Entregado"

  Escenario: Flujo alternativo válido
    Dado notas ya entregadas que necesitan una corrección
    Cuando la dirección habilita de nuevo su edición
    Entonces el sistema permite al docente corregirlas y registra quién habilitó el cambio

  Escenario: Caso de error
    Dado un periodo con estudiantes sin nivel registrado en alguna competencia marcada como desarrollada (o, en el último periodo del año, en cualquier competencia)
    Cuando el docente intenta confirmar la entrega
    Entonces el sistema no registra la entrega y muestra cuántos registros están pendientes
```

#### US-027: Mantener el catálogo de áreas y competencias

| Campo | Detalle |
|---|---|
| **ID** | US-027 |
| **Título** | Mantener el catálogo de áreas y competencias |
| **Épica relacionada** | EP-03 Registro y control de notas (D2) |
| **Requisito de origen** | RF-027 |
| **Prioridad** | Alta |

**Redacción:** Como **administrador**, quiero **mantener el catálogo de áreas y competencias de primaria**, para **que el registro de notas use las competencias oficiales**.

**Criterios de aceptación:**

```gherkin
  Escenario: Camino ideal
    Dado el administrador
    Cuando registra un área con sus competencias
    Entonces el sistema las guarda y quedan disponibles para el registro de notas de todas las secciones

  Escenario: Flujo alternativo válido
    Dado una competencia que deja de usarse
    Cuando el administrador la desactiva
    Entonces el sistema deja de mostrarla para nuevos registros y conserva las notas que ya se registraron con ella

  Escenario: Caso de error
    Dado una competencia con notas ya registradas
    Cuando el administrador intenta eliminarla
    Entonces el sistema no la elimina y muestra el mensaje "La competencia tiene notas registradas; solo puede desactivarse"
```

#### US-028: Configurar los periodos del año escolar

| Campo | Detalle |
|---|---|
| **ID** | US-028 |
| **Título** | Configurar los periodos del año escolar |
| **Épica relacionada** | EP-03 Registro y control de notas (D2) |
| **Requisito de origen** | RF-028 |
| **Prioridad** | Alta |

**Redacción:** Como **administrador**, quiero **configurar los periodos del año escolar**, para **que el registro de notas use el periodo vigente**.

**Criterios de aceptación:**

```gherkin
  Escenario: Camino ideal
    Dado el administrador
    Cuando configura el año escolar en bimestres (RN-006), con sus fechas
    Entonces el sistema crea los periodos y el registro de notas usa el periodo vigente según la fecha

  Escenario: Flujo alternativo válido
    Dado un periodo configurado cuyas fechas cambian por disposición de la institución
    Cuando el administrador las modifica
    Entonces el sistema actualiza las fechas sin alterar las notas ya registradas

  Escenario: Caso de error
    Dado el administrador que configura un periodo
    Cuando sus fechas se cruzan con las de otro periodo
    Entonces el sistema no lo guarda y muestra el mensaje "Las fechas se cruzan con otro periodo"
```

#### US-029: Marcar las competencias desarrolladas en el periodo

| Campo | Detalle |
|---|---|
| **ID** | US-029 |
| **Título** | Marcar las competencias desarrolladas en el periodo |
| **Épica relacionada** | EP-03 Registro y control de notas (D2) |
| **Requisito de origen** | RF-029 |
| **Prioridad** | Alta |

**Redacción:** Como **docente**, quiero **marcar qué competencias trabajé en el periodo**, para **que solo se me exijan notas de esas competencias**.

**Criterios de aceptación:**

```gherkin
  Escenario: Camino ideal
    Dado un docente con un periodo abierto
    Cuando marca las competencias de Matemática y de Comunicación que trabajó en el periodo
    Entonces el sistema habilita el registro de notas solo para esas competencias en ese periodo; las áreas a cargo del docente de curso no se pueden marcar

  Escenario: Flujo alternativo válido
    Dado un docente en el último periodo del año escolar
    Cuando abre las competencias de ese periodo
    Entonces el sistema marca como desarrolladas todas las competencias que aún no tienen nivel en ningún periodo, para que todas terminen el año con un nivel de logro

  Escenario: Caso de error
    Dado una competencia que ya tiene notas registradas en el periodo
    Cuando el docente intenta desmarcarla
    Entonces el sistema no la desmarca y muestra el mensaje "La competencia tiene notas registradas en este periodo"
```

#### US-035: Registrar la exoneración de un estudiante en un área

| Campo | Detalle |
|---|---|
| **ID** | US-035 |
| **Título** | Registrar la exoneración de un estudiante en un área |
| **Épica relacionada** | EP-03 Registro y control de notas (D2) |
| **Requisito de origen** | RF-035 |
| **Prioridad** | Media |

**Redacción:** Como **docente**, quiero **registrar la exoneración de un estudiante en Educación Religiosa o Educación Física**, para **que no figure como pendiente en esas competencias**.

**Criterios de aceptación:**

```gherkin
  Escenario: Camino ideal
    Dado un estudiante ficticio, "Luis Huamán", cuya exoneración de Educación Religiosa autorizó la dirección
    Cuando el docente registra la exoneración en esa área
    Entonces el sistema muestra al estudiante como "Exonerado" en esas competencias y no lo cuenta como pendiente (RF-022, RF-026)

  Escenario: Flujo alternativo válido
    Dado una exoneración temporal de Educación Física
    Cuando el docente registra su fecha de término
    Entonces el sistema vuelve a exigir el nivel de logro de esas competencias desde el periodo que empieza después de esa fecha

  Escenario: Caso de error
    Dado un docente que intenta registrar una exoneración en un área distinta, por ejemplo Matemática
    Cuando confirma el registro
    Entonces el sistema no lo guarda y muestra el mensaje "Solo se puede registrar la exoneración de Educación Religiosa o de Educación Física"
```


### EP-04: Control de asistencia (D3)

#### US-030: Registrar la asistencia de una jornada

| Campo | Detalle |
|---|---|
| **ID** | US-030 |
| **Título** | Registrar la asistencia de una jornada |
| **Épica relacionada** | EP-04 Control de asistencia (D3) |
| **Requisito de origen** | RF-030 |
| **Prioridad** | Alta |

**Redacción:** Como **docente**, quiero **registrar la asistencia de mi sección desde el celular**, para **hacerlo en el aula sin hojas de papel**.

**Criterios de aceptación:**

```gherkin
  Escenario: Camino ideal
    Dado un docente con su lista de estudiantes importada
    Cuando abre la asistencia de la jornada de hoy y toca el círculo de cada estudiante hasta llegar a su estado
    Entonces el sistema guarda cada toque en ese momento, sin botón Guardar, y con todos los estudiantes marcados muestra el resumen "Asistió: 21 · Tarde: 1 · Faltó: 2 · Justificado: 1"

  Escenario: Flujo alternativo válido
    Dado un docente que registra la asistencia
    Cuando toca primero a las excepciones y luego usa "Marcar los N restantes como Asistió"
    Entonces el sistema guarda los estados resultantes

  Escenario: Caso de error
    Dado un docente que registra la asistencia de hoy
    Cuando deja a uno o más estudiantes sin estado
    Entonces la jornada queda guardada como incompleta y el sistema muestra "N de M marcados", por ejemplo "18 de 25 marcados"
```

#### US-031: Corregir la asistencia de una jornada

| Campo | Detalle |
|---|---|
| **ID** | US-031 |
| **Título** | Corregir la asistencia de una jornada |
| **Épica relacionada** | EP-04 Control de asistencia (D3) |
| **Requisito de origen** | RF-031 |
| **Prioridad** | Alta |

**Redacción:** Como **docente**, quiero **corregir la asistencia de una jornada**, para **reflejar una justificación o corregir un error**.

**Criterios de aceptación:**

```gherkin
  Escenario: Camino ideal
    Dado un estudiante registrado como "Faltó" que presenta su justificación
    Cuando el docente toca su círculo hasta "Justificado" y escribe la nota opcional "Constancia entregada a la docente"
    Entonces el sistema actualiza el estado y la nota, y guarda la corrección en el registro de actividad (RF-008)

  Escenario: Flujo alternativo válido
    Dado una jornada anterior registrada con un error
    Cuando el docente corrige el estado de un estudiante en esa fecha
    Entonces el sistema actualiza el registro de esa jornada

  Escenario: Caso de error
    Dado una jornada perteneciente a un periodo cuyas notas ya se marcaron como entregadas
    Cuando el docente intenta corregir la asistencia
    Entonces el sistema no permite el cambio y muestra el mensaje "El periodo está cerrado. Solicita a la dirección que habilite la corrección"
```

#### US-032: Impedir el registro duplicado de una jornada

| Campo | Detalle |
|---|---|
| **ID** | US-032 |
| **Título** | Impedir el registro duplicado de una jornada |
| **Épica relacionada** | EP-04 Control de asistencia (D3) |
| **Requisito de origen** | RF-032 |
| **Prioridad** | Alta |

**Redacción:** Como **docente**, quiero **que el sistema no duplique una jornada ya registrada**, para **que los totales de asistencia sean exactos**.

**Criterios de aceptación:**

```gherkin
  Escenario: Camino ideal
    Dado una sección sin asistencia registrada para la fecha de hoy
    Cuando el docente registra la asistencia
    Entonces el sistema crea un único registro para esa sección y fecha

  Escenario: Flujo alternativo válido
    Dado una sección con asistencia ya registrada para la fecha de hoy
    Cuando el docente elige registrar la asistencia de hoy
    Entonces el sistema abre el registro existente para corregirlo (RF-031)

  Escenario: Caso de error
    Dado una jornada que el docente envía dos veces por una conexión inestable
    Cuando el sistema recibe el segundo envío
    Entonces el sistema conserva un solo registro de esa jornada y no duplica los estados
```

#### US-033: Consultar el historial de asistencia

| Campo | Detalle |
|---|---|
| **ID** | US-033 |
| **Título** | Consultar el historial de asistencia |
| **Épica relacionada** | EP-04 Control de asistencia (D3) |
| **Requisito de origen** | RF-033 |
| **Prioridad** | Alta |

**Redacción:** Como **docente**, quiero **consultar el historial de asistencia por estudiante, sección o periodo**, para **dar seguimiento a las faltas y tardanzas**.

**Criterios de aceptación:**

```gherkin
  Escenario: Camino ideal
    Dado una sección con asistencia registrada durante un mes
    Cuando el docente consulta la asistencia de ese mes
    Entonces el sistema muestra cada jornada con el estado de cada estudiante y el total de cada estado

  Escenario: Flujo alternativo válido
    Dado un docente
    Cuando consulta a un solo estudiante en un periodo
    Entonces el sistema muestra las fechas con su estado y el total por estado: Tarde, Faltó y Justificado

  Escenario: Caso de error
    Dado un rango de fechas sin registros
    Cuando el docente lo consulta
    Entonces el sistema muestra el mensaje "No hay asistencia registrada en ese rango"
```

#### US-034: Exportar la asistencia a hoja de cálculo

| Campo | Detalle |
|---|---|
| **ID** | US-034 |
| **Título** | Exportar la asistencia a hoja de cálculo |
| **Épica relacionada** | EP-04 Control de asistencia (D3) |
| **Requisito de origen** | RF-034 |
| **Prioridad** | Alta |

**Redacción:** Como **docente**, quiero **exportar la asistencia a una hoja de cálculo**, para **entregarla o usarla para el reporte oficial**.

**Criterios de aceptación:**

```gherkin
  Escenario: Camino ideal
    Dado una sección con asistencia registrada en el mes
    Cuando el docente exporta ese mes
    Entonces el sistema genera una hoja de cálculo con un estudiante por fila, una jornada por columna y los totales por estado

  Escenario: Flujo alternativo válido
    Dado un docente
    Cuando exporta un solo periodo en lugar de un mes
    Entonces el sistema genera la hoja de cálculo con las jornadas de ese periodo

  Escenario: Caso de error
    Dado un rango de fechas sin registros
    Cuando el docente intenta exportarlo
    Entonces el sistema no genera el archivo y muestra el mensaje "No hay asistencia para exportar en ese rango"
```


### EP-05: Dirección

#### US-040: Consultar los consolidados

| Campo | Detalle |
|---|---|
| **ID** | US-040 |
| **Título** | Consultar los consolidados |
| **Épica relacionada** | EP-05 Dirección |
| **Requisito de origen** | RF-040 |
| **Prioridad** | Alta |

**Redacción:** Como **dirección**, quiero **consultar las notas, la asistencia y las sesiones de cada sección**, para **monitorear la práctica pedagógica sin pedir documentos físicos**.

**Criterios de aceptación:**

```gherkin
  Escenario: Camino ideal
    Dado un usuario de la dirección
    Cuando consulta los consolidados del periodo actual
    Entonces el sistema muestra, por sección, los niveles de logro registrados, los totales de asistencia y las sesiones cargadas por cada docente, que la dirección puede abrir y descargar

  Escenario: Flujo alternativo válido
    Dado un usuario de la dirección
    Cuando filtra por una sola sección
    Entonces el sistema muestra el detalle de notas y asistencia de esa sección

  Escenario: Caso de error
    Dado un usuario de la dirección que consulta los consolidados
    Cuando intenta modificar una nota o una asistencia
    Entonces el sistema no lo permite, porque el panel de la dirección es de solo lectura
```

#### US-041: Descargar los consolidados en el formato de la dirección

| Campo | Detalle |
|---|---|
| **ID** | US-041 |
| **Título** | Descargar los consolidados en el formato de la dirección |
| **Épica relacionada** | EP-05 Dirección |
| **Requisito de origen** | RF-041 |
| **Prioridad** | Media (el formato de la dirección es [DATO I.E. PENDIENTE]) |

**Redacción:** Como **dirección**, quiero **descargar los consolidados en mi formato**, para **preparar la carga en el SIAGIE**.

**Criterios de aceptación:**

```gherkin
  Escenario: Camino ideal
    Dado un formato de la dirección configurado en el sistema
    Cuando la dirección descarga las notas del periodo de todas las secciones
    Entonces el sistema genera un archivo con ese formato y las notas de cada sección

  Escenario: Flujo alternativo válido
    Dado que la dirección aún no entregó su formato propio
    Cuando descarga los consolidados
    Entonces el sistema genera una hoja de cálculo con la misma estructura de RF-024 y RF-034

  Escenario: Caso de error
    Dado secciones que aún no entregaron sus notas del periodo
    Cuando la dirección descarga los consolidados
    Entonces el sistema genera el archivo e indica qué secciones tienen las notas pendientes de entrega
```

#### US-042: Ver el estado de entrega por docente

| Campo | Detalle |
|---|---|
| **ID** | US-042 |
| **Título** | Ver el estado de entrega por docente |
| **Épica relacionada** | EP-05 Dirección |
| **Requisito de origen** | RF-042 |
| **Prioridad** | Media |

**Redacción:** Como **dirección**, quiero **ver qué docentes entregaron sus notas y habilitar correcciones**, para **dar seguimiento a la entrega de cada periodo**.

**Criterios de aceptación:**

```gherkin
  Escenario: Camino ideal
    Dado docentes que marcaron sus notas como entregadas (RF-026)
    Cuando la dirección consulta el estado de entrega del periodo
    Entonces el sistema lista a cada docente con su estado ("Entregado" o "Pendiente") y la fecha de entrega

  Escenario: Flujo alternativo válido
    Dado un docente con las notas entregadas que necesita corregir una nota
    Cuando la dirección habilita la corrección desde esta pantalla
    Entonces el sistema cambia el estado a "En corrección" y permite al docente editar (RF-026)

  Escenario: Caso de error
    Dado un periodo que aún no ha comenzado
    Cuando la dirección consulta su estado de entrega
    Entonces el sistema muestra el mensaje "El periodo aún no ha comenzado"
```

## 6. Historias técnicas (enablers)

#### EN-01: Proyecto base con Docker Compose

| Campo | Detalle |
|---|---|
| **ID** | EN-01 |
| **Título** | Proyecto Django con PostgreSQL en Docker Compose |
| **Épica relacionada** | Transversal (todas) |
| **Origen** | Documento 10, secciones 4 y 6 |

**Redacción:** Como **equipo de desarrollo**, queremos **un proyecto Django con sus 9 módulos y PostgreSQL que se levante con un solo comando**, para **trabajar los tres con el mismo entorno que producción**.

```gherkin
  Escenario: Entorno levantado
    Dado un integrante que clona el repositorio en su laptop
    Cuando ejecuta docker compose up
    Entonces la aplicación responde en el navegador y está conectada a PostgreSQL

  Escenario: Migraciones aplicadas
    Dado el entorno levantado
    Cuando se ejecutan las migraciones
    Entonces la base de datos tiene las tablas de usuario e institución del documento 11; las demás tablas llegan con su historia
```

#### EN-02: Despliegue del plan A con vista previa por Pull Request

| Campo | Detalle |
|---|---|
| **ID** | EN-02 |
| **Título** | Despliegue en Vercel y Neon |
| **Épica relacionada** | Transversal (todas) |
| **Origen** | RNF-009; documento 10, sección 5 |

**Redacción:** Como **equipo de desarrollo**, queremos **que cada Pull Request genere una vista previa y que la rama principal se publique sola**, para **probar antes de integrar y tener el sistema siempre en línea**.

```gherkin
  Escenario: Vista previa por Pull Request
    Dado un Pull Request abierto en GitHub
    Cuando Vercel termina el despliegue
    Entonces el Pull Request muestra un enlace a una vista previa conectada a una base de datos de pruebas

  Escenario: Publicación de la rama principal
    Dado un Pull Request aprobado y fusionado en la rama principal
    Cuando termina el despliegue
    Entonces la versión publicada responde por HTTPS con los cambios del Pull Request

  Escenario: Despliegue fallido
    Dado un cambio que rompe la construcción
    Cuando Vercel intenta desplegarlo
    Entonces la versión publicada anterior sigue en línea y el Pull Request muestra el error
```

#### EN-03: Archivos de sesiones en R2

| Campo | Detalle |
|---|---|
| **ID** | EN-03 |
| **Título** | Subida de archivos por el servidor a R2 y descarga con enlaces firmados |
| **Épica relacionada** | EP-02 Repositorio de sesiones |
| **Origen** | RNF-004; documento 12, sección 5 |

**Redacción:** Como **equipo de desarrollo**, queremos **que el servidor guarde en R2 los archivos de sesión de hasta 4 MB y que la descarga use enlaces firmados de corta duración**, para **caber en el límite de 4,5 MB de las funciones de Vercel sin dejar el bucket público**.

El diseño original (subida directa del navegador a R2 con enlace firmado, hasta 10 MB) se cambió en US-010 (decisión 7): el tope bajó a 4 MB y el archivo pasa por el servidor.

```gherkin
  Escenario: Subida de un archivo de 4 MB
    Dado un docente que envía una sesión con un PDF de 4 194 304 bytes en la vista previa, con el perfil Slow 4G
    Cuando el servidor la recibe
    Entonces el archivo llega a R2 y la sesión queda registrada con su tamaño

  Escenario: Enlace de descarga vencido
    Dado un enlace firmado de descarga de R2 emitido hace más de 60 segundos
    Cuando alguien intenta usarlo
    Entonces R2 no entrega el archivo

  Escenario: Archivo mayor a 4 MB
    Dado un docente que elige un archivo de 4 194 305 bytes
    Cuando intenta enviarlo
    Entonces el campo dice "El archivo supera los 4 MB. Elige uno más pequeño." y no se envía
```

#### EN-04: Seguridad de acceso

| Campo | Detalle |
|---|---|
| **ID** | EN-04 |
| **Título** | HTTPS, contraseñas, bloqueo, inactividad, permisos por sección y manejo de claves |
| **Épica relacionada** | EP-01 Usuarios y acceso |
| **Origen** | RNF-012 a RNF-015 |

**Redacción:** Como **equipo de desarrollo**, queremos **aplicar las medidas de seguridad del documento 07 en todo el sistema**, para **proteger los datos de menores de edad (Ley N.° 29733)**.

```gherkin
  Escenario: Bloqueo por intentos fallidos
    # Ya se cubre en US-001 (escenario "Cuenta bloqueada"), con el mismo mensaje genérico.
    Dado una cuenta activa
    Cuando se ingresa una contraseña incorrecta 5 veces seguidas
    Entonces la cuenta queda bloqueada durante 15 minutos

  Escenario: Contraseña guardada como hash
    Dado un usuario recién creado
    Cuando se revisa su registro en la base de datos
    Entonces la contraseña figura solo como hash

  Escenario: Cierre por inactividad
    Dado un usuario con la sesión iniciada
    Cuando pasan 60 minutos sin actividad
    Entonces la siguiente solicitud lo redirige a la pantalla de inicio de sesión

  Escenario: Intento de abrir una sección ajena
    # Ya se cubre en US-004 (escenario "Caso de error"), con el 403 y el registro del intento.
    Dado un docente que solo tiene asignada una sección
    Cuando cambia en la dirección del navegador el identificador por el de otra sección
    Entonces el sistema niega el acceso, no muestra ningún dato de esa sección y registra el intento

  Escenario: Solicitud sin token de protección
    Dado una solicitud que modifica datos y llega sin el token CSRF
    Cuando el servidor la recibe
    Entonces la rechaza y no modifica ningún registro

  Escenario: Clave incluida por error en un commit
    Dado un integrante que intenta subir al repositorio público un commit con una clave de la base de datos o de R2
    Cuando ejecuta git push
    Entonces GitHub rechaza la subida y la clave no llega al repositorio
```

#### EN-05: Respaldo, restauración y manual técnico

| Campo | Detalle |
|---|---|
| **ID** | EN-05 |
| **Título** | Respaldo diario y restauración probada |
| **Épica relacionada** | Transversal (todas) |
| **Origen** | RNF-010, RNF-019 |

**Redacción:** Como **equipo de desarrollo**, queremos **respaldos diarios de la base de datos y de los archivos, con una restauración probada**, para **no perder más de 24 horas de datos ante una falla**.

```gherkin
  Escenario: Respaldo diario
    Dado el sistema en operación
    Cuando se cumple la hora programada del respaldo
    Entonces se genera una copia de la base de datos y de los archivos, conservada durante 30 días

  Escenario: Simulacro de restauración
    Dado un respaldo del día anterior
    Cuando se restaura en un entorno limpio siguiendo el manual técnico
    Entonces el sistema queda operativo en 8 horas o menos y con los datos del respaldo
```

#### EN-06: Datos iniciales

| Campo | Detalle |
|---|---|
| **ID** | EN-06 |
| **Título** | Catálogo curricular y datos ficticios |
| **Épica relacionada** | EP-03 Registro y control de notas |
| **Origen** | RN-007, RN-018; documento 11, sección 6 |

**Redacción:** Como **equipo de desarrollo**, queremos **cargar el catálogo del registro de notas del SIAGIE con una migración y un juego de datos ficticios con un comando (`cargar_demo`)**, para **probar con datos realistas sin usar datos de estudiantes reales**.

```gherkin
  Escenario: Catálogo cargado
    Dado una base de datos recién migrada
    Cuando se aplica la migración catalogo/0002
    Entonces existen las 11 áreas y competencias del documento 09, sección 3, con Educación Religiosa y Educación Física marcadas como exonerables

  Escenario: Sin datos reales
    Dado el juego de datos de prueba
    Cuando se revisan los estudiantes cargados
    Entonces todos los nombres son ficticios
```

#### EN-07: Rendimiento, compatibilidad y accesibilidad

| Campo | Detalle |
|---|---|
| **ID** | EN-07 |
| **Título** | Pruebas de carga, de navegadores y de accesibilidad |
| **Épica relacionada** | Transversal (todas) |
| **Origen** | RNF-001, RNF-002, RNF-003, RNF-005, RNF-008 |

**Redacción:** Como **equipo de desarrollo**, queremos **medir el rendimiento, la compatibilidad y la accesibilidad antes del piloto**, para **confirmar los umbrales del documento 07**.

```gherkin
  Escenario: Prueba de carga
    Dado 30 usuarios simulados registrando asistencia y notas
    Cuando se ejecuta la prueba de carga
    Entonces el tiempo de respuesta del servidor es de 2 segundos o menos en el percentil 95

  Escenario: Carga inicial en conexión lenta
    Dado un navegador con el perfil Slow 4G simulado de Chrome DevTools (RNF-002)
    Cuando abre la pantalla de inicio de sesión
    Entonces se transfieren 2 MB o menos y la pantalla es usable en 5 segundos o menos

  Escenario: Accesibilidad
    Dado cualquier pantalla del docente o de la dirección
    Cuando se ejecuta la revisión automática de accesibilidad
    Entonces no hay errores críticos y el contraste de texto es de 4,5:1 o más
```

#### EN-08: Canal de integración continua

| Campo | Detalle |
|---|---|
| **ID** | EN-08 |
| **Título** | Pruebas, cobertura, análisis estático, puerta de calidad y pruebas de punta a punta en cada Pull Request |
| **Épica relacionada** | Transversal (todas) |
| **Origen** | RNF-018; DoD, criterios 1, 2 y 5 |

**Redacción:** Como **equipo de desarrollo**, queremos **que cada Pull Request ejecute solo las pruebas unitarias, la cobertura, Ruff, CodeQL, SonarQube Cloud y las pruebas de Playwright**, para **comprobar la DoD sin depender de revisiones manuales**.

```gherkin
  Escenario: Pull Request que cumple
    Dado un Pull Request con pruebas que pasan, cobertura de 80 % o más y sin alertas críticas ni altas
    Cuando GitHub Actions termina de ejecutar el canal
    Entonces todas las verificaciones aparecen en verde y el Pull Request puede fusionarse tras la revisión

  Escenario: Prueba fallida o cobertura insuficiente
    Dado un Pull Request con una prueba que falla o con cobertura menor a 80 %
    Cuando termina el canal
    Entonces la verificación aparece en rojo y GitHub impide fusionar el Pull Request

  Escenario: Alerta crítica de seguridad
    Dado un cambio que arma una consulta SQL con texto escrito por el usuario
    Cuando CodeQL analiza el Pull Request
    Entonces registra una alerta de severidad alta o crítica y GitHub impide fusionar el Pull Request

  Escenario: Puerta de calidad de SonarQube no superada
    Dado un Pull Request cuyo código nuevo no supera la puerta de calidad Sonar way, por ejemplo por una cobertura menor a 80 % o un error o una vulnerabilidad nuevos
    Cuando SonarQube Cloud analiza el Pull Request
    Entonces la puerta de calidad aparece como fallida en el Pull Request y GitHub impide fusionarlo

  Escenario: Canal sin claves reales
    Dado el canal de integración continua
    Cuando se ejecutan las pruebas
    Entonces usan una base de datos PostgreSQL temporal con datos ficticios y ninguna clave de producción
```

## 7. Definition of Done (DoD) global

Una historia de usuario o un enabler está **terminado** solo si cumple los 9 criterios:

| N.° | Criterio | Cómo se verifica |
|---|---|---|
| 1 | Cobertura de pruebas unitarias **≥ 80 %** del código del cambio | Informe de cobertura en GitHub Actions y puerta de calidad Sonar way de SonarQube Cloud |
| 2 | Análisis estático **sin vulnerabilidades críticas ni altas** | Ruff (calidad del código, con sus reglas de seguridad derivadas de Bandit), CodeQL (seguridad: sigue el dato desde la entrada del usuario hasta la consulta o la pantalla) y SonarQube Cloud (puerta de calidad Sonar way sobre el código nuevo: cobertura de 80 % o más, duplicación de 3 % o menos, calificación A en fiabilidad, seguridad y mantenibilidad, y *security hotspots* revisados), en GitHub Actions (EN-08) |
| 3 | Revisión aprobada por **otra integrante del equipo** mediante Pull Request; quien abre el Pull Request no lo aprueba | Aprobación registrada en GitHub |
| 4 | Despliegue automático en un ambiente de pruebas | Vista previa de Vercel del Pull Request funcionando (EN-02) |
| 5 | Todos los escenarios Gherkin de la historia **pasan**, incluida al menos una prueba de punta a punta con Playwright de la ruta ideal | Resultado de las pruebas en GitHub Actions (EN-08) |
| 6 | Las reglas de negocio de la historia (documento 09) tienen pruebas propias | Pruebas de la capa de servicios |
| 7 | Las pantallas nuevas pasan la revisión automática de accesibilidad sin errores críticos (RNF-008) | Informe de la revisión |
| 8 | Sin datos reales de estudiantes en el código, las pruebas ni los datos de ejemplo (RN-018) | Revisión del Pull Request |
| 9 | Documentación actualizada: especificación del cambio en OpenSpec, docstrings del código, catálogo de rutas de la aplicación y, si cambió un requisito, nueva versión del documento 06 | Revisión del Pull Request |

**Sobre los criterios 1 y 2:** el repositorio es público, así que CodeQL y el plan gratuito de SonarQube Cloud no tienen costo. Cada herramienta cumple un papel: Ruff revisa el estilo mientras se programa, CodeQL busca vulnerabilidades siguiendo el recorrido de los datos y SonarQube Cloud reúne en un panel la cobertura, los problemas y la duplicación del código nuevo, que sirve de evidencia de la DoD. Bandit no se usa por separado porque Ruff incluye sus reglas. CodeQL usa la configuración por defecto de GitHub, que se activa en *Settings*, sin workflow en el repositorio; el *ruleset* de la rama principal exige su resultado. En el plan gratuito, SonarQube Cloud analiza solo la rama principal y los Pull Requests dirigidos a ella, así que todo Pull Request se abre hacia la rama principal. Su única puerta de calidad es **Sonar way**, que es más estricta que el criterio 2: también bloquea errores o vulnerabilidades nuevos de menor severidad, la duplicación mayor a 3 % y los *security hotspots* sin revisar.

**Manejo de claves (repositorio público):**

| Clave | Dónde vive | Nunca en |
|---|---|---|
| Clave secreta de Django | `.env` local y variables de entorno de Vercel | El repositorio |
| Conexión a Neon (incluye contraseña) | `.env` local y variables de entorno de Vercel; una base distinta para vistas previas y para producción | El repositorio |
| Claves de acceso de Cloudflare R2 | `.env` local y variables de entorno de Vercel; un bucket de pruebas y otro de producción | El repositorio |
| Token de SonarQube Cloud | Secretos de GitHub Actions | El repositorio |
| Contraseñas de las cuentas de administrador | Gestor de contraseñas de cada integrante | El repositorio ni los chats del equipo |

- El repositorio incluye un `.env.example` con los nombres de las variables y sin valores; `.env` está en `.gitignore`.
- La protección contra subida de secretos de GitHub queda activada (EN-04).
- Si una clave llega al repositorio, se cambia de inmediato en el servicio. Borrar el commit no basta, porque el historial es público.

**Sobre el criterio 9:** la consigna pide documentación de API con OpenAPI/Swagger. Este sistema genera sus páginas en el servidor y no expone una API pública, así que el equivalente es la especificación de cada cambio en OpenSpec, la documentación del código y el catálogo de rutas de la aplicación. Si en el futuro se agrega una API, el criterio pasa a exigir OpenAPI.

## Historial de cambios

| Versión | Fecha | Autor | Descripción |
|---|---|---|---|
| 1.0.0 | 15/10/2026 | Equipo del proyecto | Versión inicial: 5 épicas, 36 historias de usuario, 7 enablers y DoD global. |
| 1.1.0 | 15/10/2026 | Equipo del proyecto | Repositorio público: CodeQL reemplaza a Bandit en el criterio 2 de la DoD; manejo de claves; EN-04 suma permisos por sección, token CSRF y bloqueo de secretos; nuevo EN-08 (canal de integración continua con Playwright). |
| 1.2.0 | 15/10/2026 | Equipo del proyecto | Se suma SonarQube Cloud (plan gratuito) a los criterios 1 y 2 de la DoD y a EN-08; su token entra en el manejo de claves; todo Pull Request se dirige a la rama principal. |
| 1.3.0 | 19/10/2026 | Equipo del proyecto | US-001: escenario de cuenta bloqueada tras 5 intentos (RN-024), con el mismo mensaje genérico; EN-04 remite a él. US-030 y US-031 según RF-030 y RF-031 del documento 06 (V_1_4_0); mensaje de US-031 en tuteo. US-028: la I.E. organiza el año en bimestres (RN-006). EN-02 sin R2 en el título (R2 es EN-03). EN-07: perfil Slow 4G (RNF-002). EN-08, escenario 4, y DoD 1 y 2: puerta de calidad Sonar way. Sección 7: CodeQL con la configuración por defecto de GitHub. |
| 1.4.0 | 21/10/2026 | Equipo del proyecto | US-001: en los escenarios Caso de error y Cuenta bloqueada, el mensaje suma la indicación "Revisa tus datos. Si el problema sigue, pide ayuda al administrador." (revisión del prototipo de US-001, heurística 9 de Nielsen). |
| 1.5.0 | 25/10/2026 | Equipo del proyecto | EN-01, escenario 2: tablas de usuario e institución; las demás con su historia (desviación aprobada). Historia del administrador: docentes activos por semana, como el KPI-01. |
| 1.6.0 | 24/11/2026 | Equipo del proyecto | Pasada de docs: historias según los RF del documento 06 V_1_7_0 (US-004 en tuteo y con 403, US-006, US-010, US-014, US-016, US-018, US-020, US-021, US-024, US-025, US-029, US-030); nueva US-015 (dejar de compartir); US-017 retirada; nueva US-036 (docente de curso, sin RF todavía); EN-03 con subida por el servidor y 4 MB; EN-04 remite a US-004; EN-06 con la migración del catálogo del SIAGIE; épicas y resumen al día. |

[← Volver al README Principal](../../README.md)
