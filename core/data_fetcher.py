"""
Modul 18: The Trilaksana Suite — Data Ingestion & Cache Engine
Mengambil dan mengelola data historis saham secara otomatis dengan caching lokal dan filter likuiditas.
Author: Dr. Ir. Ahmad Raymond Trilaksana
"""

import os
import datetime
from datetime import timezone, timedelta
from typing import Tuple, Dict, List
import pandas as pd
import yfinance as yf

# Zona Waktu Resmi Indonesia Barat (WIB = UTC+7)
WIB = timezone(timedelta(hours=7))

def get_wib_now() -> datetime.datetime:
    """Mengembalikan waktu saat ini dalam zona waktu WIB (UTC+7)."""
    return datetime.datetime.now(WIB)

# ==============================================================================
# DAFTAR WATCHLIST UNIVERSE RESMI BEI (KOMPAS100 / IDX80 / EMERGING MID-CAP)
# Disaring otomatis oleh Gerbang Likuiditas COG (Turnover >= Rp 5 Miliar / Hari)
# ==============================================================================
DEFAULT_WATCHLISTS: Dict[str, List[Tuple[str, str]]] = {
    "Komoditas, Tambang & Energi": [
        ("ANTM.JK", "Aneka Tambang Tbk"),
        ("INCO.JK", "Vale Indonesia Tbk"),
        ("NCKL.JK", "Trimegah Bangun Persada Tbk"),
        ("MBMA.JK", "Merdeka Battery Materials Tbk"),
        ("HRUM.JK", "Harum Energy Tbk"),
        ("MDKA.JK", "Merdeka Copper Gold Tbk"),
        ("AMMN.JK", "Amman Mineral Internasional Tbk"),
        ("BRMS.JK", "Bumi Resources Minerals Tbk"),
        ("PSAB.JK", "J Resources Asia Pasifik Tbk"),
        ("TINS.JK", "Timah Tbk"),
        ("ADRO.JK", "Adaro Energy Indonesia Tbk"),
        ("PTBA.JK", "Bukit Asam Tbk"),
        ("ITMG.JK", "Indo Tambangraya Megah Tbk"),
        ("UNTR.JK", "United Tractors Tbk"),
        ("INDY.JK", "Indika Energy Tbk"),
        ("BUMI.JK", "Bumi Resources Tbk"),
        ("HRTA.JK", "Hartadinata Abadi Tbk"),
        ("MEDC.JK", "Medco Energi Internasional Tbk"),
        ("PGAS.JK", "Perusahaan Gas Negara Tbk"),
        ("AKRA.JK", "AKR Corporindo Tbk"),
        ("ELSA.JK", "Elnusa Tbk"),
        ("RAJA.JK", "Rukun Raharja Tbk"),
        ("ENRG.JK", "Energi Mega Persada Tbk"),
        ("DOID.JK", "Delta Dunia Makmur Tbk"),
        ("ABMM.JK", "ABM Investama Tbk"),
        ("TOBA.JK", "TBS Energi Utama Tbk"),
        ("KKGI.JK", "Resource Alam Indonesia Tbk"),
        ("HILL.JK", "Hillcon Tbk"),
        ("ARCI.JK", "Archi Indonesia Tbk"),
        ("CITA.JK", "Cita Mineral Investindo Tbk"),
        ("NICL.JK", "PAM Mineral Tbk"),
    ],
    "Perbankan & Keuangan": [
        ("BBCA.JK", "Bank Central Asia Tbk"),
        ("BBRI.JK", "Bank Rakyat Indonesia Tbk"),
        ("BMRI.JK", "Bank Mandiri Tbk"),
        ("BBNI.JK", "Bank Negara Indonesia Tbk"),
        ("BRIS.JK", "Bank Syariah Indonesia Tbk"),
        ("BBTN.JK", "Bank Tabungan Negara Tbk"),
        ("BDMN.JK", "Bank Danamon Indonesia Tbk"),
        ("BNGA.JK", "Bank CIMB Niaga Tbk"),
        ("NISP.JK", "Bank OCBC NISP Tbk"),
        ("BJBR.JK", "Bank BJB Tbk"),
        ("BJTM.JK", "Bank Jatim Tbk"),
        ("ARTO.JK", "Bank Jago Tbk"),
        ("BBYB.JK", "Bank Neo Commerce Tbk"),
        ("BFIN.JK", "BFI Finance Indonesia Tbk"),
        ("PNBN.JK", "Bank Pan Indonesia Tbk"),
        ("BNII.JK", "Bank Maybank Indonesia Tbk"),
        ("BTPS.JK", "Bank BTPN Syariah Tbk"),
        ("CFIN.JK", "Clipan Finance Indonesia Tbk"),
        ("ADMF.JK", "Adira Dinamika Multi Finance Tbk"),
    ],
    "Konglomerasi, Konsumer & Ritel": [
        ("ASII.JK", "Astra International Tbk"),
        ("BMTR.JK", "Global Mediacom Tbk"),
        ("BREN.JK", "Barito Renewables Energy Tbk"),
        ("TPIA.JK", "Chandra Asri Pacific Tbk"),
        ("CUAN.JK", "Petrindo Jaya Kreasi Tbk"),
        ("BRPT.JK", "Barito Pacific Tbk"),
        ("CDIA.JK", "Chandra Daya Investasi Tbk"),
        ("ICBP.JK", "Indofood CBP Sukses Makmur Tbk"),
        ("INDF.JK", "Indofood Sukses Makmur Tbk"),
        ("MYOR.JK", "Mayora Indah Tbk"),
        ("ULTJ.JK", "Ultra Jaya Milk Industry Tbk"),
        ("CMRY.JK", "Cisarua Mountain Dairy Tbk"),
        ("CPIN.JK", "Charoen Pokphand Indonesia Tbk"),
        ("JPFA.JK", "Japfa Comfeed Indonesia Tbk"),
        ("UNVR.JK", "Unilever Indonesia Tbk"),
        ("KLBF.JK", "Kalbe Farma Tbk"),
        ("SIDO.JK", "Industri Jamu Sido Muncul Tbk"),
        ("MIKA.JK", "Mitra Keluarga Karyasehat Tbk"),
        ("HEAL.JK", "Medikaloka Hermina Tbk"),
        ("SILO.JK", "Siloam International Hospitals Tbk"),
        ("AMRT.JK", "Sumber Alfaria Trijaya Tbk"),
        ("MIDI.JK", "Midi Utama Indonesia Tbk"),
        ("MAPI.JK", "Mitra Adiperkasa Tbk"),
        ("MAPA.JK", "MAP Aktif Adiperkasa Tbk"),
        ("ACES.JK", "Aspirasi Hidup Indonesia Tbk"),
        ("ERAA.JK", "Erajaya Swasembada Tbk"),
        ("AUTO.JK", "Astra Otoparts Tbk"),
        ("DRMA.JK", "Dharma Polimetal Tbk"),
        ("SMSM.JK", "Selamat Sempurna Tbk"),
        ("GGRM.JK", "Gudang Garam Tbk"),
        ("HMSP.JK", "H.M. Sampoerna Tbk"),
        ("WIIM.JK", "Wismilak Inti Makmur Tbk"),
        ("STTP.JK", "Siantar Top Tbk"),
        ("ROTI.JK", "Nippon Indosari Corpindo Tbk"),
        ("CLEO.JK", "Sariguna Primatirta Tbk"),
    ],
    "Properti, Konstruksi & Infrastruktur": [
        ("BSDE.JK", "Bumi Serpong Damai Tbk"),
        ("CTRA.JK", "Ciputra Development Tbk"),
        ("SMRA.JK", "Summarecon Agung Tbk"),
        ("PWON.JK", "Pakuwon Jati Tbk"),
        ("PANI.JK", "Pantai Indah Kapuk Dua Tbk"),
        ("ASRI.JK", "Alam Sutera Realty Tbk"),
        ("DMAS.JK", "Puradelta Lestari Tbk"),
        ("SSIA.JK", "Surya Semesta Internusa Tbk"),
        ("KIJA.JK", "Kawasan Industri Jababeka Tbk"),
        ("DILD.JK", "Intiland Development Tbk"),
        ("JSMR.JK", "Jasa Marga Tbk"),
        ("PTPP.JK", "PP (Persero) Tbk"),
        ("WIKA.JK", "Wijaya Karya Tbk"),
        ("ADHI.JK", "Adhi Karya Tbk"),
        ("TOTL.JK", "Total Bangun Persada Tbk"),
        ("INTP.JK", "Indocement Tunggal Prakarsa Tbk"),
        ("SMGR.JK", "Semen Indonesia Tbk"),
        ("SMBR.JK", "Semen Baturaja Tbk"),
        ("WTON.JK", "Wijaya Karya Beton Tbk"),
    ],
    "Telekomunikasi, Teknologi & Logistik": [
        ("TLKM.JK", "Telkom Indonesia Tbk"),
        ("ISAT.JK", "Indosat Ooredoo Hutchison Tbk"),
        ("EXCL.JK", "XL Axiata Tbk"),
        ("MTEL.JK", "Dayamitra Telekomunikasi Tbk"),
        ("TOWR.JK", "Sarana Menara Nusantara Tbk"),
        ("TBIG.JK", "Tower Bersama Infrastructure Tbk"),
        ("GOTO.JK", "GoTo Gojek Tokopedia Tbk"),
        ("EMTK.JK", "Elang Mahkota Teknologi Tbk"),
        ("SCMA.JK", "Surya Citra Media Tbk"),
        ("BUKA.JK", "Bukalapak.com Tbk"),
        ("WIFI.JK", "Solusi Sinergi Digital Tbk"),
        ("ASSA.JK", "Adi Sarana Armada Tbk"),
        ("SMDR.JK", "Samudera Indonesia Tbk"),
        ("TMAS.JK", "Temas Tbk"),
        ("BIRD.JK", "Blue Bird Tbk"),
    ]
}


