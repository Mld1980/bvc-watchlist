import os
from datetime import datetime
import streamlit as st
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from db import init_db, get_conn
from pricing_provider_cse import fetch_last_price
from alerts import check_and_alert
from telegram_notifier import send_telegram

init_db()

st.set_page_config(page_title="Suivi BVC - Watchlist", layout="wide")
st.title("📈 Bourse de Casablanca — Watchlist & Alertes (V1.1)")

with st.sidebar:
    st.subheader("⚙️ Réglages")
    refresh_min = st.number_input("Rafraîchissement (minutes)", min_value=1, max_value=60, value=5)
    if st.button("✅ Tester Telegram"):
        ok = send_telegram("Test: ton bot Telegram fonctionne ✅")
        st.success("OK" if ok else "Échec (vérifie BOT_TOKEN / CHAT_ID)")

st.divider()

# --- Form ajout/modif watchlist
st.subheader("➕ Ajouter / Modifier une action surveillée")
col1, col2, col3, col4, col5 = st.columns([1,2,1,1,1])

with col1:
    symbol = st.text_input("Symbole (ex: GTM)", value="").strip().upper()
with col2:
    name = st.text_input("Nom (optionnel)", value="")
with col3:
    min_p = st.number_input("Seuil MIN", value=0.0, step=1.0)
with col4:
    max_p = st.number_input("Seuil MAX", value=0.0, step=1.0)
with col5:
    cooldown = st.number_input("Cooldown (min)", min_value=1, max_value=1440, value=30)

c1, c2, c3 = st.columns([1,1,2])
with c1:
    save = st.button("💾 Enregistrer")
with c2:
    delete = st.button("🗑️ Supprimer")
with c3:
    st.caption("Les cours Casablanca Bourse sont généralement en différé de 15 minutes (site officiel Live Market).")

conn = get_conn()

if save and symbol:
    conn.execute("""
        INSERT INTO watchlist(symbol, name, min_price, max_price, active, cooldown_min)
        VALUES(?,?,?,?,1,?)
        ON CONFLICT(symbol) DO UPDATE SET
            name=excluded.name,
            min_price=excluded.min_price,
            max_price=excluded.max_price,
            cooldown_min=excluded.cooldown_min,
            active=1
    """, (symbol, name, float(min_p), float(max_p), int(cooldown)))
    conn.commit()
    st.success(f"{symbol} enregistré.")

if delete and symbol:
    conn.execute("DELETE FROM watchlist WHERE symbol=?", (symbol,))
    conn.commit()
    st.warning(f"{symbol} supprimé.")

st.divider()

# --- Rafraîchissement & affichage watchlist
st.subheader("👀 Watchlist (mise à jour automatique)")

rows = conn.execute("SELECT * FROM watchlist ORDER BY symbol").fetchall()

if st.button("🔄 Mettre à jour maintenant"):
    pass  # déclenche la mise à jour ci-dessous

data = []
for r in rows:
    sym = r["symbol"]
    last_price = fetch_last_price(sym)
    now = datetime.now().isoformat(timespec="seconds")

    if last_price is not None:
        conn.execute(
            "UPDATE watchlist SET last_price=?, last_update=? WHERE symbol=?",
            (float(last_price), now, sym)
        )
        conn.commit()
        alert = check_and_alert(sym, float(last_price))
    else:
        alert = None

    data.append({
        "Symbol": sym,
        "Nom": r["name"],
        "MIN": r["min_price"],
        "MAX": r["max_price"],
        "Dernier cours": last_price,
        "Dernière MAJ": now if last_price is not None else r["last_update"],
        "Alerte": alert or r["last_alert_type"],
        "Dernière alerte": r["last_alert_time"],
        "Actif": bool(r["active"]),
    })

conn.close()

st.dataframe(data, use_container_width=True)

st.caption(f"Auto-refresh conseillé: relancer la page toutes les {refresh_min} minutes (on peut ajouter un auto-refresh Streamlit ensuite).")
