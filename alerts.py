from datetime import datetime, timedelta
from db import get_conn
from telegram_notifier import send_telegram

def check_and_alert(symbol: str, price: float) -> str | None:
    """
    Retourne le type d'alerte déclenchée ("MIN"/"MAX") ou None.
    Applique un cooldown.
    """
    conn = get_conn()
    row = conn.execute("SELECT * FROM watchlist WHERE symbol=? AND active=1", (symbol,)).fetchone()
    if not row:
        conn.close()
        return None

    min_p = row["min_price"]
    max_p = row["max_price"]
    cooldown = int(row["cooldown_min"] or 30)

    last_time = row["last_alert_time"]
    last_dt = None
    if last_time:
        try:
            last_dt = datetime.fromisoformat(last_time)
        except Exception:
            last_dt = None

    now = datetime.now()
    if last_dt and now - last_dt < timedelta(minutes=cooldown):
        conn.close()
        return None

    alert_type = None
    if min_p is not None and price <= float(min_p):
        alert_type = "MIN"
    if max_p is not None and price >= float(max_p):
        alert_type = "MAX"

    if alert_type:
        msg = f"📣 Alerte {alert_type} | {symbol} | cours={price:.2f} MAD | seuils: min={min_p} max={max_p}"
        ok = send_telegram(msg)
        conn.execute(
            "UPDATE watchlist SET last_alert_type=?, last_alert_time=? WHERE symbol=?",
            (alert_type, now.isoformat(timespec="seconds"), symbol)
        )
        conn.execute(
            "INSERT INTO alerts_log(ts, symbol, price, alert_type, message) VALUES(?,?,?,?,?)",
            (now.isoformat(timespec="seconds"), symbol, price, alert_type, msg + ("" if ok else " (Telegram KO)"))
        )
        conn.commit()
        conn.close()
        return alert_type

    conn.close()
    return None
