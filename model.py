import pandas as pd
from pmdarima import auto_arima
import joblib
import os
from sklearn.metrics import mean_absolute_percentage_error
import numpy as np
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)
# Load and clean data
df = pd.read_csv('/home/dragon/DATA/financedata.csv', low_memory=False)

df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
df = df.dropna(subset=['Date'])
df = df.drop(columns=['Adj Close'])

cols_to_convert = ['Open', 'High', 'Low', 'Close', 'Volume']
for col in cols_to_convert:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Create output directory
os.makedirs('models', exist_ok=True)

# Process each ticker
tickers = df['Ticker'].unique()

for ticker in tickers:
    print(f"\n🔍 Training model for {ticker}...")

    stock_data = df[df['Ticker'] == ticker].sort_values('Date')
    ts = stock_data['Close'].dropna()

    if len(ts) < 50:
        print(f"❌ Not enough data for {ticker}, skipping.")
        continue

    # Train/test split (80/20)
    train_size = int(len(ts) * 0.8)
    train, test = ts[:train_size], ts[train_size:]

    try:
        # Initial ARIMA (non-seasonal, quick search)
        model = auto_arima(train, seasonal=False, stepwise=True, suppress_warnings=True, error_action='ignore')

        # Forecast
        forecast = model.predict(n_periods=len(test))

        # Compute accuracy
        mape = mean_absolute_percentage_error(test, forecast)
        accuracy = 100 * (1 - mape)

        print(f"📊 Accuracy for {ticker}: {accuracy:.2f}%")

        if accuracy < 90:
            print(f"🔧 Fine-tuning model for {ticker}...")
            model = auto_arima(train, seasonal=True, m=5, stepwise=True, suppress_warnings=True, error_action='ignore')

            forecast = model.predict(n_periods=len(test))
            mape = mean_absolute_percentage_error(test, forecast)
            accuracy = 100 * (1 - mape)
            print(f"🔁 Retested Accuracy: {accuracy:.2f}%")

        # Save if acceptable
        if accuracy >= 80:  # You can keep this as 90 or relax slightly
            joblib.dump(model, f'models/{ticker}_arima.pkl')
            print(f"✅ Saved model for {ticker} with {accuracy:.2f}% accuracy")
        else:
            print(f"⚠️ Model for {ticker} not accurate enough ({accuracy:.2f}%), not saved.")

    except Exception as e:
        print(f"❌ Error training {ticker}: {e}")
