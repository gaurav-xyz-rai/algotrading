# main.py

import os
from yahoo_api import YahooFinanceAPI
from utils import format_data, log_error

def main():
    # Initialize the Yahoo Finance API client
    api_client = YahooFinanceAPI()

    # Example stock symbol
    stock_symbol = "AAPL"

    try:
        # Fetch stock data
        stock_data = api_client.get_stock_data(stock_symbol)
        formatted_data = format_data(stock_data)
        print("Current Stock Data:", formatted_data)

        # Fetch historical data
        historical_data = api_client.get_historical_data(stock_symbol, "2023-01-01", "2023-12-31")
        formatted_historical_data = format_data(historical_data)
        print("Historical Stock Data:", formatted_historical_data)

    except Exception as e:
        log_error(e)

if __name__ == "__main__":
    main()