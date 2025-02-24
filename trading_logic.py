import asyncio
import time
import traceback
import logging
from binance_api import get_price, get_trade_amount, place_order, get_top_liquid_pairs, get_balance, get_historical_data
from ai_trading import train_ai_model, predict_next_move_ai
from risk_management import calculate_dynamic_risk
from telegram_bot import send_telegram_message
from config import CONFIG

logging.basicConfig(filename="trade_log.txt", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ✅ Глобальные переменные
is_running = asyncio.Event()
loss_streak = 0  
initial_balance = None  
previous_balance = None  
last_trade_time = None  
last_notification_time = None  
cycle_count = 0  
ai_models = {}  
scalers = {}  
historical_data = {}  
PAIRS = []  # Глобальный список пар

async def trade_logic():
    global loss_streak, initial_balance, previous_balance, last_trade_time, last_notification_time
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

        # ✅ Получаем **10-15 самых ликвидных пар**
        PAIRS = get_top_liquid_pairs(15)
        if not PAIRS:
            send_telegram_message("❌ Ошибка: Нет доступных пар для торговли!")
            is_running.clear()
            return  

        # ✅ Загружаем **1000 свечей** для каждой пары
        historical_data = {pair: get_historical_data(pair, '1m', 1000) for pair in PAIRS}

        # ✅ Обучаем AI для каждой пары
        for pair in PAIRS:
            if len(historical_data[pair]) >= 50:
                send_telegram_message(f"🧠 AI обучается на 1000 свечей {pair}!")
                ai_models[pair], scalers[pair] = train_ai_model(historical_data[pair])
            else:
                send_telegram_message(f"⚠ Недостаточно данных для AI {pair}.")

        send_telegram_message("✅ AI готов к торговле! Начинаем реальный трейдинг.")

        last_trade_time = time.time()
        last_notification_time = time.time()

        while is_running.is_set():
            cycle_count += 1  
            trade_executed = False  

            # 🔄 **Обновляем список пар каждые 30 минут**
            if cycle_count % 30 == 0:
                PAIRS = get_top_liquid_pairs(15)
                send_telegram_message("🔄 Обновлены топ-ликвидные пары!")

            for pair in PAIRS:
                try:
                    current_price = get_price(pair)
                    if current_price is None:
                        continue

                    # ✅ Обновляем исторические данные
                    historical_data[pair].append([time.time(), 0, 0, 0, current_price, 0])
                    if len(historical_data[pair]) > 1000:
                        historical_data[pair].pop(0)

                    stop_loss, take_profit, trailing_stop = calculate_dynamic_risk(pair)

                    # ✅ AI предсказывает сделку, если модель обучена
                    if ai_models.get(pair) is not None and scalers.get(pair) is not None:
                        decision = predict_next_move_ai(ai_models[pair], historical_data[pair][-1:], scalers[pair])
                    else:
                        decision = "hold"

                    # ✅ AI готовится к сделке
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

            # ✅ **AI адаптирует стратегию, если нет сделок > 2 часов**
            if (time.time() - last_trade_time) > 7200:
                CONFIG["STOP_LOSS_PERCENT"] *= 0.9  
                CONFIG["SELL_RISE_PERCENT"] *= 0.95  
                send_telegram_message("⚡ AI адаптирует стратегию! Чуть больше риска.")

            # ✅ **Отправляем уведомление, если прошло 3 часа без сделок**
            if not trade_executed and (time.time() - last_trade_time) > 10800:
                send_telegram_message("⚠ Уже 3 часа без сделок. Возможно, рынок во флэте.")

            await asyncio.sleep(60)  
            await check_safety_mode()  

    except Exception as e:
        error_trace = traceback.format_exc()
        send_telegram_message(f"❌ Критическая ошибка: {e}\n{error_trace}")
        logging.critical(f"Критическая ошибка: {e}\n{error_trace}")
        is_running.clear()

async def update_balance():
    global previous_balance

    current_balance = get_balance()
    if current_balance != previous_balance:
        send_telegram_message(f"💰 Новый баланс: {current_balance:.2f} USDT после сделки.")
        previous_balance = current_balance  

async def check_safety_mode():
    global loss_streak, initial_balance

    try:
        current_balance = get_balance()
        if current_balance < initial_balance * (1 - CONFIG["SAFETY_STOP_LOSS"] / 100):
            send_telegram_message("⚠ БОТ ОСТАНОВЛЕН! Потеряно более 20% депозита.")
            is_running.clear()

        if loss_streak >= CONFIG["LOSS_STREAK_LIMIT"]:
            send_telegram_message("⚠ БОТ ОСТАНОВЛЕН! 3 убыточные сделки подряд.")
            is_running.clear()

    except Exception as e:
        send_telegram_message(f"⚠ Ошибка в check_safety_mode: {e}")

async def stop_trading():
    if not is_running.is_set():
        send_telegram_message("⚠ Бот уже остановлен!")
        return

    send_telegram_message("🛑 Остановка бота... Завершаю сделки.")
    is_running.clear()
    await asyncio.sleep(3)
    send_telegram_message("🛑 Торговля полностью остановлена!")
