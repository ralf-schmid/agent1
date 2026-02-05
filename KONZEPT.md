# Fediverse Bibel-Agent: Architektur & Konzept

## Projektübersicht

Ein KI-Agent, der im Fediverse (Mastodon/ActivityPub) aktiv ist und täglich die Herrnhuter Losungen sowie Lehrtexte postet, mit späterem Ausbau zur Interaktion.

---

## Phasen-Übersicht

```
┌─────────────────────────────────────────────────────────────────────┐
│                         PHASE 1: Tägliche Posts                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────┐  │
│  │   Losungs-  │───▶│   Post-     │───▶│   Mastodon/Fediverse   │  │
│  │   Quelle    │    │   Generator │    │   API                   │  │
│  └─────────────┘    └─────────────┘    └─────────────────────────┘  │
│        ▲                                                             │
│        │ Cron (täglich 6:00)                                        │
└────────┼────────────────────────────────────────────────────────────┘
         │
┌────────┼────────────────────────────────────────────────────────────┐
│        │            PHASE 2: Interaktion                            │
│  ┌─────┴───────┐    ┌─────────────┐    ┌─────────────────────────┐  │
│  │  Mentions   │───▶│   Claude    │───▶│   Antwort-Generator     │  │
│  │  Listener   │    │   API       │    │   & Poster              │  │
│  └─────────────┘    └─────────────┘    └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Architektur (Detail)

```
                    ┌──────────────────────────────────────────────┐
                    │              HOSTING (VPS/Container)         │
                    │                                              │
                    │  ┌────────────────────────────────────────┐  │
                    │  │           AGENT-CORE (Python)          │  │
                    │  │                                        │  │
                    │  │  ┌──────────────┐  ┌────────────────┐  │  │
                    │  │  │  Scheduler   │  │  Mastodon      │  │  │
                    │  │  │  (APScheduler│  │  Client        │  │  │
                    │  │  │  oder Cron)  │  │  (Mastodon.py) │  │  │
                    │  │  └──────┬───────┘  └───────┬────────┘  │  │
                    │  │         │                  │           │  │
                    │  │         ▼                  ▼           │  │
                    │  │  ┌──────────────────────────────────┐  │  │
                    │  │  │        Post-Service              │  │  │
                    │  │  │  - Losungs-Formatter             │  │  │
                    │  │  │  - Bibelstellen-Links            │  │  │
                    │  │  │  - Hashtag-Generator             │  │  │
                    │  │  └──────────────────────────────────┘  │  │
                    │  │                                        │  │
                    │  │  ┌──────────────────────────────────┐  │  │
                    │  │  │     Interaktion-Service          │  │  │
                    │  │  │  (Phase 2)                       │  │  │
                    │  │  │  - Mentions-Polling              │  │  │
                    │  │  │  - Claude API Integration        │  │  │
                    │  │  │  - Kontext-Management            │  │  │
                    │  │  └──────────────────────────────────┘  │  │
                    │  │                                        │  │
                    │  └────────────────────────────────────────┘  │
                    │                                              │
                    │  ┌────────────────────────────────────────┐  │
                    │  │           PERSISTENZ                   │  │
                    │  │  - SQLite (gepostete Losungen)         │  │
                    │  │  - Config (JSON/YAML)                  │  │
                    │  │  - Logs                                │  │
                    │  └────────────────────────────────────────┘  │
                    │                                              │
                    └──────────────────────────────────────────────┘
                                         │
           ┌─────────────────────────────┼─────────────────────────────┐
           │                             │                             │
           ▼                             ▼                             ▼
    ┌─────────────┐             ┌─────────────────┐           ┌──────────────┐
    │  Losungen   │             │    Mastodon     │           │   Claude     │
    │  API/Daten  │             │    Instanz      │           │   API        │
    │             │             │    (Fediverse)  │           │   (Phase 2)  │
    └─────────────┘             └─────────────────┘           └──────────────┘
```

---

## Technologie-Stack

### Empfehlung: Python

| Komponente | Technologie | Begründung |
|------------|-------------|------------|
| **Sprache** | Python 3.11+ | Beste Library-Unterstützung für Mastodon, einfaches Deployment |
| **Mastodon-Client** | `Mastodon.py` | Offizielle, gut dokumentierte Library |
| **Scheduler** | `APScheduler` oder System-Cron | Zuverlässig, flexibel |
| **HTTP-Client** | `httpx` oder `requests` | Für Losungen-API |
| **KI (Phase 2)** | `anthropic` SDK | Claude API für intelligente Antworten |
| **Datenbank** | SQLite | Leichtgewichtig, keine Infrastruktur nötig |
| **Config** | `pydantic-settings` | Typsichere Konfiguration |
| **Logging** | `structlog` | Strukturiertes Logging |

### Alternative: Node.js/TypeScript

| Komponente | Technologie |
|------------|-------------|
| **Sprache** | TypeScript |
| **Mastodon-Client** | `masto.js` |
| **Scheduler** | `node-cron` |
| **KI** | `@anthropic-ai/sdk` |

**Empfehlung: Python** - besseres Ökosystem für diesen Use-Case.

---

## Datenquellen für Losungen

### Option 1: Herrnhuter Losungen API (empfohlen)
```
https://www.losungen.de/
```
- Offizielle Quelle
- XML/JSON verfügbar
- Lizenzierung beachten!

### Option 2: Losungen als Datei
- Jährliche XML-Datei der Losungen
- Lokal verarbeiten
- Download: https://www.losungen.de/download/

### Option 3: Open-Source Projekte
- GitHub: `dblap/herrnhuter-losungen`
- Verschiedene API-Wrapper verfügbar

### Bibelstellen-Links

**Gewählt: BibleServer mit Elberfelder Übersetzung** ✅

| Format | Beispiel-URL |
|--------|--------------|
| Basis | `https://www.bibleserver.com/ELB/{Stelle}` |
| Psalm 145,18 | `https://www.bibleserver.com/ELB/Psalm145,18` |
| Matthäus 7,7 | `https://www.bibleserver.com/ELB/Matthäus7,7` |

