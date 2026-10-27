"""Prueba del manage.py de la raíz, que Vercel usa para detectar Django (EN-02, D6)."""

import os
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]


def correr_desde_la_raiz(*argumentos: str) -> subprocess.CompletedProcess:
    entorno = {k: v for k, v in os.environ.items() if k != "DJANGO_SETTINGS_MODULE"}
    entorno.update(
        {
            "DJANGO_SECRET_KEY": "clave-ficticia-solo-para-pruebas",
            "DATABASE_URL": "postgres://usuario:clave@servidor-ficticio:5432/base",
        }
    )
    return subprocess.run(  # noqa: S603 - comando fijo, sin entrada del usuario
        [sys.executable, "manage.py", *argumentos],
        cwd=RAIZ,
        env=entorno,
        capture_output=True,
        text=True,
        check=False,
    )


def test_manage_de_la_raiz_corre_los_comandos_del_proyecto():
    resultado = correr_desde_la_raiz("check")

    assert resultado.returncode == 0, resultado.stderr
    assert "no issues" in resultado.stdout
