# Verificación (US-011, US-012, US-016)

## A2 (`/codex:adversarial-review --base main`)

Corregidos, con prueba de regresión:

- **high** · pypdf citaba cadenas del documento en sus avisos de recuperación (RN-015): el logger `pypdf` queda silenciado en `texto.py`.
- **medium** · el archivo de R2 no recibía `no-store`: el enlace firma `ResponseCacheControl=no-store`.
- **medium** · eliminar (o dejar de compartir) entre leer la sesión y contar la primera vista daba 500: `registrar_vista` vuelve a comprobar con la fila bloqueada y responde «La sesión ya no está disponible».
- **medium** · las sesiones que el código anterior insertó después de la migración `0002` quedaban sin `texto_busqueda`: `extraer_textos` lo repara desde título y propósito, aunque el archivo no dé texto.

## Escenarios sin prueba automática

- Cabecera `Cache-Control: no-store` de la respuesta final de R2: sin red en las pruebas; solo se comprueba que el enlace la firma (`ResponseCacheControl`).
- Carrera de `registrar_vista` con dos hilos reales en PostgreSQL: se prueba de forma determinista (la fila cambia antes de la llamada); las de eliminar y compartir sí usan hilos reales.
- Descarga con nombre original, «Ver» en pestaña nueva y «Enlace vencido»: dependen de R2 y de Vercel, así que el equipo los verificó en la vista previa (5.6), sin prueba automática.

## Mediciones

- 5.6 (vista previa): la descarga conserva el nombre original, con tildes y espacios (el `Location` trae `filename*=utf-8''…` bien codificado); «Ver» abre en pestaña nueva; el enlace lleva `X-Amz-Expires=60` y pasado ese tiempo R2 lo rechaza con `ExpiredRequest`.
- 2.5 (vista previa, 16-11-2026): Word 29 ms (10 024 car.), PDF de unos 4 MB 1215 ms (20 597 car.), los dos con 201 y sin que la función cortara (límite de 5 s). Función `/django`: 42,8 MB, Python 3.13, tiempo máximo 300 s.
- Las dos migraciones en Neon: las sesiones de 2.5 se guardaron con texto en la vista previa, lo que las exige aplicadas.

## Minor para la descripción del PR

- La carrera de `registrar_vista` se prueba de forma determinista (la fila cambia antes de la llamada), no con dos hilos reales en PostgreSQL como las de eliminar y compartir.
- El encabezado `Cache-Control` de la respuesta final de R2 no se puede comprobar en las pruebas (sin red): solo que el enlace lo firma.
- El comando `extraer_textos` debe correrse **después** del cambio de versión (ya está en el flujo de la fusión): repara también lo que el código anterior alcance a insertar entre la migración y el cambio.
- Codex no pudo ejecutar la suite (permisos del `.venv`); la suite sí corre aquí.

## DoD 1 a 9

1. Cobertura ≥ 80 %: local 98,56 % (2538 pruebas sin e2e, `verificar.py --completo`). Sonar way: pendiente del PR.
2. Análisis estático: Ruff y formato en verde; A2 con 4 hallazgos corregidos. CodeQL y SonarQube Cloud: pendiente del PR.
3. Aprobación de otra integrante: pendiente del PR.
4. Vista previa de Vercel: desplegada y medida (2.5, 5.6); la de la rama final, pendiente del PR.
5. Escenarios y e2e: `-m e2e` completo, 595 en verde (14 min 48 s). GitHub Actions: pendiente del PR.
6. Reglas de negocio: términos «compartida ⇒ fecha», eliminar solo el autor, RN-015 sin citar contenido en logs; con pruebas de servicios.
7. Accesibilidad: axe en claro y oscuro (360 px) en «Mis sesiones», «Repositorio», el panel de filtros, la página de la sesión y sus diálogos; pantallas vistas por Marco (5.5).
8. Sin datos reales: fixtures y sesiones de demostración ficticias.
9. Documentación: Catálogo de rutas de `docs/03` con las rutas nuevas; README sin cambios. Deuda en «Workflow follow-up».
