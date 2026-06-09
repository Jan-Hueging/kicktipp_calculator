import customtkinter as ctk
import threading
from scraper import scrape_multiple_matches
from calculator import normalize_odds, find_best_tips

import urllib.request
import io
from PIL import Image

COUNTRY_CODES = {
    "Deutschland": "de", "Schottland": "gb-sct", "Ungarn": "hu", "Schweiz": "ch",
    "Spanien": "es", "Kroatien": "hr", "Italien": "it", "Albanien": "al",
    "Slowenien": "si", "Dänemark": "dk", "Serbien": "rs", "England": "gb-eng",
    "Polen": "pl", "Niederlande": "nl", "Österreich": "at", "Frankreich": "fr",
    "Belgien": "be", "Slowakei": "sk", "Rumänien": "ro", "Ukraine": "ua",
    "Türkei": "tr", "Georgien": "ge", "Portugal": "pt", "Tschechien": "cz",
    "Mexiko": "mx", "Südafrika": "za", "Südkorea": "kr", "Brasilien": "br",
    "Argentinien": "ar", "USA": "us", "Kamerun": "cm", "Japan": "jp",
    "Kanada": "ca", "Uruguay": "uy", "Kolumbien": "co", "Ecuador": "ec",
    "Chile": "cl", "Peru": "pe", "Jamaika": "jm", "Paraguay": "py",
    "Bolivien": "bo", "Venezuela": "ve", "Costa Rica": "cr", "Panama": "pa",
    "Marokko": "ma", "Senegal": "sn", "Katar": "qa", "Wales": "gb-wls",
    "Irland": "ie", "Nordirland": "gb-nir", "Island": "is", "Schweden": "se",
    "Norwegen": "no", "Finnland": "fi", "Bosnien": "ba", "Montenegro": "me",
    "Griechenland": "gr"
}

_FLAG_CACHE = {}

def get_flag_image(country_name):
    code = COUNTRY_CODES.get(country_name)
    if not code:
        return None
    if code in _FLAG_CACHE:
        return _FLAG_CACHE[code]
    try:
        url = f"https://flagcdn.com/w40/{code}.png"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as response:
            img_data = response.read()
        img = Image.open(io.BytesIO(img_data))
        ctk_img = ctk.CTkImage(light_image=img, size=(24, 18))
        _FLAG_CACHE[code] = ctk_img
        return ctk_img
    except Exception:
        return None

class KicktippApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Kicktipp Expected Value Calculator")
        self.geometry("750x700")
        
        # Premium Theme Configuration
        ctk.set_appearance_mode("light")
        self.configure(fg_color="#F2F2F7")
        
        # Apple iOS Light Mode Theme Colors
        self.BG_COLOR = "#F2F2F7"           # iOS System Hintergrund (sehr helles Grau)
        self.CARD_BG = "#FFFFFF"            # Reinweiß für Karten/Boxen
        self.TEXT_DARK = "#000000"          # Tiefschwarz für perfekten Kontrast
        self.TEXT_LIGHT = "#8E8E93"         # iOS typisches Grau für Nebentexte
        self.BORDER_COLOR = "#E5E5EA"       # Sanfte Abgrenzungen
        self.APP_BLUE = "#007AFF"           # Typisches iOS Blau
        self.APP_BLUE_HOVER = "#0051A8"     # Dunkleres Blau beim Hover
        self.APP_BLUE_DISABLED = "#99C8FF"  # Schwaches, helles Blau für deaktivierten Button
        self.GOLD = "#FFD700"
        self.SILVER = "#C0C0C0"
        self.BRONZE = "#CD7F32"
        
        # Header
        self.header = ctk.CTkLabel(
            self, 
            text="⚽ Kicktipp Batch Rechner", 
            font=ctk.CTkFont(family="Segoe UI", size=26, weight="bold"), 
            text_color=self.TEXT_DARK
        )
        self.header.pack(pady=(20, 10))
        
        # --- INPUT FRAME ---
        self.input_frame = ctk.CTkFrame(self, fg_color=self.CARD_BG, corner_radius=12, border_width=1, border_color=self.BORDER_COLOR)
        self.input_frame.pack(pady=5, padx=20, fill="x")
        
        # Modus Schalter Container
        self.mode_frame = ctk.CTkFrame(self.input_frame, fg_color="transparent")
        self.mode_frame.pack(pady=(15, 5), fill="x")
        
        self.mode_title = ctk.CTkLabel(self.mode_frame, text="Einzelne Spiele", text_color=self.TEXT_DARK, font=ctk.CTkFont(weight="bold", size=15))
        self.mode_title.pack(anchor="center")
        
        self.mode_var = ctk.StringVar(value="einzel")
        self.mode_switch = ctk.CTkSwitch(
            self.mode_frame, 
            text="", 
            width=36,
            switch_width=36,
            command=self._on_mode_switch,
            variable=self.mode_var,
            onvalue="uebersicht",
            offvalue="einzel",
            progress_color=self.BORDER_COLOR, # Grau statt Blau, da kein Ein/Aus Zustand
        )
        self.mode_switch.pack(pady=5, anchor="center")
        
        self.url_label = ctk.CTkLabel(self.input_frame, text="Einzelne Spiel-Links hier einfügen:", text_color=self.TEXT_DARK, font=ctk.CTkFont(size=13))
        self.url_label.pack(pady=(5, 5), padx=20, anchor="w")
        
        # Textbox für mehrere Links
        self.url_textbox = ctk.CTkTextbox(self.input_frame, height=100, fg_color=self.CARD_BG, border_color=self.BORDER_COLOR, border_width=1, text_color=self.TEXT_DARK)
        self.url_textbox.pack(pady=(0, 10), padx=20, fill="x")
        self.url_textbox.bind("<Control-v>", self._on_paste)
        self.url_textbox.bind("<KeyRelease>", self._check_input)
        
        # Points Setting Frame
        self.points_frame = ctk.CTkFrame(self.input_frame, fg_color="transparent")
        self.points_frame.pack(pady=(0, 10), padx=20, fill="x")
        
        # Exakt
        self.lbl_ex = ctk.CTkLabel(self.points_frame, text="Exakt:", text_color=self.TEXT_DARK, font=ctk.CTkFont(weight="bold"))
        self.lbl_ex.grid(row=0, column=0, padx=(0, 5))
        self.ent_ex = ctk.CTkEntry(self.points_frame, width=45, fg_color=self.CARD_BG, justify="center", border_color=self.BORDER_COLOR, text_color=self.TEXT_DARK)
        self.ent_ex.insert(0, "4")
        self.ent_ex.grid(row=0, column=1, padx=(0, 15))
        
        # Diff
        self.lbl_diff = ctk.CTkLabel(self.points_frame, text="Diff:", text_color=self.TEXT_DARK, font=ctk.CTkFont(weight="bold"))
        self.lbl_diff.grid(row=0, column=2, padx=(0, 5))
        self.ent_diff = ctk.CTkEntry(self.points_frame, width=45, fg_color=self.CARD_BG, justify="center", border_color=self.BORDER_COLOR, text_color=self.TEXT_DARK)
        self.ent_diff.insert(0, "3")
        self.ent_diff.grid(row=0, column=3, padx=(0, 15))
        
        # Tendenz
        self.lbl_tend = ctk.CTkLabel(self.points_frame, text="Tendenz:", text_color=self.TEXT_DARK, font=ctk.CTkFont(weight="bold"))
        self.lbl_tend.grid(row=0, column=4, padx=(0, 5))
        self.ent_tend = ctk.CTkEntry(self.points_frame, width=45, fg_color=self.CARD_BG, justify="center", border_color=self.BORDER_COLOR, text_color=self.TEXT_DARK)
        self.ent_tend.insert(0, "2")
        self.ent_tend.grid(row=0, column=5)
        
        # Berechnen Button
        self.calc_btn = ctk.CTkButton(
            self.input_frame, 
            text="Start", 
            state="disabled",
            fg_color=self.APP_BLUE_DISABLED, hover_color=self.APP_BLUE_HOVER, text_color="#FFFFFF", 
            font=ctk.CTkFont(weight="bold", size=16), height=42, corner_radius=8,
            command=self._on_calc_btn_click
        )
        self.calc_btn.pack(pady=15, padx=20, fill="x")
        
        # --- PROGRESS ---
        self.progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        
        self.progress = ctk.CTkProgressBar(self.progress_frame, progress_color=self.APP_BLUE, fg_color=self.BORDER_COLOR, height=8)
        self.progress.pack(pady=(5, 0), fill="x")
        self.progress.set(0)
        
        self.status_label = ctk.CTkLabel(self.progress_frame, text="", text_color="#7F8C8D", font=ctk.CTkFont(size=13))
        self.status_label.pack()
        
        # --- RESULTS AREA ---
        # Scrollable Frame für alle Spiele (2 Spalten Layout)
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.grid_columnconfigure(0, weight=1)
        self.scroll_frame.grid_columnconfigure(1, weight=1)
        
        # Die Quoten werden jetzt in einem separaten Pop-Up Fenster angezeigt.
        
    def get_urls(self):
        text = self.url_textbox.get("0.0", "end").strip()
        lines = [line.strip() for line in text.split('\n') if line.strip().startswith("http")]
        return lines

    def _on_mode_switch(self):
        if self.mode_var.get() == "uebersicht":
            self.mode_title.configure(text="Turnier/Liga-Übersicht")
            self.url_label.configure(text="Einen Übersichts-Link einfügen:")
            self.calc_btn.configure(text="Start")
        else:
            self.mode_title.configure(text="Einzelne Spiele")
            self.url_label.configure(text="Einzelne Spiel-Links hier einfügen:")
            self.calc_btn.configure(text="Start")
            
    def _on_calc_btn_click(self):
        urls = self.get_urls()
        if not urls:
            return
            
        # Nimm den ersten Link zur Prüfung
        url = urls[0]
        mode = self.mode_var.get()
        
        # Ein direkter Spiel-Link hat in der Regel /event/ oder /teams/ in der URL
        is_match_link = '/event/' in url or '/teams/' in url
        
        # Falscher Modus: Einzelspiel im Übersichts-Modus
        if mode == "uebersicht" and is_match_link:
            self.show_error("Falscher Modus! Das ist ein Link für ein einzelnes Spiel.\\nBitte stelle den Schalter oben auf 'Einzelne Spiele'.")
            return
            
        # Falscher Modus: Übersicht im Einzelspiel-Modus
        if mode == "einzel" and not is_match_link:
            self.show_error("Falscher Modus! Das ist ein Link zu einer Turnier/Liga-Übersicht.\\nBitte stelle den Schalter oben auf 'Turnier/Liga-Übersicht'.")
            return
            
        if mode == "uebersicht":
            self.open_selection_popup()
        else:
            self.start_calculation()

    def _on_paste(self, event=None):
        try:
            clip = self.clipboard_get()
            if clip:
                self.url_textbox.insert("insert", clip)
                if not clip.endswith('\n') and not clip.endswith('\r'):
                    self.url_textbox.insert("insert", "\n")
                self.url_textbox.see("insert")
                self.after(10, self._check_input)
        except Exception:
            pass
        return "break"
        
    def _check_input(self, event=None):
        # Enable start button only if there is text in the textbox
        text = self.url_textbox.get("0.0", "end").strip()
        if len(text) > 5:
            self.calc_btn.configure(state="normal", fg_color=self.APP_BLUE)
        else:
            self.calc_btn.configure(state="disabled", fg_color=self.APP_BLUE_DISABLED)

    def open_selection_popup(self):
        urls = self.get_urls()
        if not urls:
            self.show_error("Bitte einen Übersichts-Link einfügen.")
            return
            
        url = urls[0] # Nimm den ersten Link
        
        self.calc_btn.configure(state="disabled", text="Lade Spiele...", fg_color=self.APP_BLUE_DISABLED)
        
        self.progress_frame.pack(pady=5, padx=20, fill="x")
        self.progress.configure(mode="indeterminate")
        self.progress.start()
        self.status_label.configure(text="Lade Übersicht und suche Spiele...")
        
        import threading
        threading.Thread(target=self._run_extraction_thread, args=(url,), daemon=True).start()
        
    def _run_extraction_thread(self, url):
        import scraper
        def _prog_cb(msg):
            self.after(0, lambda: self.status_label.configure(text=msg))
            
        matches = scraper.extract_matches_from_overview(url, _prog_cb)
        self.after(0, self._on_extraction_done, matches)
        
    def _on_extraction_done(self, matches):
        self.progress.stop()
        self.progress_frame.pack_forget()
        self.calc_btn.configure(state="normal", text="Start", fg_color=self.APP_BLUE)
        
        if not matches:
            self.show_error("Keine Spiele gefunden. Bitte gültigen Link prüfen.")
            return
            
        self._show_selection_popup(matches)
        
    def _show_selection_popup(self, matches):
        popup = ctk.CTkToplevel(self)
        popup.title(f"{len(matches)} Spiele gefunden")
        popup.geometry("500x600")
        popup.configure(fg_color="#F2F2F7")
        popup.focus()
        popup.attributes("-topmost", True)
        
        lbl = ctk.CTkLabel(popup, text="Welche Spiele möchtest du berechnen?", font=ctk.CTkFont(size=16, weight="bold"), text_color=self.TEXT_DARK)
        lbl.pack(pady=15)
        
        sf = ctk.CTkScrollableFrame(popup, fg_color="#FFFFFF", border_color=self.BORDER_COLOR, border_width=1, corner_radius=12)
        sf.pack(pady=10, padx=20, fill="both", expand=True)
        
        checkboxes = []
        for match in matches:
            cb = ctk.CTkCheckBox(sf, text=match['name'], text_color=self.TEXT_DARK, font=ctk.CTkFont(size=14))
            cb.pack(pady=8, padx=10, anchor="w")
            checkboxes.append((cb, match['url']))
            
        def on_confirm():
            selected_urls = [url for cb, url in checkboxes if cb.get() == 1]
            if not selected_urls:
                # Kein Spiel ausgewählt, nichts tun
                return
            
            popup.destroy()
            
            # Alle ausgewählten URLs in das Textfeld schreiben
            self.url_textbox.delete("0.0", "end")
            for u in selected_urls:
                self.url_textbox.insert("end", u + "\n")
                
            # Zurück auf Einzel-Modus stellen für das finale Berechnen
            self.mode_var.set("einzel")
            self._on_mode_switch()
            
            # Sofort berechnen
            self.start_calculation()
            
        confirm_btn = ctk.CTkButton(
            popup, text=f"Auswahl berechnen", 
            fg_color=self.APP_BLUE, hover_color=self.APP_BLUE_HOVER, text_color="#FFFFFF", 
            font=ctk.CTkFont(weight="bold", size=16), height=42, corner_radius=8,
            command=on_confirm
        )
        confirm_btn.pack(pady=20, padx=20, fill="x")

    def show_odds(self, match_name, odds_dict):
        # Neues Fenster für die Quoten erstellen
        popup = ctk.CTkToplevel(self)
        popup.title("Quoten überprüfen")
        popup.geometry("300x400")
        popup.configure(fg_color="#F2F2F7") # iOS background
        
        # Fokus auf das neue Fenster setzen
        popup.focus()
        popup.attributes("-topmost", True)
        
        lbl = ctk.CTkLabel(popup, text=match_name, font=ctk.CTkFont(size=16, weight="bold"), text_color=self.TEXT_DARK)
        lbl.pack(pady=15)
        
        textbox = ctk.CTkTextbox(popup, fg_color=self.CARD_BG, text_color=self.TEXT_DARK, border_color=self.BORDER_COLOR, border_width=1)
        textbox.pack(pady=10, padx=20, fill="both", expand=True)
        
        if not odds_dict:
            textbox.insert("end", "Keine Quoten verfügbar.")
        else:
            # Sortiere nach der Höhe der Quote (aufsteigend)
            sorted_odds = sorted(odds_dict.items(), key=lambda x: float(x[1]))
            for score, odd in sorted_odds:
                textbox.insert("end", f"Ergebnis {score:>4}   |   Quote: {odd:>6.2f}\n")
                
        textbox.configure(state="disabled")
        
        # Fenster schließen Button
        close_btn = ctk.CTkButton(
            popup, text="Schließen", 
            fg_color="#FFFFFF", hover_color=self.BORDER_COLOR, text_color=self.APP_BLUE, 
            font=ctk.CTkFont(weight="bold", size=14), corner_radius=8,
            command=popup.destroy
        )
        close_btn.pack(pady=(0, 20), padx=20)

    def start_calculation(self):
        urls = self.get_urls()
        if not urls:
            self.status_label.configure(text="Keine gültigen Links gefunden!", text_color="#E74C3C")
            self.progress_frame.pack(pady=5, padx=20, fill="x")
            return
            
        try:
            self.pts_ex = int(self.ent_ex.get())
            self.pts_diff = int(self.ent_diff.get())
            self.pts_tend = int(self.ent_tend.get())
        except ValueError:
            self.status_label.configure(text="Die Punkte müssen Zahlen sein!", text_color="#E74C3C")
            self.progress_frame.pack(pady=5, padx=20, fill="x")
            return

        # UI Reset
        self.calc_btn.configure(state="disabled", text="Arbeite...")
        self.scroll_frame.pack_forget()
        
        # Clear old result cards
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
            
        self.progress_frame.pack(pady=5, padx=20, fill="x")
        self.progress.start()
        self.status_label.configure(text="Starte Browser...", text_color="#7F8C8D")
        
        threading.Thread(target=self.run_scraping_logic, args=(urls,), daemon=True).start()
        
    def progress_callback(self, current, total, message):
        # Update aus dem Thread
        self.after(0, lambda: self.status_label.configure(text=f"[{current}/{total}] {message}"))
        
    def run_scraping_logic(self, urls):
        try:
            results = scrape_multiple_matches(urls, self.progress_callback)
            self.after(0, self.finish_calculation, results)
        except Exception as e:
            self.after(0, self.show_error, str(e))
            
    def finish_calculation(self, results):
        self.progress.stop()
        self.progress_frame.pack_forget()
        self.calc_btn.configure(state="normal", text="Erwartungswerte Berechnen")
        
        if not results:
            self.show_error("Keine Ergebnisse zurückgegeben.")
            return
            
        self.scroll_frame.pack(side="top", pady=10, padx=20, fill="both", expand=True)
        # Die Quoten-Box bleibt unsichtbar, bis ein Quoten-Button geklickt wird!
        
        # Build Cards in Grid
        col = 0
        row = 0
        
        for match in results:
            card = ctk.CTkFrame(self.scroll_frame, fg_color=self.CARD_BG, border_width=1, border_color=self.BORDER_COLOR, corner_radius=12)
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nwe")
            
            # Titel Container
            raw_name = match.get('match_name', 'Unbekannt')
            title_frame = ctk.CTkFrame(card, fg_color="transparent")
            title_frame.pack(pady=(15, 10), padx=15)
            
            teams = raw_name.replace(" vs ", " - ").split(" - ")
            
            for idx, t_name in enumerate(teams):
                t_name = t_name.strip()
                flag_img = get_flag_image(t_name)
                
                if flag_img:
                    lbl = ctk.CTkLabel(title_frame, text=f" {t_name}", image=flag_img, compound="left", font=ctk.CTkFont(size=17, weight="bold"), text_color=self.TEXT_DARK)
                else:
                    lbl = ctk.CTkLabel(title_frame, text=t_name, font=ctk.CTkFont(size=17, weight="bold"), text_color=self.TEXT_DARK)
                lbl.pack(side="left")
                
                if idx < len(teams) - 1:
                    sep = ctk.CTkLabel(title_frame, text=" - ", font=ctk.CTkFont(size=17, weight="bold"), text_color=self.TEXT_MUTED)
                    sep.pack(side="left", padx=5)
                    
            # Divider Line
            divider = ctk.CTkFrame(card, height=1, fg_color=self.BORDER_COLOR)
            divider.pack(fill="x", padx=15, pady=(0, 10))
            
            if match.get("error"):
                err_lbl = ctk.CTkLabel(card, text=match["error"], text_color="#FF3B30", wraplength=250)
                err_lbl.pack(pady=10, padx=15)
            else:
                odds = match.get("odds", {})
                probs = normalize_odds(odds)
                best_tips = find_best_tips(probs, max_goals=5, pts_exact=self.pts_ex, pts_diff=self.pts_diff, pts_tend=self.pts_tend)
                
                medals = ["🥇", "🥈", "🥉"]
                
                # Container for the tips to manage alignment
                tips_container = ctk.CTkFrame(card, fg_color="transparent")
                tips_container.pack(fill="x", padx=15, pady=(5, 10))
                
                for i in range(min(3, len(best_tips))):
                    t = best_tips[i]
                    left_text = f"{medals[i]}  {t['tip']}"
                    right_text = f"➔  {t['expected_value']:.3f} Pkt"
                    
                    if i == 0:
                        # Light Blue Background and Gold Text for Winner
                        row_frame = ctk.CTkFrame(tips_container, fg_color=self.WINNER_BG, corner_radius=8)
                        row_frame.pack(fill="x", pady=(0, 6))
                        
                        lbl_left = ctk.CTkLabel(row_frame, text=left_text, font=ctk.CTkFont(size=16, weight="bold"), text_color=self.MEDAL_COLORS[i])
                        lbl_left.pack(side="left", padx=15, pady=8)
                        
                        lbl_right = ctk.CTkLabel(row_frame, text=right_text, font=ctk.CTkFont(size=16, weight="bold"), text_color=self.MEDAL_COLORS[i])
                        lbl_right.pack(side="right", padx=15, pady=8)
                    else:
                        row_frame = ctk.CTkFrame(tips_container, fg_color="transparent")
                        row_frame.pack(fill="x", pady=2)
                        
                        lbl_left = ctk.CTkLabel(row_frame, text=left_text, font=ctk.CTkFont(size=15, weight="bold"), text_color=self.MEDAL_COLORS[i])
                        lbl_left.pack(side="left", padx=15, pady=4)
                        
                        lbl_right = ctk.CTkLabel(row_frame, text=right_text, font=ctk.CTkFont(size=15, weight="bold"), text_color=self.TEXT_MUTED)
                        lbl_right.pack(side="right", padx=15, pady=4)
                    
                # Apple Style: Gray button with Blue text
                btn = ctk.CTkButton(
                    card, 
                    text="📊 Quoten", 
                    fg_color="#F2F2F7", hover_color=self.BORDER_COLOR, text_color=self.APP_BLUE,
                    font=ctk.CTkFont(weight="bold", size=14),
                    height=32, corner_radius=8,
                    command=lambda m=match['match_name'], o=odds: self.show_odds(m, o)
                )
                btn.pack(pady=(5, 15), padx=15, fill="x")
            
            # Grid Progression
            col += 1
            if col > 1:
                col = 0
                row += 1
                
    def show_error(self, error_msg):
        self.progress.stop()
        self.progress_frame.pack_forget()
        self.calc_btn.configure(state="normal", text="Erwartungswerte Berechnen")
        
        # Zeige Fehler temporär oben
        self.status_label.configure(text=f"Kritischer Fehler: {error_msg}", text_color="#E74C3C")
        self.progress_frame.pack(pady=5, padx=20, fill="x")

if __name__ == "__main__":
    app = KicktippApp()
    app.mainloop()
