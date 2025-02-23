import requests
import matplotlib.pyplot as plt
from io import BytesIO
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

def send_telegram_message(message):
    """Отправляет текстовое сообщение в Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=data, timeout=5)
    except Exception as e:
        print(f"Ошибка отправки в Telegram: {e}")

def send_price_chart(historical_prices):
    """Генерирует график цен и отправляет в Telegram"""
    try:
        plt.figure(figsize=(10, 5))

        for pair, prices in historical_prices.items():
            if len(prices) > 1:
                plt.plot(prices, label=pair)

        plt.legend()
        plt.title("График цен")
        plt.xlabel("Время")
        plt.ylabel("Цена")
        plt.grid(True)

        buf = BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)

        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        data = {"chat_id": TELEGRAM_CHAT_ID}
        files = {"photo": buf}
        try:
            requests.post(url, data=data, files=files, timeout=10)
        except Exception as e:
            print(f"Ошибка отправки графика в Telegram: {e}")

    except Exception as e:
        print(f"⚠ Ошибка при создании графика: {e}")