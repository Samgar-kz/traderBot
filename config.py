import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

CONFIG = {
    "BALANCE_PERCENT": 5,  # % of balance used per trade
    "BUY_DROP_PERCENT": 0.5,  # Buy when price drops by 0.5%
    "SELL_RISE_PERCENT": 1.0,  # Sell when price rises by 1%
    "STOP_LOSS_PERCENT": 3.0,  # Stop loss at 3% drop
    "TRAILING_STOP_PERCENT": 1.5,  # Trailing stop at 1.5% drop after profit
    "SAFETY_STOP_LOSS": 20,  # 🔥 ✅ ADD THIS LINE (Stop bot if loss > 20%)
    "LOSS_STREAK_LIMIT": 3,  # Stop bot if 3 losses in a row
    "TOP_LIQUID_PAIRS": 5,  # Number of top liquid pairs to track
}
