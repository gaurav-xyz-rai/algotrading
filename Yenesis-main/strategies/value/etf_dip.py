import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import SMAIndicator, EMAIndicator, MACD
from ta.volatility import AverageTrueRange, BollingerBands
import finnhub
import matplotlib.pyplot as plt
import mplfinance as mpf
import os
from datetime import datetime
from utilities.email_utils import send_email
from utilities.log_util import get_logger
from config import *
logger = get_logger()

# Configurable thresholds
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70
SIGNAL_LOG_FILE = "signal_log.csv"

class ETFDipBuyer:
    def __init__(self, ticker):
        self.ticker = ticker
        self.last_signal_time = None
        self.df = pd.DataFrame()

    def fetch_data(self, force=False):
        if not force and not self.df.empty:
            return self.df

        try:
            df = yf.download(self.ticker, period=f'{LOOKBACK_DAYS}d', interval='1h', progress=False)
            if df.empty:
                raise ValueError("Empty data from Yahoo Finance")
        except Exception as e:
            logger.warning(f"Yahoo Finance data fetch failed for {self.ticker}: {e}")
            print(f"Yahoo Finance failed for {self.ticker}: {e}", flush=True)
        try:
            df.dropna(inplace=True)
            close = df['Close'].squeeze()
            high = df['High'].squeeze()
            low = df['Low'].squeeze()

            df['SMA20'] = SMAIndicator(close=close, window=20).sma_indicator()
            df['EMA50'] = EMAIndicator(close=close, window=50).ema_indicator()
            df['EMA200'] = EMAIndicator(close=close, window=200).ema_indicator()
            df['RSI'] = RSIIndicator(close=close).rsi()
            df['ATR'] = AverageTrueRange(high=high, low=low, close=close).average_true_range()
            df['MACD'] = MACD(close=close).macd()
            df['MACD_Signal'] = MACD(close=close).macd_signal()
            df['StochRSI'] = StochasticOscillator(high=high, low=low, close=close).stoch()
            bb = BollingerBands(close=close)
            df['BB_High'] = bb.bollinger_hband()
            df['BB_Low'] = bb.bollinger_lband()

            self.df = df
            return df
        except Exception as e3:
            logger.error(f"Failed processing data for {self.ticker}: {e3}")
            print(f"Failed processing data for {self.ticker}: {e3}", flush=True)
            return pd.DataFrame()

    def generate_chart(self, filename):
        df = self.df[-100:].copy()
        df.index.name = 'Date'
        try:
            mpf.plot(df, type='candle', mav=(20, 50), volume=True, style='charles', savefig=filename)
        except Exception as e:
            logger.error(f"Failed to generate chart for {self.ticker}: {e}")
            print(f"Failed to generate chart for {self.ticker}: {e}", flush=True)

    def evaluate_signal(self):
        if self.df.empty:
            return None

        df = self.df.copy()
        latest = self.df.iloc[-1]

        price   = latest['Close'].item()   # scalar float
        sma20   = latest['SMA20'].item()
        ema50   = latest['EMA50'].item()
        ema200  = latest['EMA200'].item()
        rsi     = latest['RSI'].item()
        atr     = latest['ATR'].item()
        macd    = latest['MACD'].item()
        macd_signal = latest['MACD_Signal'].item()
        stoch_rsi   = latest['StochRSI'].item()
        bb_low      = latest['BB_Low'].item()

        reasons = []
        signal_score = 0

        # Condition 1: RSI below 30
        if rsi < 30:
            signal_score += 1
            reasons.append("RSI < 30 (oversold)")

        # Condition 2: MACD turning up (bullish cross)
        if macd > macd_signal:
            signal_score += 1
            reasons.append("MACD turning up")

        # Condition 3: Price near/below EMA50
        if price <= ema50 * 1.02:
            signal_score += 1
            reasons.append("Price near/below EMA50")

        # Condition 4: Price near lower Bollinger Band
        if price <= bb_low * 1.01:
            signal_score += 1
            reasons.append("Price near lower BB")

        # Condition 5: Price near recent N-bar low (e.g., 20)
        n = 20
        recent_low = df['Low'].tail(n).min().item()
        print("Recent low:", recent_low)
        print("Price:", price)
        if price <= recent_low * 1.05:
            signal_score += 1
            reasons.append(f"Near {n}-bar low")


        # Condition 6: Bullish multi-bar pattern (bullish engulfing or hammer)
        def is_bullish_engulfing(c1, o1, c2, o2):
            return (float(c2) > float(o2)) and (float(c1) < float(o1)) and (float(c2) > float(o1)) and (float(o2) < float(c1))


        def is_hammer(c, o, h, l):
            c_val = c.iloc[0]
            o_val = o.iloc[0]
            h_val = h.iloc[0]
            l_val = l.iloc[0]

            lower_wick = min(c_val, o_val) - l_val
            upper_wick = h_val - max(c_val, o_val)
            body = abs(c_val - o_val)

            return lower_wick > (2 * body) and upper_wick < body

        c1, o1 = df['Close'].iloc[-2], df['Open'].iloc[-2]
        c2, o2 = df['Close'].iloc[-1], df['Open'].iloc[-1]
        h, l = df['High'].iloc[-1], df['Low'].iloc[-1]

        if is_bullish_engulfing(c1, o1, c2, o2):
            signal_score += 1
            reasons.append("Bullish engulfing pattern")

        elif is_hammer(c2, o2, h, l):
            signal_score += 1
            reasons.append("Hammer candle")

        # Determine trend
        trend = "Uptrend" if price > sma20 and sma20 > ema50 else "Sideways or Down"

        signal = None
        if signal_score >= 5:
            signal = "BUY"
        elif rsi > 70 and macd < macd_signal:
            signal = "SELL"

        return {
            "signal": signal,
            "trend": trend,
            "score": signal_score,
            "price": price,
            "rsi": rsi,
            "ema50": ema50,
            "ema200": ema200,
            "atr": atr,
            "reason": ", ".join(reasons)
    }


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
        df.to_csv(SIGNAL_LOG_FILE, mode='a', header=not os.path.exists(SIGNAL_LOG_FILE), index=False)

    def process(self):
        self.fetch_data()

        data = self.evaluate_signal()
        if not data or not data["signal"]:
            return

        if not self.can_alert():
            print(f"Cooldown active for {self.ticker}. Skipping alert.", flush=True)
            return

        filename = f"{self.ticker}_chart.png"
        self.generate_chart(filename)

        body = (
            f"Signal: {data['signal']}\n"
            f"Trend: {data['trend']}\n"
            f"Price: ${data['price']:.2f}\n"
            f"RSI: {data['rsi']:.2f}\n"
            f"ATR: {data['atr']:.2f}\n"
            f"Reason: {data['reason']}\n\n"
            f"Entry: ${data['price']:.2f}\n"
            f"Stop Loss: ${data['price'] - 1.5 * data['atr']:.2f}\n"
        )

        send_email(
            subject=f"Stock Alert: {self.ticker} - {data['signal']}",
            body=body,
            to_email=EMAIL_RECEIVER[0],
            from_email=EMAIL_SENDER,
            chart_path=filename
        )

        self.log_signal(data)
        logger.info(f"Alert sent for {self.ticker}: {data['signal']} | RSI: {data['rsi']:.2f} | Trend: {data['trend']}")
        print(f"Alert sent for {self.ticker}: {data['signal']} | RSI: {data['rsi']:.2f} | Trend: {data['trend']}", flush=True)
        self.mark_alerted()

        try:
            os.remove(filename)
        except Exception as e:
            logger.warning(f"Could not delete chart {filename}: {e}")
            print(f"Could not delete chart {filename}: {e}", flush=True)
