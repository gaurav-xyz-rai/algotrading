import requests
import urllib3
import time
from config import IBKR_BASE_URLS as BASE_URLS

urllib3.disable_warnings()


def log(msg):
    print(msg)


def try_requests_call(method, path, **kwargs):
    """Tries multiple BASE_URLs until a request succeeds."""
    for base_url in BASE_URLS:
        url = f"{base_url}{path}"
        try:
            res = method(url, verify=False, **kwargs)
            res.raise_for_status()
            return res
        except requests.RequestException as e:
            log(f"⚠️ Failed request to {url}: {e}")
    log(f"❌ All base URLs failed for path: {path}")
    return None


def check_status():
    res = try_requests_call(requests.get, "/iserver/auth/status")
    if res:
        log(f"IBKR Web API Auth Status: {res.json().get('authenticated')}")


def get_accounts():
    res = try_requests_call(requests.get, "/portfolio/accounts")
    return res.json() if res else []


def get_available_cash(account_id):
    res = try_requests_call(requests.get, f"/portfolio/{account_id}/ledger")
    if res:
        usd = res.json().get("USD", {})
        return usd.get("cashbalance", 0.0)
    return 0.0


def get_positions(account_id):
    res = try_requests_call(requests.get, f"/portfolio/{account_id}/positions")
    if not res:
        return []
    try:
        data = res.json()
        if isinstance(data, list):
            return data
        else:
            log(f"⚠️ Unexpected positions response (not a list): {data}")
            return []
    except Exception as e:
        log(f"❌ Failed to parse positions JSON: {e}")
        return []


def get_conid(symbol):
    params = {"symbol": symbol, "secType": "STK"}
    res = try_requests_call(requests.get, "/iserver/secdef/search", params=params)
    if res:
        data = res.json()
        if data and isinstance(data, list) and "conid" in data[0]:
            return data[0]["conid"]
    log(f"⚠️ No conid found for {symbol}")
    return None


def confirm_order_reply(reply_id):
    payload = {"confirmed": True}
    res = try_requests_call(requests.post, f"/iserver/reply/{reply_id}", json=payload)
    if res:
        log(f"✅ Order reply confirmed: {res.json()}")
        return res.json()
    return None


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
    payload = {"orders": [order]}
    res = try_requests_call(requests.post, f"/iserver/account/{account_id}/orders", json=payload)
    if res:
        response = res.json()
        log(f"✅ {action.upper()} order placed: {response}")
        if isinstance(response, list):
            for msg in response:
                if 'id' in msg:
                    confirm_order_reply(msg['id'])
        return response
    return None


def get_market_price(conid, retries=3, delay=1):
    for attempt in range(retries):
        res = try_requests_call(
            requests.get,
            "/iserver/marketdata/snapshot",
            params={"conids": conid, "fields": "31"}
        )
        if res:
            data = res.json()
            if isinstance(data, list) and data:
                snapshot = data[0]
                price = snapshot.get("31")
                if price is not None:
                    return float(price)
            log(f"⚠️ Attempt {attempt + 1}: No price for conid {conid}")
        time.sleep(delay)
    log(f"❌ Failed to fetch market price for conid {conid}")
    return None


def place_stop_loss_order(account_id, conid, qty, stop_price):
    order = {
        "acctId": account_id,
        "conid": int(conid),
        "orderType": "STP",
        "side": "SELL",
        "quantity": int(qty),
        "price": round(stop_price, 2),
        "tif": "GTC",
        "secType": "STK",
        "outsideRth": False
    }

    res = try_requests_call(requests.post, f"/iserver/account/{account_id}/orders", json={"orders": [order]})
    if not res:
        return False

    data = res.json()
    log(f"📝 Initial order response: {data}")

    if isinstance(data, list):
        first = data[0]
        if "replyid" in first:
            log(f"⚠️ Order requires confirmation: {first.get('message', '')}")
            confirm_data = confirm_order_reply(first["replyid"])
            if confirm_data:
                order_id = confirm_data.get("order_id") or confirm_data.get("id")
                log(f"✅ Stop loss order confirmed (ID: {order_id})")
            return True

    log(f"✅ Stop loss order placed successfully.")
    return True


def cancel_order(account_id, order_id):
    res = try_requests_call(requests.delete, f"/iserver/account/{account_id}/order/{order_id}")
    if res:
        log(f"✅ Order {order_id} cancelled successfully.")
        return True
    log(f"❌ Failed to cancel order {order_id}.")
    return False


def get_open_orders(account_id):
    res = try_requests_call(requests.get, "/iserver/account/orders")
    if res:
        return res.json()
    return {}


# === Utils ===
def extract_ticker(contract_desc):
    return contract_desc.split()[0] if contract_desc else ""


def test_place_order():
    check_status()
    accounts = get_accounts()
    if not accounts:
        print("❌ No accounts found.")
        return

    account_id = accounts[0].get("accountId")
    print(f"✅ Using account: {account_id}")

    symbol = "MOMO"
    conid = get_conid(symbol)
    if not conid:
        print(f"❌ Could not fetch conid for {symbol}")
        return

    print(f"✅ Fetched conid for {symbol}: {conid}")

    action = "BUY"
    quantity = 1
    print(f"🚀 Placing {action} order for {symbol}, Qty: {quantity}")
    place_market_order(account_id, conid, action, quantity)


if __name__ == "__main__":
    test_place_order()
