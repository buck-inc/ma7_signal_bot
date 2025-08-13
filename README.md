# MA7 Signal Bot + Telegram

Bot sederhana untuk memantau **harga vs MA7 (Moving Average 7)** dan mengirim **sinyal ke Telegram** saat terjadi **cross up** atau **cross down**. Siap jalan **lokal** maupun **GitHub Actions (schedule)**.

## Fitur
- Ambil data harga dari **Binance public API** (tanpa API key).
- Hitung **MA7** dari data candle.
- Kirim notifikasi **Telegram** saat **harga close menembus MA7** (cross up/down).
- Konfigurasi lewat **ENV** (bisa `.env` atau GitHub Secrets).
- Siap **upload ke GitHub** — sudah ada workflow untuk jalan otomatis.

## Struktur
```
.
├─ src/ma7_bot.py
├─ .env.example
├─ requirements.txt
├─ README.md
├─ .gitignore
└─ .github/workflows/ma7_bot.yml
```

## Cara Pakai (Lokal)
1. **Python 3.9+** disarankan.
2. Install dependensi:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` jadi `.env`, lalu isi:
   ```env
   TELEGRAM_BOT_TOKEN=123456:ABCDEF
   TELEGRAM_CHAT_ID=123456789
   SYMBOL=BTCUSDT
   INTERVAL=1h  # contoh: 1m,5m,15m,1h,4h,1d
   LOOKBACK=120
   RUN_EVERY_MIN=0  # biarkan 0; skrip langsung jalan sekali
   ```
4. Jalankan:
   ```bash
   python src/ma7_bot.py
   ```

## Cara Pakai (GitHub Actions - Schedule)
1. Upload project ini ke **repo GitHub** (Public/Private bebas).
2. Buka **Settings → Secrets and variables → Actions → New repository secret** dan tambahkan:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - (opsional) `SYMBOL` (default `BTCUSDT`)
   - (opsional) `INTERVAL` (default `1h`)
   - (opsional) `LOOKBACK` (default `120`)
3. Workflow default **jalan tiap 15 menit** (lihat `.github/workflows/ma7_bot.yml`). Bisa diubah `cron`-nya.

## Logika Sinyal
- Hitung **MA7** pada data **close**.
- Kirim pesan hanya jika terjadi **cross** pada candle terakhir:
  - **CROSS_UP**: sebelumnya di bawah MA7, sekarang di atas MA7.
  - **CROSS_DOWN**: sebelumnya di atas MA7, sekarang di bawah MA7.
- Tidak kirim pesan jika **tetap di sisi yang sama** (anti-spam).

## Catatan
- Binance bisa rate-limit — workflow sudah ringan (sekali hit).
- Timezone pesan: **Asia/Jakarta (UTC+7)**.
- Jika network bermasalah, skrip akan retry ringan & exit, GitHub Actions otomatis re-run sesuai jadwal.

Semoga cuan! 🚀
