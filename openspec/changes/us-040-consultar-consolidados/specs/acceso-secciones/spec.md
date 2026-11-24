## MODIFIED Requirements

### Requirement: Matriz de permisos de lo construido
La matriz de permisos (documento 08, RNF-013) SHALL probarse en una sola prueba parametrizada sobre las rutas de sección construidas —estudiantes, asistencia, competencias y notas— por la docente propia, una docente ajena, la dirección, el Administrador y una visita sin sesión, con lectura y con escritura. Cada historia que agrega una ruta de sección agrega sus filas. Desde US-040 suma las rutas de la dirección —Consolidados, el detalle de una sección en sus tres pestañas y la página, la descarga y la vista de una sesión— por la dirección de la institución, la dirección de otra institución, una docente, el Administrador y una visita sin sesión, solo con lectura.

#### Scenario: Matriz
- **WHEN** corre la suite de pruebas
- **THEN** cada combinación de ruta, perfil y método responde según la matriz: la docente propia entra; la ajena, 403 con registro; la dirección y el Administrador, a su inicio; sin sesión, al ingreso; y solo la docente propia guarda

#### Scenario: Matriz de la dirección
- **WHEN** corre la suite de pruebas
- **THEN** en las rutas de la dirección, la dirección de la institución entra; la de otra institución recibe "página no encontrada" (o «La sesión ya no está disponible» en una sesión); la docente y el Administrador van a su inicio; y sin sesión, al ingreso
