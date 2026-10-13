"""
Modul 18: The Trilaksana Suite — Active Portfolio Tracker & Exit Recommendation Engine
Menyimpan posisi saham yang dibeli dan mengevaluasi sinyal JUAL / TAKE PROFIT / HOLD setiap hari bursa.
"""

import os
import json
import datetime
import pandas as pd
from typing import List, Dict
from core.data_fetcher import fetch_stock_data, get_latest_price_summary, normalize_ticker, get_data_dir
from core.rolling_model import DynamicStockPredictor

PORTFOLIO_FILE = os.path.join(get_data_dir(), "active_portfolio.json")

def load_portfolio() -> List[Dict]:
    """Memuat daftar kepemilikan saham dari file lokal."""
    if not os.path.exists(PORTFOLIO_FILE):
        return []
    try:
        with open(PORTFOLIO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_portfolio(portfolio: List[Dict]) -> None:
    """Menyimpan daftar kepemilikan saham ke file lokal."""
    with open(PORTFOLIO_FILE, "w", encoding="utf-8") as f:
        json.dump(portfolio, f, indent=2, ensure_ascii=False)

def add_position(ticker: str, buy_price: float, lots: int = 10, buy_date: str = None) -> bool:
    """Menambahkan transaksi beli saham baru ke portofolio."""
    sym = normalize_ticker(ticker)
    if not buy_date:
        buy_date = datetime.date.today().strftime("%Y-%m-%d")

    portfolio = load_portfolio()
    # Buat entri posisi baru
    new_entry = {
        "id": f"{sym}_{int(datetime.datetime.now().timestamp())}",
        "ticker": sym,
        "buy_price": float(buy_price),
        "lots": int(lots),
        "shares": int(lots) * 100,
        "buy_date": buy_date
    }
    portfolio.append(new_entry)
    save_portfolio(portfolio)
    return True

def delete_position(position_id: str) -> bool:
    """Menghapus transaksi posisi dari portofolio (misal setelah dijual di bursa)."""
    portfolio = load_portfolio()
    updated = [p for p in portfolio if p.get("id") != position_id]
    save_portfolio(updated)
    return True

def evaluate_active_portfolio(years: int = 10) -> pd.DataFrame:
    """
    Mengevaluasi setiap saham di portofolio dengan data harga terbaru & model AI:
    - Menghitung Floating Profit/Loss (Rp & %)
    - Menghasilkan Rekomendasi Aksi: AMANKAN CUAN (TP), TAHAN (HOLD), atau CUT-LOSS (SL).
    """
    portfolio = load_portfolio()
    if not portfolio:
        return pd.DataFrame()

    predictor = DynamicStockPredictor(window_size=years * 250)
    rows = []

    for item in portfolio:
        sym = item["ticker"]
        buy_p = float(item["buy_price"])
        lots = int(item.get("lots", 10))
        shares = lots * 100
        total_invested = buy_p * shares

        try:
            df_raw = fetch_stock_data(sym, years=years)
            summary = get_latest_price_summary(df_raw)
            current_p = summary["close"]

            df_feat = predictor.prepare_data(df_raw)
            pred = predictor.train_and_predict_tomorrow(df_feat)

            # Hitung Nilai Sekarang & Floating PnL
            current_val = current_p * shares
            floating_pnl_rp = current_val - total_invested
            floating_pnl_pct = round(((current_p - buy_p) / buy_p) * 100, 2)

            win_prob = pred["win_probability"]
            tp_p = pred["suggested_tp"]
            sl_p = pred["suggested_sl"]

            # Logika Keputusan Aksi (Decision Engine)
            if current_p >= tp_p:
                action = "AMANKAN CUAN (TARGET TP TERCAPAI)"
                action_badge = "tp"
                action_desc = f"Harga melampaui target TP (Rp {tp_p:,.0f}). Disarankan langsung jual untuk realisasi profit."
            elif floating_pnl_pct >= 2.0 and win_prob < 48.0:
                action = "AMANKAN CUAN (LOCK PROFIT)"
                action_badge = "tp"
                action_desc = f"Posisi sedang untung (+{floating_pnl_pct}%), namun model membaca pelemahan tren besok. Realisasikan keuntungan."
            elif current_p <= sl_p:
                action = "DISIPLIN CUT-LOSS (JUAL BATASI RUGI)"
                action_badge = "sl"
                action_desc = f"Harga menyentuh batas toleransi rugi SL (Rp {sl_p:,.0f}). Jual untuk melindungi modal."
            elif win_prob <= 40.0:
                action = "KURANGI POSISI / JUAL"
                action_badge = "sl"
                action_desc = f"Probabilitas besok anjlok ({win_prob}%). Segera amankan sisa modal."
            else:
                action = "TAHAN (HOLD - POTENSI NAIK LANJUTAN)"
                action_badge = "hold"
                action_desc = f"Model memprediksi probabilitas naik {win_prob}%. Pertahankan posisi hingga mendekati TP."

            rows.append({
                "id": item["id"],
                "Ticker": sym,
                "Tanggal Beli": item.get("buy_date", "-"),
                "Harga Beli (Rp)": buy_p,
                "Jumlah Lot": lots,
                "Total Modal (Rp)": total_invested,
                "Harga Sekarang (Rp)": current_p,
                "Nilai Sekarang (Rp)": current_val,
                "Untung/Rugi (Rp)": floating_pnl_rp,
                "Untung/Rugi (%)": floating_pnl_pct,
                "Probabilitas Besok (%)": win_prob,
                "Target TP (Rp)": tp_p,
                "Batas SL (Rp)": sl_p,
                "Instruksi Aksi": action,
                "Badge": action_badge,
                "Catatan": action_desc
            })
        except Exception as e:
            print(f"Error evaluasi portofolio {sym}: {e}")
            continue

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(rows)
