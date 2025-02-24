# ai_training.py - Обучение AI модели
import pandas as pd
import ta
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LogisticRegression

def prepare_data(historical_data):
    """Подготовка данных для обучения AI"""
    df = pd.DataFrame(historical_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    
    # Добавляем технические индикаторы
    df['SMA_50'] = ta.trend.sma_indicator(df['close'], window=50)
    df['SMA_200'] = ta.trend.sma_indicator(df['close'], window=200)
    df['RSI'] = ta.momentum.rsi(df['close'], window=14)
    df['MACD'] = ta.trend.macd(df['close'])
    
    df = df.dropna()
    df['Target'] = (df['close'].shift(-1) > df['close']).astype(int)
    df = df.iloc[:-1]  # Убираем последнюю строку, чтобы X и y совпадали
    
    scaler = MinMaxScaler()
    X = scaler.fit_transform(df[['SMA_50', 'SMA_200', 'RSI', 'MACD', 'close']])
    y = df['Target'].values  
    
    return X, y, scaler

def train_ai_model(historical_data):
    """Обучение AI модели"""
    X, y, scaler = prepare_data(historical_data)
    if len(X) == 0 or len(y) == 0:
        raise ValueError("❌ Недостаточно данных для обучения AI.")
    
    model = LogisticRegression()
    model.fit(X, y)
    return model, scaler
