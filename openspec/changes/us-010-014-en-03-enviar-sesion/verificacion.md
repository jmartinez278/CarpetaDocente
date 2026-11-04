# Verificación: US-010, US-014 y EN-03 – Enviar una sesión a la dirección

## Minor para la descripción del PR

- Parte A: fuera de Vercel, R2 a medias (alguna variable `AWS_*` sí y otra no) no arranca, para que boto3 no tome credenciales de `~/.aws` sin avisar (ajuste a D2). Quien tenga una `AWS_*` exportada por otro proyecto debe quitarla (el mensaje nombra la variable).
- Parte A: Django 5.2 no escribe `ON DELETE` en el DDL; las FK de `sesion` quedan `NO ACTION` diferidas y PROTECT lo aplica el ORM (cuatro pruebas de `ProtectedError`). La verificación de 1.2 («las FK con su `ON DELETE`») no se cumple tal como está escrita.
- Parte B: si falla el borrado del archivo tras un error de la base, el log no nombra la clave (`sesiones/<UUID>`) del objeto que queda en R2 para borrarlo a mano.
- Parte B: ninguna prueba cubre el reintento con el mismo `id` sin archivo o con otros datos (D5 devuelve la sesión previa antes de validar).
- Parte B: un POST a mano con un carácter NUL en `titulo` o `proposito` da 500 en PostgreSQL y no un error del campo; desde la pantalla no se provoca.
- Parte C: «Falla el almacenamiento» se prueba en el servicio (`test_servicios_enviar.py`), no en la vista; ahí sale como 500, que D7 trata como «Se cortó la conexión».
- Parte C: «Otro rol» prueba el GET sin `HX-Request`; el GET con `HX-Request` lo cubre `RolRequeridoMixin`, sin prueba propia en Sesiones.
- Parte C: `EnviarSesionView` lee `error.message_dict`; un `ValidationError` sin campo desde el servicio daría 500 y no 400 (hoy el servicio siempre arma un dict).

## Medición D3 (tarea 3.3)

Vista previa de `968e27c` (`dpl_8xoetvbC8WFnQ4CVf5ftkuEWJkuY`), región `iad1`. Cuenta ficticia `demounoa`, cargada con `cargar_demo --institucion 2` en la rama de Neon de la vista previa. Subida con `curl --limit-rate 84375` (675 kbit/s, la subida de Slow 4G), sin la latencia del perfil.

- Build: migraciones `actividad.0005` y `repositorio.0001` aplicadas en Neon; Django 5.2.18 arranca (`GET /ingresar/` 200).
- Paquete: función `django` de 39,02 MB (`vercel inspect`; el log del build no lo muestra).

| Intento | Archivo | Tiempo | Respuesta | Sesión | Objeto en R2 |
|---|---|---|---|---|---|
| 1 (2026-11-04) | PDF de 4 194 304 bytes | 50,7 s (subida completa, 4 195 090 bytes) | 500: `PutObject` → `Unauthorized` de R2 | No (reenvío del mismo `id` → 400) | No |
| 2 (2026-11-04) | PDF de 4 194 304 bytes | 54,0 s (subida completa, 4 195 090 bytes) | 201: «Sesión enviada a la dirección» | Sí (reenvío del mismo `id` → 201) | Sí: `sesiones/<id>.pdf`, 4 194 304 bytes, `application/pdf` |

- Intento 1: la función no cortó por tiempo ni por tamaño; recibió el cuerpo entero y llegó a `storage.save`. R2 rechazó la escritura porque en Vercel (Preview) estaban otras claves; un diagnóstico local con el token del bucket de preview leyó y escribió bien. Todo o nada se cumplió: sin fila, sin entrada y sin archivo.
- Intento 2: claves de Preview reemplazadas y redeploy de `968e27c` (`dpl_DtHr3wnrVP1mfWPni2NdXjB3Fr6Y`, función de 39,02 MB, sin migraciones pendientes). La función no cortó.
- «Archivo no público»: un GET sin firma al objeto en el endpoint S3 de R2 responde 400; el token del bucket de preview no puede leer `carpetadocente-produccion` (403). En el panel de Cloudflare, «Public Development URL» (`r2.dev`) del bucket está desactivado.
- Demo, sesión y objeto de la medición quedan en la vista previa; se limpian con `quitar_demo` (deuda del bloque 3).
