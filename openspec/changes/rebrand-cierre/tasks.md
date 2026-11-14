# Tasks

Tres commits en el orden de decisiones.md: A (dirección), B (retiro de lo viejo) y C (nombres finales, solo nombres). B y C tocan el build que usan Vercel y el Dockerfile: son de alto riesgo, sin revisor (no tocan modelos, permisos ni datos personales). El archivo de `rebrand-us-020` ya está hecho (`b200ba9`).

Comandos: `uv run pytest src/backend/cuentas src/backend/repositorio scripts` y, para las e2e, `uv run pytest -m e2e <archivo> --browser chromium` con el CSS compilado y `DJANGO_ALLOW_ASYNC_UNSAFE=true`.

## 1. Cierre del rebrand

### Parte A: inicio de la dirección (normal)

- [x] 1.1 Prueba primero, `cuentas/tests/test_pantallas.py` (D1): `/direccion/` carga solo `dist/rebrand.css`; la barra lleva `appbar--portada`, sin ☰ (`data-menu-navegacion`) ni título; `<h1>` «Hola, Rosa Huamán» con `.saludo`, «Dirección» debajo, `<h2>` «Consolidados» y el estado vacío `.empty` con su ícono y el texto de la spec; scripts: los del marco, sin `portada.js` ni HTMX. `test_la_barra_de_la_direccion_lleva_la_linea_tenue` (clase `barra-superior` del marco viejo) pasa a esto. Luego `direccion/inicio.html` y su `@source` en `rebrand.css`. Verificar: rojo y luego verde; pruebas de `cuentas`
- [x] 1.2 Prueba primero, `cuentas/tests/test_marco_rebrand.py` (decisión 4): `test_el_menu_viejo_tambien_lleva_los_ganchos` pasa a la cuenta de la dirección en el marco del rebrand: «Tu cuenta», «Rosa Huamán», la I.E. y «Cerrar sesión», sin línea de sección. Verificar: pruebas de `cuentas`
- [x] 1.3 Prueba primero, `cuentas/tests/test_marco_rebrand_e2e.py`: `test_cada_pagina_carga_una_sola_hoja` suma `/direccion/` con `/static/dist/rebrand.css` (falla con el marco viejo hasta 1.1). Luego, sin cambios, `test_accesibilidad_e2e.py` con `direccion` y `direccion-menu-abierto` (delta «Accesibilidad en ambos temas») y `test_el_menu_abierto_no_desborda_la_ventana`. Verificar: esas e2e en verde
- [x] 1.4 Pantalla vista en claro/oscuro, a 360 y 1280 px, con la cuenta cerrada y abierta (la marca Marco). `verificar.py` y commit

### Parte B: retiro de lo viejo (alto riesgo)

- [x] 1.5 Inventario antes de borrar: grep de `base.html`, `marco.html`, `componentes/`, `dist/app.css`, `css/app.css` y Besley en `src/` y `scripts/`. Lo que aparezca fuera de lo que se borra y de las pruebas de 1.6–1.8 se anota aquí antes de seguir. Verificar: lista vacía o anotada
  - Besley sigue en uso legítimo (inicio de sesión del rebrand): `cuentas/ingresar.html`, `rebrand/pantallas/ingreso.css`, `copiar-vendor.mjs`, `package.json` y sus pruebas. No se toca.
  - `assert "dist/app.css" not in html` en `asistencia`, `institucion`, `notas` (2), `repositorio` y `cuentas` (`test_pantallas.py`, `test_marco_rebrand.py`): siguen ciertas en B; se invierten en C (1.11).
  - `scripts/tests/test_verificar.py` (`templates/base.html`, `templates/componentes/pie.html`) y `test_hooks.py` (`static/dist/app.css`): rutas de ejemplo para las reglas, no archivos que se lean; siguen válidas. Sin cambios.
  - Fuera de `src/` y `scripts/` (Dockerfile, CI, Vercel, hooks): ninguna referencia.
