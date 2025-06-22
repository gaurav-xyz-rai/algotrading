# 📊 ETFDipBuyer - Technical Analysis Based ETF Signal Generator

## This script analyzes ETFs using technical indicators to identify **dip-buying opportunities** in strong trending ETFs. It fetches hourly data, evaluates signals based on a scoring system, and sends alerts with charts and reasoning.

## 📈 Indicators & Metrics

| Indicator            | Description                                                                                 |
| -------------------- | ------------------------------------------------------------------------------------------- |
| **SMA20**            | Simple Moving Average over 20 periods (short-term trend)                                    |
| **EMA50**            | Exponential Moving Average over 50 periods (intermediate trend)                             |
| **EMA200**           | Exponential Moving Average over 200 periods (long-term trend, used for trend confirmation)  |
| **RSI**              | Relative Strength Index; values < 30 are oversold, > 70 are overbought                      |
| **MACD**             | Moving Average Convergence Divergence – captures trend momentum                             |
| **MACD Signal**      | Signal line used for MACD crossovers                                                        |
| **ATR**              | Average True Range – a measure of volatility                                                |
| **StochRSI**         | Stochastic RSI – momentum oscillator based on RSI values                                    |
| **BB_Low / BB_High** | Bollinger Band Lower and Upper Bounds – identifies extremes in price relative to volatility |

---

## 🚀 Strategy Overview

The strategy focuses on **buying the dip** in **strong uptrending ETFs**. It only generates BUY signals for ETFs trading above their long-term trend (200 EMA), and where multiple indicators suggest a potential rebound.

**BUY Signal Criteria (Score ≥ 3 out of 5):**

1. **RSI < 40** (oversold or nearing oversold)
2. **Price near or below EMA50**
3. **Price near lower Bollinger Band**
4. **MACD still positive** (long-term momentum intact)
5. **Bounce off SMA20** (price crossed above SMA20 after being below it)

**SELL Signal Criteria:**

- RSI > 70 (overbought) and MACD cross down (MACD < MACD Signal)

A cooldown mechanism prevents repeated alerts within a defined window.

---

## 🧠 Signal Logic Explained

- **Strong Trend Filter**:
  First, it checks if the current price is **above the 200 EMA**. If not, it skips evaluation (no BUY signals on weak trends).

- **BUY Evaluation**:
  Each of the following conditions adds +1 to the `signal_score`:

  - RSI < 40
  - Price ≤ EMA50
  - Price ≤ Lower Bollinger Band
  - MACD > 0
  - Previous close < SMA20 and current close > SMA20 (bounce off SMA20)

  A BUY signal is generated if `signal_score >= 3`.

- **SELL Evaluation**:
  If RSI > 70 and MACD < MACD Signal → SELL signal is generated.

---

## 📨 Alert Content

If a valid signal is generated:

- A **chart** is saved and attached.
- An **email** is sent with:

  - Signal type (BUY/SELL)
  - Trend (Uptrend/Sideways)
  - Price, RSI, ATR
  - Reason for signal
  - Suggested Entry, Stop Loss

Stop Loss = Price - 1.5 × ATR

---

## 📁 Log File

Signals are saved to `signal_log.csv` with the following fields:

- Datetime
- Ticker
- Signal
- Trend
- Price
- RSI
- EMA50
- EMA200
- ATR
- Reason

---

## ⚙️ Configuration (`config.py`)

Parameters such as:

- `LOOKBACK_DAYS` – Number of past days to fetch for analysis
- `SIGNAL_COOLDOWN` – Cooldown period in seconds before sending another alert
- `EMAIL_SENDER`, `EMAIL_RECEIVER` – Email credentials
  are configurable in the `config.py` file.

---

## 🔧 Dependencies

Install via pip:

```bash
pip install yfinance ta matplotlib mplfinance pandas
```

---

## 🧪 Usage

```python
from etf_signal import ETFDipBuyer

bot = ETFDipBuyer("QQQ")
bot.process()
```

This will evaluate the ticker and send an email if a signal is detected.

---

## 📬 Example Email Alert

```
Subject: Stock Alert: QQQ - BUY

Signal: BUY
Trend: Uptrend
Price: $370.25
RSI: 35.20
ATR: 1.90
Reason: RSI below 40, Price near/below EMA50, Price near Bollinger Band low

Entry: $370.25
Stop Loss: $367.40
```

---

Let me know if you'd like this exported as a markdown file or added to your project directory!

Here’s a full, clear documentation of how you configured and scheduled your Python momentum screener to run every **Friday at 8 PM EST** on an Amazon Linux 2023 (AL2023) EC2 instance using `systemd` timers.

---

## 📄 **Automated Momentum Screener Setup (Weekly Friday 8 PM EST)**

