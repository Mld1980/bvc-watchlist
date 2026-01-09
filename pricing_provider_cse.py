import re
import requests
from bs4 import BeautifulSoup

BASE = "https://www.casablanca-bourse.com"

def fetch_last_price(symbol: str, timeout=15) -> float | None:
    """
    Récupère le dernier cours (différé) depuis la page instrument Casablanca Bourse.
    Exemple: /live-market/instruments/GTM?pwa=1
    Retourne float ou None si non trouvé.
    """
    url = f"{BASE}/live-market/instruments/{symbol}?pwa=1"
    r = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
    if r.status_code != 200:
        return None

    html = r.text
    soup = BeautifulSoup(html, "html.parser")

    # 1) Tentative: chercher un pattern numérique proche de "Dernier cours" (multilingue possible)
    text = soup.get_text(" ", strip=True)

    # Ex: "Dernier cours 950,00" ou "Last price 950.00"
    m = re.search(r"(Dernier\s+cours|Last\s+price)\s*[:\-]?\s*([0-9][0-9\s]*[.,][0-9]+)", text, re.IGNORECASE)
    if m:
        return _to_float(m.group(2))

    # 2) Fallback: prendre le premier nombre "type cours" dans une zone de cotation (très tolérant)
    # (Tu peux raffiner après test réel sur 2-3 valeurs)
    m2 = re.search(r"\b([0-9][0-9\s]*[.,][0-9]+)\b", text)
    if m2:
        return _to_float(m2.group(1))

    return None

def _to_float(s: str) -> float:
    s = s.replace(" ", "").replace("\u202f", "")
    # format FR: 1 235,00
    if "," in s and "." not in s:
        s = s.replace(",", ".")
    return float(s)
