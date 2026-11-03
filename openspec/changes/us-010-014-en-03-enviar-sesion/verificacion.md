# Verificación: US-010, US-014 y EN-03 – Enviar una sesión a la dirección

## Minor para la descripción del PR

- Parte A: fuera de Vercel, R2 a medias (alguna variable `AWS_*` sí y otra no) no arranca, para que boto3 no tome credenciales de `~/.aws` sin avisar (ajuste a D2). Quien tenga una `AWS_*` exportada por otro proyecto debe quitarla (el mensaje nombra la variable).
- Parte A: Django 5.2 no escribe `ON DELETE` en el DDL; las FK de `sesion` quedan `NO ACTION` diferidas y PROTECT lo aplica el ORM (cuatro pruebas de `ProtectedError`). La verificación de 1.2 («las FK con su `ON DELETE`») no se cumple tal como está escrita.
- Parte B: si falla el borrado del archivo tras un error de la base, el log no nombra la clave (`sesiones/<UUID>`) del objeto que queda en R2 para borrarlo a mano.
- Parte B: ninguna prueba cubre el reintento con el mismo `id` sin archivo o con otros datos (D5 devuelve la sesión previa antes de validar).
- Parte B: un POST a mano con un carácter NUL en `titulo` o `proposito` da 500 en PostgreSQL y no un error del campo; desde la pantalla no se provoca.
