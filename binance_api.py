import ccxt
from config import API_KEY, API_SECRET

exchange = ccxt.binance({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True
})

trade_history = {}  # Словарь для хранения данных о входах и профите

def get_balance():
    try:
        balance = exchange.fetch_balance()
        return balance.get('USDT', {}).get('free', 0)
    except Exception as e:
        print(f"Ошибка получения баланса: {e}")
        return 0

def get_price(symbol):
    try:
        ticker = exchange.fetch_ticker(symbol)
        return ticker['last']
    except Exception as e:
        print(f"Ошибка получения цены {symbol}: {e}")
        return None

def get_trade_amount(symbol, balance_percent):
    balance = get_balance()
    if balance == 0:
        return 0
    price = get_price(symbol)
    if price is None:
        return 0
    trade_value = (balance * balance_percent) / 100
    return round(trade_value / price, 6)

def place_order(symbol, order_type, amount):
    if amount <= 0:
        return None

    try:
        if order_type == "buy":
            order = exchange.create_market_buy_order(symbol, amount)
        elif order_type == "sell":
            order = exchange.create_market_sell_order(symbol, amount)

        price = order['price']
        print(f"✅ {order_type.upper()} {symbol}: {price}")

        # Фиксируем покупку или продажу
        if order_type == "buy":
            trade_history[symbol] = {"entry": price, "profit": 0}
        elif order_type == "sell":
            if symbol in trade_history and "entry" in trade_history[symbol]:
                entry_price = trade_history[symbol]["entry"]
                profit = (price - entry_price) / entry_price * 100
                trade_history[symbol]["profit"] = profit
                print(f"📊 {symbol} продан с прибылью: {profit:.2f}%")

        return price
    except Exception as e:
        print(f"⚠ Ошибка при {order_type} {symbol}: {e}")
        return None
    
def get_top_liquid_pairs(limit=5):
    """Получает топ ликвидные пары USDT по объему торгов"""
    try:
        tickers = exchange.fetch_tickers()
        volumes = {symbol: tickers[symbol]['quoteVolume'] for symbol in tickers if '/USDT' in symbol}
        sorted_pairs = sorted(volumes.items(), key=lambda x: x[1], reverse=True)
        return [pair[0] for pair in sorted_pairs[:limit]]
    except Exception as e:
        print(f"Ошибка получения ликвидных пар: {e}")
        return []