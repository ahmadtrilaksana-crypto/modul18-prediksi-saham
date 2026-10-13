"""
Modul 18: The Trilaksana Suite — Data Ingestion & Cache Engine
Mengambil dan mengelola data historis saham (10 tahun) secara otomatis dengan caching lokal.
"""

import os
import datetime
import pandas as pd
import yfinance as yf

# Daftar Watchlist Default Bursa Efek Indonesia (IDX) & Global
DEFAULT_WATCHLISTS = {
    "Komoditas & Tambang": [
        ("ANTM.JK", "Aneka Tambang Tbk"),
        ("INCO.JK", "Vale Indonesia Tbk"),
        ("PTBA.JK", "Bukit Asam Tbk"),
        ("MDKA.JK", "Merdeka Copper Gold Tbk"),
        ("ADRO.JK", "Adaro Energy Indonesia Tbk"),
        ("MBMA.JK", "Merdeka Battery Materials Tbk"),
        ("HRUM.JK", "Harum Energy Tbk"),
        ("TINS.JK", "Timah Tbk")
    ],
    "Perbankan (Big Banks)": [
        ("BBCA.JK", "Bank Central Asia Tbk"),
        ("BBRI.JK", "Bank Rakyat Indonesia Tbk"),
        ("BMRI.JK", "Bank Mandiri Tbk"),
        ("BBNI.JK", "Bank Negara Indonesia Tbk"),
        ("BRIS.JK", "Bank Syariah Indonesia Tbk")
    ],
    "Konglomerasi & Konsumer": [
        ("ASII.JK", "Astra International Tbk"),
        ("TLKM.JK", "Telkom Indonesia Tbk"),
        ("ICBP.JK", "Indofood CBP Sukses Makmur Tbk"),
        ("UNVR.JK", "Unilever Indonesia Tbk"),
        ("GOTO.JK", "GoTo Gojek Tokopedia Tbk")
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

def fetch_stock_data(symbol: str, years: int = 10, force_refresh: bool = False) -> pd.DataFrame:
    """
    Mengambil data historis OHLCV selama N tahun dengan mekanisme cache cerdas.
    Jika cache lokal sudah diperbarui hari ini, gunakan cache lokal.
    """
    sym = normalize_ticker(symbol)
    clean_sym = sym.replace("^", "IDX_").replace(".", "_")
    cache_file = os.path.join(get_data_dir(), f"{clean_sym}_{years}y.csv")

    today_str = datetime.date.today().isoformat()

    # Cek apakah cache valid hari ini
    if not force_refresh and os.path.exists(cache_file):
        try:
            # Periksa waktu pembuatan cache file
            cache_mtime = datetime.datetime.fromtimestamp(os.path.getmtime(cache_file))
            now = datetime.datetime.now()
            
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
    start_date = (datetime.date.today() - datetime.timedelta(days=years * 365 + 30)).strftime("%Y-%m-%d")
    end_date = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")

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
