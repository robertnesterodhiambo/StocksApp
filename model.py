import os
import gc
import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_percentage_error
import matplotlib.pyplot as plt
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.callbacks import EarlyStopping
import tensorflow as tf
import warnings

warnings.filterwarnings("ignore")

# Set seeds for reproducibility
np.random.seed(42)
tf.random.set_seed(42)

# Parameters
look_back = 20
batch_size = 25
base_model_dir = 'models_lstm'
os.makedirs(base_model_dir, exist_ok=True)

# Load data
df = pd.read_csv('/home/dragon/DATA/financedata.csv', low_memory=False)
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
df = df.dropna(subset=['Date'])

# Convert price columns
for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

tickers = df['Ticker'].dropna().unique()

# Create sequences for LSTM input
def create_sequences(data, look_back):
    X, y = [], []
    for i in range(len(data) - look_back):
        X.append(data[i:i+look_back])
        y.append(data[i+look_back])
    return np.array(X), np.array(y)

# Training loop
for batch_start in range(0, len(tickers), batch_size):
    batch = tickers[batch_start:batch_start + batch_size]
    print(f"\n🚀 Processing batch {batch_start // batch_size + 1} ({len(batch)} tickers)")

    for ticker in batch:
        try:
            print(f"\n🔍 Training LSTM model for {ticker}...")

            data = df[df['Ticker'] == ticker].sort_values('Date')
            ts = data['Close'].dropna().values.reshape(-1, 1)

            if len(ts) < 60:
                print(f"❌ Not enough data for {ticker}, skipping.")
                continue

            scaler = MinMaxScaler()
            ts_scaled = scaler.fit_transform(ts)

            X, y = create_sequences(ts_scaled, look_back)
            if len(X) == 0:
                print(f"⚠️ Not enough sequence data for {ticker}, skipping.")
                continue

            split = int(len(X) * 0.8)
            X_train, X_test = X[:split], X[split:]
            y_train, y_test = y[:split], y[split:]

            X_train = X_train.reshape((X_train.shape[0], X_train.shape[1], 1))
            X_test = X_test.reshape((X_test.shape[0], X_test.shape[1], 1))

            model = Sequential([
                LSTM(50, return_sequences=False, input_shape=(look_back, 1)),
                Dense(1)
            ])

            model.compile(optimizer='adam', loss='mse')
            es = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)

            model.fit(X_train, y_train, validation_split=0.2,
                      epochs=100, batch_size=32, verbose=0, callbacks=[es])

            y_pred = model.predict(X_test)
            y_test_inv = scaler.inverse_transform(y_test.reshape(-1, 1))
            y_pred_inv = scaler.inverse_transform(y_pred)

            mape = mean_absolute_percentage_error(y_test_inv, y_pred_inv)
            accuracy = max(0, 100 * (1 - mape))

            print(f"📊 Accuracy for {ticker}: {accuracy:.2f}%")

            # Save model, scaler, and plot if accuracy is acceptable
            if accuracy >= 80:
                ticker_dir = os.path.join(base_model_dir, ticker)
                os.makedirs(ticker_dir, exist_ok=True)

                model.save(os.path.join(ticker_dir, 'model.h5'))
                joblib.dump(scaler, os.path.join(ticker_dir, 'scaler.pkl'))

                # Save plot to file instead of showing
                plt.figure(figsize=(10, 5))
                plt.plot(y_test_inv, label='Actual')
                plt.plot(y_pred_inv, label='Predicted')
                plt.title(f"{ticker} LSTM Forecast")
                plt.legend()
                plt.tight_layout()

                plot_path = os.path.join(ticker_dir, 'forecast_plot.png')
                plt.savefig(plot_path)
                plt.close()

                print(f"✅ Saved model and plot for {ticker} in '{ticker_dir}'")
            else:
                print(f"⚠️ Model for {ticker} not accurate enough ({accuracy:.2f}%), not saved.")

        except Exception as e:
            print(f"❌ Error training {ticker}: {e}")

        finally:
            gc.collect()

print("\n🎉 All LSTM batches completed.")
