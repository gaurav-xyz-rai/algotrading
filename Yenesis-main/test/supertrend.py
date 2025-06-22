import yfinance as yf
import pandas as pd
import pandas_ta as ta


def calculate_supertrend(ticker):
    df = yf.download(ticker, period="90d", interval="1d", auto_adjust=True)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)  # Use level 0: Price
        df.columns.name = None
    else:
        df.columns.name = None

    df = df[['High', 'Low', 'Close']].dropna()

    st = ta.supertrend(high=df['High'], low=df['Low'], close=df['Close'], length=10, multiplier=3.0)
    #print(st.head())
    if st is None or st.empty:
        print(f"❌ Supertrend calculation failed for {ticker}")
        return

    df = df.join(st)

    trend_col = next((col for col in df.columns if "SUPERTd" in col), None)
    price_col = next((col for col in df.columns if "SUPERT_" in col and "SUPERTd" not in col), None)

    #print(df)
    if not trend_col or not price_col:
        print(f"❌ Could not find expected Supertrend columns for {ticker}")
        return

    last = df.iloc[-1]
    trend = "Bullish" if last[trend_col] == 1 else "Bearish"
    close_price = last['Close']
    supertrend_value = last[price_col]

    stop_loss = supertrend_value * (1 - 0.01) if trend == "Bullish" else supertrend_value * (1 + 0.01)

    #print(f"📈 {ticker} Supertrend Analysis")
    #print(f"Trend       : {trend}")
    #print(f"Close Price : {close_price:.2f}")
    #print(f"Supertrend  : {supertrend_value:.2f}")
    #print(f"Stop Loss   : {stop_loss:.2f}")
    return stop_loss

if __name__ == "__main__":
    print(calculate_supertrend("AAPL"))
