import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import SMAIndicator, EMAIndicator, MACD
from ta.volatility import BollingerBands
import matplotlib.dates as mdates

# Fetch Data
ticker = 'AAPL'  # Example stock symbol
df = yf.download(ticker, period="60d", interval="1h")
df['SMA20'] = SMAIndicator(df['Close'], window=20).sma_indicator()
df['EMA50'] = EMAIndicator(df['Close'], window=50).ema_indicator()
df['RSI'] = RSIIndicator(df['Close']).rsi()
df['MACD'] = MACD(df['Close']).macd()
df['MACD_Signal'] = MACD(df['Close']).macd_signal()

bb = BollingerBands(df['Close'])
df['BB_High'] = bb.bollinger_hband()
df['BB_Low'] = bb.bollinger_lband()

# Plot Price with SMA and EMA
fig, axs = plt.subplots(3, 1, figsize=(12, 12), sharex=True)

# Plot 1: Price + SMA + EMA
axs[0].plot(df.index, df['Close'], label='Price', color='black', linewidth=1)
axs[0].plot(df.index, df['SMA20'], label='SMA20', color='blue', linewidth=1)
axs[0].plot(df.index, df['EMA50'], label='EMA50', color='red', linewidth=1)
axs[0].set_title(f"{ticker} - Price, SMA20, EMA50")
axs[0].set_ylabel('Price ($)')
axs[0].legend()

# Plot 2: RSI
axs[1].plot(df.index, df['RSI'], label='RSI', color='orange', linewidth=1)
axs[1].axhline(30, color='green', linestyle='--', label="RSI 30 (Oversold)")
axs[1].axhline(70, color='red', linestyle='--', label="RSI 70 (Overbought)")
axs[1].set_title(f"{ticker} - RSI")
axs[1].set_ylabel('RSI')
axs[1].legend()

# Plot 3: MACD
axs[2].plot(df.index, df['MACD'], label='MACD', color='green', linewidth=1)
axs[2].plot(df.index, df['MACD_Signal'], label='MACD Signal', color='red', linewidth=1)
axs[2].set_title(f"{ticker} - MACD")
axs[2].set_ylabel('MACD')
axs[2].legend()

# Add Bollinger Bands to Price chart
axs[0].fill_between(df.index, df['BB_Low'], df['BB_High'], color='gray', alpha=0.2, label="Bollinger Bands")

# Mark Buy Signals
buy_signals = df[(df['RSI'] < 30) & (df['MACD'] > df['MACD_Signal']) & (df['Close'] <= df['BB_Low'])]
axs[0].scatter(buy_signals.index, buy_signals['Close'], marker='^', color='green', label="Buy Signal", alpha=1)

# Format Date and Show Plot
axs[2].xaxis.set_major_locator(mdates.WeekdayLocator())
axs[2].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
plt.xticks(rotation=45)
plt.tight_layout()

# Show the plot
plt.show()
