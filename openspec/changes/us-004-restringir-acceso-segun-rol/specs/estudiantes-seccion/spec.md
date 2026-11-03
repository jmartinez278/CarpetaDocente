# Spec Delta

## MODIFIED Requirements

### Requirement: Acceso solo a sus secciones
Solo la docente de aula de una sección del año escolar ABIERTO SHALL ver y cambiar su lista. Una sección de otra docente, inexistente o de un año CERRADO responde 403 con el mensaje de «sin permiso» y deja una entrada de intento (spec `acceso-secciones`); otro rol va a su pantalla de inicio; sin sesión, a `/ingresar/`. Un estudiante solo se alcanza a través de su propia sección: uno de otra sección también responde 403.

#### Scenario: Sección de otra docente
- **WHEN** una docente abre la lista o edita un estudiante de una sección que no es suya
- **THEN** recibe 403 con el mensaje de «sin permiso», no ve ningún nombre y queda una entrada INTENTO_SIN_PERMISO

#### Scenario: Sección de un año cerrado
- **WHEN** la docente abre la lista de su sección de un año CERRADO
- **THEN** recibe 403

#### Scenario: Estudiante de otra sección
- **WHEN** la docente edita o quita, desde su sección, un estudiante que es de otra sección
- **THEN** recibe 403 y no se cambia nada

#### Scenario: Otro rol
- **WHEN** una cuenta de la dirección abre la dirección de la lista
- **THEN** llega a `/direccion/`
