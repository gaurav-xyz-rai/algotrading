import argparse
from database.db_connection import DatabaseConnection
from utilities.log_util import get_logger

logger = get_logger()

class DatabaseManager:
    """
    Class for managing the point-in-time database operations
    """
    def __init__(self):
        self.db = DatabaseConnection()
    
    def initialize_database(self):
        """Initialize the database structure"""
        # Create database schema if not exists
        if not self.db.create_schema_if_not_exists():
            logger.error("Failed to create database schema")
            return False
            
        # Connect to the database
        if not self.db.connect():
            logger.error("Failed to connect to database")
            return False
            
        # Create tables
        tables = [
            # Tickers table
            """
            CREATE TABLE IF NOT EXISTS tickers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                symbol VARCHAR(20) NOT NULL UNIQUE,
                name VARCHAR(255),
                sector VARCHAR(100),
                industry VARCHAR(100),
                market_cap BIGINT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB;
            """,
            # Stock prices table
            """
            CREATE TABLE IF NOT EXISTS stock_prices (
                id INT AUTO_INCREMENT PRIMARY KEY,
                ticker_id INT NOT NULL,
                date DATE NOT NULL,
                open DECIMAL(15, 5),
                high DECIMAL(15, 5),
                low DECIMAL(15, 5),
                close DECIMAL(15, 5),
                adjusted_close DECIMAL(15, 5),
                volume BIGINT,
                dividend DECIMAL(10, 5),
                stock_split DECIMAL(10, 5),
                captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY ticker_date (ticker_id, date),
                FOREIGN KEY (ticker_id) REFERENCES tickers(id)
            ) ENGINE=InnoDB;
            """,
            # Technical indicators table
            """
            CREATE TABLE IF NOT EXISTS technical_indicators (
                id INT AUTO_INCREMENT PRIMARY KEY,
                ticker_id INT NOT NULL,
                date DATE NOT NULL,
                sma_20 DECIMAL(15, 5),
                ema_50 DECIMAL(15, 5),
                ema_200 DECIMAL(15, 5),
                rsi_14 DECIMAL(10, 5),
                macd DECIMAL(10, 5),
                macd_signal DECIMAL(10, 5),
                bb_upper DECIMAL(15, 5),
                bb_lower DECIMAL(15, 5),
                atr DECIMAL(10, 5),
                captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY ticker_date (ticker_id, date),
                FOREIGN KEY (ticker_id) REFERENCES tickers(id)
            ) ENGINE=InnoDB;
            """,
            # Indices for better query performance
            """
            CREATE INDEX IF NOT EXISTS idx_ticker_id_date ON stock_prices (ticker_id, date);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_ticker_id_date_indicators ON technical_indicators (ticker_id, date);
            """
        ]
        
        for table_sql in tables:
            if not self.db.execute_query(table_sql):
                logger.error(f"Failed to create table with SQL: {table_sql[:50]}...")
                return False
                
        logger.info("Database initialized successfully")
        return True
    
    def get_database_stats(self):
        """Get statistics about the database"""
        stats = {}
        
        # Check connection
        if not self.db.connect():
            logger.error("Failed to connect to database")
            return {"error": "Failed to connect to database"}
            
        # Get ticker count
        ticker_count = self.db.execute_query("SELECT COUNT(*) as count FROM tickers", fetch=True)
        stats['ticker_count'] = ticker_count[0]['count'] if ticker_count else 0
        
        # Get price record count
        price_count = self.db.execute_query("SELECT COUNT(*) as count FROM stock_prices", fetch=True)
        stats['price_record_count'] = price_count[0]['count'] if price_count else 0
        
        # Get indicator record count
        indicator_count = self.db.execute_query("SELECT COUNT(*) as count FROM technical_indicators", fetch=True)
        stats['indicator_record_count'] = indicator_count[0]['count'] if indicator_count else 0
        
        # Get date range
        date_range = self.db.execute_query(
            "SELECT MIN(date) as min_date, MAX(date) as max_date FROM stock_prices", fetch=True)
        if date_range:
            stats['min_date'] = date_range[0]['min_date']
            stats['max_date'] = date_range[0]['max_date']
        
        # Get top stocks by market cap
        top_stocks = self.db.execute_query(
            "SELECT symbol, name, market_cap FROM tickers ORDER BY market_cap DESC LIMIT 10", fetch=True)
        stats['top_stocks'] = top_stocks if top_stocks else []
        
        return stats
    
    def clean_up_old_data(self, days_to_keep=365):
        """Clean up old data from the database"""
        if not self.db.connect():
            logger.error("Failed to connect to database")
            return False
            
        # Delete old stock prices
        delete_prices = f"""
        DELETE FROM stock_prices 
        WHERE date < DATE_SUB(CURDATE(), INTERVAL {days_to_keep} DAY)
        """
        
        # Delete old indicators
        delete_indicators = f"""
        DELETE FROM technical_indicators 
        WHERE date < DATE_SUB(CURDATE(), INTERVAL {days_to_keep} DAY)
        """
        
        prices_deleted = self.db.execute_query(delete_prices)
        indicators_deleted = self.db.execute_query(delete_indicators)
        
        logger.info(f"Cleaned up data older than {days_to_keep} days")
        logger.info(f"Prices deleted: {prices_deleted}, Indicators deleted: {indicators_deleted}")
        
        return True

def main():
    """Main function for database management"""
    parser = argparse.ArgumentParser(description="Manage the point-in-time database")
    parser.add_argument("--init", action="store_true", help="Initialize the database structure")
    parser.add_argument("--stats", action="store_true", help="Get database statistics")
    parser.add_argument("--clean", action="store_true", help="Clean up old data")
    parser.add_argument("--days", type=int, default=365, help="Days of data to keep when cleaning")
    
    args = parser.parse_args()
    
    db_manager = DatabaseManager()
    
    if args.init:
        if db_manager.initialize_database():
            print("Database initialized successfully")
        else:
            print("Failed to initialize database")
    
    if args.stats:
        stats = db_manager.get_database_stats()
        print("\n=== Database Statistics ===")
        print(f"Tickers: {stats['ticker_count']}")
        print(f"Price Records: {stats['price_record_count']}")
        print(f"Indicator Records: {stats['indicator_record_count']}")
        
        if 'min_date' in stats:
            print(f"Date Range: {stats['min_date']} to {stats['max_date']}")
        
        print("\nTop Stocks by Market Cap:")
        for i, stock in enumerate(stats.get('top_stocks', []), 1):
            market_cap_billions = stock['market_cap'] / 1_000_000_000
            print(f"{i}. {stock['symbol']} ({stock['name']}): ${market_cap_billions:.2f}B")
    
    if args.clean:
        if db_manager.clean_up_old_data(args.days):
            print(f"Successfully cleaned up data older than {args.days} days")
        else:
            print("Failed to clean up old data")

if __name__ == "__main__":
    main()
