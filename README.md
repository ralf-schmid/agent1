# Losungs-Bot 📖

Ein interaktiver Mastodon-Bot, der täglich die Herrnhuter Losungen postet und auf Nachrichten reagiert.

## Profiltext für Mastodon

> 📖 Tägliche Herrnhuter Losungen für dein Fediverse!
>
> 📅 06:00 → Tageslosung
> 💭 12:00 → Reflexionsfrage
> 📖 Mi 18:00 → Bibelquiz
> ⛪ Sa 17:00 → Gottesdienst-Erinnerung
>
> 💬 Schreib mir: "hilfe", "losung", "quiz" oder eine Bibelstelle wie "Joh 3,16"
>
> 🤖 Bot von @ralf_schmid@chaos.social
> 🔗 github.com/ralf-schmid/losungs-bot

## Features

### Automatische Posts
- 📅 **Tägliche Losung** um 06:00 Uhr mit Bibelstellen-Links
- 💭 **Reflexionsfrage** um 12:00 Uhr (KI-generierter Mittagsimpuls)
- 📖 **Bibelquiz** mittwochs um 18:00 Uhr (KI-generierte Fragen als Umfrage)
- ⛪ **Gottesdienst-Erinnerung** samstags um 17:00 Uhr
- 🎧 **Podcast-Links** (Apple/Spotify) in den Posts

### Interaktive Features
- 💬 **Erwähnungen** – Reagiert auf Nachrichten mit Befehlen
- 📖 **Bibelstellen** – Generiert Links für Verse wie "Joh 3,16"
- ❓ **Quiz auf Abruf** – Startet ein persönliches Quiz
- 🎲 **Zufällige Losung** – Verse aus dem aktuellen Jahr

### Follower-Management
- 👋 **Willkommensnachricht** für neue Follower
- 🔄 **Auto-Follow-Back** mit Admin-Benachrichtigung

### Aktivitäts-Logging
- 📊 **CSV-Log** aller Bot-Aktivitäten in `data/activity_log.csv`
- Protokolliert: Losungen, Quiz, GoDi-Erinnerungen, neue Follower, Erwähnungen

## Befehle (Erwähnungen)

Schreibe dem Bot eine Nachricht mit einem der folgenden Befehle:

| Befehl | Beschreibung |
|--------|--------------|
| `hilfe` / `help` / `?` | Liste aller Befehle |
| `losung` / `heute` / `vers` | Heutige Tageslosung |
| `zufall` / `random` | Zufällige Losung aus diesem Jahr |
| `quiz` | Startet ein persönliches Bibelquiz |
| `Joh 3,16` | Link zur Bibelstelle (beliebige Bibelstelle) |

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

# Quiz-Optionen
losungs-bot --test-quiz         # Quiz sofort posten
losungs-bot --dry-run-quiz      # Quiz-Vorschau ohne Post
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

### Bibelquiz (optional, benötigt Anthropic API)

| Variable | Beschreibung | Default |
|----------|--------------|---------|
| `QUIZ_ENABLED` | Quiz aktivieren | `false` |
| `QUIZ_DAY` | Wochentag (0=Mo, 2=Mi) | `2` |
| `QUIZ_TIME` | Uhrzeit | `18:00` |
| `QUIZ_POLL_DURATION` | Poll-Dauer in Sekunden | `86400` |
| `QUIZ_STATE_FILE` | Pfad zur State-Datei | `data/quiz_state.json` |

### Reflexionsfrage (optional, benötigt Anthropic API)

| Variable | Beschreibung | Default |
|----------|--------------|---------|
| `REFLECTION_ENABLED` | Reflexionsfrage aktivieren | `false` |
| `REFLECTION_TIME` | Uhrzeit | `12:00` |

### Interaktive Features

| Variable | Beschreibung | Default |
|----------|--------------|---------|
| `MENTIONS_ENABLED` | Auf Erwähnungen reagieren | `true` |
| `MENTIONS_CHECK_INTERVAL` | Prüf-Intervall in Sekunden | `300` |
| `FAVORITES_REACTION_ENABLED` | DM bei Favorit senden | `false` |
| `NOTIFICATION_STATE_FILE` | Pfad zur State-Datei | `data/notification_state.json` |

