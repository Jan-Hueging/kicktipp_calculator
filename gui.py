import customtkinter as ctk
import threading
from scraper import scrape_tipico_exact_score
from calculator import normalize_odds, find_best_tips

class KicktippApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Kicktipp Expected Value Calculator")
        self.geometry("550x750")
        
        # Premium Theme Configuration
        ctk.set_appearance_mode("light")
        self.configure(fg_color="#F0F3F4") # Sanftes, kühles Hellgrau als Hintergrund
        
        # Farbdefinitionen
        BEIGE_STRONG = "#E8DFD5" # Stärkeres Beige für Felder und Quoten-Kasten
        SOFT_GREEN = "#9CCB9C"   # Schwächeres, sanftes Grün für den Button
        HOVER_GREEN = "#81B581"
        
        # Header
        self.header = ctk.CTkLabel(
            self, 
            text="⚽ Kicktipp Rechner", 
            font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"), 
            text_color="#145A32" 
        )
        self.header.pack(pady=(30, 20))
        
        # Input Frame 
        self.input_frame = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=10, border_width=1, border_color="#D5DBDB")
        self.input_frame.pack(pady=10, padx=30, fill="x")
        
        self.url_label = ctk.CTkLabel(self.input_frame, text="Tipico Spiel-Link:", text_color="#2C3E50", font=ctk.CTkFont(weight="bold", size=14))
        self.url_label.pack(pady=(15, 5), padx=20, anchor="w")
        
        # Eingabefeld in starkem Beige
        self.url_entry = ctk.CTkEntry(self.input_frame, placeholder_text="https://sports.tipico.de/...", fg_color=BEIGE_STRONG, border_color="#D5DBDB", height=35, text_color="#2C3E50")
        self.url_entry.pack(pady=(0, 15), padx=20, fill="x")
        
        # Points Setting Frame
        self.points_frame = ctk.CTkFrame(self.input_frame, fg_color="transparent")
        self.points_frame.pack(pady=(0, 20), padx=20, fill="x")
        
        # Exact points
        self.lbl_ex = ctk.CTkLabel(self.points_frame, text="Exakt:", text_color="#2C3E50", font=ctk.CTkFont(weight="bold"))
        self.lbl_ex.grid(row=0, column=0, padx=(0, 5))
        self.ent_ex = ctk.CTkEntry(self.points_frame, width=45, fg_color=BEIGE_STRONG, border_color="#D5DBDB", justify="center", text_color="#2C3E50")
        self.ent_ex.insert(0, "4")
        self.ent_ex.grid(row=0, column=1, padx=(0, 15))
        
        # Diff points
        self.lbl_diff = ctk.CTkLabel(self.points_frame, text="Diff:", text_color="#2C3E50", font=ctk.CTkFont(weight="bold"))
        self.lbl_diff.grid(row=0, column=2, padx=(0, 5))
        self.ent_diff = ctk.CTkEntry(self.points_frame, width=45, fg_color=BEIGE_STRONG, border_color="#D5DBDB", justify="center", text_color="#2C3E50")
        self.ent_diff.insert(0, "3")
        self.ent_diff.grid(row=0, column=3, padx=(0, 15))
        
        # Tendency points
        self.lbl_tend = ctk.CTkLabel(self.points_frame, text="Tendenz:", text_color="#2C3E50", font=ctk.CTkFont(weight="bold"))
        self.lbl_tend.grid(row=0, column=4, padx=(0, 5))
        self.ent_tend = ctk.CTkEntry(self.points_frame, width=45, fg_color=BEIGE_STRONG, border_color="#D5DBDB", justify="center", text_color="#2C3E50")
        self.ent_tend.insert(0, "2")
        self.ent_tend.grid(row=0, column=5)
        
        # Action Button (Schwächeres Grün)
        self.calc_btn = ctk.CTkButton(
            self, 
            text="Erwartungswerte Berechnen", 
            fg_color=SOFT_GREEN, 
            hover_color=HOVER_GREEN, 
            text_color="#1A3B1A", # Dunkelgrüne Schrift für Kontrast
            font=ctk.CTkFont(weight="bold", size=16), 
            corner_radius=8,
            height=45,
            command=self.start_calculation
        )
        self.calc_btn.pack(pady=15, padx=30, fill="x")
        
        # Progress & Status
        self.progress = ctk.CTkProgressBar(self, progress_color=SOFT_GREEN, fg_color="#D5DBDB", height=8)
        self.progress.set(0)
        
        self.status_label = ctk.CTkLabel(self, text="", text_color="#7F8C8D", font=ctk.CTkFont(size=13))
        self.status_label.pack()
        
        # Results Frame
        self.results_frame = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=10, border_width=1, border_color="#D5DBDB")
        
        self.res_title = ctk.CTkLabel(self.results_frame, text="🏆 Top 3 Tipps", font=ctk.CTkFont(size=22, weight="bold"), text_color="#145A32")
        self.res_title.pack(pady=(20, 10))
        
        # 3 separate Labels für Gold, Silber, Bronze
        self.tip_labels = []
        for i in range(3):
            lbl = ctk.CTkLabel(self.results_frame, text="", font=ctk.CTkFont(size=18, family="Consolas", weight="bold"), justify="left")
            lbl.pack(pady=5, padx=20)
            self.tip_labels.append(lbl)
        
        # Odds Expander Button
        self.odds_btn = ctk.CTkButton(
            self.results_frame, 
            text="📊 Quoten überprüfen ▼", 
            fg_color="transparent", 
            hover_color="#E8DFD5", 
            text_color="#E67E22",
            font=ctk.CTkFont(weight="bold"),
            command=self.toggle_odds
        )
        self.odds_btn.pack(pady=(15, 15))
        
        # Quoten Textbox (Stärkeres Beige)
        self.odds_textbox = ctk.CTkTextbox(self.results_frame, height=140, fg_color=BEIGE_STRONG, text_color="#2C3E50", border_color="#D5DBDB", border_width=1)
        
    def toggle_odds(self):
        if self.odds_textbox.winfo_ismapped():
            self.odds_textbox.pack_forget()
            self.odds_btn.configure(text="📊 Quoten überprüfen ▼")
        else:
            self.odds_textbox.pack(pady=(0, 20), padx=20, fill="x")
            self.odds_btn.configure(text="📊 Quoten einklappen ▲")
            
    def start_calculation(self):
        url = self.url_entry.get().strip()
        if not url:
            self.status_label.configure(text="Bitte füge einen Link ein!", text_color="#E74C3C")
            return
            
        try:
            self.pts_ex = int(self.ent_ex.get())
            self.pts_diff = int(self.ent_diff.get())
            self.pts_tend = int(self.ent_tend.get())
        except ValueError:
            self.status_label.configure(text="Die Punkte müssen Zahlen sein!", text_color="#E74C3C")
            return

        # UI State Updates
        self.calc_btn.configure(state="disabled", text="Arbeite...")
        self.results_frame.pack_forget()
        self.odds_textbox.pack_forget()
        self.odds_btn.configure(text="📊 Quoten überprüfen ▼")
        
        self.progress.pack(pady=(0, 10), padx=30, fill="x")
        self.progress.start()
        self.status_label.configure(text="Browser liest Quoten aus... (ca. 5-10 Sekunden)", text_color="#7F8C8D")
        
        # Starte den Scraper in einem separaten Thread
        threading.Thread(target=self.run_scraping_logic, args=(url,), daemon=True).start()
        
    def run_scraping_logic(self, url):
        try:
            odds = scrape_tipico_exact_score(url)
            self.after(0, self.finish_calculation, odds)
        except Exception as e:
            self.after(0, self.show_error, str(e))
            
    def finish_calculation(self, odds):
        self.progress.stop()
        self.progress.pack_forget()
        self.calc_btn.configure(state="normal", text="Erwartungswerte Berechnen")
        
        if not odds or "error" in odds:
            err_msg = odds.get('error', 'Keine Quoten gefunden') if odds else 'Keine Quoten gefunden'
            self.status_label.configure(text=f"Fehler: {err_msg}", text_color="#E74C3C")
            return
            
        # Erfolgsmeldung komplett entfernen (wie vom User gewünscht)
        self.status_label.configure(text="")
        
        # Mathe-Magie
        probs = normalize_odds(odds)
        best_tips = find_best_tips(probs, max_goals=5, pts_exact=self.pts_ex, pts_diff=self.pts_diff, pts_tend=self.pts_tend)
        
        # Gold, Silber, Bronze Farben für die Top 3
        medal_colors = ["#D4AF37", "#9E9E9E", "#CD7F32"] # Gold, Silber, Bronze Hex-Codes
        medals = ["🥇", "🥈", "🥉"]
        
        for i, lbl in enumerate(self.tip_labels):
            if i < len(best_tips):
                t = best_tips[i]
                lbl.configure(
                    text=f"{medals[i]} {t['tip']:>3}   ➔   {t['expected_value']:>5.3f} Punkte",
                    text_color=medal_colors[i]
                )
        
        # Quoten-Tabelle formatieren
        self.odds_textbox.configure(state="normal")
        self.odds_textbox.delete("0.0", "end")
        sorted_odds = sorted(odds.items(), key=lambda x: (int(x[0].split(':')[0]), int(x[0].split(':')[1])))
        for score, odd in sorted_odds:
            self.odds_textbox.insert("end", f"Ergebnis {score:>4}   |   Quote: {odd:>6.2f}\n")
        self.odds_textbox.configure(state="disabled")
        
        self.results_frame.pack(pady=15, padx=30, fill="both", expand=True)
        
    def show_error(self, error_msg):
        self.progress.stop()
        self.progress.pack_forget()
        self.calc_btn.configure(state="normal", text="Erwartungswerte Berechnen")
        self.status_label.configure(text=f"Fehler aufgetreten: {error_msg}", text_color="#E74C3C")

if __name__ == "__main__":
    app = KicktippApp()
    app.mainloop()
