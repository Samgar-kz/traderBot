import ccxt
from config import API_KEY, API_SECRET
from telegram_bot import send_telegram_message

# ✅ Подключение к Binance API
exchange = ccxt.binance({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True
})

def get_balance():
    """Получает баланс USDT без отправки сообщений"""
    try:
        balance = exchange.fetch_balance()
        return round(balance.get('USDT', {}).get('free', 0), 2)
    except Exception as e:
        print(f"❌ Ошибка получения баланса Binance: {e}")
        return 0

# ✅ Получение текущей цены криптовалюты
def get_price(symbol):
    try:
        ticker = exchange.fetch_ticker(symbol)
        return ticker['last']
    except Exception as e:
        send_telegram_message(f"⚠ Ошибка получения цены {symbol}: {e}")
        return None

# ✅ Получение суммы сделки (процент от баланса)
def get_trade_amount(symbol, balance_percent=5):
    balance = get_balance()
    if balance == 0:
        return 0

    price = get_price(symbol)
    if price is None:
        return 0

    trade_value = (balance * balance_percent) / 100
    return round(trade_value / price, 6)

# ✅ Размещение ордеров (покупка/продажа)
def place_order(symbol, order_type, amount):
    if amount <= 0:
        return None

    try:
        if order_type == "buy":
            order = exchange.create_market_buy_order(symbol, amount)
        elif order_type == "sell":
            order = exchange.create_market_sell_order(symbol, amount)

        price = order['price']
        send_telegram_message(f"✅ {order_type.upper()} {symbol} по цене: {price}")
        return price

    except Exception as e:
        send_telegram_message(f"⚠ Ошибка при {order_type} {symbol}: {e}")
        return None

# ✅ Получение топ-ликвидных пар с USDT
def get_top_liquid_pairs(limit=5):
    try:
        tickers = exchange.fetch_tickers()
        volumes = {symbol: tickers[symbol]['quoteVolume'] for symbol in tickers if '/USDT' in symbol}
        sorted_pairs = sorted(volumes.items(), key=lambda x: x[1], reverse=True)
        return [pair[0] for pair in sorted_pairs[:limit]]
    except Exception as e:
        send_telegram_message(f"⚠ Ошибка получения ликвидных пар: {e}")
        return []

def get_historical_data(symbol, timeframe='1m', limit=100):
    """Загружает исторические данные с Binance"""
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        historical_data = [
            [candle[0], candle[1], candle[2], candle[3], candle[4], candle[5]] for candle in ohlcv
        ]
        return historical_data
    except Exception as e:
        print(f"❌ Ошибка загрузки истории {symbol}: {e}")
        return []