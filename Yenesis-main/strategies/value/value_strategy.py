import yfinance as yf
import pandas as pd
from datetime import datetime
from utilities.email_utils import send_email
from utilities.log_util import get_logger
from config import *  # for email credentials, etc.
import time

logger = get_logger()

def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

class ValueStockScreener:
    def __init__(self, tickers=None, use_hard_filter=False):
        """
        use_hard_filter: if True, apply relaxed filters,
                         if False, score all stocks without filtering
        """
        self.tickers = tickers or []
        self.results = []
        self.use_hard_filter = use_hard_filter

    def load_tickers_from_csv(self, filepath):
        df = pd.read_csv(filepath)
        if 'ticker' not in df.columns:
            raise ValueError("CSV must contain 'ticker' column")
        self.tickers = df['ticker'].dropna().unique().tolist()
        logger.info(f"Loaded {len(self.tickers)} tickers from {filepath}")

    def is_valid_stock(self, info):
        try:
            trailing_pe = safe_float(info.get('trailingPE'), 1000)
            forward_pe = safe_float(info.get('forwardPE'), 1000)
            pb_ratio = safe_float(info.get('priceToBook'), 1000)
            roe = safe_float(info.get('returnOnEquity'), 0)
            roa = safe_float(info.get('returnOnAssets'), 0)
            gross_margin = safe_float(info.get('grossMargins'), 0)
            profit_margin = safe_float(info.get('profitMargins'), 0)
            current_ratio = safe_float(info.get('currentRatio'), 0)
            debt_to_equity = safe_float(info.get('debtToEquity'), 10)
            earnings_growth = safe_float(info.get('earningsGrowth'), -1)
            revenue_growth = safe_float(info.get('revenueGrowth'), -1)
            fcf = safe_float(info.get('freeCashflow'), -1)
            dividend_yield = safe_float(info.get('dividendYield'), 0)
            insider_holding = safe_float(info.get('heldPercentInsiders'), 0)

            return (
                trailing_pe > 0 and trailing_pe < 30 and
                forward_pe < 30 and
                pb_ratio < 5 and
                roe > 0.1 and
                roa > 0.03 and
                gross_margin > 0.2 and
                profit_margin > 0.05 and
                current_ratio > 0.8 and
                debt_to_equity < 2 and
                earnings_growth > 0 and
                revenue_growth > 0 and
                fcf > 0 and
                insider_holding >= 0
            )
        except Exception as e:
            logger.warning(f"Error validating stock data: {e}")
            return False

    def compute_rankings(self):
        for ticker in self.tickers:
            try:
                time.sleep(0.7)
                stock = yf.Ticker(ticker)
                info = stock.info

                if info.get('returnOnEquity') is None:
                    logger.info(f"Skipping {ticker} due to missing ROE")
                    continue

                if self.use_hard_filter and not self.is_valid_stock(info):
                    logger.info(f"{ticker} filtered out by relaxed fundamental criteria")
                    continue

                self.results.append({
                    'Ticker': ticker,
                    'Name': info.get('shortName'),
                    'Description': info.get('longBusinessSummary'),
                    'P/E': safe_float(info.get('trailingPE')),
                    'Fwd P/E': safe_float(info.get('forwardPE')),
                    'P/B': safe_float(info.get('priceToBook')),
                    'ROE': safe_float(info.get('returnOnEquity')),
                    'ROA': safe_float(info.get('returnOnAssets')),
                    'Gross Margin': safe_float(info.get('grossMargins')),
                    'Profit Margin': safe_float(info.get('profitMargins')),
                    'Current Ratio': safe_float(info.get('currentRatio')),
                    'Debt/Equity': safe_float(info.get('debtToEquity')),
                    'EPS Growth': safe_float(info.get('earningsGrowth')),
                    'Revenue Growth': safe_float(info.get('revenueGrowth')),
                    'Free Cash Flow': safe_float(info.get('freeCashflow')),
                    'Dividend Yield': safe_float(info.get('dividendYield')),
                    'Insider Holding': safe_float(info.get('heldPercentInsiders'))
                })
                logger.info(f"Processed {ticker}")
            except Exception as e:
                logger.warning(f"Failed to process {ticker}: {e}")

        df = pd.DataFrame(self.results)
        if not df.empty:
            df['score'] = df.apply(self.score_stock, axis=1)
            df = df.sort_values(by='score', ascending=False).reset_index(drop=True)
        return df

    def score_stock(self, row):
        roe = row.get('ROE') or 0
        pe = row.get('P/E') or 1000
        pb = row.get('P/B') or 1000
        pm = row.get('Profit Margin') or 0
        de = row.get('Debt/Equity') or 10
        eps_growth = row.get('EPS Growth') or 0
        revenue_growth = row.get('Revenue Growth') or 0
        insider = row.get('Insider Holding') or 0

        score = (
            min(max((roe - 0.1) / 0.4, 0), 1) * 0.2 +
            min(max((30 - pe) / 30, 0), 1) * 0.15 +
            min(max((5 - pb) / 5, 0), 1) * 0.1 +
            min(max(pm / 0.3, 0), 1) * 0.1 +
            min(max((2 - de) / 2, 0), 1) * 0.1 +
            min(max(eps_growth / 0.3, 0), 1) * 0.15 +
            min(max(revenue_growth / 0.25, 0), 1) * 0.1 +
            min(max(insider / 0.15, 0), 1) * 0.1
        )
        return score

    def rank_top_picks(self, df, top_n=10):
        if df.empty:
            return df
        return df.head(top_n).reset_index(drop=True)

    def save_rankings_to_csv(self, df, output_path="value_summary.csv"):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(output_path, "w") as f:
            f.write(f"# Generated at {now}\n\n")
        df = df.round(3)
        df.to_csv(output_path, index=False, mode='a')
        logger.info(f"Saved top value picks to {output_path}")

    def run(self, tickers_csv_path=None, output_csv_path="value_summary.csv", email_to=None, top_n=10):
        if tickers_csv_path:
            self.load_tickers_from_csv(tickers_csv_path)

        df = self.compute_rankings()
        top_picks = self.rank_top_picks(df, top_n=top_n)
        self.save_rankings_to_csv(top_picks, output_csv_path)

        if email_to:
            subject = "Value Stock Screener Report - Top Picks"
            body = f"Top {top_n} value stock picks as of {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}."
            send_email(subject, body, to_email=email_to, from_email=EMAIL_SENDER, attachments=[output_csv_path])
            logger.info(f"Email sent to {email_to}")

        return top_picks