---

### ✅ Step 1: Create the Shell Script

Create the script that runs your momentum job:

```bash
nano /home/ec2-user/run_momentum.sh
```

Paste this into the file:

```bash
#!/bin/bash
cd /home/ec2-user/AlgoSage/executor/python/stocks
source venv/bin/activate
/usr/local/bin/python3.11 main.py --momentum --region usa
/usr/local/bin/python3.11 main.py --momentum --region india
```

Make it executable:

```bash
chmod +x /home/ec2-user/run_momentum.sh
```

---

### ✅ Step 2: Create the Systemd Service

Create a systemd service to run the script:

```bash
sudo nano /etc/systemd/system/momentum.service
```

Paste the following:

```ini
[Unit]
Description=Run Momentum Screener

[Service]
Type=oneshot
User=ec2-user
WorkingDirectory=/home/ec2-user
ExecStart=/home/ec2-user/run_momentum.sh
StandardOutput=append:/home/ec2-user/momentum.log
StandardError=append:/home/ec2-user/momentum-error.log
```

---

### ✅ Step 3: Create the Systemd Timer

Create a timer to schedule the above service every Friday at 8 PM EST:

```bash
sudo nano /etc/systemd/system/momentum.timer
```

Paste the following:

```ini
[Unit]
Description=Run Momentum Screener every Friday at 8 PM EST

[Timer]
OnCalendar=Fri 20:00
Persistent=true
Timezone=America/New_York

[Install]
WantedBy=timers.target
```

---

### ✅ Step 4: Reload Systemd and Enable the Timer

Run the following commands:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now momentum.timer
```

Verify it's active:

```bash
systemctl list-timers --all | grep momentum
```

---

### ✅ Step 5: Test It Manually (Optional but Recommended)

Run the service once manually:

```bash
sudo systemctl start momentum.service
```

Check logs to verify success:

```bash
journalctl -u momentum.service -n 50 --no-pager
```

Or check the custom logs:

```bash
cat /home/ec2-user/momentum.log
cat /home/ec2-user/momentum-error.log
```

---

### 📌 Notes

- Ensure your virtualenv is created with `/usr/local/bin/python3.11`.
- If using relative paths like `venv/bin/activate`, always set `WorkingDirectory` in the service.
- Timezone is explicitly set to `America/New_York` for EST.

---

This setup ensures that your momentum screener runs reliably every week at the desired time and logs all outputs for troubleshooting or auditing. Let me know if you want to auto-pull from Git, send email alerts, or log to S3.

## IBKR Web API Start

bin/run.sh root/conf.yaml

---

## 📊 Point-in-Time Database for US Stock Market Data

This module stores historical US stock market data in a MySQL database to support backtesting and analysis.

### 📋 Features

- **Structured Storage**: Organizes data in relational tables for tickers, prices, and technical indicators
- **Point-in-Time Recording**: Captures when data was collected for accurate backtesting
- **Automated Updates**: Simple commands to refresh the database with latest market data
- **Technical Indicators**: Pre-calculates and stores common indicators used by strategies

### 🗄️ Database Schema

The database consists of three primary tables:

1. **tickers**: Stock symbols and metadata

   - Symbol, Name, Sector, Industry, Market Cap

2. **stock_prices**: Daily OHLCV price data

   - Open, High, Low, Close, Adjusted Close, Volume, Dividends, Splits

3. **technical_indicators**: Pre-calculated indicators
   - SMA20, EMA50, EMA200, RSI14, MACD, Bollinger Bands, ATR

### 🛠️ Usage

Run the database update tool:

```bash
python main.py --region usa --update_db --days 30
```

Or run the dedicated update script with options:

```bash
python database/update_us_stock_data.py --days 60 --delay 0.5 --file usa_stock_post_mcap_filter.csv --notify
```

### ⚙️ Configuration

Database connection settings are read from the `resources/db_config.py` file:

```python
DATABASE_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "yenesis_market_data",
    "port": 3306,
    "options": {
        "pool_size": 5,
        "pool_recycle": 3600,
        "connect_timeout": 10,
        # Additional options...
    }
}
```

You can generate or update this configuration file using:

```bash
# Generate default configuration in resources/db_config.py
./database/create_db_config.py

# Customize with your own settings
./database/create_db_config.py --host=mydbserver --user=dbuser --password=secret --database=market_data --force
```

These settings can be overridden through:

1. Environment variables:

   - `MYSQL_HOST`
   - `MYSQL_USER`
   - `MYSQL_PASSWORD`
   - `MYSQL_DATABASE`
   - `MYSQL_PORT`

2. Direct parameters when initializing the connection:
   ```python
   db = DatabaseConnection(host="custom-host", user="custom-user")
   ```

---
