import asyncio
from binance_api import get_price, get_trade_amount, place_order, get_top_liquid_pairs, trade_history
from telegram_bot import send_telegram_message
from config import CONFIG

is_running = False  

async def trade_logic():
    global is_running  
    send_telegram_message("🚀 Бот запущен! Анализ рынка начался.")

    PAIRS = get_top_liquid_pairs(CONFIG["TOP_LIQUID_PAIRS"])  # Теперь выбираем пары автоматически!
    
    if not PAIRS:
        send_telegram_message("❌ Ошибка: не удалось загрузить ликвидные пары.")
        return  # Останавливаем, если не получилось получить пары
    
    last_prices = {pair: get_price(pair) for pair in PAIRS}
    highest_prices = last_prices.copy()
    entry_prices = {pair: None for pair in PAIRS}

    while is_running:
        try:
            for pair in PAIRS:
                current_price = get_price(pair)
                if current_price is None or pair not in last_prices:
                    continue

                price_change = (current_price - last_prices[pair]) / last_prices[pair] * 100

                # Динамический стоп-лосс и тейк-профит на основе истории
                stop_loss_percent = CONFIG["STOP_LOSS_PERCENT"]
                take_profit_percent = CONFIG["SELL_RISE_PERCENT"]

                if pair in trade_history and "profit" in trade_history[pair]:
                    last_profit = trade_history[pair]["profit"]

                    # Если последняя сделка была успешной, увеличиваем риск
                    if last_profit > 1:
                        stop_loss_percent *= 0.8  # Уменьшаем стоп-лосс
                        take_profit_percent *= 1.2  # Увеличиваем тейк-профит
                    # Если последняя сделка была убыточной, уменьшаем риск
                    elif last_profit < -1:
                        stop_loss_percent *= 1.2
                        take_profit_percent *= 0.8

                # Покупка при падении
                if price_change <= -CONFIG["BUY_DROP_PERCENT"]:
                    amount = get_trade_amount(pair, CONFIG["BALANCE_PERCENT"])
                    if amount > 0:
                        send_telegram_message(f"📉 {pair} упал на {price_change:.2f}%. Покупаю {amount}...")
                        place_order(pair, "buy", amount)
                        entry_prices[pair] = current_price
                        highest_prices[pair] = current_price

                # Продажа при росте
                elif price_change >= take_profit_percent:
                    amount = get_trade_amount(pair, CONFIG["BALANCE_PERCENT"])
                    if amount > 0:
                        send_telegram_message(f"📈 {pair} вырос на {price_change:.2f}%. Продаю {amount}...")
                        place_order(pair, "sell", amount)
                        entry_prices[pair] = None

                # Трейлинг-стоп
                elif (highest_prices[pair] - current_price) / highest_prices[pair] * 100 >= CONFIG["TRAILING_STOP_PERCENT"]:
                    amount = get_trade_amount(pair, CONFIG["BALANCE_PERCENT"])
                    if amount > 0:
                        send_telegram_message(f"🔻 {pair} достиг максимума и упал на {CONFIG['TRAILING_STOP_PERCENT']}%. Продаю {amount}...")
                        place_order(pair, "sell", amount)
                        entry_prices[pair] = None

                # Стоп-лосс
                elif entry_prices[pair] and (current_price - entry_prices[pair]) / entry_prices[pair] * 100 <= -stop_loss_percent:
                    amount = get_trade_amount(pair, CONFIG["BALANCE_PERCENT"])
                    if amount > 0:
                        send_telegram_message(f"⛔ {pair} упал ниже стоп-лосса ({stop_loss_percent}%). Закрываю позицию...")
                        place_order(pair, "sell", amount)
                        entry_prices[pair] = None

                # Обновляем максимальную цену
                if current_price > highest_prices.get(pair, 0):
                    highest_prices[pair] = current_price

                # Обновляем последнюю цену
                last_prices[pair] = current_price

            await asyncio.sleep(60)

        except Exception as e:
            print(f"⚠ Ошибка: {e}")
            send_telegram_message(f"❌ Ошибка в работе бота: {e}")
            await asyncio.sleep(30)