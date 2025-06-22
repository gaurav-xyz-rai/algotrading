# === utilities/file_handling.py ===
import pandas as pd
def load_tickers_from_csv(csv_file, suffix=''):
    try:
        df = pd.read_csv(csv_file, header=None, names=["ticker"])
        tickers = df['ticker'].dropna().unique().tolist()
        tickers = [str(t).strip() + suffix for t in tickers]
        return tickers
    except Exception as e:
        print(f"Error loading tickers: {e}")
        return []