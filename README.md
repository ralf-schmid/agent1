# Losungs-Bot 📖

Ein Mastodon-Bot, der täglich die Herrnhuter Losungen postet.

## Features

- ⏰ Tägliches automatisches Posten um 6:00 Uhr
- 🔗 Bibelstellen-Links zu BibleServer (Elberfelder Übersetzung)
- ✅ Copyright-konform gemäß Nutzungsbedingungen losungen.de

## Nutzung

```bash
# Dauerbetrieb (postet täglich um 6:00 Uhr)
losungs-bot

# Einmaliger Post
losungs-bot --once

# Vorschau ohne tatsächlichen Post
losungs-bot --dry-run
```

## Konfiguration

Umgebungsvariablen (`.env`):

```env
MASTODON_INSTANCE=https://mastodon.social
MASTODON_ACCESS_TOKEN=dein_token
LOSUNGEN_FILE=data/losungen.xml
```

## Losungen-Daten

Die XML-Datei der Losungen muss von https://www.losungen.de/download/ heruntergeladen und als `data/losungen.xml` gespeichert werden.

## Copyright

Die Losungen sind urheberrechtlich geschützt:

© Evangelische Brüder-Unität – Herrnhuter Brüdergemeine
- https://www.herrnhuter.de
- https://www.losungen.de
