import sys
import os

# Add parent directory to sys.path for config import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import yfinance as yf
import time
from config import *
MARKETCAP_THRESHOLD = 1_000_000_000
def format_market_cap(value):
    if value is None or value == 0:
        return "0"
    units = ['', 'K', 'M', 'B', 'T']
    k = 1000.0
    magnitude = 0
    while abs(value) >= k and magnitude < len(units) - 1:
        magnitude += 1
        value /= k
    return f"{value:.2f}{units[magnitude]}"

def is_valid_ticker(ticker):
    try:
        info = yf.Ticker(ticker).info

        if not info or 'regularMarketPrice' not in info or 'marketCap' not in info:
            return False, "Missing price or marketCap data"

        market_cap = info.get('marketCap', 0)
        if not market_cap:
            return False, "Market cap data missing or zero"
        if market_cap < MARKETCAP_THRESHOLD:
            return False, f"Market cap below threshold ({format_market_cap(market_cap)})"
        
        return True, market_cap

    except Exception as e:
        return False, f"Error: {e}"

def clean_csv_tickers(csv_path, output_path, column_name=None):
    df = pd.read_csv(csv_path)

    if column_name is None:
        column_name = df.columns[0]

    tickers = df[column_name].astype(str)
    valid_tickers = []
    invalid_tickers = []

    print("Checking tickers...")

    for ticker in tickers:
        time.sleep(0.5)  # polite rate limiting
        valid, reason_or_marketcap = is_valid_ticker(ticker)
        if valid:
            valid_tickers.append(ticker)
        else:
            print(f"Excluded {ticker}: {reason_or_marketcap}")
            invalid_tickers.append(ticker)

    cleaned_df = pd.DataFrame(valid_tickers, columns=[column_name])
    cleaned_df.to_csv(output_path, index=False)

    print(f"\nDone. Removed {len(invalid_tickers)} invalid tickers.")
    print(f"Cleaned CSV saved to: {output_path}")

# Example usage
if __name__ == "__main__":
    clean_csv_tickers('../data/usa_stock.csv', '../data/usa_stock_post_mcap_filter.csv', column_name='ticker')
