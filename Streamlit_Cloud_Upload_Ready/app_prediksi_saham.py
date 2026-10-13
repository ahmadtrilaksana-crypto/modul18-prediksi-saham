"""
The Trilaksana Suite — Modul 18: Quantitative Stock Prediction & Executive Decision Engine
Dashboard Cerdas Prediksi Saham Harian, Sinyal Strong Buy Terpadu, dan Rekomendasi Jual (Take Profit).
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from core.data_fetcher import DEFAULT_WATCHLISTS, fetch_stock_data, get_latest_price_summary, normalize_ticker
from core.indicators import calculate_technical_features
from core.rolling_model import DynamicStockPredictor
from core.screener import run_market_screener
from core.portfolio import (
    load_portfolio, add_position, delete_position, evaluate_active_portfolio
)

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Modul 18: Trilaksana Stock Executive Radar",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Kustomisasi CSS Modern ala Trilaksana Dark Theme
st.markdown("""
<style>
    .reportview-container {
        background: #090d16;
    }
    .metric-card {
        background: #111827;
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 12px;
        padding: 20px 22px;
        margin-bottom: 15px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.45);
    }
    .metric-label {
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #94a3b8;
        font-family: monospace;
    }
    .metric-value {
        font-size: 26px;
        font-weight: 700;
        color: #ffffff;
        margin-top: 4px;
    }
    .strong-card {
        background: linear-gradient(135deg, rgba(34, 197, 94, 0.12) 0%, #111827 100%);
        border: 1.5px solid #22c55e;
        border-radius: 12px;
        padding: 22px;
        margin-bottom: 16px;
        box-shadow: 0 4px 20px rgba(34, 197, 94, 0.15);
    }
    .wait-box {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.12) 0%, #18181b 100%);
        border: 1.5px solid #ef4444;
        border-radius: 12px;
        padding: 24px;
        margin: 20px 0;
        text-align: center;
    }
    .badge-action-tp {
        background-color: rgba(34, 197, 94, 0.25);
        color: #22c55e;
        border: 1px solid #22c55e;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 800;
        font-size: 13px;
        display: inline-block;
    }
    .badge-action-sl {
        background-color: rgba(239, 68, 68, 0.25);
        color: #ef4444;
        border: 1px solid #ef4444;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 800;
        font-size: 13px;
        display: inline-block;
    }
    .badge-action-hold {
        background-color: rgba(56, 189, 248, 0.2);
        color: #38bdf8;
        border: 1px solid #38bdf8;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 800;
        font-size: 13px;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- SIDEBAR KONTROL -----------------
with st.sidebar:
    st.image("https://fonts.gstatic.com/s/e/notoemoji/latest/1f4c8/512.webp", width=55)
    st.title("Trilaksana Suite")
    st.caption("Modul 18: Executive Decision Engine")
    st.markdown("---")

    sector_choice = st.selectbox(
        "Pilih Sektor / Watchlist:",
        ["Semua Gabungan", "Komoditas & Tambang", "Perbankan (Big Banks)", "Konglomerasi & Konsumer", "Kustom Sendiri"],
        index=0
    )

    if sector_choice == "Semua Gabungan":
        active_watchlist = []
        for lst in DEFAULT_WATCHLISTS.values():
            active_watchlist.extend(lst)
    elif sector_choice == "Kustom Sendiri":
        custom_input = st.text_input("Masukkan Ticker (pisahkan koma):", "ANTM.JK, BBCA.JK, INCO.JK, PTBA.JK")
        symbols = [s.strip().upper() for s in custom_input.split(",") if s.strip()]
        active_watchlist = [(normalize_ticker(s), s) for s in symbols]
    else:
        active_watchlist = DEFAULT_WATCHLISTS[sector_choice]

    years_window = st.slider("Jendela Rolling Historis (Tahun):", min_value=3, max_value=10, value=10, step=1)
    
    st.markdown("---")
    min_prob_threshold = st.slider("Ambang Batas Strong Buy (%):", min_value=40, max_value=75, value=60, step=1)
    
    st.markdown("---")
    force_update = st.button("🔄 Update Data & Re-train Model", use_container_width=True)
    
    st.markdown("---")
    st.caption("💡 **Prinsip Rolling-Window**: Setiap hari bursa baru masuk, data paling lampau otomatis dibuang dan bobot model diperbarui.")

# ----------------- HEADER UTAMA -----------------
st.title("📈 Modul 18: Trilaksana Executive Stock Radar")
st.markdown(
    "Sistem Pengambilan Keputusan Investasi Saham Berbasis **Machine Learning Dinamis (Rolling Window 10 Tahun)** "
    "— Memberikan Rekomendasi **Beli (Strong Buy Saja)**, Target Persentase Cuan, dan Alarm **Kapan Harus Jual (Take Profit / Cut-Loss)**."
)
st.markdown("---")

# Mengambil / Memperbarui Data Screener
screener_key = f"screener_{sector_choice}_{years_window}"
if force_update or screener_key not in st.session_state:
    with st.spinner("Memindai data 10 tahun & menghitung probabilitas model untuk seluruh watchlist..."):
        prog_bar = st.progress(0.0)
        status_lbl = st.empty()
        
        def screener_cb(curr, total, msg):
            prog_bar.progress(curr / total)
            status_lbl.text(msg)
            
        df_screener = run_market_screener(active_watchlist, years=years_window, progress_callback=screener_cb, force_refresh=force_update)
        prog_bar.empty()
        status_lbl.empty()
        st.session_state[screener_key] = df_screener
else:
    df_screener = st.session_state[screener_key]

# ----------------- TABS UTAMA -----------------
tab_pilot, tab_portofolio, tab_screener, tab_detail = st.tabs([
    "🎯 Executive Radar (Pilot Otomatis)",
    "💼 Portofolio & Rekomendasi Jual (Take Profit)",
    "📋 Seluruh Pasar & Tabel Peringkat",
    "📈 Analisis Candlestick & Backtest"
])

# -------------------------------------------------------------
# TAB 1: EXECUTIVE RADAR (PILOT OTOMATIS)
# -------------------------------------------------------------
with tab_pilot:
    st.subheader("🎯 Radar Keputusan Eksekutif: Saham Pilihan Layak Beli Hari Ini")
    st.caption(rf"Hanya menyaring saham dengan keyakinan model kuat (Probabilitas Kenaikan $\ge {min_prob_threshold}\%$) dan Risk/Reward rasional.")

    if not df_screener.empty:
        # Filter saham yang memenuhi ambang batas Strong Buy
        df_strong = df_screener[df_screener["Probabilitas Naik (%)"] >= float(min_prob_threshold)].copy()

        if not df_strong.empty:
            st.success(f"Ditemukan **{len(df_strong)} Saham Unggulan** yang memenuhi kriteria Strong Buy hari ini!")

            for idx, row in df_strong.iterrows():
                with st.container():
                    st.markdown(f"""
                    <div class="strong-card">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                            <div>
                                <span style="font-size:24px; font-weight:800; color:#ffffff;">{row['Ticker']}</span>
                                <span style="font-size:16px; color:#94a3b8; margin-left:10px;">{row['Nama Emiten']}</span>
                            </div>
                            <span class="badge-action-tp" style="font-size:14px;">REKOMENDASI: {row['Rekomendasi']}</span>
                        </div>
                        <div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:15px; margin-top:15px;">
                            <div>
                                <div class="metric-label">Harga Hari Ini</div>
                                <div style="font-size:20px; font-weight:700; color:#ffffff;">Rp {row['Harga Terakhir (Rp)']:,.0f}</div>
                                <small style="color:{'#22c55e' if row['Perubahan (%)'] >= 0 else '#ef4444'};">{row['Perubahan (%)']:+.2f}% hari ini</small>
                            </div>
                            <div>
                                <div class="metric-label">Keyakinan Model Besok</div>
                                <div style="font-size:20px; font-weight:700; color:#22c55e;">{row['Probabilitas Naik (%)']:.1f}%</div>
                                <small style="color:#22c55e;">Estimasi: +{row['Estimasi Kenaikan Besok (%)']:.2f}% (Rp {row['Target Besok (Rp)']:,.0f})</small>
                            </div>
                            <div>
                                <div class="metric-label">Target Amankan Cuan (TP)</div>
                                <div style="font-size:20px; font-weight:700; color:#38bdf8;">+{row['Potensi TP (%)']:.1f}%</div>
                                <small style="color:#38bdf8;">Jual di Rp {row['Take Profit / TP (Rp)']:,.0f}</small>
                            </div>
                            <div>
                                <div class="metric-label">Batas Disiplin Cut-Loss (SL)</div>
                                <div style="font-size:20px; font-weight:700; color:#ef4444;">{row['Batas SL (%)']:.1f}%</div>
                                <small style="color:#ef4444;">Jual jika turun ke Rp {row['Stop Loss / SL (Rp)']:,.0f}</small>
                            </div>
                        </div>
                        <div style="margin-top:15px; padding-top:10px; border-top:1px solid rgba(255,255,255,0.08); font-size:12px; color:#94a3b8;">
                            🔑 <b>Faktor Penggerak Utama:</b> {row['Faktor Kunci']} &nbsp;|&nbsp; ⚖️ <b>Risk/Reward Ratio:</b> {row['Risk/Reward']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            # Banner Proteksi Uang Tunai saat Bursa Merah / Tidak Ada yang Strong
            highest_row = df_screener.iloc[0]
            st.markdown(f"""
            <div class="wait-box">
                <div style="font-size:36px; margin-bottom:10px;">🛑</div>
                <h2 style="color:#ef4444; margin:0 0 10px 0;">STATUS BURSA: WAIT & SEE (AMANKAN DANA TUNAI)</h2>
                <p style="color:#e4e4e7; font-size:16px; max-width:750px; margin:0 auto 15px auto; line-height:1.6;">
                    Seluruh saham di watchlist saat ini berada di bawah ambang batas aman <b>({min_prob_threshold}%)</b>. 
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
    else:
        st.warning("Data pasar belum tersedia. Silakan tekan tombol 'Update Data & Re-train Model' di bilah kiri.")

# -------------------------------------------------------------
# TAB 2: PORTOFOLIO & REKOMENDASI JUAL (TAKE PROFIT)
# -------------------------------------------------------------
with tab_portofolio:
    st.subheader("💼 Portofolio Aktif: Pantauan Posisi & Alarm Rekomendasi Jual")
    st.markdown(
        "Catat saham yang sudah Bapak beli di sini. Setiap sore/pagi, sistem akan otomatis memeriksa apakah sudah waktunya "
        "**AMANKAN CUAN (JUAL)** atau **DISIPLIN CUT-LOSS** untuk mengunci keuntungan selisih harga."
    )

    col_add, col_mon = st.columns([1, 2.2])

    with col_add:
        st.markdown("#### ➕ Catat Pembelian Saham")
        st.caption("Pilih saham dari dropdown, harga pasar saat ini akan terisi otomatis.")

        # Susun daftar seluruh saham unik dari watchlist
        all_stocks = []
        seen_syms = set()
        for group in DEFAULT_WATCHLISTS.values():
            for sym, name in group:
                if sym not in seen_syms:
                    all_stocks.append((sym, name))
                    seen_syms.add(sym)

        stock_options = all_stocks + [("CUSTOM", "[Kustom] Masukkan Kode Ticker Lain...")]

        selected_stock = st.selectbox(
            "Pilih Saham (Ketik nama/kode untuk mencari):",
            stock_options,
            format_func=lambda x: f"{x[0]} — {x[1]}" if x[0] != "CUSTOM" else x[1],
            key="port_stock_selector"
        )

        if selected_stock[0] == "CUSTOM":
            custom_sym = st.text_input("Ketik Kode Saham (contoh: BBCA.JK atau BBCA):", "BBCA.JK")
            chosen_ticker = normalize_ticker(custom_sym)
            try:
                raw_df = fetch_stock_data(chosen_ticker, years=1)
                default_price = float(get_latest_price_summary(raw_df)["close"])
            except Exception:
                default_price = 1000.0
        else:
            chosen_ticker = selected_stock[0]
            # Ambil harga real-time langsung dari data screener jika tersedia
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

        st.info(f"💡 Harga pasar resmi **{chosen_ticker}** saat ini: **Rp {default_price:,.0f}**")

        in_price = st.number_input(
            "Harga Beli Transaksi (Rp):",
            min_value=1.0,
            value=float(default_price),
            step=10.0,
            key=f"price_input_{chosen_ticker}"
        )
        in_lots = st.number_input("Jumlah Lot:", min_value=1, value=10, step=1, help="1 Lot = 100 Lembar Saham")

        total_calc = in_price * in_lots * 100
        st.caption(f"Estimasi Nilai Modal: **Rp {total_calc:,.0f}** ({in_lots} Lot)")

        if st.button("💾 Simpan ke Portofolio", use_container_width=True, type="primary"):
            add_position(chosen_ticker, in_price, in_lots)
            st.success(f"Posisi {chosen_ticker} ({in_lots} Lot @ Rp {in_price:,.0f}) berhasil disimpan!")
            st.rerun()

    with col_mon:
        st.markdown("#### 📊 Status Saham yang Sedang Bapak Pegang")
        df_port = evaluate_active_portfolio(years=years_window)

        if not df_port.empty:
            total_invested = df_port["Total Modal (Rp)"].sum()
            total_current = df_port["Nilai Sekarang (Rp)"].sum()
            total_pnl = total_current - total_invested
            total_pnl_pct = (total_pnl / total_invested) * 100 if total_invested > 0 else 0

            # Ringkasan Total Portofolio
            r1, r2, r3 = st.columns(3)
            r1.metric("Total Modal Ditanam", f"Rp {total_invested:,.0f}")
            r2.metric("Nilai Portofolio Sekarang", f"Rp {total_current:,.0f}")
            r3.metric(
                "Keuntungan / Kerugian Berjalan",
                f"Rp {total_pnl:,.0f}",
                f"{total_pnl_pct:+.2f}%"
            )

            st.markdown("---")

            # Tampilkan kartu instruksi aksi untuk setiap saham
            for _, pos in df_port.iterrows():
                badge_class = f"badge-action-{pos['Badge']}"
                pnl_color = "#22c55e" if pos["Untung/Rugi (%)"] >= 0 else "#ef4444"

                st.markdown(f"""
                <div class="metric-card" style="border-left: 5px solid {pnl_color};">
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
                            <div class="metric-label">Floating Cuan / Rugi</div>
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
                    <div style="margin-top:10px; font-size:12px; color:#cbd5e1; background:rgba(255,255,255,0.04); padding:8px 12px; border-radius:6px;">
                        📢 <b>Instruksi Sistem:</b> {pos['Catatan']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                col_btn, _ = st.columns([1, 4])
                with col_btn:
                    if st.button("🗑️ Hapus (Sudah Dijual)", key=f"del_{pos['id']}"):
                        delete_position(pos["id"])
                        st.success(f"{pos['Ticker']} dihapus dari pantauan.")
                        st.rerun()
        else:
            st.info("Belum ada saham yang dicatat di portofolio. Silakan masukkan saham yang Bapak beli melalui formulir di sebelah kiri.")

# -------------------------------------------------------------
# TAB 3: SELURUH PASAR & TABEL PERINGKAT LENGKAP
# -------------------------------------------------------------
with tab_screener:
    st.subheader("📋 Peringkat Probabilitas Seluruh Watchlist Pasar")
    st.caption("Menampilkan seluruh saham terdaftar beserta rincian target harga dan persentase keuntungan.")

    if not df_screener.empty:
        def highlight_signal_badge(val):
            if "STRONG BUY" in val:
                return 'background-color: rgba(34, 197, 94, 0.25); color: #22c55e; font-weight: bold;'
            elif "BUY" in val:
                return 'background-color: rgba(56, 189, 248, 0.2); color: #38bdf8; font-weight: bold;'
            elif "SELL" in val or "AVOID" in val:
                return 'background-color: rgba(239, 68, 68, 0.2); color: #ef4444; font-weight: bold;'
            return 'color: #94a3b8;'

        display_cols = [
            "Ticker", "Nama Emiten", "Harga Terakhir (Rp)", "Perubahan (%)",
            "Probabilitas Naik (%)", "Rekomendasi",
            "Target Besok (Rp)", "Estimasi Kenaikan Besok (%)",
            "Take Profit / TP (Rp)", "Potensi TP (%)",
            "Stop Loss / SL (Rp)", "Batas SL (%)", "Risk/Reward"
        ]

        styled_df = df_screener[display_cols].style.format({
            "Harga Terakhir (Rp)": "Rp {:,.0f}",
            "Perubahan (%)": "{:+.2f}%",
            "Probabilitas Naik (%)": "{:.1f}%",
            "Target Besok (Rp)": "Rp {:,.0f}",
            "Estimasi Kenaikan Besok (%)": "{:+.2f}%",
            "Take Profit / TP (Rp)": "Rp {:,.0f}",
            "Potensi TP (%)": "{:+.1f}%",
            "Stop Loss / SL (Rp)": "Rp {:,.0f}",
            "Batas SL (%)": "{:+.1f}%"
        })

        styler_method = getattr(styled_df, "map", getattr(styled_df, "applymap", None))
        if styler_method:
            styled_df = styler_method(highlight_signal_badge, subset=['Rekomendasi'])

        st.dataframe(styled_df, use_container_width=True, height=450)
    else:
        st.warning("Data screener kosong.")

# -------------------------------------------------------------
# TAB 4: ANALISIS CANDLESTICK & WALK-FORWARD BACKTEST
# -------------------------------------------------------------
with tab_detail:
    st.subheader("📈 Analisis Mendalam Saham Individual & Validasi Ilmiah")
    
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
    c1.metric("Harga Terakhir", f"Rp {summary['close']:,.0f}", f"{summary['pct_change']:+.2f}%")
    c2.metric("Probabilitas Naik Besok", f"{pred['win_probability']}%", pred['signal'])
    
    pct_t = round(((pred['projected_close'] - summary['close']) / summary['close']) * 100, 2)
    c3.metric("Estimasi Besok", f"Rp {pred['projected_close']:,.0f}", f"{pct_t:+.2f}% (Rentang: {pred['projected_range'][0]:,.0f}-{pred['projected_range'][1]:,.0f})")
    
    pct_tp = round(((pred['suggested_tp'] - summary['close']) / summary['close']) * 100, 1)
    pct_sl = round(((pred['suggested_sl'] - summary['close']) / summary['close']) * 100, 1)
    c4.metric("Target TP / SL", f"TP: Rp {pred['suggested_tp']:,.0f} (+{pct_tp}%)", f"SL: Rp {pred['suggested_sl']:,.0f} ({pct_sl}%)")

    # Candlestick Plotly 100 Hari Terakhir
    st.markdown("#### Grafik Candlestick & Indikator Teknikal (100 Hari Terakhir)")
    df_plot = df_feat.iloc[-100:].copy()

    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        vertical_spacing=0.08, subplot_titles=(f"Candlestick & Moving Averages — {selected_sym}", "Volume Perdagangan"),
        row_heights=[0.75, 0.25]
    )

    fig.add_trace(go.Candlestick(
        x=df_plot.index,
        open=df_plot["Open"],
        high=df_plot["High"],
        low=df_plot["Low"],
        close=df_plot["Close"],
        name="OHLC",
        increasing_line_color="#22c55e",
        decreasing_line_color="#ef4444"
    ), row=1, col=1)

    fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot["SMA_20"], line=dict(color="#38bdf8", width=1.5), name="SMA 20"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot["SMA_50"], line=dict(color="#f59e0b", width=1.5), name="SMA 50"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot["BB_Upper"], line=dict(color="rgba(255,255,255,0.2)", dash="dot"), name="BB Upper"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot["BB_Lower"], line=dict(color="rgba(255,255,255,0.2)", dash="dot"), name="BB Lower", fill='tonexty', fillcolor='rgba(255,255,255,0.03)'), row=1, col=1)

    fig.add_trace(go.Bar(
        x=df_plot.index, y=df_plot["Volume"],
        marker_color=["#22c55e" if c >= o else "#ef4444" for c, o in zip(df_plot["Close"], df_plot["Open"])],
        name="Volume"
    ), row=2, col=1)

    fig.update_layout(
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        height=480,
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
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

# Footer
st.markdown("---")
st.caption("The Trilaksana Framework — Modul 18: Quantitative Stock Prediction Suite • Dijalankan secara dinamis dengan Rolling-Window 10 Tahun.")
