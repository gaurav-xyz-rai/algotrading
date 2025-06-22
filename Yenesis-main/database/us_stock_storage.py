import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import time
from database.db_connection import DatabaseConnection
from utilities.log_util import get_logger
from utilities.stock_data_fetch import StockDataFetcher
from utilities.data_utils import flatten_columns

logger = get_logger()

class USStockDataStorage:
    """
    A class to fetch and store US stock market data in a MySQL database.
    Creates a point-in-time database for historical analysis and backtesting.
    """
    
    def __init__(self, db_config=None):
        """Initialize with database configuration"""
        self.db = DatabaseConnection(**(db_config or {}))
        self.ensure_tables_exist()
    
    def ensure_tables_exist(self):
        """Ensure required database tables exist"""
        # Create database if it doesn't exist
        self.db.create_schema_if_not_exists()
        
        # Connect to the database
        if not self.db.connect():
            logger.error("Failed to connect to database")
            return False
        
        # Create tickers table
        create_tickers_table = """
        CREATE TABLE IF NOT EXISTS tickers (
            id INT AUTO_INCREMENT PRIMARY KEY,
            symbol VARCHAR(20) NOT NULL UNIQUE,
            name VARCHAR(255),
            sector VARCHAR(100),
            industry VARCHAR(100),
            market_cap BIGINT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB;
        """
        
        # Create stock prices table
        create_prices_table = """
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
        """
        
        # Create technical indicators table
        create_indicators_table = """
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
        """
        
        # Execute create table statements
        self.db.execute_query(create_tickers_table)
        self.db.execute_query(create_prices_table)
        self.db.execute_query(create_indicators_table)
        
        logger.info("Database tables created or already exist")
        return True
    
    def update_ticker_info(self, symbol, ticker_info=None):
        """Update or insert ticker information"""
        if ticker_info is None:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                
                # Extract relevant info
                name = info.get('shortName', info.get('longName', symbol))
                sector = info.get('sector', '')
                industry = info.get('industry', '')
                market_cap = info.get('marketCap', 0)
                
                ticker_info = {
                    'name': name,
                    'sector': sector,
                    'industry': industry,
                    'market_cap': market_cap
                }
            except Exception as e:
                logger.error(f"Error fetching ticker info for {symbol}: {e}")
                ticker_info = {'name': symbol, 'sector': '', 'industry': '', 'market_cap': 0}
        
        # Check if ticker exists
        check_query = "SELECT id FROM tickers WHERE symbol = %s"
        result = self.db.execute_query(check_query, (symbol,), fetch=True)
        
        if result:
            # Update existing ticker
            ticker_id = result[0]['id']
            update_query = """
            UPDATE tickers 
            SET name = %s, sector = %s, industry = %s, market_cap = %s, last_updated = NOW()
            WHERE id = %s
            """
            params = (ticker_info['name'], ticker_info['sector'], ticker_info['industry'], 
                     ticker_info['market_cap'], ticker_id)
            self.db.execute_query(update_query, params)
        else:
            # Insert new ticker
            insert_query = """
            INSERT INTO tickers (symbol, name, sector, industry, market_cap)
            VALUES (%s, %s, %s, %s, %s)
            """
            params = (symbol, ticker_info['name'], ticker_info['sector'], 
                     ticker_info['industry'], ticker_info['market_cap'])
            self.db.execute_query(insert_query, params)
            
            # Get the newly inserted ticker ID
            result = self.db.execute_query(check_query, (symbol,), fetch=True)
            ticker_id = result[0]['id'] if result else None
        
        return ticker_id
    
    def store_price_data(self, ticker_id, symbol, df):
        """Store historical price data for a ticker"""
        if df.empty:
            logger.warning(f"No price data to store for {symbol}")
            return 0
        
        # Reset index to get date as column
        df_to_store = df.reset_index()
        
        # Prepare SQL for bulk insert
        placeholders = ", ".join(["%s"] * 10)  # For all fields except id
        insert_query = f"""
        INSERT INTO stock_prices 
        (ticker_id, date, open, high, low, close, adjusted_close, volume, dividend, stock_split)
        VALUES ({placeholders})
        ON DUPLICATE KEY UPDATE
        open = VALUES(open),
        high = VALUES(high),
        low = VALUES(low),
        close = VALUES(close),
        adjusted_close = VALUES(adjusted_close),
        volume = VALUES(volume),
        dividend = VALUES(dividend),
        stock_split = VALUES(stock_split),
        captured_at = NOW()
        """
        
        # Prepare data
        params = []
        for _, row in df_to_store.iterrows():
            # Extract date as YYYY-MM-DD
            date_str = row['Date'].strftime('%Y-%m-%d')
            
            row_data = (
                ticker_id,
                date_str,
                float(row.get('Open', 0)),
                float(row.get('High', 0)),
                float(row.get('Low', 0)),
                float(row.get('Close', 0)),
                float(row.get('Adj Close', row.get('Close', 0))),
                int(row.get('Volume', 0)),
                float(row.get('Dividends', 0)),
                float(row.get('Stock Splits', 0))
            )
            params.append(row_data)
        
        # Execute in batches to avoid too large queries
        batch_size = 100
        rows_affected = 0
        
        for i in range(0, len(params), batch_size):
            batch = params[i:i + batch_size]
            result = self.db.execute_query(insert_query, batch, multi=True)
            if result:
                rows_affected += len(batch)
        
        logger.info(f"Stored {rows_affected} price records for {symbol}")
        return rows_affected
    
    def store_technical_indicators(self, ticker_id, symbol, df):
        """Store technical indicators for a ticker"""
        if df.empty:
            logger.warning(f"No technical indicator data to store for {symbol}")
            return 0
            
        # Reset index to get date as column
        df_to_store = df.reset_index()
        
        # Prepare SQL for bulk insert
        placeholders = ", ".join(["%s"] * 11)  # For all fields except id
        insert_query = f"""
        INSERT INTO technical_indicators 
        (ticker_id, date, sma_20, ema_50, ema_200, rsi_14, macd, macd_signal, bb_upper, bb_lower, atr)
        VALUES ({placeholders})
        ON DUPLICATE KEY UPDATE
        sma_20 = VALUES(sma_20),
        ema_50 = VALUES(ema_50),
        ema_200 = VALUES(ema_200),
        rsi_14 = VALUES(rsi_14),
        macd = VALUES(macd),
        macd_signal = VALUES(macd_signal),
        bb_upper = VALUES(bb_upper),
        bb_lower = VALUES(bb_lower),
        atr = VALUES(atr),
        captured_at = NOW()
        """
        
        # Prepare data
        params = []
        for _, row in df_to_store.iterrows():
            # Skip rows without sufficient indicators
            if pd.isna(row.get('SMA20', None)) and pd.isna(row.get('EMA50', None)):
                continue
                
            # Extract date as YYYY-MM-DD
            date_str = row['Date'].strftime('%Y-%m-%d')
            
            row_data = (
                ticker_id,
                date_str,
                float(row.get('SMA20', None) or 0),
                float(row.get('EMA50', None) or 0),
                float(row.get('EMA200', None) or 0),
                float(row.get('RSI', None) or 0),
                float(row.get('MACD', None) or 0),
                float(row.get('MACD_Signal', None) or 0),
                float(row.get('BB_High', None) or 0),
                float(row.get('BB_Low', None) or 0),
                float(row.get('ATR', None) or 0)
            )
            params.append(row_data)
        
        # Execute in batches to avoid too large queries
        batch_size = 100
        rows_affected = 0
        
        for i in range(0, len(params), batch_size):
            batch = params[i:i + batch_size]
            result = self.db.execute_query(insert_query, batch, multi=True)
            if result:
                rows_affected += len(batch)
        
        logger.info(f"Stored {rows_affected} indicator records for {symbol}")
        return rows_affected
    
    def fetch_and_store_ticker_data(self, symbol, start_date=None, end_date=None, calculate_indicators=True):
        """Fetch and store data for a single ticker"""
        # Default dates if not provided
        end_date = end_date or datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            # Default to fetching the last 2 years
            start_date = (datetime.now() - timedelta(days=2*365)).strftime('%Y-%m-%d')
            
        logger.info(f"Fetching data for {symbol} from {start_date} to {end_date}")
        
        try:
            # Update ticker information
            ticker_id = self.update_ticker_info(symbol)
            if not ticker_id:
                logger.error(f"Failed to get ticker ID for {symbol}")
                return False
                
            # Fetch historical data
            data_fetcher = StockDataFetcher(symbol, start=start_date, end=end_date)
            df = data_fetcher.fetch()
            
            if df.empty:
                logger.warning(f"No data retrieved for {symbol}")
                return False
                
            # Process data for storage
            df = flatten_columns(df)
            
            # Store price data
            self.store_price_data(ticker_id, symbol, df)
            
            # Calculate and store technical indicators if requested
            if calculate_indicators:
                from strategies.value.etf_dip import ETFDipBuyer
                analyzer = ETFDipBuyer(symbol)
                indicator_df = analyzer.fetch_data(force=True)
                if not indicator_df.empty:
                    self.store_technical_indicators(ticker_id, symbol, indicator_df)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing ticker {symbol}: {e}")
            return False
    
    def batch_update_us_stocks(self, ticker_list, days_to_fetch=30, delay_seconds=0.5):
        """Update data for multiple US stocks with a delay between requests"""
        start_date = (datetime.now() - timedelta(days=days_to_fetch)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        success_count = 0
        fail_count = 0
        
        for symbol in ticker_list:
            try:
                success = self.fetch_and_store_ticker_data(symbol, start_date, end_date)
                if success:
                    success_count += 1
                else:
                    fail_count += 1
                    
                # Add delay to avoid throttling
                if delay_seconds > 0:
                    time.sleep(delay_seconds)
                    
            except Exception as e:
                logger.error(f"Error updating data for {symbol}: {e}")
                fail_count += 1
                
        logger.info(f"Batch update complete. Success: {success_count}, Failed: {fail_count}")
        return success_count, fail_count
