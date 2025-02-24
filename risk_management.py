import numpy as np
from config import CONFIG

def calculate_dynamic_risk(historical_data):
    """ Dynamically calculates stop-loss, take-profit, and trailing-stop based on market volatility. """
    
    if len(historical_data) < 50:
        return CONFIG["STOP_LOSS_PERCENT"], CONFIG["SELL_RISE_PERCENT"], CONFIG["TRAILING_STOP_PERCENT"]

    closes = np.array([data[4] for data in historical_data[-50:]])  
    volatility = np.std(closes)  # Standard deviation of closing prices

    stop_loss = max(1, CONFIG["STOP_LOSS_PERCENT"] * (1 + volatility))  
    take_profit = max(1, CONFIG["SELL_RISE_PERCENT"] * (1 + volatility))
    trailing_stop = max(1, CONFIG["TRAILING_STOP_PERCENT"] * (1 + volatility))

    return round(stop_loss, 2), round(take_profit, 2), round(trailing_stop, 2)  # ✅ Always return 3 values
