# Verificación (US-011, US-012, US-016)

## A2 (`/codex:adversarial-review --base main`)

Corregidos, con prueba de regresión:

- **high** · pypdf citaba cadenas del documento en sus avisos de recuperación (RN-015): el logger `pypdf` queda silenciado en `texto.py`.
- **medium** · el archivo de R2 no recibía `no-store`: el enlace firma `ResponseCacheControl=no-store`.
- **medium** · eliminar (o dejar de compartir) entre leer la sesión y contar la primera vista daba 500: `registrar_vista` vuelve a comprobar con la fila bloqueada y responde «La sesión ya no está disponible».
- **medium** · las sesiones que el código anterior insertó después de la migración `0002` quedaban sin `texto_busqueda`: `extraer_textos` lo repara desde título y propósito, aunque el archivo no dé texto.

Pendiente, a la descripción del PR:

- La carrera de `registrar_vista` se prueba de forma determinista (la fila cambia antes de la llamada), no con dos hilos reales en PostgreSQL como las de eliminar y compartir.
- El encabezado `Cache-Control` de la respuesta final de R2 no se puede comprobar en las pruebas (sin red): solo que el enlace lo firma.
- El comando `extraer_textos` debe correrse **después** del cambio de versión (ya está en el flujo de la fusión): repara también lo que el código anterior alcance a insertar entre la migración y el cambio.
- Codex no pudo ejecutar la suite (permisos del `.venv`); la suite sí corre aquí.
