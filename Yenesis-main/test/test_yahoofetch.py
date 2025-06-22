import logging
from utilities.stock_data_fetch import StockDataFetcher  # Assuming your class is saved in stock_data_fetch.py

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(name)s: %(message)s",
)

def test_fetch():
    ticker = "ACAD"  # Change this to any stock symbol you want to test
    fetcher = StockDataFetcher(ticker)
    df = fetcher.fetch()

    if df.empty:
        print(f"No data returned for {ticker}.")
    else:
        print(f"\n📈 {ticker} Data Sample:")
        print(df.head())  # Print first 5 rows

if __name__ == "__main__":
    test_fetch()
