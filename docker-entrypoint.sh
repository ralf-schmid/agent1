#!/bin/bash
set -e

# Wenn "shell" oder "bash" als erstes Argument übergeben wird, starte eine Shell
if [ "$1" = "shell" ] || [ "$1" = "bash" ] || [ "$1" = "sh" ]; then
    exec /bin/bash
fi

# Ansonsten starte den Bot mit allen übergebenen Argumenten
exec python -m losungs_bot.main "$@"
