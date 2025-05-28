import os
from flask import Flask, render_template, request, flash
from tensorflow.keras.models import load_model
import mysql.connector
import numpy as np
import pandas as pd
import joblib  # NEW
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Needed for flash messages

# ========== MODEL LOADING SETUP ==========
MODEL_BASE_PATH = os.path.expanduser("~/DATA/models_lstm")
LOOK_BACK = 20

def get_stock_list():
    with open("/home/dragon//GIT/StocksApp/company_list.txt", "r") as file:
        return [line.strip() for line in file if line.strip()]

def load_stock_model(stock):
    model_path = os.path.join(MODEL_BASE_PATH, stock, "model.h5")
    print(f"Loading model from: {model_path}")  # Debug
    if os.path.exists(model_path):
        model = load_model(model_path, compile=False)
        return model
    else:
        raise FileNotFoundError(f"Model not found for stock: {stock}")

# ========== DATABASE CONFIGURATION ==========
db_config = {
    "host": "104.238.220.190",
    "database": "stocksjbetadev_Stocks",
    "user": "stocksjbetadev",
    "password": "qZh]R0+inyo+"
}

# ========== DATA FETCHING & FILTERING ==========
def fetch_data(ticker=None, start_date=None, end_date=None):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    query = "SELECT * FROM Stocks_data WHERE 1=1"
    params = []

    if ticker:
        query += " AND Ticker = %s"
        params.append(ticker)
    if start_date:
        query += " AND Date >= %s"
        params.append(start_date)
    if end_date:
        query += " AND Date <= %s"
        params.append(end_date)

    query += " ORDER BY Date DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def get_unique_tickers():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT Ticker FROM Stocks_data")
    tickers = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return tickers

# ========== PREDICTION ROUTE ==========
@app.route("/", methods=["GET", "POST"])
def home():
    stocks = get_stock_list()
    selected_stocks = [None, None, None]
    predictions = []

    if request.method == "POST":
        for i in range(3):
            selected = request.form.get(f"stock{i+1}")
            selected_stocks[i] = selected
            try:
                if not selected:
                    continue

                # Load model
                model = load_stock_model(selected)

                # Fetch stock data
                stock_data = fetch_data(ticker=selected, start_date="2023-01-01", end_date=str(datetime.now().date()))
                df = pd.DataFrame(stock_data)
                df = df.sort_values("Date")

                # Preprocess (only 'Close')
                df_close = df["Close"].dropna().tail(LOOK_BACK).values.reshape(-1, 1)
                if len(df_close) < LOOK_BACK:
                    raise ValueError(f"Not enough data to predict for {selected}.")

                # Load scaler
                scaler_path = os.path.join(MODEL_BASE_PATH, selected, "scaler.pkl")
                if not os.path.exists(scaler_path):
                    raise FileNotFoundError(f"Scaler not found for stock: {selected}")

                scaler = joblib.load(scaler_path)
                scaled = scaler.transform(df_close)

                # Reshape for LSTM input
                X_input = scaled.reshape(1, LOOK_BACK, 1)

                # Predict and inverse transform
                prediction = model.predict(X_input)
                predicted_price = scaler.inverse_transform(prediction)[0][0]

                predictions.append([predicted_price])
                flash(f"✅ Prediction made successfully for {selected}", "success")

            except Exception as e:
                flash(f"❌ {selected or 'Unknown stock'}: {str(e)}", "error")
                predictions.append([])

    return render_template("index.html", stocks=stocks, selected_stocks=selected_stocks, predictions=predictions,enumerate = enumerate)

# ========== DATA TABLE VIEW ROUTE ==========
@app.route("/data", methods=["GET", "POST"])
def view_data():
    filters = {"ticker": "", "start_date": "", "end_date": ""}
    results = []
    tickers = get_unique_tickers()

    if request.method == "POST":
        filters["ticker"] = request.form.get("ticker")
        filters["start_date"] = request.form.get("start_date")
        filters["end_date"] = request.form.get("end_date")
        results = fetch_data(**filters)

    return render_template("data.html", data=results, filters=filters, tickers=tickers)

# ========== RUN APP ==========
if __name__ == "__main__":
    app.run(debug=True)
