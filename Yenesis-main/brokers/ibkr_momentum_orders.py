import os
import pandas as pd
from brokers.utilities.ibkr_api import (
    check_status, get_accounts, get_available_cash, get_positions,
    place_market_order, get_market_price, get_conid, extract_ticker, get_open_orders
)
from utilities.email_utils import send_email
from utilities.telegram_util import send_telegram_message

def log(msg):
    print(msg)

def execute_momentum_trades(account_id, trade_type, csv_path="../data/reports/usa_momentum_summary.csv", top_n=20, dry_run=True):
    summary = {
        "successful_buys": [],
        "failed_buys": [],
        "successful_sells": [],
        "failed_sells": [],
    }

    try:
        df = pd.read_csv(csv_path, comment="#")
        df = df[df["ticker"].notna() & (df["ticker"] != "BENCHMARK")]
        top_df = df.sort_values("momentum_score", ascending=False).head(top_n)
        top_tickers = set(top_df["ticker"])

        log(f"🔥 Top {top_n} momentum tickers: {top_tickers}")


        raw_positions = get_positions(account_id)
        #log(f"📦 Raw positions response: {raw_positions}")

        # Safely build held_positions
        held_positions = {
            extract_ticker(p.get("contractDesc")): p
            for p in raw_positions
            if isinstance(p, dict) and "contractDesc" in p
        }


        #held_positions = {extract_ticker(p.get("contractDesc")): p for p in get_positions(account_id)}
        open_orders = get_open_orders(account_id)
        open_order_tickers = set()

        for order in open_orders:
            if isinstance(order, dict):
                desc = order.get("description", "")
                open_order_tickers.add(extract_ticker(desc))
            else:
                log(f"⚠️ Skipping non-dict open order item: {order}")

        log(f"📊 Held positions: {list(held_positions.keys())}")
        log(f"📬 Open orders: {list(open_order_tickers)}")

        if trade_type in ("sell", "both"):
            for ticker, pos in held_positions.items():
                conid, qty = pos.get("conid"), pos.get("position", 0)
                if ticker in open_order_tickers:
                    log(f"⏸️ Skipping SELL for {ticker}: already has an open order")
                    continue
                if ticker not in top_tickers and conid and qty > 0:
                    log(f"🛑 SELL: {ticker} (Qty: {qty})")
                    if not dry_run:
                        try:
                            place_market_order(account_id, conid, "SELL", qty)
                            summary["successful_sells"].append(f"{ticker} (Qty: {qty})")
                        except Exception:
                            summary["failed_sells"].append(f"{ticker} (Qty: {qty})")
                    else:
                        log(f"[DRY-RUN] Would SELL {ticker} Qty: {qty}")
                elif ticker in top_tickers:
                    log(f"✅ HOLD: {ticker}")

        if trade_type in ("buy", "both"):
            buy_candidates = [ticker for ticker in top_tickers if ticker not in held_positions and ticker not in open_order_tickers]
            if not buy_candidates:
                log("ℹ️ No new stocks to buy.")
                return summary

            available_cash = get_available_cash(account_id) - 10
            cash_per_stock = available_cash / len(buy_candidates)
            log(f"💰 Available cash: ${available_cash:.2f}, Stocks to buy: {len(buy_candidates)}, Cash per stock: ${cash_per_stock:.2f}")

            for ticker in buy_candidates:
                conid = get_conid(ticker)
                if not conid:
                    log(f"❌ Skipping {ticker}: no conid found")
                    summary["failed_buys"].append(f"{ticker} (Qty: unknown)")
                    continue

                price = get_market_price(conid)
                if not price:
                    log(f"❌ Skipping {ticker}: no price found for conid {conid}")
                    summary["failed_buys"].append(f"{ticker} (Qty: unknown)")
                    continue

                qty = int(cash_per_stock // price)
                if qty < 1:
                    log(f"❌ Skipping {ticker}: insufficient cash (${cash_per_stock:.2f}) for price ${price:.2f}")
                    summary["failed_buys"].append(f"{ticker} (Qty: {qty})")
                    continue

                log(f"🛒 BUY: {ticker} (Price: {price}, Qty: {qty})")
                if not dry_run:
                    try:
                        place_market_order(account_id, conid, "BUY", qty)
                        summary["successful_buys"].append(f"{ticker} (Qty: {qty})")
                    except Exception:
                        summary["failed_buys"].append(f"{ticker} (Qty: {qty})")
                else:
                    log(f"[DRY-RUN] Would BUY {ticker} Qty: {qty} at ${price}")

    except Exception as e:
        log(f"❌ Momentum trading error: {e}")

    return summary


def main(action, base_dir=None, region_config=None, dry_run=False):
    check_status()
    log(f"⚙️ Executing momentum action: {action}")

    accounts = get_accounts()
    if not accounts:
        log("❌ No accounts available.")
        return

    account_id = accounts[0].get("accountId")
    csv_path = os.path.join(base_dir, region_config["momentum_output"])
    log(f"📄 Using momentum CSV: {csv_path}")

    summary = execute_momentum_trades(account_id, trade_type=action, csv_path=csv_path, dry_run=dry_run)

    subject = f"[StratBot] Momentum Trades Summary ({action.upper()})"
    body = f"""
📈 Momentum Trades Completed ({'DRY RUN' if dry_run else 'LIVE'})

✅ Successful Buys:
{chr(10).join(summary['successful_buys']) or 'None'}

❌ Failed Buys (Review and consider manual orders):
{chr(10).join(summary['failed_buys']) or 'None'}

✅ Successful Sells:
{chr(10).join(summary['successful_sells']) or 'None'}

❌ Failed Sells (Review and consider manual orders):
{chr(10).join(summary['failed_sells']) or 'None'}
"""

    send_email(
        subject=subject,
        body=body.strip(),
        to_email=["rishi.rai764@gmail.com"],  # Update with your actual address
        from_email="jason.krazza@gmail.com"
    )


    # === Send to Telegram ===
    telegram_message = f"""
📈 *Momentum Trades Summary* ({'DRY RUN' if dry_run else 'LIVE'})

✅ *Successful Buys:*
{chr(10).join(summary['successful_buys']) or 'None'}

❌ *Failed Buys:*
{chr(10).join(summary['failed_buys']) or 'None'}

✅ *Successful Sells:*
{chr(10).join(summary['successful_sells']) or 'None'}

❌ *Failed Sells:*
{chr(10).join(summary['failed_sells']) or 'None'}
"""
    #send_telegram_message(telegram_message.strip())
    
if __name__ == "__main__":
    main("buy", dry_run=True)  # Default dry-run mode enabled
