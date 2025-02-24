# ai_prediction.py - Предсказания AI модели
import pandas as pd
import ta

def predict_next_move_ai(model, last_data, scaler):
    """AI предсказывает следующее движение"""
    try:
        if isinstance(last_data, list) and len(last_data) == 1:
            last_data = last_data[0]
        
        df = pd.DataFrame([last_data], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        df['SMA_50'] = ta.trend.sma_indicator(df['close'], window=50)
        df['SMA_200'] = ta.trend.sma_indicator(df['close'], window=200)
        df['RSI'] = ta.momentum.rsi(df['close'], window=14)
        df['MACD'] = ta.trend.macd(df['close'])
        
        df = df.dropna()
        if df.empty:
            return "hold"
        
        X = scaler.transform(df[['SMA_50', 'SMA_200', 'RSI', 'MACD', 'close']])
        prediction = model.predict(X)
        return "buy" if prediction[0] == 1 else "sell"
    
    except Exception as e:
        print(f"❌ Ошибка предсказания AI: {e}")
        return "hold"
