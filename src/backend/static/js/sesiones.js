// Sesiones: popup «Subir una sesión», términos (4a) y envío (spec envio-sesiones; design de US-010, US-014 y EN-03, D5,
// D7 y D8). Sin Alpine ni HTMX, con defer.
//
// - Cada apertura es un formulario nuevo con su id (crypto.randomUUID, D5); «Reintentar envío» manda el mismo.
// - El navegador revisa tipo y tamaño al elegir el archivo, solo como ayuda: el servidor lo revisa otra vez (D6).
// - Con la casilla marcada, «Enviar a la dirección» abre los términos encima; solo «Acepto y envío» envía.
// - Envío con XMLHttpRequest (fetch no informa el avance de la subida): 2xx pinta el fragmento del éxito, 400 pinta los
//   errores por campo, HX-Redirect navega y lo demás (red, 413, 5xx) es «Se cortó la conexión» (D7).
// - Historial (D8): cada popup abierto agrega una entrada; «atrás» (popstate) cierra el de arriba; cerrar con un botón o
//   Esc consume su entrada con history.back() e ignora ese popstate. En Chrome de Android «atrás» llega como cancel del
//   diálogo de arriba: se trata como Esc. Mientras sube, nada cierra el popup y salir de la página pide confirmar.
(() => {
  const subir = document.getElementById("subir");
  const terminos = document.getElementById("terminos");
  if (!subir || !terminos) return;

  const TAMANO_MAXIMO = 4 * 1024 * 1024;
  const MENSAJES = {
    faltaArchivo: "Elige un archivo PDF o Word (.docx).",
    tipo: "Este archivo no es PDF ni Word (.docx). Elige otro archivo.",
    grande: "El archivo supera los 4 MB. Elige uno más pequeño.",
    ilegible: "No pudimos leer el archivo. Vuelve a elegirlo.",
    grado: "Falta indicar el grado.",
    area: "Falta indicar el área.",
    titulo: "Falta indicar el título.",
  };
  // Orden de los campos en el formulario: el foco va al primero con error.
  const CAMPOS = ["archivo", "grado", "area", "titulo", "proposito", "compartir"];

  const $ = (selector, raiz = document) => raiz.querySelector(selector);
  const formulario = $("#formulario-sesion");
  const campos = $("[data-campos]", subir);
  const cuerpo = $("[data-cuerpo]", subir);
  const entradaArchivo = $("#archivo");
  const control = $("[data-archivo-control]", subir);
  const botonEnviar = $("[data-enviar]", subir);
  const botonCancelar = $("[data-cancelar]", subir);
  const errorRed = $("[data-error-red]", subir);
  const errorGeneral = $("[data-error-general]", subir);
  const progreso = $("[data-progreso]", subir);
  const resultado = $("[data-resultado]");
  const abrirBoton = $("[data-abrir-subir]");
  const anuncio = $("#anuncio");

  let origen = abrirBoton; // el botón que abrió el popup, para devolverle el foco
  let archivo = null; // el archivo que pasó la revisión del navegador
  let lectura = 0; // descarta la revisión de un archivo ya reemplazado
  let ocupado = false; // subiendo
  let aceptados = false; // términos aceptados para este formulario y esta casilla
  let entradas = 0; // entradas de historial propias (una por popup abierto)
  let ignorar = 0; // popstate que vienen de un history.back() propio
  let ultimoAnuncio = -1;

  const anunciar = (texto) => {
    anuncio.textContent = texto;
  };

  // «1,2 MB», con coma como el resumen del servidor (filesizeformat); CLDR da punto para es-PE.
  const tamano = (bytes) =>
    bytes < 1048576
      ? `${Math.max(1, Math.round(bytes / 1024))} KB`
      : `${(bytes / 1048576).toLocaleString("es", { maximumFractionDigits: 1 })} MB`;

  // --- Historial (D8) ---

  function empujar() {
    entradas += 1;
    history.pushState({ sesiones: entradas }, "", location.href);
  }

  function consumir(cuantas = 1) {
    const n = Math.min(cuantas, entradas);
    if (!n) return;
    entradas -= n;
    ignorar += 1;
    history.go(-n);
  }

  // --- Errores ---

  function errorCampo(campo, texto) {
    const error = document.getElementById(`${campo}-error`);
    const entrada = document.getElementById(campo);
    error.hidden = !texto;
    error.lastElementChild.textContent = texto || "";
    if (texto) entrada.setAttribute("aria-invalid", "true");
    else entrada.removeAttribute("aria-invalid");
    if (campo === "archivo") control.classList.toggle("rechazado", Boolean(texto));
  }

  function limpiarErrores() {
    for (const campo of CAMPOS) errorCampo(campo, "");
    errorGeneral.hidden = true;
  }

  function mostrarErrores(errores) {
    let primero = null;
    for (const campo of CAMPOS) {
      if (!errores[campo]) continue;
      errorCampo(campo, errores[campo]);
      primero ??= document.getElementById(campo);
    }
    if (errores.general) {
      $("p", errorGeneral).textContent = errores.general;
      errorGeneral.hidden = false;
      cuerpo.scrollTop = 0;
    }
    if (primero) primero.focus();
    else if (errores.general) cuerpo.focus();
  }

  // --- Archivo ---

  function pintarArchivo(elegido, rechazado = false) {
    $("[data-archivo-nombre]", subir).textContent = elegido ? elegido.name : "Elige tu sesión";
    let detalle = "Aún no has elegido un archivo";
    if (elegido && rechazado) detalle = `${tamano(elegido.size)} · No se ha subido`;
    else if (elegido) detalle = `${elegido.tipo} · ${tamano(elegido.size)}`;
    $("[data-archivo-detalle]", subir).textContent = detalle;
    $("[data-archivo-accion]", subir).textContent = elegido ? "Cambiar" : "Elegir";
  }

  async function reconocer(elegido) {
    const nombre = elegido.name.toLowerCase();
    if (elegido.size === 0) return null;
    if (nombre.endsWith(".pdf")) {
      const inicio = new TextDecoder().decode(await elegido.slice(0, 5).arrayBuffer());
      return inicio === "%PDF-" ? "PDF" : null;
    }
    if (nombre.endsWith(".docx")) {
      const bytes = new Uint8Array(await elegido.arrayBuffer());
      const texto = new TextDecoder("latin1").decode(bytes);
      const zip = bytes[0] === 0x50 && bytes[1] === 0x4b;
      return zip && texto.includes("[Content_Types].xml") && texto.includes("word/document.xml")
        ? "Word"
        : null;
    }
    return null;
  }

  entradaArchivo.addEventListener("change", async () => {
    const elegido = entradaArchivo.files[0];
    const version = ++lectura;
    if (!elegido) return;
    archivo = null;
    errorCampo("archivo", "");
    if (elegido.size > TAMANO_MAXIMO) {
      pintarArchivo(elegido, true);
      errorCampo("archivo", MENSAJES.grande);
      return;
    }
    let tipo = null;
    try {
      tipo = await reconocer(elegido);
    } catch {
      if (version !== lectura) return;
      pintarArchivo(elegido, true);
      errorCampo("archivo", MENSAJES.ilegible);
      return;
    }
    if (version !== lectura) return;
    if (!tipo) {
      pintarArchivo(elegido, true);
      errorCampo("archivo", MENSAJES.tipo);
      return;
    }
    archivo = elegido;
    archivo.tipo = tipo;
    pintarArchivo(archivo);
    anunciar("Archivo listo para enviar.");
  });

  for (const campo of ["grado", "area", "titulo", "proposito"]) {
    document.getElementById(campo).addEventListener("input", () => errorCampo(campo, ""));
  }
  $("#compartir").addEventListener("change", () => {
    aceptados = false;
    errorCampo("compartir", "");
  });

  // --- Abrir y cerrar ---

  function formularioNuevo() {
    formulario.reset();
    formulario.elements.id.value = crypto.randomUUID();
    archivo = null;
    aceptados = false;
    lectura += 1;
    pintarArchivo(null);
    limpiarErrores();
    errorRed.hidden = true;
    botonEnviar.textContent = "Enviar a la dirección";
    cuerpo.scrollTop = 0;
  }

  function abrir(desde) {
    if (subir.open) return;
    origen = desde || abrirBoton;
    formularioNuevo();
    document.querySelector("[data-menu-cuenta]")?.removeAttribute("open");
    subir.showModal();
    empujar();
    $("#subir-titulo").focus();
  }

  // El evento close llega después (en otra tarea): la marca dice que este cierre fue del script.
  function cerrarDialogo(dialogo) {
    if (!dialogo.open) return;
    dialogo.dataset.adrede = "si";
    dialogo.close();
  }

  function cierreAdrede(dialogo) {
    const adrede = dialogo.dataset.adrede === "si";
    delete dialogo.dataset.adrede;
    return adrede;
  }

  // Cierra el formulario (y los términos, si quedan) y devuelve el foco. ``historial``: consumir las entradas propias.
  function cerrarTodo({ historial = true, foco = true } = {}) {
    cerrarDialogo(terminos);
    cerrarDialogo(subir);
    if (historial) consumir(entradas);
    else entradas = 0;
    if (foco) origen?.focus();
  }

  function cerrarTerminos({ historial = true } = {}) {
    cerrarDialogo(terminos);
    if (historial) consumir(1);
    botonEnviar.focus();
  }

  function abrirTerminos() {
    terminos.showModal();
    empujar();
    $("#terminos-titulo").focus();
  }

  abrirBoton.addEventListener("click", () => abrir(abrirBoton));
  resultado.addEventListener("click", (evento) => {
    const otra = evento.target.closest("[data-subir-otra]");
    if (otra) abrir(otra);
  });

  botonCancelar.addEventListener("click", () => {
    if (!ocupado) cerrarTodo();
  });
  $("[data-volver]", terminos).addEventListener("click", () => cerrarTerminos());
  $("[data-aceptar]", terminos).addEventListener("click", () => {
    aceptados = true;
    cerrarTerminos();
    enviarSesion();
  });

  // Esc (y «atrás» en Chrome de Android): como «Cancelar» o «Volver»; mientras sube, nada.
  subir.addEventListener("cancel", (evento) => {
    evento.preventDefault();
    if (!ocupado) cerrarTodo();
  });
  terminos.addEventListener("cancel", (evento) => {
    evento.preventDefault();
    if (!ocupado) cerrarTerminos();
  });

  // Si el navegador cierra un popup por su cuenta (close watcher sin activación): mientras sube, se vuelve a abrir; si
  // no, se trata como un cierre con su botón.
  subir.addEventListener("close", () => {
    if (cierreAdrede(subir)) return;
    if (ocupado) {
      subir.showModal();
      return;
    }
    cerrarTodo();
  });
  terminos.addEventListener("close", () => {
    if (cierreAdrede(terminos)) return;
    cerrarTerminos();
  });

  window.addEventListener("popstate", () => {
    if (ignorar > 0) {
      ignorar -= 1;
      return;
    }
    if (!entradas) return;
    if (ocupado) {
      // «Atrás» mientras sube: se repone la entrada y el popup sigue abierto.
      history.pushState({ sesiones: entradas }, "", location.href);
      return;
    }
    entradas -= 1;
    if (terminos.open) cerrarTerminos({ historial: false });
    else cerrarTodo({ historial: false });
  });

  // --- Envío ---

  function validar() {
    limpiarErrores();
    const errores = {};
    if (!archivo) {
      errores.archivo = entradaArchivo.files[0] ? errorArchivoActual() : MENSAJES.faltaArchivo;
    }
    if (!formulario.elements.grado.value) errores.grado = MENSAJES.grado;
    if (!formulario.elements.area.value) errores.area = MENSAJES.area;
    if (!formulario.elements.titulo.value.trim()) errores.titulo = MENSAJES.titulo;
    return errores;
  }

  // El motivo del rechazo del archivo que sigue elegido (tipo o tamaño).
  function errorArchivoActual() {
    const elegido = entradaArchivo.files[0];
    return elegido.size > TAMANO_MAXIMO ? MENSAJES.grande : MENSAJES.tipo;
  }

  function bloquear(valor) {
    ocupado = valor;
    campos.disabled = valor;
    formulario.setAttribute("aria-busy", String(valor));
    for (const boton of [botonEnviar, botonCancelar]) {
      if (valor) boton.setAttribute("aria-disabled", "true");
      else boton.removeAttribute("aria-disabled");
    }
    progreso.hidden = !valor;
    if (valor) {
      botonEnviar.textContent = "Enviando…";
      window.addEventListener("beforeunload", pedirConfirmacion);
    } else {
      window.removeEventListener("beforeunload", pedirConfirmacion);
    }
  }

  function pedirConfirmacion(evento) {
    evento.preventDefault();
    evento.returnValue = "";
  }

  function avance(porcentaje) {
    $("[data-barra]", subir).value = porcentaje;
    $("[data-progreso-texto]", subir).textContent = `Subiendo… ${porcentaje} %`;
    const tramo = Math.floor(porcentaje / 25) * 25;
    if (tramo > ultimoAnuncio) {
      ultimoAnuncio = tramo;
      anunciar(`Subiendo… ${porcentaje} %`);
    }
  }

  function corte() {
    bloquear(false);
    errorRed.hidden = false;
    botonEnviar.textContent = "Reintentar envío";
    cuerpo.scrollTop = 0;
  }

  function exito(html) {
    bloquear(false);
    resultado.innerHTML = html;
    abrirBoton.hidden = true;
    cerrarTodo({ foco: false });
    origen = abrirBoton;
    $("h2", resultado)?.focus();
  }

  function errores400(texto) {
    bloquear(false);
    botonEnviar.textContent = "Enviar a la dirección";
    let errores = null;
    try {
      errores = JSON.parse(texto).errores;
    } catch {
      errores = null;
    }
    if (!errores) {
      corte();
      return;
    }
    if (errores.archivo) {
      archivo = null;
      if (entradaArchivo.files[0]) pintarArchivo(entradaArchivo.files[0], true);
    }
    if (errores.compartir) aceptados = false;
    mostrarErrores(errores);
  }

  function enviarSesion() {
    if (ocupado) return;
    const datos = new FormData(formulario);
    datos.set("archivo", archivo, archivo.name);
    if (aceptados) datos.set("acepta_terminos", "1");
    errorRed.hidden = true;
    errorGeneral.hidden = true;
    ultimoAnuncio = -1;
    bloquear(true);
    avance(0);
    botonEnviar.focus({ preventScroll: true });

    const peticion = new XMLHttpRequest();
    peticion.open("POST", formulario.action);
    peticion.setRequestHeader("X-CSRFToken", formulario.elements.csrfmiddlewaretoken.value);
    peticion.setRequestHeader("HX-Request", "true");
    peticion.upload.addEventListener("progress", (evento) => {
      if (evento.lengthComputable) avance(Math.floor((evento.loaded * 100) / evento.total));
    });
    peticion.addEventListener("load", () => {
      const destino = peticion.getResponseHeader("HX-Redirect");
      if (destino) {
        bloquear(false);
        location.assign(destino);
      } else if (peticion.status >= 200 && peticion.status < 300) {
        exito(peticion.responseText);
      } else if (peticion.status === 400) {
        errores400(peticion.responseText);
      } else {
        corte();
      }
    });
    for (const fallo of ["error", "abort", "timeout"]) peticion.addEventListener(fallo, corte);
    peticion.send(datos);
  }

  formulario.addEventListener("submit", (evento) => {
    evento.preventDefault();
    if (ocupado) return;
    const errores = validar();
    if (Object.keys(errores).length) {
      mostrarErrores(errores);
      return;
    }
    if (formulario.elements.compartir.checked && !aceptados) {
      abrirTerminos();
      return;
    }
    enviarSesion();
  });
})();
