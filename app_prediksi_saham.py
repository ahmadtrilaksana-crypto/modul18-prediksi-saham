"""
app_private_saham.py — Terminal Eksekutif Saham Privat Dr. Ahmad Raymond
Subdomain Resmi: saham.trilaksanamining.my.id
The Trilaksana Framework — Private Quantitative Stock Decision Engine

Author: Dr. Ir. Ahmad Raymond Trilaksana, S.T., M.Ak., IPM, ASEAN Eng.
Platform: Cloudflare SSL + Central Cloud Licensing + Telegram Bot
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# Konfigurasi Halaman Utama
st.set_page_config(
    page_title="Trilaksana Stock Terminal • saham.trilaksanamining.my.id",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Impor Modul Internal dengan Fallback Cerdas
try:
    from core.data_fetcher import (
        DEFAULT_WATCHLISTS,
        fetch_stock_data,
        get_latest_price_summary,
        normalize_ticker
    )
except ImportError:
    from data_fetcher import (
        DEFAULT_WATCHLISTS,
        fetch_stock_data,
        get_latest_price_summary,
        normalize_ticker
    )

try:
    from core.rolling_model import DynamicStockPredictor, round_to_idx_tick
except ImportError:
    from rolling_model import DynamicStockPredictor, round_to_idx_tick

try:
    from core.screener import run_market_screener
except ImportError:
    from screener import run_market_screener

try:
    from core.portfolio import (
        load_portfolio,
        add_position,
        delete_position,
        evaluate_active_portfolio
    )
except ImportError:
    from portfolio import (
        load_portfolio,
        add_position,
        delete_position,
        evaluate_active_portfolio
    )

try:
    from core.telegram_notifier import scan_and_notify_radar, scan_and_notify_portfolio
except ImportError:
    from telegram_notifier import scan_and_notify_radar, scan_and_notify_portfolio

try:
    from core.email_notifier import send_executive_email
except ImportError:
    try:
        from email_notifier import send_executive_email
    except ImportError:
        def send_executive_email(*args, **kwargs):
            return {"status": "warning", "message": "Modul email notifier belum siap."}

try:
    from core.auth_portal import check_authentication, render_auth_sidebar
except ImportError:
    from auth_portal import check_authentication, render_auth_sidebar

try:
    from core.theory_doc import render_theory_tab
except ImportError:
    from theory_doc import render_theory_tab

# =============================================================
# CENTRAL CLOUD LICENSING GATE v107
# =============================================================
check_authentication("Modul 18: Quantitative Stock Price Prediction & Dynamic Screener Suite")

# =============================================================
# GAYA VISUAL PREMIUM (DARK EXECUTIVE THEME)
# =============================================================
st.markdown("""
<style>
    .main { background-color: #0b0f19; }
    .stApp { background-color: #0b0f19; color: #f8fafc; }
    
    .exec-header {
        background: linear-gradient(135deg, #090d16 0%, #1e1b4b 50%, #0f172a 100%);
        padding: 24px 28px;
        border-radius: 16px;
        border: 1px solid #3b82f6;
        margin-bottom: 22px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6);
    }
    
    .metric-card {
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 15px;
    }
    
    .metric-label { font-size: 11px; text-transform: uppercase; color: #94a3b8; font-weight: 700; letter-spacing: 1px; }
    .metric-val { font-size: 24px; font-weight: 800; color: #ffffff; margin-top: 4px; }
    
    .strong-card {
        background: linear-gradient(135deg, #064e3b 0%, #022c22 100%);
        border: 1px solid #059669;
        border-radius: 14px;
        padding: 20px 24px;
        margin-bottom: 18px;
        box-shadow: 0 8px 25px rgba(5, 150, 105, 0.2);
    }

    .speculative-card {
        background: linear-gradient(135deg, #451a03 0%, #1c1917 100%);
        border: 1px solid #d97706;
        border-radius: 14px;
        padding: 20px 24px;
        margin-bottom: 18px;
        box-shadow: 0 8px 25px rgba(217, 119, 6, 0.2);
    }
    
    .wait-box {
        background: linear-gradient(135deg, #450a0a 0%, #1c1917 100%);
        border: 1px solid #b91c1c;
        border-radius: 14px;
        padding: 28px;
        text-align: center;
        margin-bottom: 20px;
    }
    
    .badge-action-tp { background: #059669; color: #ffffff; padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 12px; }
    .badge-action-spec { background: #d97706; color: #ffffff; padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 12px; }
    .badge-action-sl { background: #dc2626; color: #ffffff; padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 12px; }
    .badge-action-hold { background: #2563eb; color: #ffffff; padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 12px; }
</style>
""", unsafe_allow_html=True)

# =============================================================
# SIDEBAR KONTROL & PARAMETER EKSEKUTIF
# =============================================================
render_auth_sidebar()

st.sidebar.markdown("### ⚙️ Parameter Radar Eksekutif")
selected_sector = st.sidebar.selectbox(
    "Pilih Sektor Pantau:",
    ["Semua Gabungan"] + list(DEFAULT_WATCHLISTS.keys()),
    index=0
)

years_window = st.sidebar.slider(
    "Jendela Rolling Historis (Tahun):",
    min_value=1, max_value=10, value=2, step=1,
    help="Standar eksekutif adaptif 2 tahun (500 hari bursa dinamis) untuk menangkap tren modern tanpa noise masa lalu."
)

min_prob_threshold = st.sidebar.slider(
    "Ambang Batas Strong Buy (%):",
    min_value=40, max_value=75, value=55, step=1,
    help="Standar ambang batas optimal 55.0% untuk menyaring saham dengan keyakinan model dominan."
)

min_rr_threshold = st.sidebar.slider(
    "Minimal Risk/Reward Ratio:",
    min_value=1.0, max_value=3.0, value=1.5, step=0.1,
    help="Potensi Take Profit wajib minimal 1.5x lebih besar dari Stop Loss."
)

st.sidebar.markdown("---")
force_update = st.sidebar.button("🔄 Perbarui Data Bursa & Model", use_container_width=True)

# =============================================================
# HEADER TERMINAL UTAMA
# =============================================================
st.markdown("""
<div class="exec-header">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
            <div style="display:inline-block; padding:4px 14px; background:rgba(59,130,246,0.2); border:1px solid #3b82f6; border-radius:20px; color:#60a5fa; font-size:11px; font-weight:800; letter-spacing:1px; margin-bottom:8px;">
                THE TRILAKSANA SUITE &bull; MODUL 18
            </div>
            <h1 style="color:#ffffff; font-size:26px; font-weight:800; margin:0 0 6px 0;">
                The Trilaksana Suite — Executive Stock Terminal
            </h1>
            <div style="color:#94a3b8; font-size:14px;">
                Sistem Intelijen Kuantitatif, Radar Sinyal Beli, & Portofolio Analitik Dr. Ir. Ahmad Raymond Trilaksana
            </div>
        </div>
        <div style="text-align:right;">
            <div style="font-size:12px; color:#60a5fa; font-weight:700;">🌐 CENTRAL CLOUD LICENSING</div>
            <div style="font-size:12px; color:#22c55e; font-weight:700;">⚡ QUANTITATIVE ML ENGINE</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Susun Daftar Saham Sesuai Sektor
if selected_sector == "Semua Gabungan":
    active_watchlist = []
    seen = set()
    for grp in DEFAULT_WATCHLISTS.values():
        for s, n in grp:
            if s not in seen:
                active_watchlist.append((s, n))
                seen.add(s)
else:
    active_watchlist = DEFAULT_WATCHLISTS.get(selected_sector, [])

# Jalankan Screener di Latar Belakang
@st.cache_data(ttl=900, show_spinner=False)
def get_market_screener_cached(sector_name, years, refresh_flag):
    return run_market_screener(active_watchlist, years=years, force_refresh=refresh_flag)

with st.spinner(f"Memindai {len(active_watchlist)} saham semesta bursa dengan jendela rolling {years_window} tahun..."):
    df_screener = get_market_screener_cached(selected_sector, years_window, force_update)

# =============================================================
# STRUKTUR TAB EKSEKUTIF
# =============================================================
tab_radar, tab_portfolio, tab_deepdive, tab_all, tab_theory = st.tabs([
    "🎯 Radar Keputusan Eksekutif",
    "💼 Portofolio Pribadi & Alarm Jual",
    "🔬 Analisis Saham Individual & Backtest",
    "📋 Peringkat Seluruh Watchlist",
    "📖 Metodologi & Dasar Teori"
])

# -------------------------------------------------------------
# TAB 1: RADAR KEPUTUSAN EKSEKUTIF (STRONG BUY >= 55%)
# -------------------------------------------------------------
with tab_radar:
    col_rad_h, col_rad_b = st.columns([3, 1.4])
    with col_rad_h:
        st.subheader("🎯 Radar Keputusan Eksekutif: Saham Layak Beli Hari Ini")
        st.caption(rf"Menyaring saham dengan keyakinan model kuat ($\ge {min_prob_threshold}\%$) dan Risk/Reward $\ge {min_rr_threshold}$.")
    with col_rad_b:
        if st.button("🔄 Perbarui Analisis Radar", key="btn_refresh_radar", type="primary", use_container_width=True):
            st.rerun()

    if not df_screener.empty:
        # Render Banner Audit Metodologi Ilmiah (Data Funnel)
        attrs = getattr(df_screener, "attrs", {})
        tot_scanned = attrs.get("total_scanned", len(active_watchlist))
        pass_liq = attrs.get("passed_liquidity", len(df_screener))
        fail_liq = attrs.get("failed_liquidity", tot_scanned - pass_liq)
        win_years = attrs.get("years_window", years_window)

        f1, f2, f3, f4 = st.columns(4)
        f1.metric("Semesta Pantau (Universe)", f"{tot_scanned} Emiten", "Cakupan BEI")
        f2.metric("Lolos Likuiditas (>= Rp 5M)", f"{pass_liq} Emiten", f"{fail_liq} Gugur (Sepi)")
        f3.metric("Jendela Model Rolling", f"{win_years} Tahun", f"{win_years * 250} Hari Bursa")
        f4.metric("Ambang Batas Beli (COG)", f">={min_prob_threshold:.1f}%", f"Min R/R {min_rr_threshold}")
        st.markdown("---")

        # Ticker Lockout: Saring emiten yang sedang berstatus HOLDING di portofolio agar tidak muncul sebagai rekomendasi beli baru
        held_tickers = set()
        try:
            raw_portfolio = load_portfolio()
            for pos_item in raw_portfolio:
                if pos_item.get("status", "HOLDING").upper() == "HOLDING":
                    held_tickers.add(pos_item["symbol"])
        except Exception:
            pass

        df_fresh = df_screener[~df_screener["Ticker"].isin(held_tickers)].copy() if held_tickers else df_screener.copy()

        if held_tickers:
            st.info(f"🔒 **Ticker Lockout Aktif**: {len(held_tickers)} emiten yang sedang ada di portofolio Anda ({', '.join(sorted(held_tickers))}) disaring agar tidak muncul dobel di rekomendasi beli baru.")

        # Filter Kandidat Sesuai Logika 3-Tier
        rr_mask = df_fresh["RR_Ratio"] >= float(min_rr_threshold) if "RR_Ratio" in df_fresh.columns else True
        df_strong = df_fresh[
            (df_fresh["Probabilitas Naik (%)"] >= float(min_prob_threshold)) &
            rr_mask
        ].copy()

        df_spec = df_fresh[
            (df_fresh["Probabilitas Naik (%)"] >= 53.0) &
            (df_fresh["Probabilitas Naik (%)"] < float(min_prob_threshold)) &
            rr_mask
        ].copy()

        if not df_strong.empty:
            st.success(f"Ditemukan **{len(df_strong)} Saham Unggulan** yang memenuhi kriteria Strong Buy!")
            for _, row in df_strong.iterrows():
                curr_p = int(row['Harga Terakhir (Rp)'])
                tp_p = int(row.get('Take Profit / TP (Rp)', curr_p * 1.05))
                sl_p = int(row.get('Stop Loss / SL (Rp)', curr_p * 0.95))
                est_p = int(row.get('Target Besok (Rp)', curr_p))
                modal_1lot = int(row.get('Modal 1 Lot (Rp)', curr_p * 100))
                pct_est = float(row.get('Estimasi Kenaikan Besok (%)', 0.0))
                pct_tp = round(((tp_p - curr_p) / curr_p) * 100, 1) if curr_p > 0 else 0.0
                pct_sl = round(((sl_p - curr_p) / curr_p) * 100, 1) if curr_p > 0 else 0.0
                max_d = int(row.get('Max_Days', 5))
                recom_label = str(row.get('Rekomendasi', 'STRONG BUY'))
                is_spec = "SPECULATIVE" in recom_label or "REVERSAL" in recom_label or "CICIL" in recom_label
                card_class = "speculative-card" if is_spec else "strong-card"
                badge_class = "badge-action-spec" if is_spec else "badge-action-tp"
                guide_border = "#d97706" if is_spec else "#059669"
                guide_color = "#fcd34d" if is_spec else "#6ee7b7"

                strong_card_html = f"""<div class="{card_class}">
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
<div>
<span style="font-size:24px; font-weight:800; color:#ffffff;">{row['Ticker']}</span>
<span style="font-size:16px; color:#cbd5e1; margin-left:10px;">{row['Nama Emiten']}</span>
</div>
<span class="{badge_class}" style="font-size:14px;">REKOMENDASI: {recom_label}</span>
</div>
<div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:15px; margin-top:15px;">
<div>
<div class="metric-label">Harga Masuk (Buy)</div>
<div style="font-size:20px; font-weight:700; color:#ffffff;">Rp {curr_p:,.0f}</div>
<small style="color:{'#22c55e' if row['Perubahan (%)'] >= 0 else '#ef4444'};">{row['Perubahan (%)']:+.2f}% hari ini</small>
<div style="color:#38bdf8; font-size:12px; font-weight:700; margin-top:4px;">💼 Modal 1 Lot: Rp {modal_1lot:,.0f}</div>
</div>
<div>
<div class="metric-label">Probabilitas Naik</div>
<div style="font-size:20px; font-weight:700; color:#22c55e;">{row['Probabilitas Naik (%)']:.1f}%</div>
<small style="color:#22c55e;">Estimasi Besok: Rp {est_p:,.0f} ({pct_est:+.2f}%)</small>
</div>
<div>
<div class="metric-label">Target Take Profit (TP)</div>
<div style="font-size:20px; font-weight:700; color:#38bdf8;">Rp {tp_p:,.0f} (+{pct_tp}%)</div>
<small style="color:#38bdf8;">Amankan cuan (BEI tick)</small>
</div>
<div>
<div class="metric-label">Batas Stop Loss (SL)</div>
<div style="font-size:20px; font-weight:700; color:#ef4444;">Rp {sl_p:,.0f} ({pct_sl}%)</div>
<small style="color:#ef4444;">Disiplin risiko (BEI tick)</small>
</div>
</div>
<div style="margin-top:14px; background:rgba(0,0,0,0.35); border:1px solid {guide_border}; border-radius:8px; padding:12px 16px;">
<b style="color:{guide_color}; font-size:13px;">📝 Panduan Input Auto-Order Stockbit (⏱️ Horizon: Maks. {max_d} Hari Bursa):</b>
<div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap:10px; margin-top:6px; font-size:12px;">
<div>• <b>Harga Beli (Buy):</b> <span style="color:#ffffff;">Rp {curr_p:,.0f}</span> (1 Lot: Rp {modal_1lot:,.0f})</div>
<div>• <b>Set Take Profit (TP):</b> <span style="color:#38bdf8; font-weight:700;">Rp {tp_p:,.0f}</span> (+{pct_tp}%)</div>
<div>• <b>Set Stop Loss (SL):</b> <span style="color:#ef4444; font-weight:700;">Rp {sl_p:,.0f}</span> ({pct_sl}%)</div>
</div>
</div>
<div style="margin-top:12px; padding-top:10px; border-top:1px solid rgba(255,255,255,0.1); font-size:12px; color:#cbd5e1;">
🔑 <b>Faktor Penggerak:</b> {row.get('Faktor Kunci', 'Momentum & Akumulasi')} &nbsp;|&nbsp; ⚖️ <b>Risk/Reward:</b> {row.get('Risk/Reward', '1 : 2.0')}
</div>
</div>"""
                st.markdown(strong_card_html, unsafe_allow_html=True)

            if not df_spec.empty:
                st.markdown("#### 🟡 Saham Pilihan Alternatif: Speculative Buy / Cicil (53.0% - 54.9%)")
                for _, row in df_spec.iterrows():
                    curr_p = int(row['Harga Terakhir (Rp)'])
                    tp_p = int(row.get('Take Profit / TP (Rp)', curr_p * 1.05))
                    sl_p = int(row.get('Stop Loss / SL (Rp)', curr_p * 0.95))
                    est_p = int(row.get('Target Besok (Rp)', curr_p))
                    modal_1lot = int(row.get('Modal 1 Lot (Rp)', curr_p * 100))
                    pct_est = float(row.get('Estimasi Kenaikan Besok (%)', 0.0))
                    pct_tp = round(((tp_p - curr_p) / curr_p) * 100, 1) if curr_p > 0 else 0.0
                    pct_sl = round(((sl_p - curr_p) / curr_p) * 100, 1) if curr_p > 0 else 0.0
                    max_d_spec = int(row.get('Max_Days', 5))

                    spec_card_html = f"""<div class="speculative-card">
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
<div>
<span style="font-size:22px; font-weight:800; color:#ffffff;">{row['Ticker']}</span>
<span style="font-size:15px; color:#cbd5e1; margin-left:10px;">{row['Nama Emiten']}</span>
</div>
<span class="badge-action-spec" style="font-size:13px;">REKOMENDASI: SPECULATIVE BUY / CICIL</span>
</div>
<div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:15px; margin-top:12px;">
<div>
<div class="metric-label">Harga Hari Ini</div>
<div style="font-size:18px; font-weight:700; color:#ffffff;">Rp {curr_p:,.0f}</div>
<small style="color:{'#22c55e' if row['Perubahan (%)'] >= 0 else '#ef4444'};">{row['Perubahan (%)']:+.2f}% hari ini</small>
<div style="color:#f59e0b; font-size:11px; font-weight:700; margin-top:3px;">💼 Modal 1 Lot: Rp {modal_1lot:,.0f}</div>
</div>
<div>
<div class="metric-label">Probabilitas Naik</div>
<div style="font-size:18px; font-weight:700; color:#f59e0b;">{row['Probabilitas Naik (%)']:.1f}%</div>
<small style="color:#f59e0b;">Estimasi Besok: Rp {est_p:,.0f} ({pct_est:+.2f}%)</small>
</div>
<div>
<div class="metric-label">Target Take Profit</div>
<div style="font-size:18px; font-weight:700; color:#38bdf8;">Rp {tp_p:,.0f} (+{pct_tp}%)</div>
</div>
<div>
<div class="metric-label">Batas Stop Loss</div>
<div style="font-size:18px; font-weight:700; color:#ef4444;">Rp {sl_p:,.0f} ({pct_sl}%)</div>
</div>
</div>
<div style="margin-top:12px; background:rgba(0,0,0,0.35); border:1px solid #d97706; border-radius:8px; padding:10px 14px;">
<b style="color:#fcd34d; font-size:12px;">📝 Panduan Input Auto-Order Stockbit (⏱️ Horizon: Maks. {max_d_spec} Hari Bursa):</b>
<div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap:8px; margin-top:4px; font-size:11px;">
<div>• <b>Harga Beli (Buy):</b> <span style="color:#ffffff;">Rp {curr_p:,.0f}</span> (1 Lot: Rp {modal_1lot:,.0f})</div>
<div>• <b>Set Take Profit (TP):</b> <span style="color:#38bdf8; font-weight:700;">Rp {tp_p:,.0f}</span> (+{pct_tp}%)</div>
<div>• <b>Set Stop Loss (SL):</b> <span style="color:#ef4444; font-weight:700;">Rp {sl_p:,.0f}</span> ({pct_sl}%)</div>
</div>
</div>
<div style="margin-top:10px; padding-top:8px; border-top:1px solid rgba(255,255,255,0.1); font-size:12px; color:#cbd5e1;">
🔑 <b>Faktor Penggerak:</b> {row.get('Faktor Kunci', 'Konsolidasi & Akumulasi')} &nbsp;|&nbsp; ⚖️ <b>Risk/Reward:</b> {row.get('Risk/Reward', '1 : 2.0')}
</div>
</div>"""
                    st.markdown(spec_card_html, unsafe_allow_html=True)
        else:
            # Banner Proteksi Uang Tunai
            highest_row = df_fresh.iloc[0] if not df_fresh.empty else df_screener.iloc[0]
            st.markdown(f"""
            <div class="wait-box">
                <div style="font-size:36px; margin-bottom:10px;">🛑</div>
                <h2 style="color:#ef4444; margin:0 0 10px 0;">STATUS BURSA: WAIT & SEE (AMANKAN DANA TUNAI)</h2>
                <p style="color:#e4e4e7; font-size:16px; max-width:750px; margin:0 auto 15px auto; line-height:1.6;">
                    Seluruh saham di watchlist saat ini berada di bawah ambang batas aman <b>({min_prob_threshold:.1f}%)</b>. 
                    Pasar sedang dalam tekanan jual atau tren konsolidasi yang rawan koreksi lanjutan.
                </p>
                <div style="background:rgba(0,0,0,0.3); border-radius:8px; padding:12px 18px; display:inline-block; margin-bottom:15px;">
                    <span style="color:#94a3b8;">Probabilitas Tertinggi Hari Ini:</span> 
                    <b style="color:#ffffff;">{highest_row['Ticker']}</b> ({highest_row['Probabilitas Naik (%)']:.1f}% — {highest_row['Rekomendasi']})
                </div>
                <p style="color:#a1a1aa; font-size:13px; margin:0;">
                    💡 <b>Keputusan Sistem:</b> Jangan memaksakan diri membeli saham hari ini. Pertahankan dana tunai Anda hingga model mendeteksi sinyal <b>Strong Buy</b> baru.
                </p>
            </div>
            """, unsafe_allow_html=True)

            # Tampilkan Top 3 Radar Terdekat (Watchlist Siaga) di UI
            st.markdown("### 📊 Top 3 Radar Terdekat (Watchlist Siaga)")
            st.caption("Saham-saham berikut memiliki skor probabilitas tertinggi hari ini yang paling mendekati ambang batas Cut-Off Grade (COG):")
            
            top3_candidates = df_fresh.head(3) if not df_fresh.empty else df_screener.head(3)
            col_t1, col_t2, col_t3 = st.columns(3)
            cols_ui = [col_t1, col_t2, col_t3]

            for idx_ui, (_, row_t) in enumerate(top3_candidates.iterrows()):
                if idx_ui < len(cols_ui):
                    with cols_ui[idx_ui]:
                        p_curr = int(row_t['Harga Terakhir (Rp)'])
                        m_lot = int(row_t.get('Modal 1 Lot (Rp)', p_curr * 100))
                        p_tp = int(row_t.get('Take Profit / TP (Rp)', p_curr * 1.05))
                        p_sl = int(row_t.get('Stop Loss / SL (Rp)', p_curr * 0.95))
                        recom_color = "#f59e0b" if "SPECULATIVE" in row_t['Rekomendasi'] else "#94a3b8"

                        st.markdown(f"""
                        <div class="metric-card" style="border-top:3px solid {recom_color};">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <b style="font-size:20px; color:#ffffff;">{row_t['Ticker']}</b>
                                <span style="font-size:11px; padding:3px 8px; border-radius:12px; background:rgba(255,255,255,0.1); color:{recom_color}; font-weight:700;">
                                    {row_t['Rekomendasi']}
                                </span>
                            </div>
                            <div style="font-size:12px; color:#94a3b8; margin-bottom:8px;">{row_t['Nama Emiten']}</div>
                            <div style="font-size:24px; font-weight:800; color:{recom_color};">
                                {row_t['Probabilitas Naik (%)']:.1f}%
                            </div>
                            <div style="font-size:12px; color:#cbd5e1; margin-top:6px;">
                                💵 <b>Harga:</b> Rp {p_curr:,.0f} ({row_t['Perubahan (%)']:+.2f}%)<br>
                                💼 <b>Modal 1 Lot:</b> <span style="color:#38bdf8; font-weight:700;">Rp {m_lot:,.0f}</span><br>
                                ⚖️ <b>R/R:</b> {row_t.get('Risk/Reward', '1 : 1.5')}<br>
                                🎯 <b>TP:</b> Rp {p_tp:,.0f} | 🛡️ <b>SL:</b> Rp {p_sl:,.0f}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
    else:
        st.warning("Data pasar belum tersedia.")

# -------------------------------------------------------------
# TAB 2: PORTOFOLIO PRIBADI & REAL-TIME TRACKING
# -------------------------------------------------------------
with tab_portfolio:
    st.subheader("💼 Portofolio Pribadi & Alarm Keputusan Jual (TP / SL)")
    st.markdown("Catat posisi saham riil Bapak di sini. Portofolio ini terisolasi secara privat dan aman.")

    col_add, col_mon = st.columns([1, 2.2])

    with col_add:
        st.markdown("#### ➕ Catat Pembelian Saham Riil")
        stock_options = active_watchlist + [("CUSTOM", "[Kustom] Kode Saham Lain...")]
        selected_stock = st.selectbox(
            "Pilih Saham:",
            stock_options,
            format_func=lambda x: f"{x[0]} — {x[1]}" if x[0] != "CUSTOM" else x[1],
            key="port_stock_selector"
        )

        if selected_stock[0] == "CUSTOM":
            custom_sym = st.text_input("Ketik Kode Saham (contoh: BBCA.JK):", "BBCA.JK")
            chosen_ticker = normalize_ticker(custom_sym)
            try:
                raw_df = fetch_stock_data(chosen_ticker, years=1)
                default_price = float(get_latest_price_summary(raw_df)["close"])
            except Exception:
                default_price = 1000.0
        else:
            chosen_ticker = selected_stock[0]
            default_price = None
            if not df_screener.empty and "Ticker" in df_screener.columns:
                match = df_screener[df_screener["Ticker"] == chosen_ticker]
                if not match.empty:
                    default_price = float(match.iloc[0]["Harga Terakhir (Rp)"])
            if default_price is None:
                try:
                    raw_df = fetch_stock_data(chosen_ticker, years=1)
                    default_price = float(get_latest_price_summary(raw_df)["close"])
                except Exception:
                    default_price = 1000.0

        st.info(f"💵 Harga pasar resmi saat ini: **Rp {default_price:,.0f}**")
        in_price = st.number_input("Harga Beli Transaksi (Rp):", min_value=1.0, value=float(default_price), step=10.0)
        in_lots = st.number_input("Jumlah Lot:", min_value=1, value=10, step=1)
        total_calc = in_price * in_lots * 100
        st.caption(f"Estimasi Nilai Modal: **Rp {total_calc:,.0f}** ({in_lots} Lot)")

        if st.button("💾 Simpan ke Portofolio", use_container_width=True, type="primary"):
            add_position(chosen_ticker, in_price, in_lots)
            st.success(f"Posisi {chosen_ticker} ({in_lots} Lot @ Rp {in_price:,.0f}) berhasil disimpan!")
            st.rerun()

    with col_mon:
        # Pilihan Broker & Simulasi Fee Bursa
        col_fee_chk, col_broker_box = st.columns([1.1, 1.9])
        with col_fee_chk:
            apply_fee = st.checkbox(
                "🏷️ Terapkan Biaya Broker",
                value=True,
                key="cb_apply_broker_fee_pub",
                help="Menghitung estimasi floating P/L bersih setelah komisi sekuritas dan pajak bursa."
            )
        with col_broker_box:
            BROKER_FEES = {
                "Stockbit / Sinarmas (Beli 0.15% | Jual 0.25%)": (0.15, 0.25),
                "Mirae Asset Sekuritas (Beli 0.15% | Jual 0.25%)": (0.15, 0.25),
                "IPOT - Indo Premier (Beli 0.19% | Jual 0.29%)": (0.19, 0.29),
                "Mandiri Sekuritas - MOST (Beli 0.18% | Jual 0.28%)": (0.18, 0.28),
                "BCA Sekuritas - BEST (Beli 0.18% | Jual 0.28%)": (0.18, 0.28),
                "Ajaib Sekuritas (Beli 0.15% | Jual 0.25%)": (0.15, 0.25),
                "BNI Sekuritas - BIONS (Beli 0.17% | Jual 0.27%)": (0.17, 0.27),
                "Atur Persentase Manual (Custom %)": (0.15, 0.25),
            }
            if apply_fee:
                chosen_broker = st.selectbox(
                    "Pilih Sekuritas Anda:",
                    list(BROKER_FEES.keys()),
                    key="sb_broker_choice_pub"
                )
                if chosen_broker == "Atur Persentase Manual (Custom %)":
                    c_f1, c_f2 = st.columns(2)
                    with c_f1:
                        fee_buy = st.number_input("Fee Beli (%):", value=0.15, step=0.01, format="%.2f", key="in_fb_pub")
                    with c_f2:
                        fee_sell = st.number_input("Fee Jual (%):", value=0.25, step=0.01, format="%.2f", key="in_fs_pub")
                else:
                    fee_buy, fee_sell = BROKER_FEES[chosen_broker]
            else:
                fee_buy, fee_sell = 0.0, 0.0

        col_port_head, col_port_btn = st.columns([2, 1.3])
        with col_port_head:
            st.markdown("#### 📊 Status Saham yang Sedang Anda Pegang")
        with col_port_btn:
            if st.button("🔄 Perbarui Evaluasi Posisi", key="btn_send_port_tg", type="secondary", use_container_width=True):
                st.rerun()

        df_port = evaluate_active_portfolio(years=years_window, fee_buy_pct=fee_buy, fee_sell_pct=fee_sell)

        if not df_port.empty:
            total_invested = df_port["Total Modal (Rp)"].sum()
            total_current = df_port["Nilai Sekarang (Rp)"].sum()
            total_pnl = total_current - total_invested
            total_pnl_pct = (total_pnl / total_invested) * 100 if total_invested > 0 else 0

            # Ringkasan Total Portofolio
            lbl_modal = "Total Modal (Termasuk Fee)" if apply_fee else "Total Modal Ditanam (Gross)"
            lbl_pnl = "Keuntungan / Kerugian (Net)" if apply_fee else "Keuntungan / Kerugian (Gross)"
            r1, r2, r3 = st.columns(3)
            r1.metric(lbl_modal, f"Rp {total_invested:,.0f}")
            r2.metric("Nilai Portofolio Sekarang", f"Rp {total_current:,.0f}")
            r3.metric(lbl_pnl, f"Rp {total_pnl:+,.0f}", f"{total_pnl_pct:+.2f}%")

            st.markdown("---")
            for _, pos in df_port.iterrows():
                badge_class = f"badge-action-{pos['Badge']}"
                pnl_color = "#22c55e" if pos["Untung/Rugi (%)"] >= 0 else "#ef4444"
                injury_val = int(pos.get("Injury Time (Hari)", 0))
                injury_badge = f'<span style="background-color:#d97706; color:#ffffff; padding:2px 8px; border-radius:6px; font-size:11px; font-weight:700; margin-left:8px;">⚽ Injury Time: +{injury_val} Hari</span>' if injury_val > 0 else ''
                pnl_label = "Floating PnL (Net)" if apply_fee else "Floating Cuan / Rugi"

                port_card_html = f"""<div class="metric-card" style="border-left: 5px solid {pnl_color};">
<div style="display:flex; justify-content:space-between; align-items:center;">
<div>
<span style="font-size:22px; font-weight:800; color:#ffffff;">{pos['Ticker']}</span>
<span style="font-size:13px; color:#94a3b8; margin-left:8px;">({pos['Jumlah Lot']} Lot • Beli @ Rp {pos['Harga Beli (Rp)']:,.0f})</span>
</div>
<span class="{badge_class}">{pos['Instruksi Aksi']}</span>
</div>
<div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:12px; margin-top:12px;">
<div>
<div class="metric-label">Harga Pasar Terkini</div>
<div style="font-size:18px; font-weight:700; color:#ffffff;">Rp {pos['Harga Sekarang (Rp)']:,.0f}</div>
</div>
<div>
<div class="metric-label">{pnl_label}</div>
<div style="font-size:18px; font-weight:700; color:{pnl_color};">{pos['Untung/Rugi (%)']:+.2f}%</div>
<small style="color:{pnl_color};">Rp {pos['Untung/Rugi (Rp)']:+,.0f}</small>
</div>
<div>
<div class="metric-label">Target Take Profit (TP)</div>
<div style="font-size:18px; font-weight:700; color:#38bdf8;">Rp {pos['Target TP (Rp)']:,.0f}</div>
</div>
<div>
<div class="metric-label">Batas Cut-Loss (SL)</div>
<div style="font-size:18px; font-weight:700; color:#ef4444;">Rp {pos['Batas SL (Rp)']:,.0f}</div>
</div>
</div>
<div style="margin-top:12px; display:flex; justify-content:space-between; align-items:center; background:#0b0f19; padding:8px 12px; border-radius:6px; border:1px solid #334155; font-size:12px;">
<div>
⏱️ <b>Waktu Tunggu:</b> <span style="color:#38bdf8; font-weight:700;">{pos.get('Status Waktu', '')}</span>
{injury_badge}
</div>
<div style="color:#94a3b8; font-size:11px;">
Batas Normal: {pos.get('Batas Normal (Hari)', 5)} Hari | Total Maks: {pos.get('Total Hari Maksimal', 5)} Hari
</div>
</div>
<div style="margin-top:8px; font-size:12px; color:#cbd5e1; background:rgba(255,255,255,0.04); padding:8px 12px; border-radius:6px;">
📢 <b>Instruksi Sistem:</b> {pos['Catatan']}
</div>
</div>"""
                st.markdown(port_card_html, unsafe_allow_html=True)

                col_btn, _ = st.columns([1, 4])
                with col_btn:
                    if st.button("🗑️ Hapus (Sudah Dijual)", key=f"del_{pos['id']}"):
                        delete_position(pos["id"])
                        st.success(f"{pos['Ticker']} dihapus dari pantauan.")
                        st.rerun()
        else:
            st.info("Belum ada posisi saham yang dicatat. Silakan masukkan posisi saham Bapak di formulir sebelah kiri.")

# -------------------------------------------------------------
# TAB 3: ANALISIS SAHAM INDIVIDUAL & VALIDASI ILMIAH
# -------------------------------------------------------------
with tab_deepdive:
    st.subheader("🔬 Analisis Mendalam Saham Individual & Validasi Walk-Forward")
    selected_tuple = st.selectbox(
        "Pilih Saham untuk Dianalisis:",
        active_watchlist,
        format_func=lambda x: f"{x[0]} — {x[1]}",
        key="detail_select"
    )
    selected_sym, selected_name = selected_tuple

    with st.spinner(f"Memuat data historis dan melatih model untuk {selected_sym}..."):
        df_raw = fetch_stock_data(selected_sym, years=years_window, force_refresh=force_update)
        predictor = DynamicStockPredictor(window_size=years_window * 250)
        df_feat = predictor.prepare_data(df_raw)
        pred = predictor.train_and_predict_tomorrow(df_feat)
        summary = get_latest_price_summary(df_raw)

    c1, c2, c3, c4 = st.columns(4)
    c_close = round_to_idx_tick(summary['close'])
    m_1lot = c_close * 100
    c1.metric("Harga Terakhir", f"Rp {c_close:,.0f}", f"{summary['pct_change']:+.2f}%")
    c2.metric("Probabilitas Naik Besok", f"{pred['win_probability']}%", pred['signal'])
    pct_t = round(((pred['projected_close'] - c_close) / c_close) * 100, 2) if c_close > 0 else 0.0
    c3.metric("Estimasi Besok", f"Rp {pred['projected_close']:,.0f}", f"{pct_t:+.2f}%")
    pct_tp = round(((pred['suggested_tp'] - c_close) / c_close) * 100, 1) if c_close > 0 else 0.0
    pct_sl = round(((pred['suggested_sl'] - c_close) / c_close) * 100, 1) if c_close > 0 else 0.0
    c4.metric("Target TP / SL", f"TP: Rp {pred['suggested_tp']:,.0f} (+{pct_tp}%)", f"SL: Rp {pred['suggested_sl']:,.0f} ({pct_sl}%)")

    st.markdown(f"""
    <div style="background:rgba(255,255,255,0.04); border:1px solid #334155; border-radius:8px; padding:10px 16px; margin:12px 0; font-size:12px;">
        💼 <b>Modal 1 Lot (100 Lembar):</b> <b style="color:#38bdf8;">Rp {m_1lot:,.0f}</b> &nbsp;|&nbsp; 
        📝 <b>Tiket Auto-Order Stockbit:</b> Buy @ <b style="color:#ffffff;">Rp {c_close:,.0f}</b> &bull; 
        TP @ <b style="color:#22c55e;">Rp {pred['suggested_tp']:,.0f} (+{pct_tp}%)</b> &bull; 
        SL @ <b style="color:#ef4444;">Rp {pred['suggested_sl']:,.0f} ({pct_sl}%)</b>
    </div>
    """, unsafe_allow_html=True)

    # Chart Candlestick Plotly
    df_chart = df_raw.tail(90).copy()
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df_chart.index,
        open=df_chart["Open"], high=df_chart["High"],
        low=df_chart["Low"], close=df_chart["Close"],
        name="Harga Saham (90 Hari)"
    ))
    fig.update_layout(
        title=f"Pergerakan Harga Saham {selected_sym} (90 Hari Terakhir)",
        template="plotly_dark",
        height=400,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.markdown("#### Validasi Ilmiah: Walk-Forward Backtesting (Tanpa Data-Leakage)")
    test_days = st.slider("Jumlah Hari Perdagangan yang Diuji:", min_value=20, max_value=90, value=60, step=10, key="bt_slider")

    if st.button("🚀 Jalankan Uji Backtest untuk " + selected_sym, key="bt_btn"):
        with st.spinner("Menjalankan simulasi walk-forward rolling test..."):
            bt_res = predictor.walk_forward_backtest(df_feat, test_days=test_days)

        b1, b2, b3 = st.columns(3)
        b1.metric("Akurasi Tebakan Arah", f"{bt_res['overall_accuracy']}%", f"{bt_res['test_days']} Hari Diuji")
        b2.metric("Win-Rate Sinyal Beli", f"{bt_res['bullish_win_rate']}%", f"{bt_res['total_trades']} Transaksi Dieksekusi")
        b3.metric("Edge Keunggulan Statistik", f"{bt_res['overall_accuracy'] - 50.0:+.1f}% di atas Lempar Koin (50%)")

        df_bt = pd.DataFrame({
            "Tanggal": bt_res["dates"],
            "Harga": bt_res["prices"],
            "Arah Riil": ["Naik" if a == 1 else "Turun" for a in bt_res["actuals"]],
            "Tebakan Model": ["Naik" if p == 1 else "Turun" for p in bt_res["preds"]],
            "Hasil": ["Tepat (Benar)" if p == a else "Meleset (Salah)" for p, a in zip(bt_res["preds"], bt_res["actuals"])]
        })
        st.dataframe(df_bt, use_container_width=True, height=280)

# -------------------------------------------------------------
# TAB 4: PERINGKAT SELURUH WATCHLIST
# -------------------------------------------------------------
with tab_all:
    st.subheader("📋 Peringkat Probabilitas Seluruh Watchlist Pasar")
    if not df_screener.empty:
        display_cols = [
            "Ticker", "Nama Emiten", "Harga Terakhir (Rp)", "Modal 1 Lot (Rp)", "Perubahan (%)",
            "Probabilitas Naik (%)", "Rekomendasi",
            "Target Besok (Rp)", "Estimasi Kenaikan Besok (%)",
            "Take Profit / TP (Rp)", "Stop Loss / SL (Rp)", "Risk/Reward"
        ]
        cols_present = [c for c in display_cols if c in df_screener.columns]
        st.dataframe(df_screener[cols_present], use_container_width=True, height=450)

# -------------------------------------------------------------
# TAB 5: METODOLOGI & DASAR TEORI LENGKAP
# -------------------------------------------------------------
with tab_theory:
    render_theory_tab()

# Footer
st.markdown("---")
st.caption("The Trilaksana Framework • Private Executive Terminal — saham.trilaksanamining.my.id • Hak Cipta Dr. Ir. Ahmad Raymond Trilaksana.")
