import pandas as pd
import yfinance as yf
import logging
import time

logger = logging.getLogger(__name__)

class StockDataFetcher:
    def __init__(self, ticker):
        self.ticker = ticker

    def fetch(self, retries=3, backoff_factor=1):
        attempt = 0
        while attempt < retries:
            try:
                df = yf.download(
                    self.ticker,
                    period="2y",
                    interval="1d",
                    progress=False,
                    auto_adjust=False,
                    threads=False,
                )

                if df.empty or "Close" not in df.columns:
                    logger.warning(f"[{self.ticker}] No valid data found.")
                    return pd.DataFrame()

                logger.info(f"[{self.ticker}] Yahoo Finance fetch successful.")
                df.index = pd.to_datetime(df.index)
                return df

            except Exception as e:
                attempt += 1
                wait_time = backoff_factor * (2 ** (attempt - 1))
                logger.warning(
                    f"[{self.ticker}] Attempt {attempt} failed: {e}. Retrying in {wait_time}s..."
                )
                time.sleep(wait_time)

        logger.error(f"[{self.ticker}] Failed to fetch data after {retries} attempts.")
        return pd.DataFrame()
