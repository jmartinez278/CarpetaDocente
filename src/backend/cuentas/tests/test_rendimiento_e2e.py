"""Carga de ``/ingresar/`` con Slow 4G y sin caché (RNF-002; spec pantallas-de-inicio; D11).

Solo en Chromium: usa el protocolo de DevTools para limitar la red. Mide los bytes transferidos
(<= 2 MB) y el tiempo hasta que la página es usable (<= 5 s) e imprime las cifras (``-s`` o el
resumen de fallas las muestran). Se pide con ``uv run pytest -m e2e --browser chromium``.
"""

import time

import pytest
from playwright.sync_api import expect

from cuentas.tests.e2e import abrir_ingresar, boton_ingresar

pytestmark = pytest.mark.e2e

MAXIMO_BYTES = 2 * 1024 * 1024
MAXIMO_SEGUNDOS = 5

# Perfil Slow 4G de Chrome DevTools, el mismo del prototipo: 1,6 Mbps bajada y 750 kbps subida,
# ambos por 0,9, y 150 ms de latencia por 3,75.
SLOW_4G = {
    "offline": False,
    "downloadThroughput": 1.6 * 1024 * 1024 / 8 * 0.9,
    "uploadThroughput": 750 * 1024 / 8 * 0.9,
    "latency": 150 * 3.75,
}


def test_inicio_de_sesion_con_slow_4g(live_server, page, browser_name):
    if browser_name != "chromium":
        pytest.skip("El perfil de red por CDP existe solo en Chromium.")
    sesion = page.context.new_cdp_session(page)
    sesion.send("Network.enable")
    sesion.send("Network.setCacheDisabled", {"cacheDisabled": True})
    sesion.send("Network.emulateNetworkConditions", SLOW_4G)
    transferidos = []
    sesion.on(
        "Network.loadingFinished", lambda evento: transferidos.append(evento["encodedDataLength"])
    )

    inicio = time.perf_counter()
    abrir_ingresar(page, live_server)
    page.evaluate("document.fonts.ready")
    boton = boton_ingresar(page)
    expect(boton).to_be_visible()
    expect(boton).to_be_enabled()
    segundos = time.perf_counter() - inicio

    # Sin respuestas medidas, el tope de bytes pasaría sin medir nada.
    assert transferidos, "no se recibió ningún Network.loadingFinished"
    total = sum(transferidos)
    print(
        f"\nSlow 4G en /ingresar/: {total / 1024:.1f} KB en {len(transferidos)} respuestas, "
        f"usable en {segundos:.2f} s"
    )
    assert total <= MAXIMO_BYTES, f"{total} bytes"
    assert segundos <= MAXIMO_SEGUNDOS, f"{segundos:.2f} s"
