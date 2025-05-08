import pandas as pd
import mysql.connector
from mysql.connector import Error

# Database configuration
db_config = {
    "host": "104.238.220.190",
    "database": "stocksjbetadev_Stocks",
    "user": "stocksjbetadev",
    "password": "qZh]R0+inyo+"
}

# CSV file path
csv_path = '/home/dragon/DATA/financedata.csv'

# Read CSV
df = pd.read_csv(csv_path)

# Drop 'Adj Close' if it exists
if 'Adj Close' in df.columns:
    df = df.drop(columns=['Adj Close'])

# SQL to create the table if it doesn't exist
create_table_sql = """
CREATE TABLE IF NOT EXISTS Stocks_data (
    Date DATE,
    Open FLOAT,
    High FLOAT,
    Low FLOAT,
    Close FLOAT,
    Volume BIGINT,
    Ticker VARCHAR(10),
    PRIMARY KEY (Date, Ticker)
)
"""

# SQL to insert or update if duplicate exists
insert_sql = """
INSERT INTO Stocks_data (Date, Open, High, Low, Close, Volume, Ticker)
VALUES (%s, %s, %s, %s, %s, %s, %s)
ON DUPLICATE KEY UPDATE
    Open = VALUES(Open),
    High = VALUES(High),
    Low = VALUES(Low),
    Close = VALUES(Close),
    Volume = VALUES(Volume)
"""

def upload_to_mysql(batch_size=100000):
    try:
        # Connect to MySQL
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        print("✅ Connected to database")

        # Create table if it doesn't exist
        cursor.execute(create_table_sql)
        print("🧱 Ensured Stocks_data table exists")

        # Prepare records with NaNs converted to None
        records = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Ticker']].where(pd.notnull(df), None).values.tolist()

        # Insert in batches with update on duplicate key
        total = len(records)
        for i in range(0, total, batch_size):
            batch = records[i:i + batch_size]
            cursor.executemany(insert_sql, batch)
            conn.commit()
            print(f"✅ Upserted rows {i+1} to {min(i+batch_size, total)}")

    except Error as e:
        print(f"❌ Error: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
            print("🔌 Connection closed")

if __name__ == '__main__':
    upload_to_mysql()
