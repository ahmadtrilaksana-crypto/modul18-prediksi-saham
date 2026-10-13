"""
Modul 18: The Trilaksana Suite — Technical Indicators & Feature Engineering
Menghitung indikator teknikal komprehensif, volatilitas, dan variabel target untuk machine learning.
"""

import numpy as np
import pandas as pd

def calculate_technical_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Menghitung rangkaian indikator teknikal kuantitatif dari data OHLCV.
    """
    data = df.copy()

    # 1. Moving Averages
    data["SMA_5"] = data["Close"].rolling(window=5).mean()
    data["SMA_20"] = data["Close"].rolling(window=20).mean()
    data["SMA_50"] = data["Close"].rolling(window=50).mean()
    data["SMA_200"] = data["Close"].rolling(window=200).mean()
    
    data["EMA_12"] = data["Close"].ewm(span=12, adjust=False).mean()
    data["EMA_26"] = data["Close"].ewm(span=26, adjust=False).mean()

    # Jarak harga relatif terhadap MA (% di atas/bawah MA)
    data["Dist_SMA20"] = (data["Close"] - data["SMA_20"]) / data["SMA_20"]
    data["Dist_SMA50"] = (data["Close"] - data["SMA_50"]) / data["SMA_50"]
    data["Dist_SMA200"] = (data["Close"] - data["SMA_200"]) / data["SMA_200"]

    # 2. MACD (Moving Average Convergence Divergence)
    data["MACD"] = data["EMA_12"] - data["EMA_26"]
    data["MACD_Signal"] = data["MACD"].ewm(span=9, adjust=False).mean()
    data["MACD_Hist"] = data["MACD"] - data["MACD_Signal"]

    # 3. RSI (Relative Strength Index - 14 Periode)
    delta = data["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / (avg_loss + 1e-9)
    data["RSI_14"] = 100 - (100 / (1 + rs))

    # 4. Bollinger Bands (20 Periode, 2 STD)
    std_20 = data["Close"].rolling(window=20).std()
    data["BB_Upper"] = data["SMA_20"] + (std_20 * 2)
    data["BB_Lower"] = data["SMA_20"] - (std_20 * 2)
    data["BB_Width"] = (data["BB_Upper"] - data["BB_Lower"]) / (data["SMA_20"] + 1e-9)
    data["BB_Pct"] = (data["Close"] - data["BB_Lower"]) / (data["BB_Upper"] - data["BB_Lower"] + 1e-9)

    # 5. ATR (Average True Range - 14 Periode) untuk Pengukuran Volatilitas & Stop-Loss
    high_low = data["High"] - data["Low"]
    high_close = (data["High"] - data["Close"].shift(1)).abs()
    low_close = (data["Low"] - data["Close"].shift(1)).abs()
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    data["ATR_14"] = true_range.rolling(window=14).mean()
    data["ATR_Pct"] = data["ATR_14"] / (data["Close"] + 1e-9)

    # 6. Returns & Lag Features
    data["Return_1d"] = data["Close"].pct_change()
    data["Return_2d"] = data["Close"].pct_change(2)
    data["Return_3d"] = data["Close"].pct_change(3)
    data["Return_5d"] = data["Close"].pct_change(5)

    data["Lag_Ret_1"] = data["Return_1d"].shift(1)
    data["Lag_Ret_2"] = data["Return_1d"].shift(2)
    data["Lag_Ret_3"] = data["Return_1d"].shift(3)

    # 7. Volume Activity
    data["Vol_SMA20"] = data["Volume"].rolling(window=20).mean()
    data["Vol_Ratio"] = data["Volume"] / (data["Vol_SMA20"] + 1e-9)

    # 8. Target Variables (Hanya untuk Training — bernilai NaN pada baris terakhir hari ini)
    data["Target_Return"] = data["Close"].shift(-1) / data["Close"] - 1.0
    data["Target_Direction"] = (data["Target_Return"] > 0).astype(int)

    return data

def get_feature_columns() -> list:
    """Mengembalikan daftar nama kolom fitur yang digunakan untuk pelatihan model."""
    return [
        "Dist_SMA20", "Dist_SMA50", "Dist_SMA200",
        "MACD", "MACD_Signal", "MACD_Hist",
        "RSI_14", "BB_Width", "BB_Pct",
        "ATR_Pct", "Return_1d", "Return_2d", "Return_3d", "Return_5d",
        "Lag_Ret_1", "Lag_Ret_2", "Lag_Ret_3", "Vol_Ratio"
    ]
