import numpy as np
from config import CONFIG

def calculate_dynamic_risk(historical_data):
    """ Динамический расчет стоп-лосса и тейк-профита на основе волатильности рынка. """
    if len(historical_data) < 50:
        return CONFIG["STOP_LOSS_PERCENT"], CONFIG["SELL_RISE_PERCENT"]
    
    closes = np.array([data[4] for data in historical_data[-50:]])  
    volatility = np.std(closes)  
    
    stop_loss = max(1, CONFIG["STOP_LOSS_PERCENT"] * (1 + volatility))  
    take_profit = max(1, CONFIG["SELL_RISE_PERCENT"] * (1 + volatility))

    return round(stop_loss, 2), round(take_profit, 2)