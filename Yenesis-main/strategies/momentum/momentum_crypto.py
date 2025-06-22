import pandas as pd
import yfinance as yf
import os

def percent_change(current, previous):
    try:
        if previous == 0:
            return float('nan')
        return (current - previous) / previous
    except Exception as e:
        print(f"❌ Error in percent_change: {e}")
        return float('nan')

def fetch_momentum(symbol):
    try:
        print(f"\n📥 Fetching data for {symbol}")
        df = yf.download(symbol, period="90d", interval="1d", progress=False)
        if df.empty or len(df) < 31:
            print(f"⚠️ Not enough data for {symbol}")
            return None

        # Select the close price series for this symbol
        close = df['Close'][symbol]

        pct_change_1d = percent_change(close.values[-1], close.values[-2])
        pct_change_7d = percent_change(close.values[-1], close.values[-8])
        pct_change_30d = percent_change(close.values[-1], close.values[-31])
        pct_change_90d = percent_change(close.values[-1], close.values[0])

        print(f"✅ {symbol}: 1D={float(pct_change_1d):.2%}, 7D={float(pct_change_7d):.2%}, 30D={float(pct_change_30d):.2%}, 90D={float(pct_change_90d):.2%}")
        return {
            'symbol': symbol,
            '1d': pct_change_1d,
            '7d': pct_change_7d,
            '30d': pct_change_30d,
            '90d': pct_change_90d
        }

    except Exception as e:
        print(f"❌ Failed to fetch data for {symbol}: {e}")
        return None


def main():
    print("🚀 Starting crypto momentum strategy...")

    csv_path = os.path.join("..", "data", "crypto.csv")
    print(f"🔄 Loading symbols from: {csv_path}")

    df = pd.read_csv(csv_path)
    if 'SYMBOL' not in df.columns:
        print("❌ SYMBOL column not found in CSV")
        return

    symbols = df['SYMBOL'].dropna().unique()
    print(f"✅ Found {len(symbols)} unique symbols")

    results = []
    for sym in symbols:
        ticker = f"{sym}-USD"
        data = fetch_momentum(ticker)
        if data:
            results.append(data)

    print(f"\n📊 Successfully processed {len(results)} coins with valid data")
    if results:
        print("\n🔥 Top performers (90D momentum):")
        sorted_results = sorted(results, key=lambda x: x['90d'], reverse=True)
        for r in sorted_results[:10]:
            print(f"{r['symbol']}: 90D Change = {r['90d']:.2%}")
    else:
        print("❌ No valid data found for any symbols")

if __name__ == "__main__":
    main()
