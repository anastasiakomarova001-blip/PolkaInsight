from __future__ import annotations

import math

import pandas as pd


def add_indicators(frame: pd.DataFrame) -> pd.DataFrame:
    """Добавляет технические индикаторы к дневным котировкам."""
    data = frame.copy()
    data["date"] = pd.to_datetime(data["date"], utc=True)
    data = data.sort_values("date").drop_duplicates("date").reset_index(drop=True)
    data["close"] = pd.to_numeric(data["close"], errors="coerce")
    data = data.dropna(subset=["close"])

    close = data["close"]
    data["sma"] = close.rolling(20, min_periods=20).mean()
    data["ema"] = close.ewm(span=20, adjust=False, min_periods=20).mean()

    delta = close.diff()
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)
    avg_gain = gains.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    avg_loss = losses.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    rs = avg_gain / avg_loss.replace(0, math.nan)
    rsi = 100 - 100 / (1 + rs)
    rsi = rsi.mask((avg_loss == 0) & (avg_gain > 0), 100)
    rsi = rsi.mask((avg_loss == 0) & (avg_gain == 0), 50)
    data["rsi"] = rsi

    ema12 = close.ewm(span=12, adjust=False, min_periods=12).mean()
    ema26 = close.ewm(span=26, adjust=False, min_periods=26).mean()
    data["macd"] = ema12 - ema26
    data["macd_signal"] = data["macd"].ewm(span=9, adjust=False, min_periods=9).mean()
    data["macd_hist"] = data["macd"] - data["macd_signal"]

    data["bb_middle"] = data["sma"]
    deviation = close.rolling(20, min_periods=20).std(ddof=0)
    data["bb_upper"] = data["bb_middle"] + 2 * deviation
    data["bb_lower"] = data["bb_middle"] - 2 * deviation
    return data


def _rsi_score(value: float) -> float:
    if value < 30:
        return 60
    if value < 45:
        return 45
    if value <= 60:
        return 65
    if value <= 70:
        return 55
    return 30


def technical_analysis(frame: pd.DataFrame) -> dict:
    data = add_indicators(frame)
    valid = data.dropna(subset=["rsi", "macd", "macd_signal", "sma", "ema", "bb_upper"])
    if valid.empty:
        return {
            "score": None,
            "indicators": {},
            "explanations": ["Для расчёта индикаторов нужно не менее 34 дневных наблюдений."],
            "series": data,
        }

    latest = valid.iloc[-1]
    previous = valid.iloc[-2] if len(valid) > 1 else latest
    price = float(latest["close"])
    rsi = float(latest["rsi"])
    macd = float(latest["macd"])
    signal = float(latest["macd_signal"])
    sma = float(latest["sma"])
    ema = float(latest["ema"])
    upper = float(latest["bb_upper"])
    lower = float(latest["bb_lower"])

    rsi_part = _rsi_score(rsi)
    rising_impulse = float(latest["macd_hist"]) > float(previous["macd_hist"])
    if macd > signal:
        macd_part = 75 if rising_impulse else 65
        macd_text = "MACD выше сигнальной линии: восходящий импульс."
    else:
        macd_part = 35 if rising_impulse else 25
        macd_text = "MACD ниже сигнальной линии: нисходящий импульс."
    sma_part = 75 if price > sma else 25
    ema_part = 75 if price > ema else 25
    if price > upper:
        bb_part = 35
        bb_text = "Цена выше верхней полосы Боллинджера: импульс сильный, но риск перекупленности выше."
    elif price < lower:
        bb_part = 45
        bb_text = "Цена ниже нижней полосы Боллинджера: повышенная волатильность и перепроданность."
    else:
        bb_part = 60
        bb_text = "Цена находится внутри полос Боллинджера: экстремального отклонения нет."

    score = round(
        0.20 * rsi_part
        + 0.25 * macd_part
        + 0.20 * sma_part
        + 0.20 * ema_part
        + 0.15 * bb_part,
        1,
    )
    indicators = {
        "close": round(price, 4),
        "RSI (14)": round(rsi, 2),
        "MACD": round(macd, 4),
        "Signal": round(signal, 4),
        "SMA (20)": round(sma, 4),
        "EMA (20)": round(ema, 4),
        "BB upper": round(upper, 4),
        "BB lower": round(lower, 4),
    }
    explanations = [
        f"RSI = {rsi:.1f}. Значения ниже 30 и выше 70 показывают перепроданность и перекупленность, но не гарантируют разворот.",
        macd_text,
        f"Цена {'выше' if price > sma else 'ниже'} SMA20 и {'выше' if price > ema else 'ниже'} EMA20.",
        bb_text,
        f"Итог: 20% RSI + 25% MACD + 20% SMA + 20% EMA + 15% Bollinger Bands = {score:.1f}/100.",
    ]
    return {"score": score, "indicators": indicators, "explanations": explanations, "series": data}
