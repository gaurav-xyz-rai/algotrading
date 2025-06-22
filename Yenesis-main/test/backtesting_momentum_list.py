import os
import pandas as pd
from datetime import datetime
from strategies.momentum.momentum_ranker import MomentumRanker
from config import get_config, EMAIL_RECEIVER

# === Define your backtest dates ===
BACKTEST_DATES = [
    "2025-06-01",
    "2024-05-25",
    "2024-05-18",
    "2024-05-04",
    "2024-05-27",
    # Add more dates as needed
]

def run_backtest_for_dates(base_dir, region_config, backtest_dates):
    print("Running Momentum Ranker Backtest...")

    csv_path = os.path.join(base_dir, 'data', region_config['momentum_csv'])
    output_dir = os.path.join(base_dir, 'data', 'backtest_results')
    os.makedirs(output_dir, exist_ok=True)

    for date_str in backtest_dates:
        try:
            output_file = os.path.join(output_dir, f"momentum_ranking_{date_str}.csv")
            print(f"\nRunning for as_of_date = {date_str} ...")

            ranker = MomentumRanker(region_config=region_config)
            ranker.run(
                tickers_csv_path=csv_path,
                output_csv_path=output_file,
                email_to=None,  # Disable email during backtest
                as_of_date=date_str,
                run_trades=False  # Disable trading during backtest
            )

        except Exception as e:
            print(f"Error running backtest for {date_str}: {e}")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    region_config = get_config("US")  # Replace with your target region key

    run_backtest_for_dates(base_dir, region_config, BACKTEST_DATES)
