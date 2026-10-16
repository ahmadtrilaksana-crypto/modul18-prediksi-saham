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
from core.rolling_model import DynamicStockPredictor, round_to_idx_tick, calculate_injury_time

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

def evaluate_active_portfolio(years: int = 2, fee_buy_pct: float = 0.0, fee_sell_pct: float = 0.0) -> pd.DataFrame:
    """
    Mengevaluasi setiap saham di portofolio dengan data harga terbaru & model AI:
    - Menghitung Floating Profit/Loss (Rp & %) dengan opsi simulasi komisi broker & levy bursa
    - Menghitung Hari Kepemilikan & Hitung Mundur Waktu Normal
    - Menghitung Tambahan Waktu (Injury Time) matematis jika sedang kencang menuju target
    - Menghasilkan Rekomendasi Aksi: AMANKAN CUAN (TP), TAHAN (HOLD), INJURY TIME, atau CUT-LOSS / EXIT.
    """
    portfolio = load_portfolio()
    if not portfolio:
        return pd.DataFrame()

    predictor = DynamicStockPredictor(window_size=years * 250)
    rows = []
    today_dt = datetime.date.today()

    for item in portfolio:
        sym = item["ticker"]
        buy_p = float(item["buy_price"])
        lots = int(item.get("lots", 10))
        shares = lots * 100
        total_invested_gross = buy_p * shares
        # Modal riil termasuk komisi beli sekuritas (jika diaktifkan)
        total_invested = round(total_invested_gross * (1.0 + (fee_buy_pct / 100.0)))
        buy_date_str = item.get("buy_date", today_dt.strftime("%Y-%m-%d"))

        try:
            buy_dt = datetime.datetime.strptime(buy_date_str, "%Y-%m-%d").date()
            days_held = max(1, (today_dt - buy_dt).days)
        except Exception:
            days_held = 1

        try:
            df_raw = fetch_stock_data(sym, years=years)
            summary = get_latest_price_summary(df_raw)
            current_p = round_to_idx_tick(summary["close"])

            df_feat = predictor.prepare_data(df_raw)
            pred = predictor.train_and_predict_tomorrow(df_feat)

            # Hitung Nilai Sekarang & Floating PnL
            current_val = current_p * shares
            floating_pnl_rp = current_val - total_invested
            floating_pnl_pct = round(((current_val - total_invested) / total_invested) * 100, 2)

            # Estimasi likuidasi bersih jika dijual hari ini (dipotong fee jual + PPh)
            net_sell_val = round(current_val * (1.0 - (fee_sell_pct / 100.0))) if fee_sell_pct > 0.0 else current_val
            net_liquidate_pnl = net_sell_val - total_invested

            win_prob = pred["win_probability"]
            tp_p = round_to_idx_tick(pred["suggested_tp"])
            sl_p = round_to_idx_tick(pred["suggested_sl"])
            atr_val = pred.get("atr_volatility", current_p * 0.02)

            # Hitung Waktu Normal & Injury Time
            max_normal_days = int(pred.get("max_holding_days", 5))
            remaining_normal_days = max_normal_days - days_held

            injury_calc = calculate_injury_time(
                entry_price=buy_p,
                current_price=current_p,
                tp_price=tp_p,
                atr_val=atr_val
            )
            injury_days = injury_calc.get("injury_days", 0)
            total_allowed_days = max_normal_days + injury_days

            # Logika Keputusan Aksi (Decision Engine dengan Aturan Wasit Tegas)
            if current_p >= tp_p:
                action = "AMANKAN CUAN (TARGET TP TERCAPAI)"
                action_badge = "tp"
                action_desc = f"Harga menyentuh target TP (Rp {tp_p:,.0f}). Segera jual di Stockbit untuk merealisasikan profit +{floating_pnl_pct}%."
            elif current_p <= sl_p:
                action = "DISIPLIN CUT-LOSS (JUAL BATASI RUGI)"
                action_badge = "sl"
                action_desc = f"Harga menyentuh batas risiko SL (Rp {sl_p:,.0f}). Jual disiplin untuk melindungi sisa modal."
            elif days_held >= total_allowed_days:
                # Waktu maksimal mutlak habis (Peluit panjang wasit berbunyi)
                if floating_pnl_pct >= 2.0:
                    action = f"PELUIT AKHIR: AMANKAN CUAN (+{floating_pnl_pct}%) SEKARANG!"
                    action_badge = "tp"
                    action_desc = f"Batas waktu maksimal ({total_allowed_days} hari) telah berakhir. Jual di pasar untuk membungkus cuan +{floating_pnl_pct}%."
                else:
                    action = "PELUIT AKHIR: WAKTU HABIS — JUAL & BEBASKAN MODAL"
                    action_badge = "sl"
                    action_desc = f"Saham macet dan tidak mencapai target dalam {total_allowed_days} hari bursa. Jual di pasar untuk membebaskan modal."
            elif remaining_normal_days <= 0 and injury_days > 0:
                # Sedang dalam masa injury time resmi
                action = f"⚽ INJURY TIME WASIT (+{injury_days} HARI): PASANG TRAILING STOP"
                action_badge = "hold"
                action_desc = f"Waktu normal ({max_normal_days} hari) selesai. Diberi tambahan waktu +{injury_days} hari karena sedang kencang (+{floating_pnl_pct}%). Naikkan SL ke harga beli Rp {buy_p:,.0f} (Bebas Risiko)!"
            else:
                # Masih dalam waktu normal on-track
                action = f"TAHAN (HOLD — SISA {remaining_normal_days} HARI BURSA)"
                action_badge = "hold"
                action_desc = f"Hari ke-{days_held} dari {max_normal_days} hari bursa normal. Posisi on-track menuju target TP Rp {tp_p:,.0f} (+{round(((tp_p-buy_p)/buy_p)*100,1)}%)."

            rows.append({
                "id": item["id"],
                "Ticker": sym,
                "Tanggal Beli": buy_date_str,
                "Harga Beli (Rp)": buy_p,
                "Jumlah Lot": lots,
                "Total Modal (Rp)": total_invested,
                "Modal Pokok (Rp)": total_invested_gross,
                "Harga Sekarang (Rp)": current_p,
                "Nilai Sekarang (Rp)": current_val,
                "Nilai Bersih Jual (Rp)": net_sell_val,
                "Untung/Rugi (Rp)": floating_pnl_rp,
                "Untung/Rugi (%)": floating_pnl_pct,
                "Untung/Rugi Bersih Jual (Rp)": net_liquidate_pnl,
                "Fee Beli (%)": fee_buy_pct,
                "Fee Jual (%)": fee_sell_pct,
                "Probabilitas Besok (%)": win_prob,
                "Target TP (Rp)": tp_p,
                "Batas SL (Rp)": sl_p,
                "Hari Berjalan": days_held,
                "Batas Normal (Hari)": max_normal_days,
                "Injury Time (Hari)": injury_days,
                "Total Hari Maksimal": total_allowed_days,
                "Status Waktu": f"Hari ke-{days_held} dari {total_allowed_days} (Sisa {max(0, total_allowed_days - days_held)} Hari)",
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
