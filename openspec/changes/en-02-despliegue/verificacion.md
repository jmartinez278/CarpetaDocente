# Verificación: EN-02 – Despliegue del plan A

Se completa en el grupo 3 (tabla escenario → prueba y DoD 1 a 9).

## Minor para la descripción del PR

- `CSRF_TRUSTED_ORIGINS` se arma con `https://` + cada host de `ALLOWED_HOSTS` (D5). Si `DJANGO_ALLOWED_HOSTS` llevara un comodín (`*` o `.dominio`), el origen resultante no sería válido. Hoy esa variable no se usa con comodines en Vercel.
- El escenario de `iterator()` sin cursor con nombre se prueba por la configuración (`DISABLE_SERVER_SIDE_CURSORS`, `CONN_MAX_AGE = 0`), no recorriendo filas por la conexión agrupada de Neon: eso se ve en la vista previa (grupo 2).
- `test_en_vercel_check_deploy_no_da_errores_ni_advertencias`: la comprobación de `"WARNINGS" not in stderr` es redundante con `--fail-level WARNING`.
- `VERCEL=` vacío (copia de `.env.example`) se lee como apagado; no tiene prueba propia.
