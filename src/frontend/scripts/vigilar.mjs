// Vigila las dos entradas de Tailwind a la vez (rebrand-base, D2): un `tailwindcss --watch=always`
// por hoja. En Windows `cmd` no corre dos `--watch` con `&`, y así no hace falta otra dependencia.
// Los argumentos extra (por ejemplo `--poll=1000` en el contenedor) pasan a los dos.
// Si un vigilante termina, o llega Ctrl+C, se cierra el otro.
import { spawn } from "node:child_process";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const raiz = join(dirname(fileURLToPath(import.meta.url)), "..");

// La CLI se corre con este mismo Node, sin shell: así `kill()` llega al vigilante y no a un `cmd`.
const require = createRequire(import.meta.url);
const paqueteCli = require.resolve("@tailwindcss/cli/package.json");
const cli = join(dirname(paqueteCli), JSON.parse(readFileSync(paqueteCli, "utf8")).bin.tailwindcss);

const hojas = [
  ["app.css", "./css/app.css", "../backend/static/dist/app.css"],
  ["rebrand.css", "./css/rebrand.css", "../backend/static/dist/rebrand.css"],
];
const extra = process.argv.slice(2);

const vigilantes = new Map();
let cerrando = false;

function reenviar(flujo, destino, nombre) {
  let resto = "";
  flujo.setEncoding("utf8");
  flujo.on("data", (trozo) => {
    const lineas = (resto + trozo).split(/\r?\n/);
    resto = lineas.pop();
    for (const linea of lineas) destino.write(`[${nombre}] ${linea}\n`);
  });
  flujo.on("end", () => {
    if (resto) destino.write(`[${nombre}] ${resto}\n`);
  });
}

function cerrarTodo(codigo) {
  if (cerrando) return;
  cerrando = true;
  process.exitCode = codigo;
  for (const hijo of vigilantes.values()) {
    if (hijo.exitCode === null && hijo.signalCode === null) hijo.kill();
  }
}

for (const [nombre, entrada, salida] of hojas) {
  const hijo = spawn(
    process.execPath,
    [cli, "-i", entrada, "-o", salida, "--watch=always", ...extra],
    { cwd: raiz, stdio: ["ignore", "pipe", "pipe"] },
  );
  reenviar(hijo.stdout, process.stdout, nombre);
  reenviar(hijo.stderr, process.stderr, nombre);
  hijo.on("error", (error) => {
    console.error(`[${nombre}] no arrancó: ${error.message}`);
    cerrarTodo(1);
  });
  hijo.on("exit", (codigo, senal) => {
    vigilantes.delete(nombre);
    if (!cerrando) {
      console.error(`[${nombre}] terminó (${senal ?? codigo}); se cierra el otro vigilante`);
      cerrarTodo(codigo || 1);
    }
  });
  vigilantes.set(nombre, hijo);
}

for (const senal of ["SIGINT", "SIGTERM"]) {
  process.on(senal, () => cerrarTodo(0));
}
