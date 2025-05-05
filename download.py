import yfinance as yf
import pandas as pd
import datetime
import os

# Load tickers from file
with open('company_list.txt', 'r') as file:
    tickers = [line.strip() for line in file if line.strip()]

# Set date range
start_date = '2000-01-01'
end_date = datetime.datetime.today().strftime('%Y-%m-%d')

# Set output path
output_path = '/home/dragon/DATA/financedata.csv'
os.makedirs(os.path.dirname(output_path), exist_ok=True)  # Ensure directory exists

# Write headers only once
header_written = False

for ticker in tickers:
    try:
        print(f"⬇️ Downloading {ticker}...")
        df = yf.download(ticker, start=start_date, end=end_date, auto_adjust=True)

        if df.empty:
            print(f"⚠️ No data for {ticker}")
            continue

        df['Ticker'] = ticker
        df = df.reset_index()

        # Append to CSV
        df.to_csv(output_path, mode='a', header=not header_written, index=False)
        header_written = True
        print(f"✅ Saved data for {ticker}")

    except Exception as e:
        print(f"❌ Error downloading {ticker}: {e}")
