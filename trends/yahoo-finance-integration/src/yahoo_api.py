class YahooFinanceAPI:
    import requests
    import pandas as pd

    BASE_URL = "https://query1.finance.yahoo.com/v8/finance"

    def get_stock_data(self, symbol):
        url = f"{self.BASE_URL}/quote?symbols={symbol}"
        response = self.requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error fetching stock data: {response.status_code}")

    def get_historical_data(self, symbol, start_date, end_date):
        url = f"{self.BASE_URL}/chart/{symbol}?period1={start_date}&period2={end_date}&interval=1d"
        response = self.requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return pd.DataFrame(data['chart']['result'][0]['indicators']['quote'][0])
        else:
            raise Exception(f"Error fetching historical data: {response.status_code}")