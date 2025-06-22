# === config.py ===
LOOKBACK_DAYS = 250
THRESHOLD_FACTOR = 2
CHECK_INTERVAL = 120  # seconds
SIGNAL_COOLDOWN = 1800  # 30 minutes
FINNHUB_API_KEY = "d0imqs1r01qrfsah5740d0imqs1r01qrfsah574g"
MAX_THREADS = 10
# Email config
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_SENDER = "jason.krazza@gmail.com"
EMAIL_RECEIVER = ["rai.rishi764@gmail.com", "vs21091@gmail.com","aurangjeb@gmail.com"]
#EMAIL_RECEIVER = ["rai.rishi764@gmail.com"]
EMAIL_PASSWORD = "zohjerhnurlemofo"

BUY_SIGNAL_FILE = "./alerts/buy_signals.txt"
IBKR_BASE_URLS = [
    "https://localhost:5001/v1/api",
#    "https://localhost:5002/v1/api"  # add fallback URLs here
]

TELEGRAM_BOT_TOKEN = "7984592625:AAEmh5lB61rLuXLbjdRi3_y9WbNI2zxhhtk"
TELEGRAM_CHAT_ID = "-4870107489"
REGIONAL_CONFIGS = {
    "india": {
        "suffix": ".NS",
        "benchmark_ticker": "^NSEI",
        "marketcap_threshold": 50_000_000_000,
        "momentum_csv": "india_stock_post_mcap_filter.csv",
        "momentum_output": "data/reports/ind_momentum_summary.csv",
        "value_output": "val_india.csv",
        "ema_csv": "india_momentum.csv",
    },
    "usa": {
        "suffix": "",
        "benchmark_ticker": "^GSPC",
        "marketcap_threshold": 1_000_000_000,
        "momentum_csv": "usa_stock_post_mcap_filter.csv",
        "momentum_output": "data/reports/usa_momentum_summary.csv",
        "value_output": "val_usa.csv",
        "ema_csv": "usa_momentum.csv",
        "gateway" : ["https://localhost:5001/v1/api"]
    }
}

def get_config(region):
    return REGIONAL_CONFIGS.get(region.lower())

# Import database configuration from resources
try:
    from resources.db_config import DATABASE_CONFIG, get_db_config
except ImportError:
    # Fallback configuration if resources module is not found
    DATABASE_CONFIG = {
        "host": "localhost",
        "user": "root",
        "password": "",
        "database": "yenesis_market_data",
        "port": 3306,
        "options": {}
    }
    
    def get_db_config():
        return DATABASE_CONFIG.copy()
