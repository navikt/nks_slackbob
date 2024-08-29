FROM python:3.12-slim-bookworm
# Install uv.
COPY --from=ghcr.io/astral-sh/uv:0.4.0 /uv /bin/uv
# Opprett arbeidsmappe for prosjektet i Docker
WORKDIR /nks_slackbob
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
# Server applikasjonen som default for Docker bildet
CMD ["nks-slackbob"]
