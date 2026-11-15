// Presentación de Competencias (rebrand-us-029, D4); no es lógica de la pantalla (esa es competencias.js).
// - Hasta 899 px la tarjeta «Tu selección» es la barra fija de abajo y su alto cambia (una fila, o dos con «Deshacer cambios»,
//   o más si el texto baja de línea): se mide con un ResizeObserver y se escribe en --comp-barra, que usa el CSS para
//   scroll-padding-bottom y el pie de la página. Sin JavaScript quedan los valores de respaldo del CSS.
// - A cada casilla se le pone scroll-margin-bottom con lo que queda de su fila bajo ella, para que el foco con Tab deje la
//   fila entera sobre la barra.
(() => {
  const barra = document.querySelector(".comp-resumen");
  if (!barra) return;
  const raiz = document.documentElement;
  const celular = window.matchMedia("(max-width: 899px)");

  function medir() {
    if (celular.matches) raiz.style.setProperty("--comp-barra", `${Math.ceil(barra.getBoundingClientRect().height)}px`);
    else raiz.style.removeProperty("--comp-barra");
  }

  if ("ResizeObserver" in window) new ResizeObserver(medir).observe(barra);
  celular.addEventListener("change", medir);
  medir();

  // El resto de cada fila bajo su casilla se calcula de antemano (el desplazamiento del foco ocurre antes de focusin) y
  // se recalcula cuando la fila cambia de alto (ancho, motivos de bloqueo).
  function margen(fila) {
    const casilla = fila.querySelector("input");
    if (!casilla || !fila.offsetParent) return;
    const resto = fila.getBoundingClientRect().bottom - casilla.getBoundingClientRect().bottom;
    casilla.style.setProperty("scroll-margin-bottom", `${Math.max(0, Math.ceil(resto))}px`);
  }

  const filas = document.querySelectorAll(".comp-fila");
  if ("ResizeObserver" in window) {
    const observador = new ResizeObserver((entradas) => entradas.forEach((e) => margen(e.target)));
    filas.forEach((fila) => observador.observe(fila));
  } else {
    filas.forEach(margen);
  }
})();
