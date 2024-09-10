# Vi bruker et Docker image fra uv hvor uv allerede er installert
FROM ghcr.io/astral-sh/uv:0.4.8-python3.12-bookworm-slim
# Opprett arbeidsmappe for prosjektet i Docker
WORKDIR /nks_slackbob
# Be uv kompilere kilder for raskere oppstart
ENV UV_COMPILE_BYTECODE=1
# Kopier kode inn i Docker bildet
COPY README.md .
COPY pyproject.toml .
COPY uv.lock .
# Installer bare avhengigheter (bruker uv.lock)
RUN uv sync --frozen --no-install-project
# Kopier inn kildekode som vi forventer endrer seg
COPY src src
# Installer prosjektet ved hjelp av 'uv.lock'
RUN uv sync --frozen
# Eksponer virtual environment fra installasjonen
ENV PATH="/nks_slackbob/.venv/bin:$PATH"
# Tomt entry point for å ikke kjøre uv
ENTRYPOINT [ ]
# Server applikasjonen som default for Docker bildet
CMD ["nks-slackbob"]
