"""Pruebas del build de Vercel (EN-02, D6) y de la entrada WSGI desde la raíz del repo."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

import build_vercel

RAIZ = Path(__file__).resolve().parents[2]
URL_AGRUPADA = "postgres://usuario:clave-agrupada@host-pooler.ficticio/base"
URL_DIRECTA = "postgres://usuario:clave-directa@host-directo.ficticio/base"


class Simulador:
    """Reemplaza a subprocess.run: guarda cada llamada y puede fallar en un paso."""

    def __init__(self, falla_en=None, codigo=3):
        self.llamadas = []
        self.falla_en = falla_en
        self.codigo = codigo

    def __call__(self, comando, **kwargs):
        self.llamadas.append((list(comando), kwargs))
        falla = self.falla_en is not None and self.falla_en in comando
        return subprocess.CompletedProcess(comando, self.codigo if falla else 0)


@pytest.fixture
def entorno():
    return {"DATABASE_URL": URL_AGRUPADA, "DATABASE_URL_UNPOOLED": URL_DIRECTA, "PATH": "x"}


def test_ejecuta_npm_ci_npm_build_y_migrate_en_ese_orden(entorno):
    sim = Simulador()

    assert build_vercel.main(entorno, sim) == 0

    comandos = [c for c, _ in sim.llamadas]
    assert len(comandos) == 3
    assert comandos[0][1:] == ["ci"]
    assert comandos[1][1:] == ["run", "build"]
    assert comandos[2][1:] == [str(RAIZ / "src" / "backend" / "manage.py"), "migrate", "--noinput"]
    assert Path(sim.llamadas[0][1]["cwd"]) == RAIZ / "src" / "frontend"
    assert Path(sim.llamadas[1][1]["cwd"]) == RAIZ / "src" / "frontend"


def test_migrate_recibe_la_url_directa_como_database_url(entorno):
    sim = Simulador()

    build_vercel.main(entorno, sim)

    assert sim.llamadas[2][1]["env"]["DATABASE_URL"] == URL_DIRECTA
    # Solo ese proceso: el entorno del build no cambia.
    assert entorno["DATABASE_URL"] == URL_AGRUPADA


def test_sin_url_directa_falla_con_mensaje_y_sin_migrate(entorno, capsys):
    del entorno["DATABASE_URL_UNPOOLED"]
    sim = Simulador()

    codigo = build_vercel.main(entorno, sim)

    assert codigo != 0
    assert "DATABASE_URL_UNPOOLED" in capsys.readouterr().err
    assert not any("migrate" in c for c, _ in sim.llamadas)


def test_url_directa_vacia_cuenta_como_ausente(entorno):
    entorno["DATABASE_URL_UNPOOLED"] = ""
    sim = Simulador()

    assert build_vercel.main(entorno, sim) != 0
    assert not any("migrate" in c for c, _ in sim.llamadas)


@pytest.mark.parametrize(("paso", "esperadas"), [("ci", 1), ("build", 2), ("migrate", 3)])
def test_un_paso_que_falla_corta_el_build_con_su_codigo(entorno, paso, esperadas):
    sim = Simulador(falla_en=paso, codigo=7)

    assert build_vercel.main(entorno, sim) == 7
    assert len(sim.llamadas) == esperadas


def test_la_salida_no_contiene_las_urls(entorno, capsys):
    build_vercel.main(entorno, Simulador())
    entorno["DATABASE_URL_UNPOOLED"] = ""
    build_vercel.main(entorno, Simulador())
    salida = capsys.readouterr()

    for texto in (salida.out, salida.err):
        assert "clave-agrupada" not in texto
        assert "clave-directa" not in texto
        assert "postgres://" not in texto


def test_wsgi_importa_application_desde_la_raiz_del_repo():
    entorno = {k: v for k, v in os.environ.items() if k != "DJANGO_SETTINGS_MODULE"}
    entorno.update(
        {
            "DJANGO_SECRET_KEY": "clave-ficticia-solo-para-pruebas",
            "DATABASE_URL": "postgres://usuario:clave@servidor-ficticio:5432/base",
        }
    )
    codigo = (
        "import environ; environ.Env.read_env = lambda *a, **k: None; "
        "from src.backend.config.wsgi import application; print(callable(application))"
    )

    resultado = subprocess.run(  # noqa: S603 - comando fijo
        [sys.executable, "-c", codigo],
        cwd=RAIZ,
        env=entorno,
        capture_output=True,
        text=True,
        check=False,
    )

    assert resultado.returncode == 0, resultado.stderr
    assert resultado.stdout.strip() == "True"