### Anthropic API (für Quiz und Reflexion)

| Variable | Beschreibung | Default |
|----------|--------------|---------|
| `ANTHROPIC_API_KEY` | API-Key für Claude | - |

### Prometheus Metriken

| Variable | Beschreibung | Default |
|----------|--------------|---------|
| `METRICS_ENABLED` | Metriken-Endpoint aktivieren | `false` |
| `METRICS_PORT` | HTTP-Port für /metrics | `8080` |

## Prometheus Metriken

Der Bot stellt Prometheus-Metriken bereit, wenn `METRICS_ENABLED=true` gesetzt ist.

**Endpoint:** `http://localhost:8080/metrics` (bzw. konfigurierter Port)

| Metrik | Typ | Beschreibung |
|--------|-----|--------------|
| `losungsbot_posts_total` | Counter | Gesamtanzahl Posts (Labels: type) |
| `losungsbot_followers_count` | Gauge | Aktuelle Follower-Anzahl |
| `losungsbot_likes_total` | Gauge | Gesamtanzahl Likes über alle Posts |
| `losungsbot_mentions_total` | Counter | Verarbeitete Erwähnungen (Labels: command) |
| `losungsbot_uptime_seconds` | Gauge | Uptime in Sekunden |
| `losungsbot_cpu_usage_percent` | Gauge | CPU-Auslastung in % |
| `losungsbot_memory_usage_bytes` | Gauge | RAM-Nutzung in Bytes |
| `losungsbot_memory_usage_percent` | Gauge | RAM-Nutzung in % |
| `losungsbot_health_status` | Gauge | Health-Status (1=healthy, 0=unhealthy) |

**Post-Typen:** `losung`, `quiz`, `reflection`, `church_reminder`

**Command-Labels:** `help`, `verse_today`, `verse_random`, `quiz`, `verse_link`, `unknown`

### Counter-Persistenz

Die Counter-Metriken (`posts_total`, `mentions_total`) werden in `data/metrics_state.json` persistiert und beim Neustart des Bots wiederhergestellt. So bleiben die Zählerstände auch nach einem Container-Neustart erhalten.

## Aktivitäts-Log

Der Bot protokolliert alle Aktivitäten in `data/activity_log.csv` im Format:

```csv
Timestamp;Aktion;Beschreibung
2024-01-15 06:00:01;Losung gepostet;Der Herr ist mein Hirte...
2024-01-17 18:00:05;Quiz gestartet;Aus welchem Buch stammt dieser Vers?
2024-01-18 18:00:02;Quiz aufgelöst;Teilnehmer: 42, Verteilung: A: 30%, B: 20%, C: 40%, D: 10%
2024-01-20 17:00:01;GoDi-Erinnerung gesendet;Gottesdienst-Erinnerung gesendet
2024-01-21 08:15:03;Neue Mitglieder;user@mastodon.social
2024-01-21 14:30:22;Reaktion auf Erwähnungen;user@instance.social: Hilfe gesendet
```

| Aktion | Beschreibung |
|--------|--------------|
| Losung gepostet | Der Losungstext |
| GoDi-Erinnerung gesendet | (feste Beschreibung) |
| Quiz gestartet | Die Quizfrage |
| Quiz aufgelöst | Teilnehmerzahl und Antwortverteilung |
| Neue Mitglieder | Account-Name des neuen Followers |
| Reaktion auf Erwähnungen | Account und Art der Reaktion |

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
| Täglich | 12:00 | Reflexionsfrage posten |
| Alle 5 Min | - | Erwähnungen prüfen |
| Mittwoch | 18:00 | Bibelquiz posten |
| Donnerstag | 18:00 | Quiz-Auflösung |
| Samstag | 17:00 | Gottesdienst-Erinnerung |

## Copyright

Die Losungen sind urheberrechtlich geschützt:

© Evangelische Brüder-Unität – Herrnhuter Brüdergemeine
- https://www.herrnhuter.de
- https://www.losungen.de
