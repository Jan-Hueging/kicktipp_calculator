from playwright.sync_api import sync_playwright
import time
import re

def extract_matches_from_overview(url, progress_callback=None):
    """
    Scrapt eine Tipico Übersichtsseite (z.B. EM, WM, Bundesliga) und extrahiert alle Spiel-Links.
    Gibt eine Liste von Dictionaries zurück: [{"name": "Team A - Team B", "url": "https..."}]
    """
    from bs4 import BeautifulSoup
    import re
    
    if progress_callback:
        progress_callback("Lade Übersicht...")
        
    matches = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=['--window-position=-32000,-32000'])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
            page.wait_for_timeout(3000)
            
            # Cookie Banner wegklicken, falls es den Scroll blockiert
            try:
                page.locator("button:has-text('Akzeptieren'), button:has-text('Zustimmen')").click(timeout=2000)
            except:
                pass
            
            if progress_callback:
                progress_callback("Suche Spiele und klappe Listen auf...")
                
            # Mehrfach nach unten scrollen und "Mehr laden" Buttons klicken, um alle Spiele zu laden
            for _ in range(12):
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                page.wait_for_timeout(1000)
                
                # JS um den breiten Pfeil-Button (Load more) zu finden und zu klicken
                js_click_more = """
                () => {
                    let svgs = document.querySelectorAll('svg');
                    let clicked = false;
                    for (let svg of svgs) {
                        let btn = svg.closest('div[role="button"], button') || svg.parentElement;
                        let text = btn ? (btn.innerText || "").trim() : "";
                        // Der "Mehr laden" Button bei Tipico ist sehr breit (> 200px) und enthält keinen Text
                        if (btn && text.length < 5 && btn.clientWidth > 200) {
                            btn.click();
                            clicked = true;
                        }
                    }
                    return clicked;
                }
                """
                try:
                    clicked = page.evaluate(js_click_more)
                    if clicked:
                        page.wait_for_timeout(1500) # Warte auf das Nachladen der neuen Spiele
                except Exception as e:
                    print("Fehler beim Klicken:", e)
                
            html = page.content()
            soup = BeautifulSoup(html, 'html.parser')
            links = soup.find_all('a', href=re.compile(r'/event/|/teams/'))
            
            seen_urls = set()
            for a in links:
                href = a.get('href')
                if not href.startswith('http'):
                    href = 'https://sports.tipico.de' + href
                    
                # separator=" - " hilft, falls die Teams in separaten Spans sind
                text = a.get_text(separator=' - ', strip=True)
                
                if href not in seen_urls and text:
                    seen_urls.add(href)
                    matches.append({"name": text, "url": href})
                    
        except Exception as e:
            print(f"Fehler bei Übersichtsextraktion: {e}")
            
        browser.close()
        
    return matches

def scrape_multiple_matches(urls, progress_callback=None):
    """
    Öffnet die Tipico-Seite nur EINMAL und geht eine Liste von URLs durch.
    Gibt eine Liste von Dictionaries zurück:
    [{ "url": "...", "match_name": "Mexiko - Südafrika", "odds": {"1:0": 8.0, ...}, "error": None }, ...]
    """
    results = []
    
    with sync_playwright() as p:
        # Headless=False ist bei Wettanbietern extrem wichtig wegen Cloudflare.
        # Mit --window-position=-32000,-32000 öffnen wir es "unsichtbar" außerhalb des Bildschirms.
        browser = p.chromium.launch(headless=False, args=['--window-position=-32000,-32000'])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()
        
        for i, url in enumerate(urls):
            match_data = {"url": url, "match_name": f"Spiel {i+1}", "odds": {}, "error": None}
            
            if progress_callback:
                progress_callback(i + 1, len(urls), f"Lade {url[:30]}...")
                
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=35000)
                
                # Warte kurz, damit Tipico die Quotenblöcke nachlädt
                page.wait_for_timeout(3500)
                
                # Cookie Banner nur beim ersten Link wegklicken
                if i == 0:
                    try:
                        page.locator("button:has-text('Akzeptieren'), button:has-text('Zustimmen')").click(timeout=2000)
                    except:
                        pass
                
                if progress_callback:
                    progress_callback(i + 1, len(urls), "Extrahiere Quoten...")
                
                # JS Skript um Name und Quoten zu holen
                js_script = """
                () => {
                    // Versuche den Match-Namen aus dem Page-Title zu ziehen
                    // Typisch: "Mexiko - Südafrika Sportwetten Quoten | Tipico"
                    let title = document.title;
                    let name = title.split('Sportwetten')[0].split('Wetten')[0].split('|')[0].trim();
                    if (!name) name = "Unbekanntes Spiel";
                    
                    let extracted = { name: name, odds: {}, error: null };
                    
                    const allElements = document.querySelectorAll('*');
                    let header = null;
                    
                    // 1. Finde das Text-Element "Ergebnis"
                    for (const el of allElements) {
                        const text = el.textContent.trim();
                        if ((text === 'Ergebnis' || text === 'Genaues Ergebnis') && el.children.length === 0) {
                            header = el;
                            break;
                        }
                    }
                    
                    if (!header) { extracted.error = "Wettmarkt 'Genaues Ergebnis' nicht auf der Seite gefunden."; return extracted; }
                    
                    // 2. Gehe den DOM-Baum nach oben zum Haupt-Container
                    let container = header.parentElement;
                    let safeguard = 0;
                    while (container && container.querySelectorAll('button').length < 15 && safeguard < 10) {
                        container = container.parentElement;
                        safeguard++;
                    }
                    
                    if (!container) { extracted.error = "Container mit Quoten nicht gefunden."; return extracted; }
                    
                    // 3. Extrahiere Buttons
                    let buttons = container.querySelectorAll('button');
                    let regex = /^(\\d+)\\s*:\\s*(\\d+)$/; 
                    
                    for (let btn of buttons) {
                        let text = btn.innerText.trim();
                        let lines = text.split('\\n').map(l => l.trim()).filter(l => l.length > 0);
                        
                        if (lines.length >= 2) {
                            let match = lines[0].match(regex);
                            if (match) {
                                let oddVal = parseFloat(lines[lines.length - 1].replace(',', '.'));
                                if (!isNaN(oddVal)) {
                                    extracted.odds[match[1] + ':' + match[2]] = oddVal;
                                }
                            }
                        }
                    }
                    return extracted;
                }
                """
                
                res = page.evaluate(js_script)
                
                if res.get("name") and res.get("name") != "Unbekanntes Spiel":
                    match_data["match_name"] = res["name"]
                    
                if res.get("error"):
                    match_data["error"] = res["error"]
                else:
                    match_data["odds"] = res.get("odds", {})
                    
            except Exception as e:
                match_data["error"] = f"Seitenladefehler: {str(e)}"
                
            results.append(match_data)
            
        browser.close()
        
    return results

if __name__ == "__main__":
    # Test
    test_urls = [
        "https://sports.tipico.de/de/alle/fussball/europa/em-2024",
    ]
    print("Starte Batch-Test...")
    res = scrape_multiple_matches(test_urls, lambda cur, tot, msg: print(f"[{cur}/{tot}] {msg}"))
    print(res)
