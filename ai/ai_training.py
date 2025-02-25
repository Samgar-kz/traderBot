import pandas as pd
import ta
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LogisticRegression
import logging

logging.basicConfig(filename="ai_training_log.txt", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def prepare_data(historical_data):
    """Подготовка данных для обучения AI"""
    df = pd.DataFrame(historical_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    
    # Добавляем технические индикаторы
    df['SMA_50'] = ta.trend.sma_indicator(df['close'], window=50)
    df['SMA_200'] = ta.trend.sma_indicator(df['close'], window=200)
    df['RSI'] = ta.momentum.rsi(df['close'], window=14)
    df['MACD'] = ta.trend.macd(df['close'])
    
    df = df.dropna()
    
    # Логируем размер данных
    logging.info(f"🔍 Размер данных перед обучением: {df.shape}")

    df['Target'] = (df['close'].shift(-1) > df['close']).astype(int)
    df = df.iloc[:-1]  # Убираем последнюю строку, чтобы X и y совпадали
    
    scaler = MinMaxScaler()
    X = scaler.fit_transform(df[['SMA_50', 'SMA_200', 'RSI', 'MACD', 'close']])
    y = df['Target'].values  

    # Выводим примеры данных
    logging.info(f"📊 Пример X (первые 5 строк): {X[:5]}")
    logging.info(f"🎯 Пример y (первые 5 значений): {y[:5]}")

    return X, y, scaler

def train_ai_model(historical_data):
    """Обучение AI модели"""
    X, y, scaler = prepare_data(historical_data)
    
    if len(X) == 0 or len(y) == 0:
        raise ValueError("❌ Недостаточно данных для обучения AI.")
    
    model = LogisticRegression()
    
    logging.info("🚀 Начинаем обучение AI...")
    model.fit(X, y)  # Обучаем модель

    # Проверяем точность модели
    accuracy = model.score(X, y)
    logging.info(f"✅ AI обучение завершено. Точность модели: {accuracy:.4f}")

    return model, scaler