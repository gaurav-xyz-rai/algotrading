import requests
import urllib3

urllib3.disable_warnings()

BASE_URL = "https://localhost:5001/v1/api"

def check_status():
    print("🔐 Checking IBKR Web API auth status...")
    try:
        res = requests.get(f"{BASE_URL}/iserver/auth/status", verify=False)
        res.raise_for_status()
        print("✅ Auth Status:", res.json())
    except requests.RequestException as e:
        print("❌ Failed to check auth status:", e)

def get_accounts():
    print("📂 Fetching account information...")
    try:
        res = requests.get(f"{BASE_URL}/portfolio/accounts", verify=False)
        res.raise_for_status()
        accounts = res.json()
        print("✅ Accounts:", accounts)
        return accounts
    except requests.RequestException as e:
        print("❌ Failed to fetch accounts:", e)
        return []

def get_positions(account_id):
    print(f"📊 Fetching positions for account: {account_id}...")
    try:
        res = requests.get(f"{BASE_URL}/portfolio/{account_id}/positions", verify=False)
        res.raise_for_status()
        positions = res.json()
        if not positions:
            print("ℹ️ No open positions found.")
        else:
            for p in positions:
                conid = p.get("conid", "N/A")
                desc = p.get("contractDesc", "Unknown")
                qty = p.get("position", 0)
                avg_cost = p.get("averageCost", "N/A")
                market_val = p.get("marketValue", "N/A")
                unreal_pnl = p.get("unrealizedPnl", "N/A")

                print(f"📈 {conid} | {desc} | Qty: {qty} | "
                      f"Avg Cost: {avg_cost} | Market Value: {market_val} | "
                      f"Unrealized PnL: {unreal_pnl}")
        return positions
    except requests.RequestException as e:
        print("❌ Failed to fetch positions:", e)
        return []


if __name__ == "__main__":
    check_status()
    accounts = get_accounts()
    if accounts:
        account_id = accounts[0].get("accountId")
        get_positions(account_id)
