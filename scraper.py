from playwright.sync_api import sync_playwright
import time
import re

def scrape_tipico_exact_score(url):
    """
    Öffnet die Tipico-Seite, sucht nach dem Markt "Genaues Ergebnis"
    und extrahiert die Quoten.
    Gibt ein Dictionary zurück: {"1:0": 8.0, "2:1": 9.5, ...}
    """
    print(f"Starte Scraper für URL: {url}")
    odds_dict = {}
    
    with sync_playwright() as p:
        # Browser starten (headless=False hilft oft enorm gegen Cloudflare/Bot-Schutz)
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()
        
        try:
            # Tipico lädt ständig im Hintergrund nach, 'networkidle' wirft oft Fehler.
            # Daher nutzen wir 'domcontentloaded' und warten danach manuell kurz.
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            print("Seite geladen. Suche nach Quoten...")
            
            # WICHTIG: Tipico ändert oft das Layout. 
            # Wir suchen generisch nach Texten, die wie "1:0", "2:1" aussehen 
            # und versuchen den dazugehörigen Quoten-Button zu finden.
            
            # Warte kurz, falls dynamische Inhalte noch nachladen
            page.wait_for_timeout(5000)
            
            # Cookie-Banner wegklicken, falls vorhanden (Optional, oft nicht nötig für reines Lesen, aber sicherer)
            try:
                page.locator("button:has-text('Akzeptieren'), button:has-text('Zustimmen')").click(timeout=3000)
            except:
                pass
            
            # Finde alle Buttons auf der Seite, die eine Quote enthalten könnten.
            # Tipico zeigt Quoten oft in Buttons an.
            buttons = page.locator("button").all()
            
            # Wir bauen einen regulären Ausdruck, der z.B. "1:0" oder "1 : 0" erkennt
            score_pattern = re.compile(r"^\s*(\d+)\s*:\s*(\d+)\s*$")
            
            for button in buttons:
                try:
                    text = button.inner_text()
                    # Oft steht im Button Text wie "1:0\n8.50" oder ähnlich.
                    lines = text.strip().split('\n')
                    if len(lines) >= 2:
                        score_line = lines[0].strip()
                        odd_line = lines[-1].strip()
                        
                        match = score_pattern.match(score_line)
                        if match:
                            # Wir haben ein Ergebnis gefunden!
                            home_goals = match.group(1)
                            away_goals = match.group(2)
                            score_key = f"{home_goals}:{away_goals}"
                            
                            # Quote parsen (z.B. "8,50" -> 8.5)
                            try:
                                odd_val = float(odd_line.replace(',', '.'))
                                odds_dict[score_key] = odd_val
                            except ValueError:
                                continue
                except Exception as e:
                    # Manche Elemente sind nicht sichtbar etc.
                    continue

        except Exception as e:
            print(f"Fehler beim Scrapen: {e}")
        finally:
            browser.close()
            
    return odds_dict

if __name__ == "__main__":
    # Test-URL (Dieser Link muss eventuell durch einen aktuellen ersetzt werden!)
    test_url = "https://sports.tipico.de/de/alle/fussball/europa/em-2024" 
    # Normalerweise brauchen wir einen Link DIREKT zu einem Einzelspiel.
    print("Scraper Test-Modus gestartet...")
    odds = scrape_tipico_exact_score(test_url)
    print("\nGefundene Quoten:")
    for score, odd in odds.items():
        print(f"{score} -> {odd}")
    print(f"Insgesamt {len(odds)} Ergebnisse gefunden.")
