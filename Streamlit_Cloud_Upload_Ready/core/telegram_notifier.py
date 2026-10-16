"""
telegram_notifier.py — Executive Telegram Alert & Automated Radar Dispatcher
Modul 18: Quantitative Stock Price Prediction & Dynamic Screener Suite
The Trilaksana Framework

Author: Dr. Ir. Ahmad Raymond Trilaksana, S.T., M.Ak., IPM, ASEAN Eng.
Channel: @trilaksana_mining_bot -> Chat ID: 1604993430 (@ahmad_raymond)
"""

import json
import urllib.request
import urllib.parse
from datetime import datetime
from typing import Dict, Any, List

from core.data_fetcher import DEFAULT_WATCHLISTS
from core.screener import run_market_screener
from core.portfolio import evaluate_active_portfolio, load_portfolio

# Versi Publik: Notifikasi bot personal dinonaktifkan demi privasi dan keamanan pengguna
BOT_TOKEN = ""
CHAT_ID = ""
TELEGRAM_API_URL = ""


def send_telegram_alert(text: str, parse_mode: str = "Markdown") -> bool:
    """Versi Publik: Notifikasi Telegram otomatis dinonaktifkan demi privasi."""
    return False


def get_all_watchlist_stocks():
    """Mengambil seluruh daftar saham unik dari seluruh watchlist default."""
    all_stocks = []
    seen = set()
    for group in DEFAULT_WATCHLISTS.values():
        for sym, name in group:
            if sym not in seen:
                all_stocks.append((sym, name))
                seen.add(sym)
    return all_stocks


def scan_and_notify_radar(min_prob: float = 60.0, min_rr: float = 1.5, force_refresh: bool = False) -> Dict[str, Any]:
    """
    Memindai seluruh saham di watchlist:
    - Menyaring saham dengan Probabilitas Kenaikan >= min_prob (%) dan Risk/Reward >= min_rr.
    - Mengirim ringkasan eksekutif ke Telegram HP Dr. Ahmad Raymond.
    """
    stocks = get_all_watchlist_stocks()
    df_screener = run_market_screener(stocks, years=10, force_refresh=force_refresh)

    now_str = datetime.now().strftime("%d-%b-%Y %H:%M WIB")

    if df_screener.empty:
        msg = (
            "⚠️ *TRILAKSANA STOCK RADAR — PERINGATAN SISTEM*\n"
            "────────────────────────────\n"
            "Data pasar belum dapat diakses atau bursa sedang libur.\n"
            f"🕒 Waktu: {now_str}"
        )
        send_telegram_alert(msg)
        return {"status": "empty", "candidates_count": 0}

    # Filter kandidat Strong Buy yang memenuhi kriteria eksekutif
    rr_filter = df_screener["RR_Ratio"] >= float(min_rr) if "RR_Ratio" in df_screener.columns else True
    df_strong = df_screener[
        (df_screener["Probabilitas Naik (%)"] >= float(min_prob)) &
        rr_filter
    ].copy()

    if not df_strong.empty:
        df_strong = df_strong.sort_values(by="Probabilitas Naik (%)", ascending=False)
        candidates_count = len(df_strong)

        items_text = []
        for idx, (_, row) in enumerate(df_strong.iterrows(), start=1):
            curr_p = float(row["Harga Terakhir (Rp)"])
            tp_p = float(row.get("Take Profit / TP (Rp)", row.get("Target TP (Rp)", curr_p * 1.05)))
            sl_p = float(row.get("Stop Loss / SL (Rp)", row.get("Batas SL (Rp)", curr_p * 0.95)))
            est_p = float(row.get("Target Besok (Rp)", row.get("Estimasi Besok (Rp)", curr_p)))
            est_pct = float(row.get("Estimasi Kenaikan Besok (%)", row.get("Proyeksi Besok (%)", 0.0)))
            rr_display = str(row.get("Risk/Reward", f"1 : {row.get('RR_Ratio', 1.5)}"))

            pct_tp = round(((tp_p - curr_p) / curr_p) * 100, 1) if curr_p > 0 else 0.0
            pct_sl = round(((sl_p - curr_p) / curr_p) * 100, 1) if curr_p > 0 else 0.0

            card = (
                f"*{idx}. {row['Ticker']} — {row['Nama Emiten']}*\n"
                f"   🎯 *Probabilitas Naik:* `{row['Probabilitas Naik (%)']}%` (Strong Buy)\n"
                f"   💵 *Harga Masuk:* `Rp {curr_p:,.0f}` ({row['Perubahan (%)']:+.2f}%)\n"
                f"   🔮 *Estimasi Besok:* `Rp {est_p:,.0f}` ({est_pct:+.2f}%)\n"
                f"   🎯 *Target TP:* `Rp {tp_p:,.0f}` (+{pct_tp}%)\n"
                f"   🛡️ *Batas SL:* `Rp {sl_p:,.0f}` ({pct_sl}%)\n"
                f"   ⚖️ *Risk/Reward:* `{rr_display}`"
            )
            items_text.append(card)

        msg = (
            "🚨 *TRILAKSANA STOCK RADAR — SINYAL STRONG BUY DETECTED!* 📈\n"
            "────────────────────────────\n"
            f"Ditemukan *{candidates_count} saham unggulan* yang menembus ambang batas aman (Probabilitas $\\ge {min_prob}\\%$ & R/R $\\ge {min_rr}$):\n\n"
            + "\n\n".join(items_text) +
            "\n\n────────────────────────────\n"
            "💡 *Instruksi Aksi Eksekutif:*\n"
            "Saham di atas memiliki akumulasi probabilitas dominan. Layak dipertimbangkan untuk eksekusi beli bertahap pada sesi perdagangan.\n"
            f"🕒 *Waktu Analisis:* {now_str}\n"
            f"🌐 *Platform:* The Trilaksana Suite (Modul 18)"
        )
    else:
        # Status Wait & See (pasar tidak ada yang lolos kriteria aman 60%)
        candidates_count = 0
        msg = (
            "☕ *TRILAKSANA STOCK RADAR — STATUS BURSA: WAIT & SEE* 🛡️\n"
            "────────────────────────────\n"
            f"Seluruh saham di watchlist saat ini berada di bawah ambang batas aman (*{min_prob}%*).\n\n"
            "📌 *Kondisi Pasar:*\n"
            "Pasar sedang dalam tekanan jual atau fase konsolidasi rawan koreksi lanjutan.\n\n"
            "💡 *Keputusan Sistem Eksekutif:*\n"
            "• *JANGAN MEMAKSAKAN BELI HARI INI*.\n"
            "• Pertahankan dana tunai (Cash is King).\n"
            "• Tunggu hingga radar mendeteksi konfirmasi akumulasi baru.\n\n"
            f"🕒 *Waktu Analisis:* {now_str}\n"
            f"🌐 *Platform:* The Trilaksana Suite (Modul 18)"
        )

    send_telegram_alert(msg)
    return {"status": "success", "candidates_count": candidates_count}


