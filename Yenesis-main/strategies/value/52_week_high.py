import yfinance as yf
import pandas as pd
from datetime import datetime
from utilities.email_utils import send_email
from utilities.log_util import get_logger
from config import *

logger = get_logger()

def flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure single-level column headers after downloading from yfinance"""
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

class High52WeekNotifier:
    def __init__(self, tickers=None):
        self.tickers = tickers or []

    def load_tickers_from_csv(self, filepath):
        """Load tickers from CSV with 'ticker' column"""
        df = pd.read_csv(filepath)
        if 'ticker' not in df.columns:
            raise ValueError("CSV must have a 'ticker' column")
        self.tickers = df['ticker'].dropna().unique().tolist()
        logger.info(f"Loaded {len(self.tickers)} tickers from {filepath}")

    def get_stocks_near_52_week_high(self, threshold=0.05):
        """Return stocks whose close price is within `threshold` of their 52-week high"""
        near_high = []
        for ticker in self.tickers:
            try:
                df = yf.download(ticker, period="2y", interval="1d", progress=False, auto_adjust=False)
                if df.empty:
                    continue

                df = flatten_columns(df)

                if {"Close", "High"}.issubset(df.columns):
                    current = df["Close"].iloc[-1]
                    high_52w = df["High"].max()
                    if high_52w and (high_52w - current) / high_52w <= threshold:
                        near_high.append({
                            "ticker": ticker,
                            "current_price": float(current),
                            "52w_high": float(high_52w)
                        })
            except Exception as e:
                logger.warning(f"{ticker}: 52‑week high check failed – {e}")

        return pd.DataFrame(near_high)

    def save_highs_to_csv(self, highs_df, output_path="52_week_highs_summary.csv"):
        """Save list of stocks near 52-week highs to CSV with timestamp"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(output_path, "w") as f:
            f.write(f"# 52-Week High Report generated at {now}\n\n")

        highs_df.to_csv(output_path, index=False, mode="a")

    def run(self, tickers_csv_path=None, output_csv_path="52_week_highs_summary.csv", email_to=None):
        """Run the detection and optionally send email"""
        if tickers_csv_path:
            self.load_tickers_from_csv(tickers_csv_path)

        highs_df = self.get_stocks_near_52_week_high()

        self.save_highs_to_csv(highs_df, output_csv_path)

        logger.info(f"52-week highs saved to {output_csv_path}")

        if email_to:
            subject = "Stocks Near 52-Week Highs"
            body = f"Please find attached the 52-week high stock report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}."
            send_email(subject=subject, body=body, to_email=email_to, from_email=EMAIL_SENDER, attachments=[output_csv_path])
            logger.info(f"Report emailed to {email_to}")

        return highs_df
