# Vi bruker et Docker image fra uv hvor uv allerede er installert
FROM ghcr.io/astral-sh/uv:0.4.12-bookworm-slim AS builder
# Be uv kompilere kilder for raskere oppstart
ENV UV_COMPILE_BYTECODE=1
# Kopier fra cache siden vi bruker --mount
ENV UV_LINK_MODE=copy
# Installer Python i samme mappe som applikasjonen
ENV UV_PYTHON_INSTALL_DIR=/app/
# Opprett arbeidsmappe for prosjektet i Docker
WORKDIR /app
# Installer avhengigheter for prosjektet uten koden
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev
# Kopier kode inn i Docker bildet
ADD . /app
# Installer prosjektet
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Bildet vi ender opp med blir distroless
FROM gcr.io/distroless/base-debian12
# Kopier kode fra byggebildet
COPY --from=builder --chown=app:app /app /app
# Eksponer pakker fra virtueltmiljø
ENV PATH="/app/.venv/bin:$PATH"
# Server applikasjonen som default for Docker bildet
CMD ["python3", "/app/src/nks_slackbob/main.py"]
