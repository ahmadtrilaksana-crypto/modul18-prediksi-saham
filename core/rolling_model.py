"""
Modul 18: The Trilaksana Suite — Dynamic Rolling Model & Machine Learning Engine
Melatih model probabilitas dinamis berbasis Rolling-Window (10 tahun) untuk memprediksi harga & arah besok.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score

from core.indicators import calculate_technical_features, get_feature_columns

def round_to_idx_tick(price: float) -> int:
    """
    Membulatkan harga sesuai fraksi resmi bursa BEI (IDX Tick Size):
    - Harga < Rp 200: kelipatan Rp 1
    - Harga Rp 200 s/d < Rp 500: kelipatan Rp 2
    - Harga Rp 500 s/d < Rp 2.000: kelipatan Rp 5
    - Harga Rp 2.000 s/d < Rp 5.000: kelipatan Rp 10
    - Harga >= Rp 5.000: kelipatan Rp 25
    """
    if price is None or price <= 0:
        return 0
    p = float(price)
    if p < 200:
        return int(round(p / 1.0) * 1)
    elif p < 500:
        return int(round(p / 2.0) * 2)
    elif p < 2000:
        return int(round(p / 5.0) * 5)
    elif p < 5000:
        return int(round(p / 10.0) * 10)
    else:
        return int(round(p / 25.0) * 25)

class DynamicStockPredictor:
    """
    Mesin Prediksi Saham Kuantitatif dengan Rolling Window Dinamis (Short-Term Adaptive).
    Secara otomatis bergeser dan memperbarui bobot model setiap ada data baru (default 500 hari bursa ~ 2 tahun).
    """
    def __init__(self, window_size: int = 500):
        self.window_size = window_size
        self.feature_cols = get_feature_columns()
        self.scaler = StandardScaler()
        # Ensemble Model: Random Forest + Gradient Boosting
        self.rf_model = RandomForestClassifier(
            n_estimators=120,
            max_depth=5,
            min_samples_split=8,
            min_samples_leaf=4,
            random_state=42,
            n_jobs=-1
        )
        self.gb_model = GradientBoostingClassifier(
            n_estimators=80,
            learning_rate=0.05,
            max_depth=3,
            random_state=42
        )

    def prepare_data(self, df_raw: pd.DataFrame) -> pd.DataFrame:
        """Menghitung fitur teknikal dan membuang baris awal yang mengandung NaN."""
        df_feat = calculate_technical_features(df_raw)
        return df_feat

    def train_and_predict_tomorrow(self, df_feat: pd.DataFrame) -> dict:
        """
        Melatih model pada jendela historis (N hari terakhir) dan
        memprediksi probabilitas kenaikan harga untuk hari bursa BESOK.
        """
        # Ambil baris terakhir sebagai fitur HARI INI untuk memprediksi BESOK
        today_row = df_feat.iloc[-1]
        today_features = today_row[self.feature_cols].to_frame().T

        # Data training adalah data masa lalu yang sudah memiliki Target_Direction (semua baris sebelum baris terakhir)
        train_data = df_feat.iloc[:-1].dropna(subset=self.feature_cols + ["Target_Direction"])

        # Terapkan batas Rolling Window (misal 2.500 hari bursa ~ 10 tahun)
        if len(train_data) > self.window_size:
            train_data = train_data.iloc[-self.window_size:]

        if len(train_data) < 150:
            raise ValueError(f"Data historis tidak mencukupi (minimal 150 hari, tersedia {len(train_data)} hari)")

        X_train = train_data[self.feature_cols].values
        y_train_1d = train_data["Target_Direction"].values
        # Target 5-Day Swing Direction jika tersedia di DataFrame
        y_train_5d = train_data["Target_5d_Direction"].values if "Target_5d_Direction" in train_data.columns else y_train_1d

        # Scaling fitur
        X_train_scaled = self.scaler.fit_transform(X_train)
        today_scaled = self.scaler.transform(today_features.values)

        # Latih Ensemble Models: RF fokus ke arah momentum mikro (T+1), GB fokus ke arah trend swing (T+5)
        self.rf_model.fit(X_train_scaled, y_train_1d)
        self.gb_model.fit(X_train_scaled, y_train_5d)

        # Prediksi Probabilitas: Komposit Harmonisasi (T+1 Micro Momentum 40% + T+5 Swing Direction 60%)
        prob_rf = self.rf_model.predict_proba(today_scaled)[0][1] # Probabilitas kelas 1 (T+1)
        prob_gb = self.gb_model.predict_proba(today_scaled)[0][1] # Probabilitas kelas 1 (T+5)
        win_probability = (prob_rf * 0.40 + prob_gb * 0.60) * 100.0

        # Estimasi Volatilitas & Rentang Target Harga Besok
        latest_close = float(today_row["Close"])
        latest_atr = float(today_row["ATR_14"]) if not np.isnan(today_row["ATR_14"]) else latest_close * 0.02
        today_return = float(today_row.get("Return_1d", 0.0))
        
        # Proyeksi rentang harga besok
        expected_drift = ((win_probability - 50.0) / 50.0) * (latest_atr * 0.5)
        expected_close_tomorrow = round_to_idx_tick(latest_close + expected_drift)
        projected_high = round_to_idx_tick(max(expected_close_tomorrow + latest_atr * 0.6, latest_close * 1.005))
        projected_low = round_to_idx_tick(min(expected_close_tomorrow - latest_atr * 0.6, latest_close * 0.995))

        # PILAR 1: Plafon Batas Risiko Maksimal (Institutional Risk Cap)
        # Menghindari kasus Stop Loss terlalu dalam (seperti -11% pada saham liar)
        # Toleransi Stop Loss dibatasi maksimal 5.5% dan minimal 2.0% dari harga masuk
        raw_sl_distance = latest_atr * 1.2
        max_sl_distance = latest_close * 0.055  # Plafon SL maksimal 5.5%
        min_sl_distance = latest_close * 0.020  # Minimum SL 2.0% agar tahan noise
        final_sl_dist = max(min(raw_sl_distance, max_sl_distance), min_sl_distance)

        stop_loss = round_to_idx_tick(latest_close - final_sl_dist)
        actual_risk = latest_close - stop_loss
        # Target Take Profit terkunci tepat 2x jarak risiko aktual (Rasio Risk/Reward 1 : 2.0)
        take_profit = round_to_idx_tick(latest_close + (actual_risk * 2.0))

        # Feature Importance (Faktor Penggerak Utama)
        importances = self.rf_model.feature_importances_
        feat_imp_df = pd.DataFrame({
            "Fitur": self.feature_cols,
            "Bobot": importances
        }).sort_values(by="Bobot", ascending=False)

        top_drivers = feat_imp_df.head(4)["Fitur"].tolist()

        # PILAR 2: Filter Anti-Pisau Jatuh (Anti-Falling Knife Filter)
        # Jika hari ini harga sedang anjlok tajam (<= -3.0%), jangan langsung beri STRONG BUY
        is_falling_knife = today_return <= -0.030

        # Rekomendasi Sinyal (Spesifikasi Kalibrasi Dr. Ahmad Raymond)
        if win_probability >= 55.0:
            if is_falling_knife:
                signal = "SPECULATIVE BUY / WAIT REVERSAL"
                signal_color = "#f59e0b" # Oranye (Peringatan Pisau Jatuh)
            else:
                signal = "STRONG BUY"
                signal_color = "#22c55e" # Hijau Cerah
        elif win_probability >= 53.0:
            signal = "SPECULATIVE BUY / CICIL"
            signal_color = "#f59e0b" # Kuning / Oranye
        elif win_probability >= 50.0:
            signal = "HOLD / NEUTRAL"
            signal_color = "#94a3b8" # Abu-abu Netral
        else:
            signal = "AVOID / WAIT & SEE"
            signal_color = "#ef4444" # Merah Proteksi Modal

        # PILAR 3: Estimasi Durasi Tunggu Dinamis (First-Passage Time Stochastic Model)
        # Berbasis Teori Hit Time Brownian Motion: E[T] = Target_TP / Expected_Daily_Drift (mu_d)
        target_tp_pct = ((take_profit - latest_close) / latest_close) * 100.0 if latest_close > 0 else 5.0
        tp_pct = abs(float(target_tp_pct))
        if tp_pct < 1.0:
            tp_pct = tp_pct * 100.0

        daily_drift_pct = ((expected_close_tomorrow - latest_close) / latest_close) * 100.0 if latest_close > 0 else 1.0
        # Pengaman analitis: drift terarah minimal 0.8% per hari untuk saham yang lolos saringan beli
        mu_d = max(0.8, daily_drift_pct)

        calculated_days = int(round(tp_pct / mu_d))
        max_holding_days = max(3, min(15, calculated_days))

        return {
            "latest_date": df_feat.index[-1].strftime("%d-%m-%Y"),
            "current_price": round_to_idx_tick(latest_close),
            "win_probability": round(win_probability, 1),
            "signal": signal,
            "signal_color": signal_color,
            "projected_close": float(expected_close_tomorrow),
            "projected_range": (float(projected_low), float(projected_high)),
            "suggested_tp": float(take_profit),
            "suggested_sl": float(stop_loss),
            "atr_volatility": round(latest_atr, 1),
            "training_samples": len(train_data),
            "top_drivers": top_drivers,
            "max_holding_days": max_holding_days,
            "horizon_days": f"Maks. {max_holding_days} Hari Bursa",
            "is_falling_knife": is_falling_knife
        }

    def walk_forward_backtest(self, df_feat: pd.DataFrame, test_days: int = 60) -> dict:
        """
        Melakukan simulasi pengujian historis (Walk-Forward Validation)
        pada N hari perdagangan terakhir tanpa bias melihat masa depan (Zero Data-Leakage).
        """
        valid_df = df_feat.dropna(subset=self.feature_cols + ["Target_Direction"]).copy()
        if len(valid_df) < test_days + 150:
            test_days = max(20, len(valid_df) - 150)

        preds = []
        actuals = []
        dates = []
        prices = []

        start_idx = len(valid_df) - test_days
        for idx in range(start_idx, len(valid_df)):
            sub_train = valid_df.iloc[:idx]
            if len(sub_train) > self.window_size:
                sub_train = sub_train.iloc[-self.window_size:]

            X_tr = self.scaler.fit_transform(sub_train[self.feature_cols].values)
            y_tr = sub_train["Target_Direction"].values

            clf = RandomForestClassifier(n_estimators=50, max_depth=4, random_state=42, n_jobs=-1)
            clf.fit(X_tr, y_tr)

            today_vec = self.scaler.transform(valid_df.iloc[idx][self.feature_cols].values.reshape(1, -1))
            prob = clf.predict_proba(today_vec)[0][1]

            preds.append(1 if prob >= 0.50 else 0)
            actuals.append(int(valid_df.iloc[idx]["Target_Direction"]))
            dates.append(valid_df.index[idx].strftime("%d/%m/%Y"))
            prices.append(float(valid_df.iloc[idx]["Close"]))

        acc = accuracy_score(actuals, preds) * 100.0

        # Hitung Win-Rate jika hanya beli saat sinyal Bullish
        bullish_trades = sum(1 for p, a in zip(preds, actuals) if p == 1 and a == 1)
        total_bullish = sum(1 for p in preds if p == 1)
        bullish_win_rate = (bullish_trades / total_bullish * 100.0) if total_bullish > 0 else 0.0

        return {
            "test_days": test_days,
            "overall_accuracy": round(acc, 1),
            "bullish_win_rate": round(bullish_win_rate, 1),
            "total_trades": total_bullish,
            "dates": dates,
            "actuals": actuals,
            "preds": preds,
            "prices": prices
        }

def calculate_injury_time(entry_price: float, current_price: float, tp_price: float, atr_val: float) -> dict:
    """
    Menghitung kalkulasi Tambahan Waktu Matematis (Injury Time Wasit)
    berdasarkan sisa jarak menuju target TP dan kecepatan laju harian (ATR).
    """
    if entry_price <= 0 or current_price <= 0 or tp_price <= 0:
        return {"injury_days": 0, "status": "EXPIRED", "reason": "Data harga tidak valid"}

    current_gain_pct = ((current_price - entry_price) / entry_price) * 100.0
    target_tp_pct = ((tp_price - entry_price) / entry_price) * 100.0
    sisa_jarak_pct = target_tp_pct - current_gain_pct

    atr_pct = (float(atr_val) / float(current_price)) * 100.0 if current_price > 0 else 2.0
    if atr_pct <= 0:
        atr_pct = 2.0
    kecepatan_harian = max(1.0, atr_pct * 0.50)

    # Syarat Injury Time (Wasit Sepak Bola):
    # 1. Posisi saat ini sedang profit (>= +3.0%)
    # 2. Sisa jarak ke TP tinggal sedikit (0 < sisa jarak <= 4.5%)
    if current_gain_pct >= 3.0 and 0 < sisa_jarak_pct <= 4.5:
        calculated_days = int(round(sisa_jarak_pct / kecepatan_harian))
        injury_days = max(1, min(3, calculated_days)) # Maksimal 1 s/d 3 hari
        return {
            "injury_days": injury_days,
            "status": "INJURY_TIME_GRANTED",
            "current_gain_pct": round(current_gain_pct, 2),
            "sisa_jarak_pct": round(sisa_jarak_pct, 2),
            "reason": f"Sedang berlari kencang (+{current_gain_pct:.1f}%), sisa jarak ke TP tinggal {sisa_jarak_pct:.1f}%"
        }
    else:
        return {
            "injury_days": 0,
            "status": "WHISTLE_BLOWN",
            "current_gain_pct": round(current_gain_pct, 2),
            "sisa_jarak_pct": round(sisa_jarak_pct, 2),
            "reason": "Momentum habis / tidak memenuhi syarat tambahan waktu"
        }
