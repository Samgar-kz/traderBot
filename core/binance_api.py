# binance_api.py - Взаимодействие с Binance API
import ccxt
import logging
from config import API_KEY, API_SECRET
from bot.telegram_bot import send_telegram_message

# ✅ Настройка Binance API
exchange = ccxt.binance({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True
})

# ✅ Получение баланса

def get_balance(asset='USDT'):
    """Получает баланс указанного актива"""
    try:
        balance = exchange.fetch_balance()
        return round(balance.get(asset, {}).get('free', 0), 2)
    except Exception as e:
        logging.error(f"Ошибка получения баланса Binance: {e}")
        return 0

# ✅ Получение текущей цены

def get_price(symbol):
    """Получает текущую цену символа."""
    try:
        ticker = exchange.fetch_ticker(symbol)
        return ticker['last']
    except Exception as e:
        logging.error(f"Ошибка получения цены {symbol}: {e}")
        return None

# ✅ Расчет суммы сделки

def get_trade_amount(symbol, balance_percent=5):
    """Вычисляет размер сделки (процент от баланса)."""
    balance = get_balance()
    if balance == 0:
        return 0

    price = get_price(symbol)
    if price is None:
        return 0

    trade_value = (balance * balance_percent) / 100
    return round(trade_value / price, 6)

# ✅ Размещение ордеров

def place_order(symbol, order_type, amount):
    """Размещает ордер (покупка или продажа)"""
    if amount <= 0:
        return None

    try:
        if order_type == "buy":
            order = exchange.create_market_buy_order(symbol, amount)
        elif order_type == "sell":
            order = exchange.create_market_sell_order(symbol, amount)
        else:
            raise ValueError("Неверный тип ордера")

        price = order['price']
        send_telegram_message(f"✅ {order_type.upper()} {symbol} по цене: {price}")
        return price

    except Exception as e:
        logging.error(f"Ошибка при {order_type} {symbol}: {e}")
        send_telegram_message(f"⚠ Ошибка при {order_type} {symbol}: {e}")
        return None

# ✅ Получение топ-ликвидных пар

def get_top_liquid_pairs(limit=5):
    """Получает топ ликвидных пар, вычисляя изменение цены вручную."""
    try:
        tickers = exchange.fetch_tickers()
        
        volumes = {}
        for symbol, data in tickers.items():
            if '/USDT' in symbol and data['quoteVolume'] > 0 and data['open'] is not None and data['last'] is not None:
                change = ((data['last'] - data['open']) / data['open']) * 100
                volumes[symbol] = (data['quoteVolume'], change)

        # ✅ Фильтруем только растущие пары
        growing_pairs = {k: v for k, v in volumes.items() if v[1] > 0}
        
        # ✅ Сортируем по ликвидности
        sorted_pairs = sorted(growing_pairs.items(), key=lambda x: x[1][0], reverse=True)

        # ✅ Берем топ-N пар
        top_pairs = [pair[0] for pair in sorted_pairs[:limit]]

        return top_pairs

    except Exception as e:
        logging.error(f"Ошибка получения ликвидных пар: {e}")
        send_telegram_message(f"⚠ Ошибка получения ликвидных пар: {e}")
        return []


# ✅ Получение исторических данных

def get_historical_data(symbol, timeframe='1m', limit=100):
    """Загружает исторические данные в формате OHLCV"""
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        
        if not ohlcv or len(ohlcv) < 2:
            logging.error(f"⚠ Недостаточно данных для {symbol}. Загружено: {len(ohlcv)} записей.")
            return []
        
        return ohlcv  # ✅ Данные остаются в формате OHLCV
    
    except Exception as e:
        logging.error(f"Ошибка загрузки истории {symbol}: {e}")
        return []