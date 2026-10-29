// Asistencia de hoy (US-030, design D3, D4, D7 y D8). Sin HTMX ni Alpine: el servidor dibuja la pantalla completa y este
// archivo agrega el toque y el guardado.
//
// - Toque: el círculo es un <button> (Intro y espacio ya lo activan). Calcula el siguiente estado del ciclo, lo pinta al
//   instante y lo guarda: se envía el estado de destino, no "avanzar uno", así repetir la petición deja lo mismo (D3).
// - Una petición por fila, sin abortar: cada fila guarda lo que se ve (deseado) y lo último que el servidor guardó. Si hay
//   una petición en curso, el toque solo cambia lo deseado; al terminar la petición se envía lo deseado si cambió. Nunca
//   hay dos de la misma fila en la red y gana el último toque.
// - Respuestas: 204 guardado; 200 con HX-Redirect, sesión vencida (va a esa dirección); 400, 404 y 409, la página se
//   recarga para mostrar lo que hay en la base; red caída u otro código, la fila queda sin guardar.
// - Franja: "Guardando…" mientras falte guardar algo y "✓ Guardado" al terminar. Avance, totales y "Marcar los N
//   restantes" se recalculan con cada toque. "N sin marcar" lleva el foco al círculo de la primera fila Sin marcar.
// - Nota (D7): visible solo en Justificado; se guarda con su estado al salir del campo y tras 800 ms sin escribir.
(() => {
  const raiz = document.querySelector("[data-asistencia]");
  if (!raiz) return;

  const CICLO = { "": "ASISTIO", ASISTIO: "FALTO", FALTO: "TARDE", TARDE: "JUSTIFICADO", JUSTIFICADO: "ASISTIO" };
  const PALABRAS = { "": "Sin marcar", ASISTIO: "Asistió", FALTO: "Faltó", TARDE: "Tarde", JUSTIFICADO: "Justificado" };
  const ORDEN_TOTALES = ["ASISTIO", "TARDE", "FALTO", "JUSTIFICADO"];
  const ESPERA_NOTA = 800;
  const RECARGAR = new Set([400, 404, 409]);

  const urlMarcar = raiz.dataset.urlMarcar;
  // Los círculos de la leyenda del panel sirven de molde para el círculo de cada estado.
  const moldes = {};
  for (const circulo of raiz.querySelectorAll(".panel-jornada .leyenda .estado")) {
    const estado = [...circulo.classList].find((c) => c.startsWith("estado--")).slice(8).toUpperCase();
    moldes[estado] = circulo;
  }
  const iconoGuardado = raiz.querySelector("[data-cierre] .icono");
  let huboGuardado = false;

  const filas = [...raiz.querySelectorAll("[data-estudiante]")].map((li) => {
    const campo = li.querySelector("[data-nota-campo]");
    const actual = { estado: li.dataset.estado, nota: campo.value };
    return {
      li,
      id: li.dataset.estudiante,
      nombre: li.querySelector(".estudiante__nombre").textContent,
      boton: li.querySelector("[data-marcar]"),
      etiqueta: li.querySelector("[data-etiqueta]"),
      caja: li.querySelector("[data-nota]"),
      campo,
      contador: li.querySelector("[data-contador]"),
      deseado: { ...actual },
      guardado: { ...actual },
      enCurso: false,
      fallida: false,
      espera: null,
    };
  });
  const porBoton = new Map(filas.map((fila) => [fila.boton, fila]));
  const porCampo = new Map(filas.map((fila) => [fila.campo, fila]));

  function csrf() {
    const cookie = document.cookie.split("; ").find((c) => c.startsWith("csrftoken="));
    if (cookie) return decodeURIComponent(cookie.slice("csrftoken=".length));
    return document.querySelector("input[name=csrfmiddlewaretoken]")?.value ?? "";
  }

  function iguales(a, b) {
    return a.estado === b.estado && a.nota === b.nota;
  }

  function pendiente(fila) {
    return !iguales(fila.deseado, fila.guardado);
  }

  // --- Pantalla ---

  function pintar(fila) {
    const estado = fila.deseado.estado;
    fila.li.dataset.estado = estado;
    fila.etiqueta.textContent = PALABRAS[estado];
    fila.boton.setAttribute("aria-label", `${fila.nombre}: ${PALABRAS[estado]}. Cambiar a ${PALABRAS[CICLO[estado]]}`);
    fila.boton.replaceChildren(moldes[estado].cloneNode(true));
    const justificado = estado === "JUSTIFICADO";
    fila.caja.hidden = !justificado;
    if (!justificado) {
      fila.campo.value = "";
      fila.contador.textContent = "0";
    }
  }

  function textoRestantes(n) {
    if (n === 0) return "";
    return n === 1 ? "Marcar el restante como Asistió" : `Marcar los ${n} restantes como Asistió`;
  }

  function contar() {
    const totales = Object.fromEntries(ORDEN_TOTALES.map((estado) => [estado, 0]));
    let primeraSinMarcar = null;
    for (const fila of filas) {
      const estado = fila.deseado.estado;
      if (estado) totales[estado] += 1;
      else primeraSinMarcar ??= fila;
    }
    const marcados = ORDEN_TOTALES.reduce((suma, estado) => suma + totales[estado], 0);
    const sinMarcar = filas.length - marcados;

    for (const el of raiz.querySelectorAll("[data-marcados]")) el.textContent = marcados;
    for (const el of raiz.querySelectorAll("[data-total]")) el.textContent = totales[el.dataset.total];
    for (const el of raiz.querySelectorAll("[data-progreso]")) el.value = marcados;
    for (const el of raiz.querySelectorAll("[data-sin-marcar]")) {
      el.textContent = `${sinMarcar} sin marcar`;
      el.hidden = sinMarcar === 0;
      if (primeraSinMarcar) el.href = `#${primeraSinMarcar.li.id}`;
    }
    for (const el of raiz.querySelectorAll("[data-marcar-todos]")) {
      el.textContent = textoRestantes(sinMarcar);
      el.hidden = sinMarcar === 0;
    }
    // Con todos marcados, el avance da paso a los totales del día ("Asistió: 21 · Tarde: 1 · …").
    const resumen = ORDEN_TOTALES.map((estado) => `${PALABRAS[estado]}: ${totales[estado]}`).join(" · ");
    for (const el of raiz.querySelectorAll("[data-resumen-completo]")) {
      el.textContent = resumen;
      el.hidden = sinMarcar > 0;
    }
    for (const el of raiz.querySelectorAll("[data-avance]")) el.hidden = sinMarcar === 0;
  }

  function mostrarGuardado() {
    const guardando = filas.some((fila) => pendiente(fila) && !fila.fallida);
    for (const el of raiz.querySelectorAll("[data-guardado]")) {
      if (guardando) {
        el.className = "guardado guardado--inicial";
        el.textContent = "Guardando…";
      } else if (huboGuardado) {
        el.className = "guardado";
        el.replaceChildren(iconoGuardado.cloneNode(true), "Guardado");
      }
    }
  }

  // --- Guardado por fila (D3) ---

  function encolar(fila) {
    if (fila.enCurso || !pendiente(fila)) return;
    enviar(fila);
  }

  async function enviar(fila) {
    const envio = { ...fila.deseado };
    fila.enCurso = true;
    mostrarGuardado();
    let respuesta = null;
    try {
      respuesta = await fetch(urlMarcar.replace(/\/0\/$/, `/${fila.id}/`), {
        method: "POST",
        credentials: "same-origin",
        headers: { "X-CSRFToken": csrf(), "HX-Request": "true" },
        body: new URLSearchParams({ estado: envio.estado, nota: envio.nota }),
      });
    } catch {
      // Red caída: la fila queda sin guardar.
    }
    fila.enCurso = false;

    const redireccion = respuesta?.headers.get("HX-Redirect");
    if (redireccion) {
      window.location.assign(redireccion);
      return;
    }
    if (respuesta && RECARGAR.has(respuesta.status)) {
      window.location.reload();
      return;
    }
    if (respuesta?.status === 204) {
      fila.guardado = envio;
      fila.fallida = false;
      huboGuardado = true;
      encolar(fila);
    } else {
      fila.fallida = true;
    }
    mostrarGuardado();
  }

  // --- Eventos ---

  raiz.addEventListener("click", (evento) => {
    // "N sin marcar": lleva a la primera fila Sin marcar, centrada bajo la franja fija y con el foco en su círculo.
    if (evento.target.closest("[data-sin-marcar]")) {
      const destino = filas.find((f) => !f.deseado.estado);
      if (!destino) return;
      evento.preventDefault();
      destino.li.scrollIntoView({ block: "center" });
      destino.boton.focus({ preventScroll: true });
      return;
    }
    const fila = porBoton.get(evento.target.closest("[data-marcar]"));
    if (!fila) return;
    const estado = CICLO[fila.deseado.estado];
    fila.deseado = { estado, nota: estado === "JUSTIFICADO" ? fila.campo.value : "" };
    pintar(fila);
    contar();
    encolar(fila);
  });

  raiz.addEventListener("input", (evento) => {
    const fila = porCampo.get(evento.target);
    if (!fila) return;
    fila.contador.textContent = fila.campo.value.length;
    fila.deseado = { ...fila.deseado, nota: fila.campo.value };
    clearTimeout(fila.espera);
    fila.espera = setTimeout(() => encolar(fila), ESPERA_NOTA);
  });

  raiz.addEventListener("change", (evento) => {
    const fila = porCampo.get(evento.target);
    if (!fila) return;
    clearTimeout(fila.espera);
    encolar(fila);
  });
})();
