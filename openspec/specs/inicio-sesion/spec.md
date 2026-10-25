# inicio-sesion Specification

## Purpose
Controla la entrada al sistema con usuario y contraseña: quién entra, a qué pantalla llega según su rol, cómo se rechaza un intento sin revelar el motivo y cómo se protege una cuenta contra intentos repetidos (RF-001, RN-024, RNF-012).

## Requirements

### Requirement: Inicio de sesión único
El sistema SHALL ofrecer una sola pantalla de inicio de sesión para los tres roles, en `/ingresar/`, con los campos Usuario y Contraseña. Una cuenta activa con su usuario y su contraseña correctos MUST entrar y llegar a la pantalla de inicio de su rol.

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

### Requirement: Mensaje genérico ante un ingreso rechazado
Ante una contraseña incorrecta, un usuario que no existe, una cuenta desactivada o una cuenta bloqueada, el sistema MUST negar el acceso con el mismo mensaje en dos líneas: "Usuario o contraseña incorrectos, o cuenta inactiva" y "Revisa tus datos. Si el problema sigue, pide ayuda al administrador.", sin indicar cuál de los datos falló ni si la cuenta está bloqueada.

#### Scenario: Contraseña incorrecta
- **WHEN** un usuario ingresa una contraseña incorrecta
- **THEN** el sistema niega el acceso, muestra el mensaje genérico en dos líneas y conserva el usuario escrito, pero no la contraseña

#### Scenario: Cuenta desactivada
- **WHEN** el usuario de una cuenta desactivada ingresa su contraseña correcta
- **THEN** el sistema niega el acceso con el mismo mensaje genérico

#### Scenario: Usuario inexistente
- **WHEN** alguien ingresa un usuario que no existe
- **THEN** el sistema niega el acceso con el mismo mensaje genérico, y la respuesta no permite distinguir este caso de una contraseña incorrecta

### Requirement: Bloqueo temporal por intentos fallidos
Después de 5 intentos fallidos consecutivos sobre una misma cuenta, el sistema MUST bloquearla durante 15 minutos (RN-024). Mientras dure el bloqueo, ningún intento entra, ni siquiera con la contraseña correcta, y esos intentos no se cuentan. Al terminar el bloqueo, la cuenta vuelve a aceptar su contraseña y el conteo empieza de cero.

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

### Requirement: Ingreso correcto reinicia el conteo
Un ingreso correcto MUST dejar la cuenta sin intentos fallidos acumulados, de modo que solo 5 fallos consecutivos, sin un ingreso correcto entre ellos, bloqueen la cuenta.

#### Scenario: Fallos con un ingreso correcto en medio
- **WHEN** se ingresan 4 contraseñas incorrectas, luego la correcta y luego 4 incorrectas más
- **THEN** la cuenta no queda bloqueada

### Requirement: Desbloqueo desde el panel de administración
El panel de administración SHALL ofrecer al Administrador la acción "Desbloquear cuenta" sobre las cuentas seleccionadas. La acción MUST quitar el bloqueo y los intentos acumulados, y MUST dejar constancia en el historial de cada cuenta desbloqueada.

#### Scenario: Desbloqueo de una cuenta bloqueada
- **WHEN** el Administrador aplica "Desbloquear cuenta" a una cuenta bloqueada
- **THEN** la cuenta acepta de inmediato su contraseña correcta, sus intentos fallidos vuelven a cero y su historial registra el desbloqueo, con quién lo hizo y cuándo

#### Scenario: Cuenta que no estaba bloqueada
- **WHEN** el Administrador aplica "Desbloquear cuenta" a una cuenta sin bloqueo ni intentos acumulados
- **THEN** la cuenta no cambia, su historial no registra nada y el panel informa que no había nada que desbloquear

### Requirement: Un solo punto de entrada
El panel de administración MUST NOT ofrecer un inicio de sesión propio: su pantalla de ingreso redirige a `/ingresar/`, de modo que todo ingreso pasa por el mismo mensaje genérico y el mismo bloqueo.

#### Scenario: Ingreso al panel sin sesión
- **WHEN** alguien sin sesión abre `/admin/` o `/admin/login/`
- **THEN** el sistema lo lleva a `/ingresar/`, y al ingresar como administrador vuelve al panel

### Requirement: Redirección de la ruta raíz
La ruta raíz `/` SHALL llevar a quien no tiene sesión a `/ingresar/` y a quien tiene sesión a la pantalla de inicio de su rol. Quien ya tiene sesión y abre `/ingresar/` MUST ir a la pantalla de su rol.

#### Scenario: Raíz sin sesión
- **WHEN** alguien sin sesión abre `/`
- **THEN** el sistema lo redirige a `/ingresar/`

#### Scenario: Raíz con sesión
- **WHEN** un docente con la sesión iniciada abre `/`
- **THEN** el sistema lo redirige a `/docente/`

#### Scenario: Ingresar con la sesión ya iniciada
- **WHEN** un usuario de la dirección con la sesión iniciada abre `/ingresar/`
- **THEN** el sistema lo redirige a `/direccion/` sin mostrar el formulario

### Requirement: Pantalla de inicio reservada a su rol
Cada pantalla de inicio de rol MUST exigir la sesión iniciada y el rol que le corresponde. Sin sesión, el sistema lleva a `/ingresar/`. Con otro rol, lleva a la pantalla de inicio de ese rol, sin mostrar contenido de la pantalla pedida. La verificación de rol es la misma para toda pantalla nueva de un rol.

#### Scenario: Pantalla de rol sin sesión
- **WHEN** alguien sin sesión abre `/docente/`
- **THEN** el sistema lo lleva a `/ingresar/` y, al ingresar como docente, vuelve a `/docente/`

#### Scenario: Docente en la pantalla de la dirección
- **WHEN** un docente con la sesión iniciada abre `/direccion/`
- **THEN** el sistema lo redirige a `/docente/`

#### Scenario: Dirección en la pantalla del docente
- **WHEN** un usuario de la dirección con la sesión iniciada abre `/docente/`
- **THEN** el sistema lo redirige a `/direccion/`

#### Scenario: Usuario sin acceso al panel
- **WHEN** un docente con la sesión iniciada abre `/admin/`
- **THEN** el sistema no muestra el panel y lo redirige a `/docente/`, sin entrar en un ciclo de redirecciones
