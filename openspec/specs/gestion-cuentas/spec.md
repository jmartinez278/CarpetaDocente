# gestion-cuentas Specification

## Purpose
Permite al Administrador crear, editar y desactivar desde el panel las cuentas de docentes y de la dirección, para que solo el personal autorizado use el sistema; las cuentas se desactivan y no se eliminan (RF-003, RN-023, documento 08).

## Requirements

### Requirement: Alta de cuentas por el Administrador
El panel de administración SHALL permitir al Administrador crear una cuenta con nombres, apellidos, usuario, rol, institución y contraseña inicial, todos obligatorios. La cuenta MUST quedar activa y MUST NOT tener acceso al panel ni privilegios de superusuario. Al guardar, el panel SHALL mostrar el mensaje "Cuenta creada". El panel MUST NOT ofrecer crear una cuenta sin contraseña.

#### Scenario: Camino ideal
- **WHEN** el Administrador registra una cuenta nueva con nombres, apellidos, usuario, rol "Docente", institución y contraseña inicial
- **THEN** el sistema crea la cuenta activa y muestra el mensaje "Cuenta creada"

#### Scenario: Dato obligatorio vacío
- **WHEN** el Administrador deja vacío cualquiera de los nombres, los apellidos, la institución o la contraseña inicial
- **THEN** el sistema no crea la cuenta y señala el campo que falta

#### Scenario: Sin opción de cuenta sin contraseña
- **WHEN** el Administrador abre el alta de una cuenta
- **THEN** el formulario no ofrece crear la cuenta sin contraseña

#### Scenario: La cuenta creada no entra al panel
- **WHEN** la cuenta creada desde el panel ingresa al sistema y abre `/admin/`
- **THEN** no tiene acceso al panel ni privilegios de superusuario, y llega a la pantalla de inicio de su rol

### Requirement: Roles que se crean desde el panel
Desde el panel solo SHALL crearse cuentas con rol Docente o Dirección. Una cuenta de Administrador MUST NOT poder crearse ni asignarse desde el panel; los administradores se crean fuera del panel, por la línea de comandos.

#### Scenario: Intento de crear un Administrador
- **WHEN** el Administrador envía el alta con el rol Administrador
- **THEN** el sistema no crea la cuenta y el rol no se acepta

#### Scenario: Roles ofrecidos
- **WHEN** el Administrador abre el alta o la edición de una cuenta de docente o de la dirección
- **THEN** el campo rol ofrece solo Docente y Dirección

### Requirement: Usuario único sin distinguir mayúsculas
El usuario de una cuenta MUST ser único sin distinguir mayúsculas de minúsculas. Si ya existe, el sistema MUST NOT crear la cuenta y SHALL mostrar el mensaje "El usuario ya existe".

#### Scenario: Usuario repetido
- **WHEN** el Administrador intenta crear otra cuenta con un usuario que ya existe
- **THEN** el sistema no crea la cuenta y muestra el mensaje "El usuario ya existe"

#### Scenario: Usuario repetido con otras mayúsculas
- **WHEN** existe la cuenta "jperez" y el Administrador intenta crear otra con "JPerez"
- **THEN** el sistema no crea la cuenta y muestra el mensaje "El usuario ya existe"

### Requirement: Formato del usuario
Al crear una cuenta, el usuario MUST seguir el formato del sistema: la inicial del primer nombre y el primer apellido, en minúsculas, sin tildes, sin ñ y sin espacios, con un número al final (desde el 2) cuando esa combinación ya existe. El sistema SHALL validar la forma del usuario y SHALL proponer la base o el siguiente número libre; no exige que el usuario coincida con el calculado a partir de los nombres, y el Administrador decide el usuario final (por ejemplo, con apellidos compuestos). El alta SHALL explicar el formato con un ejemplo y, cuando el usuario se repite, SHALL proponer el siguiente que está libre.

#### Scenario: Formato inválido
- **WHEN** el Administrador escribe un usuario con mayúsculas, tildes, ñ, espacios u otros signos (por ejemplo "J.Pérez" o "j perez")
- **THEN** el sistema no crea la cuenta y explica el formato con el ejemplo "jperez"

#### Scenario: Usuario con número
- **WHEN** ya existe "jperez" y el Administrador crea una cuenta con "jperez2"
- **THEN** el sistema acepta el usuario

#### Scenario: Sugerencia del siguiente libre
- **WHEN** existen "jperez" y "jperez2" y el Administrador intenta crear "jperez" para Juana Pérez
- **THEN** el sistema muestra "El usuario ya existe" y propone "jperez3"

#### Scenario: Sugerencia a partir de nombres con tilde o ñ
- **WHEN** el Administrador crea la cuenta de "Ñahui Rosa" "Núñez Ávila" con un usuario repetido
- **THEN** la propuesta es "nnunez" (o con el número que esté libre), sin tildes ni ñ

### Requirement: Edición de cuentas
El panel SHALL permitir al Administrador editar los nombres, los apellidos, el rol, la institución y el estado activo de una cuenta. La edición MUST NOT mostrar el acceso al panel, el de superusuario, los grupos, los permisos ni el cambio obligatorio de contraseña. Los intentos fallidos y el bloqueo MUST seguir de solo lectura y "Desbloquear cuenta" no cambia. El usuario no se edita.

#### Scenario: Editar los nombres
- **WHEN** el Administrador corrige los apellidos de una cuenta y guarda
- **THEN** la cuenta queda con los apellidos nuevos y conserva su usuario y su contraseña

#### Scenario: Campos ocultos
- **WHEN** el Administrador abre la edición de una cuenta
- **THEN** no ve los campos de acceso al panel, superusuario, grupos, permisos ni cambio obligatorio de contraseña, y ve los intentos fallidos y el bloqueo sin poder cambiarlos

#### Scenario: Rol de un Administrador
- **WHEN** el Administrador abre la edición de una cuenta de Administrador
- **THEN** el rol se muestra sin poder cambiarse

### Requirement: Desactivar sin eliminar
El Administrador SHALL desactivar una cuenta quitándole "Activo". Una cuenta desactivada MUST NOT ingresar ni conservar una sesión abierta, y su fila MUST conservarse con los registros que hizo. El panel MUST NOT ofrecer eliminar cuentas: ni el botón de la cuenta ni la acción sobre varias.

#### Scenario: Docente que ya no trabaja en la institución
- **WHEN** el Administrador desactiva la cuenta de un docente
- **THEN** el sistema impide nuevos accesos con esa cuenta, con el mensaje genérico de ingreso rechazado, y la cuenta sigue en la lista como inactiva

#### Scenario: Sesión abierta de una cuenta desactivada
- **WHEN** el docente tiene la sesión iniciada y el Administrador desactiva su cuenta
- **THEN** la siguiente petición del docente lo lleva a `/ingresar/` sin mostrar la pantalla pedida

#### Scenario: No existe la opción de eliminar
- **WHEN** el Administrador abre la lista o la edición de una cuenta
- **THEN** no hay botón para eliminarla ni acción para eliminar las seleccionadas, y una petición directa de eliminación se rechaza

### Requirement: Solo el Administrador gestiona cuentas
La gestión de cuentas SHALL estar disponible solo para el rol Administrador (documento 08, matriz de acceso).

#### Scenario: Docente o dirección en la gestión de cuentas
- **WHEN** un docente o un usuario de la dirección con la sesión iniciada abre la lista o el alta de cuentas del panel
- **THEN** el sistema no muestra la gestión y lo lleva a la pantalla de inicio de su rol
