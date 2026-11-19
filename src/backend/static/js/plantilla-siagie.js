// Plantilla de notas del SIAGIE (spec plantilla-notas-siagie; design de US-024/025, D3, D4, D10 y D13). Sin Alpine ni HTMX,
// con defer, siguiendo el patrón de sesiones.js.
//
// - «Subir plantilla» abre el diálogo; cada apertura es un formulario nuevo (se vuelve a pintar el marcado de origen).
// - Envío con XMLHttpRequest (fetch no informa el avance de la subida): 200 trae el paso «Elige la sección» (que
//   reemplaza el diálogo) o el resumen (que reemplaza el contenido de <main>); 400 trae {error, ayuda_siagie}; lo demás
//   (red, 413, 5xx, o sin respuesta en TIEMPO_MAXIMO) es «Se cortó la conexión» y el archivo sigue elegido. Con
//   HX-Request, la sesión vencida o la falta de sesión responden con HX-Redirect: la página completa va al ingreso.
// - El archivo no se guarda en el servidor entre pasos (D3): este script conserva el File y lo envía otra vez con la
//   sección elegida.
// - El archivo completado llega en base64 en data-archivo y aquí se vuelve un Blob con su URL (D4).
// - «¿No es esta sección?» borra la equivalencia y cambia el panel del archivo (D13).
(() => {
  const dialogo = document.getElementById("plantilla-siagie");
  const principal = document.getElementById("contenido");
  if (!dialogo || !principal) return;

  const TAMANO_MAXIMO = 3 * 1024 * 1024;
  const TIPO_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";
  // 3 MB en Slow 4G suben en unos 40 s; con el llenado, 2 minutos sin respuesta es un corte.
  const TIEMPO_MAXIMO = 120_000;
  const MENSAJES = {
    grande: "El archivo supera los 3 MB. Elige uno más pequeño.",
    corte: "Se cortó la conexión.",
    corteDetalle: "Tu archivo sigue aquí: revisa tu conexión e inténtalo de nuevo.",
    quitar: "No pudimos quitar la equivalencia. Inténtalo de nuevo.",
  };

  const $ = (selector, raiz = dialogo) => raiz.querySelector(selector);
  const inicial = dialogo.innerHTML; // el formulario de origen, para cada apertura
  const ruta = $("#formulario-plantilla").getAttribute("action");
  const csrf = $("[name=csrfmiddlewaretoken]").value;

  let origen = null; // lo que abrió el diálogo, para devolverle el foco
  let archivo = null; // el File elegido; no se guarda en el servidor entre pasos
  let ocupado = false;
  let urlDescarga = null;

  // --- Foco y cierre ---

  function devolverFoco() {
    (origen?.isConnected ? origen : principal).focus();
  }

  function cerrar() {
    if (dialogo.open) dialogo.close();
    devolverFoco();
  }

  function abrir(desde) {
    if (dialogo.open) return;
    origen = desde;
    archivo = null;
    ocupado = false;
    dialogo.innerHTML = inicial;
    dialogo.setAttribute("aria-labelledby", "plantilla-titulo");
    dialogo.setAttribute("aria-describedby", "plantilla-ayuda");
    document.querySelector("[data-menu-cuenta]")?.removeAttribute("open");
    dialogo.showModal();
    $("#plantilla-titulo").focus();
  }

  // --- Estado del diálogo ---

  const enPasoDeSeccion = () => Boolean($("[data-paso]"));

  function puedeEnviar() {
    return enPasoDeSeccion() ? Boolean($('input[name="seccion"]:checked')) : Boolean(archivo);
  }

  function actualizarBoton() {
    const boton = $("[data-enviar]");
    if (boton) boton.disabled = ocupado || !puedeEnviar();
  }

  function pedirConfirmacion(evento) {
    evento.preventDefault();
    evento.returnValue = "";
  }

  function bloquear(valor) {
    ocupado = valor;
    for (const campos of dialogo.querySelectorAll("fieldset")) campos.disabled = valor;
    const formulario = $("form");
    if (formulario) formulario.setAttribute("aria-busy", String(valor));
    const cancelar = $("[data-cancelar]");
    if (cancelar) cancelar.disabled = valor;
    const progreso = $("[data-progreso]");
    if (progreso) progreso.hidden = !valor;
    actualizarBoton();
    if (valor) {
      // El botón que se deshabilita pierde el foco: queda en el título, que nombra el diálogo.
      $("h2").focus({ preventScroll: true });
      window.addEventListener("beforeunload", pedirConfirmacion);
    } else {
      window.removeEventListener("beforeunload", pedirConfirmacion);
    }
  }

  function avance(porcentaje) {
    const barra = $("[data-barra]");
    if (!barra) return;
    if (porcentaje === null) barra.removeAttribute("value"); // la subida terminó: el servidor trabaja
    else barra.value = porcentaje;
  }

  // --- Errores ---

  function limpiarErrores() {
    const error = $("#archivo-error");
    if (error) {
      error.hidden = true;
      $("#archivo").removeAttribute("aria-invalid");
      $("[data-archivo-control]").classList.remove("rechazado");
      $("[data-ruta-siagie]").hidden = false;
    }
    for (const aviso of dialogo.querySelectorAll("[data-error-red], [data-error-paso]")) {
      aviso.hidden = true;
    }
  }

  // Un rechazo del campo (paso de la subida) o del paso de la sección; el foco va al mensaje.
  function mostrarError({ titulo, detalle = null, ayudaSiagie = false }) {
    if (enPasoDeSeccion()) {
      const aviso = $("[data-error-paso]");
      $("[data-error-titulo]", aviso).textContent = titulo;
      const parrafo = $("[data-error-detalle]", aviso);
      parrafo.textContent = detalle || "";
      parrafo.hidden = !detalle;
      aviso.hidden = false;
      aviso.focus();
      return;
    }
    const aviso = $("#archivo-error");
    $("[data-error-titulo]", aviso).textContent = titulo;
    $("[data-error-ayuda]", aviso).hidden = !ayudaSiagie;
    // La ruta del SIAGIE solo ayuda cuando el archivo no es la plantilla.
    $("[data-ruta-siagie]").hidden = !ayudaSiagie;
    $("#archivo").setAttribute("aria-invalid", "true");
    $("[data-archivo-control]").classList.add("rechazado");
    aviso.hidden = false;
    aviso.focus();
  }

  function corte() {
    bloquear(false);
    if (enPasoDeSeccion()) {
      mostrarError({ titulo: MENSAJES.corte, detalle: MENSAJES.corteDetalle });
      return;
    }
    const aviso = $("[data-error-red]");
    aviso.hidden = false;
    aviso.focus();
  }

  // --- Archivo ---

  function pintarArchivo(elegido, rechazado = false) {
    $("[data-archivo-nombre]").textContent = elegido ? elegido.name : "Elige tu plantilla";
    let detalle = "Aún no has elegido un archivo";
    if (elegido) detalle = rechazado ? "No se ha subido" : "Excel (.xlsx)";
    $("[data-archivo-detalle]").textContent = detalle;
    $("[data-archivo-accion]").textContent = elegido ? "Cambiar" : "Elegir";
  }

  function elegirArchivo(elegido) {
    if (!elegido) return;
    limpiarErrores();
    if (elegido.size > TAMANO_MAXIMO) {
      // Solo una ayuda: el servidor tiene el mismo tope (3 MB, para que la respuesta en base64
      // quepa en los 4,5 MB de Vercel).
      archivo = null;
      pintarArchivo(elegido, true);
      mostrarError({ titulo: MENSAJES.grande });
      actualizarBoton();
      return;
    }
    archivo = elegido;
    pintarArchivo(elegido);
    actualizarBoton();
  }

  // --- Respuesta ---

  function nuevaPeticion(url) {
    const peticion = new XMLHttpRequest();
    peticion.open("POST", url);
    peticion.timeout = TIEMPO_MAXIMO;
    peticion.setRequestHeader("X-CSRFToken", csrf);
    peticion.setRequestHeader("HX-Request", "true");
    return peticion;
  }

  // Sesión vencida, sin sesión u otro rol: la página completa va a donde dice el servidor.
  function redirigido(peticion) {
    const destino = peticion.getResponseHeader("HX-Redirect");
    if (destino) location.assign(destino);
    return Boolean(destino);
  }

  function ponerPaso(fragmento) {
    dialogo.replaceChildren(fragmento);
    dialogo.setAttribute("aria-labelledby", "plantilla-seccion-titulo");
    dialogo.removeAttribute("aria-describedby");
    $("#plantilla-seccion-titulo").focus();
  }

  function soltarDescarga() {
    if (urlDescarga) URL.revokeObjectURL(urlDescarga);
    urlDescarga = null;
  }

  // El archivo viaja en base64 en el enlace; aquí se vuelve un Blob con su URL y se descarga con el nombre original.
  function prepararDescarga(enlace) {
    const binario = atob(enlace.dataset.archivo);
    const bytes = new Uint8Array(binario.length);
    for (let i = 0; i < binario.length; i += 1) bytes[i] = binario.charCodeAt(i);
    urlDescarga = URL.createObjectURL(new Blob([bytes], { type: TIPO_XLSX }));
    enlace.href = urlDescarga;
  }

  function mostrarResumen(fragmento) {
    soltarDescarga();
    for (const hijo of [...principal.children]) if (hijo !== dialogo) hijo.remove();
    principal.insertBefore(fragmento, dialogo);
    const enlace = $("[data-archivo]", principal);
    if (enlace) prepararDescarga(enlace);
    const titulo = $("h1", principal);
    document.title = `${titulo.textContent.trim()} · CarpetaDocente`;
    window.scrollTo(0, 0);
    titulo.focus();
  }

  function respuesta200(html) {
    const plantilla = document.createElement("template");
    plantilla.innerHTML = html;
    const raiz = plantilla.content.firstElementChild;
    const paso = raiz?.dataset.paso;
    if (paso === "seccion") {
      bloquear(false);
      ponerPaso(plantilla.content);
    } else if (paso === "resumen") {
      bloquear(false);
      if (dialogo.open) dialogo.close();
      mostrarResumen(plantilla.content);
    } else {
      corte();
    }
  }

  function respuesta400(texto) {
    let cuerpo = null;
    try {
      cuerpo = JSON.parse(texto);
    } catch {
      cuerpo = null;
    }
    if (!cuerpo?.error) {
      corte();
      return;
    }
    bloquear(false);
    mostrarError({ titulo: cuerpo.error, ayudaSiagie: Boolean(cuerpo.ayuda_siagie) });
  }

  function enviar(seccion = null) {
    if (ocupado || !archivo) return;
    const datos = new FormData();
    datos.set("archivo", archivo, archivo.name);
    if (seccion) datos.set("seccion", seccion);
    limpiarErrores();
    bloquear(true);
    avance(0);

    const peticion = nuevaPeticion(ruta);
    peticion.upload.addEventListener("progress", (evento) => {
      if (evento.lengthComputable) avance(Math.floor((evento.loaded * 100) / evento.total));
    });
    peticion.upload.addEventListener("load", () => avance(null));
    peticion.addEventListener("load", () => {
      if (redirigido(peticion)) return;
      if (peticion.status >= 200 && peticion.status < 300) respuesta200(peticion.responseText);
      else if (peticion.status === 400) respuesta400(peticion.responseText);
      else corte();
    });
    for (const fallo of ["error", "abort", "timeout"]) peticion.addEventListener(fallo, corte);
    peticion.send(datos);
  }

  // --- Eventos del diálogo (delegados: el contenido se reemplaza) ---

  dialogo.addEventListener("change", (evento) => {
    if (evento.target.id === "archivo") elegirArchivo(evento.target.files[0]);
    else if (evento.target.name === "seccion") actualizarBoton();
  });

  dialogo.addEventListener("submit", (evento) => {
    evento.preventDefault();
    if (ocupado) return;
    if (evento.target.id === "formulario-seccion") {
      const elegida = $('input[name="seccion"]:checked');
      if (elegida) enviar(elegida.value);
    } else {
      enviar();
    }
  });

  dialogo.addEventListener("click", (evento) => {
    if (evento.target.closest("[data-cancelar]") && !ocupado) cerrar();
  });

  // Esc (y «atrás» en Chrome de Android): como «Cancelar»; mientras procesa, nada.
  dialogo.addEventListener("cancel", (evento) => {
    evento.preventDefault();
    if (!ocupado) cerrar();
  });

  // Si el navegador lo cierra por su cuenta mientras procesa, se vuelve a abrir.
  dialogo.addEventListener("close", () => {
    if (ocupado) dialogo.showModal();
  });

  // --- Eventos de la página (delegados: el inicio y el resumen se reemplazan) ---

  document.addEventListener("click", (evento) => {
    const apertura = evento.target.closest("[data-abrir-plantilla], [data-subir-otra]");
    if (apertura) abrir(apertura);
  });

  // «¿No es esta sección?» (D13): borra la equivalencia y cambia el panel del archivo. Sin este script, el formulario
  // se envía solo y el servidor redirige al inicio. Cada borrado queda atado al panel de su resumen: si mientras
  // tanto llegó otro resumen, la respuesta ya no toca nada (ni el panel ni el Blob del resumen nuevo).
  document.addEventListener("submit", (evento) => {
    const formulario = evento.target.closest("[data-borrar-equivalencia]");
    if (!formulario) return;
    evento.preventDefault();
    const boton = $("button", formulario);
    if (boton.disabled) return;
    boton.disabled = true;
    const panel = $("[data-panel-archivo]", principal);

    const peticion = nuevaPeticion(formulario.action);
    peticion.addEventListener("load", () => {
      if (!panel.isConnected || redirigido(peticion)) return;
      if (peticion.status >= 200 && peticion.status < 300) {
        const plantilla = document.createElement("template");
        plantilla.innerHTML = peticion.responseText;
        soltarDescarga();
        panel.replaceWith(plantilla.content);
        formulario.remove();
        $("[data-aviso]", principal).focus();
      } else {
        const texto = peticion.status === 404 ? peticion.responseText : MENSAJES.quitar;
        fallaBorrar(panel, boton, texto);
      }
    });
    for (const fallo of ["error", "abort", "timeout"]) {
      peticion.addEventListener(fallo, () => {
        if (panel.isConnected) fallaBorrar(panel, boton, MENSAJES.quitar);
      });
    }
    peticion.send();
  });

  function fallaBorrar(panel, boton, texto) {
    boton.disabled = false;
    let aviso = $("[data-aviso-borrar]", panel);
    if (!aviso) {
      aviso = document.createElement("p");
      aviso.setAttribute("role", "alert");
      aviso.setAttribute("data-aviso-borrar", "");
      $("h2", panel).after(aviso);
    }
    aviso.textContent = texto;
  }
})();
