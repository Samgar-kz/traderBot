import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

CONFIG = {
    "BALANCE_PERCENT": 5,  # % от баланса для сделки
    "BUY_DROP_PERCENT": 0.5,  # Покупка при падении на 0.5%
    "SELL_RISE_PERCENT": 1.0,  # Продажа при росте на 1%
    "STOP_LOSS_PERCENT": 3.0,  # Стоп-лосс при падении на 3%
    "TRAILING_STOP_PERCENT": 1.5,  # Продаем, если цена падает на 1.5% после роста
    "TOP_LIQUID_PAIRS": 5,  # Сколько самых ликвидных пар выбирать
}