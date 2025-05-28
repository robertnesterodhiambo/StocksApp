import os
from flask import Flask, render_template, request, flash
from tensorflow.keras.models import load_model

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Needed for flash messages

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

if __name__ == "__main__":
    app.run(debug=True)
