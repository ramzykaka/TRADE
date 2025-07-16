import talib
import numpy as np

def calculate_rsi(prices, period=14):
    return talib.RSI(np.array(prices), timeperiod=period)