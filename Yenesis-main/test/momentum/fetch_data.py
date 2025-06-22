import yfinance as yf
import pandas as pd

def fetch_stock_data(ticker, period="5y", interval="1d"):
    print(f"Fetching {period} of data for {ticker}...")
    stock = yf.Ticker(ticker)
    data = stock.history(period=period, interval=interval)
    print(f"✅ Retrieved {len(data)} rows.")
    return data

if __name__ == "__main__":
    ticker = "AAPL"  # Change to any stock symbol
    df = fetch_stock_data(ticker)
    print(df.head())  # Show first few rows
    # Optionally save to CSV
    df.to_csv(f"{ticker}_5y_data.csv")
