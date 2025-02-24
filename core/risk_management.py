import numpy as np
import logging
from config import CONFIG

# ✅ Настроим логирование (чтобы видеть параметры риска в логах)
logging.basicConfig(filename="trade_log.txt", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def calculate_dynamic_risk(historical_data):
    """ Динамический расчет стоп-лосса, тейк-профита и трейлинг-стопа на основе волатильности. """

    if len(historical_data) < 50:
        logging.warning(f"⚠ Недостаточно данных для динамического риска. Используем стандартные значения.")
        return CONFIG["STOP_LOSS_PERCENT"], CONFIG["SELL_RISE_PERCENT"], CONFIG["TRAILING_STOP_PERCENT"]

    try:
        closes = np.array([data[4] for data in historical_data[-50:]])  
        volatility = np.std(closes)  # Стандартное отклонение цен закрытия

        # ✅ Динамическое изменение рисков в зависимости от волатильности
        risk_factor = 1 + (volatility / np.mean(closes))  # Волатильность относительно средней цены
        
        stop_loss = max(1, CONFIG["STOP_LOSS_PERCENT"] * risk_factor)
        take_profit = max(1, CONFIG["SELL_RISE_PERCENT"] * risk_factor)
        trailing_stop = max(1, CONFIG["TRAILING_STOP_PERCENT"] * risk_factor)

        logging.info(f"📊 Расчет рисков для текущей волатильности ({volatility:.5f}): SL={stop_loss:.2f}%, TP={take_profit:.2f}%, TS={trailing_stop:.2f}%")

        return round(stop_loss, 2), round(take_profit, 2), round(trailing_stop, 2)

    except ZeroDivisionError:
        logging.error("❌ Ошибка: Деление на ноль при расчете волатильности. Используем стандартные параметры риска.")
        return CONFIG["STOP_LOSS_PERCENT"], CONFIG["SELL_RISE_PERCENT"], CONFIG["TRAILING_STOP_PERCENT"]

    except Exception as e:
        logging.error(f"❌ Ошибка в calculate_dynamic_risk: {e}")
        return CONFIG["STOP_LOSS_PERCENT"], CONFIG["SELL_RISE_PERCENT"], CONFIG["TRAILING_STOP_PERCENT"]