# Spec Delta

## MODIFIED Requirements

### Requirement: Inicio de sesión único
El sistema SHALL ofrecer una sola pantalla de inicio de sesión para los tres roles, en `/ingresar/`, con los campos Usuario y Contraseña. Una cuenta activa con su usuario y su contraseña correctos MUST entrar y llegar a la pantalla de inicio de su rol. Desde US-003 el usuario escrito MUST pasarse a minúsculas antes de autenticar, de modo que el usuario no distingue mayúsculas.

#### Scenario: Camino ideal del docente
- **WHEN** un docente con una cuenta activa ingresa su usuario y su contraseña correctos en `/ingresar/`
- **THEN** el sistema le da acceso y lo lleva a `/docente/`

#### Scenario: Ingreso de la dirección
- **WHEN** un usuario de la dirección con una cuenta activa ingresa su usuario y su contraseña correctos
- **THEN** el sistema le da acceso y lo lleva a `/direccion/`

#### Scenario: Ingreso del administrador
- **WHEN** un administrador con una cuenta activa ingresa su usuario y su contraseña correctos
- **THEN** el sistema le da acceso y lo lleva al panel de administración en `/admin/`

#### Scenario: Campos vacíos
- **WHEN** se envía el formulario con el usuario o la contraseña vacíos
- **THEN** el sistema no intenta el ingreso, no cuenta un intento fallido y muestra junto a cada campo vacío "Ingresa tu usuario." o "Ingresa tu contraseña."

#### Scenario: Usuario con mayúsculas
- **WHEN** la docente de la cuenta "jperez" ingresa "JPerez" con su contraseña correcta
- **THEN** el sistema le da acceso y la lleva a `/docente/`

### Requirement: Bloqueo temporal por intentos fallidos
Después de 5 intentos fallidos consecutivos sobre una misma cuenta, el sistema MUST bloquearla durante 15 minutos (RN-024). Mientras dure el bloqueo, ningún intento entra, ni siquiera con la contraseña correcta, y esos intentos no se cuentan. Al terminar el bloqueo, la cuenta vuelve a aceptar su contraseña y el conteo empieza de cero. Un intento cuenta en la cuenta de su usuario en minúsculas, sin importar cómo se escribió.

#### Scenario: Quinto intento fallido
- **WHEN** se ingresa una contraseña incorrecta 5 veces seguidas para una cuenta activa
- **THEN** la cuenta queda bloqueada durante 15 minutos desde el quinto intento

#### Scenario: Contraseña correcta durante el bloqueo
- **WHEN** el usuario de una cuenta bloqueada ingresa su contraseña correcta antes de que pasen 15 minutos
- **THEN** el sistema niega el acceso con el mismo mensaje genérico, sin indicar que la cuenta está bloqueada, y el fin del bloqueo no cambia

#### Scenario: Intentos durante el bloqueo
- **WHEN** se ingresan contraseñas incorrectas mientras la cuenta está bloqueada
- **THEN** esos intentos no cuentan y el fin del bloqueo no se extiende

#### Scenario: Fin del bloqueo
- **WHEN** pasan 15 minutos desde el bloqueo y el usuario ingresa su contraseña correcta
- **THEN** el sistema le da acceso

#### Scenario: Primer fallo después del bloqueo
- **WHEN** terminó el bloqueo y el usuario ingresa una contraseña incorrecta una vez
- **THEN** la cuenta no vuelve a bloquearse: es el primer intento fallido de un nuevo conteo

#### Scenario: Intentos con otras mayúsculas
- **WHEN** se ingresa una contraseña incorrecta 5 veces seguidas para la cuenta "jperez", escribiendo el usuario como "jperez", "JPerez" o "JPEREZ"
- **THEN** los 5 intentos cuentan en la misma cuenta y "jperez" queda bloqueada durante 15 minutos
