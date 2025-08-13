import os
import time
import json
import math
import pytz
import requests
import statistics
from datetime import datetime, timezone
from typing import List, Tuple, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

TZ = pytz.timezone("Asia/Jakarta")

BINANCE_ENDPOINT = "https://api.binance.com/api/v3/klines"
TELEGRAM_ENDPOINT = "https://api.telegram.org"

def env(name: str, default: Optional[str] = None) -> str:
    v = os.getenv(name)
    if v is None or v == "":
        return default
    return v

def fetch_klines(symbol: str, interval: str, limit: int = 120) -> List[Tuple[int, float]]:
    """Return list of (close_time_ms, close_price_float)."""
    url = BINANCE_ENDPOINT
    params = {"symbol": symbol.upper(), "interval": interval, "limit": limit}
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()
    closes = []
    for row in data:
        # row: [ open_time, open, high, low, close, volume, close_time, ... ]
        close_time = int(row[6])
        close_price = float(row[4])
        closes.append((close_time, close_price))
    return closes

def ma(values: List[float], period: int = 7) -> List[Optional[float]]:
    out: List[Optional[float]] = []
    window: List[float] = []
    for v in values:
        window.append(v)
        if len(window) > period:
            window.pop(0)
        if len(window) == period:
            out.append(sum(window) / period)
        else:
            out.append(None)
    return out

def cross_signal(prices: List[float], ma_values: List[Optional[float]]) -> Optional[str]:
    """Return 'CROSS_UP' or 'CROSS_DOWN' if crossing happened on the last candle."""
    if len(prices) < 2 or len(ma_values) < 2:
        return None
    p_prev, p_last = prices[-2], prices[-1]
    m_prev, m_last = ma_values[-2], ma_values[-1]
    if m_prev is None or m_last is None:
        return None
    was_above = p_prev > m_prev
    now_above = p_last > m_last
    if (not was_above) and now_above:
        return "CROSS_UP"
    if was_above and (not now_above):
        return "CROSS_DOWN"
    return None

def fmt_jkt(ts_ms: int) -> str:
    dt = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).astimezone(TZ)
    return dt.strftime("%Y-%m-%d %H:%M:%S %Z")

def send_telegram(token: str, chat_id: str, text: str) -> None:
    url = f"{TELEGRAM_ENDPOINT}/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    r = requests.post(url, json=payload, timeout=20)
    if r.status_code >= 400:
        raise RuntimeError(f"Telegram error {r.status_code}: {r.text}")

def main():
    token = env("TELEGRAM_BOT_TOKEN")
    chat_id = env("TELEGRAM_CHAT_ID")
    symbol = env("SYMBOL", "BTCUSDT").upper()
    interval = env("INTERVAL", "1h")
    lookback = int(env("LOOKBACK", "120"))
    run_every = int(env("RUN_EVERY_MIN", "0"))  # 0 = sekali jalan
    
    if not token or not chat_id:
        raise SystemExit("TELEGRAM_BOT_TOKEN dan TELEGRAM_CHAT_ID wajib diisi (ENV atau .env).")
    
    def run_once():
        try:
            kl = fetch_klines(symbol, interval, min(max(lookback, 10), 1000))
            times = [t for t, _ in kl]
            prices = [p for _, p in kl]
            ma7 = ma(prices, period=7)
            sig = cross_signal(prices, ma7)
            
            last_time = times[-1]
            last_price = prices[-1]
            last_ma7 = ma7[-1]
            prev_price = prices[-2] if len(prices) >= 2 else None
            prev_ma7 = ma7[-2] if len(ma7) >= 2 else None
            
            ts_fmt = fmt_jkt(last_time)
            
            status = "NO_CROSS"
            if sig == "CROSS_UP":
                status = "CROSS_UP 🚀"
            elif sig == "CROSS_DOWN":
                status = "CROSS_DOWN 🔻"
            
            text_lines = [
                f"<b>[MA7 Signal]</b> {symbol} @ {interval}",
                f"Waktu  : {ts_fmt}",
                f"Harga  : {last_price:.6f}",
                f"MA7    : {last_ma7:.6f}" if last_ma7 is not None else "MA7    : belum cukup data",
                f"Signal : {status}",
            ]
            
            if prev_price is not None and prev_ma7 is not None:
                side_prev = ">" if prev_price > prev_ma7 else "<"
                side_now = ">" if last_price > (last_ma7 or last_price) else "<"
                text_lines.append(f"Side   : prev {prev_price:.6f} {side_prev} MA7 {prev_ma7:.6f} | now {last_price:.6f} {side_now} MA7 {last_ma7:.6f}")
            
            # Kirim hanya jika CROSS, agar anti-spam
            if sig in ("CROSS_UP", "CROSS_DOWN"):
                send_telegram(token, chat_id, "\n".join(text_lines))
            else:
                # Masih kirim status ringan? Komentari jika tidak mau spam sama sekali.
                # send_telegram(token, chat_id, "\n".join(text_lines))
                pass
            
            print("OK:", status)
        except Exception as e:
            print("ERROR:", e)
            # Kirim error ke Telegram biar tau
            try:
                send_telegram(token, chat_id, f"[MA7 Bot] ERROR: {e}")
            except Exception:
                pass
    
    if run_every <= 0:
        run_once()
    else:
        while True:
            run_once()
            time.sleep(run_every * 60)

if __name__ == "__main__":
    main()
