import pandas as pd
import ta
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LogisticRegression

def prepare_data(historical_data):
    df = pd.DataFrame(historical_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

    # ✅ Добавляем технические индикаторы
    df['SMA_50'] = ta.trend.sma_indicator(df['close'], window=50)
    df['SMA_200'] = ta.trend.sma_indicator(df['close'], window=200)
    df['RSI'] = ta.momentum.rsi(df['close'], window=14)
    df['MACD'] = ta.trend.macd(df['close'])

    # ✅ Удаляем пустые строки
    df = df.dropna()

    # ✅ Создаем целевую переменную (shift(-1))
    df['Target'] = (df['close'].shift(-1) > df['close']).astype(int)

    # ❌ Исправляем проблему несовместимой длины X и y
    df = df.iloc[:-1]  # Убираем последнюю строку, чтобы X и y совпадали

    # ✅ Нормализация данных
    scaler = MinMaxScaler()
    X = scaler.fit_transform(df[['SMA_50', 'SMA_200', 'RSI', 'MACD', 'close']])
    y = df['Target'].values  # Убираем .shift(-1), так как уже исправили

    return X, y, scaler

def train_ai_model(historical_data):
    """Обучает AI на исторических данных"""
    X, y, scaler = prepare_data(historical_data)

    if len(X) == 0 or len(y) == 0:
        raise ValueError("❌ Недостаточно данных для обучения AI.")

    model = LogisticRegression()
    model.fit(X, y)  # ✅ Теперь X и y всегда имеют одинаковую длину

    return model, scaler


def predict_next_move_ai(model, last_data, scaler):
    """Делает предсказание на основе последних данных"""
    try:
        # ✅ Исправляем ошибку: last_data теперь всегда список из 6 значений
        if isinstance(last_data, list) and len(last_data) == 1:
            last_data = last_data[0]  # Берем первый (и единственный) элемент

        df = pd.DataFrame([last_data], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

        # ✅ Добавляем технические индикаторы (чтобы AI понимал рынок)
        df['SMA_50'] = ta.trend.sma_indicator(df['close'], window=50)
        df['SMA_200'] = ta.trend.sma_indicator(df['close'], window=200)
        df['RSI'] = ta.momentum.rsi(df['close'], window=14)
        df['MACD'] = ta.trend.macd(df['close'])

        # ✅ Удаляем пустые строки
        df = df.dropna()
        if df.empty:
            return "hold"  # Если данных не хватает, просто ждем

        # ✅ Масштабируем данные перед подачей в AI
        X = scaler.transform(df[['SMA_50', 'SMA_200', 'RSI', 'MACD', 'close']])

        # ✅ AI предсказывает "buy" или "sell"
        prediction = model.predict(X)
        return "buy" if prediction[0] == 1 else "sell"

    except Exception as e:
        print(f"❌ Ошибка предсказания AI: {e}")
        return "hold"