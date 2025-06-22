import requests
import urllib3
import time

urllib3.disable_warnings()

BASE_URL = "https://localhost:5001/v1/api"

def log(msg): print(msg)

# === Account Info ===
def get_accounts():
    try:
        res = requests.get(f"{BASE_URL}/portfolio/accounts", verify=False)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        log(f"❌ Failed to get accounts: {e}")
        return []

# === Confirm Order Reply (e.g., warnings) ===
def confirm_order_reply(reply_id):
    try:
        payload = {"confirmed": True}
        res = requests.post(f"{BASE_URL}/iserver/reply/{reply_id}", json=payload, verify=False)
        res.raise_for_status()
        log(f"✅ Order reply confirmed: {res.json()}")
    except Exception as e:
        log(f"❌ Order reply confirmation failed: {e}")

# === Get conid from ticker ===
def get_conid(symbol):
    try:
        log(f"🔎 Fetching conid for {symbol}...")
        params = {"symbol": symbol, "secType": "STK"}
        res = requests.get(f"{BASE_URL}/iserver/secdef/search", params=params, verify=False)
        res.raise_for_status()
        data = res.json()
        if data and "conid" in data[0]:
            conid = data[0]["conid"]
            log(f"✅ Found conid {conid} for {symbol}")
            return conid
        log("⚠️ No conid found.")
        return None
    except Exception as e:
        log(f"❌ Error fetching conid: {e}")
        return None

# === Get real-time market price ===
def get_market_price(conid, retries=3, delay=1):
    url = f"{BASE_URL}/iserver/marketdata/snapshot"
    params = {"conids": conid, "fields": "31"}  # 31 = last price
    for attempt in range(retries):
        try:
            res = requests.get(url, params=params, verify=False)
            res.raise_for_status()
            data = res.json()
            if isinstance(data, list) and data:
                snapshot = data[0]
                price = snapshot.get("31")
                if price is not None:
                    return float(price)
            log(f"⚠️ Attempt {attempt+1}: No price found - {data}")
        except Exception as e:
            log(f"❌ Attempt {attempt+1}: Price fetch failed: {e}")
        time.sleep(delay)
    return None

# === Check latest order status ===
def get_order_status(account_id):
    try:
        res = requests.get(f"{BASE_URL}/iserver/account/{account_id}/orders", verify=False)
        res.raise_for_status()
        orders = res.json()
        if not orders:
            log("⚠️ No active or recent orders found.")
            return
        latest_order = orders[0]
        log(f"📦 Latest Order Status:")
        log(f"🆔 Order ID: {latest_order.get('orderId')}")
        log(f"📈 Symbol: {latest_order.get('symbol')}")
        log(f"💼 Side: {latest_order.get('side')}")
        log(f"🔢 Quantity: {latest_order.get('totalQuantity')} (filled: {latest_order.get('filledQuantity')})")
        log(f"📊 Status: {latest_order.get('orderStatus')}")
    except Exception as e:
        log(f"❌ Failed to get order status: {e}")

# === Place a market order ===
def place_market_order(account_id, conid, action, qty):
    order = {
        "acctId": account_id,
        "conid": int(conid),
        "orderType": "MKT",
        "side": action.upper(),
        "quantity": qty,
        "tif": "DAY",
        "secType": "STK",
        "outsideRth": False,
    }
    try:
        res = requests.post(
            f"{BASE_URL}/iserver/account/{account_id}/orders",
            json={"orders": [order]},
            verify=False
        )
        res.raise_for_status()
        response = res.json()
        log(f"✅ Order placed: {response}")
        for msg in response:
            if 'id' in msg:
                confirm_order_reply(msg['id'])

        # Wait for status to update
        time.sleep(2)
        get_order_status(account_id)

    except Exception as e:
        log(f"❌ Order placement failed: {e}")

# === Test function to run everything ===
def test_trade(ticker="AAPL", action="BUY", max_cash=100):
    accounts = get_accounts()
    if not accounts:
        log("❌ No accounts available.")
        return
    account_id = accounts[0].get("accountId")

    conid = get_conid(ticker)
    if not conid:
        return

    price = get_market_price(conid)
    if not price:
        log("❌ Could not get market price.")
        return

    qty = int(max_cash // price)
    if qty < 1:
        log(f"⚠️ Not enough cash to buy 1 share of {ticker}. Price: {price}")
        return

    log(f"🛒 Placing {action.upper()} order for {qty} shares of {ticker} at approx. ${price:.2f}")
    place_market_order(account_id, conid, action, qty)

# === Run the test ===
if __name__ == "__main__":
    test_trade(ticker="NVTS", action="BUY", max_cash=20)
