import os
from dotenv import load_dotenv

# ✅ Загружаем переменные окружения
load_dotenv()

# ✅ API ключи
API_KEY = os.getenv('API_KEY', 'your_default_api_key')
API_SECRET = os.getenv('API_SECRET', 'your_default_api_secret')

# ✅ Telegram настройки
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', 'your_default_telegram_token')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', 'your_default_chat_id')

# ✅ Торговые параметры
CONFIG = {
    "BALANCE_PERCENT": float(os.getenv("BALANCE_PERCENT", 5)),  # % баланса на сделку
    "BUY_DROP_PERCENT": float(os.getenv("BUY_DROP_PERCENT", 0.5)),  # Покупка при падении
    "SELL_RISE_PERCENT": float(os.getenv("SELL_RISE_PERCENT", 1.0)),  # Продажа при росте
    "STOP_LOSS_PERCENT": float(os.getenv("STOP_LOSS_PERCENT", 3.0)),  # Стоп-лосс
    "TRAILING_STOP_PERCENT": float(os.getenv("TRAILING_STOP_PERCENT", 1.5)),  # Трейлинг-стоп
    "SAFETY_STOP_LOSS": float(os.getenv("SAFETY_STOP_LOSS", 20)),  # 🔥 Остановка при убытке > 20%
    "LOSS_STREAK_LIMIT": int(os.getenv("LOSS_STREAK_LIMIT", 3)),  # Остановка после 3 подряд убытков
    "TOP_LIQUID_PAIRS": int(os.getenv("TOP_LIQUID_PAIRS", 5)),  # Количество топ-пар
}