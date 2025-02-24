import requests
import matplotlib.pyplot as plt
import io
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

# ✅ Отправка графика (изображения) в Telegram
def send_telegram_photo(image_buffer: BytesIO, caption="📊 График цены"):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    data = {"chat_id": TELEGRAM_CHAT_ID, "caption": caption}
    files = {"photo": ("chart.png", image_buffer.getvalue(), "image/png")}
    
    try:
        response = requests.post(url, data=data, files=files, timeout=10)
        response.raise_for_status()  # Проверяем ошибки HTTP
    except Exception as e:
        print(f"Ошибка отправки фото в Telegram: {e}")

def send_price_chart(historical_data):
    plt.figure(figsize=(10, 5))

    for pair, data in historical_data.items():
        prices = [entry[4] for entry in data]  # Берем только цены закрытия

        if len(prices) > 1:
            initial_price = prices[0]  
            try:
                normalized_prices = [(float(p) / float(initial_price) - 1) * 100 for p in prices]
            except ValueError:
                send_telegram_message("⚠ Ошибка в расчете нормализованных цен. Проверь API данные.")
                return


            plt.plot(normalized_prices, label=pair)

    plt.legend()
    plt.xlabel("Время")
    plt.ylabel("Изменение цены (%)")  # Обновили подпись оси Y
    plt.title("📊 30-минутный отчет о рынке (нормализованные цены)")
    plt.yscale("symlog")  # ✅ Логарифмическая шкала

    img_buf = BytesIO()
    plt.savefig(img_buf, format="png")
    img_buf.seek(0)

    send_telegram_photo(img_buf, caption="📊 30-минутный отчет о рынке (нормализованные цены)")
    plt.close()
    """Строит и отправляет график цен для нескольких валютных пар."""
    if not historical_data:
        send_telegram_message("⚠ Ошибка: Нет данных для графика!")
        return

    plt.figure(figsize=(10, 5))

    for pair, data in historical_data.items():
        timestamps = data["timestamps"]
        prices = data["prices"]
        if timestamps and prices:
            plt.plot(timestamps, prices, label=pair)

    plt.xlabel("Время")
    plt.ylabel("Цена")
    plt.legend()
    plt.title("📊 График цен (30-минутный отчет)")

     # ✅ Сохраняем в BytesIO вместо файла
    img_buf = BytesIO()
    plt.savefig(img_buf, format="png")
    img_buf.seek(0)  # Перемещаем указатель в начало

    # ✅ Отправляем график в Telegram
    send_telegram_photo(img_buf, caption="📊 30-минутный отчет о рынке")

    plt.close()  # Закрываем график, чтобы освободить память