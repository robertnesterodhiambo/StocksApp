from flask import Flask, render_template

app = Flask(__name__)

def get_stock_list():
    with open("company_list.txt", "r") as file:
        return [line.strip() for line in file if line.strip()]

@app.route("/")
def home():
    stocks = get_stock_list()
    return render_template("index.html", stocks=stocks)

if __name__ == "__main__":
    app.run(debug=True)
