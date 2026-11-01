// Borradores de la hoja de notas en este dispositivo (design de US-020, D10). Sin dependencias; lo usan notas.js (leer,
// escribir y borrar el borrador de cada área) y menu.js (borrar los de la cuenta al cerrar sesión).
//
// - Clave: cd:notas:v1:u<usuario>:s<seccion>:p<numero>:a<codigo>. Valor: {v: 1, fecha, rev, celdas}, con celdas
//   {"<estudiante>-<competencia>": {nivel, conclusion, base}}. Solo identificadores, niveles, conclusiones y fechas: nunca
//   nombres de estudiantes, áreas ni competencias (Ley 29733, RN-014/016).
// - Toda lectura y escritura va en try/catch: sin almacenamiento (bloqueado, lleno o en modo privado) la hoja funciona igual y
//   no conserva borradores.
window.NotasBorrador ??= (() => {
  const VERSION = 1;
  const PREFIJO = "cd:notas:v1:";
  const NIVELES = ["AD", "A", "B", "C"];

  const almacen = () => {
    try {
      return window.localStorage;
    } catch {
      return null;
    }
  };

  // Una nota guardada {nivel, conclusion} o null; cualquier otra cosa no es una base válida.
  const nota = (valor) =>
    valor && typeof valor === "object" && NIVELES.includes(valor.nivel)
      ? { nivel: valor.nivel, conclusion: typeof valor.conclusion === "string" ? valor.conclusion.slice(0, 500) : "" }
      : null;

  // El borrador de una clave, ya depurado: solo celdas con un nivel de la escala. null si no hay o no se puede leer.
  function leer(clave) {
    try {
      const texto = almacen()?.getItem(clave);
      if (!texto) return null;
      const valor = JSON.parse(texto);
      if (!valor || valor.v !== VERSION || typeof valor.celdas !== "object" || valor.celdas === null) return null;
      const celdas = {};
      for (const [id, celda] of Object.entries(valor.celdas)) {
        if (!/^\d+-\d+$/.test(id)) continue;
        const actual = nota(celda);
        if (actual) celdas[id] = { ...actual, base: nota(celda.base) };
      }
      return { fecha: typeof valor.fecha === "string" ? valor.fecha : null, rev: typeof valor.rev === "string" ? valor.rev : null, celdas };
    } catch {
      return null;
    }
  }

  // Escribe el borrador; sin celdas, borra la clave. Devuelve false si el dispositivo no lo pudo guardar.
  function escribir(clave, { fecha, rev, celdas }) {
    if (!Object.keys(celdas).length) return borrar(clave);
    try {
      const destino = almacen();
      if (!destino) return false;
      destino.setItem(clave, JSON.stringify({ v: VERSION, fecha, rev, celdas }));
      return true;
    } catch {
      return false;
    }
  }

  function borrar(clave) {
    try {
      almacen()?.removeItem(clave);
      return true;
    } catch {
      return false;
    }
  }

  // Las claves que empiezan con ese prefijo (por ejemplo, las de una cuenta y sección).
  function claves(prefijo) {
    try {
      const origen = almacen();
      if (!origen) return [];
      const lista = [];
      for (let i = 0; i < origen.length; i++) {
        const clave = origen.key(i);
        if (clave?.startsWith(prefijo)) lista.push(clave);
      }
      return lista;
    } catch {
      return [];
    }
  }

  // Al cerrar sesión: los borradores de esa cuenta, de todas sus secciones, periodos y áreas.
  function borrarCuenta(usuario) {
    if (!/^\d+$/.test(String(usuario))) return;
    for (const clave of claves(`${PREFIJO}u${usuario}:`)) borrar(clave);
  }

  // Envía un formulario que una pantalla detuvo para preguntar antes de salir (notas.js, competencias.js). submit() no
  // dispara el evento submit, así que menu.js no se entera: si es «Cerrar sesión», los borradores se borran aquí.
  function enviar(formulario) {
    if (formulario.matches("[data-salir]")) borrarCuenta(formulario.dataset.usuario);
    formulario.submit();
  }

  // ¿El dispositivo deja guardar? Prueba una escritura real (en modo privado o lleno, setItem falla).
  function disponible() {
    try {
      const destino = almacen();
      if (!destino) return false;
      destino.setItem(`${PREFIJO}prueba`, "1");
      destino.removeItem(`${PREFIJO}prueba`);
      return true;
    } catch {
      return false;
    }
  }

  return { leer, escribir, borrar, claves, borrarCuenta, enviar, disponible };
})();
