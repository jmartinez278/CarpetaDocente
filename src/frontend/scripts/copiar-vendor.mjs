// Copia HTMX y Alpine.js a src/backend/static/dist/vendor/ y Besley a dist/fuentes/,
// para servirlos como estáticos propios (sin CDN externo; design.md, D9).
import { copyFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const raiz = join(dirname(fileURLToPath(import.meta.url)), "..");
const dist = join(raiz, "..", "backend", "static", "dist");

const archivos = [
  ["node_modules/htmx.org/dist/htmx.min.js", "vendor", "htmx.min.js"],
  ["node_modules/alpinejs/dist/cdn.min.js", "vendor", "alpine.min.js"],
  [
    "node_modules/@fontsource/besley/files/besley-latin-600-normal.woff2",
    "fuentes",
    "besley-latin-600-normal.woff2",
  ],
  ["node_modules/@fontsource/besley/LICENSE", "fuentes", "LICENSE"],
];

for (const [origen, carpeta, nombre] of archivos) {
  mkdirSync(join(dist, carpeta), { recursive: true });
  copyFileSync(join(raiz, origen), join(dist, carpeta, nombre));
  console.log(`copiado ${carpeta}/${nombre}`);
}
