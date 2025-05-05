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

# SQL queries
drop_table_sql = "DROP TABLE IF EXISTS Stocks_data"

create_table_sql = """
CREATE TABLE Stocks_data (
    Date DATE,
    Open FLOAT,
    High FLOAT,
    Low FLOAT,
    Close FLOAT,
    Volume BIGINT,
    Ticker VARCHAR(10)
)
"""

insert_sql = """
INSERT INTO Stocks_data (Date, Open, High, Low, Close, Volume, Ticker)
VALUES (%s, %s, %s, %s, %s, %s, %s)
"""

def upload_to_mysql(batch_size=100000):
    try:
        # Connect to MySQL
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        print("✅ Connected to database")

        # Drop and recreate table
        cursor.execute(drop_table_sql)
        print("🗑️ Dropped existing Stocks_data table")

        cursor.execute(create_table_sql)
        print("🧱 Recreated Stocks_data table")

        # Prepare records with NaNs converted to None (NULL in MySQL)
        records = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Ticker']].where(pd.notnull(df), None).values.tolist()

        # Insert in batches
        total = len(records)
        for i in range(0, total, batch_size):
            batch = records[i:i + batch_size]
            cursor.executemany(insert_sql, batch)
            conn.commit()
            print(f"✅ Inserted rows {i+1} to {min(i+batch_size, total)}")

    except Error as e:
        print(f"❌ Error: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
            print("🔌 Connection closed")

if __name__ == '__main__':
    upload_to_mysql()
