# Kicktipp Expected Value Calculator

Ein Python-Tool, das Quoten von Wettanbietern (wie Tipico) ausliest und den statistisch besten Tipp (höchster Erwartungswert) für das Kicktipp-Punktesystem berechnet.

## Zielsetzung
Das Programm berechnet für alle denkbaren Spielergebnisse (0:0, 1:0, 2:1, etc.) den **Erwartungswert (Expected Value)** basierend auf:
1. Den impliziten Wahrscheinlichkeiten (abgeleitet aus Buchmacher-Quoten).
2. Den Kicktipp-Punkteregeln (z.B. 4 Punkte für exaktes Ergebnis, 3 für Tordifferenz, 2 für Tendenz).

## Architektur
- `scraper.py`: Extrahiert aktuelle Quoten für das "Genaue Ergebnis".
- `calculator.py`: Rechnet Quoten in Wahrscheinlichkeiten um und kalkuliert den Erwartungswert.
- `main.py`: Führt die Module zusammen und gibt eine sortierte Rangliste der besten Tipps aus.
