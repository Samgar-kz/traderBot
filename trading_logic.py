import asyncio
import time
import traceback
import logging
from binance_api import get_price, get_trade_amount, place_order, get_top_liquid_pairs, get_balance
from ai_trading import train_ai_model, predict_next_move_ai
from risk_management import calculate_dynamic_risk
from telegram_bot import send_telegram_message, send_price_chart
from config import CONFIG

# Настройка логов
logging.basicConfig(filename="trade_log.txt", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Глобальные переменные
is_running = asyncio.Event()
loss_streak = 0  
initial_balance = None  
cycle_count = 0  
historical_prices = {}
active_trades = {}

async def trade_logic():
    global loss_streak, initial_balance, cycle_count, historical_prices  

    try:
        send_telegram_message("🚀 AI Trading Bot запущен!")
        logging.info("AI Bot запущен!")

        # Получаем ликвидные пары
        PAIRS = get_top_liquid_pairs(CONFIG["TOP_LIQUID_PAIRS"])  
        if not PAIRS:
            send_telegram_message("❌ Ошибка: Не удалось получить ликвидные пары!")
            return  

        last_prices = {pair: get_price(pair) for pair in PAIRS}
        historical_data = {pair: [] for pair in PAIRS}
        ai_models = {pair: None for pair in PAIRS}
        scalers = {pair: None for pair in PAIRS}
        historical_prices = {pair: [] for pair in PAIRS}  

        initial_balance = get_balance()
        if initial_balance is None or initial_balance == 0:
            send_telegram_message("❌ Ошибка: Не удалось получить баланс!")
            return  

        is_running.set()

        while is_running.is_set():
            cycle_count += 1  

            for pair in PAIRS:
                try:
                    current_price = get_price(pair)
                    if current_price is None:
                        send_telegram_message(f"⚠ Ошибка: Не удалось получить цену {pair}.")
                        continue

                    historical_prices[pair].append(current_price)
                    if len(historical_prices[pair]) > 100:
                        historical_prices[pair].pop(0)

                    historical_data[pair].append([time.time(), 0, 0, 0, current_price, 0])
                    if len(historical_data[pair]) > 500:
                        historical_data[pair].pop(0)

                    stop_loss, take_profit, trailing_stop = calculate_dynamic_risk(historical_data[pair])

                    # Обучаем AI каждые 100 циклов
                    if cycle_count % 100 == 0:
                        ai_models[pair], scalers[pair] = train_ai_model(historical_data[pair])

                    # AI прогнозирует сделку
                    decision = "hold"
                    if ai_models[pair]:
                        decision = predict_next_move_ai(ai_models[pair], historical_data[pair][-1:], scalers[pair])

                    # Покупка
                    if decision == "buy":
                        amount = get_trade_amount(pair)
                        if amount > 0:
                            send_telegram_message(f"🤖 AI: Покупаем {pair}, SL: {stop_loss}%, TP: {take_profit}%, TS: {trailing_stop}%")
                            logging.info(f"BUY: {pair}, Price: {current_price}")
                            entry_price = place_order(pair, "buy", amount)
                            if entry_price:
                                active_trades[pair] = {
                                    "entry": entry_price,
                                    "stop_loss": entry_price * (1 - stop_loss / 100),
                                    "take_profit": entry_price * (1 + take_profit / 100),
                                    "trailing_stop": trailing_stop
                                }
                                loss_streak = 0  

                    # Продажа
                    elif decision == "sell":
                        amount = get_trade_amount(pair)
                        if amount > 0:
                            send_telegram_message(f"🤖 AI: Продаем {pair}, предсказание падения")
                            logging.info(f"SELL: {pair}, Price: {current_price}")
                            result_price = place_order(pair, "sell", amount)
                            if result_price and result_price < last_prices[pair]:  
                                loss_streak += 1  

                    # Проверка трейлинг-стопа
                    if pair in active_trades and "entry" in active_trades[pair]:
                        entry_price = active_trades[pair]["entry"]
                        if current_price > active_trades[pair]["take_profit"]:
                            send_telegram_message(f"🚀 {pair} достиг Take Profit! Фиксируем прибыль!")
                            place_order(pair, "sell", amount)
                            del active_trades[pair]
                        elif current_price < active_trades[pair]["stop_loss"]:
                            send_telegram_message(f"⛔ {pair} упал ниже стоп-лосса! Закрываем сделку!")
                            place_order(pair, "sell", amount)
                            del active_trades[pair]

                    last_prices[pair] = current_price  

                except Exception as trade_error:
                    error_trace = traceback.format_exc()
                    send_telegram_message(f"⚠ Ошибка в торговле {pair}: {trade_error}\n{error_trace}")
                    logging.error(f"Ошибка в торговле {pair}: {trade_error}\n{error_trace}")

            # Отправляем график в Telegram каждые 10 минут
            if cycle_count % 10 == 0:
                await send_price_chart(historical_prices)

            await asyncio.sleep(60)  
            await check_safety_mode()  

    except Exception as e:
        error_trace = traceback.format_exc()
        send_telegram_message(f"❌ Критическая ошибка: {e}\n{error_trace}")
        logging.critical(f"Критическая ошибка: {e}\n{error_trace}")
        is_running.clear()

async def check_safety_mode():
    global loss_streak, initial_balance

    try:
        current_balance = get_balance()
        if current_balance is None or current_balance == 0:
            send_telegram_message("⚠ Ошибка: Не удалось получить баланс! Останавливаем бота.")
            logging.warning("Ошибка получения баланса. Бот остановлен.")
            is_running.clear()
            return

        if current_balance < initial_balance * (1 - CONFIG["SAFETY_STOP_LOSS"] / 100):
            send_telegram_message("⚠ БОТ ОСТАНОВЛЕН! Потеряно более 20% депозита.")
            logging.warning("Бот остановлен: убыток более 20% депозита.")
            is_running.clear()  

        if loss_streak >= CONFIG["LOSS_STREAK_LIMIT"]:
            send_telegram_message("⚠ БОТ ОСТАНОВЛЕН! 3 убыточные сделки подряд.")
            logging.warning("Бот остановлен: 3 убыточные сделки подряд.")
            is_running.clear()  
            
    except Exception as safety_error:
        error_trace = traceback.format_exc()
        send_telegram_message(f"⚠ Ошибка в check_safety_mode: {safety_error}\n{error_trace}")
        logging.error(f"Ошибка в check_safety_mode: {safety_error}\n{error_trace}")

async def stop_trading():
    """ Останавливаем торговлю и завершаем сделки """
    is_running.clear()
    send_telegram_message("🛑 Торговля остановлена!")