def scan_and_notify_portfolio() -> Dict[str, Any]:
    """
    Mengevaluasi seluruh saham aktif di portofolio:
    - Menghitung Floating Profit/Loss.
    - Mengirim sinyal AMANKAN CUAN (TP), TAHAN (HOLD), atau CUT-LOSS (SL) ke Telegram.
    """
    raw_port = load_portfolio()
    now_str = datetime.now().strftime("%d-%b-%Y %H:%M WIB")

    if not raw_port:
        msg = (
            "💼 *TRILAKSANA PORTOFOLIO — LAPORAN STATUS POSISI*\n"
            "────────────────────────────\n"
            "ℹ️ Saat ini belum ada posisi saham yang disimpan di Portofolio Aktif.\n"
            "Dana kas dalam status siaga menunggu sinyal Strong Buy baru.\n"
            f"🕒 *Waktu:* {now_str}"
        )
        send_telegram_alert(msg)
        return {"status": "empty", "positions_count": 0}

    df_port = evaluate_active_portfolio(years=10)
    if df_port.empty:
        return {"status": "error", "positions_count": 0}

    total_invested = df_port["Total Modal (Rp)"].sum()
    total_current = df_port["Nilai Sekarang (Rp)"].sum()
    total_pnl_rp = total_current - total_invested
    total_pnl_pct = round((total_pnl_rp / total_invested) * 100, 2) if total_invested > 0 else 0.0

    items_text = []
    tp_alerts = 0
    sl_alerts = 0

    for idx, (_, row) in enumerate(df_port.iterrows(), start=1):
        badge_icon = "🟢" if "TAHAN" in row["Instruksi Aksi"] else ("💰" if "CUAN" in row["Instruksi Aksi"] else "⚠️")
        if "CUAN" in row["Instruksi Aksi"]:
            tp_alerts += 1
        elif "CUT-LOSS" in row["Instruksi Aksi"] or "JUAL" in row["Instruksi Aksi"]:
            sl_alerts += 1

        card = (
            f"*{idx}. {row['Ticker']}* ({row['Jumlah Lot']} Lot)\n"
            f"   💵 Beli: `Rp {row['Harga Beli (Rp)']:,.0f}` $\\rightarrow$ Sekarang: `Rp {row['Harga Sekarang (Rp)']:,.0f}`\n"
            f"   📊 Floating PnL: *{row['Untung/Rugi (%)']:+.2f}%* (`Rp {row['Untung/Rugi (Rp)']:+,.0f}`)\n"
            f"   🔮 Probabilitas Besok: `{row['Probabilitas Besok (%)']}%`\n"
            f"   🎯 TP: `Rp {row['Target TP (Rp)']:,.0f}` | 🛡️ SL: `Rp {row['Batas SL (Rp)']:,.0f}`\n"
            f"   {badge_icon} *Instruksi:* *{row['Instruksi Aksi']}*\n"
            f"   📝 *Catatan:* _{row['Catatan']}_"
        )
        items_text.append(card)

    pnl_header_icon = "🟢" if total_pnl_rp >= 0 else "🔴"
    msg = (
        f"💼 *TRILAKSANA PORTOFOLIO — REVIEW HARIAN EKSEKUTIF* {pnl_header_icon}\n"
        "────────────────────────────\n"
        f"💰 *Total Modal:* `Rp {total_invested:,.0f}`\n"
        f"📈 *Nilai Portofolio:* `Rp {total_current:,.0f}`\n"
        f"📊 *Total Floating PnL:* *{total_pnl_pct:+.2f}%* (`Rp {total_pnl_rp:+,.0f}`)\n"
        "────────────────────────────\n"
        "📋 *Rincian Posisi Saham:*\n\n"
        + "\n\n".join(items_text) +
        "\n\n────────────────────────────\n"
        f"🔔 *Ringkasan Sinyal Aksi:* {tp_alerts} Take Profit | {sl_alerts} Cut Loss | {len(df_port) - tp_alerts - sl_alerts} Tahan (Hold)\n"
        f"🕒 *Waktu Review:* {now_str}"
    )

    send_telegram_alert(msg)
    return {
        "status": "success",
        "positions_count": len(df_port),
        "total_pnl_pct": total_pnl_pct,
        "tp_alerts": tp_alerts,
        "sl_alerts": sl_alerts
    }
