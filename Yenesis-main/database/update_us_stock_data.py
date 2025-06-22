import os
import argparse
from datetime import datetime, timedelta
import pandas as pd
from database.us_stock_storage import USStockDataStorage
from utilities.file_utils import load_tickers_from_csv
from utilities.email_utils import send_email
from utilities.log_util import get_logger
from config import EMAIL_RECEIVER, EMAIL_SENDER

# Try to import from resources first
try:
    from resources.db_config import DATABASE_CONFIG, get_db_config
except ImportError:
    # Fall back to config if not found
    from config import DATABASE_CONFIG, get_db_config

logger = get_logger()

def main():
    """
    Main function to update US stock market data in MySQL database.
    """
    parser = argparse.ArgumentParser(description="Store US stock market data in MySQL database")
    parser.add_argument("--days", type=int, default=30, 
                        help="Number of days of historical data to fetch")
    parser.add_argument("--delay", type=float, default=0.5, 
                        help="Delay between API requests in seconds")
    parser.add_argument("--file", type=str, default="usa_stock_post_mcap_filter.csv", 
                        help="CSV file containing stock symbols")
    parser.add_argument("--notify", action="store_true", 
                        help="Send email notification when complete")
    parser.add_argument("--db-host", type=str, 
                        help="Database host (overrides config)")
    parser.add_argument("--db-user", type=str, 
                        help="Database user (overrides config)")
    parser.add_argument("--db-password", type=str, 
                        help="Database password (overrides config)")
    parser.add_argument("--db-name", type=str, 
                        help="Database name (overrides config)")
    args = parser.parse_args()
    
    # Get base directory
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Load tickers
    csv_path = os.path.join(base_dir, 'data', args.file)
    logger.info(f"Loading tickers from: {csv_path}")
    
    try:
        tickers = load_tickers_from_csv(csv_path)
        logger.info(f"Loaded {len(tickers)} tickers from {args.file}")
        
        # Create custom db config from args and config file
        db_config = {}
        if args.db_host:
            db_config['host'] = args.db_host
        if args.db_user:
            db_config['user'] = args.db_user
        if args.db_password:
            db_config['password'] = args.db_password
        if args.db_name:
            db_config['database'] = args.db_name
            
        # Initialize database storage
        storage = USStockDataStorage(db_config)
        
        # Start time
        start_time = datetime.now()
        
        # Process tickers
        success_count, fail_count = storage.batch_update_us_stocks(
            tickers, days_to_fetch=args.days, delay_seconds=args.delay)
            
        # End time
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Log results
        message = (
            f"Database update completed in {duration.total_seconds()/60:.2f} minutes.\n"
            f"Successfully updated: {success_count} tickers\n"
            f"Failed to update: {fail_count} tickers\n"
            f"Total processed: {success_count + fail_count} tickers\n"
        )
        logger.info(message)
        
        # Send email notification if requested
        if args.notify:
            subject = f"US Stock Database Update - {datetime.now().strftime('%Y-%m-%d')}"
            send_email(subject=subject, body=message, to_email=EMAIL_RECEIVER, from_email=EMAIL_SENDER)
            
    except Exception as e:
        logger.error(f"Error in database update process: {e}")
        if args.notify:
            subject = f"ERROR: US Stock Database Update - {datetime.now().strftime('%Y-%m-%d')}"
            send_email(
                subject=subject, 
                body=f"An error occurred during database update: {str(e)}",
                to_email=EMAIL_RECEIVER, 
                from_email=EMAIL_SENDER
            )

if __name__ == "__main__":
    main()
