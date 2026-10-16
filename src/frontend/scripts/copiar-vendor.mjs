// Copia HTMX y Alpine.js desde node_modules a src/backend/static/dist/vendor/,
// para servirlos como estáticos propios (sin CDN externo; design.md, D9).
import { copyFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const raiz = join(dirname(fileURLToPath(import.meta.url)), "..");
const destino = join(raiz, "..", "backend", "static", "dist", "vendor");

const archivos = [
  ["node_modules/htmx.org/dist/htmx.min.js", "htmx.min.js"],
  ["node_modules/alpinejs/dist/cdn.min.js", "alpine.min.js"],
];

mkdirSync(destino, { recursive: true });
for (const [origen, nombre] of archivos) {
  copyFileSync(join(raiz, origen), join(destino, nombre));
  console.log(`copiado ${nombre}`);
}
