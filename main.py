import sys
from scraper import scrape_tipico_exact_score
from calculator import normalize_odds, find_best_tips

def main():
    print("="*50)
    print("   KICKTIPP EXPECTED VALUE CALCULATOR   ")
    print("="*50)
    
    # 1. URL abfragen
    url = input("\nBitte gib den direkten Tipico-Link zum Spiel ein:\n> ").strip()
    if not url:
        print("Keine URL eingegeben. Beende Programm.")
        return

    # 2. Quoten scrapen
    print("\n[1/3] Hole Quoten von Tipico...")
    odds = scrape_tipico_exact_score(url)
    
    if not odds:
        print("\n[Fehler] Es konnten keine Quoten für 'Genaues Ergebnis' gefunden werden.")
        print("Mögliche Gründe:")
        print("- Die URL war kein Einzelspiel.")
        print("- Tipico hat das Design geändert.")
        print("- Tipico blockiert den Scraper (Captcha/Cloudflare).")
        return
        
    print(f"Erfolgreich {len(odds)} Quoten extrahiert.")

    # 3. Wahrscheinlichkeiten berechnen
    print("\n[2/3] Berechne implizite Wahrscheinlichkeiten...")
    probs = normalize_odds(odds)
    
    # 4. Erwartungswert berechnen und sortieren
    print("[3/3] Berechne Erwartungswerte für Kicktipp...\n")
    best_tips = find_best_tips(probs, max_goals=5)
    
    # 5. Ausgabe
    print("="*50)
    print("   TOP 10 TIPPS NACH ERWARTUNGSWERT (PUNKTE)   ")
    print("="*50)
    for i, t in enumerate(best_tips[:10], 1):
        # Wir zeigen auch nochmal die zugrundeliegende Wahrscheinlichkeit an
        tip_str = t['tip']
        ev = t['expected_value']
        prob_percent = probs.get(tip_str, 0) * 100
        print(f"{i:2}. Tipp {tip_str:3} -> Erwartungswert: {ev:.3f} Punkte (Eintrittswahrscheinlichkeit: {prob_percent:5.2f}%)")
        
    print("\n(Hinweis: 4 Pkt Exakt, 3 Pkt Differenz, 2 Pkt Tendenz)")

if __name__ == "__main__":
    main()
