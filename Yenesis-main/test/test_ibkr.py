import requests
import urllib3

urllib3.disable_warnings()
BASE_URL = "https://localhost:5001/v1/api"

def get_conid(symbol):
    print(f"🔍 Fetching contract ID for {symbol}...")
    response = requests.get(f"{BASE_URL}/iserver/secdef/search", params={"symbol": symbol}, verify=False)
    response.raise_for_status()
    data = response.json()
    if not data:
        raise Exception("No conid found for symbol.")
    return data[0]['conid']

def get_account_id():
    print("📋 Fetching account ID...")
    response = requests.get(f"{BASE_URL}/iserver/accounts", verify=False)
    response.raise_for_status()
    data = response.json()
    return data[0] if data else None

def place_order(account_id, conid, quantity=1):
    print(f"🛒 Placing order for conid={conid}...")
    order = {
        "conid": conid,
        "secType": "STK",
        "orderType": "MKT",
        "listingExchange": "SMART",
        "outsideRTH": False,
        "quantity": quantity,
        "side": "BUY",
        "tif": "DAY"
    }

    response = requests.post(
        f"{BASE_URL}/iserver/account/{account_id}/order",
        json=order,
        verify=False
    )
    print("🧾 Response:", response.status_code, response.text)

def main():
    try:
        symbol = "AAPL"
        conid = get_conid(symbol)
        account_id = get_account_id()
        place_order(account_id, conid)
    except Exception as e:
        print("❌ Error:", e)

if __name__ == "__main__":
    main()
