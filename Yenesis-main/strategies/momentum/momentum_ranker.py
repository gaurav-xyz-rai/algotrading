# Import necessary libraries
import yfinance as yf
import pandas as pd
import numpy as np
import time
from datetime import datetime
import urllib.error
from utilities.email_utils import send_email
from utilities.log_util import get_logger
from config import *
from utilities.stock_data_fetch import StockDataFetcher
from config import EMAIL_RECEIVER
from utilities.data_utils import flatten_columns, extract_scalar
from utilities.math_utils import calculate_z_score, scale_score, calculate_roc
from utilities.file_utils import load_tickers_from_csv
from utilities.telegram_util import send_telegram_message
logger = get_logger()
# === CONFIGURATION ===
ROC_WINDOWS = [5, 21, 50, 100, 200]  # Time windows for Rate of Change (ROC) calculation
WEIGHTS = {5: 0.3, 21: 0.3, 50: 0.2, 100: 0.1, 200: 0.1}  # Weights for each ROC window
SLEEP_TIME = 0.7
# === MAIN CLASS ===
class MomentumRanker:
    def __init__(self, tickers=None, region_config=None):
        self.tickers = tickers or []
        self.region_config = region_config 
        self.benchmark_ticker = self.region_config["benchmark_ticker"]

    # Main logic: compute momentum scores and rank stocks
    def compute_rankings(self, as_of_date: str = None):
        rows = []
        invalid_tickers = []
        time.sleep(SLEEP_TIME)    

        # Download benchmark data
        benchmark = StockDataFetcher(self.benchmark_ticker).fetch()
        if benchmark.empty or "Close" not in benchmark.columns:
            logger.warning("Benchmark data unavailable.")
            return pd.DataFrame(), benchmark

        benchmark = flatten_columns(benchmark)

        if as_of_date:
            benchmark = benchmark[benchmark.index <= as_of_date]

        # 200 EMA market regime filter
        ema_200 = benchmark["Close"].ewm(span=200, adjust=False).mean()
        latest_close = benchmark["Close"].iloc[-1]
        latest_ema = ema_200.iloc[-1]
        latest_date = benchmark.index[-1].date()

        if latest_close < latest_ema:
            logger.warning("Benchmark is below 200 EMA — skipping momentum ranking due to weak market conditions.")
        
            # Send email about situation
            subject = f"Momentum Ranking Skipped — Weak Market Conditions ({self.benchmark_ticker})"
            body = (
                f"Momentum ranking was skipped on {latest_date} because the benchmark ({self.benchmark_ticker}) "
                f"is trading below its 200-day EMA.\n\n"
                f"Details:\n"
                f"Benchmark Ticker: {self.benchmark_ticker}\n"
                f"Latest Close Price: {latest_close:.2f}\n"
                f"200 EMA: {latest_ema:.2f}\n"
                f"Difference: {latest_close - latest_ema:.2f}\n\n"
                f"This indicates unfavorable market conditions for momentum strategies."
            )
            send_email(
                subject=subject,
                body=body,
                to_email=EMAIL_RECEIVER,
                from_email=EMAIL_SENDER,
                attachments=[]
            )
            return pd.DataFrame(), benchmark
        
        for ticker in self.tickers:
            try:
                time.sleep(SLEEP_TIME)
                # Market cap check
                stock_info = yf.Ticker(ticker).fast_info
                market_cap = stock_info.get("marketCap") or stock_info.get("market_cap")
                if not market_cap or market_cap < self.region_config["marketcap_threshold"]:
                    continue

                # Download stock data
                df = StockDataFetcher(ticker).fetch()

                df = flatten_columns(df)
                if as_of_date:
                   df = df[df.index <= as_of_date]

                if len(df) < max(ROC_WINDOWS) + 1:
                    logger.info(f"{ticker} skipped due to insufficient data.")
                    continue

                record = {"ticker": ticker, "market_cap": market_cap}

                z_scores = []
                valid = True

                # We'll collect date and prices info here
                price_info = {}

                for w in ROC_WINDOWS:
                    stock_roc = calculate_roc(df, w)
                    bench_roc = calculate_roc(benchmark, w)

                    if stock_roc.empty or bench_roc.empty:
                        valid = False
                        break

                    latest_stock = extract_scalar(stock_roc.iloc[-1])
                    latest_bench = extract_scalar(bench_roc.iloc[-1])

                    # Add benchmark ROC to record for comparison
                    record[f"bench_roc_{w}"] = latest_bench
                    record[f"stock_roc_{w}"] = latest_stock

                    # Condition checks:
                    # If benchmark ROC > 0, stock ROC >= 2 * benchmark ROC
                    # If benchmark ROC < 0, stock ROC must be positive (> 0)
                    if latest_bench is None or latest_stock is None:
                        valid = False
                        break

                    if latest_bench > 0:
                        if latest_stock < 2 * latest_bench:
                            valid = False
                            break
                    else:  # benchmark ROC <= 0
                        if latest_stock <= 0:
                            valid = False
                            break

                    # Historical relative ROC for z-score
                    hist_relative_roc = (stock_roc - bench_roc).dropna()[:-1]
                    relative_roc = latest_stock - latest_bench
                    z = calculate_z_score(relative_roc, hist_relative_roc)
                    record[f"z_{w}"] = z

                    if z is None:
                        valid = False
                        break

                    z_scores.append(WEIGHTS[w] * z)

                    # Capture dates and prices for cross-checking:
                    end_date = stock_roc.index[-1]
                    # Safely get start_date only if enough data exists
                    start_date = None
                    if len(stock_roc) > w:
                        start_date = stock_roc.index[-1 - w]
                    if start_date:
                        price_info[f"roc_{w}"] = {
                            "start_date": str(start_date.date()),
                            "end_date": str(end_date.date()),
                            "start_price": round(float(df.loc[start_date, "Close"]), 2),
                            "end_price": round(float(df.loc[end_date, "Close"]), 2),
                            "benchmark_start_price": round(float(benchmark.loc[start_date, "Close"]), 2),
                            "benchmark_end_price": round(float(benchmark.loc[end_date, "Close"]), 2),
                        }

                if valid and z_scores:
                    combined_z = sum(z_scores)
                    record["momentum_score"] = scale_score(combined_z)
                    record["price_info"] = price_info
                    rows.append(record)

            except urllib.error.HTTPError as e:
                logger.warning(f"{ticker} failed with HTTP Error {e.code}: {e.reason}")
                invalid_tickers.append(ticker)
            except Exception as e:
                logger.warning(f"Failed to process {ticker}: {e}")

        if invalid_tickers:
            pd.DataFrame({"invalid_ticker": invalid_tickers}).to_csv("invalid_tickers.csv", index=False)
            logger.info(f"Invalid tickers saved to invalid_tickers.csv")

        roc_df = pd.DataFrame(rows)
        if not roc_df.empty:
            roc_df = roc_df.sort_values(by="momentum_score", ascending=False).reset_index(drop=True)
        return roc_df, benchmark

    def send_top_20_to_telegram(self,roc_df):
        if roc_df.empty:
            text = "No momentum ranking data available to report."
            send_telegram_message(text)
            return

        # Take top 20 rows sorted by momentum_score
        top_20 = roc_df.head(20)

        # Prepare lines with format: Rank. Ticker - Price
        lines = []
        for idx, row in top_20.iterrows():
            ticker = row['ticker']
            # Last known price from 'price_info' for the shortest window (say 5-day) or fallback
            price = None
            if row.get("price_info") and row["price_info"].get("roc_5"):
                price = row["price_info"]["roc_5"].get("end_price")
            if price is None:
                price = "N/A"
            momentum_score = round(row.get("momentum_score", 0), 3)
            lines.append(f"{idx + 1}. {ticker} - ${price} (Score: {momentum_score})")

        message = "📊 *Top 20 Momentum Stocks*\n\n" + "\n".join(lines)

        # Send as Markdown for better formatting
        send_telegram_message(message)


    # Save results to CSV file
    def save_rankings_to_csv(self, roc_df, benchmark_df, output_path):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
        rows = []

        # === First row: Benchmark Summary ===
        benchmark_row = {
            "ticker": "BENCHMARK",
            "market_cap": "",
            "momentum_score": ""
        }
        for w in ROC_WINDOWS:
            roc = calculate_roc(benchmark_df, w)
            latest_roc = extract_scalar(roc.iloc[-1])
            # Safely get start_date only if enough data exists
            start_date = None
            if len(roc) > w:
                start_date = roc.index[-1 - w]
            if start_date:
                benchmark_row.update({
                    f"{w}_start_date": str(start_date.date()),
                    f"{w}_end_date": str(roc.index[-1].date()),
                    f"{w}_start_price": round(benchmark_df["Close"].iloc[-1 - w], 2),
                    f"{w}_end_price": round(benchmark_df["Close"].iloc[-1], 2),
                    f"{w}_roc": round(latest_roc, 4) if latest_roc is not None else None,
                    f"{w}_z": None
                })
        rows.append(benchmark_row)

        # === Per stock rows ===
        for _, row in roc_df.iterrows():
            r = {
                "ticker": row["ticker"],
                "market_cap": row["market_cap"],
                "momentum_score": round(row["momentum_score"], 2)
            }
            for w in ROC_WINDOWS:
                r.update({
                    f"{w}_start_date": row.get(f"price_info", {}).get(f"roc_{w}", {}).get("start_date"),
                    f"{w}_end_date": row.get(f"price_info", {}).get(f"roc_{w}", {}).get("end_date"),
                    f"{w}_start_price": row.get(f"price_info", {}).get(f"roc_{w}", {}).get("start_price"),
                    f"{w}_end_price": row.get(f"price_info", {}).get(f"roc_{w}", {}).get("end_price"),
                    f"{w}_roc": round(row.get(f"stock_roc_{w}"), 4) if row.get(f"stock_roc_{w}") is not None else None,
                    f"{w}_z": round(row.get(f"z_{w}"), 2) if row.get(f"z_{w}") is not None else None
                })
            rows.append(r)

        df_final = pd.DataFrame(rows)

        # === Save CSV ===
        with open(output_path, "w") as f:
            f.write(f"# Generated at {now}\n\n")
        df_final.to_csv(output_path, index=False, mode="a", float_format="%.3f")
        logger.info(f"CSV file saved: {output_path}")

    # Main runner: loads tickers, computes rankings, saves output, optionally emails it
    def run(self, 
            tickers_csv_path=None, 
            output_csv_path=None,
            as_of_date=None):
        if tickers_csv_path:
            self.tickers = load_tickers_from_csv(tickers_csv_path)

        roc_df, benchmark_df = self.compute_rankings(as_of_date=as_of_date)

        if roc_df.empty:
            logger.info("Momentum rankings not generated due to weak market or missing data.")
            return roc_df

        self.save_rankings_to_csv(roc_df, benchmark_df, output_csv_path)
        logger.info(f"Momentum rankings saved to {output_csv_path}")
        
        subject = "Momentum Ranking Report"
        body = f"Please find attached the momentum ranking report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}."
        send_email(subject=subject, body=body, to_email=EMAIL_RECEIVER, from_email=EMAIL_SENDER, attachments=[output_csv_path])
        logger.info(f"Report emailed to {EMAIL_RECEIVER}")
        self.send_top_20_to_telegram(roc_df)
        return roc_df
