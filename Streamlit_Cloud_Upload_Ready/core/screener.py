"""
Modul 18: The Trilaksana Suite — Quantitative Stock Screener & Ranking Engine
Menyaring daftar saham, menjalankan model prediksi secara massal, dan mengurutkan rekomendasi terbaik.
"""

import pandas as pd
from typing import List, Tuple, Callable
from core.data_fetcher import fetch_stock_data, get_latest_price_summary
from core.rolling_model import DynamicStockPredictor

def run_market_screener(
    watchlist: List[Tuple[str, str]],
    years: int = 10,
    progress_callback: Callable[[int, int, str], None] = None,
    force_refresh: bool = False
) -> pd.DataFrame:
    """
    Menjalankan skrining kuantitatif pada daftar saham watchlist.
    Mengembalikan DataFrame berisi peringkat saham berdasarkan probabilitas kenaikan tertinggi,
    lengkap dengan proyeksi persentase keuntungan besok dan target swing TP/SL.
    """
    predictor = DynamicStockPredictor(window_size=years * 250)
    results = []

    total_stocks = len(watchlist)
    for idx, (sym, name) in enumerate(watchlist):
        if progress_callback:
            progress_callback(idx + 1, total_stocks, f"Memproses {sym} ({name})...")

        try:
            df_raw = fetch_stock_data(sym, years=years, force_refresh=force_refresh)
            if len(df_raw) < 150:
                continue

            summary = get_latest_price_summary(df_raw)
            df_feat = predictor.prepare_data(df_raw)
            pred = predictor.train_and_predict_tomorrow(df_feat)

            current_p = summary["close"]
            target_p = pred["projected_close"]
            tp_p = pred["suggested_tp"]
            sl_p = pred["suggested_sl"]

            # Hitung persentase proyeksi
            pct_tomorrow = round(((target_p - current_p) / current_p) * 100, 2)
            pct_tp = round(((tp_p - current_p) / current_p) * 100, 2)
            pct_sl = round(((sl_p - current_p) / current_p) * 100, 2)

            # Hitung Risk-Reward Ratio
            risk = current_p - sl_p
            reward = tp_p - current_p
            rr_ratio = round(reward / risk, 2) if risk > 0 else 1.0

            results.append({
                "Ticker": sym,
                "Nama Emiten": name,
                "Harga Terakhir (Rp)": current_p,
                "Perubahan (%)": summary["pct_change"],
                "Probabilitas Naik (%)": pred["win_probability"],
                "Rekomendasi": pred["signal"],
                "Target Besok (Rp)": target_p,
                "Estimasi Kenaikan Besok (%)": pct_tomorrow,
                "Rentang Besok (Low - High)": f"{pred['projected_range'][0]:,.0f} - {pred['projected_range'][1]:,.0f}",
                "Take Profit / TP (Rp)": tp_p,
                "Potensi TP (%)": pct_tp,
                "Stop Loss / SL (Rp)": sl_p,
                "Batas SL (%)": pct_sl,
                "Risk/Reward": f"1 : {rr_ratio}",
                "Volatilitas ATR (Rp)": pred["atr_volatility"],
                "Faktor Kunci": ", ".join(pred["top_drivers"][:2])
            })
        except Exception as e:
            print(f"Error memproses {sym}: {e}")
            continue

    if not results:
        return pd.DataFrame()

    df_res = pd.DataFrame(results)
    # Urutkan berdasarkan Probabilitas Naik tertinggi ke terendah
    df_res = df_res.sort_values(by="Probabilitas Naik (%)", ascending=False).reset_index(drop=True)
    df_res.index = df_res.index + 1 # Penomoran peringkat mulai dari 1
    return df_res
