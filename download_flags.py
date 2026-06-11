import os
import urllib.request
from gui import COUNTRY_CODES

def download_all_flags():
    os.makedirs("flags", exist_ok=True)
    
    unique_codes = set(COUNTRY_CODES.values())
    total = len(unique_codes)
    
    print(f"Lade {total} Flaggen herunter...")
    
    for i, code in enumerate(unique_codes):
        filepath = os.path.join("flags", f"{code}.png")
        if not os.path.exists(filepath):
            try:
                url = f"https://flagcdn.com/w40/{code}.png"
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as response:
                    img_data = response.read()
                with open(filepath, "wb") as f:
                    f.write(img_data)
                print(f"[{i+1}/{total}] {code}.png heruntergeladen.")
            except Exception as e:
                print(f"[{i+1}/{total}] Fehler bei {code}.png: {e}")
        else:
            print(f"[{i+1}/{total}] {code}.png existiert bereits.")
            
    print("Download abgeschlossen!")

if __name__ == "__main__":
    download_all_flags()
