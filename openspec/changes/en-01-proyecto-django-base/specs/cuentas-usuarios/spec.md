# Spec Delta

## Purpose

Establece la cuenta de usuario propia del sistema, con su rol y su institución educativa, como base de la autenticación, los permisos y la atención a más de una I.E. (documentos 08 y 11).

## ADDED Requirements

### Requirement: Entidad Institución
El sistema SHALL guardar instituciones educativas con nombre obligatorio, código modular opcional y único, organización de periodos opcional limitada a BIMESTRE o TRIMESTRE, y fecha de creación automática (documento 11, sección 3.1).

#### Scenario: Institución válida
- **WHEN** se registra una institución solo con su nombre
- **THEN** queda guardada con su fecha de creación y sin código modular ni organización de periodos

#### Scenario: Código modular repetido
- **WHEN** se registra una segunda institución con el mismo código modular que otra existente
- **THEN** la base de datos rechaza el registro

#### Scenario: Organización de periodos no permitida
- **WHEN** se intenta guardar una institución con una organización de periodos distinta de BIMESTRE o TRIMESTRE
- **THEN** la base de datos rechaza el registro

### Requirement: Usuario con rol
Cada cuenta de usuario SHALL tener exactamente uno de los roles DOCENTE, DIRECCION o ADMINISTRADOR (documento 08), y su contraseña MUST guardarse solo como hash (RNF-012).

#### Scenario: Rol no permitido
- **WHEN** se intenta guardar un usuario con un rol fuera de DOCENTE, DIRECCION o ADMINISTRADOR
- **THEN** la base de datos rechaza el registro

#### Scenario: Contraseña con hash
- **WHEN** se crea un usuario con una contraseña
- **THEN** el valor guardado no es la contraseña en texto plano y la contraseña original se verifica correctamente

### Requirement: Usuario pertenece a una institución
Todo usuario con rol DOCENTE o DIRECCION MUST pertenecer a una institución; solo el rol ADMINISTRADOR puede no tenerla (documento 11, restricción `ck_usuario_institucion`).

#### Scenario: Docente sin institución
- **WHEN** se intenta guardar un usuario DOCENTE sin institución
- **THEN** la base de datos rechaza el registro

#### Scenario: Administrador sin institución
- **WHEN** se guarda un usuario ADMINISTRADOR sin institución
- **THEN** el registro se acepta

#### Scenario: Institución con usuarios
- **WHEN** se intenta eliminar una institución que tiene usuarios
- **THEN** la eliminación se rechaza

### Requirement: Campos de control de cuenta
La cuenta de usuario SHALL incluir desde su creación los campos de control que usarán historias posteriores: cambio obligatorio de contraseña (RF-007), intentos fallidos y bloqueo temporal (RN-024), con valores iniciales sin efecto.

#### Scenario: Valores iniciales
- **WHEN** se crea un usuario nuevo sin indicar esos campos
- **THEN** no debe cambiar su contraseña, tiene cero intentos fallidos y no está bloqueado
