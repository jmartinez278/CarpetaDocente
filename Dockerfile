# Imagen de desarrollo de la aplicación Django (EN-01; design.md, D8).
# La versión de Python debe coincidir con .python-version y pyproject.toml (D4).
FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.12 /uv /uvx /bin/

# Entorno virtual fuera de /app para que el montaje de src/backend no lo tape.
ENV PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Dependencias exactas de uv.lock (incluye las de desarrollo: pytest y Ruff).
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project

COPY pyproject.toml uv.lock ./
COPY src/backend ./src/backend

EXPOSE 8000
CMD ["python", "src/backend/manage.py", "runserver", "0.0.0.0:8000"]
