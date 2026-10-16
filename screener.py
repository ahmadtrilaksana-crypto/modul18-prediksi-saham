"""
Modul 18: The Trilaksana Suite — Quantitative Stock Screener & Ranking Engine
Menyaring daftar saham, menjalankan model prediksi secara massal, menerapkan filter likuiditas,
dan mengurutkan rekomendasi terbaik.
Author: Dr. Ir. Ahmad Raymond Trilaksana
"""

import pandas as pd
from typing import List, Tuple, Callable
from core.data_fetcher import fetch_stock_data, get_latest_price_summary, check_stock_liquidity_and_quality
from core.rolling_model import DynamicStockPredictor, round_to_idx_tick

def run_market_screener(
    watchlist: List[Tuple[str, str]],
    years: int = 2,
    progress_callback: Callable[[int, int, str], None] = None,
    force_refresh: bool = False
) -> pd.DataFrame:
    """
    Menjalankan skrining kuantitatif pada daftar saham watchlist.
    Menerapkan Filter Ganda Likuiditas (anti-saham tidur/gorengan).
    Mengembalikan DataFrame berisi peringkat saham berdasarkan probabilitas kenaikan tertinggi,
    lengkap dengan proyeksi persentase keuntungan besok, target swing TP/SL, dan metadata corong data.
    """
    predictor = DynamicStockPredictor(window_size=years * 250)
    results = []
    total_scanned = len(watchlist)
    passed_liquidity = 0
    for idx, (sym, name) in enumerate(watchlist):
        if progress_callback:
            progress_callback(idx + 1, total_scanned, f"Memproses {sym} ({name})...")

        try:
            df_raw = fetch_stock_data(sym, years=years, force_refresh=force_refresh)
            
            # Filter Ganda Likuiditas & Kualitas Eksekutif (Anti-Gorengan / Anti-Tidur)
            is_valid, reason = check_stock_liquidity_and_quality(df_raw)
            if not is_valid:
                # Saham dilewati otomatis jika tidak memenuhi standar
                continue

            summary = get_latest_price_summary(df_raw)
            passed_liquidity += 1
            df_feat = predictor.prepare_data(df_raw)
            pred = predictor.train_and_predict_tomorrow(df_feat)

            current_p = round_to_idx_tick(summary["close"])
            target_p = round_to_idx_tick(pred["projected_close"])
            tp_p = round_to_idx_tick(pred["suggested_tp"])
            sl_p = round_to_idx_tick(pred["suggested_sl"])
            modal_1lot = current_p * 100

            # Hitung persentase proyeksi
            pct_tomorrow = round(((target_p - current_p) / current_p) * 100, 2) if current_p > 0 else 0.0
            pct_tp = round(((tp_p - current_p) / current_p) * 100, 2) if current_p > 0 else 0.0
            pct_sl = round(((sl_p - current_p) / current_p) * 100, 2) if current_p > 0 else 0.0

            # Hitung Risk-Reward Ratio
            risk = current_p - sl_p
            reward = tp_p - current_p
            rr_ratio = round(reward / risk, 2) if risk > 0 else 1.0

            prob = float(pred["win_probability"])

            # Logika Sinkronisasi Rekomendasi Eksekutif & Anti-Pisau Jatuh
            rekomendasi = pred["signal"]
            if rekomendasi == "STRONG BUY" and rr_ratio < 1.50:
                rekomendasi = "SPECULATIVE BUY / CICIL"
            elif prob < 50.0:
                rekomendasi = "AVOID / WAIT & SEE"

            results.append({
                "Ticker": sym,
                "Nama Emiten": name,
                "Harga Terakhir (Rp)": current_p,
                "Modal 1 Lot (Rp)": modal_1lot,
                "Perubahan (%)": summary["pct_change"],
                "Probabilitas Naik (%)": prob,
                "Rekomendasi": rekomendasi,
                "Target Besok (Rp)": target_p,
                "Estimasi Kenaikan Besok (%)": pct_tomorrow,
                "Rentang Besok (Low - High)": f"{pred['projected_range'][0]:,.0f} - {pred['projected_range'][1]:,.0f}",
                "Take Profit / TP (Rp)": tp_p,
                "Potensi TP (%)": pct_tp,
                "Stop Loss / SL (Rp)": sl_p,
                "Batas SL (%)": pct_sl,
                "Risk/Reward": f"1 : {rr_ratio}",
                "RR_Ratio": float(rr_ratio),
                "Volatilitas ATR (Rp)": pred["atr_volatility"],
                "Faktor Kunci": ", ".join(pred["top_drivers"][:2]),
                "Horizon": pred.get("horizon_days", f"Maks. {int(pred.get('max_holding_days', 5))} Hari Bursa"),
                "Max_Days": int(pred.get("max_holding_days", 5))
            })
        except Exception as e:
            # Lewati error emiten individual tanpa menghentikan pemindaian total
            continue

    if not results:
        empty_df = pd.DataFrame()
        empty_df.attrs = {
            "total_scanned": total_scanned,
            "passed_liquidity": passed_liquidity,
            "failed_liquidity": total_scanned - passed_liquidity,
            "years_window": years
        }
        return empty_df

    df_res = pd.DataFrame(results)
    # Urutkan berdasarkan Probabilitas Naik tertinggi ke terendah
    df_res = df_res.sort_values(by="Probabilitas Naik (%)", ascending=False).reset_index(drop=True)
    df_res.index = df_res.index + 1 # Penomoran peringkat mulai dari 1
    
    # Simpan atribut audit metodologi ilmiah ke dalam DataFrame
    df_res.attrs = {
        "total_scanned": total_scanned,
        "passed_liquidity": passed_liquidity,
        "failed_liquidity": total_scanned - passed_liquidity,
        "years_window": years
    }
    return df_res
