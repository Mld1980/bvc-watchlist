import re
import requests
from bs4 import BeautifulSoup
from requests.exceptions import SSLError, RequestException

BASE = "https://www.casablanca-bourse.com"

def fetch_last_price(symbol: str, timeout=15):
    url = f"{BASE}/live-market/instruments/{symbol}?pwa=1"

    try:
        r = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0"},
            verify=False  # ⚠️ important pour Streamlit Cloud
        )
        r.raise_for_status()

    except SSLError:
        return None
    except RequestException:
        return None

    soup = BeautifulSoup(r.text, "html.parser")
    text = soup.get_text(" ", strip=True)

    match = re.search(
        r"(Dernier\s+cours|Last\s+price)\s*[:\-]?\s*([0-9][0-9\s]*[.,][0-9]+)",
        text,
        re.IGNORECASE
    )

    if match:
        return _to_float(match.group(2))

    return None


def _to_float(s: str) -> float:
    s = s.replace(" ", "").replace("\u202f", "")
    if "," in s and "." not in s:
        s = s.replace(",", ".")
    return float(s)

def _to_float(s: str) -> float:
    s = s.replace(" ", "").replace("\u202f", "")
    # format FR: 1 235,00
    if "," in s and "." not in s:
        s = s.replace(",", ".")
    return float(s)
