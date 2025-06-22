import pandas as pd
import os
from stocks.strategies.ema_pullback import EMAPullbackAnalyzer
from config import *
from datetime import datetime, timedelta

INITIAL_CAPITAL = 1000  # starting capital

# Adding a function to filter the data for the last 2 years
def filter_data_for_last_two_years(df):
    two_years_ago = datetime.now() - timedelta(days=365*2)
    df['Date'] = pd.to_datetime(df['Date'])  # Ensure the 'Date' column is in datetime format
    return df[df['Date'] >= two_years_ago]

class Trade:
    def __init__(self, ticker, entry_date, entry_price, position_size):
        self.ticker = ticker
        self.entry_date = entry_date
        self.entry_price = entry_price
        self.position_size = position_size  # money allocated
        self.entry_amount = position_size

    def __str__(self):
        return f"Trade({self.ticker}, {self.entry_date}, {self.entry_price}, {self.position_size})"

def load_tickers_from_csv(csv_file, suffix=''):
    try:
        df = pd.read_csv(csv_file, header=None, names=["ticker"])
        tickers = df['ticker'].dropna().unique().tolist()
        tickers = [str(t).strip() + suffix for t in tickers]
        return tickers
    except Exception as e:
        print(f"Error loading tickers: {e}")
        return []

def backtest(tickers):
    trades = []

    for ticker in tickers:
        analyzer = EMAPullbackAnalyzer(ticker)
        df = analyzer.fetch_data(force=True)

        if df.empty or len(df) < 200:
            print(f"Skipping {ticker}: Not enough data")
            continue

        # Filter data for the last two years
        df = filter_data_for_last_two_years(df)

        for i in range(200, len(df)):
            today = df.iloc[i]
            date = today.name

            analyzer.df = df.iloc[:i+1]
            signal = analyzer.evaluate_signal()

            # Log buy signals
            if signal:
                trade = Trade(
                    ticker=ticker,
                    entry_date=date,
                    entry_price=signal['entry'],
                    position_size=INITIAL_CAPITAL  # Allocating entire initial capital for simplicity
                )
                trades.append(trade)
                print(f"Buy Trigger: {trade}")

    return trades

if __name__ == '__main__':
    tickers = load_tickers_from_csv('data/nasdaq_tickers_test.csv')
    trades = backtest(tickers)

    trades_data = [{
        'Ticker': t.ticker,
        'Entry Date': t.entry_date,
        'Entry Price': t.entry_price,
        'Position Size ($)': round(t.position_size, 2),
    } for t in trades]

    df_trades = pd.DataFrame(trades_data)
    df_trades.to_csv('./buy_triggers.csv', index=False)

    print("Buy Triggers:")
    print(df_trades)