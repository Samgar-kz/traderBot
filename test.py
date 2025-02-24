import ccxt
import time
from config import API_KEY, API_SECRET
from bot.telegram_bot import send_telegram_message
from core.binance_api import get_historical_data

# ✅ Подключение к Binance API
exchange = ccxt.binance({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True
})

tickers = exchange.fetch_tickers()
print("Всего пар:", len(tickers))
print("Примеры пар:", list(tickers.keys())[:20])  # Покажет первые 20 пар

hist = get_historical_data("BTC/USDT")
print(hist)