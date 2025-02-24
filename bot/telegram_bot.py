import requests
import matplotlib.pyplot as plt
from io import BytesIO
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

# ✅ Отправка текстового сообщения в Telegram
def send_telegram_message(message):
    """Отправляет текстовое сообщение в Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        response = requests.post(url, data=data, timeout=5)
        response.raise_for_status()
    except Exception as e:
        print(f"Ошибка отправки в Telegram: {e}")

# ✅ Отправка фото в Telegram
def send_telegram_photo(image_buffer: BytesIO, caption="📊 График цены"):
    """Отправляет изображение в Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    data = {"chat_id": TELEGRAM_CHAT_ID, "caption": caption}
    files = {"photo": ("chart.png", image_buffer.getvalue(), "image/png")}
    
    try:
        response = requests.post(url, data=data, files=files, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"Ошибка отправки фото в Telegram: {e}")

# ✅ Отправка графика с историей цен
def send_price_chart(historical_data):
    """Строит и отправляет график цен для нескольких валютных пар."""
    
    if not historical_data:
        send_telegram_message("⚠ Ошибка: Нет данных для графика!")
        return

    plt.figure(figsize=(10, 5))

    for pair, data in historical_data.items():
        try:
            timestamps = [entry[0] for entry in data]  # Временные метки
            prices = [entry[4] for entry in data]  # Закрытие цены
            
            if len(prices) > 1:
                initial_price = float(prices[0])  
                normalized_prices = [(float(p) / initial_price - 1) * 100 for p in prices]
                plt.plot(timestamps, normalized_prices, label=pair)
        
        except (ValueError, IndexError, KeyError) as e:
            print(f"⚠ Ошибка обработки данных для {pair}: {e}")
            continue

    plt.legend()
    plt.xlabel("Время")
    plt.ylabel("Изменение цены (%)")
    plt.title("📊 30-минутный отчет о рынке (нормализованные цены)")
    plt.yscale("symlog")  # ✅ Логарифмическая шкала

    # ✅ Сохраняем изображение в BytesIO и отправляем
    img_buf = BytesIO()
    plt.savefig(img_buf, format="png")
    img_buf.seek(0)

    send_telegram_photo(img_buf, caption="📊 30-минутный отчет о рынке")
    plt.close()