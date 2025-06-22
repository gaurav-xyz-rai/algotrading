import pandas as pd
import os
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from database.db_connection import DatabaseConnection

class BacktestFromDatabase:
    """
    Class for backtesting strategies using the point-in-time database.
    """
    def __init__(self):
        self.db = DatabaseConnection()
        self.db.connect()
        
    def fetch_ticker_id(self, symbol):
        """Get the ticker ID for a symbol"""
        query = "SELECT id FROM tickers WHERE symbol = %s"
        result = self.db.execute_query(query, (symbol,), fetch=True)
        if result:
            return result[0]['id']
        return None
        
    def get_ticker_data(self, symbol, start_date=None, end_date=None):
        """
        Fetch ticker data from the database with prices and indicators
        """
        ticker_id = self.fetch_ticker_id(symbol)
        if not ticker_id:
            print(f"Ticker {symbol} not found in database")
            return None
            
        # Default dates if not provided
        end_date = end_date or datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            # Default to 1 year of data
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            
        # Query to join price and indicator data
        query = """
        SELECT 
            p.date, p.open, p.high, p.low, p.close, p.adjusted_close, p.volume,
            i.sma_20, i.ema_50, i.ema_200, i.rsi_14, i.macd, i.macd_signal, 
            i.bb_upper, i.bb_lower, i.atr
        FROM 
            stock_prices p
        LEFT JOIN 
            technical_indicators i ON p.ticker_id = i.ticker_id AND p.date = i.date
        WHERE 
            p.ticker_id = %s 
            AND p.date BETWEEN %s AND %s
        ORDER BY 
            p.date ASC
        """
        
        result = self.db.execute_query(query, (ticker_id, start_date, end_date), fetch=True)
        if result:
            # Convert to dataframe
            df = pd.DataFrame(result)
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            return df
        return pd.DataFrame()
    
    def backtest_simple_strategy(self, symbol, start_date=None, end_date=None):
        """
        Backtest a simple crossover strategy using the database
        """
        # Get ticker data
        data = self.get_ticker_data(symbol, start_date, end_date)
        if data is None or data.empty:
            return None
            
        # Create signals based on a simple strategy (EMA crossover)
        data['signal'] = 0
        data['position'] = 0
        
        # Create signals: 1 when sma20 crosses above ema50, -1 when it crosses below
        data.loc[data['sma_20'] > data['ema_50'], 'signal'] = 1
        data.loc[data['sma_20'] < data['ema_50'], 'signal'] = -1
        
        # Generate positions
        data['position'] = data['signal'].diff()
        
        # Calculate returns
        data['returns'] = data['close'].pct_change()
        data['strategy_returns'] = data['position'].shift(1) * data['returns']
        
        # Calculate cumulative returns
        data['cumulative_returns'] = (1 + data['returns']).cumprod()
        data['strategy_cumulative_returns'] = (1 + data['strategy_returns']).cumprod()
        
        return data
    
    def plot_backtest(self, data, symbol):
        """
        Plot backtest results
        """
        plt.figure(figsize=(12, 8))
        
        # Plot equity curves
        plt.subplot(2, 1, 1)
        plt.plot(data.index, data['cumulative_returns'], label='Buy and Hold')
        plt.plot(data.index, data['strategy_cumulative_returns'], label='Strategy')
        plt.title(f'Backtest Results for {symbol}')
        plt.ylabel('Cumulative Returns')
        plt.legend()
        plt.grid(True)
        
        # Plot buy/sell signals
        plt.subplot(2, 1, 2)
        plt.plot(data.index, data['close'], label='Close Price')
        plt.plot(data.index, data['sma_20'], label='SMA20')
        plt.plot(data.index, data['ema_50'], label='EMA50')
        
        # Mark buy signals
        buy_signals = data[data['position'] > 0].index
        sell_signals = data[data['position'] < 0].index
        
        plt.scatter(buy_signals, data.loc[buy_signals, 'close'], marker='^', color='g', label='Buy Signal')
        plt.scatter(sell_signals, data.loc[sell_signals, 'close'], marker='v', color='r', label='Sell Signal')
        
        plt.ylabel('Price')
        plt.xlabel('Date')
        plt.legend()
        plt.grid(True)
        
        plt.tight_layout()
        plt.savefig(f'{symbol}_backtest.png')
        plt.close()
        
        return f'{symbol}_backtest.png'
        
    def run_backtest(self, symbol, start_date=None, end_date=None):
        """
        Run a backtest and return results
        """
        backtest_data = self.backtest_simple_strategy(symbol, start_date, end_date)
        if backtest_data is None or backtest_data.empty:
            print(f"No data for backtest of {symbol}")
            return None
            
        # Calculate performance metrics
        total_return = backtest_data['strategy_cumulative_returns'].iloc[-1] - 1
        buy_hold_return = backtest_data['cumulative_returns'].iloc[-1] - 1
        
        # Calculate max drawdown
        drawdown = 1 - backtest_data['strategy_cumulative_returns'] / backtest_data['strategy_cumulative_returns'].cummax()
        max_drawdown = drawdown.max()
        
        # Number of trades
        trades = backtest_data[backtest_data['position'] != 0].shape[0]
        
        # Generate chart
        chart_filename = self.plot_backtest(backtest_data, symbol)
        
        results = {
            'symbol': symbol,
            'start_date': backtest_data.index.min(),
            'end_date': backtest_data.index.max(),
            'total_return': total_return,
            'buy_hold_return': buy_hold_return,
            'outperformance': total_return - buy_hold_return,
            'max_drawdown': max_drawdown,
            'trades': trades,
            'chart_filename': chart_filename
        }
        
        return results
        
if __name__ == "__main__":
    # Example usage
    tester = BacktestFromDatabase()
    
    # Choose a ticker and date range
    symbol = 'AAPL'
    start_date = '2023-01-01'
    end_date = '2024-01-01'
    
    # Run backtest
    results = tester.run_backtest(symbol, start_date, end_date)
    
    if results:
        print(f"Backtest Results for {symbol}")
        print(f"Period: {results['start_date']} to {results['end_date']}")
        print(f"Strategy Return: {results['total_return']:.2%}")
        print(f"Buy & Hold Return: {results['buy_hold_return']:.2%}")
        print(f"Outperformance: {results['outperformance']:.2%}")
        print(f"Max Drawdown: {results['max_drawdown']:.2%}")
        print(f"Number of Trades: {results['trades']}")
        print(f"Chart saved as: {results['chart_filename']}")
