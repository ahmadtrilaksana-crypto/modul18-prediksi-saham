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

class DynamicStockPredictor:
    """
    Mesin Prediksi Saham Kuantitatif dengan Rolling Window Dinamis.
    Secara otomatis bergeser dan memperbarui bobot model setiap ada data baru.
    """
    def __init__(self, window_size: int = 2500):
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

        if len(train_data) < 200:
            raise ValueError(f"Data historis tidak mencukupi (minimal 200 hari, tersedia {len(train_data)} hari)")

        X_train = train_data[self.feature_cols].values
        y_train = train_data["Target_Direction"].values

        # Scaling fitur
        X_train_scaled = self.scaler.fit_transform(X_train)
        today_scaled = self.scaler.transform(today_features.values)

        # Latih Ensemble Models
        self.rf_model.fit(X_train_scaled, y_train)
        self.gb_model.fit(X_train_scaled, y_train)

        # Prediksi Probabilitas Besok: Rata-rata dari RF dan GB
        prob_rf = self.rf_model.predict_proba(today_scaled)[0][1] # Probabilitas kelas 1 (Naik)
        prob_gb = self.gb_model.predict_proba(today_scaled)[0][1]
        win_probability = (prob_rf * 0.55 + prob_gb * 0.45) * 100.0

        # Estimasi Volatilitas & Rentang Target Harga Besok
        latest_close = float(today_row["Close"])
        latest_atr = float(today_row["ATR_14"]) if not np.isnan(today_row["ATR_14"]) else latest_close * 0.02
        
        # Proyeksi rentang harga besok
        expected_drift = ((win_probability - 50.0) / 50.0) * (latest_atr * 0.5)
        expected_close_tomorrow = latest_close + expected_drift
        projected_high = max(expected_close_tomorrow + latest_atr * 0.6, latest_close * 1.005)
        projected_low = min(expected_close_tomorrow - latest_atr * 0.6, latest_close * 0.995)

        # Hitung Stop Loss dan Take Profit Berbasis Rasio Risk/Reward 1 : 2
        stop_loss = latest_close - (latest_atr * 1.2)
        take_profit = latest_close + (latest_atr * 2.4)

        # Feature Importance (Faktor Penggerak Utama)
        importances = self.rf_model.feature_importances_
        feat_imp_df = pd.DataFrame({
            "Fitur": self.feature_cols,
            "Bobot": importances
        }).sort_values(by="Bobot", ascending=False)

        top_drivers = feat_imp_df.head(4)["Fitur"].tolist()

        # Rekomendasi Sinyal
        if win_probability >= 63.0:
            signal = "STRONG BUY"
            signal_color = "#22c55e" # Hijau Cerah
        elif win_probability >= 53.0:
            signal = "BUY"
            signal_color = "#38bdf8" # Biru Langit
        elif win_probability >= 47.0:
            signal = "HOLD / NEUTRAL"
            signal_color = "#a1a1aa" # Abu-abu
        elif win_probability >= 38.0:
            signal = "SELL / REDUCE"
            signal_color = "#fb923c" # Oranye
        else:
            signal = "STRONG AVOID"
            signal_color = "#ef4444" # Merah

        return {
            "latest_date": df_feat.index[-1].strftime("%d-%m-%Y"),
            "current_price": latest_close,
            "win_probability": round(win_probability, 1),
            "signal": signal,
            "signal_color": signal_color,
            "projected_close": round(expected_close_tomorrow, 1),
            "projected_range": (round(projected_low, 1), round(projected_high, 1)),
            "suggested_tp": round(take_profit, 1),
            "suggested_sl": round(stop_loss, 1),
            "atr_volatility": round(latest_atr, 1),
            "training_samples": len(train_data),
            "top_drivers": top_drivers
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
