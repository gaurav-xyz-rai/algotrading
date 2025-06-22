import pandas as pd
from utilities.supertrend import calculate_supertrend
from brokers.utilities.ibkr_api import (
    log,
    check_status,
    get_accounts,
    get_positions,
    get_open_orders,
    get_conid,
    cancel_order,
    place_stop_loss_order,
    extract_ticker
)

pd.set_option("display.max_columns", None)

def main():
    check_status()

    accounts = get_accounts()
    if not accounts:
        log("❌ No accounts available.")
        return

    account_id = accounts[0].get("accountId")
    positions = get_positions(account_id)
    open_orders_response = get_open_orders(account_id)
    open_orders = open_orders_response.get("orders", []) if open_orders_response else []

    # Build dict of existing stop orders keyed by ticker symbol
    existing_stop_orders = {
        order.get("ticker"): {
            "orderId": order.get("orderId"),
            "stop_price": float(order.get("stop_price", 0))
        }
        for order in open_orders
        if order.get("orderType", "").lower() == "stop" and order.get("side", "").upper() == "SELL"
    }

    tickers = {
        extract_ticker(pos.get("contractDesc", "")): pos.get("position", 0)
        for pos in positions
        if pos.get("contractDesc")
    }

    log(f"📊 Portfolio tickers: {list(tickers.keys())}")
    failed_tickers = []

    for ticker, qty in tickers.items():
        result = calculate_supertrend(ticker)
        if not result or "stop_loss" not in result:
            failed_tickers.append(ticker)
            continue

        stop_loss = result["stop_loss"]
        conid = get_conid(ticker)
        if not conid:
            failed_tickers.append(ticker)
            continue

        existing_order = existing_stop_orders.get(ticker)
        if existing_order:
            old_price = existing_order["stop_price"]
            if abs(old_price - stop_loss) > 0.01:
                log(f"🔄 Updating stop loss for {ticker} from {old_price:.2f} to {stop_loss:.2f}")
                if cancel_order(account_id, existing_order["orderId"]):
                    place_stop_loss_order(account_id, conid, qty, stop_loss)
                else:
                    log(f"⚠️ Could not cancel existing order for {ticker}, skipping update.")
                    failed_tickers.append(ticker)
            else:
                log(f"ℹ️ Stop loss for {ticker} already at {stop_loss:.2f}, no update needed.")
        else:
            log(f"🔒 Placing new stop loss for {ticker} @ {stop_loss:.2f} (Qty: {qty})")
            place_stop_loss_order(account_id, conid, qty, stop_loss)

    if failed_tickers:
        log(f"\n⚠️ Tickers with issues: {failed_tickers}")

if __name__ == "__main__":
    main()
