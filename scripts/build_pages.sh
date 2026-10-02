#!/usr/bin/env sh
# Refresh the GitHub Pages demo (docs/) from the app. The static demo runs engine.py in the browser via Pyodide.
cd "$(dirname "$0")/.."
mkdir -p docs
cp static/index.html docs/index.html
cp engine.py docs/engine.py
echo "docs/ updated"