**Vorteile BibleServer:**
- Deutsche Plattform (DSGVO-konform)
- Elberfelder Übersetzung verfügbar
- Kurze, lesbare URLs
- Keine Tracking-Parameter nötig

---

## Hosting-Optionen

### Option 1: VPS (Virtual Private Server) - Empfohlen

```
┌─────────────────────────────────────────┐
│  VPS (z.B. Hetzner, Netcup, DigitalOcean)
│                                         │
│  + Volle Kontrolle                      │
│  + Günstig (3-5€/Monat)                 │
│  + Dauerhaft laufend                    │
│  - Selbst-Administration                │
└─────────────────────────────────────────┘
```

**Empfohlene Anbieter (DSGVO-konform):**
- Hetzner Cloud (CX11: ~4€/Monat)
- Netcup (VPS 200: ~3€/Monat)
- IONOS VPS

### Option 2: Container-Platform

```
┌─────────────────────────────────────────┐
│  Container (Docker)                     │
│                                         │
│  + Reproduzierbar                       │
│  + Einfaches Deployment                 │
│  + Skalierbar                           │
│  - Leicht höhere Komplexität            │
└─────────────────────────────────────────┘
```

**Plattformen:**
- fly.io (kostenloser Tier verfügbar)
- Railway
- Render

### Option 3: Serverless (nur für Phase 1)

```
┌─────────────────────────────────────────┐
│  Serverless Functions                   │
│                                         │
│  + Kein Server-Management               │
│  + Pay-per-Use                          │
│  - Nicht ideal für Polling (Phase 2)    │
│  - Cold-Start-Latenz                    │
└─────────────────────────────────────────┘
```

**Plattformen:**
- AWS Lambda + EventBridge
- Google Cloud Functions + Cloud Scheduler
- Cloudflare Workers

**Empfehlung: VPS mit Docker** - beste Balance aus Kontrolle, Kosten und Flexibilität.

---

## Mastodon-Instanz Wahl

### Eigener Account auf bestehender Instanz
- Einfachster Start
- Empfohlene Instanzen für Bots:
  - `botsin.space` (speziell für Bots)
  - `mastodon.social` (größte Instanz)
  - Religiöse Community-Instanzen

### Eigene Instanz (Overkill für diesen Use-Case)
- Nur sinnvoll bei sehr hohem Volumen
- Erheblicher Wartungsaufwand

---

## Post-Format (Beispiel)

```
🌅 Guten Morgen! Hier kommt die Losung für den 5. Februar 2026 📖

✨ Losung (AT):
„Der HERR ist nahe allen, die ihn anrufen."
— Psalm 145,18
🔗 bibleserver.com/ELB/Psalm145,18

💫 Lehrtext (NT):
„Bittet, so wird euch gegeben."
— Matthäus 7,7
🔗 bibleserver.com/ELB/Matthäus7,7

Einen gesegneten Tag euch allen! 🙏

#Losung #Bibel #Herrnhut #Glaube #Elberfelder
```

**Zeichenlimit:** Mastodon erlaubt 500 Zeichen pro Post - das Format passt gut rein.

---

## Phase 2: Interaktions-Konzept

### Mentions-Handling
```
┌────────────────┐     ┌─────────────────┐     ┌────────────────┐
│ Polling alle   │────▶│ Neue Mentions   │────▶│ Kontext        │
│ 5 Minuten      │     │ filtern         │     │ aufbauen       │
└────────────────┘     └─────────────────┘     └───────┬────────┘
                                                       │
                                                       ▼
┌────────────────┐     ┌─────────────────┐     ┌────────────────┐
│ Antwort        │◀────│ Claude API      │◀────│ System-Prompt  │
│ posten         │     │ Anfrage         │     │ + User-Message │
└────────────────┘     └─────────────────┘     └────────────────┘
```

### Claude System-Prompt (Konzept)
```
Du bist ein freundlicher christlicher Bot, der:
- Fragen zur Bibel beantwortet
- Ermutigung und Trost spendet
- Bibelstellen empfiehlt
- Respektvoll mit anderen Glaubensrichtungen umgeht
- Keine kontroversen theologischen Debatten führt
- Auf Deutsch antwortet
```

