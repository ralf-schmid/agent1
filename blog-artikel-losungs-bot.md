# Mein erster Mastodon-Bot: Tägliche Losungen im Fediverse

Ich habe meinen ersten Bot für Mastodon gebaut – und dabei mehr gelernt, als ich erwartet hatte. In diesem Artikel teile ich meine Erfahrungen: Von der Idee über die ersten Iterationen bis hin zu einem interaktiven Bot, der täglich Bibelverse postet und auf Nachrichten reagiert.

## Ein Bot braucht eine Aufgabe

Bevor man mit dem Programmieren beginnt, steht die wichtigste Frage: **Was soll der Bot eigentlich tun?**

Ein Bot ohne klare Aufgabe ist wie ein Werkzeug ohne Zweck. Die besten Bots lösen ein konkretes Problem oder bieten einen echten Mehrwert für ihre Follower. Sie sollten:

- **Regelmäßig** relevante Inhalte liefern
- **Zuverlässig** funktionieren (niemand mag einen Bot, der ständig offline ist)
- **Respektvoll** mit der Community umgehen (kein Spam, sinnvolle Interaktionen)

## Warum Losungen und Bibelverse?

Die [Herrnhuter Losungen](https://www.losungen.de) gibt es seit über 290 Jahren. Jeden Tag werden zwei Bibelverse ausgewählt – ein alttestamentlicher "Losungsvers" und ein neutestamentlicher "Lehrtext". Für viele Menschen gehören sie zum Tagesstart dazu.

Das macht sie zur perfekten Bot-Aufgabe:

- **Täglicher Rhythmus** – jeden Tag neuer, relevanter Inhalt
- **Klarer Mehrwert** – Follower bekommen die Losung direkt in ihre Timeline
- **Bestehende Daten** – die XML-Dateien sind frei verfügbar
- **Erweiterbar** – Links zu Bibelservern, Podcasts, Quiz-Fragen...

## Von einfach zu interaktiv: Die Iterationen

### Iteration 1: Der einfache Poster

Die erste Version war simpel: Einmal täglich die Losung posten. Der Kern besteht aus wenigen Zeilen:

```python
from mastodon import Mastodon

client = Mastodon(
    access_token="dein_token",
    api_base_url="https://mastodon.social"
)

# Losung formatieren und posten
post = f"""📖 Die Losungen – {datum}

✨ „{losungstext}"
— {losungsvers}

#losung #DieLosungen #Bibel"""

client.status_post(post)
```

Das funktionierte – aber es fühlte sich einseitig an.

### Iteration 2: Links und Kontext

Der nächste Schritt: Mehr Kontext bieten. Ich ergänzte Links zu [BibleServer](https://www.bibleserver.com), damit Leser den Vers im Zusammenhang lesen können:

```python
def generate_bible_url(reference: str) -> str:
    """Generiert einen BibleServer-Link für eine Bibelstelle."""
    # "Johannes 3,16" -> "ELB/Johannes3,16"
    book, chapter_verse = reference.rsplit(" ", 1)
    return f"https://www.bibleserver.com/ELB/{book}{chapter_verse}"
```

### Iteration 3: Interaktion

Der eigentliche Gamechanger: Der Bot reagiert auf Erwähnungen. Schreibt jemand "hilfe", antwortet er mit einer Übersicht. Bei "Joh 3,16" generiert er einen Link zur Bibelstelle.

```python
# Befehle mit Priorität – spezifische zuerst
COMMANDS = [
    ("zufall", "verse_random"),
    ("quiz", "quiz"),
    ("hilfe", "help"),
    ("losung", "verse_today"),
]

def detect_command(content: str) -> str | None:
    """Erkennt Befehle im Text."""
    for keyword, command in COMMANDS:
        if keyword in content.lower():
            return command
    return None
```

### Iteration 4: KI-generierte Inhalte

Mit der Anthropic API kam die nächste Stufe: Der Bot generiert jetzt täglich eine Reflexionsfrage zur Losung und erstellt mittwochs ein Bibelquiz mit Umfrage-Funktion:

```python
quiz_prompt = f"""Erstelle eine Quiz-Frage zur Bibelstelle:
Text: "{losungstext}"

Die Frage kann nach dem Buch, Verfasser oder historischen
Kontext fragen. Erstelle 4 Antwortmöglichkeiten."""
```

## Was der Bot heute kann

Nach mehreren Iterationen ist aus dem einfachen Poster ein vollwertiger interaktiver Bot geworden:

| Zeit | Aktion |
|------|--------|
| 06:00 | Tageslosung posten |
| 12:00 | KI-generierte Reflexionsfrage |
| Mi 18:00 | Bibelquiz mit Umfrage |
| Sa 17:00 | Gottesdienst-Erinnerung |

Dazu kommen interaktive Features:
- Antwort auf Befehle ("hilfe", "losung", "zufall", "quiz")
- Bibelstellen-Links auf Anfrage ("Joh 3,16")
- Willkommensnachricht für neue Follower
- Aktivitäts-Logging aller Aktionen

## Technische Details

Der Bot läuft als Python-Anwendung mit folgenden Komponenten:

- **[Mastodon.py](https://github.com/halcy/Mastodon.py)** – Python-Wrapper für die Mastodon API
- **APScheduler** – Zeitgesteuerte Aufgaben
- **Anthropic API** – KI-generierte Inhalte (Quiz, Reflexionen)
- **structlog** – Strukturiertes Logging

Der gesamte Code ist Open Source und auf GitHub verfügbar:

👉 **[github.com/ralf-schmid/losungs-bot](https://github.com/ralf-schmid/losungs-bot)**

## Mitmachen!

Wenn du täglich die Losungen in deiner Mastodon-Timeline haben möchtest, folge dem Bot:

📖 **[@losungen@mastodon.social](https://mastodon.social/@losungen)**

Du kannst ihm auch direkt schreiben:
- `hilfe` – Was kann der Bot?
- `losung` – Heutige Losung
- `zufall` – Zufälliger Vers aus diesem Jahr
- `quiz` – Starte ein persönliches Quiz
- `Joh 3,16` – Link zu einer Bibelstelle

## Vibe-Coding mit Claude Code

Eine Sache muss ich noch erwähnen: Dieses Projekt wäre ohne **Claude Code** nicht so entstanden. Was ist "Vibe-Coding"? Es ist diese neue Art der Softwareentwicklung, bei der man mit einer KI im Dialog programmiert – weniger wie klassisches Coding, mehr wie ein Gespräch mit einem erfahrenen Entwickler-Kollegen.

### Wie funktioniert das konkret?

Statt stundenlang Dokumentation zu lesen oder Stack Overflow zu durchforsten, beschreibe ich einfach, was ich bauen will:

> "Ich möchte einen Mastodon-Bot, der täglich die Herrnhuter Losungen postet."

Claude Code versteht den Kontext, schlägt eine Architektur vor, schreibt den Code – und ich kann in Echtzeit Feedback geben, Richtungen korrigieren oder neue Features anfragen.

### Was macht es so besonders?

- **Schnelle Iterationen** – Von der Idee zum funktionierenden Feature in Minuten statt Stunden
- **Pair-Programming-Gefühl** – Man ist nicht allein, sondern hat einen Sparringspartner
- **Lernen nebenbei** – Claude erklärt, warum bestimmte Lösungen besser sind
- **Fokus auf das Wesentliche** – Weniger Boilerplate, mehr Produktivität

### Ein Beispiel aus diesem Projekt

Als ich das CSV-Logging für Bot-Aktivitäten einbauen wollte, habe ich einfach beschrieben, welche Spalten ich brauche und welche Aktionen geloggt werden sollen. Innerhalb von Minuten hatte ich:

- Einen `ActivityLogger` mit CSV-Export
- Schutz gegen CSV-Injection (Sicherheit!)
- Integration in alle relevanten Bot-Komponenten
- Vollständige Tests

Das Beste daran: Ich musste nicht jede Zeile selbst tippen, konnte mich aber trotzdem auf die Architektur und die Details konzentrieren, die mir wichtig waren.

### Mein Fazit zum Vibe-Coding

Es macht einfach **unglaublich viel Spaß**. Die Barriere zwischen "Idee haben" und "Feature ist live" wird so niedrig wie nie zuvor. Man kann experimentieren, schnell Prototypen bauen und sich auf die kreativen Aspekte der Softwareentwicklung konzentrieren.

Für Hobby-Projekte wie diesen Bot ist es perfekt. Aber auch im professionellen Kontext sehe ich enormes Potenzial – nicht als Ersatz für Entwickler, sondern als Werkzeug, das uns produktiver und kreativer macht.

## Fazit

Ein Bot zu bauen ist mehr als nur Code schreiben. Es geht darum, einen echten Mehrwert zu schaffen – und dabei iterativ zu lernen. Mein Losungs-Bot hat sich von einem simplen Poster zu einem interaktiven Begleiter entwickelt.

Die wichtigste Lektion: **Starte einfach, iteriere oft.** Die erste Version muss nicht perfekt sein. Wichtig ist, dass sie funktioniert – alles andere kommt mit der Zeit.

---

*Hast du Fragen oder Feedback? Schreib mir auf Mastodon: [@ralf_schmid@chaos.social](https://chaos.social/@ralf_schmid)*
