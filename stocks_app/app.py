import os
from flask import Flask, render_template, request, flash
from tensorflow.keras.models import load_model
import mysql.connector

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Needed for flash messages

# ========== MODEL LOADING SETUP ==========
MODEL_BASE_PATH = os.path.expanduser("~/DATA/models_lstm")

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

@app.route("/", methods=["GET", "POST"])
def home():
    stocks = get_stock_list()
    selected_stocks = [None, None, None]

    if request.method == "POST":
        for i in range(3):
            selected = request.form.get(f"stock{i+1}")
            selected_stocks[i] = selected
            try:
                model = load_stock_model(selected)
                flash(f"✅ Model loaded successfully for {selected}", "success")
            except Exception as e:
                flash(f"❌ {str(e)}", "error")

    return render_template("index.html", stocks=stocks, selected_stocks=selected_stocks)

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
    cursor.execute("SELECT DISTINCT Ticker FROM Stocks_data ORDER BY Ticker")
    tickers = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return tickers

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