### Rate-Limiting & Sicherheit
- Max. Antworten pro Stunde begrenzen
- Blockliste für problematische Accounts
- Keine Antwort auf sensible Themen (Politik, etc.)

---

## Projektstruktur (Vorschlag)

```
fediverse-bibel-agent/
├── src/
│   ├── __init__.py
│   ├── main.py              # Einstiegspunkt
│   ├── config.py            # Konfiguration
│   ├── mastodon_client.py   # Mastodon-Interaktion
│   ├── losungen.py          # Losungen-Service
│   ├── bible_links.py       # Bibelstellen-URLs
│   ├── scheduler.py         # Job-Scheduling
│   └── ai_responder.py      # Phase 2: Claude-Integration
├── data/
│   ├── losungen_2026.xml    # Losungen-Datei
│   └── posted.db            # SQLite: gepostete Einträge
├── tests/
│   └── ...
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── .env.example
└── README.md
```

---

## Konfiguration (.env)

```env
# Mastodon
MASTODON_INSTANCE=https://mastodon.social
MASTODON_ACCESS_TOKEN=xxx

# Scheduling
POST_TIME=06:00
TIMEZONE=Europe/Berlin

# Bibel
BIBLE_TRANSLATION=ELB
BIBLE_SERVER_BASE_URL=https://www.bibleserver.com

# Phase 2
ANTHROPIC_API_KEY=xxx
POLL_INTERVAL_MINUTES=5
MAX_REPLIES_PER_HOUR=10
```

---

## Kosten-Übersicht

| Posten | Monatliche Kosten |
|--------|-------------------|
| VPS (Hetzner CX11) | ~4€ |
| Domain (optional) | ~1€ |
| Claude API (Phase 2) | ~5-20€ (nutzungsabhängig) |
| **Gesamt Phase 1** | **~5€/Monat** |
| **Gesamt Phase 2** | **~10-25€/Monat** |

---

## Nächste Schritte

### Vor der Implementierung
1. [x] Mastodon-Account auf mastodon.social erstellen (`@losungs_bot`)
2. [ ] API-Zugang (Access Token) in Mastodon generieren
3. [ ] Losungen-Lizenz/Nutzungsbedingungen prüfen
4. [x] Hosting-Plattform auswählen (Docker beim Provider)
5. [ ] Anthropic API Key für Phase 2 besorgen
6. [ ] GitHub Secrets für CI/CD einrichten

### Implementierung Phase 1
1. [ ] Projekt-Setup (Python, Dependencies, pyproject.toml)
2. [ ] Dockerfile erstellen
3. [ ] Losungen-Parser implementieren
4. [ ] BibleServer URL-Generator (Elberfelder)
5. [ ] Mastodon-Client einrichten
6. [ ] Post-Formatierung (persönlich, mit Emojis)
7. [ ] Scheduler einrichten (täglich 6:00 Uhr)
8. [ ] GitHub Actions Workflow erstellen
9. [ ] Erstes Deployment & Test

### Implementierung Phase 2
1. [ ] Mentions-Polling
2. [ ] Claude-Integration
3. [ ] Antwort-Logik
4. [ ] Sicherheits-Features
5. [ ] Testing & Feintuning

---

## ✅ Getroffene Entscheidungen

| Aspekt | Entscheidung |
|--------|--------------|
| **Mastodon-Instanz** | `mastodon.social` |
| **Account** | `@losungs_bot@mastodon.social` |
| **Bibelquelle** | BibleServer |
| **Bibelübersetzung** | Elberfelder (ELB) |
| **Hosting** | Docker-Container beim Provider |
| **Deployment** | GitHub Actions mit automatischem Deploy |
| **Stil** | Persönlich & freundlich mit Emojis 😊 |

---

## CI/CD Pipeline (GitHub Actions)

Die Deployment-Pipeline baut das Docker-Image, pusht es zu GitHub Container Registry und triggert den Webhook beim Provider:

```yaml
# .github/workflows/deploy.yml
name: Build and Deploy

on:
  push:
    branches: [main]
  workflow_dispatch:

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Trigger Webhook
        run: |
          curl -X POST https://dashboard.dtcloud.de/v1/webhooks/native \
          -H "Content-Type: application/json" \
          -d '{"name": "ghcr.io/${{ github.repository }}", "tag": "latest"}'
```

### Keine zusätzlichen Secrets nötig! 🎉

Die Pipeline nutzt GitHub Container Registry (ghcr.io) mit dem automatisch verfügbaren `GITHUB_TOKEN`. Der Provider wird per Webhook über neue Images informiert.

---

## Offene Punkte

1. **Losungen-Lizenz**
   - [ ] Nutzungsbedingungen der Herrnhuter Brüdergemeine prüfen
   - [ ] Ggf. Genehmigung einholen

2. **Phase 2 Umfang**
   - Nur auf direkte Mentions reagieren?
   - Auch Hashtags beobachten?
