# === main.py ===
import time
import pandas as pd
from strategies.value.ema_pullback import EMAPullbackAnalyzer
from strategies.value.etf_dip import ETFDipBuyer
from config import *
import os
from stocks.strategies.momentum.momentum_ranker import MomentumRanker
def load_tickers_from_csv(csv_file, suffix=''):  # or '.NS'
    try:
        df = pd.read_csv(csv_file, header=None, names=["ticker"])
        tickers = df['ticker'].dropna().unique().tolist()
        tickers = [str(t).strip() + suffix for t in tickers]  # Add suffix for Yahoo Finance
        return tickers
    except Exception as e:
        print(f"Error loading tickers: {e}")
        return []

if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.abspath(__file__))    
    csv_path = os.path.join(base_dir, 'data', 'india_stocks.csv')
    
    backtest_date = "2025-05-21"  # <-- Set your date here (YYYY-MM-DD)

    roc = MomentumRanker()
    roc.run(
        tickers_csv_path=csv_path,
        output_csv_path="roc_summary.csv",
        email_to=EMAIL_RECEIVER,
        as_of_date=backtest_date  # <-- Pass it here
    )
