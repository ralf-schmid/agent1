FROM python:3.12-slim

# Arbeitsverzeichnis
WORKDIR /app

# System-Dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    && rm -rf /var/lib/apt/lists/*

# Anwendungscode kopieren (für pip install benötigt)
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Python Dependencies und Paket installieren
RUN pip install --no-cache-dir .

# Daten-Verzeichnis kopieren
COPY data/ ./data/

# Entrypoint-Skript kopieren
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Nicht-Root-User erstellen
RUN useradd --create-home --shell /bin/bash botuser \
    && chown -R botuser:botuser /app
USER botuser

# Healthcheck
HEALTHCHECK --interval=60s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Einstiegspunkt - kann mit Argumenten überschrieben werden
# Standard: Scheduler-Modus
# --once: Einmaliger Post
# --dry-run: Vorschau ohne Post
# shell/bash: Startet eine Shell für Debugging
ENTRYPOINT ["docker-entrypoint.sh"]
CMD []
