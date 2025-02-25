import asyncio
import time
import traceback
import logging
from core.binance_api import get_price, get_trade_amount, place_order, get_top_liquid_pairs, get_balance, get_historical_data
from ai.ai_training import train_ai_model
from ai.ai_prediction import predict_next_move_ai
from core.risk_management import calculate_dynamic_risk
from bot.telegram_bot import send_telegram_message, send_price_chart
from config import CONFIG

logging.basicConfig(filename="trade_log.txt", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ✅ Глобальные переменные
is_running = asyncio.Event()
loss_streak = 0  
initial_balance = None  
previous_balance = None  
last_trade_time = None  
last_report_time = None  
cycle_count = 0  
ai_models = {}  
scalers = {}  
historical_data = {}  
PAIRS = []

async def trade_logic():
    """Основная торговая логика"""
    global loss_streak, initial_balance, previous_balance, last_trade_time, last_report_time
    global cycle_count, ai_models, scalers, historical_data, PAIRS  

    if is_running.is_set():
        send_telegram_message("⚠ Бот уже запущен!")
        return

    try:
        send_telegram_message("🚀 AI Trading Bot запущен! Загружаем исторические данные...")
        is_running.set()

        # ✅ Проверяем баланс
        initial_balance = get_balance()
        if initial_balance < 10:
            send_telegram_message(f"⚠ Недостаточно USDT для торговли (Баланс: {initial_balance:.2f} USDT). Минимум $10.")
            is_running.clear()
            return  

        previous_balance = initial_balance
        send_telegram_message(f"💰 Баланс: {initial_balance:.2f} USDT. Готов к торговле!")

        # ✅ Получаем топ-ликвидные пары
        PAIRS = get_top_liquid_pairs(10)
        if not PAIRS:
            send_telegram_message("❌ Ошибка: Нет доступных пар для торговли!")
            is_running.clear()
            return  

        # ✅ Загружаем исторические данные и обучаем AI
        for pair in PAIRS:
            if pair not in historical_data:  # Загружаем только если нет данных
                historical_data[pair] = get_historical_data(pair, '1m', 1000)
                if len(historical_data[pair]) >= 50:
                    send_telegram_message(f"🧠 AI обучается на 1000 свечей {pair}...")
                    ai_models[pair], scalers[pair] = train_ai_model(historical_data[pair])
                else:
                    send_telegram_message(f"⚠ Недостаточно данных для AI {pair}.")

        send_telegram_message("✅ AI готов к торговле! Начинаем реальный трейдинг.")
        last_trade_time = time.time()
        last_report_time = time.time()

        while is_running.is_set():
            cycle_count += 1  
            trade_executed = False  

            X_test = scalers['BTC/USDT'].transform([[50000, 50100, 49900, 50050, 50000]])  
            prediction = ai_models['BTC/USDT'].predict(X_test)  
            send_telegram_message(f"✅ AI тестовое предсказание: {prediction}")

            # ✅ Отправляем отчет раз в 30 минут
            if (time.time() - last_report_time) >= 1800:
                await send_market_report()
                last_report_time = time.time()

            # ✅ Обновляем топ-ликвидные пары раз в 10 минут
            if cycle_count % 10 == 0:
                new_pairs = get_top_liquid_pairs(10)
                
                # ✅ Если список изменился — обновляем
                if set(new_pairs) != set(PAIRS):
                    send_telegram_message(f"🔄 Обновлен список ТОП пар: {new_pairs}")

                    # ✅ Удаляем старые пары, которых больше нет в топе
                    for old_pair in list(historical_data.keys()):
                        if old_pair not in new_pairs:
                            del historical_data[old_pair]
                            del ai_models[old_pair]
                            del scalers[old_pair]

                    PAIRS = new_pairs

                    # ✅ Загружаем исторические данные только для новых пар
                    for pair in PAIRS:
                        if pair not in historical_data:
                            historical_data[pair] = get_historical_data(pair, '1m', 1000)
                            if len(historical_data[pair]) >= 50:
                                send_telegram_message(f"🧠 AI обучается на 1000 свечей {pair}...")
                                ai_models[pair], scalers[pair] = train_ai_model(historical_data[pair])
                            else:
                                send_telegram_message(f"⚠ Недостаточно данных для AI {pair}.")

            for pair in PAIRS:
                try:
                    current_price = get_price(pair)
                    if current_price is None:
                        continue

                    # ✅ Загружаем последние 3 свечи
                    new_candles = get_historical_data(pair, '1m', 3)  # Берем последние 3 свечи

                    # ✅ Добавляем только новые свечи (избегаем дубликатов)
                    for candle in new_candles:
                        if historical_data[pair] and candle[0] <= historical_data[pair][-1][0]:
                            continue  # Пропускаем, если таймстемп уже есть

                        historical_data[pair].append(candle)  # Добавляем новую свечу

                    # ✅ Удаляем старые данные, если больше 1000
                    if len(historical_data[pair]) > 1000:
                        historical_data[pair] = historical_data[pair][-1000:]  # Оставляем последние 1000


                    # ✅ Динамический риск
                    stop_loss, take_profit, trailing_stop = calculate_dynamic_risk(historical_data[pair])

                    send_telegram_message(f"📊 AI данные для {pair}: {historical_data[pair][-5:]}")  

                    # ✅ AI предсказывает сделку
                    if ai_models.get(pair) is not None and scalers.get(pair) is not None:
                        decision = predict_next_move_ai(ai_models[pair], historical_data[pair][-1:], scalers[pair])
                    else:
                        decision = "hold"

                    send_telegram_message(f"🤖 AI решение по {pair}: {decision}")

                    # ✅ AI сообщает статус
                    if decision == "buy":
                        send_telegram_message(f"📉 {pair} падает! AI ждет лучшую цену для покупки...")
                    elif decision == "sell":
                        send_telegram_message(f"📈 {pair} растет! AI готовится к продаже...")

                    # ✅ AI покупает
                    if decision == "buy":
                        amount = get_trade_amount(pair)
                        if amount > 0:
                            send_telegram_message(f"🤖 AI: Покупаем {pair}, SL: {stop_loss}%, TP: {take_profit}%, TS: {trailing_stop}%")
                            place_order(pair, "buy", amount)
                            await update_balance()
                            last_trade_time = time.time()
                            trade_executed = True

                    # ✅ AI продает
                    elif decision == "sell":
                        amount = get_trade_amount(pair)
                        if amount > 0:
                            send_telegram_message(f"🤖 AI: Продаем {pair}")
                            place_order(pair, "sell", amount)
                            await update_balance()
                            last_trade_time = time.time()
                            trade_executed = True

                except Exception as trade_error:
                    error_trace = traceback.format_exc()
                    send_telegram_message(f"⚠ Ошибка в торговле {pair}: {trade_error}\n{error_trace}")
                    logging.error(f"Ошибка в торговле {pair}: {trade_error}\n{error_trace}")

            await asyncio.sleep(60)
            await check_safety_mode()

    except Exception as e:
        error_trace = traceback.format_exc()
        send_telegram_message(f"❌ Критическая ошибка: {e}\n{error_trace}")
        logging.critical(f"Критическая ошибка: {e}\n{error_trace}")
        is_running.clear()

async def send_market_report():
    send_telegram_message("📊 30-минутный отчет о рынке...")

    if not historical_data or all(len(data) == 0 for data in historical_data.values()):
        send_telegram_message("⚠ Ошибка: Нет данных для графика! Исторические данные не загружены.")
        return  

    formatted_data = format_historical_data(historical_data)
    await send_price_chart(formatted_data)  # Отправляем только если есть данные

def format_historical_data(historical_data):
    formatted_data = {}

    for pair, data in historical_data.items():

        if not isinstance(data, list) or len(data) < 2:
            print(f"⚠ Ошибка структуры данных {pair} (ожидался список OHLCV)")
            continue

        try:
            timestamps = [int(candle[0]) for candle in data]  # Берём timestamp
            prices = [float(candle[4]) for candle in data]  # Берём close price

            formatted_data[pair] = {"timestamps": timestamps, "prices": prices}
        
        except (IndexError, ValueError) as e:
            print(f"⚠ Ошибка обработки данных {pair}: {e}")
            continue

    if not formatted_data:
        print("❌ Все данные отфильтрованы! Нет данных для графика.")

    return formatted_data

async def update_balance():
    """Обновляет баланс после сделки."""
    global previous_balance
    current_balance = get_balance()
    if current_balance != previous_balance:
        send_telegram_message(f"💰 Новый баланс: {current_balance:.2f} USDT после сделки.")
        previous_balance = current_balance  

async def check_safety_mode():
    """Останавливает бота при больших потерях."""
    global loss_streak, initial_balance
    try:
        current_balance = get_balance()
        if current_balance < initial_balance * (1 - CONFIG["SAFETY_STOP_LOSS"] / 100):
            send_telegram_message("⚠ БОТ ОСТАНОВЛЕН! Потеряно более 20% депозита.")
            is_running.clear()
    except Exception as e:
        send_telegram_message(f"⚠ Ошибка в check_safety_mode: {e}")

async def stop_trading():
    """Останавливает торговлю."""
    if not is_running.is_set():
        send_telegram_message("⚠ Бот уже остановлен!")
        return
    send_telegram_message("🛑 Остановка бота... Завершаю сделки.")
    is_running.clear()
    await asyncio.sleep(3)
    send_telegram_message("🛑 Торговля полностью остановлена!")