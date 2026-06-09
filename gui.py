import customtkinter as ctk
import threading
from scraper import scrape_multiple_matches
from calculator import normalize_odds, find_best_tips

class KicktippApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Kicktipp Expected Value Calculator")
        self.geometry("750x900")
        
        # Premium Theme Configuration
        ctk.set_appearance_mode("light")
        self.configure(fg_color="#F0F3F4")
        
        # Farbdefinitionen
        self.BEIGE_STRONG = "#E8DFD5" 
        self.SOFT_GREEN = "#9CCB9C"   
        self.HOVER_GREEN = "#81B581"
        self.TEXT_DARK = "#2C3E50"
        self.MEDAL_COLORS = ["#D4AF37", "#9E9E9E", "#CD7F32"]
        
        # Header
        self.header = ctk.CTkLabel(
            self, 
            text="⚽ Kicktipp Batch Rechner", 
            font=ctk.CTkFont(family="Segoe UI", size=26, weight="bold"), 
            text_color="#145A32" 
        )
        self.header.pack(pady=(20, 10))
        
        # --- INPUT FRAME ---
        self.input_frame = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=10, border_width=1, border_color="#D5DBDB")
        self.input_frame.pack(pady=5, padx=20, fill="x")
        
        self.url_label = ctk.CTkLabel(self.input_frame, text="Tipico Spiel-Links (einen pro Zeile):", text_color=self.TEXT_DARK, font=ctk.CTkFont(weight="bold", size=14))
        self.url_label.pack(pady=(10, 5), padx=20, anchor="w")
        
        # Textbox für mehrere Links
        self.url_textbox = ctk.CTkTextbox(self.input_frame, height=100, fg_color=self.BEIGE_STRONG, border_color="#D5DBDB", border_width=1, text_color=self.TEXT_DARK)
        self.url_textbox.pack(pady=(0, 10), padx=20, fill="x")
        
        # Points Setting Frame
        self.points_frame = ctk.CTkFrame(self.input_frame, fg_color="transparent")
        self.points_frame.pack(pady=(0, 10), padx=20, fill="x")
        
        # Exakt
        self.lbl_ex = ctk.CTkLabel(self.points_frame, text="Exakt:", text_color=self.TEXT_DARK, font=ctk.CTkFont(weight="bold"))
        self.lbl_ex.grid(row=0, column=0, padx=(0, 5))
        self.ent_ex = ctk.CTkEntry(self.points_frame, width=45, fg_color=self.BEIGE_STRONG, justify="center", text_color=self.TEXT_DARK)
        self.ent_ex.insert(0, "4")
        self.ent_ex.grid(row=0, column=1, padx=(0, 15))
        
        # Diff
        self.lbl_diff = ctk.CTkLabel(self.points_frame, text="Diff:", text_color=self.TEXT_DARK, font=ctk.CTkFont(weight="bold"))
        self.lbl_diff.grid(row=0, column=2, padx=(0, 5))
        self.ent_diff = ctk.CTkEntry(self.points_frame, width=45, fg_color=self.BEIGE_STRONG, justify="center", text_color=self.TEXT_DARK)
        self.ent_diff.insert(0, "3")
        self.ent_diff.grid(row=0, column=3, padx=(0, 15))
        
        # Tendenz
        self.lbl_tend = ctk.CTkLabel(self.points_frame, text="Tendenz:", text_color=self.TEXT_DARK, font=ctk.CTkFont(weight="bold"))
        self.lbl_tend.grid(row=0, column=4, padx=(0, 5))
        self.ent_tend = ctk.CTkEntry(self.points_frame, width=45, fg_color=self.BEIGE_STRONG, justify="center", text_color=self.TEXT_DARK)
        self.ent_tend.insert(0, "2")
        self.ent_tend.grid(row=0, column=5)
        
        # Berechnen Button
        self.calc_btn = ctk.CTkButton(
            self.input_frame, 
            text="Erwartungswerte Berechnen", 
            fg_color=self.SOFT_GREEN, hover_color=self.HOVER_GREEN, text_color="#1A3B1A", 
            font=ctk.CTkFont(weight="bold", size=16), height=40,
            command=self.start_calculation
        )
        self.calc_btn.pack(pady=10, padx=20, fill="x")
        
        # --- PROGRESS ---
        self.progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        
        self.progress = ctk.CTkProgressBar(self.progress_frame, progress_color=self.SOFT_GREEN, fg_color="#D5DBDB", height=8)
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

    def show_odds(self, match_name, odds_dict):
        # Neues Fenster für die Quoten erstellen
        popup = ctk.CTkToplevel(self)
        popup.title("Quoten überprüfen")
        popup.geometry("300x400")
        popup.configure(fg_color="#F0F3F4")
        
        # Fokus auf das neue Fenster setzen
        popup.focus()
        popup.attributes("-topmost", True)
        
        lbl = ctk.CTkLabel(popup, text=match_name, font=ctk.CTkFont(size=16, weight="bold"), text_color="#145A32")
        lbl.pack(pady=15)
        
        textbox = ctk.CTkTextbox(popup, fg_color=self.BEIGE_STRONG, text_color=self.TEXT_DARK, border_color="#D5DBDB", border_width=1)
        textbox.pack(pady=10, padx=20, fill="both", expand=True)
        
        if not odds_dict:
            textbox.insert("end", "Keine Quoten verfügbar.")
        else:
            sorted_odds = sorted(odds_dict.items(), key=lambda x: (int(x[0].split(':')[0]), int(x[0].split(':')[1])))
            for score, odd in sorted_odds:
                textbox.insert("end", f"Ergebnis {score:>4}   |   Quote: {odd:>6.2f}\n")
                
        textbox.configure(state="disabled")
        
        # Fenster schließen Button
        close_btn = ctk.CTkButton(popup, text="Schließen", fg_color=self.SOFT_GREEN, hover_color=self.HOVER_GREEN, text_color="#1A3B1A", font=ctk.CTkFont(weight="bold"), command=popup.destroy)
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
            card = ctk.CTkFrame(self.scroll_frame, fg_color="#FFFFFF", border_width=1, border_color="#D5DBDB", corner_radius=10)
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            
            # Titel
            title = ctk.CTkLabel(card, text=match.get('match_name', 'Unbekannt'), font=ctk.CTkFont(size=16, weight="bold"), text_color="#145A32", wraplength=250)
            title.pack(pady=(10, 5), padx=10)
            
            if match.get("error"):
                err_lbl = ctk.CTkLabel(card, text=match["error"], text_color="#E74C3C", wraplength=250)
                err_lbl.pack(pady=10, padx=10)
            else:
                odds = match.get("odds", {})
                probs = normalize_odds(odds)
                best_tips = find_best_tips(probs, max_goals=5, pts_exact=self.pts_ex, pts_diff=self.pts_diff, pts_tend=self.pts_tend)
                
                medals = ["🥇", "🥈", "🥉"]
                for i in range(min(3, len(best_tips))):
                    t = best_tips[i]
                    lbl = ctk.CTkLabel(
                        card, 
                        text=f"{medals[i]} {t['tip']:>3}  ➔  {t['expected_value']:>5.3f} Pkt",
                        font=ctk.CTkFont(size=14, family="Consolas", weight="bold"),
                        text_color=self.MEDAL_COLORS[i]
                    )
                    lbl.pack(pady=2)
                    
                # Odds Button mit Closure (lambda x=...: self.show_odds(x))
                btn = ctk.CTkButton(
                    card, 
                    text="📊 Quoten", 
                    fg_color="transparent", hover_color="#E8DFD5", text_color="#E67E22",
                    height=24,
                    command=lambda m=match['match_name'], o=odds: self.show_odds(m, o)
                )
                btn.pack(pady=(10, 10))
            
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