def get_data_dir() -> str:
    """Mengembalikan direktori penyimpanan cache data."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def normalize_ticker(symbol: str) -> str:
    """Format ticker agar sesuai standar Yahoo Finance (default .JK untuk saham Indonesia)."""
    sym = symbol.strip().upper()
    if not sym.endswith(".JK") and not sym.startswith("^") and "." not in sym:
        sym += ".JK"
    return sym


def check_stock_liquidity_and_quality(df: pd.DataFrame) -> Tuple[bool, str]:
    """
    Filter Ganda Otomatis Anti-Saham Tidur / Gorengan:
    1. Kedalaman data historis minimal 500 hari bursa (~2.5 tahun) untuk mengakomodasi emiten IPO besar.
    2. Rata-rata nilai transaksi harian 20 hari terakhir >= Rp 5.000.000.000 (Rp 5 Miliar).
    3. Harga penutupan terakhir >= Rp 100 (menghindari saham gocap / Rp 50).
    4. Tidak lebih dari 10% hari tanpa transaksi (Volume == 0) dalam 1 tahun terakhir (250 hari).
    """
    if df.empty:
        return False, "Data kosong"

    # 1. Maturity Filter (Minimal 450 hari bursa ~ 2 tahun kalender perdagangan)
    if len(df) < 450:
        return False, f"Riwayat bursa < 450 hari (tersedia {len(df)} hari)"

    # 2. Harga Terakhir >= Rp 100
    last_close = float(df["Close"].iloc[-1])
    if last_close < 100:
        return False, f"Harga terakhir Rp {last_close:,.0f} (< Rp 100)"

    # 3. Filter Likuiditas Transaksi 20 Hari Terakhir (>= Rp 5 Miliar)
    recent_20 = df.iloc[-20:]
    turnover_20d = (recent_20["Close"] * recent_20["Volume"]).mean()
    if turnover_20d < 5_000_000_000:
        turnover_bio = turnover_20d / 1_000_000_000
        return False, f"Turnover 20-hari rata-rata hanya Rp {turnover_bio:.2f} M (< Rp 5 Miliar)"

    # 4. Filter Saham Tidur (Maksimal 10% hari nol volume dalam 250 hari bursa terakhir)
    recent_1y = df.iloc[-min(250, len(df)):]
    zero_vol_count = (recent_1y["Volume"] <= 0).sum()
    zero_vol_ratio = zero_vol_count / len(recent_1y)
    if zero_vol_ratio > 0.10:
        return False, f"Saham tidur: {zero_vol_ratio * 100:.1f}% hari bursa tanpa transaksi (> 10%)"

    return True, "Memenuhi standar likuiditas & kualitas eksekutif"


def fetch_stock_data(symbol: str, years: int = 10, force_refresh: bool = False) -> pd.DataFrame:
    """
    Mengambil data historis OHLCV selama N tahun dengan mekanisme cache cerdas.
    Jika cache lokal sudah diperbarui hari ini, gunakan cache lokal.
    """
    sym = normalize_ticker(symbol)
    clean_sym = sym.replace("^", "IDX_").replace(".", "_")
    cache_file = os.path.join(get_data_dir(), f"{clean_sym}_{years}y.csv")

    now = get_wib_now()

    # Cek apakah cache valid hari ini
    if not force_refresh and os.path.exists(cache_file):
        try:
            cache_mtime = datetime.datetime.fromtimestamp(os.path.getmtime(cache_file), tz=WIB)
            
            # Jika cache dibuat sebelum jam penutupan bursa resmi (16:15 WIB) dan sekarang sudah lewat 16:15 WIB, refresh data closing resmi
            is_post_market = now.hour > 16 or (now.hour == 16 and now.minute >= 15)
            cache_was_pre_close = cache_mtime.date() == now.date() and (cache_mtime.hour < 16 or (cache_mtime.hour == 16 and cache_mtime.minute < 15))

            if not (is_post_market and cache_was_pre_close):
                df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
                if not df.empty:
                    if (now.date() - df.index[-1].date()).days == 0:
                        return df
        except Exception:
            pass

    # Ambil data baru dari Yahoo Finance
    start_date = (now.date() - datetime.timedelta(days=years * 365 + 30)).strftime("%Y-%m-%d")
    end_date = (now.date() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")

    try:
        ticker = yf.Ticker(sym)
        df = ticker.history(start=start_date, end=end_date, auto_adjust=False)

        if df.empty:
            # Coba ambil periode max jika tanggal spesifik kosong
            df = ticker.history(period=f"{years}y", auto_adjust=False)

        if not df.empty:
            # Standarisasi kolom
            df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
            df = df.dropna()
            df.index = pd.to_datetime(df.index).tz_localize(None) # Hilangkan timezone untuk konsistensi
            # Simpan ke cache
            df.to_csv(cache_file)
            return df
        else:
            raise ValueError(f"Tidak ada data ditemukan untuk simbol {sym}")
    except Exception as e:
        # Fallback ke cache lama jika offline atau error
        if os.path.exists(cache_file):
            return pd.read_csv(cache_file, index_col=0, parse_dates=True)
        raise RuntimeError(f"Gagal mengunduh data saham {sym}: {str(e)}")


def get_latest_price_summary(df: pd.DataFrame) -> dict:
    """Mengambil ringkasan harga dan pergerakan hari terakhir."""
    if df.empty or len(df) < 2:
        return {}
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    change = latest["Close"] - prev["Close"]
    pct_change = (change / prev["Close"]) * 100.0

    return {
        "date": df.index[-1].strftime("%d-%m-%Y"),
        "close": float(latest["Close"]),
        "open": float(latest["Open"]),
        "high": float(latest["High"]),
        "low": float(latest["Low"]),
        "volume": int(latest["Volume"]),
        "change": float(change),
        "pct_change": float(pct_change)
    }