- [x] 1.6 Prueba primero, `scripts/tests/test_paquete_frontend.py` (D2): `build` compila **una** hoja (`css/rebrand.css` → `dist/rebrand.css`), `vigilar.mjs` nombra una sola entrada y no existe `src/frontend/css/app.css`; las pruebas «las dos hojas» / «las dos entradas» pasan a esto. Luego `package.json` (`build`; `dev` y `dev:contenedor` siguen con `vigilar.mjs`), `vigilar.mjs` y su comentario. Verificar: rojo y luego verde; `uv run pytest scripts`; borrar `static/dist/app.css` local, `npm run build` y en `dist/` solo queda `rebrand.css` de hojas
- [x] 1.7 Prueba primero, `cuentas/tests/test_pantallas.py`: no existe `templates/componentes/` y ninguna plantilla de `templates/` extiende `base.html` o `marco.html` sin sufijo. Luego borrar `templates/base.html`, `templates/marco.html`, `templates/componentes/` y `src/frontend/css/app.css`; borrar `test_app_css_no_trae_los_tokens_del_rebrand` (D2). Verificar: rojo y luego verde; pruebas de `cuentas`
- [x] 1.8 Prueba de caracterización, `repositorio/tests/test_plantillas.py` (decisión 6): el pie de «Subir una sesión» tiene un solo botón «Enviar a la dirección» con `btn--primary`, `type="submit"`, `form="formulario-sesion"` y `data-enviar`; pasa antes y después. Luego `_subir_pie.html` usa `rb/boton.html` con `variante="principal"`, `tipo="submit"`, `formulario="formulario-sesion"` y `datos="enviar"`. Verificar: pruebas de `repositorio` y `uv run pytest -m e2e src/backend/repositorio/tests/test_sesiones_e2e.py --browser chromium`
- [x] 1.9 Prueba de caracterización, `cuentas/tests/test_admin.py` (decisión 7): `/admin/` con un Administrador carga `css/panel.css` y ninguna hoja de `dist/`. Verificar: pruebas de `cuentas`; el panel abierto a mano se ve igual que antes
- [x] 1.10 `verificar.py` y commit

### Parte C: nombres finales (alto riesgo)

- [x] 1.11 Prueba primero (D3): las pruebas que nombran hojas o marcos pasan a los nombres finales (`asistencia/tests/test_vistas.py`, `institucion/tests/test_vistas_estudiantes.py`, `notas/tests/test_plantilla.py`, `test_plantilla_hoja.py`, `repositorio/tests/test_plantillas.py`, `cuentas/tests/test_pantallas.py`, `test_marco_rebrand.py`, `test_marco_rebrand_e2e.py`, `test_ingresar_e2e.py`, `test_hoja_rebrand_e2e.py`, `scripts/tests/test_paquete_frontend.py`, `test_verificar.py`): carga `dist/app.css` y no `dist/rebrand.css`, `render_to_string("base.html")`, salida `dist/app.css`. Luego `git mv` de `base_rebrand.html` → `base.html`, `marco_rebrand.html` → `marco.html` y `css/rebrand.css` → `css/app.css`, y solo cadenas: `extends`, `@source`, comentarios, `package.json`, `vigilar.mjs`. Verificar: rojo y luego verde; grep de `rebrand\.css`, `marco_rebrand` y `base_rebrand` vacío fuera de `openspec/changes/archive/`, `insumos/` y `docs/`; borrar `dist/rebrand.css` local y `npm run build` deja solo `app.css`
- [x] 1.12 e2e tocadas en 1.11: `test_marco_rebrand_e2e.py`, `test_ingresar_e2e.py` y `test_hoja_rebrand_e2e.py`. `verificar.py` y commit (solo renombres y referencias)

## 2. Cierre

### Parte D: A2 y verificacion.md

- [ ] 2.1 `-m e2e` completo una vez (último cambio del rebrand) y `verificar.py --completo` (80 % o más). Con la A2 que corre el usuario (`/codex:adversarial-review --base main --background`, con foco en el delta de `pantallas-de-inicio` y en las partes B y C), corregir los Critical e Important con la prueba primero. Verificar: `verificar.py --antes-del-commit` en verde
- [ ] 2.2 `verificacion.md` corta: DoD 1 a 9, escenarios del delta sin prueba con su motivo y los Minor. Verificar: commit

## e2e a retirar

Ninguna: las de la dirección (axe a 360 y 1280 px, cuenta abierta a 320 y 360 px) las pide la spec. `test_app_css_no_trae_los_tokens_del_rebrand` se borra con la hoja que revisa (1.7).

## Workflow follow-up

- **(auditoría visual)** Única, sobre todas las pantallas (Impeccable `critique`/`detect` y Playwright MCP), incluida la dirección, antes del push final.
- **(push y PR #73)** Push con aprobación; «## Deuda» en la descripción del PR con los «Pendientes globales» del PLAN y lo de abajo.
- **(US-040)** Diseño real de la dirección con prototipos, cuando lleguen sus consolidados.
- **(PR #73, deuda)** `PeriodoDeLaSeccion.nombre` («B3»): retirarlo es un cambio aparte, fuera del rebrand, con migración y revisor (decidido por Marco en el propose, 14-11-2026).
- **(T-04)** El lugar del botón de tema en la barra sigue vacío.
- **(simplificar)** `vigilar.mjs` con una sola entrada podría ser un `--watch` directo; queda como está (D2).
