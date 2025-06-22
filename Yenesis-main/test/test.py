import requests
import pandas as pd
import datetime

symbol = "AAPL"
interval = "1d"
range_period = "5d"

url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
params = {
    "interval": interval,
    "range": range_period,
    "includePrePost": "false",
    "corsDomain": "finance.yahoo.com"
}

response = requests.get(url, params=params)

if response.status_code == 200:
    data = response.json()
    timestamps = data["chart"]["result"][0]["timestamp"]
    indicators = data["chart"]["result"][0]["indicators"]["quote"][0]

    df = pd.DataFrame(indicators)
    df["timestamp"] = [datetime.datetime.fromtimestamp(ts) for ts in timestamps]
    df.set_index("timestamp", inplace=True)

    print(df)
else:
    print("Error:", response.status_code, response.text)
