# === main.py ===
import argparse
import os
from strategies.value.ema_pullback import EMAPullbackAnalyzer
from strategies.value.etf_dip import ETFDipBuyer
from strategies.momentum.momentum_ranker import MomentumRanker
from strategies.value.value_strategy import ValueStockScreener
from config import get_config, EMAIL_RECEIVER
from utilities.file_utils import load_tickers_from_csv
from brokers.ibkr_supertrend_based_stoploss_order_for_portfolio import main as ibkr_supertrend_based_stoploss_order
from brokers.ibkr_momentum_orders import main as ibkr_momentum_orders
from database.us_stock_storage import USStockDataStorage

def run_ema_pullback(base_dir, region_config):
    print("Running EMA Pullback Screener...")
    csv_path = os.path.join(base_dir, 'data', region_config['ema_csv'])
    tickers = load_tickers_from_csv(csv_path, suffix=region_config['suffix'])
    analyzers = [EMAPullbackAnalyzer(ticker) for ticker in tickers]
    for analyzer in analyzers:
        analyzer.process()

def run_etf_dip(base_dir):
    print("Running ETF Dip Buyer Screener...")
    csv_path = os.path.join(base_dir, 'data', 'usa_etf.csv')
    tickers = load_tickers_from_csv(csv_path)
    analyzers = [ETFDipBuyer(ticker) for ticker in tickers]
    for analyzer in analyzers:
        analyzer.process()

def run_momentum_ranker(base_dir, region_config):
    print("Running Momentum Ranker Screener...")
    csv_path = os.path.join(base_dir, 'data', region_config['momentum_csv'])
    print(f"Using CSV path: {csv_path}")
    output_path = os.path.join(base_dir, region_config['momentum_output'])
    momentum_ranker = MomentumRanker(region_config=region_config)  # ✅ pass it here
    momentum_ranker.run(
        tickers_csv_path=csv_path,
        output_csv_path=output_path
    )


def run_value_stock_screener(base_dir, region_config):
    print("Running Value Stock Screener...")
    screener = ValueStockScreener()
    top_value_stocks = screener.run(
        tickers_csv_path=os.path.join(base_dir, 'data', region_config['momentum_csv']),
        output_csv_path=os.path.join(base_dir, 'data', region_config['value_output']),
        email_to=EMAIL_RECEIVER
    )

def create_supertrend_stoploss_order_for_portfolio():
    print("Creating stoploss order for portfolio...")
    ibkr_supertrend_based_stoploss_order()  # Call the IBKR stoploss order function

def update_database(base_dir, days=30, region_config=None):
    """Update the point-in-time database with latest US stock market data"""
    print("Updating US stock database...")
    csv_path = os.path.join(base_dir, 'data', region_config['momentum_csv'])
    tickers = load_tickers_from_csv(csv_path)
    
    # Initialize storage
    storage = USStockDataStorage()
    
    # Update database with ticker data
    success_count, fail_count = storage.batch_update_us_stocks(
        tickers, days_to_fetch=days, delay_seconds=0.5)
    
    print(f"Database update complete. Success: {success_count}, Failed: {fail_count}")
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run different stock screeners")
    parser.add_argument('--region', choices=['india', 'usa'], required=True, help="Region to run screener for")
    parser.add_argument('--ema', action='store_true', help="Run EMA Pullback Screener")
    parser.add_argument('--etf', action='store_true', help="Run ETF Dip Buyer Screener (USA only)")
    parser.add_argument('--momentum', action='store_true', help="Run Momentum Ranker Screener")
    parser.add_argument('--place_momentum_orders', action='store_true', help="Place momentum orders based on Momentum Ranker")
    parser.add_argument('--value', action='store_true', help="Run Value Stock Screener")
    parser.add_argument('--all', action='store_true', help="Run all screeners")
    parser.add_argument('--stoploss', action='store_true', help="Create stoploss order for portfolio")    
    parser.add_argument('--momentum_action', choices=['buy', 'sell', 'both'], help="Action to take for momentum orders")
    parser.add_argument('--update_db', action='store_true', help="Update the point-in-time database with latest market data")
    parser.add_argument('--days', type=int, default=30, help="Number of days of historical data to fetch for database update")

    args = parser.parse_args()
    base_dir = os.path.dirname(os.path.abspath(__file__))

    region_config = get_config(args.region)
    if not region_config:
        print(f"Invalid region specified: {args.region}")
        exit(1)

    any_run = False

    if args.all or args.ema:
        run_ema_pullback(base_dir, region_config)
        any_run = True
    if args.all or args.etf:
        if args.region != 'usa':
            print("ETF screener is only available for the USA region.")
        else:
            run_etf_dip(base_dir)
            any_run = True
    if args.all or args.momentum:
        run_momentum_ranker(base_dir, region_config)
        any_run = True
    if args.all or args.value:
        run_value_stock_screener(base_dir, region_config)
        any_run = True
    if args.place_momentum_orders:
        ibkr_momentum_orders(args.momentum_action, base_dir, region_config)

        any_run = True    
    if args.stoploss:
        create_supertrend_stoploss_order_for_portfolio()
        any_run = True
    if args.update_db:
        update_database(base_dir, days=args.days, region_config=region_config)
        any_run = True

    if not any_run:
        print("No screener specified. Use --help for options.")
