import yfinance as yf
import pandas as pd
from ta.trend import EMAIndicator
from ta.volatility import AverageTrueRange
import mplfinance as mpf
import os
from datetime import datetime
import pandas_ta as ta
from utilities.email_utils import send_email
from utilities.log_util import get_logger
from config import *
import matplotlib
from utilities.git import git_commit
matplotlib.use('Agg')

logger = get_logger()

SIGNAL_LOG_FILE = "./alerts/ema_pullback_log.csv"

class EMAPullbackAnalyzer:
    def __init__(self, ticker):
        self.ticker = ticker
        self.last_signal_time = None
        self.df = pd.DataFrame()

    def load_active_buy_signals(self):
        if not os.path.exists(BUY_SIGNAL_FILE):
            return set()
        with open(BUY_SIGNAL_FILE, 'r') as f:
            return set(line.strip() for line in f.readlines())

    def save_active_buy_signals(self, signals):
        with open(BUY_SIGNAL_FILE, 'w') as f:
            for ticker in sorted(signals):
                f.write(ticker + '\n')

    def fetch_data(self, force=False):
        if not force and not self.df.empty:
            return self.df

        try:
            df = yf.download(
                self.ticker,
                period=f'{LOOKBACK_DAYS}d',
                interval='1d',
                auto_adjust=True,
                progress=False
            )

            if df.empty:
                logger.error(f"Failed to fetch data for {self.ticker}: Empty DataFrame returned.")
                return pd.DataFrame()

            df.dropna(inplace=True)

            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            #print("DF Length:",len(df))  # or len(prices)
            # Add EMAs and ATR
            df['EMA20'] = EMAIndicator(close=df['Close'], window=20).ema_indicator()
            df['EMA50'] = EMAIndicator(close=df['Close'], window=50).ema_indicator()
            df['EMA100'] = EMAIndicator(close=df['Close'], window=100).ema_indicator()
            df['EMA200'] = EMAIndicator(close=df['Close'], window=200).ema_indicator()
            df['ATR'] = AverageTrueRange(high=df['High'], low=df['Low'], close=df['Close']).average_true_range()

            # Add SuperTrend
            supertrend = ta.supertrend(df['High'], df['Low'], df['Close'], length=10, multiplier=3.0)
            df = df.join(supertrend)

            # ✅ Ensure SuperTrend columns exist
            expected_columns = ['SUPERT_10_3.0', 'SUPERTd_10_3.0']
            missing = [col for col in expected_columns if col not in df.columns]
            if missing:
                logger.error(f"Missing SuperTrend columns for {self.ticker}: {missing}")
                return pd.DataFrame()

            self.df = df
            return df

        except Exception as e:
            logger.error(f"Failed fetching data for {self.ticker}: {e}")
            return pd.DataFrame()

    def generate_chart(self, filename):
        df = self.df[-100:].copy()
        df.index.name = 'Date'

        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            custom_style = mpf.make_mpf_style(
                base_mpf_style='charles',
                mavcolors=['blue', 'green', 'orange', 'red'],
                rc={
                    'font.size': 10,
                    'axes.labelsize': 'large',
                    'axes.titlesize': 'x-large',
                }
            )

            addplots = [
                mpf.make_addplot(df['EMA20'], color='blue', width=1.0),
                mpf.make_addplot(df['EMA50'], color='green', width=1.0),
                mpf.make_addplot(df['EMA100'], color='orange', width=1.0),
                mpf.make_addplot(df['EMA200'], color='red', width=1.0),
                mpf.make_addplot(df['SUPERT_10_3.0'], color='purple', width=1.0),
            ]

            mpf.plot(
                df,
                type='candle',
                addplot=addplots,
                volume=True,
                style=custom_style,
                title=f"{self.ticker} Price Chart with EMA & SuperTrend",
                ylabel='Price',
                ylabel_lower='Volume',
                figratio=(16, 9),
                figscale=1.2,
                savefig=dict(fname=filename, dpi=150, bbox_inches='tight')
            )
        except Exception as e:
            logger.error(f"Failed to generate chart for {self.ticker}: {e}")

    def evaluate_signal(self):
        if self.df.empty:
            return None
        try:
            price = float(self.df['Close'].iloc[-1])
            ema20 = float(self.df['EMA20'].iloc[-1])
            ema50 = float(self.df['EMA50'].iloc[-1])
            ema100 = float(self.df['EMA100'].iloc[-1])
            ema200 = float(self.df['EMA200'].iloc[-1])
            atr = float(self.df['ATR'].iloc[-1])
            supertrend_dir = int(self.df['SUPERTd_10_3.0'].iloc[-1])
            #logger.info(f"{self.ticker} | Price: {price}, EMA20: {ema20}, EMA50: {ema50}, EMA100: {ema100}, EMA200: {ema200}, Supertrend Dir: {supertrend_dir}")
            # ✅ BUY Signal
            if ema20 > ema50 > ema100 > ema200:
                if abs(price - ema50) / ema50 < 0.02 and supertrend_dir == 1:
                    logger.info(f"BUY: Pullback to EMA50 in strong uptrend for {self.ticker}, price: {price}, EMA50: {ema50},EMA100: {ema100},  EMA200: {ema200}")
                    entry = price
                    stop_loss = entry - (1.2 * atr)
                    take_profit = entry + (2.4 * atr)
                    return {
                        "signal": "BUY",
                        "price": price,
                        "entry": entry,
                        "stop_loss": stop_loss,
                        "take_profit": take_profit,
                        "EMA": f"\n\tEMA20: {ema20:.2f}\n\tEMA50: {ema50:.2f}\n\tEMA100: {ema100:.2f}\n\tEMA200: {ema200:.2f}",
                        "trend": "Uptrend",

                        "reason": "Pullback to EMA50 in strong uptrend with SuperTrend confirmation"
                    }

            # ✅ SELL Signal
            if supertrend_dir == -1:
                #logger.info(f"SuperTrend SELL signal detected for {self.ticker}")
                return {
                    "signal": "SELL",
                    "price": price,
                    "EMA": f"\n\tEMA20: {ema20:.2f}\n\tEMA50: {ema50:.2f}\n\tEMA100: {ema100:.2f}\n\tEMA200: {ema200:.2f}",
                    "trend": "Downtrend",
                    "reason": "SuperTrend turned to SELL"
                }

        except Exception as e:
            logger.error(f"Error evaluating signal for {self.ticker}: {e}")
            return None

        return None

    def can_alert(self):
        if not self.last_signal_time:
            return True
        elapsed = (datetime.now() - self.last_signal_time).total_seconds()
        return elapsed > SIGNAL_COOLDOWN

    def mark_alerted(self):
        self.last_signal_time = datetime.now()

    def log_signal(self, data):
        log_data = {
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ticker": self.ticker,
            **data
        }
        df = pd.DataFrame([log_data])
        os.makedirs("alerts", exist_ok=True)
        df.to_csv(
            SIGNAL_LOG_FILE,
            mode='a',
            header=not os.path.exists(SIGNAL_LOG_FILE),
            index=False
        )

    def process(self):
        df = self.fetch_data()
        if df.empty:
            logger.error(f"Skipping {self.ticker} due to empty data after fetch.")
            return

        data = self.evaluate_signal()
        if not data:
            return

        active_buy_signals = self.load_active_buy_signals()

        if data["signal"] == "SELL":
            if self.ticker not in active_buy_signals:
                #logger.info(f"No previous BUY for {self.ticker}, skipping SELL.")
                return
            else:
                active_buy_signals.remove(self.ticker)

        if data["signal"] == "BUY":
            active_buy_signals.add(self.ticker)

        if not self.can_alert():
            logger.info(f"Cooldown active for {self.ticker}. Skipping alert.")
            return

        filename = f"./charts/{self.ticker}_ema_pullback_chart.png"
        self.generate_chart(filename)

        body = (
            f"Signal: {data['signal']}\n"
            f"Trend: {data['trend']}\n"
            f"Price: {data['price']:.2f}\n"
            f"EMA: {data['EMA']}\n"
            f"Reason: {data['reason']}\n"
        )

        if data["signal"] == "BUY":
            body += (
                f"\nEntry: {data['entry']:.2f}\n"
                f"Stop Loss: {data['stop_loss']:.2f}\n"
                f"Take Profit: {data['take_profit']:.2f}\n"
            )

        send_email(
            subject=f"Stock Alert: {self.ticker} - {data['signal']}",
            body=body,
            to_email=EMAIL_RECEIVER,
            from_email=EMAIL_SENDER,
            chart_path=filename
        )

        self.log_signal(data)
        logger.info(f"Alert sent for {self.ticker}: {data['signal']} | Trend: {data['trend']}")
        self.mark_alerted()
        self.save_active_buy_signals(active_buy_signals)
        git_commit("./alerts/buy_signals.txt")
        try:
            os.remove(filename)
        except Exception as e:
            logger.warning(f"Could not delete chart {filename}: {e}")
