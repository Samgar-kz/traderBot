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

# ✅ Функция проверки и форматирования данных
def validate_historical_data(historical_data):
    """Фильтрует и форматирует данные, удаляя ошибки"""
    valid_data = {}

    for pair, data in historical_data.items():
        if not isinstance(data, list) or len(data) < 2:
            print(f"⚠ Ошибка: Недостаточно данных для {pair}")
            continue
        
        try:
            timestamps = [float(entry[0]) for entry in data if isinstance(entry[0], (int, float))]
            prices = [float(entry[4]) for entry in data if isinstance(entry[4], (int, float, str)) and entry[4].replace('.', '', 1).isdigit()]
            
            if len(timestamps) != len(prices):
                print(f"⚠ Ошибка: Несовпадение длин данных в {pair} ({len(timestamps)} vs {len(prices)})")
                continue

            valid_data[pair] = {"timestamps": timestamps, "prices": prices}
        
        except (ValueError, IndexError, KeyError) as e:
            print(f"⚠ Ошибка обработки данных для {pair}: {e}")
    
    return valid_data if valid_data else None

async def send_price_chart(historical_data):
    """Строит и отправляет график цен для нескольких валютных пар."""
    
    if not historical_data:
        send_telegram_message("⚠ Ошибка: Нет данных для графика!")
        return
    
    plt.figure(figsize=(10, 5))

    for pair, data in historical_data.items():
        try:
            if not isinstance(data, dict) or "timestamps" not in data or "prices" not in data:
                print(f"⚠ Ошибка структуры данных {pair}")
                continue

            timestamps = data["timestamps"]
            prices = data["prices"]

            if len(prices) > 1:

                # ✅ Нормализуем цены
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