import pandas as pd
from datetime import datetime, timedelta
from strategies.etf_dip import ETFDipBuyer
import os
import pytz
import matplotlib.pyplot as plt

# Configurable backtest parameters
LOOKBACK_DAYS = 365 * 2  # Two years
BUY_SIGNAL = "BUY"
BACKTEST_OUTPUT_FILE = "buy_signals.csv"
CHECK_INTERVAL = 3600  # Time interval between checks (1 hour)

def plot_signals(df, buy_signals, ticker):
    """
    Plot the stock price and overlay buy signal points.
    """
    if df.empty:
        print("No data to plot.")
        return

    plt.figure(figsize=(14, 6))
    plt.plot(df.index, df['Close'], label='Close Price', linewidth=1.5)

    # Extract buy signal dates and prices
    signal_dates = [datetime.strptime(s['date_of_trigger'], '%Y-%m-%d %H:%M:%S') for s in buy_signals]
    signal_prices = [s['buy_price'] for s in buy_signals]

    # Plot buy signals
    if signal_dates and signal_prices:
        plt.scatter(signal_dates, signal_prices, color='red', marker='^', s=100, label='Buy Signal')

    plt.title(f"{ticker} Price with Buy Signals")
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    # Save to charts directory
    os.makedirs("charts", exist_ok=True)
    plt.savefig(f"charts/{ticker}_signals.png")
    plt.close()

def backtest_stock_analyzer(ticker, start_date, end_date):
    """
    Backtest the StockAnalyzer strategy on a given ticker between the start and end date.
    """
    # Initialize the StockAnalyzer with the given ticker
    analyzer = ETFDipBuyer(ticker)
    
    # Fetch historical data (force fetching to ensure up-to-date data)
    analyzer.fetch_data(force=True)  # Force fetch new data
    
    # Filter data based on start and end date
    df_filtered = analyzer.df[(analyzer.df.index >= start_date) & (analyzer.df.index <= end_date)]

    buy_signals = []

    # Iterate through the filtered data and track buy signals
    for current_index in range(50, len(df_filtered)):  # start after enough data for indicators
        analyzer.df = df_filtered.iloc[:current_index + 1].copy()  # up to current time
        signal_data = analyzer.evaluate_signal()
        
        if signal_data and signal_data['signal'] == BUY_SIGNAL:
            signal_date = df_filtered.index[current_index]
            #buy_price = df_filtered['Close'].iloc[current_index]
            buy_price = float(df_filtered['Close'].iloc[current_index])
            buy_signals.append({
                'date_of_trigger': signal_date.strftime('%Y-%m-%d %H:%M:%S'),
                'etf_name': ticker,
                'buy_price': buy_price
            })

    return buy_signals

def save_buy_signals_to_csv(buy_signals):
    """
    Save the buy signals to a CSV file in one-line-per-signal format.
    """
    if not buy_signals:
        return  # Nothing to save

    df = pd.DataFrame(buy_signals, columns=['date_of_trigger', 'etf_name', 'buy_price'])

    # Round buy_price to 2 decimal places
    df['buy_price'] = df['buy_price'].round(2)

    write_header = not os.path.exists(BACKTEST_OUTPUT_FILE)
    
    df.to_csv(BACKTEST_OUTPUT_FILE, index=False, mode='w', header=write_header)

def load_tickers_from_csv(csv_file, suffix=''):  # or '.NS'
    try:
        df = pd.read_csv(csv_file, header=None, names=["ticker"])
        tickers = df['ticker'].dropna().unique().tolist()
        tickers = [str(t).strip() + suffix for t in tickers]  # Add suffix for Yahoo Finance
        return tickers
    except Exception as e:
        print(f"Error loading tickers: {e}")
        return []

def run_backtest():
    tickers = load_tickers_from_csv('data/usa_etf.csv')
    
    # Make start_date and end_date timezone-aware
    start_date = (datetime.now() - timedelta(days=LOOKBACK_DAYS)).astimezone(pytz.UTC)
    end_date = datetime.now().astimezone(pytz.UTC)

    all_buy_signals = []

    for ticker in tickers:
        print(f"Backtesting {ticker}...")
        buy_signals = backtest_stock_analyzer(ticker, start_date, end_date)
        all_buy_signals.extend(buy_signals)

        # Plotting
        analyzer = ETFDipBuyer(ticker)
        analyzer.fetch_data(force=False)  # Use cached or existing data
        df = analyzer.df[(analyzer.df.index >= start_date) & (analyzer.df.index <= end_date)]
        plot_signals(df, buy_signals, ticker)

    save_buy_signals_to_csv(all_buy_signals)
    print(f"Backtest completed. Signals saved to {BACKTEST_OUTPUT_FILE}")

if __name__ == '__main__':
    run_backtest()
