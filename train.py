import pandas as pd
import numpy as np
import lightgbm as lgb
import os
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder
from sklearn.impute import SimpleImputer
from keras.models import Sequential
from keras.layers import LSTM, Dense
from keras.callbacks import EarlyStopping
import warnings

warnings.filterwarnings("ignore")

# Constants
DATA_PATH = "/home/dragon/DATA/financedata.csv"
MODEL_DIR = "saved_models"
INVALID_DATE_LOG = "invalid_dates.csv"

# Create directory for models
os.makedirs(MODEL_DIR, exist_ok=True)

# Read CSV with mixed types
df = pd.read_csv(DATA_PATH, low_memory=False)

# Drop "Adj Close"
if "Adj Close" in df.columns:
    df.drop(columns=["Adj Close"], inplace=True)

# Log and remove rows with invalid dates
invalid_dates = df[~pd.to_datetime(df["Date"], errors="coerce").notna()]
if not invalid_dates.empty:
    print(f"Warning: {len(invalid_dates)} rows have invalid date format and were set to NaT.")
    invalid_dates.to_csv(INVALID_DATE_LOG, index=False)

df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
df = df.dropna(subset=["Date"])

# Convert relevant columns
for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

df.dropna(inplace=True)

# Encode Ticker as a category
df['Ticker'] = df['Ticker'].astype(str)

# Store model accuracy for each ticker
model_accuracies = {}

# Train separate model per stock ticker
tickers = df['Ticker'].unique()
for ticker in tickers:
    stock_df = df[df['Ticker'] == ticker].sort_values(by="Date")

    if len(stock_df) < 60:
        continue  # not enough data

    stock_df['Target'] = stock_df['Close'].shift(-1)
    stock_df.dropna(inplace=True)

    features = ['Open', 'High', 'Low', 'Close', 'Volume']
    X = stock_df[features]
    y = (stock_df['Target'] > stock_df['Close']).astype(int)  # Up (1) or Down (0)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, shuffle=False
    )

    best_acc = 0
    best_model = None
    patience = 3
    no_improve_count = 0

    # Try LightGBM first
    while best_acc < 0.90 and no_improve_count < patience:
        model = lgb.LGBMClassifier(n_estimators=100)
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        acc = accuracy_score(y_test, preds)

        if acc > best_acc:
            best_acc = acc
            best_model = model
            no_improve_count = 0
        else:
            no_improve_count += 1

    # Save if model is good
    if best_model and best_acc >= 0.90:
        model_path = os.path.join(MODEL_DIR, f"{ticker}_model.pkl")
        joblib.dump(best_model, model_path)

    model_accuracies[ticker] = best_acc

# Report accuracy
print("\nModel Accuracies:")
for ticker, acc in sorted(model_accuracies.items(), key=lambda x: -x[1]):
    print(f"{ticker}: {acc:.2%}")

print(f"\nSaved invalid date rows to '{INVALID_DATE_LOG}' if any were found.")
print(f"Models saved in '{MODEL_DIR}' for tickers with accuracy ≥ 90%.")
