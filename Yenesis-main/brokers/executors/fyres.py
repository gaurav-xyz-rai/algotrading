from fyers_apiv3 import fyersModel
import os

# Get from GitLab CI/CD env
access_token = os.getenv("FYERS_ACCESS_TOKEN")
client_id = os.getenv("FYERS_CLIENT_ID")  # also store this in CI/CD

fyers = fyersModel.FyersModel(token=access_token, is_async=False, client_id=client_id)

def place_buy_order():
    data = {
        "symbol": "NSE:SBIN-EQ",
        "qty": 1,
        "type": 1,
        "side": 1,
        "productType": "INTRADAY",
        "limitPrice": 0,
        "stopPrice": 0,
        "validity": "DAY",
        "disclosedQty": 0,
        "offlineOrder": False,
        "stopLoss": 0,
        "takeProfit": 0
    }
    response = fyers.place_order(data)
    print("Buy Order Response:", response)

def close_trade(symbol="NSE:SBIN-EQ-INTRADAY"):
    response = fyers.exit_positions({"id": symbol})
    print("Close Trade Response:", response)

# Trigger functions
place_buy_order()
close_trade()
