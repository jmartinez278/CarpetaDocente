"""Build de Vercel (EN-02, D6): estilos y migraciones, en ese orden y sin shell.

Vercel lo corre después de instalar las dependencias (`[tool.vercel.scripts] build`).
Los estáticos los reúne el `collectstatic` automático de Vercel.
Las migraciones usan la conexión directa de Neon (`DATABASE_URL_UNPOOLED`), no la
agrupada. Nada de lo que imprime incluye las URL de la base.
"""

import os
import shutil
import subprocess
import sys
from collections.abc import Callable, Mapping
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
FRONTEND = RAIZ / "src" / "frontend"
MANAGE = RAIZ / "src" / "backend" / "manage.py"


def main(
    entorno: Mapping[str, str] = os.environ,
    ejecutar: Callable[..., subprocess.CompletedProcess] = subprocess.run,
) -> int:
    url_directa = entorno.get("DATABASE_URL_UNPOOLED", "")
    if not url_directa:
        print(
            "Falta DATABASE_URL_UNPOOLED: las migraciones no pueden correr por la URL "
            "agrupada. Revisa la integración de Neon en Vercel.",
            file=sys.stderr,
        )
        return 1

    npm = shutil.which("npm") or "npm"
    pasos = [
        ([npm, "ci"], FRONTEND, dict(entorno)),
        ([npm, "run", "build"], FRONTEND, dict(entorno)),
        (
            [sys.executable, str(MANAGE), "migrate", "--noinput"],
            RAIZ,
            {**entorno, "DATABASE_URL": url_directa},
        ),
    ]
    for comando, carpeta, variables in pasos:
        print(f"==> {' '.join(Path(parte).name for parte in comando)}", flush=True)
        resultado = ejecutar(comando, cwd=carpeta, env=variables, check=False)
        if resultado.returncode != 0:
            print(f"El paso falló con código {resultado.returncode}.", file=sys.stderr)
            return resultado.returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())
