FROM python:3.12-slim

# Arbeitsverzeichnis
WORKDIR /app

# System-Dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Python Dependencies installieren
COPY pyproject.toml ./
RUN pip install --no-cache-dir .

# Anwendungscode kopieren
COPY src/ ./src/
COPY data/ ./data/

# Nicht-Root-User erstellen
RUN useradd --create-home --shell /bin/bash botuser \
    && chown -R botuser:botuser /app
USER botuser

# Healthcheck
HEALTHCHECK --interval=60s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Einstiegspunkt
ENTRYPOINT ["python", "-m", "losungs_bot.main"]
