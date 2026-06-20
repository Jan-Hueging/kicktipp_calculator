import webview
import threading
import sys
import os

# Set execution path to allow local imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Top level imports for scraper removed to avoid asyncio clash

class Api:
    def __init__(self):
        self.window = None

    def set_window(self, window):
        self.window = window

    def get_matches_from_overview(self, url):
        try:
            # Import scraper here to prevent playwright event loop from crashing the PyWebView UI thread
            from scraper import extract_matches_from_overview
            matches = extract_matches_from_overview(url, self._progress_cb)
            return {"success": True, "matches": matches}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def calculate_expected_values(self, data):
        urls = data.get("urls", [])
        try:
            pts_ex = int(data.get("pts_ex", 4))
            pts_diff = int(data.get("pts_diff", 3))
            pts_tend = int(data.get("pts_tend", 2))
        except ValueError:
            return {"success": False, "error": "Punkte müssen Zahlen sein"}

        try:
            from scraper import scrape_multiple_matches
            from calculator import normalize_odds, find_best_tips
            
            results = scrape_multiple_matches(urls, self._progress_cb)
            final_data = []
            for match in results:
                if match.get("error"):
                    final_data.append({"error": match["error"], "match_name": match.get("match_name", "Unbekannt")})
                    continue
                
                odds = match.get("odds", {})
                probs = normalize_odds(odds)
                best_tips = find_best_tips(probs, max_goals=5, pts_exact=pts_ex, pts_diff=pts_diff, pts_tend=pts_tend)
                
                final_data.append({
                    "match_name": match["match_name"],
                    "best_tips": best_tips,
                    "odds": odds
                })
            return {"success": True, "results": final_data}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _progress_cb(self, *args, **kwargs):
        if len(args) == 1:
            text = str(args[0])
        elif len(args) >= 3:
            text = f"[{args[0]}/{args[1]}] {args[2]}"
        else:
            text = "Lade..."
            
        if self.window:
            safe_text = text.replace("'", "\\'").replace('"', '\\"')
            try:
                self.window.evaluate_js(f"updateProgress('{safe_text}')")
            except Exception:
                pass

if __name__ == '__main__':
    api = Api()
    
    # Pfad zu index.html
    base_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = "file:///" + os.path.join(base_dir, 'web', 'index.html').replace('\\', '/')
    
    # window creation
    window = webview.create_window(
        'Kicktipp Expected Value Calculator', 
        url=html_path,
        js_api=api,
        width=1000,
        height=800,
        background_color='#0f172a'
    )
    api.set_window(window)
    
    # Start webview
    webview.start(debug=False)
