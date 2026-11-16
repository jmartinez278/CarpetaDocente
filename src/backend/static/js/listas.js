// Listas de Sesiones: pestañas, buscador, panel de filtros y «Ver más» (specs repositorio-sesiones y envio-sesiones; design
// de US-011, D10). Se apoya en HTMX (que pide los fragmentos) y es solo mejora: sin él, todo son enlaces y un formulario
// GET normales.
//
// - Pestañas: enlaces dentro de un tablist. Las flechas, Inicio y Fin mueven el foco y activan la otra pestaña. La pestaña
//   actual lleva un bloque oscuro que se desliza con transform (E-07); con el teclado, sin transición (E-06).
// - Buscador: HTMX pide solo #resultados mientras se escribe; el campo no se reemplaza, así que conserva el foco. «Borrar
//   búsqueda» lo vacía y vuelve a pedir la lista.
// - Filtros: hasta 699 px, un <dialog> que abre «Filtrar». Con Esc, «Cerrar filtros» o tocando fuera, se cierra y el foco
//   vuelve a «Filtrar». Desde 700 px es la barra de la izquierda y no se abre nunca.
// - El total de resultados se anuncia en #anuncio cada vez que cambia la lista.
// - «Ver más» agrega las tarjetas siguientes, las junta con su día si ya estaba y mueve el foco a la primera nueva.
// - Tras enviar una sesión (evento «sesion-enviada» de sesiones.js), el panel vuelve a pedir su dirección actual.
(() => {
  const $ = (selector, raiz = document) => raiz.querySelector(selector);

  // --- Pestañas e indicador ---

  // El bloque oscuro de la pestaña actual mide siempre lo mismo (``anchoBase``) y se ajusta con scaleX: así solo se
  // anima transform, no width ni height.
  let anchoBase = 0;
  let ultima = null; // dónde estuvo el indicador, para deslizarlo hacia la pestaña nueva

  function colocarIndicador({ animar }) {
    const lista = $("[data-pestanas]");
    const actual = lista && $('[role="tab"][aria-selected="true"]', lista);
    if (!actual) return;
    const caja = { x: actual.offsetLeft, y: actual.offsetTop, ancho: actual.offsetWidth, alto: actual.offsetHeight };
    if (!anchoBase) anchoBase = caja.ancho;
    const pintar = (c) => {
      lista.style.setProperty("--indicador-base", `${anchoBase}px`);
      lista.style.setProperty("--indicador-alto", `${c.alto}px`);
      lista.style.setProperty("--indicador-x", `${c.x}px`);
      lista.style.setProperty("--indicador-y", `${c.y}px`);
      lista.style.setProperty("--indicador-escala", `${c.ancho / anchoBase}`);
    };
    lista.setAttribute("data-indicador", "");
    const nueva = !lista.style.getPropertyValue("--indicador-escala");
    if (!animar || !ultima) {
      lista.setAttribute("data-quieto", "");
      pintar(caja);
    } else {
      // La nav nueva (fuera de banda) nace sin posición: parte de donde estaba el indicador y se desliza.
      if (nueva) {
        lista.setAttribute("data-quieto", "");
        pintar(ultima);
        lista.getBoundingClientRect();
      }
      if (porTeclado) lista.setAttribute("data-quieto", "");
      else lista.removeAttribute("data-quieto");
      pintar(caja);
    }
    ultima = caja;
  }

  // El cambio vino del teclado: sin transición (E-06) y el foco sigue en la pestaña nueva aunque HTMX reemplace
  // la nav fuera de banda.
  let porTeclado = false;
  let pestanaConFoco = null;

  document.addEventListener("keydown", (evento) => {
    const pestana = evento.target.closest?.('[role="tab"]');
    if (!pestana) return;
    const pestanas = [...pestana.parentElement.querySelectorAll('[role="tab"]')];
    const indice = pestanas.indexOf(pestana);
    let destino = null;
    if (evento.key === "ArrowRight") destino = pestanas[(indice + 1) % pestanas.length];
    else if (evento.key === "ArrowLeft") destino = pestanas[(indice - 1 + pestanas.length) % pestanas.length];
    else if (evento.key === "Home") destino = pestanas[0];
    else if (evento.key === "End") destino = pestanas[pestanas.length - 1];
    if (!destino || destino === pestana) return;
    evento.preventDefault();
    porTeclado = true;
    pestanaConFoco = destino.id;
    destino.focus();
    destino.click();
  });

  // --- Buscador ---

  document.addEventListener("input", (evento) => {
    if (evento.target.id !== "buscar") return;
    const borrar = document.getElementById("borrar-busqueda");
    if (borrar) borrar.hidden = !evento.target.value;
  });

  document.addEventListener("click", (evento) => {
    const borrar = evento.target.closest("#borrar-busqueda");
    if (!borrar) return;
    const campo = document.getElementById("buscar");
    campo.value = "";
    borrar.hidden = true;
    campo.focus();
    campo.form.requestSubmit();
  });

  // --- Panel de filtros ---

  const filtros = () => document.getElementById("filtros");
  const botonFiltrar = () => $("[data-abrir-filtros]");

  document.addEventListener("click", (evento) => {
    const abrir = evento.target.closest("[data-abrir-filtros]");
    if (abrir) {
      const dialogo = filtros();
      if (!dialogo || dialogo.open) return;
      dialogo.showModal();
      abrir.setAttribute("aria-expanded", "true");
      document.getElementById("filtros-titulo").focus();
      return;
    }
    if (evento.target.closest("[data-cerrar-filtros]")) {
      filtros()?.close();
      return;
    }
    // Tocar fuera del panel (en el fondo del modal) lo cierra: el clic llega al <dialog> mismo.
    const dialogo = evento.target;
    if (dialogo.id === "filtros" && dialogo.open) {
      const caja = dialogo.getBoundingClientRect();
      const dentro =
        evento.clientX >= caja.left &&
        evento.clientX <= caja.right &&
        evento.clientY >= caja.top &&
        evento.clientY <= caja.bottom;
      if (!dentro) dialogo.close();
    }
  });

  // close no sube por el DOM: se escucha en la captura. Cubre Esc, «Cerrar filtros» y el fondo.
  document.addEventListener(
    "close",
    (evento) => {
      if (evento.target.id !== "filtros") return;
      const boton = botonFiltrar();
      boton?.setAttribute("aria-expanded", "false");
      boton?.focus();
    },
    true,
  );

  // --- Anuncio del total ---

  // Quitar la búsqueda desde un filtro activo o «Borrar filtros» cambia ``q`` sin pasar por el campo: se iguala a lo que
  // respondió el servidor, salvo que la persona esté escribiendo en él.
  function igualarBuscador() {
    const campo = document.getElementById("buscar");
    const titulo = document.getElementById("resultados-titulo");
    if (!campo || !titulo || document.activeElement === campo) return;
    campo.value = titulo.dataset.q ?? "";
    const borrar = document.getElementById("borrar-busqueda");
    if (borrar) borrar.hidden = !campo.value;
  }

  function anunciarTotal() {
    const titulo = document.getElementById("resultados-titulo");
    const region = document.getElementById("anuncio");
    if (!titulo || !region) return;
    const texto = titulo.textContent.trim();
    region.textContent = "";
    // El mismo total dos veces seguidas se anuncia igual: se vacía y se vuelve a escribir.
    setTimeout(() => {
      region.textContent = texto;
    }, 50);
  }

  // --- «Ver más» ---

  let tarjetasAntes = 0;

  document.addEventListener("htmx:beforeRequest", (evento) => {
    if (evento.detail.elt.matches?.("[data-ver-mas]")) {
      tarjetasAntes = document.querySelectorAll(".sesion-tarjeta").length;
    }
  });

  function juntarDias() {
    let previa = null;
    for (const seccion of document.querySelectorAll(".sesiones-dia")) {
      if (previa && previa.dataset.dia === seccion.dataset.dia) {
        $(".sesiones-lista", previa).append(...$(".sesiones-lista", seccion).children);
        seccion.remove();
      } else {
        previa = seccion;
      }
    }
  }

  document.addEventListener("htmx:afterSwap", (evento) => {
    const origen = evento.detail.requestConfig?.elt;
    if (origen?.matches?.("[data-ver-mas]")) {
      juntarDias();
      document.querySelectorAll(".sesion-tarjeta > a")[tarjetasAntes]?.focus();
      return;
    }
    const destino = evento.detail.target?.id;
    if (destino === "resultados") igualarBuscador();
    if (destino === "resultados" || destino === "panel-sesiones") anunciarTotal();
  });

  document.addEventListener("htmx:afterSettle", () => {
    colocarIndicador({ animar: true });
    // Con otra petición en vuelo (dos flechas seguidas), el foco se reafirma y la marca espera a la última.
    if (!porTeclado) return;
    document.getElementById(pestanaConFoco)?.focus();
    if (!document.querySelector(".htmx-request")) porTeclado = false;
  });

  // --- Tras enviar una sesión ---

  document.addEventListener("sesion-enviada", () => {
    if (!window.htmx || !document.getElementById("panel-sesiones")) return;
    const consulta = new URLSearchParams(location.search);
    consulta.delete("pagina");
    const texto = consulta.toString();
    window.htmx.ajax("GET", location.pathname + (texto ? `?${texto}` : ""), {
      target: "#panel-sesiones",
      swap: "innerHTML",
    });
  });
  // --- Arranque ---

  function iniciar() {
    colocarIndicador({ animar: false });
    // Con la fuente cargada cambia el ancho de las pestañas: se coloca de nuevo, sin transición.
    document.fonts?.ready.then(() => colocarIndicador({ animar: false }));
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", iniciar);
  else iniciar();

  window.addEventListener("resize", () => colocarIndicador({ animar: false }));
})();
