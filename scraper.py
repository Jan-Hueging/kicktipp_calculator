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
            
            # WICHTIG: Tipico ändert oft das Layout und es gibt andere Märkte wie "Halbzeit Ergebnis"
            # oder Handicap-Wetten, die auch das Format "1:0" haben. Wir müssen den Block isolieren,
            # der explizit "Ergebnis" heißt. Dafür führen wir ein kleines JavaScript im Browser aus.
            
            # Warte kurz, falls dynamische Inhalte noch nachladen
            page.wait_for_timeout(4000)
            
            # Cookie-Banner wegklicken, falls vorhanden
            try:
                page.locator("button:has-text('Akzeptieren'), button:has-text('Zustimmen')").click(timeout=2000)
            except:
                pass
                
            print("Extrahiere 'Ergebnis'-Markt...")
            
            # JavaScript, das im Browser ausgeführt wird:
            js_script = """
            () => {
                const allElements = document.querySelectorAll('*');
                let header = null;
                
                // 1. Finde das Text-Element "Ergebnis"
                for (const el of allElements) {
                    const text = el.textContent.trim();
                    // Wir suchen das exakte Wort in einem Element ohne weitere HTML-Kinder
                    if ((text === 'Ergebnis' || text === 'Genaues Ergebnis') && el.children.length === 0) {
                        header = el;
                        break;
                    }
                }
                
                if (!header) return {error: "Überschrift 'Ergebnis' nicht gefunden."};
                
                // 2. Gehe den DOM-Baum nach oben, bis wir den Haupt-Container dieses Marktes finden.
                // Der Markt "Genaues Ergebnis" hat immer extrem viele Buttons (>15).
                let container = header.parentElement;
                let safeguard = 0;
                while (container && container.querySelectorAll('button').length < 15 && safeguard < 10) {
                    container = container.parentElement;
                    safeguard++;
                }
                
                if (!container) return {error: "Container mit genügend Quoten-Buttons nicht gefunden."};
                
                // 3. Extrahiere alle Buttons aus DIESEM spezifischen Container
                let buttons = container.querySelectorAll('button');
                let extractedOdds = {};
                let regex = /^(\\d+)\\s*:\\s*(\\d+)$/; // Erkennt "1:0"
                
                for (let btn of buttons) {
                    let text = btn.innerText.trim();
                    let lines = text.split('\\n').map(l => l.trim()).filter(l => l.length > 0);
                    
                    if (lines.length >= 2) {
                        let scoreLine = lines[0]; // z.B. "1:0"
                        let oddLine = lines[lines.length - 1]; // z.B. "4,40"
                        
                        let match = scoreLine.match(regex);
                        if (match) {
                            let oddVal = parseFloat(oddLine.replace(',', '.'));
                            if (!isNaN(oddVal)) {
                                extractedOdds[match[1] + ':' + match[2]] = oddVal;
                            }
                        }
                    }
                }
                return extractedOdds;
            }
            """
            
            result = page.evaluate(js_script)
            
            if "error" in result:
                print(f"[Warnung] Scraper meldet: {result['error']}")
            else:
                odds_dict = result

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
