# Losungs-Bot 📖

Ein Mastodon-Bot, der täglich die Herrnhuter Losungen postet.

## Features

- 📅 **Tägliche Losung** um 06:00 Uhr mit Bibelstellen-Links
- ⛪ **Gottesdienst-Erinnerung** samstags um 17:00 Uhr
- 📖 **Bibelquiz** mittwochs um 18:00 Uhr (KI-generierte Fragen)
- 👋 **Willkommensnachricht** für neue Follower
- 🔄 **Auto-Follow-Back** mit Admin-Benachrichtigung
- 🎧 **Podcast-Links** (Apple/Spotify) in den Posts

## Installation

### Docker (empfohlen)

```bash
# Image bauen
docker build -t losungs-bot .

# Container starten
docker run -d \
  --name losungs-bot \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  losungs-bot
```

### Lokal

```bash
pip install .
losungs-bot
```

## CLI-Optionen

```bash
losungs-bot              # Dauerbetrieb (Scheduler)
losungs-bot --once       # Einmaliger Losungs-Post
losungs-bot --dry-run    # Vorschau ohne Post
losungs-bot --debug      # Debug-Logging

# Spezielle Aktionen
losungs-bot --church-reminder   # Gottesdienst-Erinnerung posten
losungs-bot --init-followers    # Follower-Liste initialisieren
losungs-bot --test-welcome      # Test-Willkommensnachricht
losungs-bot --test-quiz         # Quiz sofort posten
losungs-bot --quiz-solution     # Quiz-Auflösung posten
```

## Konfiguration

Alle Einstellungen erfolgen über Umgebungsvariablen (`.env`-Datei):

### Erforderlich

| Variable | Beschreibung | Beispiel |
|----------|--------------|----------|
| `MASTODON_ACCESS_TOKEN` | API-Token von Mastodon | `abc123...` |

### Mastodon

| Variable | Beschreibung | Default |
|----------|--------------|---------|
| `MASTODON_INSTANCE` | Mastodon-Instanz URL | `https://mastodon.social` |

### Scheduling

| Variable | Beschreibung | Default |
|----------|--------------|---------|
| `POST_TIME` | Uhrzeit für tägliche Losung | `06:00` |
| `TIMEZONE` | Zeitzone | `Europe/Berlin` |

### Bibel

| Variable | Beschreibung | Default |
|----------|--------------|---------|
| `BIBLE_TRANSLATION` | Übersetzung auf BibleServer | `ELB` |
| `BIBLE_SERVER_BASE_URL` | BibleServer URL | `https://www.bibleserver.com` |
| `LOSUNGEN_FILE` | Pfad zu Losungen-XML(s) | `data/` |

### Gottesdienst-Erinnerung

| Variable | Beschreibung | Default |
|----------|--------------|---------|
| `CHURCH_REMINDER_ENABLED` | Feature aktivieren | `true` |
| `CHURCH_REMINDER_TIME` | Uhrzeit | `17:00` |
| `CHURCH_REMINDER_DAY` | Wochentag (0=Mo, 5=Sa) | `5` |

### Follower-Interaktionen

| Variable | Beschreibung | Default |
|----------|--------------|---------|
| `AUTO_FOLLOW_BACK` | Automatisch zurückfolgen | `true` |
| `WELCOME_MESSAGE_ENABLED` | Willkommensnachricht senden | `true` |
| `FOLLOWER_CHECK_TIME` | Uhrzeit für Follower-Check | `08:00` |
| `FOLLOWER_STATE_FILE` | Pfad zur State-Datei | `data/follower_state.json` |
| `ADMIN_NOTIFY_ACCOUNT` | Account für Benachrichtigungen | - |

### Podcast-Links

| Variable | Beschreibung | Default |
|----------|--------------|---------|
| `PODCAST_APPLE` | Apple Podcasts URL | [Link](https://podcasts.apple.com/de/podcast/die-losungen/id1434728607) |
| `PODCAST_SPOTIFY` | Spotify URL | [Link](https://open.spotify.com/show/12L3SnnMI5JMDJVtQCqBxh) |

### Bibelquiz (optional)

| Variable | Beschreibung | Default |
|----------|--------------|---------|
| `QUIZ_ENABLED` | Quiz aktivieren | `false` |
| `QUIZ_DAY` | Wochentag (0=Mo, 2=Mi) | `2` |
| `QUIZ_TIME` | Uhrzeit | `18:00` |
| `QUIZ_POLL_DURATION` | Poll-Dauer in Sekunden | `86400` |
| `QUIZ_STATE_FILE` | Pfad zur State-Datei | `data/quiz_state.json` |
| `ANTHROPIC_API_KEY` | API-Key für Claude | - |

## Losungen-Daten

Die XML-Datei muss von https://www.losungen.de/download/ heruntergeladen werden.

Unterstützte Formate:
- `Losungen Free YYYY.xml`
- `LosungenYYYY.xml`

Platziere die Dateien im `data/`-Verzeichnis. Der Bot lädt automatisch alle passenden Dateien.

## Zeitplan

| Tag | Zeit | Aktion |
|-----|------|--------|
| Täglich | 06:00 | Tageslosung posten |
| Täglich | 08:00 | Neue Follower prüfen |
| Samstag | 17:00 | Gottesdienst-Erinnerung |
| Mittwoch | 18:00 | Bibelquiz posten |
| Donnerstag | 18:00 | Quiz-Auflösung |

## Copyright

Die Losungen sind urheberrechtlich geschützt:

© Evangelische Brüder-Unität – Herrnhuter Brüdergemeine
- https://www.herrnhuter.de
- https://www.losungen.de
