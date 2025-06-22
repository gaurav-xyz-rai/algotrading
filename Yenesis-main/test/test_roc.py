import yfinance as yf
import pandas as pd

# Helper to safely extract scalar values
def extract_scalar(val):
    if isinstance(val, pd.Series):
        if len(val) == 1:
            return val.iloc[0]
        else:
            return None
    return float(val) if pd.notna(val) else None

# Ticker and windows
ticker = "^NSEI"
roc_windows = [5, 21, 50, 100, 200]

# Fetch historical data
df = yf.download(ticker, period="2y", interval="1d", auto_adjust=False)

# Flatten multi-index if needed
if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)

# Ensure 'Close' exists
if "Close" not in df.columns or df['Close'].isnull().all():
    print("No valid close data for", ticker)
else:
    print(f"\nRate of Change (ROC) verification for {ticker}:\n")

    df = df.dropna(subset=["Close"])  # Clean NaNs

    for window in roc_windows:
        if len(df) <= window:
            print(f"Not enough data for window {window}")
            continue

        # Get latest date
        current_date = df.index[-1]
        prev_date = df.index[-(window + 1)]

        current_price = df["Close"].iloc[-1]
        past_price = df["Close"].iloc[-(window + 1)]

        # Manual ROC calculation
        roc_value = (current_price - past_price) / past_price

        print(f"Window: {window} days")
        print(f"  Date T: {current_date.date()} | Close = {current_price:.2f}")
        print(f"  Date T-{window}: {prev_date.date()} | Close = {past_price:.2f}")
        print(f"  ROC({window}): {roc_value:.4f}\n")
