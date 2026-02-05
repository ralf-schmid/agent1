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
| Anbieter | URL-Format |
|----------|------------|
| BibleServer | `https://www.bibleserver.com/LUT/{Stelle}` |
| Bible Gateway | `https://www.biblegateway.com/passage/?search={Stelle}&version=LUTH1545` |
| Die-Bibel.de | `https://www.die-bibel.de/bibel/LU17/{Buch}/{Kapitel}` |

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
📖 Losung für den 5. Februar 2026

Altes Testament:
"Der HERR ist nahe allen, die ihn anrufen."
— Psalm 145,18
🔗 bibleserver.com/LUT/Psalm145,18

Neues Testament (Lehrtext):
"Bittet, so wird euch gegeben."
— Matthäus 7,7
🔗 bibleserver.com/LUT/Matthäus7,7

#Losung #Bibel #Herrnhut #Glaube
```

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
MASTODON_INSTANCE=https://botsin.space
MASTODON_ACCESS_TOKEN=xxx

# Scheduling
POST_TIME=06:00
TIMEZONE=Europe/Berlin

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
1. [ ] Mastodon-Account auf geeigneter Instanz erstellen
2. [ ] API-Zugang (Access Token) generieren
3. [ ] Losungen-Lizenz/Nutzungsbedingungen prüfen
4. [ ] VPS oder Hosting-Plattform auswählen
5. [ ] Anthropic API Key für Phase 2 besorgen

### Implementierung Phase 1
1. [ ] Projekt-Setup (Python, Dependencies)
2. [ ] Losungen-Parser implementieren
3. [ ] Mastodon-Client einrichten
4. [ ] Post-Formatierung
5. [ ] Scheduler einrichten
6. [ ] Deployment auf VPS
7. [ ] Monitoring einrichten

### Implementierung Phase 2
1. [ ] Mentions-Polling
2. [ ] Claude-Integration
3. [ ] Antwort-Logik
4. [ ] Sicherheits-Features
5. [ ] Testing & Feintuning

---

## Offene Fragen

1. **Welche Mastodon-Instanz?**
   - Eigene oder bestehende (z.B. botsin.space)?

2. **Losungen-Lizenz**
   - Kommerzielle Nutzung? Namensnennung erforderlich?

3. **Bibelübersetzung**
   - Luther 2017? Einheitsübersetzung? Elberfelder?

4. **Ton des Bots**
   - Formell oder persönlich?
   - Emojis nutzen?

5. **Phase 2 Umfang**
   - Nur auf direkte Mentions reagieren?
   - Auch Hashtags beobachten?
