import numpy as np
import pandas as pd
import ta
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, LSTM
from tensorflow.keras.optimizers import Adam

# Создание модели
def create_ai_model():
    model = Sequential([
        LSTM(50, return_sequences=True, input_shape=(50, 5)),
        LSTM(50, return_sequences=False),
        Dense(25, activation='relu'),
        Dense(1, activation='sigmoid')
    ])
    model.compile(optimizer=Adam(learning_rate=0.001), loss='binary_crossentropy', metrics=['accuracy'])
    return model

# Подготовка данных
def prepare_data(historical_data):
    df = pd.DataFrame(historical_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

    # Индикаторы
    df['SMA_50'] = ta.trend.sma_indicator(df['close'], window=50)
    df['SMA_200'] = ta.trend.sma_indicator(df['close'], window=200)
    df['RSI'] = ta.momentum.rsi(df['close'], window=14)
    df['MACD'] = ta.trend.macd(df['close'])
    
    df = df.dropna()
    
    # Нормализация данных
    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(df[['SMA_50', 'SMA_200', 'RSI', 'MACD', 'close']])

    # Создание последовательностей
    X, y = [], []
    for i in range(50, len(scaled_data) - 1):
        X.append(scaled_data[i - 50:i])
        y.append(1 if df['close'].iloc[i + 1] > df['close'].iloc[i] else 0)

    return np.array(X), np.array(y), scaler

# Тренировка модели
def train_ai_model(historical_data):
    X, y, scaler = prepare_data(historical_data)
    if len(X) == 0:
        return None, scaler

    model = create_ai_model()
    model.fit(X, y, epochs=10, batch_size=32, verbose=1)
    return model, scaler

# Прогноз следующего движения
def predict_next_move_ai(model, last_data, scaler):
    scaled_last_data = scaler.transform(last_data)
    X_test = np.array([scaled_last_data])
    prediction = model.predict(X_test)
    return "buy" if prediction[0] > 0.5 else "sell"