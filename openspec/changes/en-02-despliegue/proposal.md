# Propuesta: EN-02 – Despliegue del plan A con vista previa por Pull Request

## Why

El sistema solo corre en la laptop: no hay versión publicada para el asesor ni vista previa para revisar cada PR, y la DoD 4 sigue en "No aplica". EN-02 (RNF-009; documento 10, sección 5) publica el plan A en Vercel Hobby y Neon: cada PR genera una vista previa con su propia rama de Neon, y la rama principal se publica sola.

## What Changes

- **Configuración de producción** en `config/settings.py`, leída del entorno y activa solo cuando corre en Vercel (D5). La laptop y el CI quedan como hoy. Incluye:
  - hosts y orígenes CSRF a partir de las variables de sistema de Vercel;
  - HTTPS detrás del proxy de Vercel y cookies seguras;
  - conexión agrupada de Neon sin cursores del lado del servidor;
  - logs a la salida estándar.

  `manage.py check --deploy` queda sin advertencias.
- **Build en Vercel** (D6, D7):
  - `manage.py` delgado en la raíz para que Vercel detecte Django, y la entrada WSGI resoluble desde la raíz (`WSGI_APPLICATION` en modo nube);
  - script de build que compila el CSS con npm y aplica las migraciones con `DATABASE_URL_UNPOOLED` (decisión D1 del equipo);
  - Python 3.13, sin dependencias de desarrollo en el paquete;
  - `.vercelignore` para que `vercel deploy` desde la laptop no suba `.env`, `.env.local` ni `insumos/`.
- **Producción (después de la fusión):** primer despliegue de `main` y carga inicial con los comandos que ya existen (`createsuperuser`, `cargar_secciones`), corridos por Marco desde la laptop.
- **Escenario "Despliegue fallido" (después de la fusión):** un PR de prueba que rompe el build y se cierra sin fusionar.
- **README:** sección "Despliegue". `.env.example` documenta las variables nuevas, sin valores.

**Fuera de alcance:** Cloudflare R2 (EN-03); el registro mensual de disponibilidad de RNF-009; el check de Vercel en el ruleset `proteger-main` (D4 del equipo); dominio propio.

**Contradicción que solo se menciona (documento congelado):** el documento 10, 5.1, dice que las migraciones se ejecutan "desde el entorno de desarrollo". Por la decisión D1 del equipo, corren en el build de Vercel.

## Capabilities

### New Capabilities

- `despliegue`: configuración de producción leída del entorno, build y migraciones en Vercel, vista previa por PR con su rama de Neon, publicación de la rama principal y comportamiento ante un build fallido.

### Modified Capabilities

Ninguna. `entorno-desarrollo` sigue valiendo tal cual: la laptop no cambia.

## Impact

- **Código:**
  - `src/backend/config/settings.py` y sus pruebas (`config/tests/`);
  - `pyproject.toml` (`[tool.vercel]`), un script de build en `scripts/` con su prueba, `vercel.json` si hace falta (D7);
  - `.vercelignore`, `.gitignore` (`.vercel/`), `.env.example` y `README.md`.
- **Dependencias:** ninguna nueva de Python ni de npm.
- **Migraciones:** ninguna nueva. Se aplican las existentes en cada rama de Neon.
- **Rutas:** ninguna nueva ni cambiada; el Catálogo de rutas no se toca.
- **Requisitos:** EN-02, RNF-009 (sin el registro mensual), documento 10 (5 y 5.1). DoD 1 a 9: desde aquí la DoD 4 aplica.
- **Rama:** `feature/EN-02-despliegue`, desde `main`. Su primer commit ya es el archivo de US-005.
