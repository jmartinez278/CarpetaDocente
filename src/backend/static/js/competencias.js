// Competencias del periodo (US-029, design D9). Sin HTMX ni Alpine: el servidor dibuja la lista una vez, con el estado del
// periodo que abre, y pasa por json_script (#datos-competencias) el de cada periodo; este archivo agrega el marcado.
//
// - Borradores: cada periodo guarda lo último guardado (null si nunca se guardó) y su borrador, en memoria. Cambiar de
//   periodo o de área no interrumpe ni pierde nada. "Base" es lo guardado (o todo marcado, si no hay marcas) más lo que
//   no se puede desmarcar: las obligatorias del último periodo y las que tienen notas. Un cambio es lo que difiere de la base.
// - Bloqueos: la casilla sigue marcada, con aria-disabled y no disabled, así recibe el foco y, al intentar cambiarla (clic o
//   Espacio), anuncia su motivo en la región role="alert". Las obligatorias se calculan aquí con lo guardado en los periodos
//   anteriores, igual que el servidor; el servidor las agrega siempre.
// - Guardar: un POST por periodo con todas las competencias marcadas de todas las áreas. 204 guardado; 400, 404 y 409, el
//   mensaje junto a "Guardar" y el borrador intacto (con 409 y "competencias", esas quedan marcadas y bloqueadas); HX-Redirect,
//   la sesión venció; red caída u otro código, "No se pudo guardar". Un guardado posterior quita el aviso.
// - Celular (bajo 960 px): un área a la vez con la cápsula de flechas, posición y selector. Las marcas de todas las áreas
//   quedan en el borrador, así que guardar desde otra área guarda el conjunto completo.
// - Salida: con cambios sin guardar en algún periodo, los enlaces y formularios que salen de la pantalla abren el diálogo
//   "¿Salir sin guardar?"; recargar o cerrar la pestaña muestra el aviso del navegador (beforeunload).
(() => {
  const raiz = document.querySelector("[data-trabajo]");
  const elementoDatos = document.getElementById("datos-competencias");
  if (!raiz || !elementoDatos) return;
  const datos = JSON.parse(elementoDatos.textContent);

  const MENSAJE_NOTAS = "La competencia tiene notas registradas en este periodo";
  const MENSAJE_ANUAL = "Debe tener nivel al cerrar el año";
  const MENSAJE_FALLO = "Tus cambios siguen aquí. Reintenta.";
  const ESTADOS = { VIGENTE: "Vigente", ANTERIOR: "Anterior", FUTURO: "Futuro" };

  const $ = (selector) => document.querySelector(selector);
  const principal = raiz.closest("main");
  const lista = $("#lista-areas");
  const areas = [...lista.querySelectorAll(".comp-area")];
  const casillas = [...lista.querySelectorAll("input[data-competencia]")];
  const selectorArea = $("#area-elegida");
  const anterior = $("[data-area-anterior]");
  const siguiente = $("[data-area-siguiente]");
  const posicion = $("[data-posicion-area]");
  const botonGuardar = $("#guardar");
  const botonDeshacer = $("#deshacer");
  const dialogo = $("#confirmar-salida");
  const anuncio = $("[data-anuncio]");
  const alerta = $("[data-alerta]");
  const botones = [...document.querySelectorAll("[data-periodo]")];
  const movil = window.matchMedia("(max-width: 959px)");

  const ids = casillas.filter((c) => !c.disabled).map((c) => c.value);
  const periodos = new Map(
    datos.periodos.map((p) => [
      p.numero,
      {
        ...p,
        guardado: p.marcadas === null ? null : new Set(p.marcadas.map(String)),
        conNotas: new Set(p.con_notas.map(String)),
      },
    ]),
  );
  const ultimo = Math.max(...periodos.keys());
  const palabra = datos.periodos[0].nombre_largo.split(" ")[0].toLowerCase();
  const avisoDelServidor = principal.querySelector("[data-aviso]");

  const borradores = new Map();
  let actual = datos.inicial;
  let areaActual = Math.max(
    0,
    areas.findIndex((a) => a.dataset.area === datos.area_inicial),
  );
  let enviando = false;
  let exito = null; // Número del periodo recién guardado.
  let fallo = null; // { periodo, titulo, ayuda, enlace }
  let temporizadorAnuncio;
  let salidaPendiente = null;
  let permitirSalida = false;

  // --- Reglas del cliente (las mismas del servidor, D5 y D7) ---

  function obligatorias(numero) {
    const periodo = periodos.get(numero);
    if (!periodo.editable || numero !== ultimo) return new Set();
    const antes = new Set();
    for (const otro of periodos.values()) {
      if (otro.numero < numero && otro.guardado) otro.guardado.forEach((id) => antes.add(id));
    }
    return new Set(ids.filter((id) => !antes.has(id)));
  }

  function motivos(numero, id) {
    const resultado = [];
    if (periodos.get(numero).conNotas.has(id)) resultado.push({ icono: "nota", texto: MENSAJE_NOTAS, clase: "notas" });
    if (obligatorias(numero).has(id)) resultado.push({ icono: "aviso", texto: MENSAJE_ANUAL, clase: "anual" });
    return resultado;
  }

  function base(numero) {
    const periodo = periodos.get(numero);
    const conjunto = new Set(periodo.guardado ?? ids);
    obligatorias(numero).forEach((id) => conjunto.add(id));
    periodo.conNotas.forEach((id) => conjunto.add(id));
    return conjunto;
  }

  function borrador(numero) {
    if (!borradores.has(numero)) borradores.set(numero, new Set(base(numero)));
    const seleccion = borradores.get(numero);
    obligatorias(numero).forEach((id) => seleccion.add(id));
    periodos.get(numero).conNotas.forEach((id) => seleccion.add(id));
    return seleccion;
  }

  function cambios(numero) {
    if (!periodos.get(numero).editable) return 0;
    const seleccion = borrador(numero);
    const referencia = base(numero);
    return ids.filter((id) => seleccion.has(id) !== referencia.has(id)).length;
  }

  function pendiente(numero) {
    return periodos.get(numero).guardado === null || cambios(numero) > 0;
  }

  function periodosConCambios() {
    return [...borradores.keys()].filter((numero) => cambios(numero) > 0).sort((a, b) => a - b);
  }

  // --- Avisos para el lector de pantalla ---

  function anunciar(texto, esAlerta = false) {
    const region = esAlerta ? alerta : anuncio;
    region.textContent = "";
    clearTimeout(temporizadorAnuncio);
    temporizadorAnuncio = setTimeout(() => {
      region.textContent = texto;
    }, 35);
  }

  function icono(nombre) {
    const molde = document.querySelector("template[data-iconos]").content.querySelector(`[data-icono="${nombre}"] svg`);
    return molde.cloneNode(true);
  }

  // --- Pantalla ---

  function pintarBotones() {
    for (const boton of botones) {
      const numero = Number(boton.dataset.periodo);
      const periodo = periodos.get(numero);
      boton.setAttribute("aria-pressed", String(numero === actual));
      boton.disabled = enviando || !periodo.editable;
      const textoEstado = boton.querySelector("[data-estado-periodo]");
      textoEstado.textContent = cambios(numero) > 0 ? "Sin guardar" : ESTADOS[periodo.estado];
    }
    if (actual !== null) $("[data-fecha-periodo]").textContent = periodos.get(actual).fechas;
  }

  function pintarNota() {
    const nota = $("[data-nota-periodo]");
    nota.hidden = true;
    if (avisoDelServidor || actual === null) return;
    const periodo = periodos.get(actual);
    let titulo = "";
    let texto = "";
    if (periodo.estado === "ANTERIOR") {
      titulo = `Estás revisando un ${palabra} anterior`;
      texto = "Puedes corregirlo mientras el año esté abierto.";
    } else if (actual === ultimo) {
      titulo = `Último ${palabra} del año`;
      texto = "Las competencias que no se trabajaron antes deben tener nivel al cerrar el año. Se incluyen al guardar.";
    } else {
      return;
    }
    const contenedor = document.createElement("div");
    contenedor.className = "mensaje__texto";
    for (const [indice, contenido] of [titulo, texto].entries()) {
      const parrafo = document.createElement("p");
      parrafo.textContent = contenido;
      if (indice === 0) parrafo.className = "comp-nota__titulo";
      contenedor.append(parrafo);
    }
    nota.replaceChildren(icono("nota"), contenedor);
    nota.hidden = false;
  }

  function pintarMotivos(fila, lista_) {
    const contenedor = fila.querySelector("[data-motivos]");
    contenedor.replaceChildren(
      ...lista_.map((m) => {
        const motivo = document.createElement("span");
        motivo.className = "comp-motivo";
        const texto = document.createElement("span");
        texto.textContent = m.texto;
        const svg = icono(m.icono);
        svg.classList.add("comp-motivo__icono");
        motivo.append(svg, texto);
        return motivo;
      }),
    );
  }

  // Cambia el estado de cada casilla sin reemplazarla: el foco se queda donde está.
  function pintarAreas() {
    const seleccion = borrador(actual);
    for (const casilla of casillas) {
      if (casilla.disabled) continue;
      const id = casilla.value;
      const razones = motivos(actual, id);
      const fila = casilla.closest(".comp-competencia");
      casilla.checked = seleccion.has(id);
      if (razones.length) casilla.setAttribute("aria-disabled", "true");
      else casilla.removeAttribute("aria-disabled");
      fila.classList.toggle("comp-competencia--notas", razones.some((m) => m.clase === "notas"));
      fila.classList.toggle(
        "comp-competencia--anual",
        razones.some((m) => m.clase === "anual") && !razones.some((m) => m.clase === "notas"),
      );
      pintarMotivos(fila, razones);
    }
    pintarContadores();
  }

  function pintarContadores() {
    const seleccion = borrador(actual);
    for (const area of areas) {
      const cuenta = area.querySelector("[data-cuenta]");
      if (!cuenta) continue;
      const delArea = [...area.querySelectorAll("input[data-competencia]")];
      const marcadas = delArea.filter((c) => seleccion.has(c.value)).length;
      cuenta.textContent = `${marcadas}/${delArea.length}`;
      cuenta.setAttribute("aria-label", `${marcadas} de ${delArea.length} seleccionadas`);
    }
  }

  function pintarResumen() {
    if (actual === null) return;
    const periodo = periodos.get(actual);
    const seleccion = borrador(actual);
    const n = cambios(actual);
    const hayPendientes = pendiente(actual);
    const huboExito = exito === actual && !hayPendientes;
    const huboFallo = fallo !== null && fallo.periodo === actual;
    const nombre = periodo.nombre;

    $("[data-conteo]").textContent = `${seleccion.size} de ${datos.total} seleccionadas`;
    $("[data-conteo-periodo]").textContent = `competencias para ${nombre}`;
    const resumen = $("[data-resumen-bloqueos]");
    resumen.replaceChildren(
      ...[
        ["Con notas registradas", periodo.conNotas.size],
        ["Por cierre de año", obligatorias(actual).size],
      ]
        .filter(([, cantidad]) => cantidad > 0)
        .map(([etiqueta, cantidad]) => {
          const fila = document.createElement("div");
          const dt = document.createElement("dt");
          const dd = document.createElement("dd");
          dt.textContent = etiqueta;
          dd.textContent = String(cantidad);
          fila.append(dt, dd);
          return fila;
        }),
    );

    let texto;
    if (enviando) texto = "Guardando…";
    else if (huboFallo) texto = fallo.titulo;
    else if (huboExito) texto = `Guardado · ${nombre}`;
    else if (!hayPendientes) texto = "Sin cambios";
    else if (n > 0) texto = `${n} ${n === 1 ? "cambio" : "cambios"} sin guardar`;
    else texto = "Sin guardar";
    $("[data-texto-guardado]").textContent = texto;
    $("[data-icono-estado]").replaceChildren(icono(huboFallo ? "aviso" : huboExito || !hayPendientes ? "check" : "reloj"));

    const ayuda = $("[data-ayuda-guardado]");
    if (huboFallo && fallo.enlace) {
      const enlace = document.createElement("a");
      enlace.href = fallo.enlace;
      enlace.target = "_blank";
      enlace.rel = "noopener";
      enlace.textContent = "Volver a ingresar";
      ayuda.replaceChildren(`${fallo.ayuda} `, enlace);
    } else if (enviando) {
      ayuda.textContent = "Espera un momento.";
    } else if (huboFallo) {
      ayuda.textContent = fallo.ayuda;
    } else if (huboExito) {
      ayuda.textContent = `${seleccion.size} competencias seleccionadas.`;
    } else if (movil.matches) {
      ayuda.textContent = `${nombre} · ${seleccion.size} de ${datos.total} en total`;
    } else if (!hayPendientes) {
      ayuda.textContent = `${nombre} · ${seleccion.size} seleccionadas`;
    } else if (periodo.guardado !== null || seleccion.size !== datos.total) {
      ayuda.textContent = `${nombre} · ${seleccion.size} de ${datos.total} seleccionadas`;
    } else {
      ayuda.textContent = `${nombre} · Todo marcado para empezar.`;
    }

    const grupo = $("[data-guardado]");
    grupo.classList.toggle("comp-guardado--exito", huboExito);
    grupo.classList.toggle("comp-guardado--fallo", huboFallo);
    botonGuardar.textContent = enviando ? "Guardando…" : "Guardar";
    botonGuardar.setAttribute("aria-disabled", String(enviando || !hayPendientes));
    botonGuardar.classList.toggle("boton-principal--enviando", enviando);
    botonDeshacer.hidden = enviando || n === 0;
    pintarContadores();
    pintarNavegacion();
  }

  // El enlace «Registrar notas de B*n*» lleva el periodo visible y el área abierta a la hoja (D15).
  function pintarEnlaceNotas() {
    const enlace = $("[data-registrar-notas]");
    if (!enlace) return;
    enlace.hidden = actual === null;
    if (actual === null) return;
    enlace.querySelector("[data-nombre-periodo]").textContent = periodos.get(actual).nombre;
    // La ruta la pone el servidor en el href; aquí solo cambia la consulta, así el enlace no puede tomar otro esquema.
    enlace.search = new URLSearchParams({ periodo: String(actual), area: areas[areaActual].dataset.area }).toString();
  }

  function pintarNavegacion() {
    const area = areas[areaActual];
    pintarEnlaceNotas();
    selectorArea.value = area.dataset.area;
    selectorArea.disabled = enviando;
    posicion.textContent = `${areaActual + 1} de ${areas.length}`;
    anterior.disabled = enviando || areaActual === 0;
    siguiente.disabled = enviando || areaActual === areas.length - 1;
    for (const otra of areas) otra.hidden = movil.matches && otra !== area;
    // Un botón de un extremo se deshabilita y pierde el foco: pasa al selector.
    const foco = document.activeElement;
    if (movil.matches && foco instanceof HTMLButtonElement && foco.disabled && foco.closest(".comp-capsula")) {
      selectorArea.focus({ preventScroll: true });
    }
  }

  function pintar() {
    const hay = actual !== null;
    raiz.hidden = !hay;
    const vacio = $("[data-vacio]");
    if (vacio) vacio.hidden = hay;
    const instruccion = $("[data-instruccion]");
    if (instruccion) instruccion.hidden = !hay;
    pintarBotones();
    pintarNota();
    pintarEnlaceNotas();
    if (hay) {
      pintarAreas();
      pintarResumen();
    }
  }

  // --- Cápsula de áreas ---

  function cambiarArea(indice) {
    if (actual === null || enviando || indice < 0 || indice >= areas.length || indice === areaActual) return;
    areaActual = indice;
    pintarNavegacion();
    const area = areas[areaActual];
    const seleccion = borrador(actual);
    const delArea = [...area.querySelectorAll("input[data-competencia]")];
    const aCargo = area.classList.contains("comp-area--curso");
    const marcadas = delArea.filter((c) => seleccion.has(c.value)).length;
    anunciar(
      `Área ${areaActual + 1} de ${areas.length}. ${area.querySelector("h3").textContent}. ${
        aCargo ? "A cargo del docente de curso." : `${marcadas} de ${delArea.length} seleccionadas.`
      }`,
    );
    if (movil.matches) $(".comp-navegacion").scrollIntoView({ block: "start", behavior: "instant" });
  }

  anterior.addEventListener("click", () => cambiarArea(areaActual - 1));
  siguiente.addEventListener("click", () => cambiarArea(areaActual + 1));
  selectorArea.addEventListener("change", () => {
    cambiarArea(areas.findIndex((a) => a.dataset.area === selectorArea.value));
  });
  movil.addEventListener("change", () => {
    pintarNavegacion();
    if (actual !== null) pintarResumen();
  });

  // --- Periodos ---

  for (const boton of botones) {
    boton.addEventListener("click", () => {
      const numero = Number(boton.dataset.periodo);
      if (boton.disabled || enviando || numero === actual) return;
      const anteriorConCambios = actual !== null && cambios(actual) > 0 ? actual : null;
      actual = numero;
      exito = null;
      pintar();
      boton.focus({ preventScroll: true });
      const periodo = periodos.get(numero);
      anunciar(
        `${periodo.nombre}. ${borrador(numero).size} competencias seleccionadas.${
          anteriorConCambios === null
            ? ""
            : ` El borrador de ${periodos.get(anteriorConCambios).nombre} sigue sin guardar; se conserva mientras esta pantalla esté abierta.`
        }`,
      );
    });
  }

  // --- Casillas ---

  lista.addEventListener("click", (evento) => {
    const casilla = evento.target.closest("input[data-competencia]");
    if (!casilla || casilla.disabled) return;
    const bloqueada = casilla.getAttribute("aria-disabled") === "true";
    if (!enviando && !bloqueada) return;
    evento.preventDefault();
    if (enviando) return;
    anunciar(motivos(actual, casilla.value)[0]?.texto ?? MENSAJE_ANUAL, true);
  });

  lista.addEventListener("change", (evento) => {
    const casilla = evento.target.closest("input[data-competencia]");
    if (!casilla || casilla.disabled || enviando) return;
    if (casilla.getAttribute("aria-disabled") === "true") {
      casilla.checked = true;
      return;
    }
    const seleccion = borrador(actual);
    if (casilla.checked) seleccion.add(casilla.value);
    else seleccion.delete(casilla.value);
    exito = null;
    pintarResumen();
    pintarBotones();
  });

  botonDeshacer.addEventListener("click", () => {
    if (enviando || actual === null) return;
    borradores.set(actual, new Set(base(actual)));
    exito = null;
    pintarAreas();
    pintarResumen();
    pintarBotones();
    botonGuardar.focus({ preventScroll: true });
    anunciar(`Cambios deshechos en ${periodos.get(actual).nombre}.`);
  });

  // --- Guardar ---

  function csrf() {
    const cookie = document.cookie.split("; ").find((c) => c.startsWith("csrftoken="));
    if (cookie) return decodeURIComponent(cookie.slice("csrftoken=".length));
    return document.querySelector("input[name=csrfmiddlewaretoken]")?.value ?? "";
  }

  async function pedir(url, cuerpo) {
    try {
      return await fetch(url, {
        method: "POST",
        credentials: "same-origin",
        headers: { "X-CSRFToken": csrf(), "HX-Request": "true" },
        body: cuerpo,
      });
    } catch {
      return null; // Red caída.
    }
  }

  async function leerJson(respuesta) {
    try {
      return await respuesta.json();
    } catch {
      return {};
    }
  }

  function fallar(numero, ayuda, extra = {}) {
    fallo = { periodo: numero, titulo: "No se pudo guardar", ayuda, ...extra };
    anunciar(`${fallo.titulo}. ${ayuda}`, true);
  }

  async function guardar() {
    if (actual === null || enviando || !pendiente(actual)) return;
    const numero = actual;
    const seleccion = borrador(numero);
    enviando = true;
    fallo = null;
    exito = null;
    principal.setAttribute("aria-busy", "true");
    pintarBotones();
    pintarResumen();
    anunciar("Guardando las competencias.");

    const cuerpo = new URLSearchParams();
    ids
      .filter((id) => seleccion.has(id))
      .sort((a, b) => Number(a) - Number(b))
      .forEach((id) => cuerpo.append("competencia", id));
    // El universo que se mostró: si cambió en el servidor, no guarda y pide recargar (D5).
    datos.universo.forEach((id) => cuerpo.append("universo", id));
    const respuesta = await pedir(datos.url_guardar.replace(/\/0\/$/, `/${numero}/`), cuerpo);
    const redireccion = respuesta?.headers.get("HX-Redirect");

    if (redireccion) {
      fallo = {
        periodo: numero,
        titulo: "Tu sesión venció",
        ayuda: "Vuelve a ingresar para guardar. Tus cambios siguen aquí.",
        enlace: redireccion,
      };
      anunciar(`${fallo.titulo}. ${fallo.ayuda}`, true);
    } else if (respuesta?.status === 204) {
      periodos.get(numero).guardado = new Set(ids.filter((id) => seleccion.has(id)));
      exito = numero;
      anunciar(`Competencias guardadas en ${periodos.get(numero).nombre}. ${seleccion.size} competencias seleccionadas.`);
    } else if (respuesta && [400, 409].includes(respuesta.status)) {
      const cuerpoJson = await leerJson(respuesta);
      for (const id of cuerpoJson.competencias ?? []) {
        periodos.get(numero).conNotas.add(String(id));
        seleccion.add(String(id));
      }
      fallar(numero, cuerpoJson.mensaje ?? MENSAJE_FALLO);
    } else {
      fallar(numero, MENSAJE_FALLO);
    }

    enviando = false;
    principal.removeAttribute("aria-busy");
    pintar();
  }

  botonGuardar.addEventListener("click", () => {
    if (botonGuardar.getAttribute("aria-disabled") === "true") return;
    void guardar();
  });

  // --- Salir sin guardar ---

  function listaDePeriodos(numeros) {
    const nombres = numeros.map((n) => periodos.get(n).nombre);
    return nombres.length < 2 ? nombres[0] : `${nombres.slice(0, -1).join(", ")} y ${nombres.at(-1)}`;
  }

  function pedirSalida(continuar) {
    const pendientes = periodosConCambios();
    if (!pendientes.length) {
      continuar();
      return;
    }
    $("#texto-salida").textContent = `Tienes cambios pendientes en ${listaDePeriodos(pendientes)}. Si sales, se perderán.`;
    salidaPendiente = { continuar, foco: document.activeElement };
    if (!dialogo.open) dialogo.showModal();
  }

  $("#seguir-editando").addEventListener("click", () => dialogo.close("seguir"));
  $("#salir-sin-guardar").addEventListener("click", () => dialogo.close("salir"));
  dialogo.addEventListener("cancel", () => {
    dialogo.returnValue = "seguir";
  });
  dialogo.addEventListener("keydown", (evento) => {
    if (evento.key !== "Tab") return;
    const primero = $("#seguir-editando");
    const final = $("#salir-sin-guardar");
    if (evento.shiftKey && document.activeElement === primero) {
      evento.preventDefault();
      final.focus();
    } else if (!evento.shiftKey && document.activeElement === final) {
      evento.preventDefault();
      primero.focus();
    }
  });
  dialogo.addEventListener("close", () => {
    const salida = salidaPendiente;
    salidaPendiente = null;
    if (!salida) return;
    if (dialogo.returnValue === "salir") {
      permitirSalida = true;
      salida.continuar();
    } else if (salida.foco?.isConnected) {
      salida.foco.focus({ preventScroll: true });
    }
  });

  document.addEventListener(
    "click",
    (evento) => {
      const enlace = evento.target.closest("a[href]");
      if (
        !enlace ||
        evento.defaultPrevented ||
        evento.button !== 0 ||
        evento.ctrlKey ||
        evento.metaKey ||
        evento.shiftKey ||
        evento.altKey ||
        enlace.hasAttribute("download") ||
        enlace.target === "_blank"
      ) {
        return;
      }
      const destino = new URL(enlace.href, window.location.href);
      if (destino.origin === window.location.origin && destino.pathname === window.location.pathname && destino.hash) return;
      if (!periodosConCambios().length) return;
      evento.preventDefault();
      pedirSalida(() => window.location.assign(destino.href));
    },
    true,
  );

  // El formulario de "Cerrar sesión" también sale de la pantalla. Al confirmar, NotasBorrador.enviar borra los borradores de
  // notas de la cuenta (design de US-020, D10), que menu.js no ve porque submit() no dispara el evento.
  document.addEventListener(
    "submit",
    (evento) => {
      const formulario = evento.target;
      if (evento.defaultPrevented || !(formulario instanceof HTMLFormElement) || !periodosConCambios().length) return;
      evento.preventDefault();
      pedirSalida(() => (window.NotasBorrador ? window.NotasBorrador.enviar(formulario) : formulario.submit()));
    },
    true,
  );

  window.addEventListener("beforeunload", (evento) => {
    if (!permitirSalida && periodosConCambios().length) {
      evento.preventDefault();
      evento.returnValue = "";
    }
  });

  pintar();
})();
